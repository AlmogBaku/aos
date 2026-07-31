"""The check suite, in the order the linter runs it.

`CHECKS` is the code list `check-coverage` derives its count from — the equivalent of the
retired `tools/lint/checks/*.mjs` glob. It reads the code strings out of these modules'
source, so a code defined in a table and reported through a variable (secrets.py does
exactly that with its five) is still counted; a literal-argument scan saw zero of them once
and made the gate agree with a wrong number."""

from .agents import check_agents
from .cheatsheet import check_cheatsheets
from .crosspath import check_cross_paths
from .manifest import check_manifests
from .onboarding import check_onboarding
from .overlay import check_overlay_paths, check_overlay_schemas
from .refs import check_references
from .secrets import check_secrets
from .skill_names import check_skill_names
from .skills import check_skills
from .structure import check_structure
from .version_bump import check_version_bumps

# The full suite (aos-lint). Order is the .mjs order, which the sort at the end makes
# cosmetic — kept anyway so a crash report names the same check the JS one would have.
ALL = [
    check_manifests, check_skills, check_skill_names, check_agents, check_onboarding,
    check_overlay_paths, check_overlay_schemas, check_references,
    check_cheatsheets, check_cross_paths, check_secrets, check_version_bumps,
    check_structure,
]

# The selftest's suite: everything except the diff-aware version-bump pass, which needs a
# git history the fixture does not have.
SELFTEST = [c for c in ALL if c is not check_version_bumps]

__all__ = ["ALL", "SELFTEST"]
