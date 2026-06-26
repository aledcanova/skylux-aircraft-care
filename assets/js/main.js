/* SkyLux Private Aviation Care — Main JS */
document.addEventListener('DOMContentLoaded', () => {

  /* ── Navbar scroll ── */
  const navbar  = document.getElementById('navbar');
  const floatCta = document.getElementById('float-cta');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
    floatCta.classList.toggle('show', window.scrollY > 600);
  }, { passive: true });

  /* ── Hamburger ── */
  const ham  = document.getElementById('hamburger');
  const nav  = document.getElementById('nav-links');
  ham?.addEventListener('click', () => {
    const open = ham.classList.toggle('open');
    nav.classList.toggle('open', open);
    ham.setAttribute('aria-expanded', String(open));
  });
  nav?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    ham.classList.remove('open');
    nav.classList.remove('open');
    ham.setAttribute('aria-expanded', 'false');
  }));

  /* ── Smooth scroll ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (!t) return;
      e.preventDefault();
      const offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav')) || 72;
      window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - offset, behavior: 'smooth' });
    });
  });

  /* ── Service tabs ── */
  document.querySelectorAll('.stab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.stab').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-selected','false'); });
      document.querySelectorAll('.spanel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      btn.setAttribute('aria-selected','true');
      document.getElementById('panel-' + btn.dataset.tab)?.classList.add('active');
    });
  });

  /* ── Gallery filter ── */
  const gBtns  = document.querySelectorAll('.gbtn');
  const gItems = document.querySelectorAll('.gitem');
  gBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      gBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const f = btn.dataset.filter;
      gItems.forEach(item => { item.style.display = (f === 'all' || item.dataset.cat === f) ? '' : 'none'; });
    });
  });

  /* ── Reveal on scroll ── */
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.1 });
    document.querySelectorAll('.reveal').forEach(el => io.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('in'));
  }

  /* ── Contact form ── */
  const form    = document.getElementById('contact-form');
  const success = document.getElementById('form-success');
  form?.addEventListener('submit', e => {
    e.preventDefault();
    const btn = form.querySelector('[type="submit"]');
    btn.textContent = 'Sending…';
    btn.disabled = true;
    setTimeout(() => {
      form.style.display = 'none';
      success.classList.add('visible');
    }, 900);
  });

});
