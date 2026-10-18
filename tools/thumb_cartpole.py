"""EC 701 thumbnail: a cart swings a double pendulum up with minimum effort, then LQR holds it against kicks.

usage: python3 tools/thumb_cartpole.py   (writes img/thumbs/ec701-cartpole.webp and .gif)
Swing-up: trapezoidal collocation minimising the integral of u^2; tracked by time-varying LQR about that
trajectory, then infinite-horizon LQR about the upright. Everything is simulated on the nonlinear model.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_are
from scipy.optimize import minimize

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'img', 'thumbs')

# cart, two point masses on massless links; angles from upright, positive to the right
M, m1, m2, l1, l2, g = 1.0, 0.3, 0.3, 0.5, 0.5, 9.81


def f(s, u):
    """state s = [x, th1, th2, xd, th1d, th2d] (last axis), force u on the cart"""
    x, a, b, xd, ad, bd = np.moveaxis(s, -1, 0)
    ca, cb, sa, sb, cab, sab = np.cos(a), np.cos(b), np.sin(a), np.sin(b), np.cos(a - b), np.sin(a - b)
    k = m1 + m2
    Mm = np.stack([
        np.stack([np.full_like(a, M + k), k * l1 * ca, m2 * l2 * cb], -1),
        np.stack([k * l1 * ca, np.full_like(a, k * l1 ** 2), m2 * l1 * l2 * cab], -1),
        np.stack([m2 * l2 * cb, m2 * l1 * l2 * cab, np.full_like(a, m2 * l2 ** 2)], -1),
    ], -2)
    rhs = np.stack([
        u + k * l1 * sa * ad ** 2 + m2 * l2 * sb * bd ** 2,
        -m2 * l1 * l2 * sab * bd ** 2 + k * g * l1 * sa,
        m2 * l1 * l2 * sab * ad ** 2 + m2 * g * l2 * sb,
    ], -1)
    acc = np.linalg.solve(Mm, rhs[..., None])[..., 0]
    return np.concatenate([np.stack([xd, ad, bd], -1), acc], -1)


def jac(s, u, h=1e-6):
    A = np.empty((6, 6))
    for i in range(6):
        e = np.zeros(6); e[i] = h
        A[:, i] = (f(s + e, u) - f(s - e, u)) / (2 * h)
    B = ((f(s, u + h) - f(s, u - h)) / (2 * h))[:, None]
    return A, B


Q = np.diag([4, 40, 40, 1, 2, 2])
R = np.array([[0.05]])
UP = np.zeros(6)


def lqr(s, u):
    A, B = jac(s, u)
    S = solve_continuous_are(A, B, Q, R)
    return np.linalg.solve(R, B.T @ S), S


# ---- optimal swing-up by collocation ----
N, T = 70, 2.6
dt = T / N
S0 = np.array([0, np.pi, np.pi, 0, 0, 0])


def unpack(z):
    return z[:6 * (N + 1)].reshape(N + 1, 6), z[6 * (N + 1):]


def cost(z):
    _, u = unpack(z)
    return dt * np.sum((u[:-1] ** 2 + u[1:] ** 2) / 2)


def cost_grad(z):
    _, u = unpack(z)
    gu = dt * u.copy(); gu[0] /= 2; gu[-1] /= 2
    return np.concatenate([np.zeros(6 * (N + 1)), gu])


def defects(z):
    s, u = unpack(z)
    fs = f(s, u)
    d = s[1:] - s[:-1] - dt / 2 * (fs[1:] + fs[:-1])
    return np.concatenate([d.ravel(), s[0] - S0, s[-1] - UP])


def solve_swingup():
    t = np.linspace(0, 1, N + 1)
    guess = np.zeros((N + 1, 6))
    guess[:, 1] = np.pi * (1 - t)
    guess[:, 2] = np.pi * (1 - t)
    guess[:, 0] = 0.3 * np.sin(2 * np.pi * t)
    z0 = np.concatenate([guess.ravel(), np.zeros(N + 1)])
    bounds = [(-1.3, 1.3) if i % 6 == 0 else (None, None) for i in range(6 * (N + 1))] + [(-40, 40)] * (N + 1)
    res = minimize(cost, z0, jac=cost_grad, method='SLSQP', bounds=bounds,
                   constraints={'type': 'eq', 'fun': defects}, options={'maxiter': 600, 'ftol': 1e-9})
    s, u = unpack(res.x)
    print(f'swing-up: {res.message} cost {res.fun:.2f}, max defect {np.abs(defects(res.x)).max():.1e}, '
          f'max |u| {np.abs(u).max():.1f} N, x in [{s[:, 0].min():.2f}, {s[:, 0].max():.2f}]')
    return s, u


def simulate():
    s_ref, u_ref = solve_swingup()
    tk = np.linspace(0, T, N + 1)
    ref = lambda t: np.array([np.interp(t, tk, s_ref[:, i]) for i in range(6)])
    uref = lambda t: np.interp(t, tk, u_ref)

    # time-varying LQR along the swing-up: backward Riccati from the upright cost-to-go
    K_up, S_T = lqr(UP, 0.0)

    def riccati(t, sv):
        S = sv.reshape(6, 6)
        A, B = jac(ref(t), uref(t))
        dS = -(A.T @ S + S @ A - S @ B @ np.linalg.solve(R, B.T @ S) + Q)
        return dS.ravel()

    rs = solve_ivp(riccati, [T, 0], S_T.ravel(), dense_output=True, rtol=1e-6, atol=1e-8)

    def K_tv(t):
        A, B = jac(ref(t), uref(t))
        return np.linalg.solve(R, B.T @ rs.sol(t).reshape(6, 6))

    fps, hold0 = 25, 0.6
    kicks = [(T + 1.4, [0, 0, 0, 0, 0.7, -1.2]), (T + 3.9, [0, 0, 0, 0, -0.6, 1.1])]
    t_end = T + 6.4

    def ctrl(t, s):
        if t < 0:
            return 0.0
        if t < T:
            return float(uref(t) - (K_tv(t) @ (s - ref(t)))[0])
        return float(-(K_up @ s)[0])

    frames, us = [], []
    s = S0.astype(float).copy()
    times = np.arange(-hold0, t_end, 1 / fps)
    sub = 8
    for t in times:
        frames.append(s.copy())
        us.append(ctrl(t, s))
        for kt, dv in kicks:
            if t <= kt < t + 1 / fps:
                s = s + np.array(dv)
        h = 1 / fps / sub
        for j in range(sub):  # RK4 with the input held over each sub-step
            tt = t + j * h
            u = ctrl(tt, s)
            k1 = f(s, u); k2 = f(s + h / 2 * k1, u); k3 = f(s + h / 2 * k2, u); k4 = f(s + h * k3, u)
            s = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    frames, us = np.array(frames), np.array(us)
    print(f'closed loop: final |state| {np.abs(frames[-1]).max():.3f}, cart x in '
          f'[{frames[:, 0].min():.2f}, {frames[:, 0].max():.2f}], max |u| {np.abs(us).max():.1f} N')
    return times, frames, us, [k for k, _ in kicks]


# ---- drawing ----
BG = (8, 20, 36)
TRACK = (40, 70, 100)
CART = (52, 120, 170)
LINK = (226, 240, 246)
BOB = (150, 235, 190)
TRAIL = (80, 200, 150)
FORCE = (120, 180, 255)


def poses(s):
    x, a, b = s[0], s[1], s[2]
    p1 = (x + l1 * np.sin(a), l1 * np.cos(a))
    p2 = (p1[0] + l2 * np.sin(b), p1[1] + l2 * np.cos(b))
    return (x, 0.0), p1, p2


def canvas(w, h, ss, glow=True):
    im = Image.new('RGB', (w * ss, h * ss), BG)
    if not glow:  # flat for the gif, where a soft gradient bands after quantizing
        return im
    # faint vertical glow so the background isn't flat
    mask = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(mask).ellipse([w * ss * 0.2, -h * ss * 0.3, w * ss * 0.8, h * ss * 0.9], fill=40)
    mask = mask.filter(ImageFilter.GaussianBlur(w * ss * 0.12))
    return Image.composite(Image.new('RGB', im.size, (24, 60, 90)), im, mask)


def frame(w, h, s, u, trail, ghosts=(), ss=3, kick=0.0, glow=False):
    im = canvas(w, h, ss, glow)
    d = ImageDraw.Draw(im, 'RGBA')
    sc = h * ss * 0.42            # pixels per metre
    gy = h * ss * 0.50            # rail height; the pendulum hangs in front of it
    cx = w * ss / 2
    P = lambda p: (cx + p[0] * sc, gy - p[1] * sc)
    lw = max(1, round(sc * 0.04))

    d.line([(cx - 2.1 * sc, gy + sc * 0.11), (cx + 2.1 * sc, gy + sc * 0.11)], fill=TRACK + (255,), width=lw)

    for gs, alpha in ghosts:
        c, p1, p2 = poses(gs)
        d.line([P(c), P(p1), P(p2)], fill=LINK + (alpha,), width=max(1, lw // 2), joint='curve')
        r = sc * 0.045
        d.ellipse([P(p2)[0] - r, P(p2)[1] - r, P(p2)[0] + r, P(p2)[1] + r], fill=BOB + (alpha,))

    if len(trail) > 1:
        pts = [P(poses(q)[2]) for q in trail]
        n = len(pts)
        for i in range(1, n):
            a = int(200 * (i / n) ** 1.6)
            d.line([pts[i - 1], pts[i]], fill=TRAIL + (a,), width=lw)

    c, p1, p2 = poses(s)
    cw, ch = sc * 0.34, sc * 0.17
    cc = P(c)
    d.rounded_rectangle([cc[0] - cw / 2, cc[1] - ch / 2, cc[0] + cw / 2, cc[1] + ch / 2], radius=ch * 0.25, fill=CART + (255,))
    for wx in (-cw * 0.28, cw * 0.28):
        r = ch * 0.28
        d.ellipse([cc[0] + wx - r, gy + sc * 0.11 - 2 * r, cc[0] + wx + r, gy + sc * 0.11], fill=(30, 80, 120, 255))

    # force arrow on the cart
    if abs(u) > 0.3:
        L = np.clip(u / 30, -1, 1) * sc * 0.45
        y = cc[1]
        x0 = cc[0] - np.sign(u) * cw / 2
        x1 = x0 - L
        d.line([(x1, y), (x0 - np.sign(u) * sc * 0.03, y)], fill=FORCE + (220,), width=lw)
        hs = sc * 0.05
        tip = x0
        d.polygon([(tip, y), (tip - np.sign(u) * hs * 1.4, y - hs), (tip - np.sign(u) * hs * 1.4, y + hs)], fill=FORCE + (220,))

    d.line([P(c), P(p1), P(p2)], fill=LINK + (255,), width=lw * 2, joint='curve')
    for p, r, col in ((c, 0.035, LINK), (p1, 0.05, LINK), (p2, 0.06, BOB)):
        q = P(p)
        rr = sc * r
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=col + (255,))
    if kick > 0:  # brief ring where the kick lands
        q = P(p2)
        rr = sc * (0.08 + 0.18 * (1 - kick))
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], outline=(255, 210, 120, int(220 * kick)), width=lw)
    return im.resize((w, h), Image.LANCZOS)


def main():
    times, S, U, kicks = simulate()
    fps = 25

    # still: the swing-up as a stroboscopic exposure
    sw = [i for i, t in enumerate(times) if 0 <= t <= T]
    picks = sw[::6]
    ghosts = [(S[i], int(35 + 110 * k / len(picks))) for k, i in enumerate(picks)]
    end = sw[-1] + 5
    still = frame(1200, 630, S[end], 0.0, S[sw[0]:end], ghosts=ghosts, ss=2, glow=True)
    still.save(os.path.join(OUT, 'ec701-cartpole.webp'), quality=88, method=6)

    # animation
    gif = []
    for i, (t, s, u) in enumerate(zip(times, S, U)):
        kick = max([1 - (t - k) / 0.4 for k in kicks if 0 <= t - k < 0.4] + [0])
        gif.append(frame(440, 220, s, u, S[max(0, i - 30):i + 1], kick=kick))
    pal = gif[len(gif) // 3].quantize(colors=96, method=Image.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.NONE) for im in gif]
    path = os.path.join(OUT, 'ec701-cartpole.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=1000 // fps, loop=0, optimize=True)
    print(f'{len(q)} frames -> {path} ({os.path.getsize(path) / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
