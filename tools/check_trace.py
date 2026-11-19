#!/usr/bin/env python3
"""Check that every software requirement is verified.

A requirement counts as verified when a file under ``tests/`` or ``tools/``
carries a ``@relation(<UID>, ...)`` marker for it. StrictDoc already rejects
markers that name an unknown UID, so this script checks the other direction.
It also fails when a file in ``docs/requirements/software/`` is not included by
``software_requirements.sdoc``, because StrictDoc would silently leave it out.

@relation(SWR-ARC-001, SWR-DET-001, scope=file)
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# PARENT includes one file per domain from REQUIREMENTS_DIR.
PARENT = ROOT / "docs" / "requirements" / "software_requirements.sdoc"
REQUIREMENTS_DIR = ROOT / "docs" / "requirements" / "software"
VERIFICATION_DIRS = [ROOT / "tests", ROOT / "tools"]
VERIFICATION_SUFFIXES = {".c", ".py"}

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


def verified_uids() -> set[str]:
    found: set[str] = set()
    for directory in VERIFICATION_DIRS:
        for path in directory.rglob("*"):
            if path.suffix not in VERIFICATION_SUFFIXES:
                continue
            for args in RELATION.findall(path.read_text(encoding="utf-8")):
                found.update(
                    a.strip() for a in args.split(",") if a.strip().startswith("SWR-")
                )
    return found


def main() -> int:
    defined = defined_uids()
    if not defined:
        print(f"check_trace: no requirements found in {REQUIREMENTS_DIR.relative_to(ROOT)}")
        return 1
    orphans = unincluded_files()
    for path in orphans:
        print(f"{path.relative_to(ROOT)}: not included by {PARENT.relative_to(ROOT)}")
    missing = sorted(defined.keys() - verified_uids())
    for uid in missing:
        print(f"{defined[uid].relative_to(ROOT)}: {uid} has no test or check")
    print(f"check_trace: {len(defined) - len(missing)}/{len(defined)} requirements verified")
    return 1 if missing or orphans else 0


if __name__ == "__main__":
    sys.exit(main())
