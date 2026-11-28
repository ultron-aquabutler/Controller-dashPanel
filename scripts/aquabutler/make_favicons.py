#!/usr/bin/env python3
"""
Generate AquaButler favicon set from the sub-mark asset.

Owner: Shuri (AquaButler dev lead)
Purpose: the shipped dashPanel still serves the inherited Aqualink favicons,
so a CPE customer browsing the dashboard sees the wrong brand in the tab.

The sub-mark asset (1024x1024 navy square) contains a droplet glyph above
the AQUABUTLER wordmark with a lot of negative space. At 16x16 the wordmark
is an illegible smudge, so we crop to the droplet glyph only and rebuild
the wordmark-free mark on the canonical navy (#0050b3).

Outputs (all into themes/icons/):
  favicon-16x16.png, favicon-32x32.png, favicon-96x96.png,
  android-icon-36x36.png, android-icon-48x48.png, android-icon-72x72.png,
  android-icon-144x144.png, android-icon-192x192.png,
  apple-icon.png, apple-touch-icon.png (180x180),
  plus themes/icons/favicon.ico

Usage:  python3 scripts/aquabutler/make_favicons.py
Re-runnable; overwrites the generated set in place.
"""

import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
ASSET = os.path.join(
    REPO, "themes", "aquabutler", "assets",
    "aquabutler-submark-placeholder-2026-10-18.jpg",
)
ICONS = os.path.join(REPO, "themes", "icons")

# Canonical AquaButler palette (locked in themes/aquabutler/theme.css).
NAVY = (0, 80, 179, 255)  # #0050b3
LIGHT = (245, 248, 252, 255)  # #f5f8fc

# Fraction of the source square that the droplet glyph occupies.
# Measured from the 1024x1024 asset by scanning for non-background pixels
# (scripts/aquabutler/_measure_glyph.py): the glyph band is
# y 0.430 -> 0.488, x 0.480 -> 0.520. The lower band (y 0.512 -> 0.566)
# is the AQUABUTLER wordmark, which we deliberately drop for the favicon.
# The box below is the glyph band widened to a square and padded so the
# droplet sits centered with breathing room.
GLYPH_BOX = (0.44, 0.40, 0.56, 0.50)

PNG_TARGETS = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "favicon-96x96.png": 96,
    "android-icon-36x36.png": 36,
    "android-icon-48x48.png": 48,
    "android-icon-72x72.png": 72,
    "android-icon-96x96.png": 96,
    "android-icon-144x144.png": 144,
    "android-icon-192x192.png": 192,
    "apple-icon.png": 180,
    "apple-touch-icon.png": 180,
    # The apple-touch-icon-* set is referenced by pages/index.html at
    # 57/60/72/76/114/120/144/152/180. Generate the whole family so
    # every reference resolves to the AquaButler mark.
    "apple-icon-57x57.png": 57,
    "apple-icon-60x60.png": 60,
    "apple-icon-76x76.png": 76,
    "apple-icon-114x114.png": 114,
    "apple-icon-120x120.png": 120,
    "apple-icon-152x152.png": 152,
    "apple-icon-180x180.png": 180,
    # Windows / MS tile set - referenced by pages/index.html
    # (msapplication-TileImage) and by the ms-* browserconfig.
    "ms-icon-70x70.png": 70,
    "ms-icon-144x144.png": 144,
    "ms-icon-150x150.png": 150,
    "ms-icon-310x310.png": 310,
}


def crop_glyph(src):
    """Crop the droplet glyph out of the full sub-mark composition.

    The glyph is tiny relative to the 1024x1024 canvas (measured: x
    0.480->0.520, y 0.430->0.488). We crop a slightly generous box around
    that band and then trim any remaining background margin so the glyph
    fills the crop - otherwise the favicon renders as a speck.
    """
    w, h = src.size
    left, top, right, bottom = GLYPH_BOX
    box = (int(w * left), int(h * top), int(w * right), int(h * bottom))
    glyph = src.crop(box)

    # Trim uniform background border so the glyph fills the crop.
    bg = glyph.getpixel((0, 0))
    px = glyph.load()
    gw, gh = glyph.size
    min_x, min_y, max_x, max_y = gw, gh, -1, -1
    for y in range(gh):
        for x in range(gw):
            c = px[x, y]
            if (abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2])) > 40:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x < 0:  # nothing found - keep the original crop
        return glyph

    # Small pad so the glyph is not flush against the edge.
    pad = 2
    min_x = max(0, min_x - pad)
    min_y = max(0, min_y - pad)
    max_x = min(gw - 1, max_x + pad)
    max_y = min(gh - 1, max_y + pad)
    return glyph.crop((min_x, min_y, max_x + 1, max_y + 1))


def build_base():
    """Return a square RGBA canvas with the droplet centered on navy."""
    src = Image.open(ASSET).convert("RGB")
    glyph = crop_glyph(src)

    # Square the glyph crop (the source crop may be slightly off-square).
    side = max(glyph.size)
    square = Image.new("RGB", (side, side), NAVY[:3])
    square.paste(glyph, ((side - glyph.width) // 2, (side - glyph.height) // 2))

    # Upscale once to a generous working size so downscaling to 16px
    # averages cleanly instead of aliasing.
    work = 512
    square = square.resize((work, work), Image.LANCZOS)
    return square


def main():
    if not os.path.exists(ASSET):
        sys.exit(f"missing sub-mark asset: {ASSET}")

    os.makedirs(ICONS, exist_ok=True)
    base = build_base()

    written = []
    for name, size in sorted(PNG_TARGETS.items()):
        out = base.resize((size, size), Image.LANCZOS)
        path = os.path.join(ICONS, name)
        out.save(path, "PNG", optimize=True)
        written.append(path)

    ico_path = os.path.join(ICONS, "favicon.ico")
    base.save(ico_path, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    written.append(ico_path)

    for p in written:
        print(f"wrote {os.path.relpath(p, REPO)} ({os.path.getsize(p)} bytes)")


if __name__ == "__main__":
    main()
