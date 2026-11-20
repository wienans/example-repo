#!/usr/bin/env python3
"""Compare two sphinx-needs needs.json files and write an HTML report.

Usage: needs_diff.py OLD.json NEW.json OUT.html [--from LABEL] [--to LABEL]

Needs match by ID. A need is changed when its title, content, status or one
of its outgoing links differs. Only system and software requirements count:
the test, coverage and code needs come from generated pages that git does
not track, so two git revisions cannot be compared on them.
"""

import argparse
import difflib
import html
import json
from pathlib import Path

TYPES = ("sys", "swr")
FIELDS = ("title", "content", "status", "refines", "implements", "verifies", "measures")

CSS = """
@page { size: A4; margin: 15mm 12mm; }
body { font: 10.5pt/1.4 "DejaVu Sans", Arial, sans-serif; color: #111; }
h1 { font-size: 18pt; margin: 0 0 4mm; }
h2 { font-size: 14pt; margin: 8mm 0 3mm; border-bottom: 1px solid #999; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; break-after: avoid; }
.need { break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 0 0 3mm; }
th, td { border: 1px solid #ccc; padding: 1.5mm 2mm; text-align: left; vertical-align: top; }
th { background: #f2f2f2; width: 14%; }
pre { font: 8.5pt/1.35 "DejaVu Sans Mono", monospace; white-space: pre-wrap;
      overflow-wrap: anywhere; margin: 0; }
.diff .add { background: #e6ffec; }
.diff .del { background: #ffebe9; }
.diff .hunk { color: #666; }
"""


def load(path: Path, types=TYPES) -> dict:
    """The needs of the current version in a needs.json, by ID."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    needs = data["versions"][data["current_version"]]["needs"]
    return {id_: need for id_, need in needs.items() if need["type"] in types}


def field(need: dict, name: str):
    value = need.get(name)
    if isinstance(value, list):
        return ", ".join(sorted(value))
    return value or ""


def diff(old: dict, new: dict) -> tuple:
    """(added, removed, changed). changed holds (old_need, new_need, fields)."""
    added = [new[i] for i in sorted(new.keys() - old.keys())]
    removed = [old[i] for i in sorted(old.keys() - new.keys())]
    changed = []
    for i in sorted(old.keys() & new.keys()):
        fields = [f for f in FIELDS if field(old[i], f) != field(new[i], f)]
        if fields:
            changed.append((old[i], new[i], fields))
    return added, removed, changed


def esc(value) -> str:
    return html.escape(str(value))


def heading(need: dict) -> str:
    return f'<h3>{esc(need["id"])}: {esc(need["title"])}</h3>'


def need_table(need: dict) -> str:
    rows = [("Type", need.get("type_name") or need["type"])]
    rows += [(f.capitalize(), field(need, f)) for f in FIELDS[2:] if field(need, f)]
    cells = "".join(f"<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in rows)
    content = f'<pre>{esc(need.get("content") or "")}</pre>'
    return f'<table>{cells}<tr><th>Content</th><td>{content}</td></tr></table>'


def content_diff(old: str, new: str) -> str:
    lines = difflib.unified_diff(
        old.splitlines(), new.splitlines(), "before", "after", lineterm=""
    )
    css = {"+": "add", "-": "del", "@": "hunk"}
    out = []
    for line in list(lines)[2:]:
        kind = css.get(line[:1], "")
        out.append(f'<span class="{kind}">{esc(line)}</span>' if kind else esc(line))
    return '<pre class="diff">' + "\n".join(out) + "</pre>"


def change_table(old: dict, new: dict, fields: list) -> str:
    rows = ["<tr><th>Field</th><th>Before</th><th>After</th></tr>"]
    for f in fields:
        if f == "content":
            body = content_diff(old.get("content") or "", new.get("content") or "")
            rows.append(f'<tr><th>Content</th><td colspan="2">{body}</td></tr>')
        else:
            rows.append(
                f"<tr><th>{f.capitalize()}</th><td>{esc(field(old, f))}</td>"
                f"<td>{esc(field(new, f))}</td></tr>"
            )
    return "<table>" + "".join(rows) + "</table>"


def section(title: str, items: list, render) -> str:
    body = "".join(f'<div class="need">{render(item)}</div>' for item in items)
    return f"<h2>{title} ({len(items)})</h2>" + (body or "<p>None.</p>")


def render(old, new: dict, old_label: str, new_label: str) -> str:
    """The report as HTML. old is None when old_label has no Sphinx docs."""
    title = f"Changes from {old_label} to {new_label}"
    if old is None:
        note = (f"<p>{esc(old_label)} has no Sphinx documentation (no "
                f"docs/conf.py), so every requirement of {esc(new_label)} "
                "is listed as added.</p>")
        old = {}
    else:
        note = ""
    added, removed, changed = diff(old, new)
    parts = [
        f"<h1>{esc(title)}</h1>",
        note,
        f"<p>{len(added)} added, {len(removed)} removed, {len(changed)} "
        "changed system and software requirements.</p>",
        section("Added", added, lambda n: heading(n) + need_table(n)),
        section("Removed", removed, lambda n: heading(n) + need_table(n)),
        section("Changed", changed,
                lambda c: heading(c[1]) + change_table(*c)),
    ]
    return (
        f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(title)}</title><style>{CSS}</style></head>"
        f"<body>{''.join(parts)}</body></html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--from", dest="old_label", help="default: OLD's file name")
    parser.add_argument("--to", dest="new_label", help="default: NEW's file name")
    args = parser.parse_args()
    page = render(load(args.old), load(args.new),
                  args.old_label or args.old.name, args.new_label or args.new.name)
    args.out.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
