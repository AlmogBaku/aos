"""What the runner reads and refuses. `SESSION_KEYS` must equal `aos_cap.constants.SESSION_KEYS`
— the vocabulary the lint checks every sheet against; `tests/tool/test_session.py` imports both
and asserts it, so the two cannot drift while each tool stays an independent package."""

import re
from pathlib import Path

VERSION = "0.1.1"                       # tracks the session capability version
HARNESS_REL = Path(".aos") / "harness.yml"
SESSION_KEYS = ("open", "continue", "id", "missing")
PLACEHOLDERS = ("<profile>", "<title>", "<file>", "<session_id>", "<workdir>")
SKILLS_TOKEN = "<skills>"
# A profile or a session id goes into the harness argv as one token; a value that starts
# with `-` would become a flag, so both are held to a plain shape.
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
LEFTOVER_RE = re.compile(r"<[a-z_]+>")
TITLE_MAX = 90                          # Hermes refuses > 100; the " HH:MM" suffix needs room
DEFAULT_TIMEOUT = 540.0
# A session another turn is writing to refuses a second writer (the sheet's `busy` pattern):
# notify retries the continue this often, for this long, before it fails.
BUSY_RETRY = 30.0
BUSY_WAIT = 600.0
