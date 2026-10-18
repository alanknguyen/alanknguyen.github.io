"""EC 701 thumbnail: the HJB value function of the minimum-time double integrator, with optimal paths rolling in.

usage: python3 tools/thumb_hjb.py   (writes img/thumbs/ec701-hjb.webp and .gif)
System x1' = x2, x2' = u, |u| <= 1. The time-to-go T(x) is known in closed form and is creased along the
switching curve x1 = -x2|x2|/2. Optimal paths (bang-bang, at most one switch) lose exactly one unit of T per
second, so a marble released T(x0) seconds before a common finish time arrives with all the others.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'img', 'thumbs')

A1, A2 = 3.0, 2.2                     # state-space patch |x1| <= A1, |x2| <= A2
SX, SY, SZ = 1 / A1, 1 / A2, 0.17     # display scaling of x1, x2 and T
EL = 0.90                             # camera elevation (rad)


def T(x1, x2):
    s = x1 + x2 * np.abs(x2) / 2          # > 0 above the switching curve
    up = x2 + 2 * np.sqrt(np.maximum(x1 + x2 ** 2 / 2, 0))
    dn = -x2 + 2 * np.sqrt(np.maximum(-x1 + x2 ** 2 / 2, 0))
    return np.where(s >= 0, up, dn)


def optimal_path(x0, dt=1e-3):
    """bang-bang: u = -1 above the switching curve, +1 below, then ride the curve in"""
    x = np.array(x0, float)
    pts = [x.copy()]
    switched = False
    while np.hypot(*x) > 2e-3 and len(pts) < 20000:
        s = x[0] + x[1] * abs(x[1]) / 2
        if not switched and abs(s) < 2e-3:
            switched = True
        u = -np.sign(x[1]) if switched else -np.sign(s)
        x = x + dt * np.array([x[1], u]) + dt ** 2 / 2 * np.array([u, 0])
        pts.append(x.copy())
    return np.array(pts)


def level_set(c, n=360):
    """T = c as a closed curve (the sublevel sets are star-shaped about the origin)"""
    th = np.linspace(0, 2 * np.pi, n + 1)
    d = np.stack([np.cos(th) * A1, np.sin(th) * A2], 1)
    lo, hi = np.zeros(n + 1), np.full(n + 1, 8.0)
    for _ in range(45):
        m = (lo + hi) / 2
        inside = T(m * d[:, 0], m * d[:, 1]) < c
        lo, hi = np.where(inside, m, lo), np.where(inside, hi, m)
    return lo[:, None] * d


def project(x1, x2, z, az):
    X, Y = x1 * SX, x2 * SY
    ca, sa = np.cos(az), np.sin(az)
    px, py = ca * X - sa * Y, sa * X + ca * Y
    return px, -(py * np.sin(EL) + z * SZ * np.cos(EL)), py    # screen x, screen y (up is negative), depth


BG = (8, 20, 36)
MESH = np.array([50, 110, 165])
LOW, HIGH = np.array([60, 205, 150]), np.array([230, 242, 250])
CREASE = (255, 200, 110)
MARBLE = (240, 255, 248)
TRAIL = (120, 235, 185)


def mix(a, b, t):
    return tuple(int(v) for v in a + (b - a) * t)


class Scene:
    def __init__(self):
        self.tmax = float(T(np.array(A1), np.array(A2)))
        self.levels = np.arange(0.5, self.tmax, 0.5)
        self.sets = {c: level_set(c) for c in self.levels}
        t = np.linspace(-1, 1, 120)
        self.mesh = [(np.full_like(t, v * A1), t * A2) for v in np.linspace(-1, 1, 21)]
        self.mesh += [(t * A1, np.full_like(t, v * A2)) for v in np.linspace(-1, 1, 15)]
        sw = np.linspace(-A2, A2, 300)
        self.crease = (-sw * np.abs(sw) / 2, sw)
        # starts around the edge of the patch; each released T(x0) before the common finish
        starts = [(A1, 0.8), (A1, -1.6), (1.0, A2), (-1.4, A2), (-A1, 1.0), (-A1, -0.6), (-0.6, -A2), (1.8, -A2)]
        self.paths = [optimal_path(p) for p in starts]
        self.finish = max(len(p) for p in self.paths) * 1e-3

    def fit(self, W, H, azs=np.linspace(-0.75, -0.25, 7)):
        """scale and centre so the whole patch stays in frame over the camera's swing"""
        g = np.linspace(-1, 1, 41)
        x1, x2 = np.meshgrid(g * A1, g * A2)
        z = T(x1, x2)
        xs, ys = [], []
        for az in azs:
            sx, sy, _ = project(x1, x2, z, az)
            xs += [sx.min(), sx.max()]; ys += [sy.min(), sy.max()]
        x0, x1_, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        sc = min(W * 0.90 / (x1_ - x0), H * 0.88 / (y1 - y0))
        return sc, W / 2 - sc * (x0 + x1_) / 2, H / 2 - sc * (y0 + y1) / 2

    def draw(self, w, h, ss, az, reveal, clock, trail=1.0, glow=True, flash=0.0, fade=1.0):
        W, H = w * ss, h * ss
        sc, cx, cy = self.fit(W, H)
        lines = Image.new('RGB', (W, H), (0, 0, 0))
        d = ImageDraw.Draw(lines, 'RGBA')
        lw = max(1, round(W / 650))

        def P(x1, x2, z):
            sx, sy, dep = project(x1, x2, z, az)
            return cx + sx * sc, cy + sy * sc, dep

        def polyline(x1, x2, col, alpha, width, mask):
            z = T(x1, x2)
            sx, sy, dep = P(x1, x2, z)
            a = alpha * (0.5 + 0.5 * np.clip(0.5 - dep / 2, 0, 1)) * fade      # far side dimmer
            for i in range(1, len(sx)):
                if mask[i] and mask[i - 1]:
                    c = col if not callable(col) else col(z[i])
                    d.line([(sx[i - 1], sy[i - 1]), (sx[i], sy[i])], fill=c + (int(255 * a[i]),), width=width)

        # terrain mesh, coloured by height, grown outward from the origin
        for x1, x2 in self.mesh:
            polyline(x1, x2, lambda z: mix(MESH, LOW, min(z / self.tmax, 1) * 0.4), 0.22, lw, T(x1, x2) <= reveal)
        # level sets T = c inside the patch; the newest one flares as it appears
        for c in self.levels:
            if c > reveal:
                continue
            p = self.sets[c]
            inside = (np.abs(p[:, 0]) <= A1) & (np.abs(p[:, 1]) <= A2)
            edge = np.clip(1 - (reveal - c) / 0.8, 0, 1)
            polyline(p[:, 0], p[:, 1], mix(LOW, HIGH, c / self.tmax), 0.8 + 0.2 * edge, lw * (3 if edge > 0.3 else 2), inside)
        x1, x2 = self.crease
        polyline(x1, x2, CREASE, 0.9, lw * 2, (np.abs(x1) <= A1) & (T(x1, x2) <= reveal))

        # marbles roll on the surface; all finish at self.finish
        if clock is not None:
            for pts in self.paths:
                n = len(pts)
                i = int((clock - (self.finish - n * 1e-3)) / 1e-3)
                if i < 0:
                    continue
                i = min(i, n - 1)
                seg = pts[max(0, i - int(trail / 1e-3)):i + 1:15]
                if len(seg) > 1:
                    sx, sy, _ = P(seg[:, 0], seg[:, 1], T(seg[:, 0], seg[:, 1]))
                    m = len(sx)
                    for k in range(1, m):
                        d.line([(sx[k - 1], sy[k - 1]), (sx[k], sy[k])], fill=TRAIL + (int(235 * (k / m) ** 1.4 * fade),), width=lw * 3)
                p = pts[i]
                sx, sy, _ = P(p[0], p[1], T(p[0], p[1]))
                r = lw * 4.5
                d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=MARBLE + (int(255 * fade),))
        if flash > 0:
            sx, sy, _ = P(0.0, 0.0, 0.0)
            r = sc * (0.04 + 0.3 * (1 - flash))
            d.ellipse([sx - r, sy - r * np.sin(EL), sx + r, sy + r * np.sin(EL)], outline=(255, 225, 150, int(255 * flash)), width=lw * 2)

        im = Image.new('RGB', (W, H), BG)
        if glow:  # soft backdrop for the still; the gif stays flat so it doesn't band
            v = Image.new('L', (W, H), 0)
            ImageDraw.Draw(v).ellipse([W * 0.12, H * 0.0, W * 0.88, H * 1.05], fill=45)
            im = Image.composite(Image.new('RGB', (W, H), (22, 55, 85)), im, v.filter(ImageFilter.GaussianBlur(W * 0.1)))
        bloom = lines.filter(ImageFilter.GaussianBlur(lw * 3))
        out = np.clip(np.asarray(im, float) + np.asarray(lines, float) + 0.9 * np.asarray(bloom, float), 0, 255)
        return Image.fromarray(out.astype(np.uint8)).resize((w, h), Image.LANCZOS)


def main():
    sc = Scene()
    ends = [float(T(*p[0])) - len(p) * 1e-3 for p in sc.paths]
    print(f'T(x0) minus path time, per marble: max |error| {max(map(abs, ends)):.4f} s; finish at {sc.finish:.2f} s')

    sc.draw(1200, 630, 2, az=-0.5, reveal=sc.tmax, clock=sc.finish - 1.3, trail=2.5).save(
        os.path.join(OUT, 'ec701-hjb.webp'), quality=88, method=6)

    fps, speed = 20, 1.4
    build, pause, hold = 2.2, 0.2, 0.9
    roll = sc.finish / speed
    total = build + pause + roll + hold
    frames = []
    for i in range(int(total * fps)):
        t = i / fps
        az = -0.5 + 0.22 * np.sin(2 * np.pi * t / total)
        reveal = sc.tmax * min(1, t / build) ** 0.85 + 1e-9
        clock = None if t < build + pause else min((t - build - pause) * speed, sc.finish)
        after = t - (build + pause + roll)
        flash = max(0.0, 1 - after / 0.7) if after >= 0 else 0.0
        fade = 1.0 if t < total - 0.35 else max(0.0, (total - t) / 0.35)
        frames.append(sc.draw(440, 220, 2, az, reveal, clock, flash=flash, fade=fade, glow=False))
    pal = frames[int((build + pause + roll * 0.6) * fps)].quantize(colors=64, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    path = os.path.join(OUT, 'ec701-hjb.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=1000 // fps, loop=0, optimize=True)
    print(f'{len(q)} frames -> {path} ({os.path.getsize(path) / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
