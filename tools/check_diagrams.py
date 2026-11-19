#!/usr/bin/env python3
"""Validate every Mermaid diagram in the Markdown docs.

Each ```mermaid block under docs/ must follow
docs/02_architecture/00_diagram_conventions.md:

1. Its type is one of ALLOWED_TYPES.
2. The two lines after the type keyword are accTitle and accDescr.
3. Every classDef comes before the first node or edge line.
4. Every classDef and style sets a text color with a WCAG contrast of at
   least MIN_CONTRAST. Node classes are measured against their own fill,
   edge classes (no fill) against the edge label background.
5. No linkStyle, because edges are styled through edge IDs. No reversed
   arrow such as <-.-, because it renders without an arrowhead.
6. A flowchart defines at most MAX_NODES nodes.
7. Mermaid CLI (mmdc) renders it to SVG without an error.

The script writes each block to build/diagrams/ as
<file>_<nn>_<type>_<title>.mmd next to its rendered .svg.
Pass --no-render to skip check 7.
"""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "build" / "diagrams"
PUPPETEER_CONFIG = ROOT / "tools" / "mermaid" / "puppeteer.json"
MERMAID_CONFIG = ROOT / "tools" / "mermaid" / "mermaid.json"

ALLOWED_TYPES = {"flowchart", "sequenceDiagram", "stateDiagram-v2"}
MIN_CONTRAST = 4.5
MAX_NODES = 20
EDGE_LABEL_BACKGROUND = "e8e8e8"
NAMED_COLORS = {
    "black": "000000",
    "white": "ffffff",
    "darkgreen": "006400",
    "darkblue": "00008b",
}

BLOCK = re.compile(r"^```mermaid\n(.*?)^```", re.MULTILINE | re.DOTALL)
HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
STYLE_LINE = re.compile(r"^(classDef|style)\s+(\S+)\s+(.+)$")
NODE_DEF = re.compile(r"(?:^|\s|>|\|)([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[|\(|\{)")
PREAMBLE = ("accTitle", "accDescr", "classDef", "%%", "direction", "autonumber")


def hex_of(value: str) -> str | None:
    value = value.strip().lower()
    if value in NAMED_COLORS:
        return NAMED_COLORS[value]
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if not m:
        return None
    digits = m.group(1)
    return "".join(c * 2 for c in digits) if len(digits) == 3 else digits


def luminance(hex6: str) -> float:
    channels = [int(hex6[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def sanitize(text: str, limit: int) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return text[:limit].rstrip("_")


def body_lines(source: str) -> list[str]:
    return [line.strip() for line in source.splitlines() if line.strip()]


def style_errors(lines: list[str]) -> list[str]:
    errors = []
    for line in lines:
        m = STYLE_LINE.match(line)
        if not m:
            continue
        kind, name, props = m.groups()
        fields = dict(
            (k.strip(), v.strip())
            for k, v in (p.split(":", 1) for p in props.rstrip(";").split(",") if ":" in p)
        )
        if "color" not in fields:
            errors.append(f"{kind} {name} must set color")
            continue
        background = fields.get("fill", "#" + EDGE_LABEL_BACKGROUND)
        fill_hex, color_hex = hex_of(background), hex_of(fields["color"])
        if fill_hex is None or color_hex is None:
            errors.append(f"{kind} {name}: unknown color {background!r} or {fields['color']!r}")
            continue
        ratio = contrast(fill_hex, color_hex)
        if ratio < MIN_CONTRAST:
            errors.append(f"{kind} {name}: contrast {ratio:.2f} is below {MIN_CONTRAST}")
    return errors


def structure_errors(lines: list[str]) -> list[str]:
    errors = []
    kind = lines[0].split()[0] if lines else ""
    if kind not in ALLOWED_TYPES:
        hint = ". Draw C4 views as flowcharts, see docs/adr/0007-c4-views-as-flowcharts.md" if kind.startswith("C4") else ""
        errors.append(f"diagram type {kind!r} is not one of {sorted(ALLOWED_TYPES)}{hint}")
    if len(lines) < 3 or not lines[1].startswith("accTitle:") or not lines[2].startswith("accDescr:"):
        errors.append("the two lines after the type keyword must be accTitle: and accDescr:")
    body = lines[1:]
    first_content = next((i for i, l in enumerate(body) if not l.startswith(PREAMBLE)), len(body))
    if any(l.startswith("classDef") for l in body[first_content:]):
        errors.append("every classDef must come before the first node or edge line")
    if any(re.search(r"<-[-.]+(?![->])", l) for l in body):
        errors.append("a reversed arrow such as <-.- renders without an arrowhead. Use A ~~~ B to rank, then B -.-> A")
    if any(l.startswith("linkStyle") for l in body):
        errors.append("use edge IDs and edge classes instead of linkStyle")
    if kind == "flowchart":
        nodes = {
            m
            for l in body
            if not l.startswith(("subgraph", "classDef", "class ", "style", "acc", "%%"))
            for m in NODE_DEF.findall(l)
        }
        if len(nodes) > MAX_NODES:
            errors.append(f"{len(nodes)} nodes, more than {MAX_NODES}. Split the diagram")
    return errors


def find_mmdc() -> str | None:
    candidates = [os.environ.get("MMDC"), shutil.which("mmdc"), "/opt/mmdc/node_modules/.bin/mmdc"]
    return next((c for c in candidates if c and os.access(c, os.X_OK)), None)


def render(mmdc: str, mmd: pathlib.Path) -> str | None:
    svg = mmd.with_suffix(".svg")
    result = subprocess.run(
        [mmdc, "-q", "-i", str(mmd), "-o", str(svg),
         "-p", str(PUPPETEER_CONFIG), "-c", str(MERMAID_CONFIG)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not svg.exists() or svg.stat().st_size == 0:
        return " ".join((result.stderr or result.stdout).strip().splitlines()[:3])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-render", action="store_true", help="skip the mmdc render")
    args = parser.parse_args()

    mmdc = None
    if not args.no_render:
        mmdc = find_mmdc()
        if mmdc is None:
            print("check_diagrams: mmdc not found. Install @mermaid-js/mermaid-cli or set MMDC.")
            return 1

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    failures = 0
    count = 0
    for md in sorted(DOCS.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for number, match in enumerate(BLOCK.finditer(text), start=1):
            count += 1
            source = match.group(1)
            lines = body_lines(source)
            line_no = text.count("\n", 0, match.start()) + 1
            headings = HEADING.findall(text, 0, match.start())
            title = sanitize(headings[-1] if headings else "diagram", 20)
            kind = lines[0].split()[0] if lines else "empty"

            errors = structure_errors(lines) + style_errors(lines)

            mmd = OUT / f"{sanitize(md.stem, 40)}_{number:02d}_{sanitize(kind, 20)}_{title}.mmd"
            mmd.write_text(source, encoding="utf-8")
            if mmdc and not errors:
                render_error = render(mmdc, mmd)
                if render_error:
                    errors.append(f"mmdc: {render_error}")

            for error in errors:
                print(f"{md.relative_to(ROOT)}:{line_no}: {error}")
            failures += bool(errors)

    rendered = "" if args.no_render else ", rendered to build/diagrams"
    print(f"check_diagrams: {count - failures}/{count} diagrams pass{rendered}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
