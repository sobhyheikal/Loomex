"""
Run from the Loomex project folder:   python3 use_landscape.py

Uses banner landscape.jpg as the desktop hero photo, with the text centered over the empty wall at its
top (the same layout as the phone). Phones are untouched. A .bak copy is saved first. Safe to re-run.
"""
import re
import shutil
import sys
from pathlib import Path

URL = ("https://djeqpdphxcjceognytrv.supabase.co/storage/v1/object/public/"
       "product_images/hero%20section/banner%20landscape.jpg")

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")

if len(re.findall(r'HERO_BANNER = "[^"]*"', t)) != 1:
    sys.exit("Stopped: couldn't find the HERO_BANNER line. Nothing was changed.")
new = re.sub(r'(HERO_BANNER = ")[^"]*(")', lambda m: m.group(1) + URL + m.group(2), t, count=1)

stacked = (
    "\n/* stacked hero */\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero { display: flex; flex-direction: column-reverse; align-items: stretch; }\n"
    "  .hp-hero .hp-wrap { position: static; z-index: auto; padding: 56px 32px 28px; }\n"
    "  .hp-hero-bg { margin-top: 0; }\n"
    "  .hp-hero-bg::after { background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,0) 12%); }\n"
    "}\n"
)
wide = (
    "\n/* wide hero */\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero { --vw: min(0.38vw, 6px); }\n"
    "  .hp-hero-bg { margin-top: 0; }\n"
    "  .hp-hero-bg::after { background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,.6) 8%, rgba(33,30,26,0) 28%); }\n"
    "}\n"
)
if "/* wide hero */" not in new:
    if new.count(stacked) != 1:
        sys.exit("Stopped: run fix_stacked.py first (couldn't find the hero block). Nothing was changed.")
    new = new.replace(stacked, wide, 1)

if new == t:
    sys.exit("templates.py: already done, nothing to do.")
shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(new, encoding="utf-8")
print("templates.py: desktop hero now uses banner landscape.jpg, text over the top wall")
print("Restart the server and hard-refresh (Cmd+Shift+R).")
