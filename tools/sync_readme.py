#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
SCRIPT = ROOT / "paste-to-run.sh"
BEGIN = "<!-- BEGIN GENERATED PASTE-TO-RUN -->"
END = "<!-- END GENERATED PASTE-TO-RUN -->"

text = README.read_text(encoding="utf-8")
script = SCRIPT.read_text(encoding="utf-8").rstrip("\n")
start = text.index(BEGIN) + len(BEGIN)
stop = text.index(END, start)
replacement = f"\n\n```sh\n{script}\n```\n\n"
README.write_text(text[:start] + replacement + text[stop:], encoding="utf-8")
