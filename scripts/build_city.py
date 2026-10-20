#!/usr/bin/env python3
"""Render a taller, more mobile-friendly SVG contribution city."""
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
    request = Request(
        "https://api.github.com/graphql",
        body,
        {
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "Content-Type": "application/json",
            "User-Agent": "westside-city",
        },
    )
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(wi, di, d) for wi, week in enumerate(calendar["weeks"]) for di, d in enumerate(week["contributionDays"])]
    return calendar["totalContributions"], days


def render(total, days):
    # Taller aspect ratio so the graphic reads larger on mobile.
    width, height = 1180, 760
    start_x = 78
    base_y = 430
    week_step = 18.6
    day_step_x = 12.0
    day_step_y = 15.0
    tile_w = 15.0
    tile_depth = 8.0

    max_count = max((d["contributionCount"] for _, _, d in days), default=1) or 1

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution City">']
    parts.append(
        """<defs>
<linearGradient id="bg" x2="0" y2="1"><stop stop-color="#081128"/><stop offset="1" stop-color="#040713"/></linearGradient>
<linearGradient id="purple" x2="0" y2="1"><stop stop-color="#d391ff"/><stop offset="1" stop-color="#5a26d9"/></linearGradient>
<linearGradient id="blue" x2="0" y2="1"><stop stop-color="#79efff"/><stop offset="1" stop-color="#2257ea"/></linearGradient>
<linearGradient id="right" x2="0" y2="1"><stop stop-color="#6252df"/><stop offset="1" stop-color="#1b1f60"/></linearGradient>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3"/></filter>
</defs>"""
    )
    parts.append(f'<rect width="{width}" height="{height}" rx="24" fill="url(#bg)"/>')
    parts.append('<text x="34" y="50" font-family="Arial" font-weight="700" font-size="24" fill="#ffffff">CONTRIBUTION CITY</text>')
    parts.append(f'<text x="34" y="76" font-family="Arial" font-size="15" fill="#b7a9da">{total:,} contributions · rolling 12 months</text>')
    parts.append('<text x="940" y="50" font-family="Arial" font-size="12" fill="#c4b8e4">HEIGHT = ACTIVITY</text>')

    # Taller, closer ground plane.
    parts.append('<path d="M52 438 L970 408 L1128 534 L214 604 Z" fill="#11153d" opacity="0.92"/>')
    parts.append('<path d="M76 441 L964 412 L1100 521 L224 592 Z" fill="#0d1133" opacity="0.66"/>')

    month_positions = []
    seen_months = set()

    # Draw back to front.
    for wi, di, d in sorted(days, key=lambda item: (item[0] + item[1], item[0], item[1])):
        amount = d["contributionCount"]
        x = start_x + wi * week_step + di * day_step_x
        y = base_y + di * day_step_y - wi * 0.50
        month = d["date"][:7]
        if di == 0 and month not in seen_months:
            seen_months.add(month)
            month_positions.append((x, month))

        if amount == 0:
            parts.append(f'<path d="M{x:.1f} {y:.1f} l{tile_depth:.1f} -4 l{tile_w:.1f} 0 l-{tile_depth:.1f} 4 Z" fill="#41316f" opacity="0.24"/>')
            continue

        rel = amount / max_count
        h = 26 + 220 * (rel ** 0.70)
        top = y - h
        is_blue = (wi + di) % 5 == 0
        glow_color = '#63e7ff' if is_blue else '#8b52ff'
        face = 'url(#blue)' if is_blue else 'url(#purple)'

        # glow body
        parts.append(f'<rect x="{x+2:.1f}" y="{top+10:.1f}" width="{tile_w+1:.1f}" height="{h-3:.1f}" fill="{glow_color}" opacity="0.18" filter="url(#glow)"/>')
        # top face
        parts.append(f'<path d="M{x:.1f} {top:.1f} l{tile_depth:.1f} -5 l{tile_w:.1f} 0 l-{tile_depth:.1f} 5 Z" fill="#e6c8ff" opacity="0.96"/>')
        # front face
        parts.append(f'<path d="M{x:.1f} {top:.1f} h{tile_w:.1f} v{h:.1f} h-{tile_w:.1f} Z" fill="{face}"/>')
        # right face
        parts.append(f'<path d="M{x+tile_w:.1f} {top:.1f} l{tile_depth:.1f} -5 v{h:.1f} l-{tile_depth:.1f} 5 Z" fill="url(#right)"/>')
        # highlight edge
        parts.append(f'<line x1="{x+2:.1f}" y1="{top+4:.1f}" x2="{x+2:.1f}" y2="{y-4:.1f}" stroke="#ffffff" stroke-opacity="0.14" stroke-width="1"/>')
        # window stripes
        stripe_count = max(1, int(h // 26))
        for idx in range(1, stripe_count):
            sy = top + idx * 24
            if sy < y - 6:
                parts.append(f'<line x1="{x+4:.1f}" y1="{sy:.1f}" x2="{x+tile_w-3:.1f}" y2="{sy:.1f}" stroke="#efe0ff" opacity="0.16" stroke-width="1"/>')

    # Month labels at bottom, more breathing room.
    for x, month in month_positions:
        m = dt.date.fromisoformat(month + "-01").strftime("%b")
        parts.append(f'<text x="{x:.1f}" y="690" font-family="Arial" font-size="12" fill="#a99acb">{m}</text>')

    parts.append('</svg>')
    Path('assets').mkdir(exist_ok=True)
    Path('assets/contribution-city.svg').write_text("\n".join(parts), encoding='utf-8')


if __name__ == '__main__':
    render(*load())
