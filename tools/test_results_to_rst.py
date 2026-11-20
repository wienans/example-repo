#!/usr/bin/env python3
"""Turn Ceedling's JUnit report into the "Test results" page.

Unity names a test by its C function, which no ready-made JUnit importer maps
to source. So this script writes ``docs/generated/test_results.rst`` itself:

- a table of all test files with their counts and durations,
- one section per test file, opening with that file's summary table,
- one ``test`` need per test with its status, file, function, location,
  runtime, the ``@brief`` of its Doxygen comment, the failure message, and a
  ``verifies`` link to each requirement its role=Test marker names.

A failed, skipped or unrun test is a result like any other: it shows, it does
not stop the build. ``make trace`` is the gate that fails on it. Each need's
``:style:`` is its status in lower case, for the colours in docs/_static/.

Run: make docs
Output: docs/generated/test_results.rst (git ignores it)
"""

import dataclasses
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

from source_markers import ROOT, read_markers

# make docs runs the suite once, under gcov; that run writes this report.
JUNIT_REPORT = ROOT / "build" / "ceedling" / "artifacts" / "gcov" / "junit_tests_report.xml"
OUT = ROOT / "docs" / "generated" / "test_results.rst"

STATUSES = ("PASSED", "FAILED", "SKIPPED", "NOT_RUN")

BRIEF = re.compile(r"@brief\s+(.*?)\s*(?=\n\s*\*\s*@|\n\s*\*/)", re.DOTALL)


@dataclasses.dataclass
class Test:
    path: str
    function: str
    uids: list[str]
    brief: str = ""
    status: str = "NOT_RUN"
    message: str = ""
    line: str = ""
    duration: float | None = None


def read_report() -> tuple[dict[tuple[str, str], dict], dict[str, float]]:
    """Test case results keyed by (file, function), and each suite's duration by file."""
    cases: dict[tuple[str, str], dict] = {}
    suites: dict[str, float] = {}
    # A build that does not compile writes no report. Every test is then NOT_RUN.
    if not JUNIT_REPORT.is_file():
        return cases, suites
    tree = ET.parse(JUNIT_REPORT)
    for suite in tree.iter("testsuite"):
        suites[suite.get("name", "") + ".c"] = float(suite.get("time", "0"))
    for case in tree.iter("testcase"):
        failure = case.find("failure")
        if failure is not None:
            status, message = "FAILED", failure.get("message", "")
        elif case.find("skipped") is not None:
            status, message = "SKIPPED", ""
        else:
            status, message = "PASSED", ""
        cases[(case.get("file", ""), case.get("name", ""))] = {
            "status": status,
            "message": message,
            "line": case.get("line", ""),
            "duration": float(case.get("time", "0")),
        }
    return cases, suites


def brief_before(path: pathlib.Path, line: int) -> str:
    """The @brief of the Doxygen comment that holds the marker on this line."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = max(i for i in range(line) if "/**" in lines[i])
    comment = "\n".join(lines[start : line + 20])
    match = BRIEF.search(comment)
    if not match:
        return ""
    return " ".join(part.strip().lstrip("*").strip() for part in match.group(1).splitlines())


def collect_tests() -> list[Test]:
    # check_trace.py fails on malformed markers; here they only leave a test
    # without requirements.
    markers, errors = read_markers()
    for error in errors:
        print(f"warning: {error}")
    cases, _ = read_report()
    tests: list[Test] = []
    seen: set[tuple[str, str]] = set()
    for m in markers:
        if m.role != "Test" or not m.function.startswith("test_"):
            continue
        test = Test(m.file, m.function, m.uids, brief_before(m.path, m.line - 1))
        seen.add((test.path, test.function))
        tests.append(test)
    # A test without a marker still shows, with no requirement to verify.
    for path, function in cases:
        if (path, function) not in seen:
            tests.append(Test(path, function, []))
    for test in tests:
        case = cases.get((test.path, test.function))
        if case:
            test.status, test.message, test.line, test.duration = (
                case["status"], case["message"], case["line"], case["duration"],
            )
    return tests


def list_table(caption: str, header: list[str], rows: list[list[str]], widths: str = "") -> str:
    out = [f".. list-table:: {caption}", "   :header-rows: 1"]
    if widths:
        out.append(f"   :widths: {widths}")
    out.append("")
    for row in [header, *rows]:
        out.append(f"   * - {row[0]}")
        out += [f"     - {cell}" for cell in row[1:]]
    return "\n".join(out)


def counts(tests: list[Test]) -> list[str]:
    return [str(len(tests))] + [str(sum(t.status == s for t in tests)) for s in STATUSES]


RST_SPECIAL = re.compile(r"([\\`*_|\[\]<>])")


def rst_text(value: str) -> str:
    """Field values are reStructuredText: keep |x|, *x* and the like literal."""
    return RST_SPECIAL.sub(r"\\\1", value)


def label(path: str) -> str:
    """The label of a test file's section, for links from the overview table."""
    return "tr-" + re.sub(r"[^a-z0-9]+", "-", path.lower())


def heading(title: str, underline: str) -> str:
    return f"{title}\n{underline * len(title)}"


def indent(text: str, spaces: int) -> str:
    return "\n".join(" " * spaces + line if line else "" for line in text.splitlines())


def result_need(number: int, test: Test) -> str:
    need = [
        f".. test:: {test.function}",
        f"   :id: TR-{number:03d}",
        f"   :status: {test.status}",
        f"   :style: {test.status.lower()}",
    ]
    if test.uids:
        need.append(f"   :verifies: {', '.join(test.uids)}")
    need += [
        f"   :file: {test.path}",
        f"   :function: {test.function}",
        f"   :location: {test.path}:{test.line}" if test.line else f"   :location: {test.path}",
    ]
    if test.duration is not None:
        need.append(f"   :runtime: {test.duration:.3f} s")
    body = []
    if test.brief:
        body.append(indent(rst_text(test.brief), 3))
    if test.message:
        body += ["   Failure message::", indent(test.message, 6)]
    return "\n".join(need) + ("\n\n" + "\n\n".join(body) if body else "")


def main() -> int:
    tests = collect_tests()
    _, suite_durations = read_report()
    by_file: dict[str, list[Test]] = {}
    for test in tests:
        by_file.setdefault(test.path, []).append(test)

    header = ["Test file", "Tests", "Passed", "Failed", "Skipped", "Not run", "Duration"]
    rows = [
        [f":ref:`{path} <{label(path)}>`", *counts(group), f"{suite_durations.get(path, 0):.3f} s"]
        for path, group in by_file.items()
    ]
    rows.append(["**All files**", *counts(tests), f"{sum(suite_durations.values()):.3f} s"])
    parts = [
        heading("Test results", "="),
        f"Generated from ``{JUNIT_REPORT.relative_to(ROOT)}`` by ``tools/test_results_to_rst.py``.",
        list_table("All test files", header, rows, widths="40 10 10 10 10 10 10"),
    ]
    number = 0
    for path, group in by_file.items():
        parts.append(f".. _{label(path)}:")
        parts.append(heading(rst_text(path), "-"))
        parts.append(
            list_table(f"Summary for {rst_text(path)}", header[1:], [[*counts(group), f"{suite_durations.get(path, 0):.3f} s"]])
        )
        for test in group:
            number += 1
            parts.append(result_need(number, test))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    summary = dict(zip(STATUSES, counts(tests)[1:]))
    print(f"test_results_to_rst: wrote {OUT.relative_to(ROOT)} ({len(tests)} results in {len(by_file)} files, {summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
