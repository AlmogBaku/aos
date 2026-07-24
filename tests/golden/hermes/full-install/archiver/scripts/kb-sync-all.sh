#!/usr/bin/env bash
set -euo pipefail
cd <HOME>/aos/tests/.sandbox/aos-clone
export AOS_REGISTRY=<HOME>/aos/tests/.sandbox/aos-clone/kb-registry.yaml
export AOS_AGENT=archiver
export PATH="<HOME>/.hermes/profiles/aos-test/home/.local/bin:$PATH"
exec base --registry <HOME>/aos/tests/.sandbox/aos-clone/kb-registry.yaml sync --all
