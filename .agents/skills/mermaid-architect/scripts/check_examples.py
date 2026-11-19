#!/usr/bin/env python3
"""Check every Mermaid example in this skill.

Every ```mermaid block in a Markdown file must render with Mermaid CLI, and
every classDef or style line that sets a fill must also set a text color with
a WCAG contrast of at least 4.5 on that fill. Put a deliberately broken example
in a ```text block so that no renderer tries to draw it.

Usage:
	python3 scripts/check_examples.py [--no-render] [path ...]

Paths default to the skill folder. Set MMDC to the mmdc binary when it is not
on PATH. Each render starts a headless Chromium. CHECK_WORKERS sets how many run
at once, default 2. Exit status 1 means at least one example failed.
"""

import argparse
import concurrent.futures
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SKILL = pathlib.Path(__file__).resolve().parent.parent
MIN_CONTRAST = 4.5
NAMED = {"black": "000000", "white": "ffffff", "darkgreen": "006400", "darkblue": "00008b", "darkred": "8b0000"}
BLOCK = re.compile(r"^[ \t]*```mermaid[ \t]*\n(.*?)^[ \t]*```", re.M | re.S)
STYLE = re.compile(r"^\s*(classDef|style)\s+(\S+)\s+(.+)$", re.M)


def to_hex(value: str) -> str | None:
    value = value.strip().lower()
    if value in NAMED:
        return NAMED[value]
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if not m:
        return None
    d = m.group(1)
    return "".join(c * 2 for c in d) if len(d) == 3 else d


def luminance(h: str) -> float:
    c = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def style_errors(source: str) -> list[str]:
    errors = []
    for kind, name, props in STYLE.findall(source):
        fields = dict(
            (k.strip(), v.strip())
            for k, v in (p.split(":", 1) for p in props.rstrip(";").split(",") if ":" in p)
        )
        if "fill" not in fields:
            continue
        if "color" not in fields:
            errors.append(f"{kind} {name} sets fill but no color")
            continue
        fill, text = to_hex(fields["fill"]), to_hex(fields["color"])
        if fill and text and contrast(fill, text) < MIN_CONTRAST:
            errors.append(f"{kind} {name}: {fields['color']} on {fields['fill']} is {contrast(fill, text):.2f}, below {MIN_CONTRAST}")
    return errors


def find_mmdc() -> str | None:
    for candidate in (os.environ.get("MMDC"), shutil.which("mmdc")):
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    return None


def render(mmdc: str, source: str, workdir: pathlib.Path, index: int) -> str | None:
    mmd = workdir / f"{index:04d}.mmd"
    mmd.write_text(source, encoding="utf-8")
    config = workdir / "puppeteer.json"
    if not config.exists():
        config.write_text('{"args": ["--no-sandbox"]}', encoding="utf-8")
    result = subprocess.run(
        [mmdc, "-q", "-i", str(mmd), "-o", str(mmd.with_suffix(".svg")), "-p", str(config)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return None
    return " ".join((result.stderr or result.stdout).strip().splitlines()[:2])[:200]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check every Mermaid example in this skill.")
    parser.add_argument("paths", nargs="*", type=pathlib.Path, default=[SKILL])
    parser.add_argument("--no-render", action="store_true", help="check contrast only")
    args = parser.parse_args()

    mmdc = None if args.no_render else find_mmdc()
    if not args.no_render and mmdc is None:
        print("check_examples: mmdc not found. Install @mermaid-js/mermaid-cli or set MMDC.")
        return 1

    files = sorted(f for p in args.paths for f in ([p] if p.is_file() else p.rglob("*.md")))
    examples = []
    for md in files:
        text = md.read_text(encoding="utf-8")
        for m in BLOCK.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            examples.append((f"{md.relative_to(SKILL) if md.is_relative_to(SKILL) else md}:{line}", m.group(1)))

    failures: dict[str, list[str]] = {}
    for where, source in examples:
        for error in style_errors(source):
            failures.setdefault(where, []).append(error)

    if mmdc:
        with tempfile.TemporaryDirectory() as tmp, concurrent.futures.ThreadPoolExecutor(int(os.environ.get("CHECK_WORKERS", "2"))) as pool:
            work = pathlib.Path(tmp)
            futures = {pool.submit(render, mmdc, src, work, i): where for i, (where, src) in enumerate(examples)}
            for future in concurrent.futures.as_completed(futures):
                error = future.result()
                if error:
                    failures.setdefault(futures[future], []).append(f"mmdc: {error}")

    for where in sorted(failures):
        for error in failures[where]:
            print(f"{where}: {error}")
    mode = "contrast" if args.no_render else "render and contrast"
    print(f"check_examples: {len(examples) - len(failures)}/{len(examples)} examples pass ({mode})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
