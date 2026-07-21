#!/usr/bin/env python3
"""Generate the cohesive 'chrome' SVGs so the whole profile reads as ONE console
instead of polished panels wrapped in default-GitHub markdown (grey code-pill
headers + bordered tables). Produces:
  - banner-*.svg   slim terminal section headers (replace `### ❯ ...`)
  - stack.svg      the tech stack as a console panel (replaces bordered table)
  - now.svg        the ./now block as a console panel (replaces bordered table)
All emerald, all hand-built, all served from the repo."""
import os

OUT = "assets"
os.makedirs(OUT, exist_ok=True)
MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace"
ADV = 0.60  # mono advance factor

# shared palette
BG0, BG1 = "#0c1424", "#06090f"
STROKE = "#1a3a2a"
PROMPT = "#3fb950"
CMD = "#eaf5ee"
MUTED = "#6b8a76"
DIM = "#5f7a68"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def defs(idp):
    return f'''<defs>
  <linearGradient id="bg{idp}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>
  <pattern id="grid{idp}" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#1f9c52" fill-opacity="0.05"/></pattern>
  <filter id="ng{idp}" x="-40%" y="-60%" width="180%" height="220%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>'''


# ---- section banner ------------------------------------------------------
def banner(name, cmd, comment):
    W, H = 900, 52
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(cmd)}">']
    p.append(defs(name))
    p.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="12" fill="url(#bg{name})" stroke="{STROKE}" stroke-width="1.3"/>')
    p.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="12" fill="url(#grid{name})"/>')
    # left emerald accent bar
    p.append(f'<rect x="1.5" y="1.5" width="4" height="{H-3}" rx="2" fill="{PROMPT}"/>')
    # prompt + command
    p.append(f'<g font-family="{MONO}" font-size="17">')
    p.append(f'<text x="24" y="33" fill="{PROMPT}" font-weight="700" filter="url(#ng{name})">❯</text>')
    p.append(f'<text x="46" y="33" fill="{CMD}" font-weight="600" letter-spacing="0.3">{esc(cmd)}</text>')
    # blinking caret
    cx = 46 + len(cmd) * 17 * ADV + 12
    p.append(f'<rect x="{cx:.0f}" y="19" width="9" height="18" rx="1" fill="{PROMPT}"><animate attributeName="opacity" dur="1.1s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.5;0.5;1"/></rect>')
    # right comment
    p.append(f'<text x="{W-24}" y="32" text-anchor="end" fill="{DIM}" font-size="12.5" letter-spacing="0.5">{esc(comment)}</text>')
    p.append('</g></svg>')
    open(f"{OUT}/banner-{name}.svg", "w").write("".join(p))


banner("about", "./about.sh", "// who am i")
banner("stack", "cat stack.txt", "// tools of the trade")
banner("stats", "gh stats --summary", "// live from the api")
banner("now", "./now", "// current focus")
banner("connect", "./connect", "// say hello")


# ---- stack panel ---------------------------------------------------------
def window(W, H, title, idp):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    p.append(defs(idp))
    p.append(f'<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="16" fill="url(#bg{idp})" stroke="{STROKE}" stroke-width="1.5"/>')
    p.append(f'<clipPath id="body{idp}"><rect x="9" y="53" width="{W-18}" height="{H-62}"/></clipPath>')
    p.append(f'<g clip-path="url(#body{idp})"><rect x="9" y="53" width="{W-18}" height="{H-62}" fill="url(#grid{idp})"/></g>')
    p.append(f'<g font-family="{MONO}">')
    p.append(f'<circle cx="34" cy="30" r="6.5" fill="#ff5f57"/><circle cx="56" cy="30" r="6.5" fill="#f0b429"/><circle cx="78" cy="30" r="6.5" fill="#3fb950"/>')
    p.append(f'<text x="{W/2}" y="35" text-anchor="middle" font-size="13.5" fill="{MUTED}" letter-spacing="0.5">{esc(title)}</text>')
    p.append(f'<line x1="9" y1="52" x2="{W-9}" y2="52" stroke="#12261a" stroke-width="1.2"/></g>')
    return p


# stack rows: (label, [(name, dotcolor), ...])
rows = [
    ("web & design",   [("React", "#61DAFB"), ("Next.js", "#eef2f0"), ("TypeScript", "#3178C6"), ("Tailwind", "#38B2AC"), ("Figma", "#F24E1E")]),
    ("backend & data", [("Node", "#339933"), ("Python", "#3776AB"), ("PostgreSQL", "#4a9df0"), ("MongoDB", "#47A248"), ("Prisma", "#eef2f0"), ("Docker", "#2496ED")]),
    ("security & web3", [("SOC/Blue-team", "#9fef00"), ("Ethereum", "#c9d6e8"), ("Solidity", "#c88b5a"), ("Hardhat", "#f0b429")]),
    ("cloud & ops",    [("AWS", "#FF9900"), ("GCP", "#4285F4"), ("Vercel", "#eef2f0"), ("Git", "#F05032"), ("Actions", "#3fb950"), ("Bash", "#7ee787")]),
]
W = 900
row_h = 46
top = 74
H = top + len(rows) * row_h + 16
p = window(W, H, "dr-winner@soc: ~/stack", "stk")
p.append(f'<g font-family="{MONO}">')
label_x, tok_x0 = 30, 210
fs = 13.5
for i, (label, toks) in enumerate(rows):
    cy = top + i * row_h + row_h / 2
    p.append(f'<text x="{label_x}" y="{cy+5:.0f}" font-size="13.5" fill="{PROMPT}"><tspan fill="{PROMPT}" font-weight="700">❯ </tspan><tspan fill="{MUTED}">{esc(label)}</tspan></text>')
    x = tok_x0
    for name, dot in toks:
        tw = len(name) * fs * ADV
        pill_w = 16 + 8 + tw + 14
        p.append(f'<rect x="{x:.0f}" y="{cy-13:.0f}" width="{pill_w:.0f}" height="26" rx="13" fill="#0e1a12" stroke="#1c3a26" stroke-width="1"/>')
        p.append(f'<circle cx="{x+14:.0f}" cy="{cy:.0f}" r="3.5" fill="{dot}"/>')
        p.append(f'<text x="{x+24:.0f}" y="{cy+4:.0f}" font-size="{fs}" fill="#d7e6dc">{esc(name)}</text>')
        x += pill_w + 8
p.append('</g></svg>')
open(f"{OUT}/stack.svg", "w").write("".join(p))


# ---- now panel -----------------------------------------------------------
now_rows = [
    ("security ops", "#56d364", "Agentic AI for the SOC — detections, triage, and automation that removes toil."),
    ("building",     "#3fb950", "Fast, clean interfaces on Next.js + TypeScript; EVM contracts in Solidity + Hardhat."),
    ("learning",     "#7ee787", "Detection engineering, cloud security, and applied LLMs for defensive tooling."),
]
W = 900
row_h = 52
top = 74
H = top + len(now_rows) * row_h + 12
p = window(W, H, "dr-winner@soc: ~/now", "now")
p.append(f'<g font-family="{MONO}">')
for i, (label, col, desc) in enumerate(now_rows):
    cy = top + i * row_h + row_h / 2
    p.append(f'<text x="30" y="{cy+5:.0f}" font-size="14"><tspan fill="{PROMPT}" font-weight="700">❯ </tspan><tspan fill="{col}" font-weight="700">{label}</tspan></text>')
    p.append(f'<text x="210" y="{cy+5:.0f}" font-size="13" fill="#b9cdc1">{esc(desc)}</text>')
    if i < len(now_rows) - 1:
        p.append(f'<line x1="30" y1="{cy+row_h/2:.0f}" x2="{W-30}" y2="{cy+row_h/2:.0f}" stroke="#12261a" stroke-width="1"/>')
p.append('</g></svg>')
open(f"{OUT}/now.svg", "w").write("".join(p))

print("chrome written: banners + stack.svg + now.svg")
