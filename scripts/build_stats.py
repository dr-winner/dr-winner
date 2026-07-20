#!/usr/bin/env python3
"""Regenerate the self-hosted stats SVGs (command-deck + contribution heatmap)
from live GitHub data. Runs in CI (see .github/workflows/stats.yml) and commits
the result, so the profile shows fresh numbers with NO third-party embed that
could rate-limit or 503. Standard library only.

Env:
  STATS_TOKEN or GITHUB_TOKEN  — token for the GitHub API (a classic PAT with
        read:user + repo gives the fullest numbers incl. private contributions).
  STATS_USER                   — login (default: dr-winner)
"""
import json, os, sys, urllib.request, datetime as dt

USER = os.environ.get("STATS_USER", "dr-winner")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")

if not TOKEN:
    sys.exit("no token in STATS_TOKEN / GITHUB_TOKEN")


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": f"stats-{USER}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    if j.get("errors"):
        raise RuntimeError(j["errors"])
    return j["data"]


def rest(path):
    req = urllib.request.Request(f"https://api.github.com/{path}",
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": f"stats-{USER}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ---- fetch ---------------------------------------------------------------
u = rest(f"users/{USER}")
followers, public_repos, created = u["followers"], u["public_repos"], u["created_at"]
start_year = int(created[:4])
now = dt.datetime.now(dt.timezone.utc)

WINDOW_Q = """query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){ contributionsCollection(from:$from,to:$to){
    totalCommitContributions totalPullRequestContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }"""

# per-year loop for all-time total + a full day map for streaks
day_count, total_all = {}, 0
for y in range(start_year, now.year + 1):
    frm = dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc)
    to = min(dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
    d = gql(WINDOW_Q, {"login": USER, "from": frm.isoformat(), "to": to.isoformat()})
    cc = d["user"]["contributionsCollection"]
    total_all += cc["contributionCalendar"]["totalContributions"]
    for w in cc["contributionCalendar"]["weeks"]:
        for cd in w["contributionDays"]:
            day_count[cd["date"]] = cd["contributionCount"]

# last-365d window for commits / PRs / heatmap
frm = now - dt.timedelta(days=365)
last = gql(WINDOW_Q, {"login": USER, "from": frm.isoformat(), "to": now.isoformat()})["user"]["contributionsCollection"]
commits_12 = last["totalCommitContributions"]
prs_12 = last["totalPullRequestContributions"]
weeks_12 = last["contributionCalendar"]["weeks"]

# streaks
dates = sorted(day_count)
cur = longest = run = 0
prev = None
for ds in dates:
    dd = dt.date.fromisoformat(ds)
    if day_count[ds] > 0:
        run = run + 1 if (prev and (dd - prev).days == 1) else 1
        longest = max(longest, run)
        prev = dd
    else:
        prev = dd if False else prev
        run = 0
        prev = dd
# recompute current streak walking back from today (allow today == 0)
cur = 0
d = now.date()
if day_count.get(d.isoformat(), 0) == 0:
    d -= dt.timedelta(days=1)
while day_count.get(d.isoformat(), 0) > 0:
    cur += 1
    d -= dt.timedelta(days=1)

# languages
LANG_Q = """{ user(login:"%s"){ repositories(first:100, ownerAffiliations:OWNER, isFork:false){
  nodes{ languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name color} } } } } } }""" % USER
lang_tot, lang_col = {}, {}
for node in gql(LANG_Q, {})["user"]["repositories"]["nodes"]:
    for e in node["languages"]["edges"]:
        n = e["node"]["name"]
        lang_tot[n] = lang_tot.get(n, 0) + e["size"]
        lang_col[n] = e["node"]["color"] or "#58d0ff"
lsum = sum(lang_tot.values()) or 1
top = sorted(lang_tot.items(), key=lambda x: -x[1])[:5]
langs = [(n, 100 * v / lsum, lang_col[n]) for n, v in top]


def fmt(n): return f"{n:,}"

# ---- deck SVG ------------------------------------------------------------
W, H = 900, 320
tiles = [
    (fmt(total_all), "TOTAL CONTRIBUTIONS", "#58d0ff", "heat"),
    (fmt(commits_12), "COMMITS · 12 MO", "#7ee787", "commit"),
    (fmt(prs_12), "PULL REQUESTS", "#c297ff", "branch"),
    (str(cur), "DAY STREAK · CURRENT", "#f0b429", "flame"),
    (str(public_repos), "REPOSITORIES", "#58d0ff", "repo"),
    (str(followers), "FOLLOWERS", "#7ee787", "user"),
]


def icon(kind, x, y, col):
    g = f'<g stroke="{col}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="translate({x},{y})">'
    if kind == "heat":
        g = f'<g fill="{col}" stroke="none" transform="translate({x},{y})">'
        ops = [0.35,0.9,0.55,0.7,0.4,1,0.5,0.8,0.45]
        for i in range(3):
            for j in range(3):
                g += f'<rect x="{i*6}" y="{j*6}" width="4.4" height="4.4" rx="1" fill-opacity="{ops[i*3+j]}"/>'
    elif kind == "commit":
        g += '<circle cx="8" cy="8" r="3.4"/><path d="M8 0.5V4.6M8 11.4V15.5"/>'
    elif kind == "branch":
        g += '<circle cx="4" cy="3.5" r="2.6"/><circle cx="4" cy="12.5" r="2.6"/><circle cx="13" cy="3.5" r="2.6"/><path d="M4 6.1v3.8M13 6.1c0 4-9 2-9 6.4"/>'
    elif kind == "flame":
        g = f'<g fill="{col}" stroke="none" transform="translate({x},{y})"><path d="M8 0.5c2.6 3 4.6 5 4.6 8.2A4.6 4.6 0 0 1 3.4 8.7c0-1.4.6-2.5 1.5-3.4.2 1 .8 1.7 1.6 2 .2-2.6 .5-4.4 1.5-6.8z"/>'
    elif kind == "repo":
        g += '<rect x="1.5" y="2" width="13" height="12" rx="1.5"/><path d="M1.5 5.5h13M5 2v12"/>'
    elif kind == "user":
        g += '<circle cx="8" cy="5" r="3"/><path d="M2.5 14.5c0-3.3 2.5-5 5.5-5s5.5 1.7 5.5 5"/>'
    return g + "</g>"


p = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats for {USER}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1424"/><stop offset="1" stop-color="#06090f"/></linearGradient>
  <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#1c88c8" fill-opacity="0.05"/></pattern>
  <filter id="ng" x="-40%" y="-60%" width="180%" height="220%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="body"><rect x="9" y="53" width="{W-18}" height="{H-62}"/></clipPath>
</defs>
<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="16" fill="url(#bg)" stroke="#1e2f4d" stroke-width="1.5"/>
<g clip-path="url(#body)"><rect x="9" y="53" width="{W-18}" height="{H-62}" fill="url(#grid)"/></g>
<g font-family="{MONO}">
  <circle cx="34" cy="30" r="6.5" fill="#ff5f57"/><circle cx="56" cy="30" r="6.5" fill="#f0b429"/><circle cx="78" cy="30" r="6.5" fill="#3fb950"/>
  <text x="{W/2}" y="35" text-anchor="middle" font-size="13.5" fill="#6b7a99" letter-spacing="0.5">{USER}@soc: ~/metrics</text>
  <line x1="9" y1="52" x2="{W-9}" y2="52" stroke="#16233c" stroke-width="1.2"/>
  <text x="30" y="80" font-size="13" fill="#5b6b87">❯ gh api /stats --summary <tspan fill="#3fb950">✓ live</tspan></text>
  <line x1="580" y1="70" x2="580" y2="{H-24}" stroke="#16233c" stroke-width="1.2"/>
  <text x="606" y="80" font-size="12.5" fill="#6b7a99" letter-spacing="2">LANGUAGES</text>
</g>
<g font-family="{MONO}">''']
x0, colw, gap, tw, th = 30, 170, 15, 170, 84
row_y = [96, 192]
for i, (num, label, col, ic) in enumerate(tiles):
    c, r = i % 3, i // 3
    tx, ty = x0 + c * (colw + gap), row_y[r]
    d0 = 0.08 * i
    p.append(f'<g opacity="0"><animate attributeName="opacity" begin="{d0:.2f}s" dur="0.5s" fill="freeze" values="0;1"/>'
             f'<animateTransform attributeName="transform" type="translate" begin="{d0:.2f}s" dur="0.5s" fill="freeze" values="0 8;0 0"/>'
             f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="10" fill="#0b1526" stroke="#16233c" stroke-width="1"/>'
             f'<rect x="{tx}" y="{ty}" width="3.5" height="{th}" rx="2" fill="{col}"/>{icon(ic, tx+16, ty+15, col)}'
             f'<text x="{tx+16}" y="{ty+62}" font-size="30" font-weight="700" fill="{col}" filter="url(#ng)">{num}</text>'
             f'<text x="{tx+17}" y="{ty+77}" font-size="10" fill="#6b7a99" letter-spacing="1">{label}</text></g>')
bx, bw, by0, bstep = 606, 250, 108, 37
for i, (name, pct, col) in enumerate(langs):
    y = by0 + i * bstep
    p.append(f'<circle cx="{bx+4}" cy="{y-4}" r="4" fill="{col}"/>'
             f'<text x="{bx+18}" y="{y}" font-size="12.5" fill="#c9d6e8">{name}</text>'
             f'<text x="{bx+bw}" y="{y}" text-anchor="end" font-size="12" fill="#7d8ba5" font-weight="600">{pct:.1f}%</text>'
             f'<rect x="{bx}" y="{y+7}" width="{bw}" height="7" rx="3.5" fill="#0e1a2e"/>'
             f'<rect x="{bx}" y="{y+7}" width="0" height="7" rx="3.5" fill="{col}">'
             f'<animate attributeName="width" begin="{0.3+0.12*i:.2f}s" dur="0.9s" fill="freeze" values="0;{bw*pct/100:.1f}" '
             f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.7 0.2 1"/></rect>')
p.append("</g></svg>")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "command-deck.svg"), "w").write("".join(p))

# ---- heatmap SVG ---------------------------------------------------------
nW = len(weeks_12)
cell, gap2 = 12, 3
gw = nW * (cell + gap2)
HW, HH = gw + 60, 7 * (cell + gap2) + 74
mx = max((day for w in weeks_12 for day in [d["contributionCount"] for d in w["contributionDays"]]), default=1) or 1
scale = ["#0e1a2e", "#0e4a5e", "#157a94", "#22b8d6", "#7dedff"]
def lvl(c):
    if c <= 0: return scale[0]
    return scale[min(4, 1 + int(c / (mx / 4 + 0.001)))]
hp = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{HW}" height="{HH}" viewBox="0 0 {HW} {HH}" role="img" aria-label="Contribution heatmap">
<rect x="1" y="1" width="{HW-2}" height="{HH-2}" rx="14" fill="#0a1120" stroke="#1e2f4d" stroke-width="1.2"/>
<g font-family="{MONO}">
  <text x="24" y="30" font-size="13" fill="#6b7a99">❯ contributions --last-year <tspan fill="#7dedff" font-weight="700">{last["contributionCalendar"]["totalContributions"]:,}</tspan></text>''']
ox, oy = 30, 48
di = 0
for wi, w in enumerate(weeks_12):
    for d in w["contributionDays"]:
        wd = dt.date.fromisoformat(d["date"]).weekday()  # Mon=0
        row = (wd + 1) % 7  # Sun row 0
        x = ox + wi * (cell + gap2)
        y = oy + row * (cell + gap2)
        hp.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{lvl(d["contributionCount"])}" opacity="0">'
                  f'<animate attributeName="opacity" begin="{0.0008*di:.3f}s" dur="0.4s" fill="freeze" values="0;1"/></rect>')
        di += 1
hp.append(f'<g transform="translate({HW-150},{HH-22})" font-family="{MONO}"><text x="0" y="10" font-size="10" fill="#5b6b87">less</text>')
for i, cscale in enumerate(scale):
    hp.append(f'<rect x="{34+i*15}" y="1" width="11" height="11" rx="2.5" fill="{cscale}"/>')
hp.append(f'<text x="{34+5*15+2}" y="10" font-size="10" fill="#5b6b87">more</text></g></g></svg>')
open(os.path.join(OUT, "heatmap.svg"), "w").write("".join(hp))

print(f"OK total={total_all} commits12={commits_12} prs12={prs_12} cur={cur} long={longest} "
      f"repos={public_repos} followers={followers} langs={[n for n,_,_ in langs]} weeks={nW}")
