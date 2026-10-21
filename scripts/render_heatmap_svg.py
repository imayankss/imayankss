#!/usr/bin/env python3
"""
Render data/contributions.json (from fetch_contributions.py) as a GitHub-style
53-week x 7-day heatmap of rounded boxes. The boxes slide in on a diagonal
sweep once (CSS keyframes) and freeze; below sit a Less -> More legend and a
stats footer.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
STATIC=1 emits the finished frame for previews.
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "..", "data", "contributions.json")
OUT = os.path.join(HERE, "..", "contrib-heatmap.svg")
STATIC = bool(os.environ.get("STATIC"))

PROMPT = "mayank@github:~$"

# empty -> brightest; level 5 is a neon top end above GitHub's own four greens
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 22
LEFT_W = 30
MONTH_H = 22
TITLEBAR_H = 30
FOOTER_H = 92

BG_TOP, BG_BOTTOM = "#111722", "#0d1117"
FRAME = "#30363d"
MUTED = "#7d8590"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
GOLD = "#f2cc60"

COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42  # diagonal sweep timing


def level(count, top):
    """Scale to this user's own busiest day; sqrt keeps one huge day from flattening the rest."""
    if count == 0:
        return 0
    return min(5, 1 + int(4.999 * (count / max(top, 1)) ** 0.5))


def weeks(days):
    """Columns of 7 (Sunday first), padding the first week's leading days with None."""
    first = datetime.date.fromisoformat(days[0]["date"])
    col = [None] * ((first.weekday() + 1) % 7)
    out = []
    for d in days:
        col.append(d)
        if len(col) == 7:
            out.append(col)
            col = []
    if col:
        out.append(col + [None] * (7 - len(col)))
    return out


def render(data):
    grid = weeks(data["days"])
    top = max(d["count"] for d in data["days"])
    W = PAD + LEFT_W + len(grid) * STEP - GAP + PAD
    grid_top = TITLEBAR_H + MONTH_H
    grid_left = PAD + LEFT_W
    grid_bottom = grid_top + 7 * STEP - GAP
    H = grid_bottom + FOOTER_H

    css = (".c{opacity:1}" if STATIC else
           "@keyframes cell{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:none}}"
           f".c{{opacity:0;animation:cell {CELL_DUR}s cubic-bezier(.2,.8,.2,1) both}}")
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
             f'text-anchor="middle">{PROMPT} ./contributions.sh --graph</text>')

    # month labels over the first week that contains the 1st..7th
    last_month = None
    for ci, col in enumerate(grid):
        d = next((c for c in col if c), None)
        date = datetime.date.fromisoformat(d["date"])
        if date.month != last_month and date.day <= 7 and ci < len(grid) - 2:
            p.append(f'<text x="{grid_left + ci * STEP}" y="{TITLEBAR_H + 16}" fill="{MUTED}" '
                     f'font-size="10">{date.strftime("%b")}</text>')
        last_month = date.month if date.day <= 7 else last_month
    for ri, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p.append(f'<text x="{PAD}" y="{grid_top + ri * STEP + CELL * 0.8:.1f}" fill="{MUTED}" '
                 f'font-size="9">{name}</text>')

    for ci, col in enumerate(grid):
        for ri, d in enumerate(col):
            if d is None:
                continue
            n = d["count"]
            delay = "" if STATIC else f' style="animation-delay:{ci * COL_T + ri * ROW_T:.3f}s"'
            p.append(f'<rect class="c" x="{grid_left + ci * STEP}" y="{grid_top + ri * STEP}" '
                     f'width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[level(n, top)]}"{delay}>'
                     f'<title>{d["date"]}: {n} contribution{"" if n == 1 else "s"}</title></rect>')

    # legend, right-aligned under the grid
    ly = grid_bottom + 8
    lx = W - PAD - 34 - len(PALETTE) * CELL
    p.append(f'<text x="{lx - 6}" y="{ly + 9}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        p.append(f'<rect x="{lx + i * CELL}" y="{ly}" width="{CELL - 2}" height="{CELL - 2}" rx="2" fill="{c}"/>')
    p.append(f'<text x="{lx + len(PALETTE) * CELL + 4}" y="{ly + 9}" fill="{MUTED}" font-size="10">More</text>')

    sep = ly + CELL + 12
    p.append(f'<line x1="0" y1="{sep}" x2="{W}" y2="{sep}" stroke="{FRAME}"/>')
    best, rng = data["best_day"], data["range"]
    y1, y2 = sep + 24, sep + 48
    p.append(f'<text x="{PAD}" y="{y1}" font-size="13" fill="{MUTED}">'
             f'<tspan fill="{GREEN}" font-weight="700">{data["total_contributions"]:,}</tspan>'
             f' contributions in the last year</text>')
    p.append(f'<text x="{W - PAD}" y="{y1}" font-size="12" fill="{MUTED}" text-anchor="end">'
             f'{rng["start"]} &#8594; {rng["end"]}</text>')
    p.append(f'<text x="{PAD}" y="{y2}" font-size="13" fill="{MUTED}">current streak '
             f'<tspan fill="{ACCENT}" font-weight="700">{data["current_streak"]} days</tspan>'
             f'  &#183;  longest <tspan fill="{ACCENT}" font-weight="700">{data["longest_streak"]} days</tspan>'
             f'  &#183;  active <tspan fill="{ACCENT}" font-weight="700">{data["active_days"]} days</tspan></text>')
    p.append(f'<text x="{W - PAD}" y="{y2}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
             f'<tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    svg = render(json.load(open(IN)))
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(svg):,} bytes")
