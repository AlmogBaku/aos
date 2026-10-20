#!/usr/bin/env bash
# aos:kb:sync — exec job, no model. Installed by aos kb@0.8.1.
export AOS_HOME=<HOME>/aos/upstream/tests/.sandbox/aos-home
export AOS_AGENT=agent:archiver
exec <HOME>/aos/upstream/tests/.sandbox/uv/bin/kb sync --all
