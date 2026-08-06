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

// Contact form — AJAX submit to Formspree with inline feedback.
// Formspree refuses AJAX posts while reCAPTCHA is enabled on the form, so any
// failure falls back to a native POST: Formspree handles the challenge and its
// _next value returns the visitor here with ?sent=1. Without JS at all, the
// form POSTs natively from the start. Either way the enquiry gets through.
const SENT_MSG = 'Thanks — your message is on its way. We usually reply within a day.';

const showStatus = (form, msg, ok) => {
  const status = form.querySelector('.form-status');
  if (!status) return;
  status.hidden = false;
  status.textContent = msg;
  status.classList.toggle('is-success', ok);
  status.classList.toggle('is-error', !ok);
};

document.querySelectorAll('.contact__form').forEach((form) => {
  // Returned from Formspree's own page after a native fallback submit.
  if (new URLSearchParams(location.search).get('sent') === '1') {
    const btn = form.querySelector('button[type="submit"]');
    if (btn) btn.hidden = true;
    showStatus(form, SENT_MSG, true);
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

    // form.submit() bypasses this handler, so there's no submit loop.
    const fallback = () => form.submit();

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
    })
      .then((res) => {
        if (!res.ok) return fallback();
        form.reset();
        if (btn) btn.hidden = true;
        showStatus(form, SENT_MSG, true);
      })
      .catch(fallback);
  });
});
