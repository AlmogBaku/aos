"""The two repo-wide walks every gate shares: which files exist, and which of them are
capability packages."""

from pathlib import Path
from typing import NamedTuple

# tools/aos_lint/src/aos_lint/repo.py -> the repo root is five parents up.
REPO_ROOT = Path(__file__).resolve().parents[4]

# Paths the repo-wide walks never enter. The lint selftest fixture contains
# planted violations and is linted only by its own runner.
# .aos/ is deliberately NOT skipped: a committed .aos path must be caught by
# the overlay check (in CI the tree is a clean checkout, so no local noise).
# .claude/.agents/.venv/__pycache__: local harness/tooling state and build artifacts, never
# kit content. __pycache__ matters because these walks do not read .gitignore, so a compiled
# .pyc would otherwise be scanned as a source file — and a token check reads its string table.
SKIP_DIRS = {".git", "node_modules", ".sandbox", ".claude", ".agents", ".venv",
             "__pycache__"}
SKIP_PREFIXES = ["tools/lint/selftest/", "tools/aos_lint/selftest/"]


def walk_repo(root=None) -> list[str]:
    """Every file under `root`, as repo-relative slash-joined paths, unsorted in
    directory order — the JS walk's order, which several gates' output depends on."""
    root = Path(REPO_ROOT if root is None else root)
    out: list[str] = []

    def visit(directory: Path) -> None:
        for entry in _listdir(directory):
            abs_path = directory / entry
            rel = abs_path.relative_to(root).as_posix()
            if any(rel.startswith(p) or f"{rel}/" == p for p in SKIP_PREFIXES):
                continue
            # is_dir() follows symlinks, matching node's statSync (not lstatSync).
            if abs_path.is_dir():
                if entry in SKIP_DIRS:
                    continue
                visit(abs_path)
            else:
                out.append(rel)

    visit(root)
    return out


def _listdir(directory: Path) -> list[str]:
    """readdirSync order. Node returns the OS order; sorting makes the walk stable across
    filesystems, which only ever tightens a gate whose findings are sorted anyway."""
    return sorted(p.name for p in directory.iterdir())


class Capability(NamedTuple):
    id: str
    dir: Path
    rel: str


def list_capabilities(root=None) -> list[Capability]:
    """A capability is any capabilities/<id>/ directory holding a CAPABILITY.md.
    (`capabilities/<id>.md` one-pagers are the spec docs and live alongside.)"""
    root = Path(REPO_ROOT if root is None else root)
    caps_dir = root / "capabilities"
    if not caps_dir.is_dir():
        return []
    return [
        Capability(d.name, caps_dir / d.name, f"capabilities/{d.name}")
        for d in sorted(caps_dir.iterdir(), key=lambda p: p.name)
        if d.is_dir() and (d / "CAPABILITY.md").is_file()
    ]
