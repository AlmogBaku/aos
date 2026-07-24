#!/usr/bin/env bash
set -euo pipefail
exec base --registry <HOME>/aos/tests/.sandbox/aos-clone/kb-registry.yaml sync --all
