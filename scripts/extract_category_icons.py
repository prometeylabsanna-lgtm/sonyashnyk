"""Витягує іконки підкатегорій з category_icons_part_*.png.

Запуск: ./venv/bin/python scripts/extract_category_icons.py
Не перезаписує іконки гілки «Насіння» (4 підкатегорії).
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "img" / "catalog" / "subcats"
ASSETS = Path.home() / ".cursor/projects/Users-olegbonislavskyi-Sites/assets"

PARTS = [
    ASSETS / "category_icons_part_1-8e2b42b4-5332-48f5-ab54-0d085579c719.png",
    ASSETS / "category_icons_part_2-776e3abd-1e0c-42ea-b9b4-cf085f36dca2.png",
    ASSETS / "category_icons_part_3-11c413af-c0db-490d-b5df-9d42d0d52890.png",
    ASSETS / "category_icons_part_4-94e4a89c-965a-4278-9594-f9d1e1921691.png",
    ASSETS / "category_icons_part_5-3f8f672d-2605-41bf-8d86-0da17b13beca.png",
    ASSETS / "category_icons_part_6-730d06d4-4a12-4248-a196-2655b8245292.png",
]
OVERLAPS = [80, 103, 113, 88, 83]

# RGB як у еталона «Насіння»
ART = (100, 112, 97)
TARGET = 320
TARGET_MAX = 220

SKIP = {
    "nasinnia-ovochiv",
    "nasinnia-kvitiv",
    "vagove-nasinnia",
    "gazonni-travi",
}

# blob_id -> slug (після детекції /tmp/icon_blobs)
BLOB_TO_SLUG = {
    0: "buriaki",
    1: "kukurudza",
    2: "redis-redka",
    3: "salati-zelen-priani-travi",
    4: "gorokh-kvasolia-bobi",
    5: "garbuzi-kavuni-dini",
    6: "kapusta",
    7: "baklazhani",
    9: "pertsi-solodki-ta-gostri",
    10: "odnorichni",
    11: "bagatorichni-ta-dvorichni",
    12: "shlangi",
    13: "zapchastini-ta-ziednuvani",
    14: "rozpiliuvachi-ta-zroshuvachi",
    15: "fungitsidi",
    17: "protruiniki",
    18: "prilipachi-ta-adiuvanti",
    19: "sekatori-nozhi-ta-nozhitsi",
    20: "suchkorizi",
    21: "vse-dlia-shcheplennia",  # ніж для щеплення (на аркуші сокири окремо)
    22: "aksesuari",
    23: "vse-dlia-gazonu",
    24: "farba-dlia-derev-pobilka-zamazka",
    25: "lokhina",
    26: "troiandi",
    27: "kali",
    28: "tiulpani",
    29: "smorodina",
    30: "tsibulia-ozima-ta-vesniana",
    31: "krokusi",
    32: "agrus",
    33: "tsibulia",
    34: "kartoplia",
    35: "mikrobiologichni-dobriva-ta-biopreparati",
    37: "dobriva-dlia-gazonu",
    39: "pidkisliuvachi-ta-rozkisliuvachi",
    40: "biodestruktori-dlia-kompostu",
    41: "plastikovi-gorshchiki",
    42: "substrati",
}

# Додаткові розрізані регіони зі злитих блобів: (blob_id, x0_frac, x1_frac) -> slug
SPLIT_BLOBS = {
    16: [
        (0.0, 0.52, "insektitsidi"),
        (0.48, 1.0, "gerbitsidi"),
    ],
    36: [
        (0.0, 0.38, "dobriva-dlia-kvituchikh-roslin"),
        (0.35, 0.72, "dobriva-dlia-khvoinikh-i-vichnozelenikh-roslin"),
    ],
    38: [
        (0.0, 0.55, "dobriva-dlia-plodovo-iagidnikh-i-ovochevikh-kultur"),
        (0.52, 1.0, "mineralni-dobriva"),
    ],
}


def stitch() -> Image.Image:
    imgs = [Image.open(p).convert("RGB") for p in PARTS]
    x = 0
    positions = [0]
    for i, ov in enumerate(OVERLAPS):
        x += imgs[i].width - ov
        positions.append(x)
    total_w = positions[-1] + imgs[-1].width
    h = imgs[0].height
    canvas = Image.new("RGB", (total_w, h), (255, 255, 255))
    for im, xpos in zip(imgs, positions):
        canvas.paste(im, (xpos, 0))
    return canvas


def detect_blobs(canvas: Image.Image):
    from collections import deque

    W, H = canvas.size
    px = canvas.load()

    def is_ink(x, y, thr=160):
        r, g, b = px[x, y]
        return (r + g + b) / 3 < thr

    visited = [[False] * W for _ in range(H)]
    comps = []
    for y in range(H):
        for x in range(W):
            if visited[y][x] or not is_ink(x, y):
                continue
            q = deque([(x, y)])
            visited[y][x] = True
            xs, ys, n = [], [], 0
            while q:
                cx, cy = q.popleft()
                xs.append(cx)
                ys.append(cy)
                n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and not visited[ny][nx] and is_ink(nx, ny):
                        visited[ny][nx] = True
                        q.append((nx, ny))
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            bw, bh = x1 - x0 + 1, y1 - y0 + 1
            if n < 180 or bw < 28 or bh < 28 or bw > 220 or bh > 160:
                continue
            if bw > 150 and bh < 40:
                continue
            comps.append((y0, x0, x1, y1, n))

    used = [False] * len(comps)
    merged = []
    for i, c in enumerate(comps):
        if used[i]:
            continue
        y0, x0, x1, y1, n = c
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j, c2 in enumerate(comps):
                if used[j]:
                    continue
                y0b, x0b, x1b, y1b, nb = c2
                if x0b <= x1 + 18 and x1b >= x0 - 18 and y0b <= y1 + 18 and y1b >= y0 - 18:
                    x0, x1 = min(x0, x0b), max(x1, x1b)
                    y0, y1 = min(y0, y0b), max(y1, y1b)
                    n += nb
                    used[j] = True
                    changed = True
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if bw >= 30 and bh >= 30 and bw <= 240 and bh <= 180 and n >= 200:
            merged.append((y0, x0, x1, y1))
    merged.sort()
    return merged


def crop_icon_region(canvas, box):
    y0, x0, x1, y1 = box
    W, H = canvas.size
    pad = 4
    left, right = max(0, x0 - pad), min(W, x1 + pad + 1)
    top, bottom = max(0, y0 - pad), min(H, y1 + pad + 1)
    full_h = bottom - top
    if full_h > 70:
        bottom = top + int(full_h * 0.72)
    return canvas.crop((left, top, right, bottom))


def to_transparent(rgb: Image.Image, strip_right_arc: bool = False) -> Image.Image:
    rgb = rgb.convert("RGB")
    # легкий апскейл до ~2× якщо дрібна іконка (краща чіткість ніж 3.4× зі старого спрайту)
    w, h = rgb.size
    scale = min(2.5, max(1.0, 160 / max(w, h)))
    if scale > 1.05:
        rgb = rgb.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    # згладити JPEG-шум без сильного розмиття
    rgb = rgb.filter(ImageFilter.MedianFilter(size=3))

    px = rgb.load()
    w, h = rgb.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    opx = out.load()
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            lum = (r + g + b) / 3.0
            if lum >= 232:
                continue
            # прибрати залишок кола праворуч (субстрати)
            if strip_right_arc:
                dist = math.hypot(x - cx, y - cy)
                # дуга біля правого краю купи
                if x > w * 0.62 and abs(dist - w * 0.55) < 6 and lum > 100:
                    continue
            if lum < 110:
                a = 255
            elif lum < 180:
                a = int(255 - (lum - 110) * 2.0)
            else:
                a = int(max(0, (232 - lum) * 4.5))
            if a < 22:
                continue
            opx[x, y] = (*ART, a)
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


def save_slug(slug: str, rgb_crop: Image.Image):
    if slug in SKIP:
        print(f"  skip {slug}")
        return
    strip = slug == "substrati"
    final = fit_canvas(to_transparent(rgb_crop, strip_right_arc=strip))
    path = OUT / f"{slug}.png"
    final.save(path, optimize=True)
    print(f"  -> {path.name}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    canvas = stitch()
    blobs = detect_blobs(canvas)
    print(f"stitched {canvas.size}, blobs={len(blobs)}")

    for i, box in enumerate(blobs):
        crop = crop_icon_region(canvas, box)
        if i in SPLIT_BLOBS:
            for x0f, x1f, slug in SPLIT_BLOBS[i]:
                w = crop.width
                part = crop.crop((int(w * x0f), 0, int(w * x1f), crop.height))
                save_slug(slug, part)
            continue
        slug = BLOB_TO_SLUG.get(i)
        if not slug:
            continue
        save_slug(slug, crop)

    # Тимчасові копії, якщо на аркуші немає окремої іконки (не затираємо вже згенеровані)
    aliases = {
        "kabachki-tsukini-patisoni": "garbuzi-kavuni-dini",
        "malina": "smorodina",
        "biostimuliatori": "mikrobiologichni-dobriva-ta-biopreparati",
        "biozakhist-vid-khvorob-ta-shkidnikiv": "gerbitsidi",
        "zakhist-vid-krotiv-slimakiv-murakh": "farba-dlia-derev-pobilka-zamazka",
        "poliv-krapelnii": "shlangi",
        "keramichni-gorshchiki": "plastikovi-gorshchiki",
        "pokrashchuvachi-gruntiv": "substrati",
        "nartsisi": "tiulpani",
        "giatsinti": "krokusi",
        "liliyi": "kali",
        "gladiolusi": "krokusi",
        "begoniyi-ta-gloksiniyi": "kali",
        "khosti": "lokhina",
        "inshi-tsibulini-ta-bulbi-kvitiv": "tiulpani",
        "inshi-sadzhantsi": "lokhina",
        "sokiri-ta-koluni": "suchkorizi",
        "opriskuvachi": "rozpiliuvachi-ta-zroshuvachi",
        "tomati": "baklazhani",
        "ogirki": "pertsi-solodki-ta-gostri",
        "morkva": "buriaki",
    }
    for dest, src in aliases.items():
        src_path = OUT / f"{src}.png"
        dest_path = OUT / f"{dest}.png"
        if dest in SKIP or not src_path.exists() or dest_path.exists():
            continue
        Image.open(src_path).save(dest_path)
        print(f"  alias {dest} <- {src}")

    print("done")


if __name__ == "__main__":
    main()
