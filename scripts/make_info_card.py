#!/usr/bin/env python3
"""
Hand-authored neofetch-style info card. Each line fades and slides in on a
short stagger (CSS keyframes, plays once). The card's height is matched to the
ASCII portrait so the two sit flush side by side in the README.

Edit the LINES below when your details change, then re-run:
  python scripts/make_info_card.py
  STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
PORTRAIT = os.path.join(HERE, "..", "portrait-ascii.svg")
STATIC = bool(os.environ.get("STATIC"))

# README display widths: portrait + card = heatmap width (370 + 490 = 860)
PORTRAIT_SHOWN_W = 370
CARD_SHOWN_W = 490

USER = "mayank@github"

# ("key", "value") rows; key=None continues the previous value; "" = spacer;
# ("#", "text") = section heading
LINES = [
    ("Role", "AI/ML Engineer"),
    ("Study", "Integrated M.Tech (AI) @ VIT Bhopal"),
    ("Now", "reliability-aware on-device summarization"),
    ("Focus", "NLP · LLM evaluation · forecasting"),
    (None, "fraud-risk modelling · decision support"),
    "",
    ("#", "shipped"),
    ("SecureSwipe", "capacity-aware fraud-risk triage"),
    ("CASA", "deposit-trend forecasting for a bank"),
    ("LeadScore", "customer-360 lead scoring + CLTV"),
    ("AmazonML", "Amazon ML Challenge 2026"),
    "",
    ("Stack", "Python · PyTorch · scikit-learn · XGBoost"),
    (None, "FastAPI · Streamlit · dbt · SQL · Spark"),
    ("Learning", "calibration · abstention · on-device AI"),
    ("Ethos", "evidence over metrics; fail safely"),
    "",
    ("Reach", "linkedin.com/in/imayankss"),
]

W = 600
PAD = 22
TITLEBAR_H = 30
FONT = 13.5
KEY_W = 112

BG_TOP, BG_BOTTOM = "#111722", "#0d1117"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
KEY = "#58a6ff"
HEAD = "#d2a8ff"
GREEN = "#3fb950"
SWATCHES = ["#ff7b72", "#ffa657", "#f2cc60", "#3fb950", "#39c5cf", "#58a6ff", "#d2a8ff", "#e6edf3"]

STAGGER = 0.09
FIRST = 0.35


def portrait_height():
    """Card height that renders at the same on-screen height as the portrait."""
    try:
        head = open(PORTRAIT).read(300)
        pw, ph = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', head).groups())
        return round(ph * PORTRAIT_SHOWN_W / pw * W / CARD_SHOWN_W)
    except (OSError, AttributeError):
        return 450


H = portrait_height()
e = html.escape

css = """
@keyframes in { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: none; } }
.l { opacity: 0; animation: in .45s cubic-bezier(.2,.8,.2,1) both; }
@keyframes blink { 50% { opacity: 0; } }
.cur { animation: blink 1s steps(1) infinite; }
""".strip()
if STATIC:
    css = ".l { opacity: 1; }"

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    f"<style>{css}</style>",
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">{USER}:~$ neofetch</text>')

n = 0


def line(y, inner):
    global n
    p.append(f'<g class="l" style="animation-delay:{FIRST + n * STAGGER:.2f}s">'
             f'<text x="{PAD}" y="{y:.1f}" font-size="{FONT}">{inner}</text></g>')
    n += 1


# header: user@host, then an underline the same length, neofetch-style
y = TITLEBAR_H + 30
line(y, f'<tspan fill="{GREEN}" font-weight="700">mayank</tspan><tspan fill="{MUTED}">@</tspan>'
        f'<tspan fill="{GREEN}" font-weight="700">github</tspan>')
y += 18
line(y, f'<tspan fill="{MUTED}">{"-" * len(USER)}</tspan>')

body = [l for l in LINES]
footer_h = 46
row_h = (H - footer_h - (y + 10)) / len(body)
y += 10
for item in body:
    y += row_h
    if item == "":
        continue
    key, val = item
    if key == "#":
        line(y, f'<tspan fill="{HEAD}">~/{e(val)}</tspan>')
    elif key is None:
        line(y, f'<tspan x="{PAD + KEY_W}" fill="{TEXT}">{e(val)}</tspan>')
    else:
        line(y, f'<tspan fill="{KEY}" font-weight="700">{e(key)}</tspan>'
                f'<tspan x="{PAD + KEY_W}" fill="{TEXT}">{e(val)}</tspan>')

# neofetch colour swatches + a blinking prompt
sw_y = H - footer_h + 8
for i, c in enumerate(SWATCHES):
    p.append(f'<g class="l" style="animation-delay:{FIRST + (n + i * 0.4) * STAGGER:.2f}s">'
             f'<rect x="{PAD + i * 26}" y="{sw_y}" width="22" height="12" rx="2" fill="{c}"/></g>')
cur_x = W - PAD - 8
p.append(f'<rect class="cur" x="{cur_x}" y="{sw_y - 2}" width="8" height="15" fill="{TEXT}"/>')
p.append("</svg>")

svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT}: {len(svg):,} bytes, {W}x{H}")
