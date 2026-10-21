#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions fragment
(the same HTML the profile page loads), then write data/contributions.json with
the raw days plus derived stats: total, current/longest streak, best day.

No token, no GraphQL. Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "imayankss")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        sys.exit("no calendar cells found -- GitHub's markup may have changed")

    days = []
    for td in cells:
        tip = tips.get(td.get("id"), "")
        m = re.match(r"([\d,]+) contribution", tip)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": td["data-date"], "count": count, "level": int(td.get("data-level") or 0)})
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # today doesn't break the current streak until it's over
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1
    current = 0
    while i >= 0 and days[i]["count"]:
        current += 1
        i -= 1
    return current, longest


def build(days):
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"]),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {OUT}: {data['total_contributions']} contributions, "
          f"streak {data['current_streak']} (longest {data['longest_streak']})")
