(() => {
  const root = document.documentElement;

  // theme: dark unless the visitor picked light
  const toggle = document.querySelector('[data-theme-toggle]');
  const theme = () => root.dataset.theme || 'dark';
  const relabel = () => {
    if (!toggle) return;
    const label = theme() === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    toggle.setAttribute('aria-label', label);
    toggle.title = label;
  };
  toggle?.addEventListener('click', () => {
    const next = theme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch {}
    relabel();
  });
  relabel();

  // mail links are assembled here so the address isn't sitting in the page source
  document.querySelectorAll('a[data-mail-user]:not(.notes-errata)').forEach((a) => {
    const subject = a.dataset.mailSubject ? `?subject=${encodeURIComponent(a.dataset.mailSubject)}` : '';
    a.href = `mailto:${a.dataset.mailUser}@${a.dataset.mailDomain}${subject}`;
  });

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

  // note pickers: one entry, several notes; the choice sets the panel, Read and Errata links
  document.querySelectorAll('[data-note-picker]').forEach((picker) => {
    const select = picker.querySelector('select');
    const entry = picker.closest('.entry');
    const show = () => {
      const opt = select.selectedOptions[0];
      select.querySelectorAll('option').forEach((o) => { document.getElementById(o.value).hidden = o !== opt; });
      entry.querySelectorAll('[data-note-link]').forEach((a) => { a.href = opt.dataset.href; });
      const errata = entry.querySelector('[data-note-errata]');
      if (errata) errata.href = `mailto:${errata.dataset.mailUser}@${errata.dataset.mailDomain}?subject=${encodeURIComponent(`Erratum: ${opt.dataset.title}`)}`;
    };
    select.addEventListener('change', show);
    show();
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
