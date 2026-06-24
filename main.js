// Ordinary Agency — interactions

// Current year in footer
document.getElementById('year').textContent = new Date().getFullYear();

// Sticky-header border on scroll
const header = document.getElementById('header');
const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
onScroll();
window.addEventListener('scroll', onScroll, { passive: true });

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
