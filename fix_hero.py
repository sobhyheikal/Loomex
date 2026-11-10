"""
Run from the Loomex project folder:   python3 fix_hero.py

Homepage hero on desktop = the phone hero: the portrait photo with the text above it,
in a centered column 700px wide. Everything else on the page is untouched.
A .bak copy is saved first. Safe to re-run.
"""
import shutil
import sys
from pathlib import Path

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")
if "/* hero column */" in t:
    sys.exit("templates.py: hero already fixed, nothing to do.")

anchor = ".hp-hero { --vw: min(1vw, 7px); }"
src_old = '<source media="(max-width: 699px)"'
for old, label in ((anchor, "hero size rule (run fix_home.py first)"), (src_old, "hero <picture> source")):
    if t.count(old) != 1:
        sys.exit(f"Stopped: expected 1 match for '{label}' but found {t.count(old)}. Nothing was changed.")

t = t.replace(anchor, anchor + "\n  /* hero column */\n  .hp-hero { max-width: 700px; margin-left: auto; margin-right: auto; }")
t = t.replace(src_old, '<source media="all"')
shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(t, encoding="utf-8")
print("templates.py: hero now matches the phone layout on desktop")
print("Restart the server and hard-refresh (Cmd+Shift+R).")
