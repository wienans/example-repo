#!/usr/bin/env python3
"""Build the "Code coverage" StrictDoc document from gcovr's JSON.

StrictDoc's own *.gcov.json import only marks a function covered once it ran
and never reaches a requirement. This script reads gcovr's JSON and the role=Implementation markers in src/ and
writes one document, ``Code coverage``:

- an overview table of all files (lines, branches, functions) with a link to
  gcovr's full HTML report, which the make target copies next to the page,
- "By requirement": one REQ_COVERAGE node per requirement, a Child of that
  requirement, with the lines and branches of the code its markers name and
  the lines and branches its tests never reach,
- "By file": a section per source file with its summary table and a link to
  gcovr's page for that file, then one FUNC_COVERAGE node per function with
  its execution count, lines, branches, the requirements it implements, links
  to each uncovered line in gcovr's page, and a File relation to the function.

Which lines belong to a requirement follows StrictDoc's marker scopes:

- ``scope=function``: every line of the function below the comment,
- ``scope=range_start`` ... ``scope=range_end``: the lines from the start
  marker to the end marker,
- ``scope=line``: the marker's line and the line after it, also when the
  marker trails code (``x = 1; // @relation(...)``), as StrictDoc counts it,
- ``scope=file``: every line of the file.

Markers may sit in ``/* */`` or ``//`` comments, read as StrictDoc's C reader
reads them: a function marker belongs to the comment that ends on the line
right above the definition, so in ``//`` style the marker's own line must be
that line, and a marker in a one-line ``/* @relation(...) */`` is ignored by
StrictDoc, so the script warns about it instead of counting it.

A narrower marker wins: a line inside a range or line marker counts only for
that marker's requirements, not for the requirements of the enclosing function
or file marker. An implementation marker the script cannot place is printed
as a warning instead of being skipped silently.

Coverage is that of the whole test suite (one ``ceedling gcov:all`` run), not
of the tests that verify a requirement.

Markers are read by source_markers.py, so they count where StrictDoc shows
them. If gcovr's JSON is missing (the code did not build), the document says
so instead of failing the site.

Every UID ends in FULL, PARTIAL or NONE, which tools/strictdoc/site.css
colours green, amber or red.

Run: make docs
Output: docs/generated/coverage.sdoc (git ignores it; see
test_results_to_sdoc.py for why it lives there). StrictDoc renders it as
html/<checkout>/docs/generated/coverage.html, and make docs copies gcovr's HTML
to the gcovr/ folder next to it.
"""

import dataclasses
import hashlib
import json
import pathlib
import sys

from source_markers import ROOT, read_markers

GCOVR_JSON = ROOT / "build" / "ceedling" / "artifacts" / "gcov" / "gcovr" / "GcovCoverage.json"
OUT = ROOT / "docs" / "generated" / "coverage.sdoc"
# gcovr's HTML. StrictDoc also shows coverage nodes on the requirement pages,
# so the link climbs to docs/ first: it resolves from docs/generated/ and from
# docs/requirements/, which sit at the same depth.
GCOVR_HTML = "../generated/gcovr"
GCOVR_PREFIX = "GcovCoverageResults"

HEADER = """\
[DOCUMENT]
TITLE: Code coverage
OPTIONS:
  VIEW_STYLE: Table

[GRAMMAR]
ELEMENTS:
- TAG: TEXT
  FIELDS:
  - TITLE: STATEMENT
    TYPE: String
    REQUIRED: True
- TAG: REQ_COVERAGE
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: True
  - TITLE: TITLE
    TYPE: String
    REQUIRED: True
  - TITLE: STATUS
    TYPE: SingleChoice(FULL, PARTIAL, NONE)
    REQUIRED: True
  - TITLE: CODE
    TYPE: String
    REQUIRED: False
  - TITLE: UNCOVERED
    TYPE: String
    REQUIRED: False
  RELATIONS:
  - TYPE: Parent
    ROLE: measures
    REVERSE_ROLE: is measured by
- TAG: FUNC_COVERAGE
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: True
  - TITLE: TITLE
    TYPE: String
    REQUIRED: True
  - TITLE: STATUS
    TYPE: SingleChoice(FULL, PARTIAL, NONE)
    REQUIRED: True
  - TITLE: CALLS
    TYPE: String
    REQUIRED: True
  - TITLE: LINES
    TYPE: String
    REQUIRED: True
  - TITLE: BRANCHES
    TYPE: String
    REQUIRED: True
  - TITLE: REQUIREMENTS
    TYPE: String
    REQUIRED: False
  - TITLE: UNCOVERED
    TYPE: String
    REQUIRED: False
  RELATIONS:
  - TYPE: File"""


@dataclasses.dataclass
class Piece:
    """The code one implementation marker names."""

    file: str
    kind: str  # function, range, line or file
    uids: list[str]
    function: str = ""
    first: int = 0
    last: int = 0

    def label(self) -> str:
        if self.kind == "function":
            return f"``{self.function}`` in ``{self.file}``"
        if self.kind == "file":
            return f"``{self.file}`` (whole file)"
        return f"``{self.file}:{self.first}-{self.last}`` ({self.kind})"


@dataclasses.dataclass
class Tally:
    """Covered and total counts of lines and branches, plus what is missing."""

    lines_hit: int = 0
    lines: int = 0
    branches_hit: int = 0
    branches: int = 0
    uncovered: list[str] = dataclasses.field(default_factory=list)

    def add(self, other: "Tally") -> None:
        self.lines_hit += other.lines_hit
        self.lines += other.lines
        self.branches_hit += other.branches_hit
        self.branches += other.branches
        self.uncovered += other.uncovered

    @property
    def status(self) -> str:
        if self.lines_hit == 0:
            return "NONE"
        if self.lines_hit == self.lines and self.branches_hit == self.branches:
            return "FULL"
        return "PARTIAL"


def percent(done: int, total: int) -> str:
    return f"{100 * done / total:.0f}% ({done}/{total})" if total else "n/a"


def gcovr_page(file: str) -> str:
    """gcovr names a file's page after the MD5 of its path."""
    digest = hashlib.md5(file.encode("utf-8")).hexdigest()
    return f"{GCOVR_HTML}/{GCOVR_PREFIX}.{pathlib.Path(file).name}.{digest}.html"


def implementation_pieces() -> tuple[list[Piece], list[str]]:
    """Every role=Implementation marker in src/ as a Piece, and those it cannot place."""
    markers, errors = read_markers()
    warnings = [e for e in errors if e.startswith("src/")]
    pieces: list[Piece] = []
    open_ranges: dict[str, list[tuple[list[str], int]]] = {}
    for marker in markers:
        if marker.role != "Implementation":
            continue
        stack = open_ranges.setdefault(marker.file, [])
        if marker.scope == "function":
            pieces.append(Piece(marker.file, "function", marker.uids, function=marker.function))
        elif marker.scope == "file":
            pieces.append(Piece(marker.file, "file", marker.uids))
        elif marker.scope == "line":
            pieces.append(Piece(marker.file, "line", marker.uids, first=marker.line, last=marker.line + 1))
        elif marker.scope == "range_start":
            stack.append((marker.uids, marker.line))
        elif marker.scope == "range_end":
            if not stack or stack[-1][0] != marker.uids:
                warnings.append(f"{marker.where}: range_end without a matching range_start")
                continue
            _, start = stack.pop()
            pieces.append(Piece(marker.file, "range", marker.uids, first=start, last=marker.line))
        else:
            warnings.append(f"{marker.where}: unsupported scope '{marker.scope}'")
    for file, stack in open_ranges.items():
        for _, start in stack:
            warnings.append(f"{file}:{start}: range_start without a range_end")
    return pieces, warnings


def tally(file: str, records: list[dict]) -> Tally:
    """Lines and branches of gcovr line records, with links to what is missing."""
    result = Tally()
    for line in sorted(records, key=lambda r: r["line_number"]):
        number = line["line_number"]
        link = f"`{file}:{number} <{gcovr_page(file)}#L{number}>`_"
        where = f" in ``{line['function_name']}``" if line.get("function_name") else ""
        result.lines += 1
        result.lines_hit += line["count"] > 0
        branches = line.get("branches", [])
        taken = sum(b["count"] > 0 for b in branches)
        result.branches += len(branches)
        result.branches_hit += taken
        if line["count"] == 0:
            result.uncovered.append(f"- {link}{where}: line never executed")
        elif taken < len(branches):
            result.uncovered.append(f"- {link}{where}: {len(branches) - taken} of {len(branches)} branches never taken")
    return result


def list_table(caption: str, header: list[str], rows: list[list[str]], widths: str = "") -> str:
    out = [f".. list-table:: {caption}", "   :header-rows: 1"]
    if widths:
        out.append(f"   :widths: {widths}")
    out.append("")
    for row in [header, *rows]:
        out.append(f"   * - {row[0]}")
        out += [f"     - {cell}" for cell in row[1:]]
    return "\n".join(out)


def text_node(statement: str) -> str:
    return f"[TEXT]\nSTATEMENT: >>>\n{statement}\n<<<"


def multiline(field: str, value: str) -> list[str]:
    return [f"{field}: >>>", value, "<<<"]


def section_uid(file: str) -> str:
    return "CF-" + pathlib.Path(file).stem


def main() -> int:
    if not GCOVR_JSON.is_file():
        # The gcov build failed, most likely a compile error. Say so on the
        # page rather than fail the whole site.
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            HEADER + "\n\n" + text_node(
                f"No coverage data: ``{GCOVR_JSON.relative_to(ROOT)}`` is missing. "
                "The coverage build did not finish; run ``ceedling gcov:all`` to see why."
            ) + "\n",
            encoding="utf-8",
        )
        print(f"coverage_to_sdoc: {GCOVR_JSON.relative_to(ROOT)} missing, wrote a placeholder")
        return 0
    data = json.loads(GCOVR_JSON.read_text(encoding="utf-8"))
    # gcovr's line records by file and line number.
    records: dict[str, dict[int, dict]] = {
        f["file"]: {line["line_number"]: line for line in f["lines"]} for f in data["files"]
    }
    pieces, warnings = implementation_pieces()
    # Convention: one code line gets scope=line, more get a range. gcovr
    # records a statement on its first line, so this counts statements.
    for piece in pieces:
        if piece.kind not in ("range", "line") or piece.file not in records:
            continue
        code_lines = [n for n in records[piece.file] if piece.first <= n <= piece.last]
        if piece.kind == "range" and len(code_lines) == 1:
            warnings.append(f"{piece.file}:{piece.first}: range covers one code line, use scope=line")
        if piece.kind == "line" and not code_lines:
            warnings.append(
                f"{piece.file}:{piece.first}: scope=line covers no code line; "
                "the marker must sit on the code line or the line right above it"
            )
    for warning in warnings:
        print(f"warning: {warning}")

    # Lines a range or line marker claims. They leave the enclosing function's
    # or file's requirements.
    claimed: dict[str, set[int]] = {}
    for piece in pieces:
        if piece.kind in ("range", "line"):
            claimed.setdefault(piece.file, set()).update(range(piece.first, piece.last + 1))

    def piece_lines(piece: Piece) -> dict[int, dict] | None:
        """The line records a piece covers, or None if the tests do not build its code."""
        file_records = records.get(piece.file)
        if file_records is None:
            return None
        taken = claimed.get(piece.file, set())
        if piece.kind == "function":
            lines = {
                n: r for n, r in file_records.items()
                if r.get("function_name") == piece.function and n not in taken
            }
            in_function = any(r.get("function_name") == piece.function for r in file_records.values())
            return lines if in_function else None
        if piece.kind == "file":
            return {n: r for n, r in file_records.items() if n not in taken}
        return {n: r for n, r in file_records.items() if piece.first <= n <= piece.last}

    # By file: totals per file and per function.
    files: dict[str, list[tuple[dict, Tally]]] = {}
    for file in data["files"]:
        for function in file["functions"]:
            lines = [r for r in file["lines"] if r.get("function_name") == function["name"]]
            files.setdefault(file["file"], []).append((function, tally(file["file"], lines)))

    def file_row(name: str, link: str) -> list[str]:
        total = Tally()
        for _, function_tally in files[name]:
            total.add(function_tally)
        executed = sum(f["execution_count"] > 0 for f, _ in files[name])
        return [
            link,
            percent(total.lines_hit, total.lines),
            percent(total.branches_hit, total.branches),
            percent(executed, len(files[name])),
        ]

    header = ["File", "Lines", "Branches", "Functions"]
    rows = [file_row(name, f"`{name} <#{section_uid(name)}>`_") for name in files]
    grand = Tally()
    for name in files:
        for _, function_tally in files[name]:
            grand.add(function_tally)
    all_functions = [f for name in files for f, _ in files[name]]
    rows.append(
        [
            "**All files**",
            percent(grand.lines_hit, grand.lines),
            percent(grand.branches_hit, grand.branches),
            percent(sum(f["execution_count"] > 0 for f in all_functions), len(all_functions)),
        ]
    )
    parts = [
        HEADER,
        text_node(
            f"Generated from ``{GCOVR_JSON.relative_to(ROOT)}`` by "
            "``tools/coverage_to_sdoc.py``. Line-by-line detail: "
            f"`gcovr report <{GCOVR_HTML}/{GCOVR_PREFIX}.html>`_.\n\n"
            + list_table("All files", header, rows, widths="40 20 20 20")
        ),
    ]

    # By requirement.
    by_requirement: dict[str, list[Piece]] = {}
    for piece in pieces:
        for uid in piece.uids:
            by_requirement.setdefault(uid, []).append(piece)
    counts = {"FULL": 0, "PARTIAL": 0, "NONE": 0}
    parts.append(
        "[[SECTION]]\nUID: COV-BY-REQUIREMENT\nTITLE: By requirement\n\n"
        + text_node(
            "Each entry counts the lines its ``role=Implementation`` markers name: "
            "a whole function, a range, a line or a file. A line inside a range or "
            "line marker counts only for that marker's requirements. Coverage is "
            "that of the whole test suite."
        )
    )
    for number, uid in enumerate(sorted(by_requirement), start=1):
        # Line records by (file, line), so overlapping pieces count once.
        union: dict[tuple[str, int], dict] = {}
        code: list[str] = []
        unmeasured: list[str] = []
        for piece in by_requirement[uid]:
            lines = piece_lines(piece)
            if lines is None:
                code.append(f"- {piece.label()}: not measured by the unit tests")
                unmeasured.append(f"- {piece.label()}: not measured by the unit tests")
                continue
            piece_tally = tally(piece.file, list(lines.values()))
            note = ""
            if piece.kind in ("function", "file"):
                carved = sum(
                    1 for n, r in records[piece.file].items()
                    if n in claimed.get(piece.file, set())
                    and (piece.kind == "file" or r.get("function_name") == piece.function)
                )
                if carved:
                    note = f", {carved} lines left to narrower markers"
            code.append(f"- {piece.label()}: lines {percent(piece_tally.lines_hit, piece_tally.lines)}{note}")
            union.update({(piece.file, n): r for n, r in lines.items()})
        total = Tally()
        for file in sorted({f for f, _ in union}):
            total.add(tally(file, [r for (f, _), r in union.items() if f == file]))
        total.uncovered += unmeasured
        # Code the unit tests do not build is a gap, not full coverage.
        status = "PARTIAL" if total.status == "FULL" and unmeasured else total.status
        counts[status] += 1
        node = [
            "[REQ_COVERAGE]",
            # Short UID: the Child list shows "UID TITLE". The status suffix
            # drives the colour, as for test results.
            f"UID: COV-{number:03d}-{status}",
            f"TITLE: lines {percent(total.lines_hit, total.lines)}, branches {percent(total.branches_hit, total.branches)}",
            f"STATUS: {status}",
            *multiline("CODE", "\n".join(code)),
        ]
        if total.uncovered:
            node += multiline("UNCOVERED", "\n".join(total.uncovered))
        node += ["RELATIONS:", "- TYPE: Parent", f"  VALUE: {uid}", "  ROLE: measures"]
        parts.append("\n".join(node))
    parts.append("[[/SECTION]]")

    # By file.
    parts.append("[[SECTION]]\nUID: COV-BY-FILE\nTITLE: By file")
    number = 0
    for name, functions in files.items():
        parts.append(
            f"[[SECTION]]\nUID: {section_uid(name)}\nTITLE: {name}\n\n"
            + text_node(
                f"`Line-by-line detail in gcovr <{gcovr_page(name)}>`_\n\n"
                + list_table(f"Summary for {name}", header[1:], [file_row(name, "")[1:]])
            )
        )
        for function, function_tally in functions:
            number += 1
            # Requirements of every piece that covers a line of this function.
            function_lines = {
                n for n, r in records[name].items() if r.get("function_name") == function["name"]
            }
            uids: list[str] = []
            for piece in pieces:
                lines = piece_lines(piece) if piece.file == name else None
                if lines and function_lines & lines.keys():
                    uids += [u for u in piece.uids if u not in uids]
            node = [
                "[FUNC_COVERAGE]",
                f"UID: FC-{number:03d}-{function_tally.status}",
                f"TITLE: {function['name']}",
                f"STATUS: {function_tally.status}",
                f"CALLS: {function['execution_count']}",
                f"LINES: {percent(function_tally.lines_hit, function_tally.lines)}",
                f"BRANCHES: {percent(function_tally.branches_hit, function_tally.branches)}",
            ]
            # [LINK: UID] links without adding a relation, so the requirement
            # pages stay lean. StrictDoc resolves one per line.
            node += multiline(
                "REQUIREMENTS", "\n".join(f"- [LINK: {u}]" for u in sorted(uids)) if uids else "None: a helper."
            )
            if function_tally.uncovered:
                node += multiline("UNCOVERED", "\n".join(function_tally.uncovered))
            node += ["RELATIONS:", "- TYPE: File", f"  VALUE: {name}", f"  FUNCTION: {function['name']}"]
            parts.append("\n".join(node))
        parts.append("[[/SECTION]]")
    parts.append("[[/SECTION]]")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(
        f"coverage_to_sdoc: wrote {OUT.relative_to(ROOT)} ({len(by_requirement)} requirements {counts}, "
        f"{number} functions in {len(files)} files, {len(warnings)} warnings)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
