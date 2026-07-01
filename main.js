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
// Progressive enhancement: without JS the form still POSTs normally.
document.querySelectorAll('.contact__form').forEach((form) => {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const status = form.querySelector('.form-status');
    const btn = form.querySelector('button[type="submit"]');
    const showStatus = (msg, ok) => {
      if (!status) return;
      status.hidden = false;
      status.textContent = msg;
      status.classList.toggle('is-success', ok);
      status.classList.toggle('is-error', !ok);
    };
    if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { Accept: 'application/json' },
    })
      .then((res) => {
        if (res.ok) {
          form.reset();
          if (btn) btn.hidden = true;
          showStatus('Thanks — your message is on its way. We usually reply within a day.', true);
        } else {
          return res.json().then((d) => {
            const msg = d && d.errors ? d.errors.map((x) => x.message).join(', ')
              : 'Something went wrong. Please email mike@ordinaryagency.com.au.';
            showStatus(msg, false);
            if (btn) { btn.disabled = false; btn.textContent = 'Send message'; }
          });
        }
      })
      .catch(() => {
        showStatus('Network error. Please email mike@ordinaryagency.com.au.', false);
        if (btn) { btn.disabled = false; btn.textContent = 'Send message'; }
      });
  });
});
