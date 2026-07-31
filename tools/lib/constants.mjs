// The project name is a placeholder — RFC-001 picks the real one. Everything
// name-derived lives here so the rename is a one-file sweep (plus grep).
export const KIT_NAME = 'aos';
export const STATE_DIR = `.${KIT_NAME}/`; // machine-local state, gitignored (ARCHITECTURE §3.1)
// The install-time provenance stamp, never shipped upstream. It lives inside SKILL.md's own
// `metadata` extension hatch, because that schema is EXTERNAL and we are a vendor in it —
// a top-level `x-aos-origin` was us reserving namespace in somebody else's house. `x-*` stays
// reserved in CAPABILITY.md, which is ours, for THIRD parties. Mirrored in
// aos_cap/constants.py.
export const ORIGIN_FRONTMATTER_PATH = ['metadata', KIT_NAME, 'origin'];
export const ORIGIN_FRONTMATTER_KEY = ORIGIN_FRONTMATTER_PATH.join('.'); // display form
export const LEGACY_ORIGIN_FRONTMATTER_KEY = `x-${KIT_NAME}-origin`; // retired; must not ship
export const ORIGIN_JOB_PREFIX = `${KIT_NAME}:`; // jobs.json entries: origin: aos:<cap>@<ver>

// ARCHITECTURE §3.1 — the user-owned overlay family. Upstream never contains these.
export const OVERLAY_BASENAMES = ['MOD.md', 'kb-registry.yaml'];
// Fixtures simulate the user clone and golden snapshots record the rendered user
// side, so overlay paths are allowed there (RFC-002) — ARCHITECTURE §3.1's
// invariant is about *shipped* paths.
export const OVERLAY_EXEMPT_PREFIXES = ['tests/fixtures/', 'tests/golden/'];

// ARCHITECTURE §5.2 — the fixed, enumerated depends.host vocabulary. Adding a
// word requires updating every cheat-sheet; the linter enforces the closed set.
export const HOST_FEATURES = [
  'cron',
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
export const MANIFEST_KEYS = ['id', 'version', 'tags', 'summary', 'depends', 'schedules', 'skills', 'kb', 'skill_prefix'];
export const DEPENDS_KEYS = ['capabilities', 'host'];
export const SCHEDULE_KEYS = ['id', 'cron', 'agent', 'prompt_ref', 'exec', 'degraded'];
export const DEGRADED_MODES = ['manual', 'skip', 'inline'];
export const SKILL_ENTRY_KEYS = ['id', 'used_by'];
export const KB_KEYS = ['writes', 'zones'];
export const KB_ZONE_KEYS = ['path', 'owner_agent'];
export const MAIN_AGENT = 'main'; // §2.2: `main` = the front agent

// ARCHITECTURE §2.5 — skill identity. `skill_prefix` is capability-declared (else the
// capability id); the *installed* name it produces is the shipped identity and carries the
// Agent Skills spec's limits (agentskills.io/specification, and the authoring guide's
// reserved-word rule). Mirrored in aos-cap's cli.py.
export const SKILL_PREFIX_RE = /^[a-z0-9]+(-[a-z0-9]+)*-$/;
export const SKILL_NAME_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
export const SKILL_NAME_MAX = 64;
export const RESERVED_NAME_WORDS = ['anthropic', 'claude'];
// A reference/ file past this length needs a Contents block: partial reads (head -100)
// must still reveal the full scope of what is in there.
export const REFERENCE_TOC_LINES = 100;

// §2.5 — installed names are COMPUTED, so shipped prose carries a slot, never a literal.
// Mirrored as SKILL_SLOT/AGENT_SLOT in aos_cap/slots.py; if the two disagree, the tool is
// the bug. The `(?<!\\)` guard is why an escaped example survives: capability-lifecycle
// documents the syntax it is rendered by, so lint must skip what render skips.
export const SKILL_SLOT_RE = /(?<!\\)\{\{skill:\s*([a-z0-9-]+)(?:\/([a-z0-9-]+))?\s*\}\}/g;
export const AGENT_SLOT_RE = /(?<!\\)\{\{agent:\s*([a-z0-9-]+)(?:\/([a-z0-9-]+))?\s*\}\}/g;
// Migration prose legitimately names retired skills (`capability-installer`,
// `capability-builder`) that resolve to nothing by design. A path allowlist would rot; a
// marker on the line keeps the intent local and greppable.
export const HISTORICAL_NAME_MARKER = '<!-- aos-lint-allow: historical -->';

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
