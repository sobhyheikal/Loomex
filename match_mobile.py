"""
Run from the Loomex project folder:   python3 match_mobile.py

Makes the customer site use the mobile layout on every screen size, stretched to the full width:
  * static/style.css and templates.py: removes every desktop-only (min-width: 560px and up) CSS block
  * turns the phone-only hero rules (max-width: 699px) on for all screens
  * removes the 560px content-width cap
A .bak copy of each file is saved first. Safe to re-run.
"""
import re
import shutil
import sys
from pathlib import Path

MQ = re.compile(r"@media\s*\(\s*(min|max)-width\s*:\s*(\d+)px\s*\)\s*\{")


def process(text: str):
    out, i, removed, unwrapped = [], 0, 0, 0
    while True:
        m = MQ.search(text, i)
        if not m:
            out.append(text[i:])
            break
        kind, px = m.group(1), int(m.group(2))
        if kind == "min" and px >= 560:
            depth, j = 1, m.end()
            while j < len(text) and depth:
                depth += (text[j] == "{") - (text[j] == "}")
                j += 1
            if depth:
                sys.exit("Stopped: unbalanced braces in a media block. Nothing was changed.")
            out.append(text[i:m.start()])
            if text[j:j + 1] == "\n":
                j += 1
            i = j
            removed += 1
        elif kind == "max" and px == 699:
            out.append(text[i:m.start()])
            out.append("@media all {")
            i = m.end()
            unwrapped += 1
        else:
            out.append(text[i:m.end()])
            i = m.end()
    return "".join(out), removed, unwrapped


def main():
    for name in ("static/style.css", "templates.py"):
        p = Path(name)
        if not p.exists():
            sys.exit(f"Can't find {name}. Run this from the Loomex project folder.")
    for name in ("static/style.css", "templates.py"):
        p = Path(name)
        t = p.read_text(encoding="utf-8")
        new, removed, unwrapped = process(t)
        extra = ""
        if name == "static/style.css":
            new = re.sub(r"--max:\s*560px;", "--max: none;", new)
            new = re.sub(r"--max-wide:\s*1180px;", "--max-wide: none;", new)
            extra = ", width cap removed"
        elif removed or unwrapped:
            new = re.sub(r"style\.css\?v=(\d+)", lambda m: f"style.css?v={int(m.group(1)) + 1}", new, count=1)
            extra = ", style.css version bumped"
        if new == t:
            print(f"{name}: nothing to change (already done)")
            continue
        shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))
        p.write_text(new, encoding="utf-8")
        print(f"{name}: removed {removed} desktop blocks, enabled {unwrapped} phone-only blocks{extra}")
    print("\nDone. Restart the server and hard-refresh the browser (Cmd+Shift+R).")


main()
