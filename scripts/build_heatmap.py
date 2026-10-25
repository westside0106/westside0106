#!/usr/bin/env python3
"""Generate a custom neon GitHub contribution heatmap and animated SVG snake.

Uses the GitHub GraphQL contribution calendar. Private contributions depend on
the token's visibility; never invent missing days or contribution counts.
"""
import datetime as dt
import html
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

USER = "westside0106"
QUERY = """query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{contributionDays{date contributionCount}}
      }
    }
  }
}"""
PALETTE = ["#17213d", "#32276e", "#6241b6", "#a25cf4", "#66dcff"]


def get_calendar():
    token = os.environ["GH_TOKEN"]
    payload = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    request = Request(
        "https://api.github.com/graphql", payload,
        {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
         "User-Agent": "westside0106-profile-art"}
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(str(result["errors"]))
    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return calendar["totalContributions"], calendar["weeks"]


def make_svg(total, weeks):
    # GitHub returns up to 53 calendar weeks (Sunday-first).
    count = len(weeks)
    width = 1080
    left, top, step, cell = 49, 167, 18, 13
    last = max((day["contributionCount"] for week in weeks for day in week["contributionDays"]), default=1)
    last = max(last, 1)
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 400" role="img" aria-label="SyFy16 contribution heatmap with animated snake">',
        '<defs>',
        '<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#101a3b"/><stop offset=".58" stop-color="#090f25"/><stop offset="1" stop-color="#160d35"/></linearGradient>',
        '<linearGradient id="line" x2="1" y2="0"><stop stop-color="#9156ff"/><stop offset=".55" stop-color="#58d9ff"/><stop offset="1" stop-color="#e59dff"/></linearGradient>',
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '</defs>',
        '<rect width="1080" height="400" rx="24" fill="url(#bg)"/>',
        '<rect x="1" y="1" width="1078" height="398" rx="23" fill="none" stroke="#39466d"/>',
        '<text x="48" y="58" font-family="Arial,sans-serif" font-size="27" font-weight="700" fill="#f4f5ff">ACTIVITY // SYFY16</text>',
        '<text x="48" y="87" font-family="Arial,sans-serif" font-size="16" fill="#aab7d5">Real GitHub contributions · rolling 12 months</text>',
        f'<text x="1030" y="60" text-anchor="end" font-family="Arial,sans-serif" font-size="31" font-weight="700" fill="#80e6ff">{total:,}</text>',
        '<text x="1030" y="84" text-anchor="end" font-family="Arial,sans-serif" font-size="14" fill="#aab7d5">API contributions</text>',
        '<path d="M48 108H1032" stroke="#2b3658"/>',
    ]
    positions = []
    for col, week in enumerate(weeks):
        days = week["contributionDays"]
        for day in days:
            weekday = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
            x, y = left + col * step, top + weekday * step
            n = day["contributionCount"]
            level = 0 if n == 0 else (1 if n < 3 else 2 if n < 7 else 3 if n < 14 else 4)
            elements.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{PALETTE[level]}" stroke="#526292" stroke-opacity=".24"/>')
            positions.append((x + cell / 2, y + cell / 2))
    for row, label in [(0, "SUN"), (2, "TUE"), (4, "THU"), (6, "SAT")]:
        elements.append(f'<text x="14" y="{top + row*step + 10}" font-family="Arial,sans-serif" font-size="10" fill="#8596b9">{label}</text>')
    elements += [
        '<text x="49" y="335" font-family="Arial,sans-serif" font-size="14" fill="#aab7d5">Less</text>',
    ]
    for i, color in enumerate(PALETTE):
        elements.append(f'<rect x="{92 + i*23}" y="322" width="15" height="15" rx="3" fill="{color}"/>')
    elements += [
        '<text x="219" y="335" font-family="Arial,sans-serif" font-size="14" fill="#aab7d5">More</text>',
        '<text x="1030" y="335" text-anchor="end" font-family="Arial,sans-serif" font-size="14" fill="#8fa5d0">DAILY AUTO-UPDATE</text>',
        '<text x="49" y="372" font-family="Arial,sans-serif" font-size="12" fill="#7387b4">Activity is sourced from GitHub GraphQL. Private contributions may be excluded.</text>',
    ]
    # Serpentine path across the contribution grid. No external scripts needed:
    # SVG animateMotion works inside an <img> in most browsers, with a static
    # fallback for reduced-motion or unsupported renderers.
    trail = []
    for col in range(count):
        rows = range(7) if col % 2 == 0 else range(6, -1, -1)
        for row in rows:
            trail.append((left + col*step + cell/2, top + row*step + cell/2))
    path = "M" + " L".join(f"{x:g},{y:g}" for x,y in trail)
    elements.append(f'<path id="snakeRoute" d="{html.escape(path)}" fill="none" stroke="none"/>')
    for index in range(7, -1, -1):
        radius = 3.5 + (7-index)*0.57
        opacity = 0.27 + (7-index)*0.09
        color = "#aa6bff" if index > 3 else "#76eaff"
        elements.append(
            f'<circle r="{radius:.1f}" fill="{color}" opacity="{opacity:.2f}" filter="url(#glow)">'
            f'<animateMotion dur="24s" begin="-{index*0.09:.2f}s" repeatCount="indefinite" rotate="auto">'
            f'<mpath href="#snakeRoute" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="#snakeRoute"/>'
            '</animateMotion></circle>'
        )
    elements.append('</svg>')
    return "\n".join(elements)


def main():
    total, weeks = get_calendar()
    Path("assets").mkdir(exist_ok=True)
    Path("assets/contribution-heatmap.svg").write_text(make_svg(total, weeks), encoding="utf-8")
    print(f"Rendered {len(weeks)} weeks, {total} API contributions")


if __name__ == "__main__":
    main()
