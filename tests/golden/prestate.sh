#!/usr/bin/env bash
# Snapshot the parts of ~/.hermes an aos install must NOT touch (canaries).
# Usage: prestate.sh <out-file>
set -euo pipefail
OUT="${1:?usage: prestate.sh <out-file>}"
H="$HOME/.hermes"
{
  echo "config_sha256=$(sha256sum "$H/config.yaml" | cut -d' ' -f1)"
  echo "profiles=$(ls "$H/profiles" | grep -v '^aos-' | sort | tr '\n' ',')"
  echo "root_skills=$(ls "$H/skills" | sort | sha256sum | cut -d' ' -f1)"
  echo "root_job_ids=$(python3 -c "import json;print(','.join(sorted(j['id'] for j in json.load(open('$H/cron/jobs.json'))['jobs'])))" 2>/dev/null || echo none)"
} > "$OUT"
echo "prestate written to $OUT"
