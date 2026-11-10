"""
Run from the Loomex project folder:   python3 fix_stacked.py

Homepage hero on desktop = the phone layout: eyebrow, big title and the two buttons centered at the
top, with the photo below. Desktop uses the horizontal banner photo, edge to edge; phone keeps the
portrait photo. A .bak copy is saved first. Safe to re-run.
"""
import shutil
import sys
from pathlib import Path

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")
if "/* stacked hero */" in t:
    sys.exit("templates.py: already done, nothing to do.")
if "/* landscape hero */" not in t:
    sys.exit("Stopped: run fix_landscape.py first. Nothing was changed.")

old_desktop = (
    "@media (min-width: 700px) {\n"
    "  .hp-hero::after { background: linear-gradient(to right, rgba(18,15,12,.92) 0%, rgba(18,15,12,.62) 40%, rgba(18,15,12,.08) 75%); }\n"
    "  .hp-hero .hp-wrap { padding-bottom: 90px; }\n"
    "}\n"
)
if t.count(old_desktop) != 1:
    sys.exit(f"Stopped: expected 1 match for the desktop hero block but found {t.count(old_desktop)}. Nothing was changed.")
t = t.replace(old_desktop, "", 1)

head = "@media (max-width: 699px) {"
start = t.find(head, t.find("/* landscape hero */"))
if start < 0:
    sys.exit("Stopped: couldn't find the phone hero block. Nothing was changed.")
depth, j = 0, start + len("@media (max-width: 699px) ")
while j < len(t):
    depth += (t[j] == "{") - (t[j] == "}")
    j += 1
    if depth == 0:
        break
block = "@media all {" + t[start + len(head):j]

desktop = (
    "\n/* stacked hero */\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero { display: flex; flex-direction: column-reverse; align-items: stretch; }\n"
    "  .hp-hero .hp-wrap { position: static; z-index: auto; padding: 56px 32px 28px; }\n"
    "  .hp-hero-bg { margin-top: 0; }\n"
    "  .hp-hero-bg::after { background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,0) 12%); }\n"
    "}\n"
)
t = t[:start] + block + desktop + t[j:]
shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(t, encoding="utf-8")
print("templates.py: desktop hero now stacked like the phone, with the horizontal banner")
print("Restart the server and hard-refresh (Cmd+Shift+R).")
