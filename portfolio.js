(() => {
  const root = document.documentElement;
  root.classList.add('js');
  let saved;
  try { saved = localStorage.getItem('theme'); } catch (_) { /* Storage is optional. */ }
  if (saved === 'light' || saved === 'dark') root.dataset.theme = saved;
  const theme = document.querySelector('.theme-toggle');
  const labelTheme = () => theme.setAttribute('aria-label', `Switch to ${root.dataset.theme === 'dark' ? 'light' : 'dark'} theme`);
  labelTheme();
  theme.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (_) { /* Keep the current session functional. */ }
    labelTheme();
  });
  const menu = document.getElementById('reference-menu-toggle');
  const links = document.getElementById('reference-nav-links');
  const setMenu = open => { links.classList.toggle('open', open); menu.setAttribute('aria-expanded', String(open)); menu.setAttribute('aria-label', open ? 'Close menu' : 'Open menu'); };
  setMenu(false);
  menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
  links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { setMenu(false); menu.focus(); } });
  document.addEventListener('click', e => { if (!e.target.closest('#navbar')) setMenu(false); });
  document.getElementById('navbar').addEventListener('focusout', () => { setTimeout(() => { if (!document.activeElement.closest('#navbar')) setMenu(false); }, 0); });
  // Native buttons remain keyboard-operable; hidden is applied only after JS loads.
  const workflowButtons = [...document.querySelectorAll('[data-workflow]')];
  const selectWorkflow = key => {
    workflowButtons.forEach(button => {
      const selected = button.dataset.workflow === key;
      button.setAttribute('aria-pressed', String(selected));
      document.getElementById(button.getAttribute('aria-controls')).hidden = !selected;
    });
  };
  workflowButtons.forEach(button => button.addEventListener('click', () => selectWorkflow(button.dataset.workflow)));
  selectWorkflow('ar');
  document.querySelectorAll('.pipe-step').forEach(step => step.addEventListener('click', () => step.focus({preventScroll:true})));
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(({target,isIntersecting}) => {
      if (!isIntersecting) return;
      if (!motion.matches) target.classList.add('entering');
      observer.unobserve(target);
    }), {threshold: .08});
    document.querySelectorAll('.card, .section-header, .visual-timeline-item, .cert-list-item').forEach((el,i) => { el.style.setProperty('--delay', `${i % 2 * 70}ms`); observer.observe(el); });

  }
  // A single measured offset serves native anchors and active-link tracking.
  const navbar = document.getElementById('navbar');
  const navItems = [...links.querySelectorAll('a[href^="#"]')];
  const offset = () => navbar.getBoundingClientRect().bottom + 16;
  const updateOffset = () => root.style.setProperty('--anchor-offset', `${offset()}px`);
  updateOffset();
  new ResizeObserver(updateOffset).observe(navbar);
  window.addEventListener('resize', updateOffset);
  const updateActive = () => {
    let active = null;
    navItems.forEach(a => {
      const target = document.querySelector(a.hash);
      if (target && target.getBoundingClientRect().top <= offset() + 3) active = a;
    });
    navItems.forEach(a => {
      a.classList.toggle('active', a === active);
      if (a === active) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
  };
  window.addEventListener('scroll', updateActive, {passive:true});
  window.addEventListener('scrollend', updateActive);
  document.addEventListener('animationend', updateActive);
  window.addEventListener('resize', updateActive);
  const ready = () => {
    document.getElementById('preloader').classList.add('is-ready');
    updateOffset();
    if (location.hash) {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView({behavior:'instant'});
    }
    updateActive();
  };
  const fontsReady = document.fonts ? document.fonts.ready : Promise.resolve();
  Promise.race([fontsReady, new Promise(resolve => setTimeout(resolve, 1200))]).then(ready);
  document.querySelectorAll('.hero-cascade').forEach(el => {
    if (!motion.matches) {
      el.style.setProperty('--delay', `${Math.min(Number(el.dataset.seq || 0), 6) * 65}ms`);
      el.classList.add('entering');
    }
  });
  const top = document.getElementById('backToTop');
  top.addEventListener('click', () => window.scrollTo({top:0,behavior:motion.matches?'instant':'smooth'}));
  let queued = false;
  const update = () => {
    queued = false;
    const y = window.scrollY, height = root.scrollHeight - innerHeight;
    navbar.classList.toggle('scrolled', y > 24);
    document.getElementById('scroll-progress').style.width = `${height > 0 ? y / height * 100 : 0}%`;
    top.classList.toggle('is-visible', y > 500);
    document.querySelector('.dashboard-preview').style.setProperty('--parallax', !motion.matches && innerWidth > 700 ? `${Math.min(y * .035, 12)}px` : '0px');
  };
  addEventListener('scroll', () => { if (!queued) { queued = true; requestAnimationFrame(update); } }, {passive:true});
  motion.addEventListener('change', update);
  update();
})();

