#!/usr/bin/env python3
"""Aurora-Glass profile art for dr-winner. A full departure from the terminal
theme: deep indigo->violet->teal aurora gradients, drifting glowing orbs,
frosted-glass panels, light type. Produces hero + section headers + stack + now.
Stats/heatmap are produced by build_stats.py in the same visual language.
All self-contained SVG (each file is its own document; ids don't collide)."""
import os

OUT = "assets"
os.makedirs(OUT, exist_ok=True)
SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Consolas,monospace"

# palette
INK = "#f4f2ff"
SUB = "#c3bce0"
MUTE = "#8b86ad"
VIOLET = "#a855f7"
TEAL = "#22d3ee"
PINK = "#ec4899"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def aurora_defs(idp, orbs=True):
    """Shared aurora background defs + a frosted glass look. Caller wraps content."""
    return f'''<defs>
  <linearGradient id="grad{idp}" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#150e2e"/>
    <stop offset="0.45" stop-color="#1b1440"/>
    <stop offset="1" stop-color="#0a1630"/>
  </linearGradient>
  <linearGradient id="txt{idp}" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#e9d5ff"/>
    <stop offset="0.5" stop-color="#c4b5fd"/>
    <stop offset="1" stop-color="#67e8f9"/>
  </linearGradient>
  <linearGradient id="glass{idp}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.10"/>
    <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.045"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0.02"/>
  </linearGradient>
  <linearGradient id="hair{idp}" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/>
    <stop offset="0.5" stop-color="#ffffff" stop-opacity="0.10"/>
    <stop offset="1" stop-color="#ffffff" stop-opacity="0.28"/>
  </linearGradient>
  <filter id="blur{idp}" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="55"/></filter>
  <filter id="soft{idp}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10"/></filter>
</defs>'''


def orbs(idp, W, H):
    """Three drifting blurred colour orbs, clipped to the panel."""
    return f'''<g clip-path="url(#clip{idp})" filter="url(#blur{idp})" opacity="0.9">
    <circle cx="{W*0.16:.0f}" cy="{H*0.20:.0f}" r="150" fill="{VIOLET}" opacity="0.55">
      <animate attributeName="cx" dur="16s" repeatCount="indefinite" values="{W*0.16:.0f};{W*0.22:.0f};{W*0.16:.0f}" keyTimes="0;0.5;1"/>
      <animate attributeName="cy" dur="16s" repeatCount="indefinite" values="{H*0.20:.0f};{H*0.34:.0f};{H*0.20:.0f}" keyTimes="0;0.5;1"/>
    </circle>
    <circle cx="{W*0.82:.0f}" cy="{H*0.30:.0f}" r="140" fill="{TEAL}" opacity="0.42">
      <animate attributeName="cx" dur="19s" repeatCount="indefinite" values="{W*0.82:.0f};{W*0.74:.0f};{W*0.82:.0f}" keyTimes="0;0.5;1"/>
      <animate attributeName="cy" dur="19s" repeatCount="indefinite" values="{H*0.30:.0f};{H*0.16:.0f};{H*0.30:.0f}" keyTimes="0;0.5;1"/>
    </circle>
    <circle cx="{W*0.55:.0f}" cy="{H*0.9:.0f}" r="130" fill="{PINK}" opacity="0.30">
      <animate attributeName="cx" dur="22s" repeatCount="indefinite" values="{W*0.55:.0f};{W*0.62:.0f};{W*0.55:.0f}" keyTimes="0;0.5;1"/>
    </circle>
  </g>'''


def panel_open(idp, W, H, rx=26):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">']
    p.append(aurora_defs(idp))
    p.append(f'<clipPath id="clip{idp}"><rect x="0" y="0" width="{W}" height="{H}" rx="{rx}"/></clipPath>')
    p.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="{rx}" fill="url(#grad{idp})"/>')
    p.append(orbs(idp, W, H))
    # frosted glass overlay + border + top hairline
    p.append(f'<rect x="0.75" y="0.75" width="{W-1.5}" height="{H-1.5}" rx="{rx}" fill="url(#glass{idp})" stroke="#ffffff" stroke-opacity="0.14" stroke-width="1.2"/>')
    p.append(f'<rect x="14" y="1.5" width="{W-28}" height="1.4" rx="1" fill="url(#hair{idp})"/>')
    return p


def dot(x, y, col, r=4):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>'


# ---------------------------------------------------------------- HERO
def build_hero():
    W, H = 900, 340
    idp = "h"
    p = panel_open(idp, W, H, rx=28)
    # eyebrow
    p.append(f'<text x="52" y="82" font-family="{MONO}" font-size="13" letter-spacing="6" fill="{TEAL}" opacity="0.9">SECURITY · WEB · AI</text>')
    # big gradient name
    p.append(f'<text x="50" y="164" font-family="{SANS}" font-size="76" font-weight="800" fill="url(#txt{idp})" letter-spacing="-1">drWinner</text>')
    # blinking availability dot glow near name
    # subtitle
    p.append(f'<text x="52" y="206" font-family="{SANS}" font-size="21" font-weight="500" fill="{SUB}">Detection engineering &amp; agentic AI — I break it, then build it back safer.</text>')
    # role chips
    chips = ["SOC Analyst", "Pentester", "AI Engineer", "Web3 Builder"]
    x = 52
    cy = 250
    for i, c in enumerate(chips):
        tw = len(c) * 8.6
        w = tw + 34
        col = [VIOLET, TEAL, PINK, "#818cf8"][i % 4]
        p.append(f'<g><rect x="{x:.0f}" y="{cy}" width="{w:.0f}" height="34" rx="17" fill="#ffffff" fill-opacity="0.06" stroke="#ffffff" stroke-opacity="0.12"/>')
        p.append(dot(x + 18, cy + 17, col, 3.6))
        p.append(f'<text x="{x+30:.0f}" y="{cy+22}" font-family="{SANS}" font-size="14" font-weight="500" fill="{INK}">{esc(c)}</text></g>')
        x += w + 12
    # status line bottom
    sy = 312
    p.append(dot(60, sy - 4, "#34d399", 5))
    p.append(f'<circle cx="60" cy="{sy-4}" r="5" fill="#34d399" opacity="0.6" filter="url(#soft{idp})"><animate attributeName="opacity" dur="2.2s" repeatCount="indefinite" values="0.2;0.7;0.2" keyTimes="0;0.5;1"/></circle>')
    p.append(f'<text x="76" y="{sy}" font-family="{MONO}" font-size="13.5" fill="{SUB}">Available for work</text>')
    p.append(f'<text x="{76+150}" y="{sy}" font-family="{MONO}" font-size="13.5" fill="{MUTE}">·  open source  ·  44-day streak</text>')
    p.append('</svg>')
    open(f"{OUT}/hero.svg", "w").write("".join(p))


# ---------------------------------------------------------------- SECTION HEADER
def build_header(name, num, title, comment, accent=VIOLET):
    W, H = 900, 58
    idp = f"s{name}"
    p = panel_open(idp, W, H, rx=16)
    # number badge
    p.append(f'<rect x="18" y="15" width="30" height="28" rx="9" fill="#ffffff" fill-opacity="0.06" stroke="#ffffff" stroke-opacity="0.12"/>')
    p.append(f'<text x="33" y="34" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="700" fill="{accent}">{num}</text>')
    # title
    p.append(f'<text x="62" y="37" font-family="{SANS}" font-size="20" font-weight="700" fill="{INK}" letter-spacing="0.2">{esc(title)}</text>')
    # right comment
    p.append(f'<text x="{W-24}" y="36" text-anchor="end" font-family="{MONO}" font-size="12.5" fill="{MUTE}" letter-spacing="0.5">{esc(comment)}</text>')
    p.append('</svg>')
    open(f"{OUT}/hdr-{name}.svg", "w").write("".join(p))


# ---------------------------------------------------------------- STACK
def build_stack():
    rows = [
        ("Web & design",   [("React", TEAL), ("Next.js", "#e9e9ef"), ("TypeScript", "#60a5fa"), ("Tailwind", "#2dd4bf"), ("Figma", "#fb7185")]),
        ("Backend & data", [("Node", "#4ade80"), ("Python", "#60a5fa"), ("PostgreSQL", "#818cf8"), ("MongoDB", "#4ade80"), ("Prisma", "#e9e9ef"), ("Docker", "#38bdf8")]),
        ("Security & web3", [("SOC / Blue-team", "#a3e635"), ("Ethereum", "#c4b5fd"), ("Solidity", "#f0abfc"), ("Hardhat", "#fbbf24")]),
        ("Cloud & ops",    [("AWS", "#fbbf24"), ("GCP", "#60a5fa"), ("Vercel", "#e9e9ef"), ("Git", "#fb7185"), ("Actions", "#a855f7"), ("Bash", "#4ade80")]),
    ]
    W = 900
    row_h = 52
    top = 40
    H = top + len(rows) * row_h + 20
    idp = "stk"
    p = panel_open(idp, W, H, rx=24)
    for i, (label, toks) in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        p.append(f'<text x="34" y="{cy+5:.0f}" font-family="{SANS}" font-size="13.5" font-weight="600" fill="{SUB}">{esc(label)}</text>')
        x = 230
        for name, col in toks:
            tw = len(name) * 7.7
            w = 20 + tw + 16
            p.append(f'<rect x="{x:.0f}" y="{cy-15:.0f}" width="{w:.0f}" height="30" rx="15" fill="#ffffff" fill-opacity="0.055" stroke="#ffffff" stroke-opacity="0.12"/>')
            p.append(dot(x + 15, cy, col, 3.6))
            p.append(f'<text x="{x+27:.0f}" y="{cy+4:.0f}" font-family="{SANS}" font-size="13" font-weight="500" fill="{INK}">{esc(name)}</text>')
            x += w + 9
    p.append('</svg>')
    open(f"{OUT}/stack.svg", "w").write("".join(p))


# ---------------------------------------------------------------- NOW
def build_now():
    rows = [
        ("Security ops", VIOLET, "Agentic AI for the SOC — detections, triage, and automation that removes toil."),
        ("Building",     TEAL,   "Fast, clean interfaces on Next.js + TypeScript; EVM contracts in Solidity + Hardhat."),
        ("Learning",     PINK,   "Detection engineering, cloud security, and applied LLMs for defensive tooling."),
    ]
    W = 900
    row_h = 58
    top = 34
    H = top + len(rows) * row_h + 16
    idp = "now"
    p = panel_open(idp, W, H, rx=24)
    for i, (label, col, desc) in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        p.append(f'<circle cx="42" cy="{cy:.0f}" r="5" fill="{col}"/>')
        p.append(f'<circle cx="42" cy="{cy:.0f}" r="5" fill="{col}" opacity="0.5" filter="url(#soft{idp})"/>')
        p.append(f'<text x="66" y="{cy+5:.0f}" font-family="{SANS}" font-size="15" font-weight="700" fill="{INK}">{esc(label)}</text>')
        p.append(f'<text x="230" y="{cy+5:.0f}" font-family="{SANS}" font-size="13.5" fill="{SUB}">{esc(desc)}</text>')
        if i < len(rows) - 1:
            p.append(f'<rect x="34" y="{cy+row_h/2:.0f}" width="{W-68}" height="1" fill="#ffffff" fill-opacity="0.06"/>')
    p.append('</svg>')
    open(f"{OUT}/now.svg", "w").write("".join(p))


if __name__ == "__main__":
    build_hero()
    build_header("about", "01", "About", "who am i", VIOLET)
    build_header("stack", "02", "Stack", "tools of the trade", TEAL)
    build_header("stats", "03", "Metrics", "live from the api", PINK)
    build_header("now", "04", "Now", "current focus", "#818cf8")
    build_header("connect", "05", "Connect", "say hello", VIOLET)
    build_stack()
    build_now()
    print("aurora chrome written")
