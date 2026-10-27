"""EC 710 thumbnail: dynamic programming on a stochastic maze.

usage: python3 tools/thumb_dp.py   (writes img/thumbs/ec710-dp.webp and .gif)
Each move succeeds with probability P and otherwise the agent stays put (a slip). Value iteration
    J(x) <- min_u [ 1 + P J(f(x, u)) + (1 - P) J(x) ],   J(goal) = 0
gives the expected number of moves to go; the gif lights the maze up sweep by sweep as values settle, outward from
the goal, then traces the optimal policy from the start and lets the agent follow it, slips included. The still is
the gif's first frame.
"""
import os
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'img', 'thumbs')

CW, CH = 14, 7                     # maze cells (2:1, like the thumbnail)
MOVES = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # up, right, down, left
START, GOAL = (0, 0), (CW - 1, CH - 1)
P = 0.8                            # chance a move succeeds


def make_maze(seed=4, extra=7):
    """recursive backtracker, plus a few knocked-out walls so there are loops and more than one route"""
    rng = np.random.default_rng(seed)
    open_ = {(x, y): set() for x in range(CW) for y in range(CH)}
    seen, stack = {START}, [START]
    while stack:
        x, y = stack[-1]
        nb = [(d, (x + dx, y + dy)) for d, (dx, dy) in enumerate(MOVES)
              if 0 <= x + dx < CW and 0 <= y + dy < CH and (x + dx, y + dy) not in seen]
        if not nb:
            stack.pop()
            continue
        d, c = nb[rng.integers(len(nb))]
        open_[(x, y)].add(d); open_[c].add((d + 2) % 4)
        seen.add(c); stack.append(c)
    k = 0
    while k < extra:
        x, y = int(rng.integers(1, CW - 1)), int(rng.integers(1, CH - 1))
        d = int(rng.integers(4))
        if d not in open_[(x, y)]:
            dx, dy = MOVES[d]
            open_[(x, y)].add(d); open_[(x + dx, y + dy)].add((d + 2) % 4)
            k += 1
    return open_


def step(c, d):
    return (c[0] + MOVES[d][0], c[1] + MOVES[d][1])


def value_iteration(open_):
    """returns the value history (one array per sweep, inf where not yet reached) and the converged J"""
    J = np.full((CW, CH), np.inf)
    J[GOAL] = 0.0
    hist = [J.copy()]
    while True:
        Jn = J.copy()
        for c in open_:
            if c == GOAL:
                continue
            best = min(1 + P * J[step(c, d)] + (1 - P) * J[c] if np.isfinite(J[c]) else
                       (1 / P + J[step(c, d)]) for d in open_[c])
            Jn[c] = min(Jn[c], best)
        if np.allclose(np.nan_to_num(Jn, posinf=1e9), np.nan_to_num(J, posinf=1e9), atol=1e-9):
            return hist, J
        J = Jn
        hist.append(J.copy())


def policy_path(open_, J):
    path, c = [START], START
    while c != GOAL:
        c = step(c, min(open_[c], key=lambda d: J[step(c, d)]))
        path.append(c)
    return path


def bfs_len(open_):
    dist, q = {GOAL: 0}, deque([GOAL])
    while q:
        c = q.popleft()
        for d in open_[c]:
            n = step(c, d)
            if n not in dist:
                dist[n] = dist[c] + 1; q.append(n)
    return dist


BG = (8, 20, 36)
WALL = (55, 95, 140)
NEAR, FAR = np.array([255, 200, 110]), np.array([40, 120, 150])   # value tiles: amber near the goal, teal far
TRAIL = (110, 235, 190)
AGENT = (240, 255, 248)
GOALC = (225, 150, 50)       # deeper than it looks: the bloom lightens it


def render(w, h, open_, J, jmax, trail, agent, ss=2, goal_flash=0.0, fade=1.0, front=None):
    W, H = w * ss, h * ss
    pad = H * 0.06
    s = min((W - 2 * pad) / CW, (H - 2 * pad) / CH)
    ox, oy = (W - s * CW) / 2, (H - s * CH) / 2
    C = lambda c: (ox + (c[0] + 0.5) * s, oy + (c[1] + 0.5) * s)
    lines = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(lines, 'RGBA')
    base = Image.new('RGB', (W, H), BG)
    b = ImageDraw.Draw(base, 'RGBA')
    lw = max(1, round(s * 0.07))

    # value tiles: inset rounded squares, coloured by expected moves to go; the newest sweep flares
    if J is not None:
        g = s * 0.2
        for (x, y) in open_:
            v = J[x, y]
            if not np.isfinite(v):
                continue
            k = 1 - v / jmax
            col = tuple(int(c) for c in FAR + (NEAR - FAR) * k ** 1.5)
            a = 30 + 55 * k
            if front is not None and front[x, y]:
                a = 170
            b.rounded_rectangle([ox + x * s + g, oy + y * s + g, ox + (x + 1) * s - g, oy + (y + 1) * s - g],
                                radius=s * 0.15, fill=col + (int(a * fade),))
    for (x, y), ds in open_.items():
        x0, y0, x1, y1 = ox + x * s, oy + y * s, ox + (x + 1) * s, oy + (y + 1) * s
        a = int(220 * fade)
        if 0 not in ds: d.line([(x0, y0), (x1, y0)], fill=WALL + (a,), width=lw)
        if 3 not in ds: d.line([(x0, y0), (x0, y1)], fill=WALL + (a,), width=lw)
        if y == CH - 1: d.line([(x0, y1), (x1, y1)], fill=WALL + (a,), width=lw)
        if x == CW - 1: d.line([(x1, y0), (x1, y1)], fill=WALL + (a,), width=lw)
    if trail and len(trail) > 1:
        d.line([C(c) for c in trail], fill=TRAIL + (int(225 * fade),), width=lw * 3, joint='curve')
    gx, gy = C(GOAL)
    r = s * 0.3
    d.rectangle([gx - r, gy - r, gx + r, gy + r], fill=GOALC + (int(255 * fade),))
    if goal_flash > 0:
        rr = s * (0.4 + 1.2 * (1 - goal_flash))
        d.ellipse([gx - rr, gy - rr, gx + rr, gy + rr], outline=GOALC + (int(230 * goal_flash),), width=lw)
    if agent is not None:
        ax, ay = C(agent)
        r = s * 0.24
        d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=AGENT + (int(255 * fade),))
    bloom = lines.filter(ImageFilter.GaussianBlur(lw * 2.5))
    out = np.clip(np.asarray(base, float) + np.asarray(lines, float) + 0.8 * np.asarray(bloom, float), 0, 255)
    return Image.fromarray(out.astype(np.uint8)).resize((w, h), Image.LANCZOS)


def main():
    open_ = make_maze()
    hist, J = value_iteration(open_)
    dist = bfs_len(open_)
    path = policy_path(open_, J)
    err = max(abs(J[c] - dist[c] / P) for c in open_)
    print(f'{len(hist)} sweeps; J(start) = {J[START]:.2f} expected moves = shortest {dist[START]} / P; '
          f'max |J - dist/P| = {err:.1e}; policy path {len(path) - 1} moves')
    jmax = np.nanmax(J[np.isfinite(J)])

    # the run the agent takes: follow the policy, each move slipping with probability 1 - P (fixed seed)
    rng = np.random.default_rng(11)
    run, c = [START], START
    i = 0
    while c != GOAL:
        nxt = path[i + 1]
        if rng.random() < P:
            c = nxt; i += 1
        run.append(c)
    slips = len(run) - len(path)
    print(f'agent run: {len(run) - 1} steps with {slips} slips')

    # still: the gif's first frame
    render(1200, 630, open_, None, jmax, [START], START).save(os.path.join(OUT, 'ec710-dp.webp'), quality=88, method=6)

    fps = 20
    frames = [render(440, 220, open_, None, jmax, [START], START)] * int(0.8 * fps)
    # value iteration, one sweep every 0.12 s; cells light up as their value first becomes finite
    for k in range(1, len(hist)):
        front = np.isfinite(hist[k]) & ~np.isfinite(hist[k - 1])
        for j in range(int(0.12 * fps) + 1):
            frames.append(render(440, 220, open_, hist[k], jmax, [START], START, front=front if j == 0 else None))
    frames += [render(440, 220, open_, J, jmax, [START], START)] * int(0.6 * fps)
    # the agent follows the policy at 6 moves a second; a slip is a beat in place
    for t in range(1, len(run)):
        a, b2 = run[t - 1], run[t]
        n = int(fps / 6)
        for j in range(1, n + 1):
            f = j / n
            if a == b2:   # slip: a little shudder in place
                pos = (a[0] + 0.12 * np.sin(np.pi * f * 2), a[1])
            else:
                pos = (a[0] + (b2[0] - a[0]) * f, a[1] + (b2[1] - a[1]) * f)
            trail = [p for k2, p in enumerate(run[:t]) if k2 == 0 or p != run[k2 - 1]] + [pos]
            frames.append(render(440, 220, open_, J, jmax, trail, pos))
    final = [p for k2, p in enumerate(run) if k2 == 0 or p != run[k2 - 1]]
    for j in range(int(1.2 * fps)):
        frames.append(render(440, 220, open_, J, jmax, final, GOAL, goal_flash=max(0.0, 1 - j / (0.8 * fps))))
    for j in range(int(0.5 * fps)):
        frames.append(render(440, 220, open_, J, jmax, final, GOAL, fade=1 - (j + 1) / (0.5 * fps)))

    # palette from several frames, plus reserved colours for the small bright things (agent, goal, flares)
    picks = [frames[0], frames[len(frames) // 3], frames[len(frames) * 2 // 3], frames[-25]]
    sheet = Image.new('RGB', (440, 220 * len(picks)))
    for k, f in enumerate(picks):
        sheet.paste(f, (0, 220 * k))
    base = sheet.quantize(colors=96, method=Image.MEDIANCUT).getpalette()[:96 * 3]
    keep = [(255, 255, 255), (240, 255, 248), (255, 255, 118), (255, 240, 150), (255, 215, 120),
            (255, 200, 110), (225, 150, 50), (180, 120, 50)]
    pal = Image.new('P', (1, 1))
    pal.putpalette(base + [v for c in keep for v in c])
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    out = os.path.join(OUT, 'ec710-dp.gif')
    q[0].save(out, save_all=True, append_images=q[1:], duration=1000 // fps, loop=0, optimize=True)
    print(f'{len(q)} frames ({len(q) / fps:.1f} s) -> {out} ({os.path.getsize(out) / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
