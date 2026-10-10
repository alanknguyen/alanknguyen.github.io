(() => {
  const reader = document.querySelector('.notes-reader');
  if (!reader) return;
  const count = Number(reader.dataset.count);
  const [rw, rh] = reader.dataset.ratio.split('/').map(Number);
  const scroller = reader.querySelector('.notes-pages');
  const sheet = scroller.querySelector('.notes-sheet');
  const toc = reader.querySelector('.notes-toc');
  const tocList = reader.querySelector('.notes-toc-list');
  const bar = document.querySelector('.notes-bar');
  const input = bar.querySelector('.notes-page');
  const prev = bar.querySelector('.notes-prev');
  const next = bar.querySelector('.notes-next');
  const tocBtn = bar.querySelector('.notes-toc-btn');
  const zoomSel = bar.querySelector('.notes-zoom');
  const zoomIn = bar.querySelector('.notes-zoom-in');
  const zoomOut = bar.querySelector('.notes-zoom-out');
  const spreadBtn = bar.querySelector('.notes-spread');
  const wide = matchMedia('(min-width: 1001px)');

  const ACTUAL = rw * 96 / 72; // 100% = the page at its printed size
  const LEVELS = [0.5, 0.75, 1, 1.25, 1.5, 2, 3];
  const GAP = 18;

  // view: mode is auto | page | width | z (fixed zoom); remembered per visitor
  const view = { mode: 'auto', z: 1, spread: false };
  try { Object.assign(view, JSON.parse(localStorage.getItem('notes-view') || '{}')); } catch {}
  const save = () => { try { localStorage.setItem('notes-view', JSON.stringify(view)); } catch {} };

  // pages are placeholders with the right shape; each image loads as it nears the view
  const load = new IntersectionObserver((entries) => entries.forEach(({ target, isIntersecting }) => {
    if (!isIntersecting) return;
    const img = target.querySelector('img');
    img.src = img.dataset.src;
    load.unobserve(target);
  }), { root: scroller, rootMargin: '1500px 600px' });

  for (let n = 1; n <= count; n++) {
    const page = document.createElement('div');
    page.className = 'sheet-page';
    page.id = `p${n}`;
    page.style.aspectRatio = `${rw} / ${rh}`;
    const img = document.createElement('img');
    img.alt = `Page ${n}`;
    img.draggable = false;
    img.decoding = 'async';
    img.dataset.src = `p${String(n).padStart(3, '0')}.webp`;
    page.appendChild(img);
    sheet.appendChild(page);
    load.observe(page);
  }
  const pages = sheet.children;

  // where we are: the first page of the row crossing the upper third of the view
  const current = () => {
    const mid = scroller.scrollTop + scroller.clientHeight / 3;
    let n = 1;
    for (let i = 0; i < pages.length; i++) {
      if (pages[i].offsetTop > mid) break;
      if (i === 0 || pages[i].offsetTop !== pages[i - 1].offsetTop) n = i + 1;
    }
    return n;
  };
  const rowStart = (i) => { while (i > 0 && pages[i - 1].offsetTop === pages[i].offsetTop) i--; return i; };

  // y is a fraction of the page height; short hops glide, long jumps land directly
  const go = (n, y = 0) => {
    n = Math.min(count, Math.max(1, n));
    const pg = pages[n - 1];
    const top = pg.offsetTop - 12 + Math.max(0, y * pg.offsetHeight - (y ? 24 : 0));
    const near = !y && Math.abs(n - current()) <= 2;
    const left = pg.offsetLeft < scroller.scrollLeft || pg.offsetLeft + pg.offsetWidth > scroller.scrollLeft + scroller.clientWidth
      ? pg.offsetLeft - 12 : scroller.scrollLeft;
    scroller.scrollTo({ top, left, behavior: near ? 'smooth' : 'auto' });
  };
  const visit = (n, y = 0) => { history.pushState(null, '', `#p${n}`); go(n, y); };
  const step = (dir) => {
    const i = rowStart(current() - 1);
    if (dir > 0) {
      let j = i;
      while (j < pages.length && pages[j].offsetTop === pages[i].offsetTop) j++;
      go(Math.min(count, j + 1));
    } else {
      go(i > 0 ? rowStart(i - 1) + 1 : 1);
    }
  };

  // layout: page width from the view mode, then put the reader back where it was
  const cols = () => (view.spread && wide.matches ? 2 : 1);
  const pageWidth = () => {
    const cs = getComputedStyle(scroller);
    const W = scroller.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    const H = scroller.clientHeight - parseFloat(cs.paddingTop) - 72;
    const c = cols();
    const fitW = (W - GAP * (c - 1)) / c;
    if (!wide.matches) return fitW;
    if (view.mode === 'width') return fitW;
    if (view.mode === 'page') return Math.min(H * rw / rh, fitW);
    if (view.mode === 'z') return ACTUAL * view.z;
    return Math.min(fitW, ACTUAL * 1.05);
  };
  const showView = () => {
    const custom = zoomSel.querySelector('[value="custom"]');
    if (view.mode === 'z' && !LEVELS.includes(view.z)) {
      custom.textContent = `${Math.round(view.z * 100)}%`;
      custom.hidden = false;
      zoomSel.value = 'custom';
    } else {
      custom.hidden = true;
      zoomSel.value = view.mode === 'z' ? String(view.z) : view.mode;
    }
    spreadBtn.setAttribute('aria-pressed', String(view.spread));
  };
  const layout = () => {
    const n = current();
    const anchor = pages[n - 1];
    const frac = anchor.offsetHeight ? (scroller.scrollTop - anchor.offsetTop) / anchor.offsetHeight : 0;
    const w = Math.max(160, Math.round(pageWidth()));
    sheet.style.setProperty('--pw', `${w}px`);
    sheet.style.setProperty('--cols', cols());
    sheet.classList.toggle('spread', cols() === 2);
    scroller.scrollTop = anchor.offsetTop + frac * anchor.offsetHeight;
    scroller.scrollLeft = (scroller.scrollWidth - scroller.clientWidth) / 2;
    showView();
    sync(true);
  };
  const zoomBy = (dir) => {
    const z = pages[0].offsetWidth / ACTUAL;
    const to = dir > 0 ? LEVELS.find((l) => l > z + 0.01) : [...LEVELS].reverse().find((l) => l < z - 0.01);
    if (!to) return;
    view.mode = 'z';
    view.z = to;
    layout();
    save();
  };

  zoomSel.addEventListener('change', () => {
    const v = zoomSel.value;
    if (v === 'custom') return;
    if (['auto', 'page', 'width'].includes(v)) view.mode = v;
    else { view.mode = 'z'; view.z = Number(v); }
    layout();
    save();
    scroller.focus({ preventScroll: true });
  });
  zoomIn.addEventListener('click', () => zoomBy(1));
  zoomOut.addEventListener('click', () => zoomBy(-1));
  spreadBtn.addEventListener('click', () => { view.spread = !view.spread; layout(); save(); });
  let resizeTick = false;
  addEventListener('resize', () => {
    if (resizeTick) return;
    resizeTick = true;
    requestAnimationFrame(() => { layout(); resizeTick = false; });
  });

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
  const closeToc = () => { toc.classList.remove('open'); tocBtn.setAttribute('aria-expanded', 'false'); };
  tocBtn.addEventListener('click', () => {
    const open = !toc.classList.contains('open');
    toc.classList.toggle('open', open);
    tocBtn.setAttribute('aria-expanded', String(open));
    if (open) reveal(markToc(current()), true);
  });
  document.addEventListener('click', (e) => { if (toc.classList.contains('open') && !toc.contains(e.target) && !tocBtn.contains(e.target)) closeToc(); });

  fetch('index.json').then((r) => r.json()).then((meta) => {
    meta.toc.forEach(([level, title, page]) => {
      const a = document.createElement('a');
      a.href = `#p${page}`;
      a.className = `toc-${level}`;
      a.textContent = title;
      a.dataset.page = page;
      a.addEventListener('click', (e) => { e.preventDefault(); closeToc(); visit(page); scroller.focus({ preventScroll: true }); });
      tocList.appendChild(a);
    });
    tocLinks = [...tocList.querySelectorAll('a')];
    const here = markToc(current());
    if (wide.matches) reveal(here, true);

    Object.entries(meta.links).forEach(([n, list]) => {
      const page = pages[Number(n) - 1];
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

  // page box, address and contents follow the scroll
  let shown = 0;
  function sync(force) {
    const n = current();
    if (n === shown && !force) return;
    shown = n;
    if (document.activeElement !== input) input.value = n;
    prev.disabled = n <= 1;
    next.disabled = rowStart(count - 1) <= n - 1;
    history.replaceState(null, '', n > 1 ? `#p${n}` : location.pathname);
    const here = markToc(n);
    if (wide.matches) reveal(here, false);
  }
  let ticking = false;
  scroller.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { sync(); ticking = false; });
  }, { passive: true });

  prev.addEventListener('click', () => step(-1));
  next.addEventListener('click', () => step(1));
  input.addEventListener('change', () => visit(Math.min(count, Math.max(1, Number(input.value) || 1))));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeToc();
    if ((e.target instanceof Element && e.target.closest('input, textarea, select')) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
    if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomBy(1); }
    if (e.key === '-' || e.key === '_') { e.preventDefault(); zoomBy(-1); }
  });
  addEventListener('popstate', () => {
    const m = location.hash.match(/^#p(\d+)$/);
    go(m ? Number(m[1]) : 1);
  });

  // no save-as or drag from the page images
  scroller.addEventListener('contextmenu', (e) => e.preventDefault());
  scroller.addEventListener('dragstart', (e) => e.preventDefault());

  // read #pN before the first layout rewrites the address, then open there
  const start = location.hash.match(/^#p(\d+)$/);
  layout();
  if (start) go(Number(start[1]));
  sync(true);
  scroller.focus({ preventScroll: true });
})();
