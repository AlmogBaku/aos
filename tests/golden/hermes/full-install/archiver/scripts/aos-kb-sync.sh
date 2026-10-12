#!/usr/bin/env bash
# aos:kb:sync — exec job, no model wakes up (kb@0.8.0)
export AOS_HOME=<HOME>/aos/upstream/tests/.sandbox/aos-home
export AOS_AGENT=agent:archiver
export PATH=<HOME>/aos/upstream/tests/.sandbox/uv/bin:$PATH
exec kb sync --all
