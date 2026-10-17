#!/usr/bin/env python3
"""Render a close-up isometric SVG city from actual GitHub contribution data."""
import datetime as dt
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen

USER = "westside0106"
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

def load():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    request = Request("https://api.github.com/graphql", body, {
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Content-Type": "application/json",
        "User-Agent": "westside-city",
    })
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(wi, di, d) for wi, week in enumerate(calendar["weeks"])
            for di, d in enumerate(week["contributionDays"])]
    return calendar["totalContributions"], days

def render(total, days):
    # Show the entire rolling year; hide empty weeks visually by using faint ground tiles.
    weeks = max(w for w, _, _ in days) + 1
    countmax = max((day["contributionCount"] for _, _, day in days), default=1) or 1
    width, height = 1300, 540
    # Fit all weeks into viewport, building footprints are closer and occupy most vertical space.
    step = min(21, 1080 / max(weeks-1, 1))
    ox, oy = 42, 290
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 540" role="img" aria-label="Contribution City">']
    parts.append("""<defs>
<linearGradient id="bg" x2="0" y2="1"><stop stop-color="#0a1029"/><stop offset="1" stop-color="#040713"/></linearGradient>
<linearGradient id="purple" x2="0" y2="1"><stop stop-color="#cf83ff"/><stop offset="1" stop-color="#5420c8"/></linearGradient>
<linearGradient id="blue" x2="0" y2="1"><stop stop-color="#6deeff"/><stop offset="1" stop-color="#194aca"/></linearGradient>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="5"/></filter></defs>""")
    parts.append('<rect width="1300" height="540" rx="22" fill="url(#bg)"/>')
    parts.append('<text x="27" y="43" font-family="Arial" font-weight="bold" font-size="23" fill="#fff">CONTRIBUTION CITY</text>')
    parts.append(f'<text x="27" y="66" font-family="Arial" font-size="14" fill="#b7a9da">{total:,} contributions · rolling 12 months</text>')
    parts.append('<path d="M25 310 L1115 282 L1260 375 L160 427 Z" fill="#171739" opacity=".85"/>')
    for wi, di, d in sorted(days, key=lambda v:(v[1], v[0])):
        amount = d["contributionCount"]
        x = ox + wi*step + di*11
        y = oy + di*17 - wi*.45
        if not amount:
            parts.append(f'<path d="M{x:.1f} {y:.1f} l10 -5 l15 0 l-10 5 Z" fill="#372967" opacity=".36"/>')
            continue
        h = 18 + 174 * math.sqrt(amount/countmax)
        z = y-h
        front = 'blue' if (wi+di)%5==0 else 'purple'
        parts.append(f'<rect x="{x:.1f}" y="{z:.1f}" width="16" height="{h:.1f}" fill="#764cff" opacity=".24" filter="url(#glow)"/>')
        parts.append(f'<path d="M{x:.1f} {z:.1f} l9 -5 l16 0 l-9 5 Z" fill="#dfc0ff"/>')
        parts.append(f'<path d="M{x:.1f} {z:.1f} h16 v{h:.1f} h-16 Z" fill="url(#{front})"/>')
        parts.append(f'<path d="M{x+16:.1f} {z:.1f} l9 -5 v{h:.1f} l-9 5 Z" fill="#26227e"/>')
        for k in range(1, int(h//23)):
            yy=z+k*23
            parts.append(f'<path d="M{x+4:.1f} {yy:.1f} h8" stroke="#e8d5ff" stroke-width="1" opacity=".2"/>')
    previous = None
    for wi, _, d in days:
        month = d["date"][:7]
        if month != previous:
            previous=month
            x=ox+wi*step
            parts.append(f'<text x="{x:.1f}" y="487" font-family="Arial" font-size="12" fill="#a99acb">{dt.date.fromisoformat(month+"-01").strftime("%b")}</text>')
    parts.append('<text x="1080" y="43" fill="#ad9fcd" font-family="Arial" font-size="12">HEIGHT = ACTIVITY</text>')
    parts.append('</svg>')
    Path("assets").mkdir(exist_ok=True)
    Path("assets/contribution-city.svg").write_text("\n".join(parts), encoding="utf-8")

if __name__ == "__main__":
    render(*load())
