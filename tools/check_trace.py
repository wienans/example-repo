#!/usr/bin/env python3
"""Check that every software requirement is verified.

A requirement counts as verified when a file under ``tests/`` or ``tools/``
carries a ``@relation(<UID>, ...)`` marker for it. StrictDoc already rejects
markers that name an unknown UID, so this script checks the other direction.

@relation(SWR-ARC-001, SWR-DET-001, scope=file)
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "docs" / "requirements" / "software_requirements.sdoc"
VERIFICATION_DIRS = [ROOT / "tests", ROOT / "tools"]
VERIFICATION_SUFFIXES = {".c", ".py"}

UID_LINE = re.compile(r"^UID:\s*(SWR-[A-Z]+-\d+)\s*$", re.MULTILINE)
RELATION = re.compile(r"@relation\(([^)]*)\)")


def defined_uids() -> set[str]:
    return set(UID_LINE.findall(REQUIREMENTS.read_text(encoding="utf-8")))


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
    missing = sorted(defined - verified_uids())
    for uid in missing:
        print(f"{REQUIREMENTS.relative_to(ROOT)}: {uid} has no test or check")
    print(f"check_trace: {len(defined) - len(missing)}/{len(defined)} requirements verified")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
