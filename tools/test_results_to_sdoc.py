#!/usr/bin/env python3
"""Turn Ceedling's JUnit report into the "Test results" StrictDoc document.

StrictDoc's own JUnit import does not fit Unity: its dialects resolve a test
name to a Google Test macro, a Python file or a Rust path, never to a C
function. So this script writes a native ``.sdoc``, laid out like StrictDoc's
test report:

- a table of all test files with their counts and durations,
- one section per test file (a heading in the table of contents), opening
  with that file's summary table,
- one TEST_RESULT per test with its status, path, function, line, duration,
  the ``@brief`` of its Doxygen comment, the failure message, a "verifies"
  relation to each requirement its role=Test marker names, and a File
  relation to the test function.

A failed, skipped or unrun test is a result like any other: it shows, it does
not stop the build. ``make trace`` is the gate that fails on it.

Each TEST_RESULT UID ends in its status, for tools/strictdoc/site.css.

Run: make docs
Output: docs/generated/test_results.sdoc (git ignores it)
"""

import dataclasses
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

from source_markers import ROOT, read_markers

# make docs runs the suite once, under gcov; that run writes this report.
JUNIT_REPORT = ROOT / "build" / "ceedling" / "artifacts" / "gcov" / "junit_tests_report.xml"
# StrictDoc excludes every root .gitignore entry, so build/ is never scanned,
# and a second export input path breaks the links from requirements to code.
# docs/generated/ keeps its own .gitignore, which StrictDoc does not read. It
# sits at the depth of docs/01_requirements/: StrictDoc links a requirement to
# its code from the depth of the document it is shown in.
OUT = ROOT / "docs" / "generated" / "test_results.sdoc"

# StrictDoc's own label pair for tests. "satisfies" would claim a failed test
# satisfies its requirement.
ROLE = "verifies"
REVERSE_ROLE = "is verified by"
STATUSES = ("PASSED", "FAILED", "SKIPPED", "NOT_RUN")

BRIEF = re.compile(r"@brief\s+(.*?)\s*(?=\n\s*\*\s*@|\n\s*\*/)", re.DOTALL)

HEADER = f"""\
[DOCUMENT]
TITLE: Test results
OPTIONS:
  VIEW_STYLE: Table

[GRAMMAR]
ELEMENTS:
- TAG: TEXT
  FIELDS:
  - TITLE: STATEMENT
    TYPE: String
    REQUIRED: True
- TAG: TEST_RESULT
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: True
  - TITLE: TITLE
    TYPE: String
    REQUIRED: True
  - TITLE: STATUS
    TYPE: SingleChoice({", ".join(STATUSES)})
    REQUIRED: True
  - TITLE: DESCRIPTION
    TYPE: String
    REQUIRED: False
  - TITLE: TEST_PATH
    TYPE: String
    REQUIRED: True
  - TITLE: TEST_FUNCTION
    TYPE: String
    REQUIRED: True
  - TITLE: LINE
    TYPE: String
    REQUIRED: False
  - TITLE: DURATION
    TYPE: String
    REQUIRED: False
  - TITLE: MESSAGE
    TYPE: String
    REQUIRED: False
  RELATIONS:
  - TYPE: Parent
    ROLE: {ROLE}
    REVERSE_ROLE: {REVERSE_ROLE}
  - TYPE: File
"""


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


def section_uid(path: str) -> str:
    """The anchor of a test file's section, for links from the overview table."""
    return "TF-" + pathlib.Path(path).stem


def text_node(statement: str) -> str:
    return f"[TEXT]\nSTATEMENT: >>>\n{statement}\n<<<"


def result_node(number: int, test: Test) -> str:
    node = [
        "[TEST_RESULT]",
        # The requirement's Child list shows "UID TITLE", so the UID stays
        # short: a running number plus the status. The status ends the UID
        # because StrictDoc's HTML carries the UID in attributes (href,
        # data-uid) but not the STATUS field, and CSS can only match
        # attributes. tools/strictdoc/site.css colours on that
        # suffix. Nothing links to these UIDs by hand, so a UID that
        # changes with the result is harmless.
        f"UID: TR-{number:03d}-{test.status}",
        f"TITLE: {test.function}",
        f"STATUS: {test.status}",
    ]
    if test.brief:
        node.append(f"DESCRIPTION: {rst_text(test.brief)}")
    node += [f"TEST_PATH: {test.path}", f"TEST_FUNCTION: {test.function}"]
    if test.line:
        node.append(f"LINE: {test.line}")
    if test.duration is not None:
        node.append(f"DURATION: {test.duration:.3f} s")
    if test.message:
        node.append(f"MESSAGE: {rst_text(test.message)}")
    node.append("RELATIONS:")
    for uid in test.uids:
        node += ["- TYPE: Parent", f"  VALUE: {uid}", f"  ROLE: {ROLE}"]
    node += ["- TYPE: File", f"  VALUE: {test.path}", f"  FUNCTION: {test.function}"]
    return "\n".join(node)


def main() -> int:
    tests = collect_tests()
    _, suite_durations = read_report()
    by_file: dict[str, list[Test]] = {}
    for test in tests:
        by_file.setdefault(test.path, []).append(test)

    header = ["Test file", "Tests", "Passed", "Failed", "Skipped", "Not run", "Duration"]
    rows = [
        # Each file name links to its section further down.
        [f"`{path} <#{section_uid(path)}>`_", *counts(group), f"{suite_durations.get(path, 0):.3f} s"]
        for path, group in by_file.items()
    ]
    rows.append(["**All files**", *counts(tests), f"{sum(suite_durations.values()):.3f} s"])
    overview = (
        f"Generated from ``{JUNIT_REPORT.relative_to(ROOT)}`` by "
        "``tools/test_results_to_sdoc.py``.\n\n"
        + list_table("All test files", header, rows, widths="40 10 10 10 10 10 10")
    )

    # The SDoc grammar allows exactly one blank line between blocks.
    parts = [HEADER.rstrip("\n"), text_node(overview)]
    number = 0
    for path, group in by_file.items():
        parts.append(f"[[SECTION]]\nUID: {section_uid(path)}\nTITLE: {path}")
        parts.append(
            text_node(
                list_table(
                    f"Summary for {path}",
                    header[1:],
                    [[*counts(group), f"{suite_durations.get(path, 0):.3f} s"]],
                )
            )
        )
        for test in group:
            number += 1
            parts.append(result_node(number, test))
        parts.append("[[/SECTION]]")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    summary = dict(zip(STATUSES, counts(tests)[1:]))
    print(f"test_results_to_sdoc: wrote {OUT.relative_to(ROOT)} ({len(tests)} results in {len(by_file)} files, {summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
