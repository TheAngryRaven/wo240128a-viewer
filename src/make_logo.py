#!/usr/bin/env python3
"""
Convert a logo image into packed 1-bit bitmaps for the UI core.

    python3 src/make_logo.py logo.png > src/logo_bitmaps.js

Output: a JS object LOGO_SRC with three sizes (HI for transforms, MID for 1:1 display,
SM for the header icon). Bits are row-major, MSB first, 1 = dark, base64 encoded.
The same packing works for a C `const uint8_t logo_hi[]` array.
"""
import base64
import sys
import warnings

import numpy as np
from PIL import Image, ImageOps

warnings.simplefilter("ignore")

SIZES = [("HI", 240), ("MID", 120), ("SM", 26)]


def load(path: str) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    g = ImageOps.grayscale(bg.convert("RGB"))
    arr = np.array(g)
    ys, xs = np.where(arr < 128)
    return g.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def pack(img: Image.Image, w: int):
    h = round(w * img.size[1] / img.size[0])
    bits = (np.array(img.resize((w, h), Image.LANCZOS)) < 128).astype(np.uint8)
    return w, h, base64.b64encode(np.packbits(bits.flatten()).tobytes()).decode()


if __name__ == "__main__":
    g = load(sys.argv[1])
    rows = []
    for name, w in SIZES:
        W, H, b64 = pack(g, w)
        rows.append(f'  {name}: {{ w: {W}, h: {H}, b64: "{b64}" }}')
    print("const LOGO_SRC = {\n" + ",\n".join(rows) + "\n};")
