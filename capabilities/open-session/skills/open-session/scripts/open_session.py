#!/usr/bin/env python3
"""Open one new titled Hermes session whose seed prompt is stored hidden, left unread.
Reply on stdout, `title:` + `session_id:` on stderr; needs Hermes' venv python (it must
`import hermes_state`). Flags, exit codes, why each hermes flag: reference/hermes.md."""
import argparse
import os
import subprocess
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path

SCRUB_EXACT = ("HERMES_CRON_SESSION", "HERMES_UI_SESSION_ID")
SCRUB_PREFIX = ("HERMES_SESSION_", "HERMES_CRON_AUTO_DELIVER_")

def profile_home(profile: str) -> Path:
    """<root>/profiles/<p>, or <root> for `default`; root = $HERMES_HOME (its grandparent when
    that points at a profile dir), else ~/.hermes."""
    env_home = os.environ.get("HERMES_HOME", "").strip()
    if env_home:
        p = Path(env_home)
        root = p.parent.parent if p.parent.name == "profiles" else p
    else:
        root = Path.home() / ".hermes"
    return root if profile == "default" else root / "profiles" / profile

def fresh_title(home: Path, title: str) -> str:
    """Fresh session per run: `-c --create-if-missing` *resumes* a title it can resolve (exact or
    newest `"<title> #N"`, hermes_state_titles.py:167), so a collision takes a local-clock
    ` HH:MM` suffix — ` HH:MM:SS` if that minute is taken too."""
    from hermes_state import SessionDB
    candidate = title
    with closing(SessionDB(home / "state.db")) as db:
        for fmt in ("%H:%M", "%H:%M:%S"):
            if not db.resolve_session_by_title(candidate):
                break
            candidate = f"{title} {datetime.now().strftime(fmt)}"
    return candidate

def polish(home: Path, session_id: str, seed: str, preview: str) -> None:
    """Presentation-only, never fatal (a failed step is one `warning:` line): display_kind='hidden'
    on the seed row (hermes_state_messages.py:364), then unread — a NULL `last_read_at` reads as
    *read*, so it needs an explicit 0.0 watermark plus a preview (hermes_state_sessions.py:917)."""
    from hermes_state import SessionDB
    with closing(SessionDB(home / "state.db")) as db:
        try:
            if not db.set_latest_matching_message_display_kind(
                    session_id, role="user", content=seed, display_kind="hidden"):
                raise RuntimeError("no matching seed row")
        except Exception as exc:
            sys.stderr.write(f"warning: seed left visible: {exc}\n")
        try:
            db.touch_session_activity(session_id, description=preview[:120])
            db.set_session_read(session_id, read=False)
        except Exception as exc:
            sys.stderr.write(f"warning: unread mark failed: {exc}\n")

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for flag in ("--profile", "--title", "--prompt-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--skills", action="append", metavar="NAME", default=[])
    ap.add_argument("--workdir")
    ap.add_argument("--timeout", type=float, default=540.0)
    args = ap.parse_args()
    home = profile_home(args.profile)
    for name in args.skills:
        if not (skill_md := home / "skills" / name / "SKILL.md").exists():
            sys.stderr.write(f"error: skill {name} not found at {skill_md}\n")
            return 2
    title = fresh_title(home, args.title)
    sys.stderr.write(f"title: {title}\n")

    env = {k: v for k, v in os.environ.items()
           if k not in SCRUB_EXACT and not k.startswith(SCRUB_PREFIX)}
    argv = ["hermes", "-p", args.profile, "--cli"]
    argv += [arg for name in args.skills for arg in ("--skills", name)]
    argv += ["--pass-session-id", "chat"] + (["--in", args.workdir] if args.workdir else [])
    argv += ["-c", title, "--create-if-missing", "--source", "cli",
             "-Q", "--query-file", args.prompt_file]
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=args.timeout, env=env)
    except subprocess.TimeoutExpired:
        sys.stderr.write(f'timeout: session "{title}" may still exist\n')
        return 124

    ids = [ln.split("session_id:", 1)[1].strip()
           for ln in run.stderr.splitlines() if ln.strip().startswith("session_id:")]
    if run.returncode != 0 or not ids:
        sys.stderr.write(run.stderr)
        return run.returncode or 2

    polish(home, ids[-1], Path(args.prompt_file).read_text(errors="replace"), next((s for s in
        map(str.strip, run.stdout.splitlines()) if s and not s.startswith(("⚠", "Session "))), ""))
    sys.stdout.write(run.stdout)
    sys.stderr.write(f"session_id: {ids[-1]}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
