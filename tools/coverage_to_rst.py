#!/usr/bin/env python3
"""Build the "Code coverage" page from gcovr's JSON.

gcovr knows lines and functions, not requirements. This script reads gcovr's
JSON and the role=Implementation markers in src/ and writes
``docs/generated/coverage.rst``:

- an overview table of all files (lines, branches, functions) with a link to
  gcovr's full HTML report, which the make target copies next to the page,
- "By requirement": one ``cov`` need per requirement that ``measures`` it,
  with the lines and branches of the code its markers name and the lines and
  branches its tests never reach,
- "By file": a section per source file with its summary table, a link to
  gcovr's page for that file, and a table of its functions with execution
  count, lines, branches, the requirements they implement and links to each
  uncovered line in gcovr's page. These rows are not needs, so the need count
  stays at one per requirement.

Which lines belong to a requirement follows the marker scopes:

- ``scope=function``: every line of the function below the comment,
- ``scope=range_start`` ... ``scope=range_end``: the lines from the start
  marker to the end marker,
- ``scope=line``: the marker's line and the line after it, also when the
  marker trails code (``x = 1; // @relation(...)``),
- ``scope=file``: every line of the file.

source_markers.py reads and pairs the markers and reports the ones it cannot
place; this script prints those as warnings.

A narrower marker wins: a line inside a range or line marker counts only for
that marker's requirements, not for the requirements of the enclosing function
or file marker.

Coverage is that of the whole test suite (one ``ceedling gcov:all`` run), not
of the tests that verify a requirement. If gcovr's JSON is missing (the code
did not build), the page says so instead of failing the site.

Each need's ``:style:`` is its status in lower case (full, partial, none), for
the colours in docs/_static/.

Run: make docs
Output: docs/generated/coverage.rst (git ignores it). Sphinx renders it as
<html>/generated/coverage.html, and make docs copies gcovr's HTML to the
gcovr/ folder next to it.
"""

import dataclasses
import hashlib
import json
import pathlib
import re
import sys

from source_markers import ROOT, Piece, code_pieces, read_markers
from test_results_to_rst import heading, list_table, rst_text

GCOVR_JSON = ROOT / "build" / "ceedling" / "artifacts" / "gcov" / "gcovr" / "GcovCoverage.json"
OUT = ROOT / "docs" / "generated" / "coverage.rst"
# gcovr's HTML, relative to the page. Links appear only on this page: a
# requirement page lists a coverage need by ID, not its body.
GCOVR_HTML = "gcovr"
GCOVR_PREFIX = "GcovCoverageResults"

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
    found, warnings = code_pieces(markers, "Implementation")
    return found, [e for e in errors if e.startswith("src/")] + warnings


def tally(file: str, records: list[dict]) -> Tally:
    """Lines and branches of gcovr line records, with links to what is missing."""
    result = Tally()
    for line in sorted(records, key=lambda r: r["line_number"]):
        number = line["line_number"]
        link = f"`{file}:{number} <{gcovr_page(file)}#L{number}>`__"
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


def label(file: str) -> str:
    """The label of a source file's section, for links from the overview table."""
    return "cov-" + re.sub(r"[^a-z0-9]+", "-", file.lower())


def cell(text: str) -> str:
    """A list-table cell whose text may span lines, such as a bullet list."""
    return text.replace("\n", "\n       ")


def main() -> int:
    if not GCOVR_JSON.is_file():
        # The gcov build failed, most likely a compile error. Say so on the
        # page rather than fail the whole site.
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            heading("Code coverage", "=") + "\n\n"
            f"No coverage data: ``{GCOVR_JSON.relative_to(ROOT)}`` is missing. "
            "The coverage build did not finish; run ``ceedling gcov:all`` to see why.\n",
            encoding="utf-8",
        )
        print(f"coverage_to_rst: {GCOVR_JSON.relative_to(ROOT)} missing, wrote a placeholder")
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
    rows = [file_row(name, f":ref:`{name} <{label(name)}>`") for name in files]
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
        heading("Code coverage", "="),
        f"Generated from ``{GCOVR_JSON.relative_to(ROOT)}`` by ``tools/coverage_to_rst.py``. "
        f"Line-by-line detail: `gcovr report <{GCOVR_HTML}/{GCOVR_PREFIX}.html>`__.",
        list_table("All files", header, rows, widths="40 20 20 20"),
    ]

    # By requirement.
    by_requirement: dict[str, list[Piece]] = {}
    for piece in pieces:
        for uid in piece.uids:
            by_requirement.setdefault(uid, []).append(piece)
    counts = {"FULL": 0, "PARTIAL": 0, "NONE": 0}
    parts += [
        heading("By requirement", "-"),
        "Each entry counts the lines its ``role=Implementation`` markers name: "
        "a whole function, a range, a line or a file. A line inside a range or "
        "line marker counts only for that marker's requirements. Coverage is "
        "that of the whole test suite.",
    ]
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
        need = [
            f".. cov:: Coverage of {uid}",
            f"   :id: COV-{number:03d}",
            f"   :status: {status}",
            f"   :style: {status.lower()}",
            f"   :measures: {uid}",
            f"   :lines: {percent(total.lines_hit, total.lines)}",
            f"   :branches: {percent(total.branches_hit, total.branches)}",
            "",
            "   Code:",
            "",
            *[f"   {line}" for line in code],
        ]
        if total.uncovered:
            need += ["", "   Uncovered:", "", *[f"   {line}" for line in total.uncovered]]
        parts.append("\n".join(need))

    # By file.
    parts.append(heading("By file", "-"))
    function_count = 0
    for name, functions in files.items():
        rows = []
        for function, function_tally in functions:
            function_count += 1
            # Requirements of every piece that covers a line of this function.
            function_lines = {
                n for n, r in records[name].items() if r.get("function_name") == function["name"]
            }
            uids: list[str] = []
            for piece in pieces:
                lines = piece_lines(piece) if piece.file == name else None
                if lines and function_lines & lines.keys():
                    uids += [u for u in piece.uids if u not in uids]
            rows.append(
                [
                    f"``{function['name']}``",
                    function_tally.status,
                    str(function["execution_count"]),
                    percent(function_tally.lines_hit, function_tally.lines),
                    percent(function_tally.branches_hit, function_tally.branches),
                    ", ".join(f":need:`{u}`" for u in sorted(uids)) or "None: a helper.",
                    cell("\n".join(function_tally.uncovered)) or "None",
                ]
            )
        parts += [
            f".. _{label(name)}:",
            heading(rst_text(name), "~"),
            f"`Line-by-line detail in gcovr <{gcovr_page(name)}>`__",
            list_table(f"Summary for {rst_text(name)}", header[1:], [file_row(name, "")[1:]]),
            list_table(
                f"Functions in {rst_text(name)}",
                ["Function", "Status", "Calls", "Lines", "Branches", "Requirements", "Uncovered"],
                rows,
                widths="20 8 6 12 12 16 26",
            ),
        ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(
        f"coverage_to_rst: wrote {OUT.relative_to(ROOT)} ({len(by_requirement)} requirements {counts}, "
        f"{function_count} functions in {len(files)} files, {len(warnings)} warnings)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
