from pathlib import Path
import sys

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project_metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())

project = project_metadata["project"]["name"]
author = "Benjamin J. Schiller"
copyright = "2012, Benjamin J. Schiller"
release = project_metadata["project"]["version"]
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

exclude_patterns = ["_build"]
html_theme = "furo"
html_title = f"{project} {release} documentation"
htmlhelp_basename = "twobitreaderdoc"

latex_documents = [
    ("index", "twobitreader.tex", "twobitreader Documentation", author, "manual"),
]

man_pages = [
    ("index", "twobitreader", "twobitreader Documentation", [author], 1),
]

texinfo_documents = [
    (
        "index",
        "twobitreader",
        "twobitreader Documentation",
        author,
        "twobitreader",
        project_metadata["project"]["description"],
        "Miscellaneous",
    ),
]
