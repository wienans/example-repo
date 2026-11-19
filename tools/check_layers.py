#!/usr/bin/env python3
"""Enforce the firmware layer rule (SWR-ARC-001) and determinism rule (SWR-DET-001).

Every header under src/ belongs to the layer of the directory it lives in.
An #include is legal only if the including file's layer may depend on the
included header's layer. Headers not found under src/ are external; only the
freestanding C headers below are allowed outside the HAL port. Outside the port,
dynamic memory and floating point are rejected.

Exit 0 when clean, 1 with "path:line: message" lines otherwise.

@relation(SWR-ARC-001, SWR-DET-001, scope=file, role=Check)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PORT = "port"

ALLOWED = {
    "app": {"app", "domain", "middleware", "bsp"},
    "domain": {"domain"},
    "middleware": {"middleware"},
    "bsp": {"bsp", "hal", "domain"},
    "hal": {"hal"},
}
FREESTANDING = {"stdint.h", "stdbool.h", "stddef.h"}

INCLUDE_RE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')
BANNED_RE = re.compile(r"\b(malloc|calloc|realloc|free)\s*\(|\b(float|double)\b")
COMMENT_OR_STRING_RE = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', re.S
)


def layer_of(path: Path) -> str:
    parts = path.relative_to(SRC).parts
    if len(parts) >= 3 and parts[0] == "hal" and parts[1] == PORT:
        return PORT
    return parts[0]


def blank_comments_and_strings(text: str) -> str:
    """Replace comments and literals with spaces, keeping line numbers intact."""
    return COMMENT_OR_STRING_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def main() -> int:
    sources = sorted(p for p in SRC.rglob("*") if p.suffix in (".c", ".h"))
    header_layer = {}
    errors = []

    for path in sources:
        if path.suffix != ".h":
            continue
        layer = layer_of(path)
        if layer != PORT and layer not in ALLOWED:
            errors.append(f"{path.relative_to(ROOT)}:1: unknown layer '{layer}'")
        if path.name in header_layer and header_layer[path.name] != layer:
            errors.append(f"{path.relative_to(ROOT)}:1: header name '{path.name}' is used by two layers")
        header_layer[path.name] = layer

    for path in sources:
        rel = path.relative_to(ROOT)
        layer = layer_of(path)
        text = path.read_text(encoding="utf-8")
        is_port = layer == PORT

        for lineno, line in enumerate(text.splitlines(), start=1):
            match = INCLUDE_RE.match(line)
            if not match or is_port:
                continue
            name = Path(match.group(2)).name
            target = header_layer.get(name)
            if target is None:
                if match.group(1) == "<" and name in FREESTANDING:
                    continue
                errors.append(f"{rel}:{lineno}: layer '{layer}' includes external header '{match.group(2)}'")
            elif target not in ALLOWED.get(layer, set()):
                errors.append(f"{rel}:{lineno}: layer '{layer}' must not include '{name}' from layer '{target}'")

        if is_port:
            continue
        code = blank_comments_and_strings(text)
        for lineno, line in enumerate(code.splitlines(), start=1):
            for match in BANNED_RE.finditer(line):
                errors.append(f"{rel}:{lineno}: '{match.group(1) or match.group(2)}' is only allowed in src/hal/port/")

    for error in errors:
        print(error)
    if errors:
        print(f"check_layers: {len(errors)} violation(s)")
        return 1
    print(f"check_layers: {len(sources)} files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
