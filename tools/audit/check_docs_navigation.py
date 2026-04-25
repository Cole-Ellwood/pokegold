#!/usr/bin/env python3
"""Validate helper docs used to navigate ROM work."""

from __future__ import annotations

import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

HELPER_DOCS = (
    "docs/codex_context.md",
    "docs/project_map.md",
    "docs/codex_review_playbook.md",
    "docs/generated/dev_index.md",
)

REQUIRED_PATHS = (
    *HELPER_DOCS,
    "docs/boss_ai_spec.md",
    "docs/mechanics_changes_from_base.md",
    "docs/manifest.md",
    "docs/RELEASE_NOTES.md",
    "docs/build.md",
    "scripts/generate_dev_index.py",
    "tools/audit/check_release_smoke.py",
    "tools/audit/check_ai_tiers.py",
    "tools/audit/check_boss_ai_gating.py",
    "tools/audit/check_boss_ai_no_cheat.py",
    "tools/audit/check_boss_items_present.py",
    "tools/audit/check_boss_moves_complete.py",
    "tools/audit/check_battle_math_safety.py",
    "main.asm",
    "engine/battle/ai/boss.asm",
    "engine/battle/core.asm",
    "engine/battle/effect_commands.asm",
    "engine/battle/type_passive_damage_mods.asm",
    "engine/battle/late_gen_held_items.asm",
    "engine/battle/move_effects",
    "data/moves/moves.asm",
    "data/moves/effects.asm",
    "data/moves/effects_pointers.asm",
    "data/moves/contact_flags.asm",
    "data/pokemon/base_stats.asm",
    "data/pokemon/base_stats",
    "data/pokemon/evos_attacks.asm",
    "data/trainers/parties.asm",
    "data/trainers/attributes.asm",
    "data/trainers/ai_tiers.asm",
    "maps",
    "data/maps",
    "engine/events",
    "data/events/special_pointers.asm",
    "engine/overworld",
    "ram/wram.asm",
    "ram/sram.asm",
    "ram/hram.asm",
    "layout.link",
    "pokegold.map",
    "pokegold.sym",
)

OBJECTIVE_PHRASES = (
    "fair but very hard",
    "Boss fights are the centerpiece",
    "without cheating",
    "Fairness is non-negotiable",
    "Quality-of-life changes support the main game",
    "Weak Pokemon should become usable",
)

PATH_PREFIXES = (
    ".local/",
    "audio/",
    "constants/",
    "data/",
    "dist/",
    "docs/",
    "engine/",
    "gfx/",
    "home/",
    "macros/",
    "maps/",
    "outbox/",
    "ram/",
    "rgbds-1.0.1/",
    "scripts/",
    "tools/",
    "workspace/",
)

PATHLIKE_EXTENSIONS = (
    ".asm",
    ".exe",
    ".gbc",
    ".link",
    ".map",
    ".md",
    ".o",
    ".py",
    ".sha1",
    ".sym",
    ".txt",
)


def normalize_lines(text: str) -> str:
    return "\n".join(text.splitlines()) + "\n"


def normalize_dev_index(text: str) -> str:
    text = normalize_lines(text)
    return re.sub(r"^Generated: .*$", "Generated: <date>", text, flags=re.MULTILINE)


def clean_ref(raw: str) -> str | None:
    ref = raw.strip().strip(".,;:()[]")
    ref = ref.replace("\\", "/")
    if not ref or " " in ref or "*" in ref:
        return None
    ref = re.sub(
        r"^(.+\.(?:asm|exe|link|map|md|py|sha1|sym|txt)):\d+$",
        r"\1",
        ref,
    )
    if ref.startswith(".") and "/" not in ref:
        return None
    if ref.startswith(PATH_PREFIXES):
        return ref.rstrip("/")
    if ref.endswith(PATHLIKE_EXTENSIONS):
        return ref
    return None


def backtick_path_refs(path: Path) -> set[str]:
    refs: set[str] = set()
    text = path.read_text(encoding="utf-8")
    for raw in re.findall(r"`([^`\n]+)`", text):
        ref = clean_ref(raw)
        if ref is not None:
            refs.add(ref)
    return refs


def check_required_paths(errors: list[str]) -> None:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    for path in missing:
        errors.append(f"missing required navigation path: {path}")
    if not missing:
        print("PASS: required helper docs and important paths exist")


def check_backtick_references(errors: list[str]) -> None:
    missing: list[tuple[str, str]] = []
    for helper in HELPER_DOCS:
        helper_path = ROOT / helper
        if not helper_path.exists():
            continue
        for ref in sorted(backtick_path_refs(helper_path)):
            if not (ROOT / ref).exists():
                missing.append((helper, ref))
    for helper, ref in missing:
        errors.append(f"broken helper-doc path reference in {helper}: {ref}")
    if not missing:
        print("PASS: helper-doc path references resolve")


def check_objective_text(errors: list[str]) -> None:
    context_path = ROOT / "docs/codex_context.md"
    if not context_path.exists():
        errors.append("missing docs/codex_context.md for objective validation")
        return
    context = context_path.read_text(encoding="utf-8")
    missing = [phrase for phrase in OBJECTIVE_PHRASES if phrase not in context]
    for phrase in missing:
        errors.append(f"missing objective phrase in docs/codex_context.md: {phrase!r}")
    if not missing:
        print("PASS: core objective phrases are present")


def check_generated_index(errors: list[str]) -> None:
    committed_path = ROOT / "docs/generated/dev_index.md"
    generator = ROOT / "scripts/generate_dev_index.py"
    if not committed_path.exists() or not generator.exists():
        errors.append("cannot check generated index freshness; index or generator is missing")
        return

    tmp_root = ROOT / ".local" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
        out_path = Path(tmp) / "dev_index.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(generator),
                "--rom",
                "pokegold",
                "--out",
                str(out_path),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            errors.append(
                "failed to regenerate docs/generated/dev_index.md for comparison: "
                + (proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}")
            )
            return

        committed = normalize_dev_index(committed_path.read_text(encoding="utf-8"))
        regenerated = normalize_dev_index(out_path.read_text(encoding="utf-8"))
        if committed != regenerated:
            diff = list(
                difflib.unified_diff(
                    committed.splitlines(),
                    regenerated.splitlines(),
                    fromfile="docs/generated/dev_index.md",
                    tofile="regenerated dev_index.md",
                    lineterm="",
                )
            )
            preview = "\n".join(diff[:40])
            errors.append(
                "docs/generated/dev_index.md is stale relative to current linker outputs"
                + (f"\n{preview}" if preview else "")
            )
            return

    print("PASS: generated dev index matches current linker outputs")


def main() -> int:
    errors: list[str] = []
    check_required_paths(errors)
    check_backtick_references(errors)
    check_objective_text(errors)
    check_generated_index(errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("ALL DOC NAVIGATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
