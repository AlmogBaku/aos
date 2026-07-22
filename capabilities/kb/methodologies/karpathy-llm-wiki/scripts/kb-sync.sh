#!/usr/bin/env bash
# kb-sync — the 5-minute rebase-only sync loop for one KB.
# Usage: kb-sync.sh <kb-root>
# Exit codes: 0 ok · 2 commit failed · 3 pull/rebase failed (aborted clean) · 4 push failed
# Conflicts are NEVER auto-resolved: on rebase failure we abort (repo never left wedged),
# append a sync-conflict line to log.md, and exit non-zero so the scheduler surfaces it.
set -uo pipefail

KB_ROOT="${1:?usage: kb-sync.sh <kb-root>}"
cd "$KB_ROOT" || exit 1

LOG_DIR="_ops"
OK_LOG="$LOG_DIR/sync.log"
ERR_LOG="$LOG_DIR/sync-errors.log"
mkdir -p "$LOG_DIR"
TS="$(date -u +%Y-%m-%dT%H:%M+00:00)"

trim() { [ -f "$1" ] && tail -n 1000 "$1" > "$1.tmp" && mv "$1.tmp" "$1"; }

git add -A
if ! git diff --cached --quiet; then
  N="$(git diff --cached --name-only | wc -l | tr -d ' ')"
  git commit -q -m "auto-sync: $TS ($N files)" || { echo "$TS commit failed" >> "$ERR_LOG"; trim "$ERR_LOG"; exit 2; }
  echo "$TS committed $N files" >> "$OK_LOG"
fi

if git remote get-url origin > /dev/null 2>&1; then
  # Routine fetch chatter stays out of the error log — only real failures land there.
  if ! git pull --rebase --no-stat origin "$(git rev-parse --abbrev-ref HEAD)" > /dev/null 2>> "$ERR_LOG"; then
    git rebase --abort > /dev/null 2>&1
    echo "$TS | kb-sync | sync-conflict | . | rebase aborted, conflict needs human" >> log.md
    echo "$TS pull/rebase failed — aborted clean, conflict surfaced" >> "$ERR_LOG"
    trim "$ERR_LOG"
    exit 3
  fi
  git push -q origin "$(git rev-parse --abbrev-ref HEAD)" 2>> "$ERR_LOG" || { echo "$TS push failed" >> "$ERR_LOG"; trim "$ERR_LOG"; exit 4; }
fi

trim "$OK_LOG"
exit 0
