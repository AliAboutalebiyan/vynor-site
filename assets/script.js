
// Mobile nav toggle
const toggle = document.getElementById('navToggle');
const links = document.getElementById('navLinks');
if (toggle && links) {
  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    links.classList.remove('open');
    toggle.setAttribute('aria-expanded','false');
  }));
}

// Copy email button
const copyBtn = document.getElementById('copyEmail');
if (copyBtn) {
  const copyLabel = copyBtn.querySelector('.copy-label');
  const originalLabel = copyLabel.textContent;
  let resetCopyLabel;
  copyBtn.addEventListener('click', async () => {
    const email = copyBtn.dataset.email;
    try {
      await navigator.clipboard.writeText(email);
      clearTimeout(resetCopyLabel);
      copyLabel.textContent = copyBtn.dataset.copiedLabel;
      resetCopyLabel = setTimeout(() => (copyLabel.textContent = originalLabel), 1800);
    } catch (e) {
      window.location.href = 'mailto:' + email;
    }
  });
}

// Subtle reveal-on-scroll for cards
if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
const io = new IntersectionObserver((entries) => {
  entries.forEach(en => {
    if (en.isIntersecting) { en.target.style.opacity = 1; en.target.style.transform = 'none'; io.unobserve(en.target); }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.card, .tl-item').forEach((el, i) => {
  el.style.opacity = 0;
  el.style.transform = 'translateY(16px)';
  el.style.transition = 'opacity .5s ease ' + (i % 4) * 0.06 + 's, transform .5s ease ' + (i % 4) * 0.06 + 's';
  io.observe(el);
});
}
