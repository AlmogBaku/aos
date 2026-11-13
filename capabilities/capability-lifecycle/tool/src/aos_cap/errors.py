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
    SLOT_UNRESOLVABLE = 18
    LINK_OWNED = 19
    NO_HARNESS = 20
    BAD_RENDER_ID = 21      # swap/discard: not a capability id, or a symlinked render dir
    NOT_STAGED = 22         # swap/discard: nothing at rendered/.staging/<id>
    STAGED_UNSAFE = 23      # swap: the staged render bakes its own staging path, or drops a linked target
    WRONG_PLACE = 24        # render --out / record / rehash: a path the household layout forbids there
    MIGRATE_BLOCKED = 25    # migrate rendered: drift, uncommitted renders, old references or old links remain
    SWAP_RECOVERED = 26     # swap: an interrupted swap's old render was put back live; run swap again


def fail(code: Exit, msg: str) -> NoReturn:
    print(f"aos-cap: {msg}", file=sys.stderr)
    sys.exit(code)
