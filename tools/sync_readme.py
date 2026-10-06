#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SCRIPT = ROOT / "paste-to-run.sh"
CODE_BEGIN = "<!-- BEGIN GENERATED PASTE-TO-RUN -->"
CODE_END = "<!-- END GENERATED PASTE-TO-RUN -->"
BUTTON_BEGIN = "<!-- BEGIN COPY BUTTON -->"
BUTTON_END = "<!-- END COPY BUTTON -->"

text = README.read_text(encoding="utf-8")
script = SCRIPT.read_text(encoding="utf-8").rstrip("\n")

start = text.index(CODE_BEGIN) + len(CODE_BEGIN)
stop = text.index(CODE_END, start)
text = text[:start] + f"\n\n```bash\n{script}\n```\n\n" + text[stop:]

repo = os.environ.get("GITHUB_REPOSITORY", "")
if "/" in repo:
    owner, name = repo.split("/", 1)
    copy_url = f"https://{owner}.github.io/{name}/copy.html"
else:
    copy_url = "copy.html"
button = f'\n<a href="{copy_url}"><kbd>📋 Copy paste-to-run.sh</kbd></a>\n'
start = text.index(BUTTON_BEGIN) + len(BUTTON_BEGIN)
stop = text.index(BUTTON_END, start)
text = text[:start] + button + text[stop:]

README.write_text(text, encoding="utf-8")
