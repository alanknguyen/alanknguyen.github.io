"""Build the notes library page, notes/index.html: every collection with its notes, and a reader that
switches between notes in place.

usage: python3 tools/notes_library.py
Collections (title, year, lecturer, thumbnail, summary) come from tools/notes_collections.json; each note's
title and summary from tools/notes.json (short names and part headings from the collection); pages and outline from notes/<collection>/<note>/index.json.
notes_pages.py runs this after every rebuild, so the page stays in step with the notes.
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
NOTES = os.path.join(ROOT, 'notes')
LIB_V = '4'  # library.css and library.js; the site's css and js versions come from notes_pages.VERSIONS
DISCLAIMER = ('These are my own notes from courses and reading, written mainly for my own reference. '
              'They&rsquo;re working drafts, so expect gaps and errors.')

e = lambda v: html.escape(str(v), quote=False)
a = lambda v: html.escape(str(v), quote=True)


def order(num):
    m = re.match(r'(\d+)(.*)', num)
    return (int(m.group(1)), m.group(2)) if m else (0, num)


def split_title(title):
    """'EC 701 Notes 3a: Linear System Preliminaries: Solving Linear Systems' -> ('3a', 'Linear System Preliminaries', 'Solving Linear Systems')"""
    m = re.match(r'.*?Notes (\w+):\s*(.*)', title)
    num, rest = (m.group(1), m.group(2)) if m else ('', title)
    if re.search(r'\d[a-z]$', num) and ':' in rest:
        group, short = (s.strip() for s in rest.split(':', 1))
        return num, group, short[:1].upper() + short[1:]
    return num, None, rest


def collect():
    info = json.load(open(os.path.join(HERE, 'notes.json')))
    out = []
    for c in json.load(open(os.path.join(HERE, 'notes_collections.json'))):
        notes = []
        for key, meta in info.items():
            if not key.startswith(c['key'] + '/'):
                continue
            idx = os.path.join(NOTES, key, 'index.json')
            if not os.path.exists(idx):
                continue
            ix = json.load(open(idx))
            num, group, short = split_title(meta['title'])
            # short names and part headings chosen in notes_collections.json win over the parsed title
            nid = key.split('/', 1)[1]
            short = c.get('names', {}).get(nid, short)
            group = c.get('groups', {}).get(re.sub(r'[a-z]+$', '', nid)) if re.search(r'\d[a-z]$', nid) else None
            notes.append({
                'key': key, 'id': key.split('/', 1)[1], 'num': num, 'group': group, 'short': short,
                'title': meta['title'], 'summary': meta.get('summary', ''), 'pages': ix['count'],
                'toc': [[lvl, t, p] for lvl, t, p in ix['toc']],
            })
        notes.sort(key=lambda n: order(n['id']))
        out.append({**c, 'notes': notes, 'pages': sum(n['pages'] for n in notes)})
    return out


def parts(c):
    """the notes of a collection: numbered parts gathered into blocks under their shared heading"""
    blocks = []  # [(heading or None, [notes])]
    for n in c['notes']:
        if blocks and n['group'] and blocks[-1][0] == n['group']:
            blocks[-1][1].append(n)
        else:
            blocks.append((n['group'], [n]))
    out = []
    for group, ns in blocks:
        head = ''
        if group:
            part = ns[0]['num'].rstrip('abcdefgh')
            head = f'<p class="lp-head"><span class="lp-part">Part {e(part)}</span>{e(group)}</p>'
        rows = ''.join(
            f'<li><a href="#{a(n["key"])}" title="{a(n["summary"])}">'
            f'<span class="lp-num">{e(n["num"])}</span><span class="lp-t">{e(n["short"])}</span>'
            f'<span class="lp-pp">{n["pages"]} pp</span></a></li>' for n in ns)
        out.append(f'          <div class="lp-block">{head}<ol>{rows}</ol></div>')
    return '\n'.join(out)


def tags(c):
    return '\n'.join(f'            <li class="tag tag-{a(k)}">{e(t)}</li>' for t, k in c.get('tags', []))


def info(c):
    rows = []
    if c.get('course'):
        rows.append(('Main source', e(c['course'])))
    if c.get('sources'):
        rows.append(('Primary source' if len(c['sources']) == 1 else 'Primary sources', '<br>'.join(e(x) for x in c['sources'])))
    return ''.join(f'<div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)


def card(c):
    first = c['notes'][0]['key'] if c['notes'] else ''
    return f'''      <li class="entry" id="{a(c['key'])}">
        <div class="thumb-col">
          <a class="thumb wide" href="#{a(first)}" tabindex="-1" aria-hidden="true">
            <img src="../{a(c['thumb'])}" data-gif="../{a(c['gif'])}" alt="{a(c['alt'])}" width="1200" height="600" loading="lazy">
          </a>
          <ul class="tags" aria-label="Categories">
{tags(c)}
          </ul>
        </div>
        <div class="entry-body">
          <h3><a href="#{a(first)}">{e(c['title'])}</a></h3>
          <p class="authors">NK Nguyen, scribe. Lectures by <a class="plain" href="{a(c['lecturer_url'])}">{e(c['lecturer'])}</a>.</p>
          <p class="venue">{e(c['year'])} · {len(c['notes'])} notes · {c['pages']} pages</p>
          <p class="summary">{c['summary']}</p>
          <p class="entry-links">
            <a class="lib-start" href="#{a(first)}">Start reading</a>
            <button type="button" class="lib-toggle" data-panel="{a(c['key'])}-notes" aria-controls="{a(c['key'])}-notes" aria-expanded="false">{len(c['notes'])} notes</button>
            <button type="button" class="lib-toggle" data-panel="{a(c['key'])}-info" aria-controls="{a(c['key'])}-info" aria-expanded="false">More info</button>
          </p>
        </div>
        <div class="entry-extra lib-panel lib-parts" id="{a(c['key'])}-notes" hidden>
{parts(c)}
        </div>
        <div class="entry-extra lib-panel more-info" id="{a(c['key'])}-info" hidden>
          <dl class="info-list">{info(c)}</dl>
        </div>
      </li>'''


PAGE = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
  <title>Notes · Nguyễn Khôi Nguyên (Alan)</title>
  <meta name="description" content="Working notes by Nguyễn Khôi Nguyên (Alan) on optimal and robust control, dynamic programming and stochastic control.">
  <link rel="canonical" href="https://alanknguyen.com/notes/">
  <link rel="icon" href="../favicon.ico?v=3" sizes="any">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png?v=3">
  <link rel="stylesheet" href="../css/site.css?v=@css_v@">
  <link rel="stylesheet" href="../css/library.css?v=@lib_v@">
  <script>
    var t = null; try { t = localStorage.getItem('theme'); } catch (e) {} document.documentElement.dataset.theme = t || 'light';
    // open straight into the reader when the address names a note, so the library never flashes
    if (/^#[a-z0-9-]+\\/[a-z0-9]+/.test(location.hash)) document.documentElement.classList.add('lib-reading');
  </script>
</head>
<body class="lib-body">
<a class="skip" href="#library">Skip to content</a>
<button type="button" class="theme-toggle" data-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
  <svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>
</button>

<main class="page lib-home" id="library">
  <p class="lib-crumb"><a href="../">Nguyễn Khôi Nguyên (Alan)</a></p>
  <h1 class="lib-h1">Notes</h1>
  <p class="section-note">@disclaimer@</p>
  <ol class="entries lib-collections">
@cards@
  </ol>
</main>

<div class="lib-reader" aria-label="Note reader">
  <aside class="lib-rail" id="lib-rail" aria-label="All notes">
    <div class="rail-head">
      <a class="rail-back" href="./">&larr; All notes</a>
      <button type="button" class="rail-close" aria-label="Close the notes list">&times;</button>
    </div>
    <label class="rail-search"><span class="sr">Search all notes</span>
      <input type="search" placeholder="Search all notes" autocomplete="off" spellcheck="false">
      <kbd>/</kbd>
    </label>
    <ol class="rail-results" hidden></ol>
    <nav class="rail-tree"></nav>
  </aside>
  <div class="lib-stage">
    <div class="stage-top">
      <button type="button" class="rail-open" aria-controls="lib-rail" aria-expanded="false">
        <svg viewBox="0 0 20 14" width="18" height="13" aria-hidden="true"><path d="M1 1h18M1 7h18M1 13h18"/></svg> Notes
      </button>
      <span class="stage-title"></span>
    </div>
    <iframe class="lib-frame" title="Note reader"></iframe>
    <div class="up-next" hidden>
      <span class="un-label">Up next</span>
      <a class="un-link" href="#"></a>
      <button type="button" class="un-close" aria-label="Dismiss">&times;</button>
    </div>
  </div>
</div>

<noscript><style>.lib-reader{display:none}</style></noscript>
<script type="application/json" id="lib-data">@data@</script>
<script src="../js/site.js?v=@js_v@"></script>
<script src="../js/library.js?v=@lib_v@"></script>
</body>
</html>
'''


def build():
    cols = collect()
    data = [{'key': c['key'], 'title': c['title'], 'year': c['year'],
             'notes': [{k: n[k] for k in ('key', 'id', 'num', 'group', 'short', 'title', 'summary', 'pages', 'toc')} for n in c['notes']]}
            for c in cols]
    from notes_pages import VERSIONS
    page = PAGE
    values = {**VERSIONS, 'lib_v': LIB_V, 'disclaimer': DISCLAIMER, 'cards': '\n'.join(card(c) for c in cols),
              'data': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')}
    for k, v in values.items():
        page = page.replace(f'@{k}@', v)
    with open(os.path.join(NOTES, 'index.html'), 'w') as f:
        f.write(page)
    print(f'library -> notes/index.html ({sum(len(c["notes"]) for c in cols)} notes in {len(cols)} collections)')


if __name__ == '__main__':
    build()
