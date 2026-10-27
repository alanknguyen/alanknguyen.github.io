"""EC 710 thumbnail (placeholder still): the dynamic programming recursion, centred.

usage: python3 tools/thumb_dp.py   (writes img/thumbs/ec710-dp.webp)
"""
import os

import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'img', 'thumbs')
BG = (8, 20, 36)


def main(w=1200, h=630, ss=2):
    plt.rcParams['mathtext.fontset'] = 'cm'
    W, H = w * ss, h * ss
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_alpha(0)
    pt = lambda frac: H * frac * 72 / 100        # font size as a fraction of the height
    fig.text(0.5, 0.62, r'$J_k(x_k) = \min_{u_k}\ \mathbb{E}_{w_k}\left[\, g_k(x_k,u_k,w_k) + J_{k+1}(x_{k+1}) \,\right]$',
             ha='center', va='center', fontsize=pt(0.072), color='#e6f2fa')
    fig.text(0.5, 0.36, r'$x_{k+1} = f_k(x_k, u_k, w_k)$', ha='center', va='center', fontsize=pt(0.072), color='#96f0c8')
    fig.canvas.draw()
    text = Image.frombuffer('RGBA', fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).copy()
    plt.close(fig)

    im = Image.new('RGB', (W, H), BG)
    v = Image.new('L', (W, H), 0)
    ImageDraw.Draw(v).ellipse([W * 0.15, H * 0.05, W * 0.85, H * 0.95], fill=40)
    im = Image.composite(Image.new('RGB', (W, H), (22, 55, 85)), im, v.filter(ImageFilter.GaussianBlur(W * 0.1)))
    rgb = np.asarray(text, float)[..., :3] * (np.asarray(text, float)[..., 3:] / 255)
    glow = np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(W / 200)), float)
    base = np.clip(np.asarray(im, float) + 0.6 * glow, 0, 255).astype(np.uint8)
    out = Image.alpha_composite(Image.fromarray(base).convert('RGBA'), text).convert('RGB')
    path = os.path.join(OUT, 'ec710-dp.webp')
    out.resize((w, h), Image.LANCZOS).save(path, quality=90, method=6)
    print(f'-> {path}')


if __name__ == '__main__':
    main()
