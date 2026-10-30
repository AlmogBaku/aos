# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "typer>=0.15", "aos-session", "aos-cap"]
# [tool.uv.sources]
# aos-session = { path = "../../capabilities/session/tool", editable = true }
# aos-cap = { path = "../../capabilities/capability-lifecycle/tool", editable = true }
# ///
"""Tier-0 suite for `aos-session` — in-process through typer's CliRunner, against a FAKE
harness: a script that records its argv and answers the way the sheet's patterns expect. No
real harness is touched; every value is synthetic."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from typer.testing import CliRunner

from aos_session.cli import app
from aos_session.constants import SESSION_KEYS

REPO = Path(__file__).resolve().parents[2]
TOOL_DIR = REPO / "capabilities" / "session" / "tool"
_runner = CliRunner()

FAKE = f'''#!{sys.executable}
import json, os, sys, time
argv = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as fh:
    fh.write(json.dumps({{"argv": argv, "secret": os.environ.get("FAKE_SECRET_TOKEN")}}) + "\\n")
if "--resume" in argv:
    mode = os.environ.get("FAKE_CONTINUE", "ok")
    if mode == "missing":
        print("Session not found: " + argv[argv.index("--resume") + 1], file=sys.stderr); sys.exit(1)
    if mode == "fail":
        print("upstream API error", file=sys.stderr); sys.exit(1)
    if mode in ("busy", "busy-once"):
        tries = sum(1 for _ in open(os.environ["FAKE_LOG"]))
        if mode == "busy" or tries == 1:
            print("hermes-refusal-reason: SESSION_NOT_OWNED", file=sys.stderr); sys.exit(1)
    print("turn added"); sys.exit(0)
mode = os.environ.get("FAKE_OPEN", "ok")
if mode == "sleep":
    time.sleep(5)
if mode == "fail":
    print("cannot open", file=sys.stderr); sys.exit(3)
print("first reply")
if mode != "noid":
    print("session_id: s-new1", file=sys.stderr)
'''

SHEET = r'''---
harness: fake
mapping:
  session:
    primitive: a session
    open: fakeharness -p <profile> <skills> chat --in <workdir> -c <title> -Q --query-file <file>
    skill_arg: --skills <name>
    continue: fakeharness -p <profile> chat --resume <session_id> -Q --query-file <file>
    id: {stderr: '^session_id: (\S+)$'}
    missing: {stderr: '^Session not found'}
    busy: {stderr: '^hermes-refusal-reason: SESSION_NOT_OWNED'}
    scrub_env: [FAKE_SECRET_*]
---
# Fake
'''


class Result:
    def __init__(self, r):
        self.returncode, self.stdout = r.exit_code, r.stdout
        self.stderr = r.stderr if r.stderr_bytes is not None else ""


class SessionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "home"
        (self.home / ".aos").mkdir(parents=True)
        self.cli = root / "fakeharness"
        self.cli.write_text(FAKE)
        self.cli.chmod(0o755)
        self.sheet = root / "harness-fake.md"
        self.sheet.write_text(SHEET)
        self.record({"harness": "fake", "sheet": str(self.sheet), "cli": str(self.cli)})
        self.log = root / "argv.jsonl"
        self.prompt = root / "prompt.md"
        self.prompt.write_text("Start this week's interview.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, data):
        (self.home / ".aos" / "harness.yml").write_text(yaml.safe_dump(data))

    def cli_run(self, *args, **env):
        base = {"AOS_HOME": None, "HOME": self.tmp.name, "FAKE_LOG": str(self.log)}
        r = _runner.invoke(app, ["--home", str(self.home), *args], env={**base, **env},
                           catch_exceptions=False)
        return Result(r)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def open(self, *extra, **env):
        return self.cli_run("open", "--profile", "p", "--title", "Weekly interview",
                        "--prompt-file", str(self.prompt), *extra, **env)

    def notify(self, **env):
        return self.cli_run("notify", "--profile", "default", "--session", "s-old1",
                        "--prompt-file", str(self.prompt), "--title", "Dana approved", **env)

    # -- open --------------------------------------------------------------
    def test_open_appends_the_local_time_and_reports_the_new_id(self):
        r = self.open()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r'^Opened "Weekly interview \d\d:\d\d" \(session s-new1\) '
                                   r"in profile p\.")
        argv = self.calls()[0]["argv"]
        self.assertRegex(argv[argv.index("-c") + 1], r"^Weekly interview \d\d:\d\d$")
        self.assertEqual(argv[argv.index("--query-file") + 1], str(self.prompt.resolve()))
        self.assertIn("first reply", r.stdout)

    def test_open_with_exact_title_passes_the_title_unchanged(self):
        r = self.open("--exact-title")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('Opened "Weekly interview" (session s-new1)', r.stdout)
        argv = self.calls()[0]["argv"]
        self.assertEqual(argv[argv.index("-c") + 1], "Weekly interview")

    def test_angle_brackets_in_a_value_reach_the_harness_unchanged(self):
        workdir = Path(self.tmp.name) / "<draft>"
        workdir.mkdir()
        r = self.cli_run("open", "--profile", "p", "--title", "Review <draft> and <file>",
                         "--prompt-file", str(self.prompt), "--workdir", str(workdir))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        argv = self.calls()[0]["argv"]
        self.assertRegex(argv[argv.index("-c") + 1], r"^Review <draft> and <file> \d\d:\d\d$")
        self.assertEqual(argv[argv.index("--in") + 1], str(workdir))

    def test_open_expands_skills_once_per_name(self):
        r = self.open("--skills", "alpha", "--skills", "beta")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        argv = self.calls()[0]["argv"]
        self.assertEqual(argv[2:6], ["--skills", "alpha", "--skills", "beta"])

    def test_open_without_skills_drops_the_placeholder(self):
        self.assertEqual(self.open().returncode, 0)
        self.assertEqual(self.calls()[0]["argv"][:3], ["-p", "p", "chat"])

    def test_open_that_fails_reports_cron_failure_and_exits_1(self):
        r = self.open(FAKE_OPEN="fail")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("[CRON_FAILURE]"), r.stdout)
        self.assertIn("exit 3", r.stdout)
        self.assertIn("cannot open", r.stdout)

    def test_open_with_no_session_id_on_stderr_exits_1(self):
        r = self.open(FAKE_OPEN="noid")
        self.assertEqual(r.returncode, 1)
        self.assertIn("printed no session id", r.stdout)

    def test_timeout_exits_124(self):
        r = self.open("--timeout", "1", FAKE_OPEN="sleep")
        self.assertEqual(r.returncode, 124)

    # -- notify ------------------------------------------------------------
    def test_notify_continues_a_live_session_and_opens_nothing(self):
        r = self.notify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("Added to session s-old1 in profile default."))
        calls = self.calls()
        self.assertEqual(len(calls), 1)
        argv = calls[0]["argv"]
        self.assertEqual(argv[argv.index("--resume") + 1], "s-old1")
        self.assertEqual(argv[argv.index("--query-file") + 1], str(self.prompt.resolve()))

    def test_notify_opens_a_new_session_only_when_the_old_one_is_gone(self):
        r = self.notify(FAKE_CONTINUE="missing")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, r'^Session s-old1 is gone; opened "Dana approved \d\d:\d\d" '
                                   r"\(session s-new1\)")
        self.assertEqual(len(self.calls()), 2)

    @mock.patch("aos_session.cli.BUSY_RETRY", 0.01)
    @mock.patch("aos_session.cli.BUSY_WAIT", 5.0)
    def test_notify_waits_while_the_session_is_busy_then_adds_the_turn(self):
        r = self.notify(FAKE_CONTINUE="busy-once")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(r.stdout.startswith("Added to session s-old1"))
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue(all("--resume" in c["argv"] for c in self.calls()))

    @mock.patch("aos_session.cli.BUSY_RETRY", 0.01)
    @mock.patch("aos_session.cli.BUSY_WAIT", 0.1)
    def test_notify_still_busy_after_the_wait_exits_1_and_opens_nothing(self):
        r = self.notify(FAKE_CONTINUE="busy")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("[CRON_FAILURE]"), r.stdout)
        self.assertIn("still busy", r.stdout)
        self.assertTrue(all("--resume" in c["argv"] for c in self.calls()))

    def test_notify_other_failure_exits_1_and_opens_no_stray_session(self):
        r = self.notify(FAKE_CONTINUE="fail")
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stdout.startswith("[CRON_FAILURE]"))
        self.assertIn("upstream API error", r.stdout)
        self.assertEqual(len(self.calls()), 1)

    # -- refusals ----------------------------------------------------------
    def test_unsupported_session_row_exits_4_before_any_call(self):
        self.sheet.write_text("---\nharness: fake\nmapping:\n  session: {support: none, "
                              "instead: no sessions}\n---\n")
        self.assertEqual(self.open().returncode, 4)
        self.assertEqual(self.calls(), [])

    def test_unsupported_step_exits_4(self):
        self.sheet.write_text(SHEET.replace(
            "    open: fakeharness -p <profile> <skills> chat --in <workdir> -c <title> -Q "
            "--query-file <file>", "    open: {support: none, instead: not titled}"))
        self.assertEqual(self.open().returncode, 4)
        self.assertEqual(self.calls(), [])

    def test_no_harness_record_exits_2(self):
        (self.home / ".aos" / "harness.yml").unlink()
        r = self.open()
        self.assertEqual(r.returncode, 2)
        self.assertIn("aos-cap harness set", r.stderr)

    def test_a_profile_or_session_shaped_like_a_flag_exits_2(self):
        r = self.cli_run("notify", "--profile", "default", "--session", "--help",
                     "--prompt-file", str(self.prompt), "--title", "t")
        self.assertEqual(r.returncode, 2)
        r = self.cli_run("open", "--profile", "-x", "--title", "t", "--prompt-file", str(self.prompt))
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_unknown_placeholder_in_the_sheet_exits_2(self):
        self.sheet.write_text(SHEET.replace("-Q --query-file <file>\n    skill_arg",
                                            "-Q --query-file <prompt>\n    skill_arg"))
        self.assertEqual(self.open().returncode, 2)

    def test_the_recorded_cli_runs_with_an_empty_path(self):
        r = self.open(PATH="")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_scrub_env_from_the_sheet_keeps_a_variable_out_of_the_child(self):
        self.assertEqual(self.open(FAKE_SECRET_TOKEN="x").returncode, 0)
        self.assertIsNone(self.calls()[0]["secret"])

    # -- contract ----------------------------------------------------------
    def test_session_keys_agree_with_the_kit_vocabulary(self):
        from aos_cap.constants import SESSION_KEYS as KIT
        self.assertEqual(tuple(SESSION_KEYS), tuple(KIT))

    def test_version_tracks_the_capability(self):
        declared = re.search(r"^version: (\S+)$",
                             (REPO / "capabilities/session/CAPABILITY.md").read_text(), re.M).group(1)
        r = self.cli_run("--version")
        self.assertIn(f"aos-session {declared}", r.stdout)
        self.assertIn(f'version = "{declared}"', (TOOL_DIR / "pyproject.toml").read_text())


class InstalledScriptTest(unittest.TestCase):
    """The one thing CliRunner cannot prove: that `[project.scripts]` resolves."""

    def test_the_installed_script_runs_and_reports_its_version(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home}
            r = subprocess.run(["uv", "run", "--quiet", "--project", str(TOOL_DIR),
                                "aos-session", "--version"], capture_output=True, text=True,
                               env=env, timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"^aos-session \d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
