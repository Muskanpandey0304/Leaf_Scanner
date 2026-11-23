"""Draw the Leaf Scanner launcher icon (green tile, white leaf, scanner corners) and write the Android icon files."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

RES = Path(__file__).resolve().parent.parent / "mobile_app/android/app/src/main/res"
S = 2048  # supersampled canvas


def mark(size, leaf_scale=1.0):
    """Transparent image holding the white leaf, its veins and the four scanner corners."""
    k = size / 1000.0
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = 500
    sc = lambda x, y: (cx * k + (x - cx) * k * leaf_scale, cy * k + (y - cy) * k * leaf_scale)

    # leaf: base bottom-left to tip top-right
    bx, by, tx, ty = 300, 710, 715, 285
    dx, dy = tx - bx, ty - by
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    W = 175
    left, right = [], []
    for i in range(0, 101):
        t = i / 100
        w = W * (math.sin(math.pi * t) ** 0.85) * (1.0 - 0.18 * t)
        x, y = bx + dx * t, by + dy * t
        left.append(sc(x + nx * w * 1.08, y + ny * w * 1.08))
        right.append(sc(x - nx * w * 0.92, y - ny * w * 0.92))
    d.polygon(left + right[::-1], fill=(255, 255, 255, 255))
    # midrib + stem + side veins in green
    green = (46, 125, 50, 255)
    vw = max(2, int(15 * k * leaf_scale))
    d.line([sc(bx - 70, by + 70), sc(tx - 25, ty + 25)], fill=green, width=vw)
    for t in (0.30, 0.48, 0.66):
        x, y = bx + dx * t, by + dy * t
        for sgn in (1, -1):
            ex = x + dx / length * 70 + nx * 105 * sgn
            ey = y + dy / length * 70 + ny * 105 * sgn
            d.line([sc(x, y), sc(ex, ey)], fill=green, width=max(2, int(9 * k * leaf_scale)))
    # scanner corners
    a, b, ln, th = 175, 825, 125, 34
    wcol = (255, 255, 255, 255)
    for (px, py, sx, sy) in ((a, a, 1, 1), (b, a, -1, 1), (a, b, 1, -1), (b, b, -1, -1)):
        d.line([sc(px, py), sc(px + sx * ln, py)], fill=wcol, width=int(th * k * leaf_scale))
        d.line([sc(px, py), sc(px, py + sy * ln)], fill=wcol, width=int(th * k * leaf_scale))
        r = th * k * leaf_scale / 2
        for (qx, qy) in ((px, py), (px + sx * ln, py), (px, py + sy * ln)):
            X, Y = sc(qx, qy)
            d.ellipse([X - r, Y - r, X + r, Y + r], fill=wcol)
    return im


def gradient(size):
    g = Image.new("RGB", (size, size))
    px = g.load()
    c1, c2 = (27, 94, 32), (67, 160, 71)  # dark green -> light green
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return g


def legacy_icon():
    size = S
    bg = gradient(size).convert("RGBA")
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(bg, (0, 0), m)
    out.alpha_composite(mark(size, 0.96))
    return out


def adaptive_foreground():
    # adaptive icon: 108dp canvas, only the central 66dp is always visible -> shrink the mark into that
    return mark(S, 0.74)


def save(img, path, px):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.resize((px, px), Image.LANCZOS).save(path)


def main():
    leg, fg = legacy_icon(), adaptive_foreground()
    sizes = {"mdpi": (48, 108), "hdpi": (72, 162), "xhdpi": (96, 216), "xxhdpi": (144, 324), "xxxhdpi": (192, 432)}
    for dens, (ic, lay) in sizes.items():
        save(leg, RES / f"mipmap-{dens}" / "ic_launcher.png", ic)
        save(fg, RES / f"mipmap-{dens}" / "ic_launcher_foreground.png", lay)
    (RES / "mipmap-anydpi-v26").mkdir(exist_ok=True)
    (RES / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/ic_launcher_background"/>\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n</adaptive-icon>\n', encoding="utf-8")
    (RES / "values" / "ic_launcher_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#2E7D32</color>\n</resources>\n',
        encoding="utf-8")
    prev = Path(__file__).resolve().parent.parent / "docs" / "icon_preview.png"
    prev.parent.mkdir(exist_ok=True)
    sheet = Image.new("RGBA", (1100, 560), (240, 244, 240, 255))
    sheet.alpha_composite(leg.resize((512, 512), Image.LANCZOS), (20, 24))
    circ = Image.new("RGBA", (440, 440), (0, 0, 0, 0))
    bgc = Image.new("RGBA", (440, 440), (46, 125, 50, 255))
    mc = Image.new("L", (440, 440), 0)
    ImageDraw.Draw(mc).ellipse([0, 0, 439, 439], fill=255)
    circ.paste(bgc, (0, 0), mc)
    circ.alpha_composite(fg.resize((440, 440), Image.LANCZOS))
    circ.putalpha(mc)
    sheet.alpha_composite(circ, (600, 60))
    sheet.save(prev)
    print("icons written; preview at", prev)


main()
