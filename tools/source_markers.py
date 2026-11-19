"""Read the StrictDoc @relation markers in src/, tests/ and tools/.

check_trace.py, test_results_to_sdoc.py and coverage_to_sdoc.py all work from
these markers, so they read them in one place and the way StrictDoc's C reader
does:

- A marker may sit in a ``/* */`` or a ``//`` comment. StrictDoc finds nothing
  in a one-line ``/* @relation(...) */``, so such a marker is an error here
  rather than evidence StrictDoc does not show.
- A ``scope=function`` marker belongs to the comment that ends on the line
  right above the function definition. In ``//`` style each line is a comment
  of its own, so the marker's line must be that line.
- Every marker names its role, and each directory has one: Implementation in
  src/, Test in tests/, Check in tools/.
"""

import dataclasses
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
# The role every marker in a directory must carry.
ROLE_BY_DIR = {
    ROOT / "src": "Implementation",
    ROOT / "tests": "Test",
    ROOT / "tools": "Check",
}
MARKED_SUFFIXES = {".c", ".h", ".py"}

RELATION = re.compile(r"@relation\(([^)]*)\)")
# After the marker: the rest of the block comment, "*/", then the definition.
FUNCTION_AFTER_BLOCK_COMMENT = re.compile(
    r"[^\n]*\n(?:[ \t]*\*[^/\n][^\n]*\n|[ \t]*\*\n)*[ \t]*\*/[ \t]*\n[\w \t\*]*?\b(\w+)\s*\("
)
# After a // marker: the definition on the next line.
FUNCTION_AFTER_LINE_COMMENT = re.compile(r"[^\n]*\n[\w \t\*]*?\b(\w+)\s*\(")


@dataclasses.dataclass
class Marker:
    path: pathlib.Path
    line: int
    role: str
    scope: str
    uids: list[str]
    function: str = ""  # the function below a scope=function marker

    @property
    def file(self) -> str:
        return str(self.path.relative_to(ROOT))

    @property
    def where(self) -> str:
        return f"{self.file}:{self.line}"


def read_markers() -> tuple[list[Marker], list[str]]:
    """Every marker that names a software requirement, and the problems found."""
    markers: list[Marker] = []
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
                role = next((a.removeprefix("role=") for a in args if a.startswith("role=")), "")
                scope = next((a.removeprefix("scope=") for a in args if a.startswith("scope=")), "")
                marker = Marker(path, text.count("\n", 0, match.start()) + 1, role, scope, uids)

                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                before = text[line_start : match.start()]
                after = text[match.end() : line_end if line_end != -1 else len(text)]
                in_line_comment = "//" in before
                if path.suffix in (".c", ".h") and not in_line_comment and "/*" in before and "*/" in after:
                    errors.append(
                        f"{marker.where}: StrictDoc ignores a marker in a one-line /* */ comment; "
                        "use // or put the marker on its own line of a block comment"
                    )
                    continue
                if role != expected:
                    has = f"role={role}" if role else "no role"
                    errors.append(f"{marker.where}: marker needs role={expected}, has {has}")
                    continue
                if scope == "function":
                    pattern = FUNCTION_AFTER_LINE_COMMENT if in_line_comment else FUNCTION_AFTER_BLOCK_COMMENT
                    function = pattern.match(text, match.end())
                    if function is None:
                        errors.append(f"{marker.where}: scope=function marker is not right above a function definition")
                        continue
                    marker.function = function.group(1)
                markers.append(marker)
    return markers, errors
