/* ============================================================
   SKYLUX AIRCRAFT CARE — Main JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Sticky nav scroll effect ── */
  const navbar = document.getElementById('navbar');
  const floatingCta = document.querySelector('.floating-cta');

  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY > 60;
    navbar.classList.toggle('scrolled', scrolled);
    floatingCta?.classList.toggle('visible', window.scrollY > 500);
    updateActiveNavLink();
  }, { passive: true });

  /* ── Active nav link on scroll ── */
  const sections = document.querySelectorAll('section[id], div[id]');
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

  function updateActiveNavLink() {
    let current = '';
    const navH = navbar ? navbar.offsetHeight : 68;
    sections.forEach(sec => {
      if (window.scrollY + navH + 80 >= sec.offsetTop) current = sec.id;
    });
    navLinks.forEach(a => {
      a.classList.toggle('active', a.getAttribute('href') === '#' + current);
    });
  }

  /* ── Mobile hamburger ── */
  const hamburger = document.getElementById('hamburger');
  const navLinksEl = document.getElementById('nav-links');

  hamburger?.addEventListener('click', () => {
    const open = hamburger.classList.toggle('open');
    navLinksEl.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });

  navLinksEl?.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      hamburger.classList.remove('open');
      navLinksEl.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  /* ── Smooth scroll for all anchor links ── */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const navH = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 68;
      window.scrollTo({ top: target.offsetTop - navH, behavior: 'smooth' });
    });
  });

  /* ── Scroll reveal ── */
  const revealEls = document.querySelectorAll('.reveal');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const delay = parseInt(entry.target.dataset.delay || 0);
        setTimeout(() => entry.target.classList.add('revealed'), delay);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.05, rootMargin: '0px 0px 0px 0px' });

  revealEls.forEach((el) => {
    // Only calculate stagger delay if not already set to 0 in HTML
    if (!el.hasAttribute('data-delay')) {
      const siblings = [...el.parentElement.children].filter(c => c.classList.contains('reveal'));
      const idx = siblings.indexOf(el);
      el.dataset.delay = Math.min(idx * 60, 240);
    }
    revealObserver.observe(el);
  });

  // Fallback: reveal everything after 1.2s so nothing stays invisible
  setTimeout(() => {
    revealEls.forEach(el => el.classList.add('revealed'));
  }, 1200);

  /* ── Counter animation ── */
  const counters = document.querySelectorAll('.stat-num[data-target]');
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseInt(el.dataset.target);
      const duration = 1600;
      const start = performance.now();
      const animate = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(ease * target);
        if (progress < 1) requestAnimationFrame(animate);
      };
      requestAnimationFrame(animate);
      counterObserver.unobserve(el);
    });
  }, { threshold: 0.5 });
  counters.forEach(c => counterObserver.observe(c));

  /* ── Gallery filter ── */
  const filterBtns = document.querySelectorAll('.filter-btn');
  const galleryItems = document.querySelectorAll('.gallery-item');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.filter;
      galleryItems.forEach(item => {
        const match = filter === 'all' || item.dataset.cat === filter;
        item.style.display = match ? '' : 'none';
      });
    });
  });

  /* ── Contact form ── */
  const form = document.getElementById('contact-form');
  const successMsg = document.getElementById('form-success');

  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    let valid = true;
    form.querySelectorAll('[required]').forEach(field => {
      if (!field.value.trim()) {
        field.classList.add('error');
        valid = false;
      } else {
        field.classList.remove('error');
      }
    });
    if (!valid) return;

    const submitBtn = form.querySelector('[type="submit"]');
    submitBtn.textContent = 'Sending…';
    submitBtn.disabled = true;

    /* Simulate async submission — replace with real fetch() to your backend */
    setTimeout(() => {
      form.style.display = 'none';
      successMsg.classList.add('visible');
      successMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 1200);
  });

  form?.querySelectorAll('input, select, textarea').forEach(field => {
    field.addEventListener('input', () => field.classList.remove('error'));
  });

  /* ── Parallax: hero plane (subtle) ── */
  const heroPlane = document.querySelector('.hero-plane');
  if (heroPlane && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
    window.addEventListener('scroll', () => {
      heroPlane.style.transform = `translateY(${window.scrollY * 0.12}px)`;
    }, { passive: true });
  }

});

