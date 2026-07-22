// The project name is a placeholder — RFC-001 picks the real one. Everything
// name-derived lives here so the rename is a one-file sweep (plus grep).
export const KIT_NAME = 'aos';
export const STATE_DIR = `.${KIT_NAME}/`; // machine-local state, gitignored (ARCHITECTURE §3.1)
export const ORIGIN_FRONTMATTER_KEY = `x-${KIT_NAME}-origin`; // install-time tag, never shipped
export const ORIGIN_JOB_PREFIX = `${KIT_NAME}:`; // jobs.json entries: origin: aos:<cap>@<ver>

// ARCHITECTURE §3.1 — the user-owned overlay family. Upstream never contains these.
export const OVERLAY_BASENAMES = ['MOD.md', 'kb-registry.yaml'];
// Fixtures simulate the user clone, so overlay paths are allowed there (RFC-002
// golden-render fixtures) — ARCHITECTURE §3.1's invariant is about *shipped* paths.
export const OVERLAY_EXEMPT_PREFIXES = ['tests/fixtures/'];

// ARCHITECTURE §5.2 — the fixed, enumerated depends.host vocabulary. Adding a
// word requires updating every cheat-sheet; the linter enforces the closed set.
export const HOST_FEATURES = [
  'scheduler',
  'messaging.inbound',
  'messaging.outbound',
  'voice.stt',
  'voice.tts',
  'calendar.read',
  'calendar.write',
  'email',
  'secrets-store',
];
export const HOST_LEVELS = ['required', 'preferred', 'optional'];

// ARCHITECTURE §2.2
export const CAPABILITY_TAGS = ['infra', 'usecase'];
export const MANIFEST_KEYS = ['id', 'version', 'tags', 'summary', 'depends', 'schedules', 'skills', 'kb'];
export const DEPENDS_KEYS = ['capabilities', 'host'];
export const SCHEDULE_KEYS = ['id', 'cron', 'agent', 'prompt_ref', 'degraded'];
export const DEGRADED_MODES = ['manual', 'skip', 'inline'];
export const SKILL_ENTRY_KEYS = ['id', 'used_by'];
export const KB_KEYS = ['writes', 'zones'];
export const KB_ZONE_KEYS = ['path', 'owner_agent'];
export const MAIN_AGENT = 'main'; // §2.2: `main` = the front agent

// ARCHITECTURE §2.3 — neutral agent spec
export const AGENT_KEYS = ['name', 'purpose', 'model_class', 'tools', 'workspace', 'context_files'];
export const AGENT_REQUIRED_KEYS = ['name', 'purpose', 'model_class'];
export const MODEL_CLASSES = ['fast', 'balanced', 'deep'];
export const AGENT_TOOLS = ['fs.read', 'fs.write', 'shell', 'web'];
export const AGENT_WORKSPACES = ['own', 'shared'];

// ONBOARDING.md question schema (type vocabulary: BUILD-GAPS G2 / ARCHITECTURE §3.1)
export const QUESTION_KEYS = ['id', 'prompt', 'type', 'required', 'secret', 're_ask'];
export const QUESTION_REQUIRED_KEYS = ['id', 'prompt', 'type'];
export const QUESTION_TYPES = ['string', 'number', 'boolean', 'enum', 'list', 'path'];

// ARCHITECTURE §5.2 — required cheat-sheet sections, verbatim.
export const CHEATSHEET_SECTIONS = [
  'Primitive mapping',
  'Materialization guide',
  'Introspection guide',
  'Secrets',
  'Removal',
  'Feature notes',
];
