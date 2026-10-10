(() => {
  const reader = document.querySelector('.notes-reader');
  if (!reader) return;
  const count = Number(reader.dataset.count);
  const pagesEl = reader.querySelector('.notes-pages');
  const toc = reader.querySelector('.notes-toc');
  const tocList = reader.querySelector('.notes-toc-list');
  const bar = document.querySelector('.notes-bar');
  const input = bar.querySelector('.notes-page');
  const prev = bar.querySelector('.notes-prev');
  const next = bar.querySelector('.notes-next');
  const tocBtn = bar.querySelector('.notes-toc-btn');

  // pages are placeholders with the right shape; each image loads as it nears the view
  const load = new IntersectionObserver((entries) => entries.forEach(({ target, isIntersecting }) => {
    if (!isIntersecting) return;
    const img = target.querySelector('img');
    img.src = img.dataset.src;
    load.unobserve(target);
  }), { rootMargin: '2000px 0px' });

  for (let n = 1; n <= count; n++) {
    const page = document.createElement('div');
    page.className = 'page';
    page.id = `p${n}`;
    page.style.aspectRatio = reader.dataset.ratio;
    const img = document.createElement('img');
    img.alt = `Page ${n}`;
    img.draggable = false;
    img.decoding = 'async';
    img.dataset.src = `p${String(n).padStart(3, '0')}.webp`;
    page.appendChild(img);
    pagesEl.appendChild(page);
    load.observe(page);
  }
  const pageEls = pagesEl.children;

  // all pages share one size, so the current page follows from the first page's position
  const current = () => {
    const first = pageEls[0].getBoundingClientRect();
    const step = count > 1 ? pageEls[1].offsetTop - pageEls[0].offsetTop : first.height;
    const n = Math.floor((innerHeight / 3 - first.top) / step) + 1;
    return Math.min(count, Math.max(1, n));
  };
  const go = (n, y = 0) => {
    n = Math.min(count, Math.max(1, n));
    const pg = pageEls[n - 1];
    const top = scrollY + pg.getBoundingClientRect().top + Math.max(0, y * pg.offsetHeight - (y ? 24 : 0)) - 12;
    const near = !y && Math.abs(n - current()) <= 2;
    scrollTo({ top, behavior: near ? 'smooth' : 'auto' });
  };
  const visit = (n, y = 0) => {
    history.pushState(null, '', `#p${n}`);
    go(n, y);
  };

  // contents: sidebar (or sheet on small screens) from the outline, and the contents pages made clickable
  let tocLinks = [];
  const markToc = (n) => {
    let here = null;
    for (const a of tocLinks) { if (Number(a.dataset.page) <= n) here = a; else break; }
    tocLinks.forEach((a) => a.classList.toggle('current', a === here));
    return here;
  };
  // scroll only the contents list, never the page
  const reveal = (a, center) => {
    if (!a) { toc.scrollTop = 0; return; }
    const top = a.offsetTop, bottom = top + a.offsetHeight;
    if (center) toc.scrollTop = top - toc.clientHeight / 2;
    else if (top < toc.scrollTop) toc.scrollTop = top - 8;
    else if (bottom > toc.scrollTop + toc.clientHeight) toc.scrollTop = bottom - toc.clientHeight + 8;
  };
  const wide = matchMedia('(min-width: 1001px)');
  const sticky = () => wide.matches;
  const closeToc = () => { toc.classList.remove('open'); tocBtn.setAttribute('aria-expanded', 'false'); };
  tocBtn.addEventListener('click', () => {
    const open = !toc.classList.contains('open');
    toc.classList.toggle('open', open);
    tocBtn.setAttribute('aria-expanded', String(open));
    if (open) reveal(markToc(current()), true);
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeToc(); });
  document.addEventListener('click', (e) => { if (toc.classList.contains('open') && !toc.contains(e.target) && !tocBtn.contains(e.target)) closeToc(); });

  fetch('index.json').then((r) => r.json()).then((meta) => {
    meta.toc.forEach(([level, title, page]) => {
      const a = document.createElement('a');
      a.href = `#p${page}`;
      a.className = `toc-${level}`;
      a.textContent = title;
      a.dataset.page = page;
      a.addEventListener('click', (e) => { e.preventDefault(); closeToc(); visit(page); });
      tocList.appendChild(a);
    });
    tocLinks = [...tocList.querySelectorAll('a')];
    const here = markToc(current());
    if (sticky()) reveal(here, true);

    Object.entries(meta.links).forEach(([n, list]) => {
      const page = pageEls[Number(n) - 1];
      list.forEach(([x, y, w, h, to, toY]) => {
        const a = document.createElement('a');
        a.className = 'pl';
        a.href = `#p${to}`;
        a.tabIndex = -1;
        a.setAttribute('aria-label', `Go to page ${to}`);
        Object.assign(a.style, { left: `${x * 100}%`, top: `${y * 100}%`, width: `${w * 100}%`, height: `${h * 100}%` });
        a.addEventListener('click', (e) => { e.preventDefault(); visit(to, toY); });
        page.appendChild(a);
      });
    });
  }).catch(() => { tocBtn.hidden = true; toc.hidden = true; });

  // page bar, address and sidebar follow the scroll
  let shown = 0;
  const sync = () => {
    const n = current();
    if (n === shown) return;
    shown = n;
    if (document.activeElement !== input) input.value = n;
    prev.disabled = n <= 1;
    next.disabled = n >= count;
    history.replaceState(null, '', n > 1 ? `#p${n}` : location.pathname);
    const here = markToc(n);
    if (sticky()) reveal(here, false);
  };
  let ticking = false;
  addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { sync(); ticking = false; });
  }, { passive: true });

  prev.addEventListener('click', () => go(current() - 1));
  next.addEventListener('click', () => go(current() + 1));
  input.addEventListener('change', () => visit(Math.min(count, Math.max(1, Number(input.value) || 1))));
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea')) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); go(current() + 1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(current() - 1); }
  });
  addEventListener('popstate', () => {
    const m = location.hash.match(/^#p(\d+)$/);
    go(m ? Number(m[1]) : 1);
  });

  // no save-as or drag from the page images
  pagesEl.addEventListener('contextmenu', (e) => e.preventDefault());
  pagesEl.addEventListener('dragstart', (e) => e.preventDefault());

  // open at #pN when the address carries one
  const start = location.hash.match(/^#p(\d+)$/);
  requestAnimationFrame(() => { if (start) go(Number(start[1])); sync(); });
})();
