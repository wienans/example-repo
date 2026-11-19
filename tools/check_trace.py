#!/usr/bin/env python3
"""Check that every software requirement is implemented and verified.

Code and tests name a requirement with a StrictDoc marker that carries a role:

- ``role=Implementation`` in ``src/``: the function, range or line implements
  the requirement.
- ``role=Test`` in ``tests/``: the unit test verifies it.
- ``role=Check`` in ``tools/``: a static check verifies it over the whole tree.

A ``Test`` marker counts as evidence only if the test function right below it
passed in the last Ceedling run. The script reads that result from the JUnit
report that Ceedling's ``report_tests_log_factory`` plugin writes, so run
``make test`` first. ``make trace`` does that.

StrictDoc already rejects markers that name an unknown UID, so this script
checks the other direction. It fails when:

- a marker is malformed: it lacks the role its directory needs, sits in a
  one-line ``/* */`` comment StrictDoc ignores, or is a ``scope=function``
  marker not right above a function (see ``source_markers.py``),
- a ``Test`` marker does not sit on a ``test_*`` function,
- the JUnit report is missing, or older than a file under ``src/`` or ``tests/``,
- a software requirement has no passing ``Test`` and no ``Check``,
- a software requirement has no ``Implementation`` marker. A requirement that a
  ``Check`` verifies is exempt, because it constrains every source file rather
  than naming one,
- a ``docs/requirements/software_*.sdoc`` domain file is not included by
  ``software_requirements.sdoc``, because StrictDoc would silently leave it out.

This script checks traceability, not layering or determinism, so it carries no
marker of its own. A marker here would count as evidence for a requirement it
does not verify.
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

from source_markers import ROOT, Marker, read_markers

# PARENT includes one software_<domain>.sdoc per domain from its own folder.
# StrictDoc links a requirement to its code from the depth of the file that
# defines it, so the domain files sit next to PARENT, not in a subfolder.
PARENT = ROOT / "docs" / "requirements" / "software_requirements.sdoc"
REQUIREMENTS_DIR = PARENT.parent
DOMAIN_GLOB = "software_*.sdoc"
JUNIT_REPORT = ROOT / "build" / "ceedling" / "artifacts" / "test" / "junit_tests_report.xml"
# A report older than any of these files does not describe the current code.
REPORT_INPUTS = [ROOT / "src", ROOT / "tests", ROOT / "project.yml"]

UID_LINE = re.compile(r"^UID:\s*(SWR-[A-Z]+-\d+)\s*$", re.MULTILINE)
INCLUDE = re.compile(r"^\[DOCUMENT_FROM_FILE\]\nFILE:\s*(\S+)\s*$", re.MULTILINE)


def unincluded_files() -> list[pathlib.Path]:
    """Domain files that the parent does not include, so StrictDoc never shows them."""
    included = {
        (PARENT.parent / f).resolve()
        for f in INCLUDE.findall(PARENT.read_text(encoding="utf-8"))
    }
    return [p for p in domain_files() if p.resolve() not in included]


def domain_files() -> list[pathlib.Path]:
    return [p for p in sorted(REQUIREMENTS_DIR.glob(DOMAIN_GLOB)) if p != PARENT]


def defined_uids() -> dict[str, pathlib.Path]:
    found: dict[str, pathlib.Path] = {}
    for path in domain_files():
        for uid in UID_LINE.findall(path.read_text(encoding="utf-8")):
            found[uid] = path
    return found


def collect_markers() -> tuple[list[Marker], list[str]]:
    """The markers, plus problems: malformed markers and Test markers off a test function."""
    markers, errors = read_markers()
    kept: list[Marker] = []
    for marker in markers:
        if marker.role == "Test" and not marker.function.startswith("test_"):
            errors.append(f"{marker.where}: Test marker is not on a test_* function")
            continue
        kept.append(marker)
    return kept, errors


def newest_input() -> pathlib.Path:
    files = [p for d in REPORT_INPUTS for p in ([d] if d.is_file() else d.rglob("*")) if p.is_file()]
    return max(files, key=lambda p: p.stat().st_mtime)


def read_test_results() -> tuple[dict[tuple[str, str], str], str | None]:
    """Map (test file, test function) to passed, failed or skipped, or explain why not."""
    if not JUNIT_REPORT.is_file():
        return {}, f"{JUNIT_REPORT.relative_to(ROOT)}: missing, run make test first"
    newest = newest_input()
    if newest.stat().st_mtime > JUNIT_REPORT.stat().st_mtime:
        return {}, (
            f"{JUNIT_REPORT.relative_to(ROOT)}: older than {newest.relative_to(ROOT)}, "
            "run make test first"
        )
    results: dict[tuple[str, str], str] = {}
    for case in ET.parse(JUNIT_REPORT).iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            outcome = "failed"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        results[(case.get("file", ""), case.get("name", ""))] = outcome
    return results, None


def main() -> int:
    defined = defined_uids()
    if not defined:
        print(f"check_trace: no requirements found in {REQUIREMENTS_DIR.relative_to(ROOT)}")
        return 1
    problems: list[str] = []
    for path in unincluded_files():
        problems.append(f"{path.relative_to(ROOT)}: not included by {PARENT.relative_to(ROOT)}")

    markers, marker_errors = collect_markers()
    problems.extend(marker_errors)
    results, report_error = read_test_results()
    if report_error:
        problems.append(report_error)

    implemented: set[str] = set()
    verified: set[str] = set()
    # Why each test that names a requirement does not count, keyed by UID.
    unproven: dict[str, list[str]] = {}
    for marker in markers:
        if marker.role in ("Implementation", "Check"):
            implemented.update(marker.uids)
        if marker.role == "Check":
            verified.update(marker.uids)
        if marker.role == "Test":
            outcome = results.get((marker.file, marker.function), "not run")
            if outcome == "passed":
                verified.update(marker.uids)
            else:
                for uid in marker.uids:
                    unproven.setdefault(uid, []).append(f"{marker.function} {outcome}")

    # Without a usable report every test reads "not run". The report error is the
    # one cause, so it stands alone instead of one line per requirement.
    if not report_error:
        for uid in sorted(defined.keys() - verified):
            why = f" ({', '.join(unproven[uid])})" if uid in unproven else ""
            problems.append(f"{defined[uid].relative_to(ROOT)}: {uid} has no passing test or check{why}")
    for uid in sorted(defined.keys() - implemented):
        problems.append(f"{defined[uid].relative_to(ROOT)}: {uid} has no implementation")

    for line in problems:
        print(line)
    if report_error:
        print(f"check_trace: test evidence unknown, {len(defined.keys() & implemented)}/{len(defined)} implemented")
        return 1
    print(
        f"check_trace: {len(defined.keys() & verified)}/{len(defined)} requirements verified, "
        f"{len(defined.keys() & implemented)}/{len(defined)} implemented"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
