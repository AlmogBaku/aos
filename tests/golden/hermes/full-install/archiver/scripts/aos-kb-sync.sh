#!/usr/bin/env bash
# aos:kb:sync — exec job, no model. Installed by aos kb@0.8.0.
export AOS_AGENT=agent:archiver
export AOS_HOME=<HOME>/aos/upstream/tests/.sandbox/aos-home
exec <HOME>/.local/share/uv/tools/aos-kb/bin/kb sync --all
