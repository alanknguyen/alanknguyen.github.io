"""Render a notes PDF into page images, an index (outline, labels, links) and the notes page.

usage: python3 tools/notes_pages.py notes-src/ec562.pdf notes/ec562 [--dpi 175] [--watermark] [--page-only]
The page text (title, course, term, lecturer) comes from tools/notes.json, keyed by the output folder's path
under notes/ (notes/ec562 -> "ec562", notes/ec701/1 -> "ec701/1").
"""
import argparse
import hashlib
import html
import io
import json
import os
import sys
from string import Template
from multiprocessing import Pool

import fitz
from PIL import Image, ImageDraw, ImageFont

FONT = '/System/Library/Fonts/Supplemental/Verdana.ttf'
MARK = 'alanknguyen.com'
HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(HERE, '..', 'notes')
VERSIONS = {'css_v': '43', 'js_v': '18', 'notes_v': '10'}


def watermark(im, alpha=18):
    w, h = im.size
    layer = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(FONT, int(w * 0.028))
    step_x, step_y = int(d.textlength(MARK, font=f) * 1.9), int(w * 0.16)
    for row, y in enumerate(range(0, h * 2, step_y)):
        for x in range(-step_x + (row % 2) * step_x // 2, w * 2, step_x):
            d.text((x, y), MARK, font=f, fill=(90, 100, 120, alpha))
    layer = layer.rotate(30, resample=Image.BICUBIC).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))
    return Image.alpha_composite(im.convert('RGBA'), layer).convert('RGB')


def render(job):
    pdf, out, dpi, mark, i = job
    page = fitz.open(pdf)[i]
    im = Image.open(io.BytesIO(page.get_pixmap(dpi=dpi).tobytes('png'))).convert('RGB')
    if mark:
        im = watermark(im)
    path = os.path.join(out, f'p{i + 1:03d}.webp')
    im.save(path, quality=82, method=6)
    return os.path.getsize(path)


def index(pdf):
    doc = fitz.open(pdf)
    w, h = doc[0].rect.width, doc[0].rect.height
    r = lambda v: round(v, 4)
    toc = doc.get_toc(simple=True)
    # every internal link (contents, figures, equations, tables, ...) gets a clickable box
    links = {}
    for i, page in enumerate(doc):
        out = []
        for l in page.get_links():
            if l.get('page', -1) < 0:
                continue
            a, to = l['from'], l.get('to')
            y = r(min(max((h - to.y) / h, 0), 1)) if to is not None else 0
            out.append([r(a.x0 / w), r(a.y0 / h), r((a.x1 - a.x0) / w), r((a.y1 - a.y0) / h), l['page'] + 1, y])
        if out:
            links[i + 1] = out
    return {
        'count': len(doc),
        'size': [round(w), round(h)],
        'labels': [p.get_label() or str(i + 1) for i, p in enumerate(doc)],
        'toc': [[lvl, title, pg] for lvl, title, pg in toc if lvl <= 2],
        'links': links,
    }


def note_key(out):
    return os.path.relpath(os.path.abspath(out), os.path.abspath(NOTES)).replace(os.sep, '/')


def write_page(out, meta, build):
    key = note_key(out)
    info = json.load(open(os.path.join(HERE, 'notes.json'))).get(key)
    if not info:
        print(f'no entry for "{key}" in tools/notes.json, skipping the page')
        return
    values = {k: html.escape(v) for k, v in info.items() if isinstance(v, str)}
    root = os.path.relpath(os.path.join(HERE, '..'), os.path.abspath(out)).replace(os.sep, '/') + '/'
    values.update(VERSIONS, root=root, build=build, count=meta['count'], w=meta['size'][0], h=meta['size'][1])
    page = Template(open(os.path.join(HERE, 'notes_page.tmpl')).read()).substitute(values)
    with open(os.path.join(out, 'index.html'), 'w') as f:
        f.write(page)
    print(f'page -> {os.path.join(out, "index.html")}')


def fill_home(key, name, block):
    home = os.path.join(HERE, '..', 'index.html')
    start, end = f'<!-- {name}:{key} -->', f'<!-- /{name}:{key} -->'
    page = open(home).read()
    if start not in page or end not in page:
        print(f'no {start} block in index.html, skipping')
        return
    a, b = page.index(start) + len(start), page.index(end)
    with open(home, 'w') as f:
        f.write(page[:a] + '\n' + block + page[b:])
    print(f'home {name} -> index.html')


def write_home(key, info, count):
    """Home entry blocks: the source line under the authors, and More info (fields, then one paragraph)."""
    e = lambda v: html.escape(v, quote=False)
    sources = info.get('sources', [])
    if sources:
        label = 'Main source' if len(sources) == 1 else 'Main sources'
        fill_home(key, 'sources', f'          <p class="venue">{label}: {"; ".join(e(x) for x in sources)}</p>\n')
    fields = [('Pages', str(count))] + ([('Draft', info['draft'])] if info.get('draft') else [])
    if info.get('textbook'):
        fields.append(('Textbook', info['textbook']))
    rows = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in fields)
    para = []
    if info.get('book'):
        para.append(f"Part of <i>{e(info['book'])}</i>" + (f", {e(info['book_status'])}" if info.get('book_status') else '') + '.')
    if info.get('about'):
        para.append(e(info['about']))
    block = f'            <dl class="info-list">{rows}</dl>\n'
    if para:
        block += f'            <p>{" ".join(para)}</p>\n'
    fill_home(key, 'info', block)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('out')
    ap.add_argument('--dpi', type=int, default=175)
    ap.add_argument('--watermark', action='store_true')
    ap.add_argument('--page-only', action='store_true', help='only rebuild index.json and index.html')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n = len(fitz.open(a.pdf))
    if not a.page_only:
        with Pool() as pool:
            sizes = pool.map(render, [(a.pdf, a.out, a.dpi, a.watermark, i) for i in range(n)])
        print(f'{n} pages -> {a.out} ({sum(sizes) / 1e6:.1f} MB)')
    meta = index(a.pdf)
    data = json.dumps(meta, separators=(',', ':'), ensure_ascii=False)
    with open(os.path.join(a.out, 'index.json'), 'w') as f:
        f.write(data)
    nlinks = sum(len(v) for v in meta['links'].values())
    print(f"index: {len(meta['toc'])} outline entries, {nlinks} links")
    # build stamp from the PDF and the index, so a rebuild busts cached page images and index.json
    build = hashlib.sha1(open(a.pdf, 'rb').read() + data.encode()).hexdigest()[:8]
    write_page(a.out, meta, build)
    key = note_key(a.out)
    info = json.load(open(os.path.join(HERE, 'notes.json'))).get(key)
    if info:
        write_home(key, info, meta['count'])


if __name__ == '__main__':
    sys.exit(main())
