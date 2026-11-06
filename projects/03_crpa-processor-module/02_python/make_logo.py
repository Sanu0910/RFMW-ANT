"""BEL CRL logo for the SDR case: the BEL mark with the Hindi line replaced by 'CENTRAL RESEARCH LABORATORY' in the
same lettering as 'BHARAT ELECTRONICS'. The letters are cut from that line of the original logo (every letter but Y
is in it); Y is drawn with the stroke width and slant of its I. Spacing = the original letter / word gaps.
    python make_logo.py   ->  00_input/BEL_CRL_logo.png
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "..", "02_ls-crpa4-rf-module", "00_input", "BEL_logo.png")
OUT = os.path.join(ROOT, "00_input", "BEL_CRL_logo.png")
TEXT = "CENTRAL RESEARCH LABORATORY"
TOP, BOT = 405, 520                      # rows of the BHARAT ELECTRONICS line
SPAN = (540, 1885)                       # new line: from the mark to the right edge (x), baseline just above the rule
BASE = 362
CAP_PX = 92                              # letter height (BHARAT ELECTRONICS = 100 px): the width-fitted line is
                                         # stretched up to this height, into the space the Hindi line used


def main():
    src = np.asarray(Image.open(SRC).convert("RGB")).astype(int)
    gray = src.max(2)
    ink = gray < 140; ink[:395] = False
    lab, _n = ndimage.label(ink)
    comps = sorted([(s[1].start, i + 1) for i, s in enumerate(ndimage.find_objects(lab)) if (lab[s] == i + 1).sum() > 200])
    cover = np.clip((255 - gray) / 255.0, 0, 1)
    glyph = {}
    for (_x, idx), ch in zip(comps, "BHARATELECTRONICS"):
        m = ndimage.binary_dilation(lab == idx, iterations=2); m[:395] = False
        a = np.zeros_like(cover); a[m] = cover[m]
        xs = np.where(m.any(0))[0]
        glyph.setdefault(ch, a[TOP:BOT, xs.min():xs.max() + 1])
    glyph["Y"] = make_y(glyph["I"])

    def row_gap(a, b, off=0):
        g = [off + np.where(b[r] > 0.5)[0].min() - np.where(a[r] > 0.5)[0].max()
             for r in range(a.shape[0]) if (a[r] > 0.5).any() and (b[r] > 0.5).any()]
        return min(g)
    masks = [(lab == i)[TOP:BOT] for _x, i in comps]
    gaps = [row_gap(masks[k], masks[k + 1]) for k in range(len(masks) - 1) if k != 5]
    lg, wg = int(np.median(gaps)), row_gap(masks[5], masks[6])

    H = BOT - TOP; canvas = np.zeros((H, 6000)); x = 0; need = None
    for ch in TEXT:
        if ch == " ":
            need = int(round(wg * 1.6)); continue
        g = glyph[ch]
        if need is None and x == 0:
            pos = 0
        else:
            req = need if need is not None else lg
            pos = x - g.shape[1]
            while any((g[r] > 0.5).any() and (canvas[r] > 0.5).any() and
                      pos + np.where(g[r] > 0.5)[0].min() - np.where(canvas[r] > 0.5)[0].max() < req for r in range(H)):
                pos += 1
        canvas[:, pos:pos + g.shape[1]] = np.maximum(canvas[:, pos:pos + g.shape[1]], g)
        x = max(x, pos + g.shape[1]); need = None
    cols = np.where(canvas.max(0) > 0.05)[0]
    line = canvas[:, cols.min():cols.max() + 1]

    x0, x1 = SPAN; hh = int(round(line.shape[0] * CAP_PX / 100.0))
    L = np.asarray(Image.fromarray((line * 255).astype(np.uint8)).resize((x1 - x0, hh), Image.LANCZOS)) / 255.0
    out = src.astype(float)
    R, B = src[..., 0], src[..., 2]; blue = (B - R > 60) & (B > 120)
    yy, xx = np.mgrid[0:src.shape[0], 0:src.shape[1]]
    out[(yy >= 200) & (yy <= 366) & (xx >= 505) & ~blue] = 255          # remove the Hindi line, keep the mark + rule
    reg = out[BASE - hh:BASE, x0:x1]; reg[:] = reg * (1 - L[..., None])
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(OUT)
    print("logo ->", os.path.relpath(OUT, ROOT), "letter gap", lg, "word gap", wg, "line height", hh, "px")


def make_y(I):
    """Y in the BHARAT ELECTRONICS style: stroke width and slant measured on its I."""
    m = I > 0.5
    rows = [k for k in range(m.shape[0]) if m[k].any()]
    w = int(np.median([np.ptp(np.where(m[k])[0]) + 1 for k in rows]))
    sh = (np.where(m[rows[0] + 3])[0].mean() - np.where(m[rows[-1] - 3])[0].mean()) / (rows[-1] - rows[0])
    h, base = rows[-1] - rows[0], rows[-1]
    W = int(h * 0.62 + sh * h + w + 10); k = 4
    im = Image.new("L", (W * k, I.shape[0] * k), 0); d = ImageDraw.Draw(im)
    P = lambda u, v: ((u + sh * v + 4) * k, (base - v) * k)
    cx, mid, sp = h * 0.31 + w / 2, h * 0.45, h * 0.31
    d.polygon([P(cx - w / 2, 0), P(cx + w / 2, 0), P(cx + w / 2, mid), P(cx - w / 2, mid)], fill=255)
    d.polygon([P(cx - w / 2, mid), P(cx + w / 2, mid), P(cx - sp + w / 2 + 3, h), P(cx - sp - w / 2 + 3, h)], fill=255)
    d.polygon([P(cx - w / 2, mid), P(cx + w / 2, mid), P(cx + sp + w / 2 - 3, h), P(cx + sp - w / 2 - 3, h)], fill=255)
    g = np.asarray(im.resize((W, I.shape[0]), Image.LANCZOS)) / 255.0
    cols = np.where(g.max(0) > 0.05)[0]
    return g[:, cols.min():cols.max() + 1]


if __name__ == "__main__":
    main()
