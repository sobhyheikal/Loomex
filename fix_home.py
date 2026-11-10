"""
Run from the Loomex project folder:   python3 fix_home.py

Fixes the stretched homepage:
  * hero text and buttons stop growing past phone size (they still scale on small screens)
  * homepage sections (categories, sets, why, closing) sit in a centered column about 720px wide;
    the hero image, ticker and coloured bands still run edge to edge
A .bak copy is saved first. Safe to re-run.
"""
import re
import shutil
import sys
from pathlib import Path

p = Path("templates.py")
if not p.exists():
    sys.exit("Can't find templates.py. Run this from the Loomex project folder.")
t = p.read_text(encoding="utf-8")
if "--vw: min(1vw" in t:
    sys.exit("templates.py: already fixed, nothing to do.")

start = t.find("@media all {")
if start < 0:
    sys.exit("Stopped: couldn't find the phone hero block. Did you run match_mobile.py first?")
depth, j = 0, start + len("@media all ")
while j < len(t):
    depth += (t[j] == "{") - (t[j] == "}")
    j += 1
    if depth == 0:
        break
block = t[start:j]
if "hp-hero" not in block:
    sys.exit("Stopped: the first '@media all' block isn't the hero block. Nothing was changed.")

new_block = re.sub(r"(\d+(?:\.\d+)?)vw", r"calc(\1 * var(--vw))", block)
new_block = new_block.replace(
    "@media all {",
    "@media all {\n  .hp-hero { --vw: min(1vw, 7px); }\n"
    "  .hp-wrap { max-width: 720px; margin-left: auto; margin-right: auto; }", 1)

shutil.copy2(p, p.with_suffix(".py.bak"))
p.write_text(t[:start] + new_block + t[j:], encoding="utf-8")
print("templates.py: hero sizes capped, homepage sections centered")
print("Restart the server and hard-refresh (Cmd+Shift+R).")
