---
capability: open-session
onboarded_version: 0.2.2
answers:
  open_command: |-
    <hermes venv>/bin/python <render-dir>/scripts/open_session.py --profile {profile} --title {title} --prompt-file {prompt_file} {skills} --workdir {workdir}
---

The script runs under Hermes' own interpreter — the one behind the `hermes` launcher — because it imports `hermes_state` to hide the seed.
