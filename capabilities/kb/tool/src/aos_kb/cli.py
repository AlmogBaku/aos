"""kb — the kb capability's deterministic executor.

Deterministic operations ONLY: this tool never calls an LLM and never invokes an
agent. Skills call it; it answers in exit codes, stdout, and files — files are the
async message bus (a sync conflict becomes a .kb/pending/ entry, not a
callback). Every write verb makes its own commit: author = the human principal whose
knowledge it is, committer = the acting agent, with aos-verb/aos-path trailers. Git is
the single audit substrate — there is no log.md.

Every shared record is one file per record (captures, pending entries, per-principal
state). That is what keeps a base conflict-free when several machines — or
several people — sync it; nothing here relies on a merge driver.

Reports (lint, adopt) are report-only and written for an LLM to judge: the report is
the interface. Search/links exit codes carry no information beyond "ran".

Layout guard: every base-scoped verb validates .kb/base.yml `layout` and fails loudly
on mismatch — never path-guesses across format generations. A layout 1 tree (root
BASE.yaml) is recognised only to point at `kb migrate`.

Spec: design/kb-methodology.md (spec branch). Contract = verb set + boundary; the
implementation language is a build choice.
"""

import argparse

from .constants import VERSION, LAYOUT, PENDING_KINDS, WAITS_ON
from .query import add_query_args
from .commands.lifecycle import cmd_init, cmd_adopt, cmd_migrate
from .commands.capture import cmd_capture, cmd_find, cmd_ingest, cmd_pending, cmd_inbox
from .commands.wiki import (
    cmd_search, cmd_links, cmd_index, cmd_set, cmd_prune, cmd_archive, cmd_verify,
    cmd_state,
)
from .commands.lint import cmd_lint
from .commands.sync import cmd_sync
from .commands.admin import cmd_grants, cmd_config, cmd_refuse, cmd_commit, cmd_history
from .commands.survey import cmd_import_survey


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        prog="kb",
        description="Deterministic executor for kb bases. Judgment-free: skills "
                    "decide, this tool does. See `--help` per verb.")
    ap.add_argument("--version", action="version", version=f"kb {VERSION} "
                    f"(layout {LAYOUT})")
    ap.add_argument("--base", help="base name (registry) or path; default: cwd/"
                    "registry default")
    ap.add_argument("--registry", help="kb-registry.yaml path (default: <home>/personal/kb-registry.yaml)")
    ap.add_argument("--agent", help="acting subject — the committer of every write "
                    "(default $AOS_AGENT or agent:main)")
    ap.add_argument("--principal", help="the human a write belongs to; becomes the "
                    "git author and the grants subject (default $AOS_PRINCIPAL_ID, "
                    "else the first matching entry in <home>/.aos/kb-principal.yml, "
                    "else the repo's git identity). The display name rides "
                    "$AOS_PRINCIPAL_NAME")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold + register a new base")
    p.add_argument("name")
    p.add_argument("--path", required=True)
    p.add_argument("--audience", choices=["private", "shared"], default="private")
    p.add_argument("--purpose", default="")
    p.add_argument("--sync", choices=["rebase-5min", "manual", "none"],
                   default="manual")
    p.add_argument("--remote")
    p.add_argument("--tag")
    p.add_argument("--default", action="store_true")
    p.add_argument("--templates")
    p.add_argument("--kb-version", default=VERSION)
    p.add_argument("--curation", choices=["self", "designated"], default="self",
                   help="self: everyone drains their own queue (default). designated: "
                        "one principal holds the wiki write grants and reads everyone's "
                        "raw material — name them with --curator")
    p.add_argument("--curator", help="principal id, iff --curation designated")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("adopt", help="register an existing tree; report divergence; "
                       "zero writes into it")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--audience", choices=["private", "shared"], default="private")
    p.add_argument("--purpose", default="")
    p.add_argument("--audit-days", type=int, default=8)
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("ingest", help="pending capture -> _raw/ (a git mv: location is "
                       "the state, and history has to follow)")
    p.add_argument("path", nargs="+")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("pending", help="the one queue: add | list | resolve")
    p.add_argument("op", choices=["add", "list", "resolve"])
    p.add_argument("path", nargs="*", help="resolve: the entries to clear")
    p.add_argument("--kind", choices=sorted(PENDING_KINDS), default="finding")
    p.add_argument("--waits-on", choices=sorted(WAITS_ON), default="human")
    p.add_argument("--title", default="pending item")
    p.add_argument("--body", help="short body inline")
    p.add_argument("--file", help="body from a file, or - for stdin")
    add_query_args(p)
    p.set_defaults(func=cmd_pending)

    p = sub.add_parser("find", help="metadata query over every page (`search` is the "
                       "full-text one — different question, both stay)")
    add_query_args(p)
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("capture", help="instant mechanical capture into .kb/pending/")
    p.add_argument("--text")
    p.add_argument("--file")
    p.add_argument("--title")
    p.add_argument("--source", help="channel provenance, e.g. whatsapp:voice")
    p.add_argument("--corrects", help="path of the item this supersedes — a link, so "
                                     "the drain never has to LLM-match free text")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("migrate", help="carry a layout 1 base to layout 2 (git mv "
                       "throughout, so history follows)")
    # Its own --base, deliberately: the global one resolves through Base(), which
    # refuses a layout 1 tree by design. Migrate is the one verb that must accept one.
    p.add_argument("--base", dest="migrate_base",
                   help="the layout 1 base to carry across (default: cwd)")
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("set", help="mutate frontmatter (one attributed commit)")
    p.add_argument("path")
    p.add_argument("assignment", nargs="+", metavar="key=value")
    p.set_defaults(func=cmd_set)

    p = sub.add_parser("prune", help="delete what `expires:` says is over (git is the "
                       "undo); _raw/ is never pruned")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_prune)

    p = sub.add_parser("archive", help="git rm + a reason — the history IS the archive")
    p.add_argument("path", nargs="+")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_archive)

    p = sub.add_parser("config", help="get/set base config; principal.* is "
                       "machine-local")
    p.add_argument("op", choices=["get", "set"])
    p.add_argument("assignment", metavar="key[=value]")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("inbox", help="the inbox is a view: this principal's pending "
                       "items (--all for everyone's)")
    p.add_argument("--failed", action="store_true")
    p.add_argument("--all", action="store_true",
                   help="include other principals' items (designated-curator and CI "
                        "path); default is yours alone")
    add_query_args(p)
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("state", help="attention-window ops (capped)")
    p.add_argument("op", choices=["add", "bump", "drop", "check", "show"])
    p.add_argument("--note")
    p.add_argument("--ref")
    p.add_argument("--review-by")
    p.add_argument("--stale-days", type=int, default=42)
    p.add_argument("--all", action="store_true",
                   help="show: the union across every principal's shard")
    add_query_args(p)
    p.set_defaults(func=cmd_state)

    p = sub.add_parser("search", help="BM25 over the base; exact/alias hits first "
                       "with a create-safety verdict")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    add_query_args(p)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("links", help="backlinks / outbound / orphans")
    p.add_argument("page", nargs="?")
    p.add_argument("--orphans", action="store_true")
    add_query_args(p)
    p.set_defaults(func=cmd_links)

    p = sub.add_parser("lint", help="the deterministic check catalog (report-only; "
                       "the report is the interface)")
    p.add_argument("--write-report", action="store_true")
    p.add_argument("--audit-days", type=int, default=8)
    p.add_argument("--stale-pending-days", type=int, default=14,
                   help="an entry waiting on a human longer than this is a finding")
    p.add_argument("--ci", action="store_true",
                   help="exit 1 on any critical — for a hook or an unattended runner "
                        "that needs a verdict rather than a report")
    p.set_defaults(func=cmd_lint)

    p = sub.add_parser("grants", help="grant lookup")
    p.add_argument("check", choices=["check"])
    p.add_argument("--subject", required=True)
    p.add_argument("--verb", required=True)
    p.add_argument("--path", required=True)
    p.set_defaults(func=cmd_grants)

    p = sub.add_parser("index", help="regenerate index.md from the tree")
    p.add_argument("rebuild", choices=["rebuild"])
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("sync", help="ff-pull then merge on divergence, push with "
                       "jittered retry; conflict -> safe abort + review entry + "
                       "exit 3; never calls an LLM")
    p.add_argument("--all", action="store_true",
                   help="every registry base with sync: rebase-5min (the rest are "
                        "reported as skipped, never silently dropped)")
    p.add_argument("--no-jitter", action="store_true",
                   help="skip the pre-fetch stagger (tests, and a one-off manual run)")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("commit", help="attribute a hand-written change (author = "
                       "principal, committer = agent, aos-verb trailer)")
    p.add_argument("--verb", required=True, help="one of the aos-verb vocabulary")
    p.add_argument("--path", required=True, action="append",
                   help="repeatable; base-relative")
    p.add_argument("--summary", required=True)
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("history", help="recent activity from git — the orientation "
                       "read, in a pinned format")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("refuse", help="record a refused write (refuse commit + "
                       "review-queue entry); payload stays with the caller")
    p.add_argument("--path", required=True)
    p.add_argument("--verb", default="write")
    p.add_argument("--subject")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_refuse)

    p = sub.add_parser("verify", help="flip a page to verified: true (user-confirmed)")
    p.add_argument("page")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("import", help="bulk import of a foreign KB (source is "
                       "READ-ONLY, always; design §6.7)")
    imp = p.add_subparsers(dest="import_cmd", required=True)
    ps = imp.add_parser("survey", help="inventory + shape detection of a source tree")
    ps.add_argument("src")
    ps.add_argument("--json", action="store_true")
    ps.set_defaults(func=cmd_import_survey)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
