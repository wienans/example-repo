#!/usr/bin/env python3
"""Build the release PDFs, tag the release and publish it on GitHub.

Usage: release.py VERSION [--previous TAG] [--no-publish]

1. Checks that the tree is clean, on main, and contains origin/main.
2. Tags HEAD as VERSION, so the PDFs print VERSION on their title page.
3. Prints every StrictDoc document into one PDF:
   build/release/documentation-VERSION.pdf
4. Prints StrictDoc's Diff screen, Changelog tab, from the previous tag to
   VERSION: build/release/changes-PREVIOUS-to-VERSION.pdf
5. Pushes main and the tag, and creates a GitHub release with both PDFs.

A failing build deletes the local tag again. --no-publish stops after step 4
and deletes the tag, to check the PDFs before a real release.
"""

import argparse
import html
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "release"
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")

# The Diff screen is laid out for a browser window: a fixed-height grid
# with a scrolling main area. For print, everything flows on the page, and
# the navigation, the revision form and the tabs go away.
PRINT_CSS = """
@page { size: A4; margin: 12mm; }
html, body, .layout, .layout_main, .main, .content,
turbo-frame, .changelog, .changelog_content, .changelog_changes {
  display: block !important;
  height: auto !important;
  max-height: none !important;
  overflow: visible !important;
  position: static !important;
}
body { background: white !important; }
.layout_nav, .layout_header, .layout_footer, .layout_aside, .layout_toc,
.layout_tree, sdoc-form, sdoc-toast, .sdoc-tabs, .skeleton { display: none !important; }
.release-title { font: 600 20px sans-serif; margin: 0 0 16px; }
.changelog_change_meta { break-after: avoid; }
.diff_node_field { break-inside: avoid; }
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


def tool_env() -> dict:
    """StrictDoc's PDF export calls html2pdf4doc, which sits next to strictdoc."""
    env = dict(os.environ)
    strictdoc = shutil.which(env.get("STRICTDOC", "strictdoc"))
    if strictdoc is None:
        fail("strictdoc not found; set STRICTDOC")
    env["PATH"] = str(Path(strictdoc).parent) + os.pathsep + env["PATH"]
    env["STRICTDOC"] = strictdoc
    chrome = env.get("HTML2PDF4DOC_CHROME_BINARY") or env.get(
        "PUPPETEER_EXECUTABLE_PATH"
    ) or shutil.which("chromium") or shutil.which("google-chrome")
    if not chrome:
        fail("Chrome or Chromium not found; set PUPPETEER_EXECUTABLE_PATH")
    env["HTML2PDF4DOC_CHROME_BINARY"] = chrome
    return env


def build_full_pdf(env: dict, version: str) -> Path:
    out_dir = OUT / "strictdoc"
    run(
        env["STRICTDOC"], "export", ".",
        "--formats", "html2pdf",
        "--generate-bundle-document",
        "--output-dir", str(out_dir),
        env=env,
    )
    target = OUT / f"documentation-{version}.pdf"
    shutil.copyfile(out_dir / "html2pdf" / "pdf" / "bundle.pdf", target)
    return target


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=300) as response:
        return response.read().decode("utf-8")


def build_diff_pdf(env: dict, previous: str, version: str) -> Path:
    """StrictDoc computes the diff only in its web server, so start one,
    take the Changelog tab and print it with headless Chrome."""
    port = free_port()
    base = f"http://127.0.0.1:{port}/"
    log = open(OUT / "strictdoc-server.log", "w")
    server = subprocess.Popen(
        [env["STRICTDOC"], "server", ".", "--port", str(port),
         "--output-path", str(OUT / "server")],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(120):
            if server.poll() is not None:
                fail(f"strictdoc server exited; see {log.name}")
            try:
                fetch(base)
                break
            except OSError:
                time.sleep(1)
        else:
            fail("strictdoc server did not start")

        query = urllib.parse.urlencode(
            {"tab": "changelog", "left_revision": previous,
             "right_revision": version}
        )
        page = fetch(f"{base}diff?{query}")
        result = fetch(f"{base}diff_result?{query}")
        if 'class="changelog' not in result:
            fail("the Diff screen returned no changelog")

        # The page loads its result lazily into a turbo-frame. Put the result
        # in directly, drop the scripts, and resolve assets against the server.
        page = re.sub(
            r'<turbo-frame id="diff_result".*?</turbo-frame>',
            lambda _: result, page, count=1, flags=re.S,
        )
        page = re.sub(r"<script\b.*?</script>", "", page, flags=re.S)
        title = html.escape(f"Changes from {previous} to {version}")
        page = page.replace(
            "<head>",
            f'<head><base href="{base}"><style>{PRINT_CSS}</style>', 1,
        ).replace("<title>", f"<title>{title} - ", 1)
        page = re.sub(
            r"(<main[^>]*>)",
            rf'\1<h1 class="release-title">{title}</h1>', page, count=1,
        )
        html_path = OUT / "changes.html"
        html_path.write_text(page, encoding="utf-8")

        target = OUT / f"changes-{previous}-to-{version}.pdf"
        run(
            env["HTML2PDF4DOC_CHROME_BINARY"], "--headless", "--no-sandbox",
            "--disable-gpu", "--no-pdf-header-footer",
            "--virtual-time-budget=10000",
            f"--print-to-pdf={target}", html_path.as_uri(),
            env=env, capture_output=True,
        )
        if not target.exists() or target.stat().st_size == 0:
            fail("Chrome wrote no diff PDF")
        return target
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()


def publish(version: str, previous: str, pdfs: list) -> None:
    run("git", "push", "origin", "main")
    run("git", "push", "origin", version)
    notes = (
        f"Documentation of {version}.\n\n"
        f"- `{pdfs[0].name}`: every requirement, architecture page and ADR, "
        "with the test results and code coverage of this version.\n"
        f"- `{pdfs[1].name}`: what changed since {previous}, from the "
        "StrictDoc Diff screen."
    )
    run(
        "gh", "release", "create", version, *map(str, pdfs),
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
    previous = args.previous or git("describe", "--tags", "--abbrev=0", "HEAD")
    git("rev-parse", "--verify", f"{previous}^{{commit}}")
    env = tool_env()

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    run("git", "tag", "-a", args.version, "-m", f"Release {args.version}")
    try:
        pdfs = [
            build_full_pdf(env, args.version),
            build_diff_pdf(env, previous, args.version),
        ]
    except BaseException:
        run("git", "tag", "-d", args.version)
        raise
    for pdf in pdfs:
        print(f"release: wrote {pdf.relative_to(ROOT)}")

    if args.no_publish:
        run("git", "tag", "-d", args.version)
        return
    publish(args.version, previous, pdfs)


if __name__ == "__main__":
    main()
