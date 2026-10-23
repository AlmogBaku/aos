"""Where the harness facts come from: the household's `.aos/harness.yml` (written by
`aos-cap harness set`) names the installed cheat-sheet and the absolute harness CLI, and the
sheet's frontmatter `mapping.session` holds the command templates. Nothing here names a
harness — a new harness is a new sheet, never new code."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .constants import HARNESS_REL, SESSION_KEYS
from .errors import Exit, fail


@dataclass
class Harness:
    name: str
    cli: Optional[str]
    session: dict


def find_home(home: Optional[str]) -> Path:
    """`--home`, else `$AOS_HOME`, else `~/aos` — named, never discovered; it must hold `.aos/`."""
    root = Path(home or os.environ.get("AOS_HOME") or Path.home() / "aos").expanduser()
    if not (root / ".aos").is_dir():
        fail(Exit.BAD_INPUT, f"{root} is not an aos household (no .aos/) — pass --home")
    return root


def _frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        fail(Exit.BAD_INPUT, f"cannot read the cheat-sheet {path}: {e.strerror}")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        fail(Exit.BAD_INPUT, f"{path} has no frontmatter — not a structured cheat-sheet")
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        fail(Exit.BAD_INPUT, f"{path}: frontmatter does not parse: {e}")
    if not isinstance(data, dict):
        fail(Exit.BAD_INPUT, f"{path}: frontmatter is not a mapping")
    return data


def load(home: Path) -> Harness:
    rec_path = home / HARNESS_REL
    try:
        record = yaml.safe_load(rec_path.read_text())
    except OSError:
        fail(Exit.BAD_INPUT, f"no harness recorded at {rec_path} — run `aos-cap harness set <runtime>`")
    except yaml.YAMLError as e:
        fail(Exit.BAD_INPUT, f"{rec_path} does not parse: {e}")
    if not isinstance(record, dict) or not record.get("harness") or not record.get("sheet"):
        fail(Exit.BAD_INPUT, f"{rec_path} lacks harness/sheet — run `aos-cap harness set <runtime>`")
    fm = _frontmatter(Path(record["sheet"]).expanduser())
    session = (fm.get("mapping") or {}).get("session")
    name = str(record["harness"])
    if not isinstance(session, dict) or "primitive" not in session:
        fail(Exit.UNSUPPORTED, f"sessions are not supported on {name} "
                               f"(the cheat-sheet's mapping.session has no primitive)")
    for key in SESSION_KEYS:
        if key not in session:
            fail(Exit.BAD_INPUT, f"the {name} cheat-sheet's mapping.session lacks `{key}`")
    return Harness(name, record.get("cli"), session)


def step(harness: Harness, key: str) -> str:
    """The command template for one step, or exit 4 when the sheet marks it unsupported."""
    value = harness.session.get(key)
    if isinstance(value, dict):
        fail(Exit.UNSUPPORTED, f"`{key}` is not supported on {harness.name} "
                               f"({value.get('instead') or value.get('note') or 'the sheet says so'})")
    if not isinstance(value, str) or not value.strip():
        fail(Exit.BAD_INPUT, f"the {harness.name} cheat-sheet's mapping.session.{key} is empty")
    return value


def pattern(harness: Harness, key: str) -> re.Pattern:
    value = harness.session.get(key)
    regex = value.get("stderr") if isinstance(value, dict) else None
    if not isinstance(regex, str):
        fail(Exit.BAD_INPUT, f"the {harness.name} cheat-sheet's mapping.session.{key} needs a "
                             f"`stderr:` regex")
    try:
        return re.compile(regex, re.M)
    except re.error as e:
        fail(Exit.BAD_INPUT, f"mapping.session.{key}.stderr is not a regex: {e}")
