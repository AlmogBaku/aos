---
capability: open-session
onboarded_version: 0.1.0
answers:
  open_command: |-
    <hermes venv>/bin/python <home>/personal/capabilities/open-session/skills/open-session/scripts/open_session.py --profile {profile} --title {title} --prompt-file {prompt_file} {skills} --workdir {workdir}
---

The script runs under Hermes' own interpreter — the one behind the `hermes` launcher — because it imports `hermes_state` to hide the seed.
