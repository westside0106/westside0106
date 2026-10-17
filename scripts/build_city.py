#!/usr/bin/env python3
"""Build a static, GitHub-compatible isometric SVG contribution city."""
import datetime as dt
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen

USER = "westside0106"
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""

def load():
    token = os.environ["GH_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = Request("https://api.github.com/graphql", body, {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "westside-profile-city"
    })
    with urlopen(req, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [(wi, di, day) for wi, week in enumerate(weeks)
            for di, day in enumerate(week["contributionDays"])]
    return cal["totalContributions"], days

def build(total, days):
    counts = [d["contributionCount"] for _, _, d in days]
    maxcount = max(counts, default=1) or 1
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 420" role="img" aria-label="GitHub Contribution City">']
    out += ['<defs><linearGradient id="sky" x2="0" y2="1"><stop stop-color="#0b1028"/><stop offset="1" stop-color="#050915"/></linearGradient><linearGradient id="face" x2="0" y2="1"><stop stop-color="#a35dff"/><stop offset="1" stop-color="#4214ae"/></linearGradient><linearGradient id="blue" x2="0" y2="1"><stop stop-color="#4fe6ff"/><stop offset="1" stop-color="#1448d8"/></linearGradient></defs>']
    out += ['<rect width="1300" height="420" rx="20" fill="url(#sky)"/>']
    out += ['<text x="30" y="44" fill="#f4f0ff" font-family="Arial,sans-serif" font-size="25" font-weight="bold">CONTRIBUTION CITY</text>']
    out += [f'<text x="30" y="70" fill="#a99fc9" font-family="Arial,sans-serif" font-size="15">{total:,} contributions · last 12 months</text>']
    out += ['<path d="M25 325 L1050 371 L1245 272 L217 220 Z" fill="#111435" opacity=".68"/>']
    # Paint from back to front: one day = one building, 53 weeks x 7 days.
    for wi, di, day in sorted(days, key=lambda v: (v[0] + v[1], v[0])):
        count = day["contributionCount"]
        x = 50 + wi * 20 + di * 12
        y = 208 + di * 13 - wi * .5
        w, depth = 13, 7
        h = (8 + 104 * math.sqrt(count / maxcount)) if count else 3
        top = y - h
        main = "url(#blue)" if wi % 5 == 0 else "url(#face)"
        opacity = ".95" if count else ".25"
        out += [f'<g opacity="{opacity}"><path d="M{x:.1f} {top:.1f} l{depth} -4 l{w} 0 l-{depth} 4 Z" fill="#c59bff"/>']
        out += [f'<path d="M{x:.1f} {top:.1f} l{w} 0 v{h:.1f} l-{w} 0 Z" fill="{main}"/>']
        out += [f'<path d="M{x+w:.1f} {top:.1f} l{depth} -4 v{h:.1f} l-{depth} 4 Z" fill="#27207f"/></g>']
    for month in (1, 3, 5, 7, 9, 11):
        matching = [(w, d, v) for w, d, v in days if int(v["date"][5:7]) == month]
        if matching:
            w = matching[0][0]
            x = 55 + w * 20
            label = dt.date(2026, month, 1).strftime("%b")
            out += [f'<text x="{x}" y="391" fill="#a69cbd" font-size="12" font-family="Arial,sans-serif">{label}</text>']
    out += ['<text x="1055" y="46" fill="#ab9bc5" font-size="13" font-family="Arial,sans-serif">HEIGHT = DAILY ACTIVITY</text>']
    out += ['<text x="1055" y="67" fill="#8c79c8" font-size="12" font-family="Arial,sans-serif">Live GitHub contributions</text>']
    out += ['</svg>']
    path = Path("assets/contribution-city.svg")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")

if __name__ == "__main__":
    total, days = load()
    build(total, days)
