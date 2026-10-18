"""EC 701 thumbnail: minimum-time landing on a loop.

usage: python3 tools/thumb_lander.py   (writes img/thumbs/ec701-lander.webp and .gif)
Accel is -1 with the engine off and +1 at full burn. Each hop: burn up from rest on the pad, then the
time-optimal landing (coast, one switch on h = v^2/2, burn). In the (v, h) phase plane every hop is a closed
teardrop through the origin, so the gif loops seamlessly.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'img', 'thumbs')

import numpy as np

BG = (8, 20, 36)
MINT = (150, 240, 200)
PALE = (230, 242, 250)
BLUE = (70, 130, 190)
AMBER = (255, 200, 110)



class Canvas:
    """draw on a black line layer at ss x supersampling, then add bloom over the background"""

    def __init__(self, w, h, ss=2):
        self.w, self.h, self.ss = w, h, ss
        self.W, self.H = w * ss, h * ss
        self.lines = Image.new('RGB', (self.W, self.H), (0, 0, 0))
        self.d = ImageDraw.Draw(self.lines, 'RGBA')
        self.base = Image.new('RGB', (self.W, self.H), BG)
        self.bd = ImageDraw.Draw(self.base, 'RGBA')   # unbloomed layer (text, faint fills)
        self.lw = max(1, round(self.W / 650))

    def finish(self, glow_bg=False, bloom=0.9):
        im = self.base
        if glow_bg:
            v = Image.new('L', (self.W, self.H), 0)
            ImageDraw.Draw(v).ellipse([self.W * 0.1, -self.H * 0.1, self.W * 0.9, self.H * 1.1], fill=45)
            im = Image.composite(Image.new('RGB', im.size, (22, 55, 85)), im, v.filter(ImageFilter.GaussianBlur(self.W * 0.1)))
        b = self.lines.filter(ImageFilter.GaussianBlur(self.lw * 3))
        out = np.clip(np.asarray(im, float) + np.asarray(self.lines, float) + bloom * np.asarray(b, float), 0, 255)
        return Image.fromarray(out.astype(np.uint8)).resize((self.w, self.h), Image.LANCZOS)


def save_gif(frames, path, fps, colors=64, ref=None):
    ref = frames[len(frames) // 2] if ref is None else ref
    pal = ref.quantize(colors=colors, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=round(1000 / fps), loop=0, optimize=True)
    print(f'{len(q)} frames -> {path} ({os.path.getsize(path) / 1e6:.2f} MB)')

DT = 2e-3
HOPS = [1.5, 2.1, 1.1]          # launch burn durations
MATH = ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia Italic.ttf', 10)


def T(h, v):
    s = h + v * abs(v) / 2
    return v + 2 * np.sqrt(h + v * v / 2) if s >= 0 else -v + 2 * np.sqrt(-h + v * v / 2)


def hop(tau):
    """rest -> burn up for tau -> min-time landing; rows (h, v, u)"""
    out, h, v, t = [], 0.0, 0.0, 0.0
    while t < tau:
        out.append((h, v, 1.0))
        h, v, t = h + v * DT + DT * DT / 2, v + DT, t + DT
    t_land, burning = T(h, v), False
    while len(out) < 40000:
        if not burning and v < 0 and h <= v * v / 2:
            burning = True
        u = 1.0 if burning else -1.0
        out.append((h, v, u))
        if burning and v >= 0:
            break
        h, v = h + v * DT + u * DT * DT / 2, v + u * DT
    out = np.array(out)
    out[-1] = (0.0, 0.0, 0.0)
    return out, t_land


RUNS = []
for tau in HOPS:
    r, t_land = hop(tau)
    landing = len(r) * DT - tau
    print(f'hop tau={tau}: landing {landing:.3f} s vs closed form {t_land:.3f} s, apex h={r[:, 0].max():.3f}')
    RUNS.append(r)

HMAX = max(r[:, 0].max() for r in RUNS) * 1.12
VMAX = max(np.abs(r[:, 1]).max() for r in RUNS) * 1.25


def arrow(c, p0, p1, col, lw):
    c.d.line([p0, p1], fill=col, width=lw)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = np.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    s = lw * 2.5
    c.d.polygon([p1, (p1[0] - ux * s * 1.6 - uy * s, p1[1] - uy * s * 1.6 + ux * s),
                 (p1[0] - ux * s * 1.6 + uy * s, p1[1] - uy * s * 1.6 - ux * s)], fill=col)


def frame(w, h, run, i, glow_bg=False):
    c = Canvas(w, h)
    W, H, lw = c.W, c.H, c.lw
    hh, vv, u = run[i]

    # lander on the left
    gx0, gx1 = W * 0.05, W * 0.47
    gy = H * 0.88
    sc = (gy - H * 0.10) / HMAX
    cx = (gx0 + gx1) / 2
    c.d.line([(gx0, gy), (gx1, gy)], fill=BLUE + (220,), width=lw * 2)
    c.d.line([(cx - W * 0.06, gy - lw), (cx + W * 0.06, gy - lw)], fill=AMBER + (240,), width=lw * 3)
    by = gy - hh * sc
    bw, bh = W * 0.05, H * 0.13
    if u > 0:  # flame, flickering
        L = bh * (0.95 + 0.3 * np.sin(i * 1.9))
        top = by - bh * 0.22
        L = min(L, gy - top - lw)   # the ground stops the plume
        c.d.polygon([(cx - bw * 0.42, top), (cx + bw * 0.42, top), (cx, top + L)], fill=AMBER + (255,))
        c.d.polygon([(cx - bw * 0.2, top), (cx + bw * 0.2, top), (cx, top + L * 0.55)], fill=(255, 246, 225, 255))
    c.d.polygon([(cx - bw / 2, by - bh), (cx + bw / 2, by - bh), (cx + bw * 0.62, by - bh * 0.25), (cx - bw * 0.62, by - bh * 0.25)], fill=PALE + (255,))
    for sgn in (-1, 1):
        c.d.line([(cx + sgn * bw * 0.5, by - bh * 0.3), (cx + sgn * bw * 0.95, by - lw)], fill=PALE + (255,), width=lw * 2)
    c.d.ellipse([cx - bw * 0.2, by - bh * 0.85, cx + bw * 0.2, by - bh * 0.62], fill=(40, 90, 140, 255))

    # phase plane on the right: v across, h up
    px0, px1, py0, py1 = W * 0.56, W * 0.93, H * 0.14, H * 0.88
    pcx = (px0 + px1) / 2
    Pp = lambda v, hgt: (pcx + v / VMAX * (px1 - px0) / 2, py1 - hgt / HMAX * (py1 - py0))
    axis = (150, 180, 210, 255)
    arrow(c, Pp(-VMAX, 0), (px1 + W * 0.02, py1), axis, lw * 2)
    arrow(c, Pp(0, 0), (pcx, py0 - H * 0.05), axis, lw * 2)
    vs = np.linspace(-VMAX * 0.97, 0, 120)
    c.d.line([Pp(v, v * v / 2) for v in vs if v * v / 2 <= HMAX], fill=AMBER + (210,), width=lw * 2, joint='curve')
    seg = run[:i + 1:6]
    if len(seg) > 1:
        c.d.line([Pp(v, x) for x, v, _ in seg] + [Pp(vv, hh)], fill=MINT + (240,), width=lw * 3, joint='curve')
    q = Pp(vv, hh)
    r = lw * 4.5
    c.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=(AMBER if u > 0 else PALE) + (255,))
    f = MATH.font_variant(size=int(H * 0.09))
    c.bd.text((px1 + W * 0.005, py1 - H * 0.125), 'v', font=f, fill=PALE + (240,))
    c.bd.text((pcx + W * 0.02, py0 - H * 0.085), 'h', font=f, fill=PALE + (240,))
    return c.finish(glow_bg=glow_bg)


def main(out):
    r = RUNS[1]
    burn = np.where(r[:, 2] > 0)[0]
    last_burn = burn[burn > len(r) // 2]
    frame(1200, 630, r, int(last_burn[0] + 0.4 * (last_burn[-1] - last_burn[0])), glow_bg=True).save(os.path.join(out, 'ec701-lander.webp'), quality=88)
    fps, speed, rest = 20, 1.9, 0.45
    frames = []
    for run in RUNS:
        n = len(run)
        steps = int(n * DT / speed * fps)
        frames += [frame(440, 220, run, min(n - 1, int(k * speed / fps / DT))) for k in range(steps)]
        frames += [frame(440, 220, run, n - 1)] * int(rest * fps)     # landed, engine off, teardrop closed
    save_gif(frames, os.path.join(out, 'ec701-lander.gif'), fps, ref=frames[len(frames) // 2])


if __name__ == '__main__':
    main(OUT)
