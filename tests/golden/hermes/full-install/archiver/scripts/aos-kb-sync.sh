#!/usr/bin/env bash
set -euo pipefail
export AOS_REGISTRY=<HOME>/aos/tests/.sandbox/aos-home/personal/kb-registry.yaml
export AOS_AGENT=agent:archiver
exec base sync --all
