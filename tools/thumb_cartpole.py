"""EC 701 thumbnail: a cart swings a double pendulum up with minimum effort, LQR holds it through a kick, and the
swing-up run backwards lowers it again, so the gif loops.

usage: python3 tools/thumb_cartpole.py   (writes img/thumbs/ec701-cartpole.webp and .gif)
Swing-up: trapezoidal collocation minimising the integral of u^2, tracked by time-varying LQR. The model is
frictionless, so the swing-up played backwards (same states, velocities reversed, u(T - t)) is also a solution;
it is tracked the same way down to the hanging rest state. Everything is simulated on the nonlinear model.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
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


Q = np.diag([20, 40, 40, 4, 2, 2])
R = np.array([[0.05]])
UP = np.zeros(6)
DOWN = np.array([0, np.pi, np.pi, 0, 0, 0])
FLIP = np.array([1, 1, 1, -1, -1, -1])     # time reversal: same configuration, velocities negated


def lqr(s, u):
    A, B = jac(s, u)
    S = solve_continuous_are(A, B, Q, R)
    return np.linalg.solve(R, B.T @ S), S


# ---- optimal swing-up by collocation ----
N, T = 70, 2.6
dt = T / N


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
    return np.concatenate([d.ravel(), s[0] - DOWN, s[-1] - UP])


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


def tracker(ref, uref, s_end, u_end):
    """time-varying LQR along (ref, uref) on [0, T], from the infinite-horizon cost-to-go at the end state"""
    _, S_T = lqr(s_end, u_end)

    def riccati(t, sv):
        S = sv.reshape(6, 6)
        A, B = jac(ref(t), uref(t))
        return (-(A.T @ S + S @ A - S @ B @ np.linalg.solve(R, B.T @ S) + Q)).ravel()

    rs = solve_ivp(riccati, [T, 0], S_T.ravel(), dense_output=True, rtol=1e-6, atol=1e-8)

    def u(t, s):
        A, B = jac(ref(t), uref(t))
        K = np.linalg.solve(R, B.T @ rs.sol(t).reshape(6, 6))
        return float(uref(t) - (K @ (s - ref(t)))[0])
    return u


FPS = 20
HOLD, BAL = 0.2, 4.2               # rest at the bottom; time balanced at the top
KICK = (1.0, np.array([0, 0, 0, 0, 0.7, -1.2]))
END = T + BAL + T + HOLD


def simulate():
    s_ref, u_ref = solve_swingup()
    tk = np.linspace(0, T, N + 1)
    up_ref = lambda t: np.array([np.interp(t, tk, s_ref[:, i]) for i in range(6)])
    up_u = lambda t: np.interp(t, tk, u_ref)
    dn_ref = lambda t: up_ref(T - t) * FLIP
    dn_u = lambda t: up_u(T - t)
    swing_up = tracker(up_ref, up_u, UP, 0.0)
    swing_dn = tracker(dn_ref, dn_u, DOWN, 0.0)
    K_up, _ = lqr(UP, 0.0)
    K_dn, _ = lqr(DOWN, 0.0)

    def ctrl(t, s):
        if t < 0:
            return float(-(K_dn @ (s - DOWN))[0])
        if t < T:
            return swing_up(t, s)
        if t < T + BAL:
            return float(-(K_up @ s)[0])
        if t < 2 * T + BAL:
            return swing_dn(t - T - BAL, s)
        return float(-(K_dn @ (s - DOWN))[0])

    s = DOWN.astype(float).copy()
    times = np.arange(-HOLD, END - HOLD, 1 / FPS)
    out, us, sub = [], [], 10
    for t in times:
        out.append(s.copy())
        us.append(ctrl(t, s))
        if t <= T + KICK[0] < t + 1 / FPS:
            s = s + KICK[1]
        h = 1 / FPS / sub
        for j in range(sub):  # RK4 with the input held over each sub-step
            u = ctrl(t + j * h, s)
            k1 = f(s, u); k2 = f(s + h / 2 * k1, u); k3 = f(s + h / 2 * k2, u); k4 = f(s + h * k3, u)
            s = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    S = np.array(out)
    print(f'state before swing-down {np.round(S[np.searchsorted(times, T + BAL)], 3)}')
    print(f'end vs start (loop seam) {np.abs(s - DOWN).max():.4f}; cart x in [{S[:, 0].min():.2f}, {S[:, 0].max():.2f}]')
    return times, S, np.array(us)


# ---- drawing ----
BG = (8, 20, 36)
RAIL = (70, 120, 170)
RAIL_IN = (30, 60, 95)
CART = (40, 120, 200)
WHEEL = (24, 52, 82)      # joint centres
LINK1 = (60, 210, 160)
LINK2 = (150, 240, 200)
JOINT = (235, 245, 250)
LINK = (230, 242, 250)
TIP = (190, 255, 225)
TRAIL = (90, 220, 170)
FORCE = (120, 180, 255)
KICKC = (255, 200, 110)


def poses(s):
    x, a, b = s[0], s[1], s[2]
    p1 = (x + l1 * np.sin(a), l1 * np.cos(a))
    p2 = (p1[0] + l2 * np.sin(b), p1[1] + l2 * np.cos(b))
    return (x, 0.0), p1, p2


def frame(w, h, s, trail, u=0.0, kick=0.0, ss=2, glow=False, ghosts=(), dots=(), centre=0.5, rail=1.85, plot=None):
    W, H = w * ss, h * ss
    lines = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(lines, 'RGBA')                   # glowing layer
    solid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    o = ImageDraw.Draw(solid, 'RGBA')                   # solid parts on top, true colours
    sc = H * 0.38                 # pixels per metre
    gy = H * 0.52                 # rail height; the pendulum hangs in front of it
    cx = W * centre
    lw = max(1, round(W / 300))
    cw, ch = sc * 0.46, sc * 0.19
    wr = ch * 0.36                # wheel radius
    body_bot = gy - wr * 1.1
    pv = lambda p: (cx + p[0] * sc, body_bot - ch * 0.55 - p[1] * sc)   # world -> screen, origin at the pivot

    # rail: two-tone bar with sleepers and end stops
    x0, x1 = cx - rail * sc, cx + rail * sc
    for xx in np.linspace(x0, x1, 23):
        d.line([(xx, gy - lw * 0.5), (xx, gy + lw * 3.5)], fill=RAIL_IN + (255,), width=lw)
    d.line([(x0, gy), (x1, gy)], fill=RAIL + (255,), width=lw * 3)
    d.line([(x0, gy), (x1, gy)], fill=RAIL_IN + (255,), width=lw)
    for e in (x0, x1):
        d.rounded_rectangle([e - lw * 2, gy - sc * 0.09, e + lw * 2, gy + sc * 0.05], radius=lw, fill=RAIL + (255,))

    if len(trail) > 1:  # fading trail of the tip
        pts = [pv(poses(q)[2]) for q in trail]
        n = len(pts)
        for i in range(1, n):
            d.line([pts[i - 1], pts[i]], fill=TRAIL + (int(220 * (i / n) ** 1.5),), width=lw * 2)

    def cart(dr, px, alpha, outline=False):
        if outline:   # past positions: outline with a faint fill, so overlapping carts stay readable
            dr.rounded_rectangle([px - cw / 2, body_bot - ch, px + cw / 2, body_bot], radius=ch * 0.25,
                                 fill=CART + (alpha // 5,), outline=CART + (alpha,), width=lw)
            for wx in (-cw * 0.3, cw * 0.3):
                dr.ellipse([px + wx - wr, gy - 2 * wr, px + wx + wr, gy], outline=CART + (alpha,), width=lw)
            return
        dr.rounded_rectangle([px - cw / 2, body_bot - ch, px + cw / 2, body_bot], radius=ch * 0.25, fill=CART + (alpha,))
        for wx in (-cw * 0.3, cw * 0.3):
            dr.ellipse([px + wx - wr, gy - 2 * wr, px + wx + wr, gy], fill=CART + (alpha,))

    for gs, alpha in ghosts:   # faded past poses: cart, links and ball
        gc, g1, g2 = poses(gs)
        cart(o, cx + gc[0] * sc, alpha, outline=True)
        o.line([pv(gc), pv(g1), pv(g2)], fill=LINK2 + (alpha,), width=round(lw * 1.4), joint='curve')
        rr = sc * 0.05
        q = pv(g2)
        o.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=TIP + (alpha,))
    for ds_, alpha in dots:    # stroboscopic traces of the ball
        q = pv(poses(ds_)[2])
        rr = sc * 0.028
        d.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=TIP + (alpha,))

    c, p1, p2 = poses(s)
    px = cx + c[0] * sc
    # force on the cart
    if abs(u) > 0.5:
        L = np.clip(abs(u) / 25, 0.15, 1) * sc * 0.55
        sg = np.sign(u)
        tail = px - sg * (cw / 2 + lw * 2 + L)
        tip = px - sg * (cw / 2 + lw * 2)
        y = body_bot - ch * 0.5
        d.line([(tail, y), (tip - sg * lw * 4, y)], fill=FORCE + (230,), width=lw * 2)
        hs = lw * 4
        d.polygon([(tip, y), (tip - sg * hs * 1.5, y - hs), (tip - sg * hs * 1.5, y + hs)], fill=FORCE + (230,))
    # cart: body, lighter top plate, accent stripe, wheels with hubs, pivot bearing
    d.rounded_rectangle([px - cw / 2, body_bot - ch, px + cw / 2, body_bot], radius=ch * 0.22, fill=CART + (90,))   # halo
    cart(o, px, 255)
    piv = pv(c)

    # pendulum: two coloured links, ringed joints, glowing tip
    q1, q2 = pv(p1), pv(p2)
    for dr in (d, o):   # glow underneath, crisp colour on top
        a = 150 if dr is d else 255
        dr.line([piv, q1], fill=LINK1 + (a,), width=round(lw * 2.4))
        dr.line([q1, q2], fill=LINK2 + (a,), width=round(lw * 2.4))
    for q, r in ((piv, 0.035), (q1, 0.045)):
        rr = sc * r
        o.ellipse([q[0] - rr, q[1] - rr, q[0] + rr, q[1] + rr], fill=JOINT + (255,))
        rr2 = rr * 0.45
        o.ellipse([q[0] - rr2, q[1] - rr2, q[0] + rr2, q[1] + rr2], fill=WHEEL + (255,))
    rr = sc * 0.065
    d.ellipse([q2[0] - rr * 1.3, q2[1] - rr * 1.3, q2[0] + rr * 1.3, q2[1] + rr * 1.3], fill=TIP + (200,))
    o.ellipse([q2[0] - rr, q2[1] - rr, q2[0] + rr, q2[1] + rr], fill=TIP + (255,))
    if kick > 0:
        rr = sc * (0.08 + 0.22 * (1 - kick))
        d.ellipse([q2[0] - rr, q2[1] - rr, q2[0] + rr, q2[1] + rr], outline=KICKC + (int(240 * kick),), width=lw * 2)

    if plot is not None:
        plot(d, o, W, H, lw)

    im = Image.new('RGB', (W, H), BG)
    if glow:  # soft backdrop for the still only; in the gif it would band
        v = Image.new('L', (W, H), 0)
        ImageDraw.Draw(v).ellipse([W * 0.2, -H * 0.2, W * 0.8, H * 1.1], fill=40)
        im = Image.composite(Image.new('RGB', (W, H), (22, 55, 85)), im, v.filter(ImageFilter.GaussianBlur(W * 0.1)))
    bloom = lines.filter(ImageFilter.GaussianBlur(lw * 2.5))
    out = np.clip(np.asarray(im, float) + np.asarray(lines, float) + 0.75 * np.asarray(bloom, float), 0, 255)
    out = Image.alpha_composite(Image.fromarray(out.astype(np.uint8)).convert('RGBA'), solid).convert('RGB')
    return out.resize((w, h), Image.LANCZOS)


def still(s0, w=1200, h=630, ss=2):
    """the static thumbnail: the gif's first frame, with the state equation in the space below the rail"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['mathtext.fontset'] = 'cm'
    W, H = w * ss, h * ss
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    fig.text(0.75, 0.25, r'$\dot{x} = Ax + Bu$', ha='center', va='center', fontsize=H * 0.11 * 72 / 100, color='#e6f2fa')
    fig.canvas.draw()
    text = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).copy()
    plt.close(fig)

    scene = frame(w, h, s0, [s0], ss=ss).resize((W, H), Image.LANCZOS)
    rgb = np.asarray(text, float)[..., :3] * (np.asarray(text, float)[..., 3:] / 255)
    glow = np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(W / 250)), float)
    base = np.clip(np.asarray(scene, float) + 0.5 * glow, 0, 255).astype(np.uint8)
    out = Image.alpha_composite(Image.fromarray(base).convert('RGBA'), text).convert('RGB')
    out.resize((w, h), Image.LANCZOS).save(os.path.join(OUT, 'ec701-cartpole.webp'), quality=90, method=6)


def main():
    times, S, U = simulate()
    i_top = np.searchsorted(times, T + 0.5)
    i0 = np.searchsorted(times, 0.0)
    i_end = np.searchsorted(times, T)
    still(S[0])

    frames = []
    for i, t in enumerate(times):
        dk = t - (T + KICK[0])
        kick = max(0.0, 1 - dk / 0.5) if dk >= 0 else 0.0
        frames.append(frame(440, 220, S[i], S[max(0, i - 16):i + 1], u=U[i], kick=kick))
    pal = frames[i_top].quantize(colors=96, method=Image.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.NONE) for im in frames]
    path = os.path.join(OUT, 'ec701-cartpole.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=1000 // FPS, loop=0, optimize=True)
    print(f'{len(q)} frames -> {path} ({os.path.getsize(path) / 1e6:.2f} MB)')


if __name__ == '__main__':
    main()
