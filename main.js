// Ordinary Agency — interactions

// Current year in footer
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Sticky-header border on scroll
const header = document.getElementById('header');
if (header) {
  const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}

// Mobile menu toggle
const toggle = document.querySelector('.nav-toggle');
const menu = document.getElementById('mobile-menu');
if (toggle && menu) {
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    toggle.setAttribute('aria-label', open ? 'Open menu' : 'Close menu');
    menu.hidden = open;
  });
  menu.querySelectorAll('a').forEach((a) =>
    a.addEventListener('click', () => {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
      menu.hidden = true;
    })
  );
}

// Scroll-reveal
const revealEls = document.querySelectorAll('.reveal');
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (reduce || !('IntersectionObserver' in window)) {
  revealEls.forEach((el) => el.classList.add('is-visible'));
} else {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
  );

  // Stagger siblings slightly for a refined cascade
  revealEls.forEach((el) => {
    const parent = el.parentElement;
    const sibs = Array.from(parent.children).filter((c) => c.classList.contains('reveal'));
    const idx = sibs.indexOf(el);
    if (idx > 0) el.style.transitionDelay = `${Math.min(idx * 70, 280)}ms`;
    io.observe(el);
  });
}

// Contact + discovery forms — AJAX submit to the worker's /oa-form route
// (Resend emails Mike) with inline feedback. If the fetch itself dies, a native
// POST still works: the worker 303s back here with ?sent=1. Without JS at all,
// the form POSTs natively from the start.
const SENT_MSG = 'Thanks — your message is on its way. We usually reply within a day.';
const FAIL_MSG = 'That didn\u2019t send. Please try again, or email mike@ordinaryagency.com.au.';

const showStatus = (form, msg, ok) => {
  const status = form.querySelector('.form-status');
  if (!status) return;
  status.hidden = false;
  status.textContent = msg;
  status.classList.toggle('is-success', ok);
  status.classList.toggle('is-error', !ok);
};

// A form may name a panel to reveal instead of an inline message — the long
// discovery form swaps itself out for a thank-you rather than tacking a line
// under a submit button that's scrolled far off screen.
const succeed = (form, msg) => {
  // Only ever fired once the send is confirmed — the discovery form listens for
  // this to bin its draft, and a draft must outlive an abandoned submit.
  form.dispatchEvent(new CustomEvent('oa:sent'));
  const panelId = form.dataset.successPanel;
  const panel = panelId && document.getElementById(panelId);
  if (panel) {
    form.hidden = true;
    panel.hidden = false;
    panel.setAttribute('tabindex', '-1');
    panel.focus({ preventScroll: true });
    panel.scrollIntoView({ block: 'start', behavior: 'smooth' });
    return;
  }
  const btn = form.querySelector('button[type="submit"]');
  if (btn) btn.hidden = true;
  showStatus(form, msg, true);
};

document.querySelectorAll('.contact__form, .dsc__form').forEach((form) => {
  // Returned from the worker after a native (no-JS or fallback) submit.
  if (new URLSearchParams(location.search).get('sent') === '1') {
    succeed(form, SENT_MSG);
  }

  // Coming back via the back button restores a disabled
  // "Sending…" button from the bfcache, with no way to try again.
  window.addEventListener('pageshow', () => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn && btn.disabled && btn.dataset.label) {
      btn.disabled = false;
      btn.textContent = btn.dataset.label;
    }
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const label = btn ? btn.textContent : '';
    if (btn) { btn.dataset.label = label; btn.disabled = true; btn.textContent = 'Sending…'; }

    // Network failure only: form.submit() bypasses this handler, so no loop.
    const fallback = () => form.submit();
    // The worker answered and said no — a native retry would fail the same
    // way, so say so and give the button back rather than failing silently.
    const refuse = (msg) => {
      if (btn) { btn.disabled = false; btn.textContent = label; }
      showStatus(form, msg || FAIL_MSG, false);
    };

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          return refuse(body.error);
        }
        form.reset();
        if (btn) btn.textContent = label;
        succeed(form, SENT_MSG);
      })
      .catch(fallback);
  });
});

// ---------------------------------------------------------------------------
// Discovery form — turn the long questionnaire into a stepper.
// Every step ships visible, so with no JS this is one honest scrolling form
// that still submits. Everything below is enhancement.
// ---------------------------------------------------------------------------
(() => {
  const form = document.getElementById('dsc-form');
  if (!form) return;

  const steps = [...form.querySelectorAll('.dsc__step')];
  if (steps.length < 2) return;

  // Once steps are hidden, the browser's own validation would block submission
  // on a required field it cannot scroll to or focus, and the submit event
  // would never fire. Validation moves to validateStep() below. Without JS the
  // attribute is never set, so native validation still applies.
  form.noValidate = true;

  const progress   = document.getElementById('dsc-progress');
  const fill       = document.getElementById('dsc-progress-fill');
  const text       = document.getElementById('dsc-progress-text');
  const backBtn    = document.getElementById('dsc-back');
  const nextBtn    = document.getElementById('dsc-next');
  const submitBtn  = document.getElementById('dsc-submit');
  const saveNote   = document.getElementById('dsc-save-note');
  const STORE_KEY  = 'oa_discovery_v1';

  let current = 0;

  // Came back from a native submit: the brief is in, so the draft is spent.
  const justSent = new URLSearchParams(location.search).get('sent') === '1';

  // --- draft persistence -----------------------------------------------------
  // Losing thirty answers to a stray refresh would be miserable. Kept in this
  // browser only; never sent anywhere until the form is submitted.
  const saveDraft = () => {
    try {
      const data = {};
      new FormData(form).forEach((v, k) => {
        if (k.startsWith('_')) return;
        if (data[k] === undefined) data[k] = v;
        else if (Array.isArray(data[k])) data[k].push(v);
        else data[k] = [data[k], v];
      });
      localStorage.setItem(STORE_KEY, JSON.stringify(data));
    } catch (_) { /* private window, blocked storage — carry on */ }
  };

  const loadDraft = () => {
    let data;
    try {
      data = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
    } catch (_) { return false; }
    if (!data) return false;

    Object.entries(data).forEach(([name, value]) => {
      const values = Array.isArray(value) ? value : [value];
      form.querySelectorAll(`[name="${CSS.escape(name)}"]`).forEach((el) => {
        if (el.type === 'checkbox' || el.type === 'radio') {
          if (values.includes(el.value)) el.checked = true;
        } else if (values[0] !== undefined) {
          el.value = values[0];
        }
      });
    });
    return true;
  };

  const clearDraft = () => {
    try { localStorage.removeItem(STORE_KEY); } catch (_) {}
  };

  // --- validation ------------------------------------------------------------
  // Native validity covers required inputs. Checkbox groups can't express
  // "at least one of these", so data-require-one carries that, and an adjacent
  // "other" text field counts as an answer.
  const validateStep = (i) => {
    const step = steps[i];
    let firstBad = null;

    step.querySelectorAll('input, textarea, select').forEach((el) => {
      if (!el.checkValidity() && !firstBad) firstBad = el;
    });

    step.querySelectorAll('[data-require-one]').forEach((group) => {
      const name = group.dataset.requireOne;
      const checked = group.querySelector(`[name="${CSS.escape(name)}"]:checked`);
      const other = group.querySelector(`[name="${CSS.escape(name)} — other"]`);
      const ok = !!checked || (other && other.value.trim() !== '');
      const err = group.querySelector(`[data-error-for="${CSS.escape(name)}"]`);
      if (err) err.hidden = ok;
      if (!ok && !firstBad) firstBad = group.querySelector('input');
    });

    if (firstBad) {
      if (typeof firstBad.reportValidity === 'function' && !firstBad.checkValidity()) {
        firstBad.reportValidity();
      } else {
        firstBad.focus();
      }
      return false;
    }
    return true;
  };

  // --- rendering -------------------------------------------------------------
  const render = (i, { focus = true } = {}) => {
    current = i;
    steps.forEach((s, n) => { s.hidden = n !== i; });

    const pct = Math.round(((i + 1) / steps.length) * 100);
    if (fill) fill.style.width = pct + '%';
    if (text) text.textContent = `Step ${i + 1} of ${steps.length}`;

    backBtn.hidden   = i === 0;
    nextBtn.hidden   = i === steps.length - 1;
    submitBtn.hidden = i !== steps.length - 1;

    if (focus) {
      const legend = steps[i].querySelector('.dsc__legend');
      if (legend) {
        legend.setAttribute('tabindex', '-1');
        legend.focus({ preventScroll: true });
      }
      const top = form.getBoundingClientRect().top + window.scrollY - 90;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  };

  // --- wire up ---------------------------------------------------------------
  progress.hidden = false;
  nextBtn.hidden = false;

  if (justSent) { clearDraft(); return; }

  const restored = loadDraft();
  if (saveNote) {
    saveNote.hidden = false;
    if (restored) saveNote.textContent = 'We restored your answers from last time.';
  }

  form.addEventListener('input', saveDraft);
  form.addEventListener('change', saveDraft);

  nextBtn.addEventListener('click', () => {
    if (!validateStep(current)) return;
    render(Math.min(current + 1, steps.length - 1));
  });

  backBtn.addEventListener('click', () => render(Math.max(current - 1, 0)));

  // Guard the final submit too — someone can reach it without passing through
  // every step if they restore a draft.
  form.addEventListener('submit', (e) => {
    for (let i = 0; i < steps.length; i++) {
      if (!validateStep(i)) {
        e.preventDefault();
        e.stopImmediatePropagation();
        render(i);
        return;
      }
    }
  }, true);

  // Not on submit — a send can still fail, and binning thirty answers at that
  // point is the worst moment to do it.
  form.addEventListener('oa:sent', clearDraft);

  // Enter in a single-line field should advance, not submit from step 2.
  form.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    if (e.target.tagName === 'TEXTAREA') return;
    if (current < steps.length - 1) {
      e.preventDefault();
      nextBtn.click();
    }
  });

  render(0, { focus: false });
})();

// Homepage blueprint (website-development.html) — every callout is open in the
// markup so it reads without JS. On a phone the text column is narrow and nine
// open rows get very long, so start with just the first open; tap to expand.
if (window.matchMedia('(max-width: 680px)').matches) {
  document.querySelectorAll('.bp-callout').forEach((d, i) => { if (i > 0) d.open = false; });
}

// Floating call button on phones — appears once the header's call button has
// scrolled out of view, so the number is always one tap away.
(() => {
  if (!window.matchMedia('(max-width: 860px)').matches) return;
  const fab = document.createElement('a');
  fab.href = 'tel:+61403566928';
  fab.className = 'call-fab';
  fab.setAttribute('aria-label', 'Call Ordinary Agency on 0403 566 928');
  fab.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/></svg>Call Mike';
  fab.tabIndex = -1;
  document.body.appendChild(fab);
  const footer = document.querySelector('.site-footer');
  const update = () => {
    const pastHeader = window.scrollY > 480;
    // Step aside over the footer, which has its own contact links.
    const atFooter = footer && footer.getBoundingClientRect().top < window.innerHeight - 40;
    const show = pastHeader && !atFooter;
    fab.classList.toggle('is-shown', show);
    fab.tabIndex = show ? 0 : -1;
  };
  update();
  window.addEventListener('scroll', update, { passive: true });
})();

// Conversion events. Sends to whichever analytics is on the page (GA4's gtag or
// Plausible) and does nothing when neither is, so it's safe to ship before one
// is chosen. Events: call_click, email_click, form_sent, brief_sent,
// outbound_senditbro.
const track = (name, props = {}) => {
  const data = { page: location.pathname, ...props };
  if (typeof window.gtag === 'function') window.gtag('event', name, data);
  if (typeof window.plausible === 'function') window.plausible(name, { props: data });
};
document.addEventListener('click', (e) => {
  const a = e.target.closest && e.target.closest('a[href]');
  if (!a) return;
  const href = a.getAttribute('href');
  const where = a.closest('header') ? 'header' : a.classList.contains('call-fab') ? 'floating' : a.closest('footer') ? 'footer' : 'page';
  if (href.startsWith('tel:')) track('call_click', { where });
  else if (href.startsWith('mailto:')) track('email_click', { where });
  else if (href.includes('senditbro.com.au')) track('outbound_senditbro', { where });
});
document.querySelectorAll('.contact__form, .dsc__form').forEach((form) => {
  form.addEventListener('oa:sent', () => track(form.classList.contains('dsc__form') ? 'brief_sent' : 'form_sent'));
});
