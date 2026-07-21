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

# languages + stars (one pass over owned repos)
LANG_Q = """{ user(login:"%s"){ repositories(first:100, ownerAffiliations:OWNER, isFork:false){
  nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name color} } } } } } }""" % USER
lang_tot, lang_col, stars_total = {}, {}, 0
for node in gql(LANG_Q, {})["user"]["repositories"]["nodes"]:
    stars_total += node.get("stargazerCount", 0)
    for e in node["languages"]["edges"]:
        n = e["node"]["name"]
        lang_tot[n] = lang_tot.get(n, 0) + e["size"]
        lang_col[n] = e["node"]["color"] or "#56d364"
lsum = sum(lang_tot.values()) or 1
top = sorted(lang_tot.items(), key=lambda x: -x[1])[:5]
langs = [(n, 100 * v / lsum, lang_col[n]) for n, v in top]


def fmt(n): return f"{n:,}"

# ---- Aurora-Glass deck SVG ----------------------------------------------
SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
INK, SUB, MUTE = "#f4f2ff", "#c3bce0", "#8b86ad"
VIOLET, TEAL, PINK = "#a855f7", "#22d3ee", "#ec4899"

W, H = 900, 316
tiles = [
    (fmt(total_all), "Total contributions", VIOLET),
    (fmt(commits_12), "Commits · 12 mo", TEAL),
    (fmt(prs_12), "Pull requests", "#818cf8"),
    (fmt(stars_total), "Stars earned", "#fbbf24"),
    (str(public_repos), "Repositories", PINK),
    (str(followers), "Followers", "#34d399"),
]


def aurora_bg(idp, W, H, rx=24):
    return (f'<defs>'
            f'<linearGradient id="grad{idp}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#150e2e"/><stop offset="0.45" stop-color="#1b1440"/><stop offset="1" stop-color="#0a1630"/></linearGradient>'
            f'<linearGradient id="glass{idp}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0.10"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.02"/></linearGradient>'
            f'<linearGradient id="hair{idp}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0.10"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.28"/></linearGradient>'
            f'<filter id="blur{idp}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="55"/></filter>'
            f'<filter id="ng{idp}" x="-40%" y="-60%" width="180%" height="220%"><feGaussianBlur stdDeviation="2.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<clipPath id="clip{idp}"><rect x="0" y="0" width="{W}" height="{H}" rx="{rx}"/></clipPath>'
            f'</defs>'
            f'<rect x="0" y="0" width="{W}" height="{H}" rx="{rx}" fill="url(#grad{idp})"/>'
            f'<g clip-path="url(#clip{idp})" filter="url(#blur{idp})" opacity="0.9">'
            f'<circle cx="{W*0.16:.0f}" cy="{H*0.22:.0f}" r="150" fill="{VIOLET}" opacity="0.5"/>'
            f'<circle cx="{W*0.85:.0f}" cy="{H*0.30:.0f}" r="140" fill="{TEAL}" opacity="0.4"/>'
            f'<circle cx="{W*0.55:.0f}" cy="{H*0.95:.0f}" r="130" fill="{PINK}" opacity="0.28"/></g>'
            f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="{rx}" fill="url(#glass{idp})" stroke="#ffffff" stroke-opacity="0.14" stroke-width="1.2"/>'
            f'<rect x="14" y="1.5" width="{W-28}" height="1.4" rx="1" fill="url(#hair{idp})"/>')


p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="GitHub stats for {USER}">']
p.append(aurora_bg("m", W, H))
# header row
p.append(f'<circle cx="34" cy="34" r="4" fill="#34d399"/><text x="48" y="39" font-family="{SANS}" font-size="14" font-weight="600" fill="{SUB}">Live from the GitHub API</text>')
p.append(f'<text x="600" y="39" font-family="{SANS}" font-size="12.5" font-weight="600" fill="{MUTE}" letter-spacing="2">TOP LANGUAGES</text>')
p.append(f'<line x1="574" y1="60" x2="574" y2="{H-22}" stroke="#ffffff" stroke-opacity="0.08" stroke-width="1"/>')
# stat cards 3x2
x0, colw, gap, cw, ch = 30, 175, 12, 168, 90
row_y = [64, 166]
for i, (num, label, col) in enumerate(tiles):
    c, r = i % 3, i // 3
    tx, ty = x0 + c * (colw + gap), row_y[r]
    d0 = 0.07 * i
    p.append(f'<g opacity="0"><animate attributeName="opacity" begin="{d0:.2f}s" dur="0.5s" fill="freeze" values="0;1"/>'
             f'<animateTransform attributeName="transform" type="translate" begin="{d0:.2f}s" dur="0.5s" fill="freeze" values="0 10;0 0"/>'
             f'<rect x="{tx}" y="{ty}" width="{cw}" height="{ch}" rx="14" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.10"/>'
             f'<circle cx="{tx+22}" cy="{ty+26}" r="4.5" fill="{col}"/>'
             f'<circle cx="{tx+22}" cy="{ty+26}" r="4.5" fill="{col}" opacity="0.6" filter="url(#ngm)"/>'
             f'<text x="{tx+20}" y="{ty+66}" font-family="{SANS}" font-size="34" font-weight="800" fill="{col}" filter="url(#ngm)">{num}</text>'
             f'<text x="{tx+21}" y="{ty+82}" font-family="{SANS}" font-size="11" font-weight="500" fill="{SUB}" letter-spacing="0.3">{label}</text></g>')
# language bars
bx, bw, by0, bstep = 600, 268, 92, 40
for i, (name, pct, col) in enumerate(langs):
    y = by0 + i * bstep
    p.append(f'<circle cx="{bx+5}" cy="{y-4}" r="4" fill="{col}"/>'
             f'<text x="{bx+20}" y="{y}" font-family="{SANS}" font-size="13" font-weight="500" fill="{INK}">{name}</text>'
             f'<text x="{bx+bw}" y="{y}" text-anchor="end" font-family="{SANS}" font-size="12.5" fill="{SUB}" font-weight="600">{pct:.1f}%</text>'
             f'<rect x="{bx}" y="{y+8}" width="{bw}" height="7" rx="3.5" fill="#ffffff" fill-opacity="0.06"/>'
             f'<rect x="{bx}" y="{y+8}" width="0" height="7" rx="3.5" fill="{col}">'
             f'<animate attributeName="width" begin="{0.3+0.1*i:.2f}s" dur="0.9s" fill="freeze" values="0;{bw*pct/100:.1f}" '
             f'calcMode="spline" keyTimes="0;1" keySplines="0.2 0.7 0.2 1"/></rect>')
p.append("</svg>")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "command-deck.svg"), "w").write("".join(p))

# ---- Aurora heatmap SVG --------------------------------------------------
nW = len(weeks_12)
cell, gap2 = 12, 3
gw = nW * (cell + gap2)
HW, HH = gw + 60, 7 * (cell + gap2) + 78
mx = max((d["contributionCount"] for w in weeks_12 for d in w["contributionDays"]), default=1) or 1
# violet -> teal aurora scale
scale = ["#ffffff14", "#4c1d95", "#6d28d9", "#7c3aed", "#22d3ee"]
def lvl(c):
    if c <= 0: return scale[0]
    return scale[min(4, 1 + int(c / (mx / 4 + 0.001)))]
hp = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{HW}" height="{HH}" viewBox="0 0 {HW} {HH}" fill="none" role="img" aria-label="Contribution heatmap">']
hp.append(aurora_bg("hm", HW, HH, rx=18))
hp.append(f'<text x="26" y="34" font-family="{SANS}" font-size="13.5" font-weight="500" fill="{SUB}">Contributions · last year '
          f'<tspan font-weight="800" fill="{TEAL}">{last["contributionCalendar"]["totalContributions"]:,}</tspan></text>')
ox, oy = 28, 50
di = 0
for wi, w in enumerate(weeks_12):
    for d in w["contributionDays"]:
        wd = dt.date.fromisoformat(d["date"]).weekday()
        row = (wd + 1) % 7
        x = ox + wi * (cell + gap2)
        y = oy + row * (cell + gap2)
        hp.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{lvl(d["contributionCount"])}" opacity="0">'
                  f'<animate attributeName="opacity" begin="{0.0008*di:.3f}s" dur="0.4s" fill="freeze" values="0;1"/></rect>')
        di += 1
hp.append(f'<g transform="translate({HW-150},{HH-24})" font-family="{SANS}"><text x="0" y="10" font-size="10" fill="{MUTE}">less</text>')
for i, cscale in enumerate(scale):
    hp.append(f'<rect x="{34+i*15}" y="1" width="11" height="11" rx="3" fill="{cscale}"/>')
hp.append(f'<text x="{34+5*15+2}" y="10" font-size="10" fill="{MUTE}">more</text></g></svg>')
open(os.path.join(OUT, "heatmap.svg"), "w").write("".join(hp))

print(f"OK total={total_all} commits12={commits_12} prs12={prs_12} cur={cur} long={longest} "
      f"repos={public_repos} followers={followers} langs={[n for n,_,_ in langs]} weeks={nW}")
