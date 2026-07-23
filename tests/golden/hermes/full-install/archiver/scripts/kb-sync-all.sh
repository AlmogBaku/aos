#!/usr/bin/env bash
set -euo pipefail
cd /home/anakin/aos/tests/.sandbox/aos-clone
export AOS_REGISTRY=/home/anakin/aos/tests/.sandbox/aos-clone/kb-registry.yaml
export AOS_AGENT=archiver
exec base --registry /home/anakin/aos/tests/.sandbox/aos-clone/kb-registry.yaml sync --all
