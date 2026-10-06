#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SCRIPT = ROOT / "paste-to-run.sh"
CODE_BEGIN = "<!-- BEGIN GENERATED PASTE-TO-RUN -->"
CODE_END = "<!-- END GENERATED PASTE-TO-RUN -->"

text = README.read_text(encoding="utf-8")
script = SCRIPT.read_text(encoding="utf-8").rstrip("\n")

start = text.index(CODE_BEGIN) + len(CODE_BEGIN)
stop = text.index(CODE_END, start)
text = text[:start] + f"\n\n```bash\n{script}\n```\n\n" + text[stop:]

README.write_text(text, encoding="utf-8")
