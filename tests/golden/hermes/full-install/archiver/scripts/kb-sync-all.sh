#!/usr/bin/env bash
set -euo pipefail
cd /home/anakin/aos/tests/.sandbox/aos-clone
export AOS_REGISTRY=/home/anakin/aos/tests/.sandbox/aos-clone/kb-registry.yaml
export AOS_AGENT=archiver
exec uv run /home/anakin/aos/tests/.sandbox/aos-clone/capabilities/kb/skills/kb/scripts/base.py sync --all
