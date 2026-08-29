#!/usr/bin/env python3
"""Check, repair, and synchronize the portable writing-craft skill package.

This utility uses only the Python standard library. It never downloads files,
deletes files, or reads/writes user manuscripts. --repair fills only missing
managed files. --sync explicitly refreshes managed mirrors from the canonical
.agents skill source while preserving existing platform entry files.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SKILL_NAME = "writing-craft"
ROOT_MARKER = ".writing-craft-root"
CANONICAL_RELATIVE = ".agents/skills/writing-craft"
ROOT_MIRROR_RELATIVE = "."
CLAUDE_MIRROR_RELATIVE = ".claude/skills/writing-craft"

DEFAULT_CORE_FILES = [
    "SKILL.md",
    "README.md",
    "GUIDE.md",
    "MANIFEST.json",
    "agents/openai.yaml",
    "references/fallbacks.md",
    "references/process.md",
    "references/genre-playbooks.md",
    "references/chinese-style.md",
    "references/rewrite-examples.md",
    "references/reader-momentum.md",
    "references/input-materials.md",
    "references/voice-profile.md",
    "references/material-ledger.md",
    "references/human-voice.md",
    "references/emotional-clarity.md",
    "references/emotion-atlas.md",
    "references/literary-reference.md",
    "references/review-checklist.md",
    "scripts/skill_doctor.py",
    "scripts/prose_audit.py",
    "tests/test_skill_doctor.py",
    "tests/test_package_contract.py",
    "tests/test_prose_audit.py",
]
DEFAULT_MIRROR_PATHS = [ROOT_MIRROR_RELATIVE, CLAUDE_MIRROR_RELATIVE]
DEFAULT_PLATFORM_ENTRIES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".claude/settings.json",
    ".github/copilot-instructions.md",
    ".cursor/rules/writing-craft.mdc",
]

DEFAULT_MANIFEST: Dict[str, Any] = {
    "schema_version": 1,
    "name": SKILL_NAME,
    "distribution_root_marker": ROOT_MARKER,
    "canonical_path": CANONICAL_RELATIVE,
    "core_files": DEFAULT_CORE_FILES,
    "mirror_paths": DEFAULT_MIRROR_PATHS,
    "platform_entries": DEFAULT_PLATFORM_ENTRIES,
}

ENTRY_TEMPLATES = {
    "AGENTS.md": """# writing-craft\n\nWhen the user asks to plan, draft, rewrite, polish, or review Chinese writing, read `.agents/skills/writing-craft/SKILL.md`. If that path is unavailable, read the package-root `SKILL.md`; if it is also unavailable, read `.claude/skills/writing-craft/SKILL.md`.\n\nFollow the selected entrypoint's adaptive workflow: infer or confirm the writing need and use context, give a concise writing judgment when appropriate, preserve factual boundaries and the user's voice, then use only the routed references. If files are missing, follow `references/fallbacks.md` or continue with its minimum viable workflow.\n""",
    "CLAUDE.md": """# writing-craft\n\nFor Chinese writing tasks, use `.agents/skills/writing-craft/SKILL.md` as the shared workflow. Fall back to the package-root `SKILL.md`, then `.claude/skills/writing-craft/SKILL.md` if needed.\n\nDo not assume a full interview is needed for a small edit. Use the adaptive task gate, preserve confirmed facts and the user's own voice, and follow `references/fallbacks.md` when a skill file is missing. Claude Code may invoke this skill as `/writing-craft` when the platform has loaded the registered path.\n""",
    "GEMINI.md": """# writing-craft\n\nWhen a user requests Chinese writing, editing, rewriting, planning, or critique, read `.agents/skills/writing-craft/SKILL.md`. If unavailable, use the package-root `SKILL.md`, then `.claude/skills/writing-craft/SKILL.md`.\n\nUse its adaptive intake, fact-boundary, revision-range, and fallback rules. Do not fabricate personal experiences, quotations, facts, or literary citations to make prose sound more human.\n""",
    ".claude/settings.json": """{\n  "skills": [\n    ".agents/skills/writing-craft"\n  ]\n}\n""",
    ".github/copilot-instructions.md": """# writing-craft\n\nFor Chinese writing requests, follow `.agents/skills/writing-craft/SKILL.md`. If it is missing, fall back to the package-root `SKILL.md`, then `.claude/skills/writing-craft/SKILL.md`.\n\nMatch intake depth to task size. Preserve verified facts and the user's voice. Route to references only when they change the result, and use `references/fallbacks.md` if a referenced file is unavailable.\n""",
    ".cursor/rules/writing-craft.mdc": """---\ndescription: Chinese writing workflow for planning, drafting, revision, and critique\nalwaysApply: false\n---\n\nFor Chinese writing tasks, read `.agents/skills/writing-craft/SKILL.md`. If that path is unavailable, use the package-root `SKILL.md`, then `.claude/skills/writing-craft/SKILL.md`. Follow its adaptive intake, factual-boundary, voice, revision-range, and fallback rules.\n""",
}


def is_safe_relative(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def merged_list(values: Any, fallback: Iterable[str]) -> List[str]:
    """Keep recovery-critical defaults even when a manifest is partial."""
    result = list(fallback)
    if not isinstance(values, list):
        return result
    for item in values:
        if (is_safe_relative(item) or item == ".") and item not in result:
            result.append(item)
    return result


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".%s.writing-craft-tmp" % path.name)
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    os.replace(temporary, path)


def copy_file_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(".%s.writing-craft-tmp" % destination.name)
    shutil.copy2(source, temporary)
    os.replace(temporary, destination)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 128), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(root: Path) -> Tuple[Dict[str, Any], List[str]]:
    canonical_manifest = root / CANONICAL_RELATIVE / "MANIFEST.json"
    root_manifest = root / "MANIFEST.json"
    warnings: List[str] = []
    manifest_path = canonical_manifest if canonical_manifest.is_file() else root_manifest

    if not manifest_path.is_file():
        warnings.append("MANIFEST.json is missing; using the embedded manifest.")
        return dict(DEFAULT_MANIFEST), warnings

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        warnings.append("MANIFEST.json is unreadable (%s); using the embedded manifest." % error)
        return dict(DEFAULT_MANIFEST), warnings

    if not isinstance(payload, dict) or payload.get("name") != SKILL_NAME:
        warnings.append("MANIFEST.json is invalid; using the embedded manifest.")
        return dict(DEFAULT_MANIFEST), warnings

    manifest = dict(DEFAULT_MANIFEST)
    manifest.update(payload)
    manifest["core_files"] = merged_list(payload.get("core_files"), DEFAULT_CORE_FILES)
    manifest["mirror_paths"] = merged_list(payload.get("mirror_paths"), DEFAULT_MIRROR_PATHS)
    manifest["platform_entries"] = merged_list(
        payload.get("platform_entries"), DEFAULT_PLATFORM_ENTRIES
    )
    if manifest.get("canonical_path") != CANONICAL_RELATIVE:
        warnings.append("MANIFEST.json changed canonical_path; using the fixed .agents source.")
        manifest["canonical_path"] = CANONICAL_RELATIVE
    return manifest, warnings


def discover_root(script_path: Path, requested_root: Optional[str]) -> Tuple[Path, bool]:
    if requested_root:
        root = Path(requested_root).expanduser().resolve()
        return root, looks_like_distribution_root(root)

    start = script_path.resolve().parent.parent
    mirrored_root = root_from_mirror(start)
    if mirrored_root is not None:
        return mirrored_root, True
    for candidate in [start, *start.parents]:
        if (candidate / ROOT_MARKER).is_file():
            return candidate, True
    for candidate in [start, *start.parents]:
        if looks_like_distribution_root(candidate):
            return candidate, True
    return start, False


def root_from_mirror(candidate: Path) -> Optional[Path]:
    """Recognize a script executed inside .agents or .claude after root loss."""
    parent = candidate.parent
    grandparent = parent.parent
    if candidate.name != SKILL_NAME or parent.name != "skills":
        return None
    if grandparent.name not in {".agents", ".claude"}:
        return None
    distribution_root = grandparent.parent
    return distribution_root if looks_like_distribution_root(distribution_root) else None


def looks_like_distribution_root(candidate: Path) -> bool:
    if candidate.name == SKILL_NAME and candidate.parent.name == "skills" and candidate.parent.parent.name in {".agents", ".claude"}:
        return False
    root_manifest = (candidate / "MANIFEST.json").is_file()
    root_payload = (candidate / "SKILL.md").is_file() and (
        candidate / "scripts" / "skill_doctor.py"
    ).is_file()
    canonical_manifest = (candidate / CANONICAL_RELATIVE / "MANIFEST.json").is_file()
    canonical_payload = (candidate / CANONICAL_RELATIVE / "SKILL.md").is_file() and (
        candidate / CANONICAL_RELATIVE / "scripts" / "skill_doctor.py"
    ).is_file()
    claude_payload = (candidate / CLAUDE_MIRROR_RELATIVE / "SKILL.md").is_file() and (
        candidate / CLAUDE_MIRROR_RELATIVE / "scripts" / "skill_doctor.py"
    ).is_file()
    platform_signal = any(
        (
            (candidate / "AGENTS.md").is_file(),
            (candidate / "CLAUDE.md").is_file(),
            (candidate / "GEMINI.md").is_file(),
            (candidate / ".claude" / "settings.json").is_file(),
            (candidate / ".github" / "copilot-instructions.md").is_file(),
            (candidate / ".cursor" / "rules" / "writing-craft.mdc").is_file(),
        )
    )
    has_mirror_signal = canonical_manifest or canonical_payload or claude_payload
    return (candidate / ROOT_MARKER).is_file() or (
        root_manifest and (platform_signal or has_mirror_signal)
    ) or (root_payload and (platform_signal or has_mirror_signal)) or (
        platform_signal and has_mirror_signal
    )


def canonical_root(root: Path, manifest: Dict[str, Any], full_distribution: bool) -> Path:
    if full_distribution:
        return root / manifest["canonical_path"]
    return root


def all_managed_locations(root: Path, manifest: Dict[str, Any], full_distribution: bool) -> List[Path]:
    if not full_distribution:
        return [root]

    locations = [canonical_root(root, manifest, True)]
    for relative in manifest["mirror_paths"]:
        location = root if relative == "." else root / relative
        if location not in locations:
            locations.append(location)
    return locations


def candidate_sources(root: Path, manifest: Dict[str, Any], full_distribution: bool) -> List[Path]:
    locations = all_managed_locations(root, manifest, full_distribution)
    preferred = canonical_root(root, manifest, full_distribution)
    return [preferred] + [location for location in locations if location != preferred]


def existing_source(relative: str, candidates: Iterable[Path], destination: Path) -> Optional[Path]:
    for candidate in candidates:
        source = candidate / relative
        if source != destination and source.is_file():
            return source
    return None


def manifest_text() -> str:
    return json.dumps(DEFAULT_MANIFEST, ensure_ascii=False, indent=2) + "\n"


def status_for(root: Path, manifest: Dict[str, Any], full_distribution: bool) -> Dict[str, Any]:
    canonical = canonical_root(root, manifest, full_distribution)
    core_files = manifest["core_files"]
    canonical_missing = [relative for relative in core_files if not (canonical / relative).is_file()]
    mirror_missing: Dict[str, List[str]] = {}
    mirror_drift: Dict[str, List[str]] = {}

    if full_distribution:
        for relative_root in manifest["mirror_paths"]:
            mirror = root if relative_root == "." else root / relative_root
            label = relative_root
            missing = [relative for relative in core_files if not (mirror / relative).is_file()]
            if missing:
                mirror_missing[label] = missing
            drift = [
                relative
                for relative in core_files
                if (canonical / relative).is_file()
                and (mirror / relative).is_file()
                and file_hash(canonical / relative) != file_hash(mirror / relative)
            ]
            if drift:
                mirror_drift[label] = drift

    entry_missing = []
    marker_missing = False
    if full_distribution:
        entry_missing = [
            relative for relative in manifest["platform_entries"] if not (root / relative).is_file()
        ]
        marker_missing = not (root / ROOT_MARKER).is_file()
    healthy = not any((canonical_missing, mirror_missing, mirror_drift, entry_missing, marker_missing))
    return {
        "root": str(root),
        "canonical": str(canonical),
        "full_distribution": full_distribution,
        "healthy": healthy,
        "canonical_missing": canonical_missing,
        "mirror_missing": mirror_missing,
        "mirror_drift": mirror_drift,
        "entry_missing": entry_missing,
        "marker_missing": marker_missing,
    }


def repair_canonical(
    root: Path,
    manifest: Dict[str, Any],
    full_distribution: bool,
    changes: List[str],
) -> List[str]:
    canonical = canonical_root(root, manifest, full_distribution)
    if not full_distribution:
        return [relative for relative in manifest["core_files"] if not (canonical / relative).is_file()]

    candidates = candidate_sources(root, manifest, full_distribution)
    unrecoverable: List[str] = []
    for relative in manifest["core_files"]:
        destination = canonical / relative
        if destination.is_file():
            continue
        source = existing_source(relative, candidates, destination)
        if source is not None:
            copy_file_atomic(source, destination)
            changes.append("restored canonical %s" % relative)
            continue
        if relative == "MANIFEST.json":
            write_text_atomic(destination, manifest_text())
            changes.append("created canonical MANIFEST.json from embedded defaults")
            continue
        if source is None:
            unrecoverable.append(relative)
            continue
    return unrecoverable


def update_mirrors(
    root: Path, manifest: Dict[str, Any], mode: str, changes: List[str]
) -> None:
    canonical = canonical_root(root, manifest, True)
    for mirror_relative in manifest["mirror_paths"]:
        mirror = root if mirror_relative == "." else root / mirror_relative
        for relative in manifest["core_files"]:
            source = canonical / relative
            destination = mirror / relative
            if not source.is_file():
                continue
            if mode == "sync" or not destination.is_file():
                copy_file_atomic(source, destination)
                verb = "synchronized" if mode == "sync" else "restored"
                changes.append("%s %s/%s" % (verb, mirror_relative, relative))


def update_entries(root: Path, manifest: Dict[str, Any], changes: List[str]) -> None:
    for relative in manifest["platform_entries"]:
        content = ENTRY_TEMPLATES.get(relative)
        destination = root / relative
        if content is not None and not destination.is_file():
            write_text_atomic(destination, content)
            changes.append("created platform entry %s" % relative)


def ensure_root_marker(root: Path, changes: List[str]) -> None:
    marker = root / ROOT_MARKER
    if not marker.is_file():
        write_text_atomic(marker, "writing-craft distribution root\n")
        changes.append("created %s" % ROOT_MARKER)


def mutate(
    root: Path, manifest: Dict[str, Any], full_distribution: bool, mode: str
) -> Dict[str, Any]:
    changes: List[str] = []
    if not full_distribution:
        status = status_for(root, manifest, False)
        status.update(
            {
                "action": mode,
                "changes": changes,
                "unrecoverable": status["canonical_missing"],
                "note": "Standalone copy detected. No sibling mirrors were found, so no repair was attempted.",
            }
        )
        return status

    ensure_root_marker(root, changes)
    canonical = canonical_root(root, manifest, True)
    canonical.mkdir(parents=True, exist_ok=True)
    unrecoverable = repair_canonical(root, manifest, True, changes)
    if not unrecoverable and all((canonical / item).is_file() for item in manifest["core_files"]):
        update_mirrors(root, manifest, mode, changes)
        update_entries(root, manifest, changes)
    else:
        changes.append("did not update mirrors because canonical files are still missing")

    status = status_for(root, manifest, True)
    status.update({"action": mode, "changes": changes, "unrecoverable": unrecoverable})
    return status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true", help="Report missing or drifted managed files.")
    actions.add_argument("--repair", action="store_true", help="Restore missing files without overwriting drift.")
    actions.add_argument("--sync", action="store_true", help="Refresh mirrors from the canonical .agents source.")
    parser.add_argument("--root", help="Distribution root. Defaults to this script's package root.")
    parser.add_argument(
        "--rebuild-distribution",
        action="store_true",
        help="Explicitly rebuild a full cross-platform layout from a root copy after all layout signals are lost.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.rebuild_distribution and not args.root:
        raise SystemExit("--rebuild-distribution requires --root to avoid modifying a standalone skill install.")
    mode = "sync" if args.sync else "repair" if args.repair else "check"
    root, detected_distribution = discover_root(Path(__file__), args.root)
    full_distribution = detected_distribution or args.rebuild_distribution
    manifest, warnings = load_manifest(root)

    if mode == "check":
        result = status_for(root, manifest, full_distribution)
        result.update(
            {
                "action": mode,
                "changes": [],
                "rebuild_distribution": args.rebuild_distribution,
                "warnings": warnings,
            }
        )
    else:
        result = mutate(root, manifest, full_distribution, mode)
        result["rebuild_distribution"] = args.rebuild_distribution
        result["warnings"] = warnings

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
