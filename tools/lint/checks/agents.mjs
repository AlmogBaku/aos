import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join, basename } from 'node:path';
import { parse } from 'yaml';
import {
  AGENT_KEYS, AGENT_REQUIRED_KEYS, MODEL_CLASSES, AGENT_TOOLS, AGENT_WORKSPACES,
} from '../../lib/constants.mjs';

export function agentFiles(cap) {
  const dir = join(cap.dir, 'agents');
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((n) => n.endsWith('.agent.yaml')).map((n) => join(dir, n));
}

export function agentNames(cap) {
  return agentFiles(cap).map((f) => {
    try {
      return parse(readFileSync(f, 'utf8'))?.name;
    } catch {
      return null;
    }
  }).filter(Boolean);
}

// ARCHITECTURE §2.3 — the neutral agent spec carries only what all first-tier
// harnesses can express. Anything else belongs in adapters/<harness>/.
export function checkAgents({ caps, report }) {
  for (const cap of caps) {
    for (const path of agentFiles(cap)) {
      const file = `${cap.rel}/agents/${basename(path)}`;
      let data;
      try {
        data = parse(readFileSync(path, 'utf8'));
      } catch (e) {
        report('error', 'agent/parse', file, e.message);
        continue;
      }
      if (data == null || typeof data !== 'object') {
        report('error', 'agent/parse', file, 'agent spec is not a YAML mapping');
        continue;
      }
      for (const key of Object.keys(data)) {
        if (!AGENT_KEYS.includes(key)) {
          report('error', 'agent/unknown-key', file, `"${key}" is not in the §2.3 neutral vocabulary (no provider names, no harness tuning)`);
        }
      }
      for (const key of AGENT_REQUIRED_KEYS) {
        if (!data[key]) report('error', 'agent/required', file, `"${key}" is required`);
      }
      if (data.name && basename(path) !== `${data.name}.agent.yaml`) {
        report('error', 'agent/name-file', file, `name "${data.name}" must match filename ${data.name}.agent.yaml`);
      }
      if (data.model_class && !MODEL_CLASSES.includes(data.model_class)) {
        report('error', 'agent/model-class', file, `model_class must be one of {${MODEL_CLASSES.join(', ')}}`);
      }
      for (const tool of data.tools ?? []) {
        if (!AGENT_TOOLS.includes(tool)) {
          report('error', 'agent/tool', file, `tool "${tool}" is not in the neutral vocabulary {${AGENT_TOOLS.join(', ')}}`);
        }
      }
      if (data.workspace && !AGENT_WORKSPACES.includes(data.workspace)) {
        report('error', 'agent/workspace', file, `workspace must be one of {${AGENT_WORKSPACES.join(', ')}}`);
      }
      for (const ref of data.context_files ?? []) {
        if (!existsSync(join(cap.dir, ref))) {
          report('error', 'agent/context-file', file, `context_files entry "${ref}" does not resolve inside the capability`);
        }
      }
    }
  }
}
