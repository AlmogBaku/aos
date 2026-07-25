#!/usr/bin/env bash
set -euo pipefail

# Registry entries may contain ~/ paths; keep their expansion anchored to the OS user,
# not Hermes's sandboxed process home.
export HOME="<HOME>"
export AOS_REGISTRY="<HOME>/aos/tests/.sandbox/aos-home/personal/kb-registry.yaml"
export AOS_AGENT="agent:archiver"
exec "<HOME>/aos/tests/.sandbox/aos-home/.local/share/uv/tools/aos-base/bin/base" sync --all
