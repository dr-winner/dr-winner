#!/usr/bin/env python3
"""Generate the animated SOC-console hero SVG for dr-winner's GitHub profile.
Single looping timeline: every animated attribute is one <animate dur=CYCLE
repeatCount=indefinite> driven by values/keyTimes, so all lines stay in sync
and the typing loop is seamless. Works when embedded as <img> on GitHub."""

CYCLE = 13.0
W, H = 900, 320
FS = 18            # body mono size
ADV = FS * 0.60    # mono char advance
BX = 40            # body left x
TOP = 92           # first baseline
LH = 31            # line height

# palette — emerald terminal
C = dict(
    prompt="#3fb950", cmd="#c9d6e8", name="#f0fff5", role="#9fb8a6",
    dot_g="#3fb950", green="#7ee787", cyan="#56d364", amber="#f0b429",
    muted="#5f7a68", tbar="#6b8a76", sep="#3fb950",
)

def kt(t):  # clamp to [0,1]
    return max(0.0, min(1.0, t / CYCLE))

# Each line: (segments, start, dur, is_output_big, is_cursor)
# segments = list of (text, color, bold)  -> rendered as tspans; width from char count
lines = [
    ([("❯ ", C["prompt"], True), ("whoami", C["cmd"], False)], 0.5, 0.55, False, False),
    ([("drWinner", C["name"], True)], 1.2, 1.05, True, False),
    ([("❯ ", C["prompt"], True), ("cat role.txt", C["cmd"], False)], 2.5, 0.75, False, False),
    ([("SOC Analyst", C["role"], False), ("  ·  ", C["sep"], True), ("Pentester", C["role"], False),
      ("  ·  ", C["sep"], True), ("AI Engineer", C["role"], False), ("  ·  ", C["sep"], True),
      ("Web3 Builder", C["role"], False)], 3.4, 1.55, False, False),
    ([("❯ ", C["prompt"], True), ("systemctl status --now", C["cmd"], False)], 5.2, 1.0, False, False),
    ([("● ONLINE", C["green"], True), ("   ▲ 44-day streak", C["amber"], False),
      ("   ◆ open to work", C["cyan"], False)],
     6.4, 1.5, False, False),
    ([("❯ ", C["prompt"], True)], 8.4, 0.2, False, True),
]

def seg_len(segs):
    return sum(len(t) for t, _, _ in segs)

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

parts = []
parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="drWinner — SOC Analyst, Pentester, AI Engineer, Web3 Builder">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0c1424"/>
    <stop offset="1" stop-color="#06090f"/>
  </linearGradient>
  <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#0e1a2e"/>
    <stop offset="1" stop-color="#0a1220"/>
  </linearGradient>
  <radialGradient id="glow" cx="0.5" cy="0.0" r="1.0">
    <stop offset="0" stop-color="#3fb950" stop-opacity="0.12"/>
    <stop offset="0.6" stop-color="#3fb950" stop-opacity="0"/>
  </radialGradient>
  <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">
    <circle cx="1" cy="1" r="1" fill="#1f9c52" fill-opacity="0.07"/>
  </pattern>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="tglow" x="-40%" y="-60%" width="180%" height="220%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="4" result="b"/>
    <feFlood flood-color="#3fb950" flood-opacity="0.85"/>
    <feComposite in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="body"><rect x="9" y="53" width="{W-18}" height="{H-62}"/></clipPath>
</defs>

<!-- window -->
<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="16" fill="url(#bg)" stroke="#1a3a2a" stroke-width="1.5"/>
<rect x="6" y="6" width="{W-12}" height="{H-12}" rx="16" fill="url(#glow)"/>
<g clip-path="url(#body)"><rect x="9" y="53" width="{W-18}" height="{H-62}" fill="url(#grid)"/></g>

<!-- title bar -->
<g font-family="'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace">
  <circle cx="34" cy="30" r="6.5" fill="#ff5f57"/><circle cx="56" cy="30" r="6.5" fill="#f0b429"/><circle cx="78" cy="30" r="6.5" fill="#3fb950"/>
  <text x="{W/2}" y="35" text-anchor="middle" font-size="13.5" fill="{C['tbar']}" letter-spacing="0.5">dr-winner@soc: ~/profile</text>
  <!-- signal bars (right) -->
  <g transform="translate({W-70},20)">''')
# animated signal bars in title bar
import math
for i, bh in enumerate([6, 10, 14, 18]):
    x = i * 8
    vals = ";".join(f"{v:.0f}" for v in [bh, bh*0.4, bh, bh*0.6, bh])
    parts.append(f'<rect x="{x}" y="{22-bh}" width="5" height="{bh}" rx="1.5" fill="#3fb950" fill-opacity="0.75">'
                 f'<animate attributeName="height" dur="1.8s" repeatCount="indefinite" values="{vals}" keyTimes="0;0.25;0.5;0.75;1"/>'
                 f'<animate attributeName="y" dur="1.8s" repeatCount="indefinite" values="{22-bh};{22-bh*0.4:.0f};{22-bh};{22-bh*0.6:.0f};{22-bh}" keyTimes="0;0.25;0.5;0.75;1"/></rect>')
parts.append(f'''  </g>
  <line x1="9" y1="52" x2="{W-9}" y2="52" stroke="#16233c" stroke-width="1.2"/>
</g>

<!-- scanline -->
<g clip-path="url(#body)">
  <rect x="9" y="0" width="{W-18}" height="2.5" fill="#3fb950" fill-opacity="0.10">
    <animate attributeName="y" dur="6s" repeatCount="indefinite" values="53;{H-14};53" keyTimes="0;0.6;1"/>
  </rect>
</g>

<!-- body -->
<g font-family="'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace" font-size="{FS}">''')

for idx, (segs, start, dur, big, cursor) in enumerate(lines):
    y = TOP + idx * LH
    fs = 23 if big else FS
    adv = fs * 0.60
    n = seg_len(segs)
    textw = n * adv
    clipw = textw + 44
    # keyTimes for typing reveal over CYCLE
    t0, t1 = kt(start), kt(start + dur)
    # clip rect grows 0 -> clipw
    cid = f"c{idx}"
    parts.append(f'<clipPath id="{cid}"><rect x="{BX-4}" y="{y-fs}" width="0" height="{fs+10}">'
                 f'<animate attributeName="width" dur="{CYCLE}s" repeatCount="indefinite" '
                 f'values="0;0;{clipw:.0f};{clipw:.0f}" keyTimes="0;{t0:.4f};{t1:.4f};1" calcMode="linear"/></rect></clipPath>')
    # line text
    fill_first = segs[0][1]
    weight = 'font-weight="700"' if any(b for _, _, b in segs) else ''
    extra = 'filter="url(#tglow)"' if big else ''
    parts.append(f'<g clip-path="url(#{cid})"><text x="{BX}" y="{y}" font-size="{fs}" {extra}>')
    for t, col, bold in segs:
        fw = ' font-weight="700"' if bold else ''
        parts.append(f'<tspan fill="{col}"{fw}>{esc(t)}</tspan>')
    parts.append('</text></g>')
    # caret
    caret_x = BX + textw + 2
    if cursor:
        # blinking caret after prompt types in
        bt = kt(start + dur)
        parts.append(f'<rect x="{caret_x:.0f}" y="{y-fs+3}" width="{adv*0.9:.0f}" height="{fs+1}" fill="#3fb950">'
                     f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                     f'values="0;0;1;0;1;0;1;0;1;0;1" keyTimes="0;{bt:.4f};{bt+0.001:.4f};'
                     f'{kt(start+dur+0.5):.4f};{kt(start+dur+1.0):.4f};{kt(start+dur+1.5):.4f};'
                     f'{kt(start+dur+2.0):.4f};{kt(start+dur+2.5):.4f};{kt(start+dur+3.0):.4f};'
                     f'{kt(start+dur+3.5):.4f};1"/></rect>')
    else:
        # moving caret that rides the typing edge, then disappears
        ct0, ct1 = kt(start), kt(start + dur)
        parts.append(f'<rect y="{y-fs+3}" x="{BX-2}" width="{adv*0.9:.0f}" height="{fs+1}" fill="#3fb950" opacity="0">'
                     f'<animate attributeName="x" dur="{CYCLE}s" repeatCount="indefinite" '
                     f'values="{BX-2};{BX-2};{caret_x:.0f};{caret_x:.0f}" keyTimes="0;{ct0:.4f};{ct1:.4f};1"/>'
                     f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                     f'values="0;0;1;1;0;0" keyTimes="0;{ct0:.4f};{min(ct0+0.001,1):.4f};{ct1:.4f};{min(ct1+0.02,1):.4f};1"/></rect>')

parts.append('</g>\n</svg>\n')

import os
os.makedirs("assets", exist_ok=True)
with open("assets/hero-console.svg", "w") as f:
    f.write("".join(parts))
print("hero written:", len("".join(parts)), "bytes")
