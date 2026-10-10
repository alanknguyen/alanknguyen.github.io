(() => {
  const root = document.documentElement;

  // theme: light unless the visitor picked dark
  const toggle = document.querySelector('[data-theme-toggle]');
  const theme = () => root.dataset.theme || 'light';
  const relabel = () => { if (toggle) toggle.textContent = theme() === 'dark' ? 'Light mode' : 'Dark mode'; };
  toggle?.addEventListener('click', () => {
    const next = theme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch {}
    relabel();
  });
  relabel();

  // touch screens can't hover, so a tap flips "(Alan)" instead
  if (!matchMedia('(hover: hover)').matches) {
    document.querySelectorAll('.flip').forEach((el) => el.addEventListener('click', () => el.classList.toggle('flipped')));
  }

  // figure strips and bibtex blocks under an entry
  document.querySelectorAll('[data-reveal]').forEach((btn) => {
    const target = document.getElementById(btn.dataset.reveal);
    if (!target) return;
    btn.setAttribute('aria-expanded', String(!target.hidden));
    btn.addEventListener('click', () => {
      target.hidden = !target.hidden;
      btn.setAttribute('aria-expanded', String(!target.hidden));
    });
  });

  // thumbnails: still image, swapped for its gif while the entry is hovered or focused
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.thumb img[data-gif]').forEach((img) => {
    const still = img.getAttribute('src');
    const entry = img.closest('.entry') || img;
    const on = () => { if (!reduceMotion) img.src = img.dataset.gif; };
    const off = () => { img.src = still; };
    entry.addEventListener('mouseenter', on);
    entry.addEventListener('mouseleave', off);
    entry.addEventListener('focusin', on);
    entry.addEventListener('focusout', (e) => { if (!entry.contains(e.relatedTarget)) off(); });

    // fetch the gif once the entry is close, so the first hover doesn't wait on it
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(([e]) => {
        if (!e.isIntersecting) return;
        new Image().src = img.dataset.gif;
        io.disconnect();
      }, { rootMargin: '200px' });
      io.observe(entry);
    }
  });
})();
