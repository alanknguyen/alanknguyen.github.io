"""Hover animation for the EC 562 notes thumbnail: an N-slit grating lit by a broad Gaussian beam,
intensity in the x-z plane by exact angular-spectrum propagation, with the wavelength sweeping.

usage: python3 tools/grating_anim.py img/thumbs/fourier-optics-anim.gif
Units are output pixels of the 1200 x 630 still; the defaults reproduce fourier-optics-thumbnail.webp.
"""
import sys

import numpy as np
from PIL import Image

STOPS = [(0.00, (13, 32, 56)), (0.30, (24, 62, 100)), (0.52, (32, 86, 120)), (0.70, (52, 128, 104)),
         (0.86, (130, 196, 165)), (0.95, (220, 245, 233)), (1.00, (255, 255, 255))]


def colormap(v):
    v = np.clip(v, 0, 1)
    out = np.zeros(v.shape + (3,))
    for (p0, c0), (p1, c1) in zip(STOPS[:-1], STOPS[1:]):
        m = (v >= p0) & (v <= p1)
        t = ((v - p0) / (p1 - p0))[m]
        for k in range(3):
            out[..., k][m] = c0[k] + (c1[k] - c0[k]) * t
    return out


def intensity(lam=8.5, slit=14.0, sigma=200.0, n_slits=11, period=24.0, W=1200, H=630, sub=4, pad=6, zcols=600):
    dx = 1.0 / sub
    ny = 1 << int(np.ceil(np.log2(H * pad / dx)))
    y = (np.arange(ny) - ny / 2) * dx
    u0 = np.zeros(ny, np.complex64)
    for c in (np.arange(n_slits) - (n_slits - 1) / 2) * period:
        u0[np.abs(y - c) <= slit / 2] = 1
    u0 *= np.exp(-(y / sigma) ** 2)
    k = 2 * np.pi / lam
    ky = 2 * np.pi * np.fft.fftfreq(ny, d=dx)
    kz = np.sqrt(np.maximum(k ** 2 - ky ** 2, 0)).astype(np.float32)
    spectrum = np.fft.fft(u0) * (np.abs(ky) < k)
    zs = (np.arange(zcols) + 0.5) * W / zcols
    win = slice(ny // 2 - H * sub // 2, ny // 2 + H * sub // 2)
    out = np.empty((H, zcols), np.float32)
    for j in range(0, zcols, 50):
        z = zs[j:j + 50]
        u = np.fft.ifft(spectrum[None] * np.exp(1j * kz[None] * z[:, None]).astype(np.complex64), axis=1)
        out[:, j:j + 50] = (np.abs(u[:, win]) ** 2).reshape(len(z), H, sub).mean(2).T
    return out


def frame(lam, gamma=0.35):
    v = intensity(lam) ** gamma
    v = v / np.quantile(v, 0.985)
    im = Image.fromarray(colormap(v).astype(np.uint8)).resize((1200, 630), Image.BILINEAR)
    return im.crop((0, 15, 1200, 615)).resize((440, 220), Image.LANCZOS)   # the thumbnail's 2:1 box


def main(out, n=48, colors=96):
    frames = [frame(8.5 + 2.0 * np.sin(2 * np.pi * i / n)) for i in range(n)]
    w, h = frames[0].size
    mosaic = Image.new('RGB', (w, h * 8))
    for k, i in enumerate(np.linspace(0, n - 1, 8).astype(int)):
        mosaic.paste(frames[i], (0, k * h))
    pal = mosaic.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=80, loop=0, optimize=True, disposal=1)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'fourier-optics-anim.gif'))
