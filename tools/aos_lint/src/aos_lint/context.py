"""The context every check reads, and the finding it reports.

One object rather than a bag of arguments, for the reason the .mjs version passed a `ctx`:
`files` and `caps` are two repo-wide walks, and a suite of thirteen checks each doing its own
would be thirteen walks of a tree the first one already read."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .repo import Capability, list_capabilities, walk_repo


@dataclass
class Finding:
    severity: str
    code: str
    file: str
    message: str


@dataclass
class Context:
    root: Path
    files: list[str]
    caps: list[Capability]
    findings: list[Finding] = field(default_factory=list)
    base: Optional[str] = None
    personal_root: bool = False
    dep_roots: list[Path] = field(default_factory=list)

    def report(self, severity: str, code: str, file: str, message: str) -> None:
        self.findings.append(Finding(severity, code, file, message))


def build_context(root, base=None, personal_root=False, dep_roots=()) -> Context:
    # Resolved, always — every real entry point already passed an absolute root (the JS
    # linter did `resolve(rootArg)`), and `refs/escape` is why it must stay that way: it
    # decides "inside the tree?" by string prefix against `root`, so a RELATIVE root
    # reported every dead link as an escape instead. Resolving here means no caller can
    # reintroduce that by passing a path relative to the cwd.
    root = Path(root).resolve()
    return Context(root=root, files=walk_repo(root), caps=list_capabilities(root),
                   base=base, personal_root=personal_root, dep_roots=list(dep_roots))
