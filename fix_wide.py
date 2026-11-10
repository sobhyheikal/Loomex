"""
Run from the Loomex project folder:   python3 fix_wide.py

Desktop hero uses the new wide banner (with empty wall at the top), with the text centered over that
wall exactly like the phone layout. Phones are untouched. A .bak copy is saved first. Safe to re-run.
"""
import shutil
import sys
from pathlib import Path

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")
if "/* wide hero */" in t:
    sys.exit("templates.py: already done, nothing to do.")

old_css = (
    "\n/* stacked hero */\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero { display: flex; flex-direction: column-reverse; align-items: stretch; }\n"
    "  .hp-hero .hp-wrap { position: static; z-index: auto; padding: 56px 32px 28px; }\n"
    "  .hp-hero-bg { margin-top: 0; }\n"
    "  .hp-hero-bg::after { background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,0) 12%); }\n"
    "}\n"
)
new_css = (
    "\n/* wide hero */\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero { --vw: min(0.38vw, 6px); }\n"
    "  .hp-hero-bg { margin-top: 0; }\n"
    "  .hp-hero-bg::after { background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,.6) 8%, rgba(33,30,26,0) 28%); }\n"
    "}\n"
)
old_img = "hero%20section/banner%20img.jpeg"
new_img = "hero%20section/banner-wide.jpeg"
for old, label in ((old_css, "stacked hero block (run fix_stacked.py first)"), (old_img, "HERO_BANNER address")):
    if t.count(old) != 1:
        sys.exit(f"Stopped: expected 1 match for '{label}' but found {t.count(old)}. Nothing was changed.")
t = t.replace(old_css, new_css, 1).replace(old_img, new_img, 1)
shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(t, encoding="utf-8")
print("templates.py: desktop hero now uses banner-wide.jpeg with the text over the top wall")
print("Upload banner-wide.jpeg to Supabase first, then restart the server and hard-refresh (Cmd+Shift+R).")
