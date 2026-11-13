#!/usr/bin/env bash
# aos:kb:sync — kb@0.8.3 exec job (no model). Installed by capability-install; recorded in the aos lockfile.
export AOS_AGENT=agent:archiver
export AOS_HOME=<HOME>/aos/upstream/tests/.sandbox/aos-home
export PATH=<HOME>/aos/upstream/tests/.sandbox/uv/bin:$PATH
out=$(kb sync --all 2>&1) || { echo "kb sync needs attention:"; echo "$out"; exit 1; }
