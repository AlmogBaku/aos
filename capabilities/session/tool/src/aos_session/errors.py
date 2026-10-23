import sys
from enum import IntEnum
from typing import NoReturn


class Exit(IntEnum):
    """Exit codes are the contract — callers (hooks, cron agents) branch on them. Never
    renumber; only append."""
    OK = 0
    HARNESS_FAILED = 1      # the harness command failed, or printed no session id
    BAD_INPUT = 2           # bad flag value, no household, no harness record, bad sheet
    UNSUPPORTED = 4         # the sheet says this harness cannot do the step
    TIMEOUT = 124


def fail(code: Exit, msg: str) -> NoReturn:
    print(f"aos-session: {msg}", file=sys.stderr)
    sys.exit(code)
