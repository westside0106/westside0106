#!/usr/bin/env python3
"""Compact isometric contribution city, last 90 days plus 12-month overview."""
import datetime as dt
import json
import math
import os
from pathlib import Path
from urllib.request import Request, urlopen

USER="westside0106"
Q='query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'

def load():
    req=Request("https://api.github.com/graphql",json.dumps({"query":Q,"variables":{"login":USER}}).encode(),{"Authorization":"Bearer "+os.environ["GH_TOKEN"],"Content-Type":"application/json","User-Agent":"westside-city"})
    with urlopen(req,timeout=30) as f: data=json.load(f)
    if data.get("errors"):raise RuntimeError(str(data["errors"]))
    cal=data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"],sorted((d for w in cal["weeks"] for d in w["contributionDays"]),key=lambda d:d["date"])

def render(total,days):
    recent=days[-90:]
    peak=max((d["contributionCount"] for d in recent),default=1) or 1
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 760" role="img" aria-label="Contribution City">']
    out.append("""<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="#09132b"/><stop offset="1" stop-color="#040716"/></linearGradient><linearGradient id="violet" x2="0" y2="1"><stop stop-color="#c98cff"/><stop offset="1" stop-color="#4e22b9"/></linearGradient><linearGradient id="cyan" x2="0" y2="1"><stop stop-color="#7cefff"/><stop offset="1" stop-color="#2058d9"/></linearGradient><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter></defs>""")
    out.append('<rect width="1000" height="760" rx="25" fill="url(#bg)"/>')
    out.append('<text x="34" y="50" font-family="Arial" font-size="28" font-weight="bold" fill="#fff">CONTRIBUTION CITY</text>')
    out.append(f'<text x="34" y="80" font-family="Arial" font-size="17" fill="#b7a8d9">{sum(d["contributionCount"] for d in recent):,} Beiträge · letzte 90 Tage</text>')
    def xy(col,row):return (475+30*col-40*row,180+16*col+21*row)
    def poly(points,fill,extra=""):
        return '<polygon points="'+ ' '.join(f'{x:.1f},{y:.1f}' for x,y in points)+'" fill="'+fill+'" '+extra+'/>'
    out.append(poly([xy(-.6,-.6),xy(12.8,-.6),xy(12.8,6.8),xy(-.6,6.8)],"#13183b",'stroke="#513c9a" stroke-width="2"'))
    for c in range(13):
        for r in range(7):
            x,y=xy(c,r)
            out.append(poly([(x,y),(x+22,y+12),(x-6,y+27),(x-28,y+15)],"#352762",'fill-opacity=".48" stroke="#604c97" stroke-opacity=".42"'))
    start=dt.date.fromisoformat(recent[0]["date"]) if recent else dt.date.today()
    positions=[]
    for d in recent:
        age=(dt.date.fromisoformat(d["date"])-start).days
        positions.append((age//7,age%7,d["contributionCount"]))
    for c,r,n in sorted(positions,key=lambda v:(v[0]+v[1],v[0])):
        if not n:continue
        x,y=xy(c,r);h=24+160*math.sqrt(n/peak)
        color="url(#cyan)" if (c+r)%4==0 else "url(#violet)"
        top=[(x,y-h),(x+22,y+12-h),(x-6,y+27-h),(x-28,y+15-h)]
        out.append(poly([(x-28,y+15-h),(x,y-h),(x,y),(x-28,y+15)],color))
        out.append(poly([(x,y-h),(x+22,y+12-h),(x+22,y+12),(x,y)],"#2c2077"))
        out.append(poly(top,"#deb7ff"))
    out.append('<text x="35" y="587" font-family="Arial" font-size="15" fill="#c5b6e0">1 Gebäude = 1 aktiver Tag · Höhe = Beiträge</text>')
    out.append('<path d="M35 620H965" stroke="#30274d"/>')
    out.append('<text x="35" y="650" font-family="Arial" font-size="18" font-weight="bold" fill="#f2eaff">JAHRESÜBERSICHT</text>')
    out.append(f'<text x="965" y="650" text-anchor="end" font-family="Arial" font-size="15" fill="#c6b8e6">{total:,} API-Beiträge · 12 Monate</text>')
    weeks=[sum(d["contributionCount"] for d in days[i:i+7]) for i in range(0,len(days),7)]
    peakweek=max(weeks,default=1) or 1
    for i,n in enumerate(weeks):
        x=35+i*930/len(weeks);h=(5+45*math.sqrt(n/peakweek)) if n else 3
        out.append(f'<rect x="{x:.1f}" y="{730-h:.1f}" width="{max(3,930/len(weeks)-4):.1f}" height="{h:.1f}" rx="2" fill="{("#9562ff" if n else "#242440")}"/>')
    out.append('</svg>')
    Path("assets").mkdir(exist_ok=True)
    Path("assets/contribution-city.svg").write_text("\n".join(out),encoding="utf-8")

if __name__=="__main__":render(*load())
