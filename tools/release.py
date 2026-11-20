#!/usr/bin/env python3
"""Build the release PDFs, tag the release and publish it on GitHub.

Usage: release.py VERSION [--previous TAG] [--no-publish]

1. Checks that the tree is clean, on main, and contains origin/main.
2. Tags HEAD as VERSION.
3. Builds the Sphinx site as one page and prints it with headless Chromium:
   build/release/documentation-VERSION.pdf
4. Builds needs.json for the previous tag and for VERSION, compares the
   system and software requirements by ID (tools/needs_diff.py) and prints
   the report: build/release/changes-PREVIOUS-to-VERSION.pdf
5. Zips the HTML that make docs built, build/sphinx/html and
   build/doxygen/html, into build/release/docs-VERSION.zip.
6. Pushes main and the tag, and creates a GitHub release with the two PDFs
   and the zip.

A failing build deletes the local tag again. --no-publish stops after step 5
and deletes the tag, to check the files before a real release.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import needs_diff

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "release"
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")
COVERAGE_JSON = ROOT / "build/ceedling/artifacts/gcov/gcovr/GcovCoverage.json"
SPHINX = os.environ.get("SPHINX") or "sphinx-build"
# Folders that make docs builds, and their names inside the zip.
SITES = {
    ROOT / "build" / "sphinx" / "html": "sphinx/html",
    ROOT / "build" / "doxygen" / "html": "doxygen/html",
}

# Furo keeps every table, paragraph and code block on one page, which pushes
# a long needs table or listing to the next page and leaves the rest of the
# page blank. For print, tables and code break between rows and lines, long
# code lines wrap, and the controls that only work on screen go away.
PRINT_CSS = """
@page { size: A4; margin: 15mm 12mm; }
.skip-to-content, .back-to-top, .needs_collapse { display: none !important; }
table, pre, p, ul, ol, dl, blockquote { break-inside: auto !important; }
tr, .mermaid, object, img { break-inside: avoid; }
object, img { max-width: 100% !important; height: auto; }
pre { white-space: pre-wrap !important; overflow-wrap: anywhere; }
.release-version { font-size: 1.4em; margin: 0 0 1.5em; }
"""


def run(*cmd: str, **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, check=True, text=True, **kwargs)


def git(*args: str) -> str:
    return run("git", *args, capture_output=True).stdout.strip()


def fail(message: str) -> None:
    sys.exit(f"release: {message}")


def check_repo(version: str) -> None:
    if not VERSION_RE.match(version):
        fail(f"VERSION must look like v1.2.3, got {version!r}")
    if git("status", "--porcelain"):
        fail("the working tree has uncommitted changes; commit them first")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        fail("releases are made from main")
    git("fetch", "--tags", "origin")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"], cwd=ROOT
    ).returncode != 0:
        fail("main is behind origin/main; pull first")
    if git("tag", "--list", version):
        fail(f"tag {version} already exists")


def find_chrome() -> str:
    chrome = os.environ.get("PUPPETEER_EXECUTABLE_PATH") or shutil.which(
        "chromium"
    ) or shutil.which("google-chrome")
    if not chrome:
        fail("Chrome or Chromium not found; set PUPPETEER_EXECUTABLE_PATH")
    return chrome


def print_pdf(chrome: str, page: Path, target: Path) -> Path:
    run(
        chrome, "--headless", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", "--virtual-time-budget=10000",
        f"--print-to-pdf={target}", page.as_uri(),
        capture_output=True,
    )
    if not target.exists() or target.stat().st_size == 0:
        fail(f"Chrome wrote no {target.name}")
    return target


def build_full_pdf(chrome: str, version: str) -> Path:
    """Build the site as one page, as make docs does, and print it."""
    site = OUT / "singlehtml"
    run(
        SPHINX, "-q", "-W", "--keep-going", "-b", "singlehtml",
        "-D", f"release={version}", "-D", f"version={version}",
        "docs", str(site),
    )
    page = site / "index.html"
    text = page.read_text(encoding="utf-8")
    text = text.replace("</head>", f"<style>{PRINT_CSS}</style></head>", 1)
    text = text.replace(
        "</h1>", f'</h1><p class="release-version">Version {version}</p>', 1
    )
    page.write_text(text, encoding="utf-8")
    return print_pdf(chrome, page, OUT / f"documentation-{version}.pdf")


def build_needs_json(docs: Path, out_dir: Path) -> Path:
    """-Q instead of -W: a checkout of an older tag has no docs/generated/
    pages and no Doxygen XML, and neither holds a requirement. -Q still
    prints errors."""
    run(SPHINX, "-Q", "-b", "needs", str(docs), str(out_dir))
    return out_dir / "needs.json"


def build_changelog(chrome: str, previous: str, version: str) -> Path:
    new = needs_diff.load(build_needs_json(ROOT / "docs", OUT / "needs-new"))
    has_sphinx = subprocess.run(
        ["git", "cat-file", "-e", f"{previous}:docs/conf.py"], cwd=ROOT,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    old = None
    if has_sphinx:
        tree = OUT / "previous"
        run("git", "worktree", "add", "--detach", str(tree), previous)
        try:
            old = needs_diff.load(
                build_needs_json(tree / "docs", OUT / "needs-old")
            )
        finally:
            run("git", "worktree", "remove", "--force", str(tree))
    page = OUT / "changes.html"
    page.write_text(needs_diff.render(old, new, previous, version), encoding="utf-8")
    return print_pdf(chrome, page, OUT / f"changes-{previous}-to-{version}.pdf")


def build_site_zip(version: str) -> Path:
    target = OUT / f"docs-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for folder, name in SITES.items():
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, f"{name}/{path.relative_to(folder)}")
    return target


def publish(version: str, previous: str, files: list) -> None:
    run("git", "push", "origin", "main")
    run("git", "push", "origin", version)
    notes = (
        f"Documentation of {version}.\n\n"
        f"- `{files[0].name}`: every requirement, architecture page and ADR, "
        "with the test results and code coverage of this version.\n"
        f"- `{files[1].name}`: the system and software requirements added, "
        f"removed or changed since {previous}.\n"
        f"- `{files[2].name}`: the Sphinx site (`sphinx/html/index.html`) "
        "and the Doxygen API reference (`doxygen/html/index.html`)."
    )
    run(
        "gh", "release", "create", version, *map(str, files),
        "--verify-tag", "--title", version, "--notes", notes,
        "--generate-notes", "--notes-start-tag", previous,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="new tag, for example v0.2.0")
    parser.add_argument("--previous", help="tag to diff against "
                        "(default: the latest tag before HEAD)")
    parser.add_argument("--no-publish", action="store_true",
                        help="build the PDFs, then delete the tag again")
    args = parser.parse_args()

    check_repo(args.version)
    # make reports leaves a placeholder coverage document when gcovr did not
    # run. A release must not ship that.
    if not COVERAGE_JSON.exists():
        fail(f"{COVERAGE_JSON.relative_to(ROOT)} is missing; run make reports "
             "and check that gcovr is installed")
    for folder in SITES:
        if not (folder / "index.html").exists():
            fail(f"{folder.relative_to(ROOT)}/index.html is missing; run make docs")
    previous = args.previous or git("describe", "--tags", "--abbrev=0", "HEAD")
    git("rev-parse", "--verify", f"{previous}^{{commit}}")
    chrome = find_chrome()

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    # Forget worktrees that an aborted run left under OUT.
    git("worktree", "prune")
    run("git", "tag", "-a", args.version, "-m", f"Release {args.version}")
    try:
        files = [
            build_full_pdf(chrome, args.version),
            build_changelog(chrome, previous, args.version),
            build_site_zip(args.version),
        ]
    except BaseException:
        run("git", "tag", "-d", args.version)
        raise
    for file in files:
        print(f"release: wrote {file.relative_to(ROOT)}")

    if args.no_publish:
        run("git", "tag", "-d", args.version)
        return
    publish(args.version, previous, files)


if __name__ == "__main__":
    main()
