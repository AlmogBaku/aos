#!/usr/bin/env bash
# aos:kb:sync -- exec job, no model wakes up. Runs kb sync --all against the household registry.
export AOS_HOME="<HOME>/aos/tests/.sandbox/aos-home"
export AOS_REGISTRY="<HOME>/aos/tests/.sandbox/aos-home/personal/kb-registry.yaml"
export AOS_AGENT="agent:archiver"
kb sync --all --registry "$AOS_REGISTRY"
