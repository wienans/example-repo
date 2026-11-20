"""Sphinx configuration for the motor control documentation.

make docs runs Doxygen first (XML for Breathe), then the generators in tools/
that write docs/generated/, then sphinx-build. See the docs target in the
Makefile and docs/adr/0006-documentation-toolchain.md.
"""

import os
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent

project = "Motor control example"
author = "Motor control team"

extensions = [
    "myst_parser",
    "sphinx_needs",
    "sphinxcontrib.mermaid",
    "breathe",
]

root_doc = "index"
exclude_patterns = ["Doxyfile", "**/.gitignore"]
# A Markdown page links to a source file by its path; it is not a document.
suppress_warnings = ["myst.xref_missing"]

html_theme = "furo"
html_title = project
html_static_path = ["_static"]
html_css_files = ["status.css"]

# -- Markdown ---------------------------------------------------------------
# ```mermaid fences stay plain Mermaid, so GitHub renders the same files.
myst_fence_as_directive = ["mermaid"]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3

# -- Mermaid ----------------------------------------------------------------
# Rendered at build time by Mermaid CLI, the one make diagrams checks with,
# so the site needs no network and prints to PDF.
mermaid_output_format = "svg"
# The same lookup as tools/check_diagrams.py.
mermaid_cmd = os.environ.get("MMDC") or shutil.which("mmdc") or "/opt/mmdc/node_modules/.bin/mmdc"
# Puppeteer looks for its own Chrome download unless told otherwise.
if shutil.which("chromium"):
    os.environ.setdefault("PUPPETEER_EXECUTABLE_PATH", shutil.which("chromium"))
mermaid_params = [
    "--configFile", str(ROOT / "tools" / "mermaid" / "mermaid.json"),
    "--puppeteerConfigFile", str(ROOT / "tools" / "mermaid" / "puppeteer.json"),
    "--backgroundColor", "transparent",
]

# -- Breathe ----------------------------------------------------------------
breathe_projects = {"motor": str(ROOT / "build" / "doxygen" / "xml")}
breathe_default_project = "motor"
breathe_domain_by_extension = {"h": "c", "c": "c"}
primary_domain = "c"


def _patch_function_pointer_typedefs() -> None:
    """Doxygen 1.18 writes ``typedef void (*f)(void *)`` as type ``void(*)``,
    name ``f``, args ``(void *)``. Breathe 5.1 joins them to ``void(*) f
    (void *)``, which Sphinx's C parser rejects, so rebuild the declaration."""
    from breathe.renderer.sphinxrenderer import SphinxRenderer

    original = SphinxRenderer.visit_typedef

    def visit_typedef(self, node):
        type_ = "".join(n.astext() for n in self.render(node.type))
        if not type_.endswith("(*)"):
            return original(self, node)
        declaration = f"{type_[:-3]} (*{node.name}){node.argsstring or ''}"
        return self.handle_declaration(node, node.kind.value, declaration)

    SphinxRenderer.visit_typedef = visit_typedef


_patch_function_pointer_typedefs()

# -- sphinx-needs -----------------------------------------------------------
# make docs runs Sphinx with -W, so a link to an unknown ID fails the build.
needs_id_required = True
needs_id_regex = r"^[A-Z][A-Z0-9-]+$"
needs_types = [
    {"directive": "sys", "title": "System requirement", "prefix": "SYS-", "color": "#BFD8D2", "style": "node"},
    {"directive": "swr", "title": "Software requirement", "prefix": "SWR-", "color": "#FEDCD2", "style": "node"},
    {"directive": "impl", "title": "Implementation", "prefix": "IMPL-", "color": "#DDDDFF", "style": "component"},
    {"directive": "check", "title": "Check", "prefix": "CHK-", "color": "#FFF2B3", "style": "component"},
    {"directive": "test", "title": "Test result", "prefix": "TR-", "color": "#DCF0C8", "style": "component"},
    {"directive": "cov", "title": "Coverage", "prefix": "COV-", "color": "#EEEEEE", "style": "artifact"},
]
needs_links = {
    "refines": {"incoming": "is refined by", "outgoing": "refines"},
    "implements": {"incoming": "is implemented by", "outgoing": "implements", "style": "dashed"},
    "verifies": {"incoming": "is verified by", "outgoing": "verifies", "color": "#2E7D2E"},
    "measures": {"incoming": "is measured by", "outgoing": "measures", "style": "dotted", "summary": True},
}
STRING = {"schema": {"type": "string"}, "nullable": True}
needs_fields = {
    "file": {"description": "Source file, relative to the repo root", **STRING},
    "function": {"description": "Function the need points at", **STRING},
    "location": {"description": "file:line of the marker or test", **STRING},
    "runtime": {"description": "Test run time", **STRING},
    "lines": {"description": "Line coverage", **STRING},
    "branches": {"description": "Branch coverage", **STRING},
    "calls": {"description": "Execution count of a function", **STRING},
    # Test results: PASSED to NOT_RUN. Coverage: FULL, PARTIAL, NONE.
    # Requirements carry no status.
    "status": {
        "schema": {"type": "string", "enum": ["PASSED", "FAILED", "SKIPPED", "NOT_RUN", "FULL", "PARTIAL", "NONE"]},
        "nullable": True,
    },
}
needs_flow_engine = "graphviz"
needs_build_json = True
