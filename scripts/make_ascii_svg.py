#!/usr/bin/env python3
"""
Turn the prepped portrait (see prep_photo.py) into a monochrome ASCII-art SVG
that prints itself like a terminal: each row is uncovered by a left-to-right
clip wipe with a block cursor riding the edge, rows staggered top -> bottom.
Plays once, then freezes.

GitHub renders <img>-embedded SVGs and runs their SMIL animations (no JS), so
all the motion lives in here.

Usage: python scripts/make_ascii_svg.py [source-prepped.png] [portrait-ascii.svg]
       STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait-ascii.svg")
STATIC = bool(os.environ.get("STATIC"))

NAME = "Mayank Suryavanshi"
PROMPT = "mayank@github:~$"

# light ink on a dark terminal, so bright pixels get dense glyphs (a positive
# image: the face reads as a face). The space is reserved for the background.
RAMP = " .`:-=+*cs#%@"
COLS = int(os.environ.get("COLS", 120))
CHAR_ASPECT = 8 / 15     # monospace cell width / height
GAMMA = 0.9              # <1 lifts mid-tones into denser glyphs
CONTRAST = 1.08
BG_LEVEL = 250           # prep_photo.py paints the background pure white

ART_W = 640
PAD = 20
TITLEBAR_H = 30
STATUS_H = 34

BG_TOP, BG_BOTTOM = "#111722", "#0d1117"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
ACCENT = "#58a6ff"

PRINT_SECONDS = 5.5      # whole portrait prints in this long, at any resolution

# ---- 1. sample the image into a COLS x ROWS character grid -----------------
im = Image.open(SRC).convert("L")
ROWS = round(COLS * im.height / im.width * CHAR_ASPECT)
im = im.resize((COLS, ROWS), Image.LANCZOS)
bg = im.load()
px = ImageEnhance.Contrast(im).enhance(CONTRAST).load()

rows = []
for y in range(ROWS):
    line = []
    for x in range(COLS):
        if bg[x, y] >= BG_LEVEL:
            line.append(" ")
            continue
        # subject pixels start at index 1, so even black hair keeps its silhouette
        idx = 1 + round((px[x, y] / 255.0) ** GAMMA * (len(RAMP) - 2))
        line.append(RAMP[min(idx, len(RAMP) - 1)])
    rows.append("".join(line))

# ---- 2. lay out the SVG ----------------------------------------------------
CELL_W = ART_W / COLS
CELL_H = CELL_W / CHAR_ASPECT
ART_H = ROWS * CELL_H
W = ART_W + PAD * 2
art_top = TITLEBAR_H + 10
status_top = art_top + ART_H + 10
H = status_top + STATUS_H
ROW_DUR = PRINT_SECONDS / ROWS

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient></defs>',
    f'<rect width="{W:.0f}" height="{H:.0f}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1:.0f}" height="{H-1:.0f}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W / 2:.0f}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">{PROMPT} ./portrait.sh</text>')

font_size = CELL_H * 0.86
for ry, line in enumerate(rows):
    if not line.strip():
        continue
    row_y = art_top + ry * CELL_H
    text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H * 0.76:.1f}" fill="{INK}" '
            f'font-size="{font_size:.2f}" textLength="{ART_W}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC:
        p.append(text)
        continue
    begin = ry * ROW_DUR
    p.append(f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
             f'<animate attributeName="width" from="0" to="{ART_W}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    p.append(f'<rect y="{row_y + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" fill="{INK}" opacity="0">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{begin:.3f}s" '
             f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>')

# status bar: "whoami" + the name, then a blinking block cursor
p.append(f'<line x1="0" y1="{status_top:.1f}" x2="{W:.0f}" y2="{status_top:.1f}" stroke="{FRAME}"/>')
sy = status_top + 22
p.append(f'<text x="{PAD}" y="{sy:.1f}" fill="{MUTED}" font-size="13">{PROMPT} whoami '
         f'<tspan fill="{ACCENT}" font-weight="700">{NAME}</tspan></text>')
cursor_x = PAD + len(f"{PROMPT} whoami {NAME} ") * 13 * 0.6
p.append(f'<rect x="{cursor_x:.1f}" y="{sy - 12:.1f}" width="8" height="15" fill="{INK}">'
         f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" '
         f'repeatCount="indefinite"/></rect>')
p.append("</svg>")

svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {len(svg):,} bytes, {W:.0f}x{H:.0f}, {COLS}x{ROWS} chars")
