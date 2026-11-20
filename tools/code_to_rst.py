#!/usr/bin/env python3
"""Write the "Code traceability" page from the markers in src/ and tools/.

One ``impl`` need per role=Implementation marker and one ``check`` need per
role=Check marker, grouped in a section per file. Each need links to the
requirements its marker names (``implements`` or ``verifies``), so every
requirement page lists the code behind it. The body shows the code: the
function, range or lines the marker names, with a link to the API reference
for a function a header declares. role=Test markers are left to the test
results page, whose needs carry the result as well.

source_markers.py reads and pairs the markers. The ones it cannot place are
printed as warnings; ``make trace`` is the gate that fails on them.

Run: make docs
Output: docs/generated/code.rst (git ignores it)
"""

import re
import sys

from source_markers import ROOT, Piece, code_pieces, read_markers
from test_results_to_rst import heading, rst_text

OUT = ROOT / "docs" / "generated" / "code.rst"
# Need type, link and ID prefix per marker role.
ROLES = {"Implementation": ("impl", "implements", "IMPL"), "Check": ("check", "verifies", "CHK")}
LANGUAGE = {".c": "c", ".h": "c", ".py": "python"}


def function_extent(piece: Piece) -> tuple[int, int]:
    """First and last line of the function definition below a marker."""
    lines = (ROOT / piece.file).read_text(encoding="utf-8").splitlines()
    name = re.compile(rf"\b{piece.function}\s*\(")
    first = next(i for i in range(piece.line, len(lines)) if name.search(lines[i])) + 1
    if piece.file.endswith(".py"):
        # The body ends before the next line indented no deeper than "def".
        indent = len(lines[first - 1]) - len(lines[first - 1].lstrip())
        last = first
        for i in range(first, len(lines)):
            if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= indent:
                break
            if lines[i].strip():
                last = i + 1
        return first, last
    depth = 0
    for i in range(first - 1, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if depth == 0 and "}" in lines[i]:
            return first, i + 1
    raise ValueError(f"{piece.where}: no end of {piece.function}")


def whole_comments(piece: Piece) -> tuple[int, int]:
    """The lines of a range or line marker, widened to the block comments its
    markers sit in, so the excerpt does not start or end inside a comment."""
    lines = (ROOT / piece.file).read_text(encoding="utf-8").splitlines()
    first, last = piece.first, piece.last
    if "//" not in lines[first - 1]:
        while first > 1 and "/*" not in lines[first - 1]:
            first -= 1
    if piece.kind == "range" and "//" not in lines[last - 1]:
        while last < len(lines) and "*/" not in lines[last - 1]:
            last += 1
    return first, last


def declared_in_header(function: str) -> bool:
    """Breathe documents what the headers declare, so only those resolve as :c:func:."""
    declaration = re.compile(rf"\b{function}\s*\(")
    return any(declaration.search(h.read_text(encoding="utf-8")) for h in (ROOT / "src").rglob("*.h"))


def need(piece: Piece, role: str, number: int) -> str:
    directive, link, prefix = ROLES[role]
    if piece.kind == "function":
        title = piece.function
        first, last = function_extent(piece)
    elif piece.kind == "file":
        title, first, last = piece.file, 0, 0
    else:
        title = f"{piece.file}:{piece.first}-{piece.last}"
        first, last = whole_comments(piece)
    out = [
        f".. {directive}:: {title}",
        f"   :id: {prefix}-{number:03d}",
        f"   :{link}: {', '.join(piece.uids)}",
        f"   :file: {piece.file}",
    ]
    if piece.function:
        out.append(f"   :function: {piece.function}")
    out += [f"   :location: {piece.where}", ""]
    if piece.kind == "function":
        ref = f":c:func:`{piece.function}`" if declared_in_header(piece.function) else f"``{piece.function}``"
        out += [f"   Function {ref}, lines {first} to {last}.", ""]
    elif piece.kind == "file":
        out.append(f"   The whole file ``{piece.file}``.")
    else:
        out += [f"   Lines {first} to {last} ({piece.kind}).", ""]
    if first:
        language = LANGUAGE.get("." + piece.file.rsplit(".", 1)[-1], "text")
        out += [
            f"   .. literalinclude:: /../{piece.file}",
            f"      :language: {language}",
            f"      :lines: {first}-{last}",
            "      :lineno-match:",
        ]
    return "\n".join(out)


def main() -> int:
    markers, errors = read_markers()
    by_file: dict[str, list[tuple[Piece, str]]] = {}
    warnings = list(errors)
    for role in ROLES:
        found, role_warnings = code_pieces(markers, role)
        warnings += role_warnings
        for piece in found:
            by_file.setdefault(piece.file, []).append((piece, role))
    for warning in warnings:
        print(f"warning: {warning}")

    parts = [
        heading("Code traceability", "="),
        "Generated from the ``@relation`` markers in ``src/`` and ``tools/`` by "
        "``tools/code_to_rst.py``. Tests are on the test results page.",
    ]
    numbers = {role: 0 for role in ROLES}
    for file in sorted(by_file):
        parts.append(heading(rst_text(file), "-"))
        for piece, role in sorted(by_file[file], key=lambda p: p[0].line):
            numbers[role] += 1
            parts.append(need(piece, role, numbers[role]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(
        f"code_to_rst: wrote {OUT.relative_to(ROOT)} ({numbers['Implementation']} impl, "
        f"{numbers['Check']} check in {len(by_file)} files, {len(warnings)} warnings)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
