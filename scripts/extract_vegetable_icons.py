"""Витягує іконки підкатегорій «Насіння овочів» з аркуша.

Джерело: assets/1b65e965-cfb5-4e4b-8643-f2a98c05a38d.jpg
Запуск: ./venv/bin/python scripts/extract_vegetable_icons.py
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "img" / "catalog" / "subcats"
SRC = (
    Path.home()
    / ".cursor/projects/Users-olegbonislavskyi-Sites/assets"
    / "1b65e965-cfb5-4e4b-8643-f2a98c05a38d.jpg"
)

SLUGS = [
    "tomati",
    "ogirki",
    "pertsi-solodki-ta-gostri",
    "kabachki-tsukini-patisoni",
    "baklazhani",
    "buriaki",
    "morkva",
    "redis-redka",
    "salati-zelen-priani-travi",
    "tsibulia",
    "gorokh-kvasolia-bobi",
    "kapusta",
    "kukurudza",
    "garbuzi-kavuni-dini",
]

# Вертикальні зони лише під малюнки (без підписів)
ICON_ROWS = [
    (18, 118),
    (150, 265),
    (300, 410),
]

TARGET = 320
TARGET_MAX = 220
PAD = 6


def detect_boxes(sheet: Image.Image, y0: int, y1: int):
    px = sheet.load()
    w, h = sheet.size
    ink = [[False] * w for _ in range(h)]
    for y in range(y0, y1):
        for x in range(w):
            r, g, b = px[x, y]
            if (r + g + b) / 3 < 235:
                ink[y][x] = True

    seen = [[False] * w for _ in range(h)]
    boxes = []
    for y in range(y0, y1):
        for x in range(w):
            if not ink[y][x] or seen[y][x]:
                continue
            q = deque([(x, y)])
            seen[y][x] = True
            minx = maxx = x
            miny = maxy = y
            n = 0
            while q:
                cx, cy = q.popleft()
                n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if nx < 0 or ny < y0 or nx >= w or ny >= y1:
                        continue
                    if seen[ny][nx] or not ink[ny][nx]:
                        continue
                    seen[ny][nx] = True
                    q.append((nx, ny))
                    minx = min(minx, nx)
                    maxx = max(maxx, nx)
                    miny = min(miny, ny)
                    maxy = max(maxy, ny)
            bw, bh = maxx - minx + 1, maxy - miny + 1
            if bw >= 40 and bh >= 40 and n >= 180:
                boxes.append([minx, miny, maxx + 1, maxy + 1])

    boxes.sort(key=lambda b: b[0])
    merged = []
    for b in boxes:
        if merged and b[0] <= merged[-1][2] + 12:
            m = merged[-1]
            merged[-1] = [
                min(m[0], b[0]),
                min(m[1], b[1]),
                max(m[2], b[2]),
                max(m[3], b[3]),
            ]
        else:
            merged.append(b)
    return merged


def to_rgba(rgb: Image.Image) -> Image.Image:
    rgb = rgb.convert("RGB")
    w, h = rgb.size
    scale = min(2.6, max(1.0, 170 / max(w, h)))
    if scale > 1.05:
        rgb = rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    rgb = rgb.filter(ImageFilter.MedianFilter(size=3))

    px = rgb.load()
    w, h = rgb.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lum = (r + g + b) / 3.0
            if lum >= 242:
                continue
            if lum < 120:
                a = 255
            elif lum < 200:
                a = int(255 - (lum - 120) * 1.8)
            else:
                a = int(max(0, (242 - lum) * 5.5))
            if a < 18:
                continue
            opx[x, y] = (r, g, b, a)
    return out


def fit_canvas(icon: Image.Image) -> Image.Image:
    px = icon.load()
    w, h = icon.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 20:
                xs.append(x)
                ys.append(y)
    if not xs:
        return Image.new("RGBA", (TARGET, TARGET), (0, 0, 0, 0))
    crop = icon.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))
    bw, bh = crop.size
    scale = TARGET_MAX / max(bw, bh)
    nw, nh = max(1, int(bw * scale)), max(1, int(bh * scale))
    scaled = crop.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (TARGET, TARGET), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((TARGET - nw) // 2, (TARGET - nh) // 2))
    return canvas


def main():
    if not SRC.exists():
        raise SystemExit(f"Немає файлу: {SRC}")

    OUT.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(SRC).convert("RGB")
    w, _ = sheet.size

    crops = []
    for y0, y1 in ICON_ROWS:
        for x0, iy0, x1, iy1 in detect_boxes(sheet, y0, y1):
            crops.append(
                sheet.crop(
                    (
                        max(0, x0 - PAD),
                        max(0, iy0 - PAD),
                        min(w, x1 + PAD),
                        min(y1, iy1 + PAD),
                    )
                )
            )

    print(f"detected {len(crops)} icons, expected {len(SLUGS)}")
    if len(crops) != len(SLUGS):
        raise SystemExit("Кількість іконок не збігається зі списком slug")

    for slug, crop in zip(SLUGS, crops):
        final = fit_canvas(to_rgba(crop))
        path = OUT / f"{slug}.png"
        final.save(path, optimize=True)
        print(f"  -> {path.name}")

    print("done")


if __name__ == "__main__":
    main()
