"""
Run from the Loomex project folder:   python3 fix_landscape.py

Homepage hero:
  * desktop / tablet (700px and wider): the horizontal banner photo, edge to edge,
    with the text over the left side (the original desktop design)
  * phone (under 700px): unchanged, the portrait photo with the text above it
A .bak copy is saved first. Safe to re-run.
"""
import shutil
import sys
from pathlib import Path

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")
if "/* landscape hero */" in t:
    sys.exit("templates.py: already done, nothing to do.")

column = "  /* hero column */\n  .hp-hero { max-width: 700px; margin-left: auto; margin-right: auto; }\n"
wrap_rule = "  .hp-wrap { max-width: 720px; margin-left: auto; margin-right: auto; }\n"
for old, label in (((".hp-hero { --vw: min(1vw, 7px); }"), "hero size rule (run fix_home.py first)"),
                   (wrap_rule, "homepage column rule (run fix_home.py first)"),
                   ('<source media="all"', "hero <picture> source")):
    if t.count(old) != 1:
        sys.exit(f"Stopped: expected 1 match for '{label}' but found {t.count(old)}. Nothing was changed.")
start = t.find("@media all {")
if start < 0 or t.find(".hp-hero", start) < 0:
    sys.exit("Stopped: couldn't find the hero block. Nothing was changed.")

new_head = (
    "/* landscape hero */\n"
    ".hp-wrap { max-width: 720px; margin-left: auto; margin-right: auto; }\n"
    ".hp-hero .hp-wrap { max-width: 1180px; padding-left: 32px; padding-right: 32px; }\n"
    "@media (min-width: 700px) {\n"
    "  .hp-hero::after { background: linear-gradient(to right, rgba(18,15,12,.92) 0%, rgba(18,15,12,.62) 40%, rgba(18,15,12,.08) 75%); }\n"
    "  .hp-hero .hp-wrap { padding-bottom: 90px; }\n"
    "}\n"
    "@media (max-width: 699px) {"
)
t = t[:start] + new_head + t[start + len("@media all {"):]
t = t.replace(column, "", 1).replace(wrap_rule, "", 1)
t = t.replace('<source media="all"', '<source media="(max-width: 699px)"', 1)
shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(t, encoding="utf-8")
print("templates.py: desktop uses the horizontal banner, phone keeps the portrait hero")
print("Restart the server and hard-refresh (Cmd+Shift+R).")
