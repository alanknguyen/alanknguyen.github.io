// Notes library: the collections, and a reader that moves between notes in place.
// The reader is the regular note page in a frame; the rail beside it lists every note and the
// current note's sections, and the two talk by postMessage (page changes out, jumps in).
(() => {
  const root = document.documentElement;
  const data = JSON.parse(document.getElementById('lib-data').textContent);
  const notes = data.flatMap((c) => c.notes.map((n) => ({ ...n, col: c })));
  const byKey = new Map(notes.map((n) => [n.key, n]));

  const rail = document.querySelector('.lib-rail');
  const tree = rail.querySelector('.rail-tree');
  const search = rail.querySelector('.rail-search input');
  const results = rail.querySelector('.rail-results');
  const frame = document.querySelector('.lib-frame');
  const stageTitle = document.querySelector('.stage-title');
  const railOpen = document.querySelector('.rail-open');
  const upNext = document.querySelector('.up-next');
  const upLink = upNext.querySelector('.un-link');

  const label = (n) => `Notes ${n.num} · ${n.short}`;

  // ---- library cards: the notes list and more info open full width under the card;
  // only one notes list is open on the page at a time
  const setPanel = (panel, open) => {
    panel.hidden = !open;
    document.querySelector(`[data-panel="${panel.id}"]`)?.setAttribute('aria-expanded', String(open));
  };
  document.querySelectorAll('.lib-toggle').forEach((btn) => {
    const panel = document.getElementById(btn.dataset.panel);
    btn.addEventListener('click', () => {
      const open = panel.hidden;
      if (open && panel.classList.contains('lib-parts')) {
        document.querySelectorAll('.lib-parts').forEach((p) => { if (p !== panel) setPanel(p, false); });
      }
      setPanel(panel, open);
    });
  });

  // ---- the rail: every collection, its notes, and the open note's sections
  const groupNum = (num) => num.replace(/[a-z]+$/, '');
  data.forEach((c) => {
    const sec = document.createElement('section');
    sec.className = 'rail-col';
    sec.dataset.col = c.key;
    sec.innerHTML = `<button type="button" class="rail-col-h" aria-expanded="false"><span></span><small>${c.year}</small></button><ol></ol>`;
    sec.querySelector('.rail-col-h span').textContent = c.title;
    const ol = sec.querySelector('ol');
    ol.hidden = true;
    let lastGroup = null;
    c.notes.forEach((n) => {
      if (n.group && n.group !== lastGroup) {
        const g = document.createElement('li');
        g.className = 'rail-group';
        g.innerHTML = '<span class="rg-part"></span><span class="rg-t"></span>';
        g.querySelector('.rg-part').textContent = `Part ${groupNum(n.num)}`;
        g.querySelector('.rg-t').textContent = n.group;
        ol.appendChild(g);
      }
      lastGroup = n.group;
      const li = document.createElement('li');
      li.className = n.group ? 'rail-item sub' : 'rail-item';
      li.innerHTML = `<a class="rail-note" href="#${n.key}"><span class="rn-num"></span><span class="rn-t"></span><span class="rn-pp"></span></a><ol class="rail-toc" hidden></ol>`;
      const a = li.querySelector('.rail-note');
      a.dataset.note = n.key;
      a.title = n.title;
      li.querySelector('.rn-num').textContent = n.num;
      li.querySelector('.rn-t').textContent = n.short;
      li.querySelector('.rn-pp').textContent = n.pages;
      ol.appendChild(li);
    });
    const h = sec.querySelector('.rail-col-h');
    h.addEventListener('click', () => showCol(sec, h.getAttribute('aria-expanded') !== 'true'));
    tree.appendChild(sec);
  });

  // the rail's collections fold; one is open at a time
  function showCol(sec, open) {
    tree.querySelectorAll('.rail-col').forEach((other) => {
      const on = other === sec ? open : false;
      other.querySelector('.rail-col-h').setAttribute('aria-expanded', String(on));
      other.querySelector(':scope > ol').hidden = !on;
    });
  }

  // ---- reading
  let current = null; // the open note
  let page = 1;
  let tocLinks = [];

  const fillToc = (n) => {
    tree.querySelectorAll('.rail-toc').forEach((t) => { t.hidden = true; t.innerHTML = ''; });
    tree.querySelectorAll('.rail-note').forEach((a) => {
      const on = a.dataset.note === n.key;
      a.classList.toggle('current', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    const link = tree.querySelector(`.rail-note[data-note="${n.key}"]`);
    const toc = link.nextElementSibling;
    n.toc.forEach(([lvl, t, p]) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#${n.key}/p${p}`;
      a.className = `rt-${lvl}`;
      a.textContent = t;
      a.dataset.page = p;
      li.appendChild(a);
      toc.appendChild(li);
    });
    toc.hidden = !n.toc.length;
    tocLinks = [...toc.querySelectorAll('a')];
    // the note's collection is the open one
    showCol(link.closest('.rail-col'), true);
    link.scrollIntoView({ block: 'nearest' });
  };

  const markToc = (p) => {
    let here = null;
    for (const a of tocLinks) { if (Number(a.dataset.page) <= p) here = a; else break; }
    tocLinks.forEach((a) => a.classList.toggle('here', a === here));
    if (here) {
      const r = here.getBoundingClientRect(), box = rail.getBoundingClientRect();
      if (r.top < box.top + 120 || r.bottom > box.bottom - 20) here.scrollIntoView({ block: 'nearest' });
    }
  };

  const neighbour = (n, d) => notes[notes.indexOf(n) + d];

  const open = (n, p) => {
    root.classList.add('lib-reading');
    closeRail();
    upNext.hidden = true;
    if (current !== n) {
      current = n;
      page = p || 1;
      frame.src = `${n.key}/${page > 1 ? `#p${page}` : ''}`;
      fillToc(n);
      stageTitle.textContent = label(n);
      document.title = `${n.title} · Notes`;
    } else if (p && p !== page) {
      frame.contentWindow?.postMessage({ type: 'notes-go', n: p }, location.origin);
    }
    markToc(page);
  };

  const showUpNext = () => {
    const nx = neighbour(current, 1);
    if (!nx || upNext.dataset.dismissed === current.key) { upNext.hidden = true; return; }
    upLink.textContent = nx.col === current.col ? label(nx) : `${nx.col.title}: ${label(nx)}`;
    upLink.href = `#${nx.key}`;
    upNext.hidden = false;
  };
  upNext.querySelector('.un-close').addEventListener('click', () => { upNext.dataset.dismissed = current.key; upNext.hidden = true; });

  addEventListener('message', (e) => {
    if (e.origin !== location.origin || e.source !== frame.contentWindow || e.data?.type !== 'notes-page' || !current) return;
    if (!e.data.path?.endsWith(`/${current.key}/`)) return; // a note still unloading after a switch
    page = e.data.n;
    markToc(page);
    history.replaceState(null, '', `#${current.key}${page > 1 ? `/p${page}` : ''}`);
    if (e.data.last) showUpNext(); else upNext.hidden = true;
  });

  // the frame follows the site theme without reloading
  new MutationObserver(() => {
    const doc = frame.contentDocument;
    if (doc?.documentElement) doc.documentElement.dataset.theme = root.dataset.theme;
  }).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
  frame.addEventListener('load', () => {
    const doc = frame.contentDocument;
    if (doc?.documentElement) doc.documentElement.dataset.theme = root.dataset.theme;
  });

  // ---- routing: #collection/note[/pN] reads a note; anything else is the library
  const route = () => {
    const m = location.hash.match(/^#([a-z0-9-]+\/[a-z0-9]+)(?:\/p(\d+))?$/);
    const n = m && byKey.get(m[1]);
    if (n) { open(n, m[2] ? Number(m[2]) : 1); return; }
    root.classList.remove('lib-reading');
    current = null;
    frame.removeAttribute('src');
    document.title = 'Notes · Nguyễn Khôi Nguyên (Alan)';
  };
  addEventListener('hashchange', route);

  // ---- search: note titles, summaries and every section heading, across all collections
  const index = notes.flatMap((n) => [
    { n, p: 1, text: `${n.num} ${n.short} ${n.group || ''} ${n.col.title} ${n.summary}`, head: label(n), sub: n.col.title },
    ...n.toc.map(([, t, p]) => ({ n, p, text: t, head: t, sub: `Notes ${n.num} · page ${p}` })),
  ]);
  const norm = (s) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '');
  let hits = [], active = -1;
  const showHits = () => {
    results.innerHTML = '';
    hits.forEach((h, i) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#${h.n.key}/p${h.p}`;
      a.className = i === active ? 'active' : '';
      a.innerHTML = '<span class="rr-h"></span><span class="rr-s"></span>';
      a.querySelector('.rr-h').textContent = h.head;
      a.querySelector('.rr-s').textContent = h.sub;
      a.addEventListener('click', () => { search.value = ''; runSearch(); });
      li.appendChild(a);
      results.appendChild(li);
    });
    if (!hits.length) results.innerHTML = '<li class="rr-none">No matches</li>';
  };
  const runSearch = () => {
    const words = norm(search.value).split(/\s+/).filter(Boolean);
    tree.hidden = !!words.length;
    results.hidden = !words.length;
    if (!words.length) return;
    hits = index.filter((x) => { const t = norm(x.text); return words.every((w) => t.includes(w)); }).slice(0, 40);
    active = hits.length ? 0 : -1;
    showHits();
  };
  search.addEventListener('input', runSearch);
  search.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!hits.length) return;
      active = (active + (e.key === 'ArrowDown' ? 1 : -1) + hits.length) % hits.length;
      showHits();
      results.querySelector('.active')?.scrollIntoView({ block: 'nearest' });
    }
    if (e.key === 'Enter' && hits[active]) {
      location.hash = `${hits[active].n.key}/p${hits[active].p}`;
      search.value = '';
      runSearch();
    }
    if (e.key === 'Escape') { search.value = ''; runSearch(); search.blur(); }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && root.classList.contains('lib-reading') && document.activeElement !== search) {
      e.preventDefault();
      openRail();
      search.focus();
    }
    if (e.key === 'Escape') closeRail();
  });

  // ---- small screens: the rail is a drawer
  function openRail() { rail.classList.add('open'); railOpen.setAttribute('aria-expanded', 'true'); }
  function closeRail() { rail.classList.remove('open'); railOpen.setAttribute('aria-expanded', 'false'); }
  railOpen.addEventListener('click', openRail);
  rail.querySelector('.rail-close').addEventListener('click', closeRail);
  rail.querySelector('.rail-back').addEventListener('click', (e) => { e.preventDefault(); history.pushState(null, '', location.pathname); route(); });

  route();
})();
