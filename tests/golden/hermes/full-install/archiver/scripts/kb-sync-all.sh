#!/usr/bin/env bash
set -u
status=0
for kb in personal-kb acme-kb; do
  /home/anakin/.hermes/profiles/aos-archiver/scripts/kb-sync.sh "/home/anakin/aos/tests/.sandbox/kb/$kb" || status=$?
done
exit "$status"
