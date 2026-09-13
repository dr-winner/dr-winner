#!/usr/bin/env python3
"""Generate self-hosted GitHub telemetry for the profile README.

Uses only the standard library and GitHub API. The output favors signal over
vanity metrics: contribution history, recent engineering activity, pull
requests, continuity, and the language distribution of owned repositories.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("STATS_USER", "dr-winner")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)

SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace"
BG = "#08141D"
PANEL = "#0C1A24"
LINE = "#243946"
TEXT = "#F2FAF8"
SUB = "#9DB1BB"
MUTE = "#718994"
MINT = "#50E3C2"
BLUE = "#66A3FF"
AMBER = "#FFB86B"

if not TOKEN:
    sys.exit("no token in STATS_TOKEN / GITHUB_TOKEN")


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"stats-{USER}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def rest(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": f"stats-{USER}"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


user = rest(f"users/{USER}")
public_repos = user["public_repos"]
start_year = int(user["created_at"][:4])
now = dt.datetime.now(dt.timezone.utc)

window_query = """query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){ contributionsCollection(from:$from,to:$to){
    totalCommitContributions totalPullRequestContributions
    contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } } } } }"""

day_count = {}
total_all = 0
for year in range(start_year, now.year + 1):
    start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
    data = gql(window_query, {"login": USER, "from": start.isoformat(), "to": end.isoformat()})
    collection = data["user"]["contributionsCollection"]
    total_all += collection["contributionCalendar"]["totalContributions"]
    for week in collection["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            day_count[day["date"]] = day["contributionCount"]

start = now - dt.timedelta(days=365)
last = gql(window_query, {"login": USER, "from": start.isoformat(), "to": now.isoformat()})
last = last["user"]["contributionsCollection"]
commits_12 = last["totalCommitContributions"]
prs_12 = last["totalPullRequestContributions"]
weeks_12 = last["contributionCalendar"]["weeks"]


language_query = """{ user(login:\"%s\"){ repositories(first:100, ownerAffiliations:OWNER, isFork:false){
  nodes{ languages(first:10, orderBy:{field:SIZE,direction:DESC}){ edges{ size node{name color} } } } } } }""" % USER
language_totals = {}
language_colors = {}
for repo in gql(language_query, {})["user"]["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        language_totals[name] = language_totals.get(name, 0) + edge["size"]
        language_colors[name] = edge["node"]["color"] or MINT
language_sum = sum(language_totals.values()) or 1
languages = [
    (name, 100 * size / language_sum, language_colors[name])
    for name, size in sorted(language_totals.items(), key=lambda item: -item[1])[:5]
]


def base_svg(width, height, title):
    return [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" role="img" aria-label="{esc(title)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{PANEL}"/><stop offset="1" stop-color="{BG}"/></linearGradient>
    <linearGradient id="signal" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{MINT}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" stroke="#8EC5D1" stroke-opacity="0.045"/></pattern>
  </defs>
  <rect width="{width}" height="{height}" rx="20" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" rx="20" fill="url(#grid)"/>
  <path d="M1 1H{width - 1}" stroke="url(#signal)" stroke-opacity="0.72"/>
''']


def finish_svg(parts, width, height):
    parts.append(f'<rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="19.25" stroke="#8EC5D1" stroke-opacity="0.20" stroke-width="1.5"/></svg>')
    return "".join(parts)


# Compact telemetry deck
width, height = 900, 230
parts = base_svg(width, height, f"GitHub engineering telemetry for {USER}")
parts.append(f'<text x="28" y="39" font-family="{MONO}" font-size="11.5" font-weight="600" letter-spacing="2" fill="{MINT}">ENGINEERING TELEMETRY / LIVE</text>')
parts.append(f'<text x="872" y="39" text-anchor="end" font-family="{MONO}" font-size="10.5" fill="{MUTE}">GITHUB GRAPHQL</text>')

metrics = [
    (f"{total_all:,}", "CONTRIBUTIONS / ALL TIME", MINT),
    (f"{commits_12:,}", "COMMITS / 12 MONTHS", BLUE),
    (f"{prs_12:,}", "PULL REQUESTS / 12 MONTHS", AMBER),
    (str(public_repos), "PUBLIC REPOSITORIES", "#E681A8"),
]
card_width = 201
for index, (value, label, color) in enumerate(metrics):
    x = 28 + index * 216
    parts.append(f'<rect x="{x}" y="58" width="{card_width}" height="92" rx="12" fill="#FFFFFF" fill-opacity="0.025" stroke="{LINE}"/>')
    parts.append(f'<rect x="{x}" y="58" width="3" height="92" rx="1.5" fill="{color}"/>')
    parts.append(f'<text x="{x + 18}" y="108" font-family="{SANS}" font-size="31" font-weight="750" fill="{TEXT}">{value}</text>')
    parts.append(f'<text x="{x + 18}" y="132" font-family="{MONO}" font-size="9.5" letter-spacing="0.8" fill="{SUB}">{label}</text>')

bar_x, bar_y, bar_width = 28, 174, 844
parts.append(f'<text x="{bar_x}" y="169" font-family="{MONO}" font-size="9.5" letter-spacing="1.1" fill="{MUTE}">OWNED-REPOSITORY LANGUAGE MIX</text>')
position = bar_x
for name, percent, color in languages:
    segment = bar_width * percent / 100
    parts.append(f'<rect x="{position:.1f}" y="180" width="{max(segment - 2, 1):.1f}" height="9" rx="4.5" fill="{color}"/>')
    position += segment
if position < bar_x + bar_width:
    parts.append(f'<rect x="{position:.1f}" y="180" width="{bar_x + bar_width - position:.1f}" height="9" rx="4.5" fill="{LINE}"/>')
legend_x = bar_x
for name, percent, color in languages:
    label_width = max(105, len(name) * 7 + 46)
    parts.append(f'<circle cx="{legend_x + 4}" cy="210" r="3" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 13}" y="214" font-family="{SANS}" font-size="11" fill="{SUB}">{esc(name)} {percent:.0f}%</text>')
    legend_x += label_width
(OUT / "command-deck.svg").write_text(finish_svg(parts, width, height))

# Contribution matrix
width, height = 900, 170
parts = base_svg(width, height, "Contribution activity for the last year")
last_total = last["contributionCalendar"]["totalContributions"]
parts.append(f'<text x="28" y="37" font-family="{MONO}" font-size="11.5" font-weight="600" letter-spacing="1.6" fill="{MINT}">ACTIVITY / 365 DAYS</text>')
parts.append(f'<text x="872" y="37" text-anchor="end" font-family="{SANS}" font-size="12" fill="{SUB}">{last_total:,} contributions</text>')

cell, gap = 11, 4
origin_x, origin_y = 28, 53
maximum = max((day["contributionCount"] for week in weeks_12 for day in week["contributionDays"]), default=1) or 1
scale = ["#152732", "#174B4C", "#1C7A70", "#35B89F", MINT]

def level(count):
    if count <= 0:
        return scale[0]
    return scale[min(4, 1 + int(count / (maximum / 4 + 0.001)))]

for week_index, week in enumerate(weeks_12):
    for day in week["contributionDays"]:
        weekday = (dt.date.fromisoformat(day["date"]).weekday() + 1) % 7
        x = origin_x + week_index * (cell + gap)
        y = origin_y + weekday * (cell + gap)
        parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{level(day["contributionCount"])}"/>')

(OUT / "heatmap.svg").write_text(finish_svg(parts, width, height))
print(f"OK total={total_all} commits12={commits_12} prs12={prs_12} repos={public_repos}")
