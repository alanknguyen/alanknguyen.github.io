"""Image-plus-plot thumbnail candidates for the Engineering Fourier Optics book, with physical units.

usage: python3 tools/thumb_fourier3.py OUTDIR [fresnel slit gaussian imaging talbot]
Each frame is a computed field on the left and a quantitative plot on the right, annotated with numbers.
  fresnel   circular aperture (a = 1 mm, 633 nm): pattern at z, and the on-axis intensity 4 sin^2(pi N_F/2) vs z.
  slit      100 um slit: x-z map with a moving screen, and the profile there against the Fraunhofer sinc^2.
  gaussian  focused Gaussian beam (w0 = 20 um): intensity map, and w(z) with the Gouy phase.
  imaging   coherent 4f imaging of a Siemens star as the NA changes, and the coherent and incoherent
            transfer functions with the cutoff NA/lambda.
  talbot    Talbot carpet of a 20 um grating, and the intensity across a screen sweeping one Talbot length
            (self-image, half-period shift, frequency doubling).
  fresnel-light  the same, on a white figure like the research thumbnail.
The still is each gif's first frame at 1200 x 600.
"""
import io
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

GW, GH, SW, SH = 440, 220, 1200, 600
FPS = 20
BG = '#0b1020'
FG = '#dfe6f3'
DIM = '#8892a8'
SPINE = '#3a4560'
LIGHT = False                                                    # set by the *-light options: white figure, dark text


def use_light():
    global BG, FG, DIM, SPINE, LIGHT
    BG, FG, DIM, SPINE, LIGHT = '#ffffff', '#1c1c1c', '#555555', '#b5b5b5', True
LAM = 633e-9
plt.rcParams.update({'font.family': 'DejaVu Sans', 'mathtext.fontset': 'dejavusans'})


def frame(draw, W, H, plot_w=0.4):
    fig = plt.figure(figsize=(6.4, 3.2), facecolor=BG)
    axi = fig.add_axes([0.015, 0.04, 0.455, 0.92])
    axp = fig.add_axes([0.575, 0.19, plot_w, 0.7])
    for s in axp.spines.values():
        s.set_color(SPINE)
    axp.set_facecolor(BG)
    axp.tick_params(colors=DIM, labelsize=7, length=2)
    draw(fig, axi, axp)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100 * W / 640, facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return np.asarray(Image.open(buf).convert('RGB').resize((W, H), Image.LANCZOS))


def label(ax, x, y, s, **kw):
    kw.setdefault('color', FG)
    kw.setdefault('fontsize', 8)
    kw.setdefault('bbox', dict(boxstyle='round,pad=0.25', fc=BG, ec='none', alpha=0.65))
    ax.text(x, y, s, transform=ax.transAxes, **kw)


def pingpong(t):
    return 0.5 - 0.5 * np.cos(2 * np.pi * t)


# ---------- circular aperture ----------
_c = {}


def circ(NF, n=512, a=40.0, lam=0.5):
    if 'U0' not in _c:
        yy, xx = np.mgrid[-n // 2:n // 2, -n // 2:n // 2].astype(float)
        _c['U0'] = np.fft.fft2((np.hypot(xx, yy) < a).astype(complex))
        f = np.fft.fftfreq(n)
        _c['f2'] = np.add.outer(f ** 2, f ** 2)
    z = a ** 2 / (lam * NF)
    arg = 1 - lam ** 2 * _c['f2']
    I = np.abs(np.fft.ifft2(_c['U0'] * np.exp(2j * np.pi / lam * z * np.sqrt(np.maximum(arg, 0))))) ** 2
    c = 110
    return I[n // 2 - c:n // 2 + c, n // 2 - c:n // 2 + c]


def fresnel(t, W, H):
    a = 1e-3
    zf = a ** 2 / LAM                                            # 1.58 m
    z = 0.22 * (2.2 / 0.22) ** pingpong(t)                      # 22 cm -> 2.2 m, log
    NF = zf / z
    I = circ(NF)
    I0 = 4 * np.sin(np.pi * NF / 2) ** 2

    # colours for the plot side; the image side is always dark (magma), so its labels stay light
    curve, edge, dot, val = (('#e07b00', '#1f6fd1', '#d6336c', '#c2255c') if LIGHT
                             else ('#ffb454', '#5ad1ff', '#ff5c8a', '#ff8fb0'))
    dark = dict(boxstyle='round,pad=0.25', fc='#0b1020', ec='none', alpha=0.65)

    def draw(fig, axi, axp):
        axi.imshow(I ** 0.6, cmap='magma', vmin=0, vmax=max(np.percentile(I ** 0.6, 99.9), 1e-9))
        axi.add_patch(plt.Circle((110, 110), 40, fill=False, ls='--', lw=0.8, color='#5ad1ff', alpha=0.8))
        axi.plot([14, 54], [204, 204], color='white', lw=2)
        axi.text(34, 198, '1 mm', color='white', fontsize=7, ha='center')
        axi.axis('off')
        label(axi, 0.03, 0.92, 'λ = 633 nm,  a = 1 mm', fontsize=7.5, color='#dfe6f3', bbox=dark)
        label(axi, 0.97, 0.92, f'z = {z * 100:.0f} cm', fontsize=8.5, ha='right', color='#ffcf6b', bbox=dark)
        label(axi, 0.97, 0.84, f'$N_F$ = {NF:.2f}', fontsize=8.5, ha='right', color='#ffcf6b', bbox=dark)
        zz = np.geomspace(0.2, 2.4, 800)
        axp.semilogx(zz, 4 * np.sin(np.pi * zf / zz / 2) ** 2, color=curve, lw=1.8)
        axp.axvline(zf, color=edge, ls='--', lw=0.9)
        axp.text(zf * 1.04, 4.25, '$a^2/\\lambda$', color=edge, fontsize=8)
        axp.plot([z], [I0], 'o', ms=7, color=dot, mec='white', mew=1)
        right = z < 1.4
        axp.text(z * (1.12 if right else 0.89), I0 + 0.3 if I0 < 3.4 else I0 - 0.75, f'{I0:.2f}', color=val,
                 fontsize=8, ha='left' if right else 'right')
        axp.set_xlim(0.2, 2.4); axp.set_ylim(-0.2, 4.6)
        axp.set_xticks([0.2, 0.5, 1, 2]); axp.set_xticklabels(['0.2', '0.5', '1', '2'])
        axp.set_xlabel('distance z (m)', color=FG, fontsize=8)
        axp.set_ylabel('on-axis  I / I$_{inc}$', color=FG, fontsize=8)
        axp.set_title('$I_0 = 4\\,\\sin^2(\\pi N_F/2)$', color=FG, fontsize=9)
    return frame(draw, W, H)


# ---------- single slit ----------
_s = {}


def slit_setup():
    if _s:
        return _s
    a, dy, ny = 100e-6, 0.5e-6, 1 << 14
    y = (np.arange(ny) - ny / 2) * dy
    u0 = (np.abs(y) <= a / 2).astype(complex)
    k = 2 * np.pi / LAM
    ky = 2 * np.pi * np.fft.fftfreq(ny, d=dy)
    kz = np.sqrt(np.maximum(k ** 2 - ky ** 2, 0))
    S = np.fft.fft(u0)
    zs = np.linspace(0.5e-3, 60e-3, 300)
    sel = np.abs(y) <= 0.6e-3
    Imap = np.array([np.abs(np.fft.ifft(S * np.exp(1j * kz * z)))[sel] ** 2 for z in zs]).T
    _s.update(a=a, y=y[sel], S=S, kz=kz, sel=sel, zs=zs, Imap=Imap)
    return _s


def slit(t, W, H):
    s = slit_setup()
    a = s['a']
    z = 2e-3 * (55e-3 / 2e-3) ** pingpong(t)
    NF = a ** 2 / (LAM * z)
    I = np.abs(np.fft.ifft(s['S'] * np.exp(1j * s['kz'] * z)))[s['sel']] ** 2
    y = s['y']
    x0 = LAM * z / a
    IF = np.sinc(y / x0) ** 2

    def draw(fig, axi, axp):
        M = s['Imap'] ** 0.5
        axi.imshow(M, cmap='inferno', aspect='auto', origin='lower',
                   extent=[s['zs'][0] * 1e3, s['zs'][-1] * 1e3, y[0] * 1e3, y[-1] * 1e3], vmax=np.percentile(M, 99.5))
        axi.axvline(z * 1e3, color='#5ad1ff', lw=1.2)
        axi.set_xticks([]); axi.set_yticks([])
        for sp in axi.spines.values():
            sp.set_visible(False)
        label(axi, 0.03, 0.9, 'slit a = 100 µm,  λ = 633 nm', fontsize=7.5)
        label(axi, 0.03, 0.05, 'z →', fontsize=8, color=DIM)
        label(axi, 0.97, 0.05, f'z = {z * 1e3:.1f} mm', fontsize=8.5, ha='right', color='#5ad1ff')
        axp.plot(y * 1e3, I / I.max(), color='#ffb454', lw=1.6, label='computed')
        axp.plot(y * 1e3, IF, color='#9cc4ff', lw=1.1, ls='--', label='Fraunhofer sinc$^2$', alpha=min(1, 0.25 + 1.5 / NF))
        for sgn in (-1, 1):
            axp.axvline(sgn * x0 * 1e3, color='#ff5c8a', lw=0.8, alpha=0.7)
        if 1.8 * x0 * 1e3 > 0.09:
            axp.text(x0 * 1e3, 1.13, f'λz/a = {x0 * 1e6:.0f} µm', color='#ff8fb0', fontsize=7.5, ha='center')
        xl = max(0.09, 1.8 * x0 * 1e3)
        axp.set_xlim(-xl, xl); axp.set_ylim(0, 1.25)
        axp.set_xlabel('x on screen (mm)', color=FG, fontsize=8)
        axp.set_ylabel('I / I$_{max}$', color=FG, fontsize=8)
        axp.set_title(f'$N_F$ = {NF:.2f}', color='#ffcf6b', fontsize=9)
        axp.legend(fontsize=6.5, frameon=False, labelcolor=FG, loc='upper left')
    return frame(draw, W, H)


# ---------- Gaussian beam ----------
def gaussian(t, W, H):
    w0 = 20e-6
    zR = np.pi * w0 ** 2 / LAM
    theta = LAM / (np.pi * w0)
    z = -6e-3 + 12e-3 * pingpong(t)
    wz = w0 * np.sqrt(1 + (z / zR) ** 2)
    zz = np.linspace(-6.5e-3, 6.5e-3, 400)
    xx = np.linspace(-140e-6, 140e-6, 220)
    ww = w0 * np.sqrt(1 + (zz / zR) ** 2)
    I = (w0 / ww) ** 2 * np.exp(-2 * xx[:, None] ** 2 / ww ** 2)

    def draw(fig, axi, axp):
        axi.imshow(I ** 0.7, cmap='hot', aspect='auto', origin='lower', extent=[zz[0] * 1e3, zz[-1] * 1e3, -140, 140])
        axi.plot(zz * 1e3, ww * 1e6, color='#5ad1ff', lw=0.8, ls='--')
        axi.plot(zz * 1e3, -ww * 1e6, color='#5ad1ff', lw=0.8, ls='--')
        axi.axvline(z * 1e3, color='white', lw=1)
        axi.annotate('', xy=(z * 1e3, wz * 1e6), xytext=(z * 1e3, -wz * 1e6),
                     arrowprops=dict(arrowstyle='<->', color='#5ad1ff', lw=1))
        axi.set_xticks([]); axi.set_yticks([])
        for sp in axi.spines.values():
            sp.set_visible(False)
        label(axi, 0.03, 0.9, '$w_0$ = 20 µm,  λ = 633 nm', fontsize=7.5)
        label(axi, 0.97, 0.05, f'2w = {2 * wz * 1e6:.0f} µm', fontsize=8.5, ha='right', color='#5ad1ff')
        axp.plot(zz * 1e3, ww * 1e6, color='#5ad1ff', lw=1.8)
        axp.axvspan(-zR * 1e3, zR * 1e3, color='#5ad1ff', alpha=0.08)
        axp.plot([z * 1e3], [wz * 1e6], 'o', ms=7, color='#5ad1ff', mec='white', mew=1)
        axp.set_xlim(zz[0] * 1e3, zz[-1] * 1e3); axp.set_ylim(0, 75)
        axp.set_xlabel('z (mm)', color=FG, fontsize=8)
        axp.set_ylabel('beam radius w (µm)', color='#5ad1ff', fontsize=8)
        ax2 = axp.twinx()
        ax2.plot(zz * 1e3, np.degrees(np.arctan(zz / zR)), color='#ffb454', lw=1.4, ls='--')
        ax2.plot([z * 1e3], [np.degrees(np.arctan(z / zR))], 'o', ms=5, color='#ffb454', mec='white', mew=0.8)
        ax2.set_ylim(-95, 95)
        ax2.tick_params(colors=DIM, labelsize=7, length=2)
        ax2.set_ylabel('Gouy phase (°)', color='#ffb454', fontsize=8)
        for sp in ax2.spines.values():
            sp.set_color('#3a4560')
        axp.set_title(f'$z_R$ = {zR * 1e3:.2f} mm,  θ = {theta * 1e3:.1f} mrad', color=FG, fontsize=8.5)
    return frame(draw, W, H, plot_w=0.33)


# ---------- coherent 4f imaging ----------
_im = {}


def imaging(t, W, H):
    n, L = 512, 200e-6                                           # field of view 200 um
    if not _im:
        yy, xx = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]
        r, th = np.hypot(xx, yy), np.arctan2(yy, xx)
        obj = ((np.sin(24 * th) > 0) & (r < 0.92)).astype(float)
        _im['F'] = np.fft.fftshift(np.fft.fft2(obj))
        fy, fx = np.mgrid[-n // 2:n // 2, -n // 2:n // 2]
        _im['rho'] = np.hypot(fx, fy) / L                        # cycles per metre
    NA = 0.02 * (0.25 / 0.02) ** (1 - pingpong(t))              # starts at 0.25 (sharp)
    fc = NA / LAM
    img = np.abs(np.fft.ifft2(np.fft.ifftshift(_im['F'] * (_im['rho'] <= fc)))) ** 2
    res = 0.61 * LAM / NA

    def draw(fig, axi, axp):
        axi.imshow(img, cmap='bone', vmin=0, vmax=np.percentile(img, 99.8))
        axi.plot([20, 20 + 128], [490, 490], color='#ffcf6b', lw=2)
        axi.text(84, 470, '50 µm', color='#ffcf6b', fontsize=7, ha='center')
        axi.axis('off')
        label(axi, 0.03, 0.92, f'NA = {NA:.3f}', fontsize=9, color='#ffcf6b')
        label(axi, 0.03, 0.84, f'0.61λ/NA = {res * 1e6:.1f} µm', fontsize=7.5)
        f = np.linspace(0, 900, 900)                              # lp/mm
        fcm = fc / 1e3
        ctf = (f <= fcm).astype(float)
        u = np.clip(f / (2 * fcm), 0, 1)
        otf = 2 / np.pi * (np.arccos(u) - u * np.sqrt(1 - u ** 2))
        axp.plot(f, ctf, color='#5ad1ff', lw=1.8, label='coherent (CTF)')
        axp.plot(f, otf, color='#ff8fb0', lw=1.5, ls='--', label='incoherent (OTF)')
        axp.axvline(fcm, color='#ffcf6b', lw=0.9)
        axp.text(min(fcm, 620) + 12, 0.62, f'$f_c$ = NA/λ\n= {fcm:.0f} lp/mm', color='#ffcf6b', fontsize=7.5)
        axp.set_xlim(0, 900); axp.set_ylim(0, 1.15)
        axp.set_xlabel('spatial frequency (lp/mm)', color=FG, fontsize=8)
        axp.set_ylabel('transfer', color=FG, fontsize=8)
        axp.legend(fontsize=6.5, frameon=False, labelcolor=FG, loc='upper right')
    return frame(draw, W, H)


# ---------- Talbot ----------
def talbot(t, W, H):
    p = 20e-6
    zT = 2 * p ** 2 / LAM
    m = np.arange(-60, 61)
    c = 0.15 * np.sinc(m * 0.15) * np.exp(-(m / 40) ** 2)
    x = np.linspace(-p, p, 260)
    zg = np.linspace(0, zT, 360)
    E = np.exp(2j * np.pi * np.outer(x, m) / p) * c
    carpet = np.abs(E @ np.exp(-1j * np.pi * LAM * np.outer(m ** 2, zg) / p ** 2)) ** 2
    z = zT * t
    prof = np.abs(E @ np.exp(-1j * np.pi * LAM * m ** 2 * z / p ** 2)) ** 2
    frac = z / zT
    names = {0: 'self-image', 0.25: 'period halved', 0.5: 'shifted by p/2', 0.75: 'period halved', 1: 'self-image'}
    tag = next((v for k, v in names.items() if abs(frac - k) < 0.02), '')

    def draw(fig, axi, axp):
        axi.imshow(carpet ** 0.6, cmap='viridis', aspect='auto', origin='lower', extent=[0, zT * 1e3, -20, 20],
                   vmax=np.percentile(carpet ** 0.6, 99.6))
        axi.axvline(z * 1e3, color='white', lw=1.1)
        for k in (0.25, 0.5, 0.75):
            axi.axvline(k * zT * 1e3, color='white', lw=0.5, ls=':', alpha=0.6)
        axi.set_xticks([]); axi.set_yticks([])
        for sp in axi.spines.values():
            sp.set_visible(False)
        label(axi, 0.03, 0.9, 'p = 20 µm,  λ = 633 nm', fontsize=7.5, color='white')
        label(axi, 0.97, 0.05, f'$z_T = 2p^2/\\lambda$ = {zT * 1e3:.2f} mm', fontsize=7.5, ha='right', color='white')
        axp.fill_between(x * 1e6, prof / prof.max(), color='#7ee08a', alpha=0.2, lw=0)
        axp.plot(x * 1e6, prof / prof.max(), color='#7ee08a', lw=1.6)
        axp.set_xlim(-20, 20); axp.set_ylim(0, 1.15)
        axp.set_xlabel('x (µm)', color=FG, fontsize=8)
        axp.set_ylabel('I / I$_{max}$', color=FG, fontsize=8)
        axp.set_title(f'z / $z_T$ = {frac:.2f}' + (f'  ·  {tag}' if tag else ''), color='#ffcf6b', fontsize=8.5)
    return frame(draw, W, H)


def fresnel_light(t, W, H):
    use_light()
    return fresnel(t, W, H)


OPTIONS = {'fresnel-light': (fresnel_light, 5.0), 'fresnel': (fresnel, 5.0), 'slit': (slit, 5.0), 'gaussian': (gaussian, 5.0),
           'imaging': (imaging, 5.0), 'talbot': (talbot, 6.0)}


def save_gif(frames, path, colors=192):
    sheet = Image.fromarray(np.concatenate(frames[::max(1, len(frames) // 8)], axis=0))
    pal = sheet.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    q = [Image.fromarray(f).quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=1000 // FPS, loop=0, optimize=True)


def main(out, names):
    os.makedirs(out, exist_ok=True)
    for name in names:
        fn, secs = OPTIONS[name]
        n = int(secs * FPS)
        frames = [fn(i / n, GW, GH) for i in range(n)]
        save_gif(frames, os.path.join(out, f'fo-{name}.gif'))
        Image.fromarray(fn(0.0, SW, SH)).save(os.path.join(out, f'fo-{name}.webp'), quality=90, method=6)
        print(name, n, 'frames', f"{os.path.getsize(os.path.join(out, f'fo-{name}.gif')) / 1e6:.2f} MB")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or list(OPTIONS))
