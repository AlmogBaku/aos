#!/usr/bin/env python3
"""Read-only Ghostwriter backlog check. JSON stdout; no state mutation."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path

ACTIVE_PIECE_STATUSES = {"developing", "waiting", "review"}
VALID_PIECE_STATUSES = ACTIVE_PIECE_STATUSES | {
    "parked",
    "approved-manual-publish",
    "published",
    "dismissed",
}
VALID_NEXT_ACTIONS = {
    "develop",
    "critique",
    "user-decision",
    "manual-approval",
    "repurpose",
    "manual-publish",
    "none",
}
ALLOWED_ACTIONS = {
    "developing": {"develop", "critique"},
    "waiting": {"user-decision"},
    "review": {"critique", "user-decision", "manual-approval"},
    "parked": {"user-decision"},
    "approved-manual-publish": {"repurpose", "manual-publish"},
    "published": {"none"},
    "dismissed": {"none"},
}


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    block = text.split("---\n", 2)[1]
    out: dict[str, object] = {}
    for raw in block.splitlines():
        if not raw or raw[0].isspace() or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value.startswith("[") and value.endswith("]"):
            out[key.strip()] = [
                item.strip().strip('"').strip("'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            out[key.strip()] = value
    return out


def age_days(value: object) -> int | None:
    if not value:
        return None
    return (date.today() - datetime.fromisoformat(str(value)).date()).days


def contained(base: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(base.resolve(strict=False))
        return True
    except ValueError:
        return False


def ref_exists(ref: str, kb_base: Path | None, workspace: Path) -> bool:
    if ref.startswith("kb:"):
        if not kb_base:
            return False
        raw = Path(ref[3:]).expanduser()
        candidate = raw if raw.is_absolute() else kb_base / raw
        return contained(kb_base, candidate) and candidate.exists()
    raw = Path(ref).expanduser()
    candidate = raw if raw.is_absolute() else workspace / raw
    return contained(workspace, candidate) and candidate.exists()


def references(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)] if value else []


def truthy(value: object) -> bool:
    return str(value).lower() in {"true", "yes", "1"}


def validate_safety_metadata(path: Path, meta: dict, invalid: list[dict[str, str]]) -> None:
    if meta.get("status") not in {"review", "approved-manual-publish"}:
        return
    for field in ("private_sources_used", "sensitive_flags", "unsupported_claims"):
        if field not in meta or not isinstance(meta[field], list):
            invalid.append({"path": str(path), "field": field, "reason": "required list"})
    for field in ("approval_required", "private_source_clearance"):
        if field not in meta or str(meta[field]).lower() not in {"true", "false"}:
            invalid.append({"path": str(path), "field": field, "reason": "required canonical boolean"})


def evidence_entries(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    marker = "## Evidence map"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    entries: list[dict[str, str]] = []
    for block in re.split(r"(?m)^- claim_or_atom:\s*", section)[1:]:
        lines = block.splitlines()
        entry = {"claim_or_atom": lines[0].strip()}
        for line in lines[1:]:
            match = re.match(r"\s{2}(source|locator|sensitivity|confirmation):\s*(.+)\s*$", line)
            if match:
                entry[match.group(1)] = match.group(2).strip()
        entries.append(entry)
    return entries


def validate_evidence(path: Path, kb_base: Path | None, workspace: Path, invalid: list[dict[str, str]], broken: list[dict[str, str]]) -> list[dict[str, str]]:
    entries = evidence_entries(path)
    if not entries:
        invalid.append({"path": str(path), "field": "Evidence map", "reason": "missing or empty"})
        return []
    required = {"claim_or_atom", "source", "locator", "sensitivity", "confirmation"}
    for index, entry in enumerate(entries, 1):
        missing = sorted(required - entry.keys())
        if missing:
            invalid.append({"path": str(path), "field": f"Evidence map[{index}]", "reason": f"missing {', '.join(missing)}"})
            continue
        if not ref_exists(entry["source"], kb_base, workspace):
            broken.append({"artifact": str(path), "field": f"Evidence map[{index}].source", "reference": entry["source"]})
        if entry["sensitivity"] not in {"none", "review"}:
            invalid.append({"path": str(path), "field": f"Evidence map[{index}].sensitivity", "reason": "expected none or review"})
        if entry["confirmation"] not in {"supported", "needs-confirmation"}:
            invalid.append({"path": str(path), "field": f"Evidence map[{index}].confirmation", "reason": "expected supported or needs-confirmation"})
    return entries


def validate_approval(path: Path, meta: dict, entries: list[dict[str, str]], invalid: list[dict[str, str]]) -> None:
    status = str(meta.get("status") or "")
    action = str(meta.get("next_action") or "")
    if not (status == "approved-manual-publish" or (status == "review" and action == "manual-approval")):
        return
    blockers: list[str] = []
    if references(meta.get("unsupported_claims")):
        blockers.append("unsupported_claims")
    if truthy(meta.get("approval_required")):
        blockers.append("approval_required")
    if references(meta.get("sensitive_flags")):
        blockers.append("sensitive_flags")
    if references(meta.get("private_sources_used")) and not truthy(meta.get("private_source_clearance")):
        blockers.append("uncleared_private_sources")
    if any(entry.get("sensitivity") == "review" for entry in entries):
        blockers.append("Evidence map sensitivity review")
    if any(entry.get("confirmation") != "supported" for entry in entries):
        blockers.append("Evidence map needs confirmation")
    if blockers:
        invalid.append({"path": str(path), "field": "approval", "reason": "blockers: " + ", ".join(blockers)})


def validate_references(path: Path, meta: dict, kb_base: Path | None, workspace: Path, invalid: list[dict[str, str]], broken: list[dict[str, str]]) -> None:
    interview_refs = references(meta.get("related_interviews"))
    for field, refs in (("related_interviews", interview_refs), ("related_kb_sources", references(meta.get("related_kb_sources")))):
        for ref in refs:
            if not ref_exists(ref, kb_base, workspace):
                broken.append({"artifact": str(path), "field": field, "reference": ref})


def validate_dates(path: Path, meta: dict, stale_days: int, stale: list[str], invalid: list[dict[str, str]]) -> None:
    touched = meta.get("last_touched_at") or meta.get("created_at")
    if not touched:
        invalid.append({"path": str(path), "field": "last_touched_at/created_at", "reason": "missing"})
        return
    try:
        age = age_days(touched)
    except (TypeError, ValueError):
        invalid.append({"path": str(path), "field": "last_touched_at/created_at", "reason": "invalid ISO date"})
        return
    if age is not None and age >= stale_days:
        stale.append(str(path))


def validate_parked_piece(path: Path, meta: dict, kb_base: Path | None, workspace: Path, invalid: list[dict[str, str]], broken: list[dict[str, str]]) -> None:
    if meta.get("status") == "dismissed":
        return
    if meta.get("status") != "parked" or meta.get("next_action") != "user-decision":
        invalid.append({"path": str(path), "field": "status/next_action", "reason": "archived piece must be parked/user-decision or dismissed"})
        return
    prior_status = str(meta.get("parked_from_status") or "")
    prior_action = str(meta.get("parked_from_next_action") or "")
    if prior_status not in ACTIVE_PIECE_STATUSES or prior_action not in ALLOWED_ACTIONS.get(prior_status, set()):
        invalid.append({"path": str(path), "field": "parked_from_status/parked_from_next_action", "reason": "invalid resume cursor"})
    validate_references(path, meta, kb_base, workspace, invalid, broken)
    validate_evidence(path, kb_base, workspace, invalid, broken)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--kb-base")
    parser.add_argument("--ideas-limit", type=int, default=10)
    parser.add_argument("--pieces-limit", type=int, default=2)
    parser.add_argument("--idea-stale-days", type=int, default=30)
    parser.add_argument("--piece-stale-days", type=int, default=14)
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve(strict=False)
    kb_base = Path(args.kb_base).expanduser().resolve(strict=False) if args.kb_base else None
    root_errors: list[dict[str, str]] = []
    if not root.is_dir():
        root_errors.append({"path": str(root), "field": "workspace", "reason": "missing directory"})
    if kb_base and not kb_base.is_dir():
        root_errors.append({"path": str(kb_base), "field": "kb_base", "reason": "missing directory"})
    if root_errors:
        print(json.dumps({"active_ideas": 0, "ideas_limit": args.ideas_limit, "active_pieces": 0, "pieces_limit": args.pieces_limit, "ideas_over_limit": False, "pieces_over_limit": False, "stale_ideas": [], "stale_pieces": [], "broken_interview_references": [], "invalid_metadata": root_errors}, indent=2))
        return 2
    ideas: list[str] = []
    queued_idea_ids: set[str] = set()
    idea_paths_by_id: dict[str, list[str]] = {}
    pieces: list[str] = []
    stale_ideas: list[str] = []
    stale_pieces: list[str] = []
    broken: list[dict[str, str]] = []
    invalid: list[dict[str, str]] = []

    for path in sorted((root / "ideas").glob("*.md")) if (root / "ideas").exists() else []:
        meta = frontmatter(path)
        if meta.get("status") != "queued":
            invalid.append({"path": str(path), "field": "status", "reason": "expected queued"})
            continue
        ideas.append(str(path))
        idea_id = str(meta.get("id") or "")
        if not idea_id:
            invalid.append({"path": str(path), "field": "id", "reason": "missing stable idea ID"})
        else:
            queued_idea_ids.add(idea_id)
            idea_paths_by_id.setdefault(idea_id, []).append(str(path))
        validate_dates(path, meta, args.idea_stale_days, stale_ideas, invalid)
        validate_references(path, meta, kb_base, root, invalid, broken)
        validate_evidence(path, kb_base, root, invalid, broken)

    for path in sorted((root / "archive" / "ideas").glob("*.md")) if (root / "archive" / "ideas").exists() else []:
        meta = frontmatter(path)
        if meta.get("status") == "dismissed":
            continue
        if meta.get("status") != "parked" or meta.get("next_action") != "user-decision" or meta.get("parked_from_status") != "queued":
            invalid.append({"path": str(path), "field": "status/next_action/parked_from_status", "reason": "invalid parked idea resume state"})
        idea_id = str(meta.get("id") or "")
        if not idea_id:
            invalid.append({"path": str(path), "field": "id", "reason": "missing stable idea ID"})
        else:
            idea_paths_by_id.setdefault(idea_id, []).append(str(path))
        validate_references(path, meta, kb_base, root, invalid, broken)
        validate_evidence(path, kb_base, root, invalid, broken)

    for idea_id, paths in idea_paths_by_id.items():
        if len(paths) > 1:
            for path in paths:
                invalid.append({"path": path, "field": "id", "reason": f"duplicate idea ID: {idea_id}"})

    for path in sorted((root / "pieces").glob("*/piece.md")) if (root / "pieces").exists() else []:
        meta = frontmatter(path)
        status = str(meta.get("status") or "")
        action = str(meta.get("next_action") or "")
        source_idea_id = str(meta.get("source_idea_id") or "")
        if source_idea_id and source_idea_id in queued_idea_ids:
            invalid.append({"path": str(path), "field": "source_idea_id", "reason": "source idea is still queued; finish or roll back the transfer"})
        if status not in VALID_PIECE_STATUSES:
            invalid.append({"path": str(path), "field": "status", "reason": "unknown piece status"})
        elif action not in VALID_NEXT_ACTIONS:
            invalid.append({"path": str(path), "field": "next_action", "reason": "unknown or missing next_action"})
        elif action not in ALLOWED_ACTIONS[status]:
            invalid.append({"path": str(path), "field": "next_action", "reason": f"{action} is invalid for {status}"})
        if status in ACTIVE_PIECE_STATUSES:
            pieces.append(str(path))
            validate_dates(path, meta, args.piece_stale_days, stale_pieces, invalid)
        validate_references(path, meta, kb_base, root, invalid, broken)
        entries = validate_evidence(path, kb_base, root, invalid, broken)
        validate_safety_metadata(path, meta, invalid)
        validate_approval(path, meta, entries, invalid)

    for path in sorted((root / "archive" / "pieces").glob("*/piece.md")) if (root / "archive" / "pieces").exists() else []:
        validate_parked_piece(path, frontmatter(path), kb_base, root, invalid, broken)

    print(json.dumps({
        "active_ideas": len(ideas),
        "ideas_limit": args.ideas_limit,
        "active_pieces": len(pieces),
        "pieces_limit": args.pieces_limit,
        "ideas_over_limit": len(ideas) > args.ideas_limit,
        "pieces_over_limit": len(pieces) > args.pieces_limit,
        "stale_ideas": stale_ideas,
        "stale_pieces": stale_pieces,
        "broken_interview_references": broken,
        "invalid_metadata": invalid,
    }, indent=2))
    return 2 if broken or invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
