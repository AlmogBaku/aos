import re

# Backstop only — the real defense is the extraction redaction checklist.
# Fixture fakes must use FAKE-… shapes, which are exempt by construction.
PATTERNS = [
    ("secrets/token",
     re.compile(r"\b(sk|xox[bapsr]|ghp|gho|glpat|AKIA)[-_][A-Za-z0-9_-]{16,}\b"),
     "API-token-shaped string"),
    ("secrets/jwt",
     re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b"),
     "JWT-shaped string"),
    ("secrets/private-key",
     re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
     "private key block"),
    ("secrets/phone",
     re.compile(r"(?<!\+0{3})\+[1-9]\d{9,14}\b"),
     "phone-number-shaped string (use +000000000000)"),
    ("secrets/whatsapp-jid",
     re.compile(r"\b\d{10,15}@s\.whatsapp\.net\b"),
     "WhatsApp JID"),
]

TEXT_EXT = re.compile(r"\.(md|ya?ml|json|mjs|js|py|sh|txt|tmpl)$")
_EXEMPT = re.compile(r"FAKE|EXAMPLE|PLACEHOLDER|xxx", re.I)


def check_secrets(ctx) -> None:
    for rel in ctx.files:
        if not TEXT_EXT.search(rel):
            continue
        text = (ctx.root / rel).read_text(encoding="utf-8")
        for code, pattern, what in PATTERNS:
            for m in pattern.finditer(text):
                if _EXEMPT.search(m.group(0)):
                    continue
                ctx.report("error", code, rel,
                           f'{what}: "{m.group(0)[:12]}…" — this repo is public; redact '
                           f"(CLAUDE.md self-containment)")
