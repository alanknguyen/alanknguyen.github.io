(() => {
  const root = document.documentElement;

  // theme: stored choice wins, otherwise follow the OS
  const toggle = document.querySelector('[data-theme-toggle]');
  const prefersDark = matchMedia('(prefers-color-scheme: dark)');
  const theme = () => root.dataset.theme || (prefersDark.matches ? 'dark' : 'light');
  const relabel = () => { if (toggle) toggle.textContent = theme() === 'dark' ? 'Light mode' : 'Dark mode'; };
  toggle?.addEventListener('click', () => {
    const next = theme() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch {}
    relabel();
  });
  prefersDark.addEventListener('change', relabel);
  relabel();

  // show-all buttons for long lists; CSS hides the rows past data-show
  document.querySelectorAll('[data-toggle]').forEach((btn) => {
    const list = document.getElementById(btn.dataset.toggle);
    if (!list) return;
    const hidden = list.children.length - Number(list.dataset.show || 5);
    if (hidden <= 0) { btn.remove(); return; }
    const label = () => {
      const open = list.classList.contains('expanded');
      btn.textContent = open ? 'Show fewer' : `Show all (${hidden} more)`;
      btn.setAttribute('aria-expanded', String(open));
    };
    btn.addEventListener('click', () => { list.classList.toggle('expanded'); label(); });
    label();
  });

  // Thumbnails: videos loop while on screen, or on hover with data-play="hover".
  // An <img data-gif> swaps to the gif on hover. Reduced motion makes everything hover-only.
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const canHover = matchMedia('(hover: hover)').matches;
  const videos = [...document.querySelectorAll('.thumb video')];

  videos.forEach((v) => {
    v.muted = true; v.loop = true; v.playsInline = true;
    if (reduceMotion || v.closest('.thumb').dataset.play === 'hover') v.dataset.hover = '1';
  });

  const play = (v) => v.play().catch(() => {});
  const observer = 'IntersectionObserver' in window
    ? new IntersectionObserver((entries) => entries.forEach(({ target: v, isIntersecting }) => {
        if (v.dataset.hover) return;
        isIntersecting ? play(v) : v.pause();
      }), { rootMargin: '120px' })
    : null;
  videos.forEach((v) => (observer ? observer.observe(v) : (v.dataset.hover ? null : play(v))));

  document.querySelectorAll('.thumb').forEach((thumb) => {
    const entry = thumb.closest('.entry') || thumb;
    const v = thumb.querySelector('video');
    const img = thumb.querySelector('img[data-gif]');
    const still = img?.getAttribute('src');
    const on = () => {
      if (v?.dataset.hover) play(v);
      if (img && !reduceMotion) img.src = img.dataset.gif;
    };
    const off = () => {
      if (v?.dataset.hover) { v.pause(); v.currentTime = 0; }
      if (img && still) img.src = still;
    };
    if (canHover) {
      entry.addEventListener('mouseenter', on);
      entry.addEventListener('mouseleave', off);
    }
    entry.addEventListener('focusin', on);
    entry.addEventListener('focusout', off);
  });
})();
