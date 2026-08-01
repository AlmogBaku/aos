import yaml

from ..constants import (
    AGENT_KEYS, AGENT_REQUIRED_KEYS, AGENT_TOOLS, AGENT_WORKSPACES, MODEL_CLASSES,
)


def agent_files(cap) -> list:
    directory = cap.dir / "agents"
    if not directory.exists():
        return []
    return [p for p in sorted(directory.iterdir(), key=lambda p: p.name)
            if p.name.endswith(".agent.yaml")]


def agent_names(cap) -> list[str]:
    """Every declared agent's `name:`, dropping the unreadable and the unnamed.

    Deliberately NOT `aos_cap.names.declared_agent_ids`: that one falls back to the filename
    stem, because a name COMPUTATION must never raise or come back empty. Here the absence is
    the finding — `agent/required` reports the missing `name:`, and a stem substituted behind
    its back would let `schedules/agent` and `skill/used-by-ref` resolve against a name the
    installed agent will not actually have."""
    out = []
    for path in agent_files(cap):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        name = data.get("name") if isinstance(data, dict) else None
        if name:
            out.append(name)
    return out


# ARCHITECTURE §2.3 — the neutral agent spec carries only what all first-tier
# harnesses can express. Anything else belongs in adapters/<harness>/.
def check_agents(ctx) -> None:
    for cap in ctx.caps:
        for path in agent_files(cap):
            file = f"{cap.rel}/agents/{path.name}"
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                ctx.report("error", "agent/parse", file, str(e))
                continue
            if not isinstance(data, dict):
                ctx.report("error", "agent/parse", file, "agent spec is not a YAML mapping")
                continue
            for key in data:
                if key not in AGENT_KEYS:
                    ctx.report("error", "agent/unknown-key", file,
                               f'"{key}" is not in the §2.3 neutral vocabulary (no provider '
                               f"names, no harness tuning)")
            for key in AGENT_REQUIRED_KEYS:
                if not data.get(key):
                    ctx.report("error", "agent/required", file, f'"{key}" is required')
            if data.get("name") and path.name != f"{data['name']}.agent.yaml":
                ctx.report("error", "agent/name-file", file,
                           f'name "{data["name"]}" must match filename '
                           f"{data['name']}.agent.yaml")
            if data.get("model_class") and data["model_class"] not in MODEL_CLASSES:
                ctx.report("error", "agent/model-class", file,
                           f"model_class must be one of {{{', '.join(MODEL_CLASSES)}}}")
            for tool in data.get("tools") or []:
                if tool not in AGENT_TOOLS:
                    ctx.report("error", "agent/tool", file,
                               f'tool "{tool}" is not in the neutral vocabulary '
                               f"{{{', '.join(AGENT_TOOLS)}}}")
            if data.get("workspace") and data["workspace"] not in AGENT_WORKSPACES:
                ctx.report("error", "agent/workspace", file,
                           f"workspace must be one of {{{', '.join(AGENT_WORKSPACES)}}}")
            for ref in data.get("context_files") or []:
                if not (cap.dir / str(ref)).exists():
                    ctx.report("error", "agent/context-file", file,
                               f'context_files entry "{ref}" does not resolve inside the '
                               f"capability")
