#!/usr/bin/env python3
"""Check that every software requirement is implemented and verified.

Code and tests name a requirement with a StrictDoc marker that carries a role:

- ``role=Implementation`` in ``src/``: the function implements the requirement.
- ``role=Test`` in ``tests/``: the unit test verifies it.
- ``role=Check`` in ``tools/``: a static check verifies it over the whole tree.

StrictDoc already rejects markers that name an unknown UID, so this script
checks the other direction. It fails when:

- a marker under one of those directories lacks the role that directory needs,
- a software requirement has no ``Test`` or ``Check`` marker,
- a software requirement has no ``Implementation`` marker. A requirement that a
  ``Check`` verifies is exempt, because it constrains every source file rather
  than naming one,
- a file in ``docs/requirements/software/`` is not included by
  ``software_requirements.sdoc``, because StrictDoc would silently leave it out.

This script checks traceability, not layering or determinism, so it carries no
marker of its own. A marker here would count as evidence for a requirement it
does not verify.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# PARENT includes one file per domain from REQUIREMENTS_DIR.
PARENT = ROOT / "docs" / "requirements" / "software_requirements.sdoc"
REQUIREMENTS_DIR = ROOT / "docs" / "requirements" / "software"
# The role every marker in a directory must carry.
ROLE_BY_DIR = {
    ROOT / "src": "Implementation",
    ROOT / "tests": "Test",
    ROOT / "tools": "Check",
}
VERIFYING_ROLES = {"Test", "Check"}
MARKED_SUFFIXES = {".c", ".h", ".py"}

UID_LINE = re.compile(r"^UID:\s*(SWR-[A-Z]+-\d+)\s*$", re.MULTILINE)
RELATION = re.compile(r"@relation\(([^)]*)\)")
INCLUDE = re.compile(r"^\[DOCUMENT_FROM_FILE\]\nFILE:\s*(\S+)\s*$", re.MULTILINE)


def unincluded_files() -> list[pathlib.Path]:
    """Domain files that the parent does not include, so StrictDoc never shows them."""
    included = {
        (PARENT.parent / f).resolve()
        for f in INCLUDE.findall(PARENT.read_text(encoding="utf-8"))
    }
    return [p for p in sorted(REQUIREMENTS_DIR.glob("*.sdoc")) if p.resolve() not in included]


def defined_uids() -> dict[str, pathlib.Path]:
    found: dict[str, pathlib.Path] = {}
    for path in sorted(REQUIREMENTS_DIR.glob("*.sdoc")):
        for uid in UID_LINE.findall(path.read_text(encoding="utf-8")):
            found[uid] = path
    return found


def collect_markers() -> tuple[dict[str, set[str]], list[str]]:
    """Map each role to the UIDs it names, and list markers with the wrong role."""
    by_role: dict[str, set[str]] = {}
    errors: list[str] = []
    for directory, expected in ROLE_BY_DIR.items():
        for path in sorted(directory.rglob("*")):
            if path.suffix not in MARKED_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8")
            for match in RELATION.finditer(text):
                args = [a.strip() for a in match.group(1).split(",")]
                uids = [a for a in args if a.startswith("SWR-")]
                if not uids:
                    continue
                roles = [a.removeprefix("role=") for a in args if a.startswith("role=")]
                role = roles[0] if roles else None
                if role != expected:
                    line = text.count("\n", 0, match.start()) + 1
                    errors.append(
                        f"{path.relative_to(ROOT)}:{line}: marker needs role={expected}, "
                        f"has {'role=' + role if role else 'no role'}"
                    )
                    continue
                by_role.setdefault(role, set()).update(uids)
    return by_role, errors


def main() -> int:
    defined = defined_uids()
    if not defined:
        print(f"check_trace: no requirements found in {REQUIREMENTS_DIR.relative_to(ROOT)}")
        return 1
    problems: list[str] = []
    for path in unincluded_files():
        problems.append(f"{path.relative_to(ROOT)}: not included by {PARENT.relative_to(ROOT)}")

    by_role, role_errors = collect_markers()
    problems.extend(role_errors)

    verified = set().union(*(by_role.get(r, set()) for r in VERIFYING_ROLES))
    implemented = by_role.get("Implementation", set()) | by_role.get("Check", set())
    for uid in sorted(defined.keys() - verified):
        problems.append(f"{defined[uid].relative_to(ROOT)}: {uid} has no test or check")
    for uid in sorted(defined.keys() - implemented):
        problems.append(f"{defined[uid].relative_to(ROOT)}: {uid} has no implementation")

    for line in problems:
        print(line)
    print(
        f"check_trace: {len(defined.keys() & verified)}/{len(defined)} requirements verified, "
        f"{len(defined.keys() & implemented)}/{len(defined)} implemented"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
