"""How this tool says no: one exit-code enum and one exit function.

Exit codes ARE the interface (ARCHITECTURE §2.4) — the skills branch on them in prose
and the tier-0 suite asserts the numbers, so they live in one named place rather than
as bare integers scattered through eleven verbs."""

import sys
from enum import IntEnum
from typing import NoReturn


class Exit(IntEnum):
    """Exit codes are the contract — tests assert these numbers and skills branch on
    them in prose. Never renumber; only append."""
    OK = 0
    GENERIC = 1
    MANIFEST_INVALID = 12
    DRIFT = 13
    NO_ENTRY = 14
    NO_HOME = 15
    ARTIFACT_MISSING = 16
    NAME_COLLISION = 17


def fail(code: Exit, msg: str) -> NoReturn:
    print(f"aos-cap: {msg}", file=sys.stderr)
    sys.exit(code)
