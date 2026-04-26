#!/usr/bin/env python3
"""Validate helper docs used to navigate ROM work."""

from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CORE_HELPER_DOCS = (
    "docs/README.md",
    "docs/codex_context.md",
    "docs/project_map.md",
    "docs/project_roadmap.md",
    "docs/codex_review_playbook.md",
    "docs/boss_ai_spec.md",
    "docs/qol_handoff.md",
    "docs/balance_intent.md",
    "docs/evolution_policy.md",
    "docs/buff_backlog.md",
    "docs/generated/dev_index.md",
    "docs/generated/balance_audit.md",
)

REQUIRED_AGENT_NAVIGATION_DOCS = (
    "docs/agent_navigation/README.md",
    "docs/agent_navigation/start_card.md",
    "docs/agent_navigation/doc_roles.md",
    "docs/agent_navigation/navigation_health_check.md",
    "docs/agent_navigation/task_router.md",
    "docs/agent_navigation/source_output_ownership.md",
    "docs/agent_navigation/verification_matrix.md",
    "docs/agent_navigation/artifact_catalog.md",
    "docs/agent_navigation/custom_terms.md",
    "docs/agent_navigation/subsystems/boss_ai_trace.md",
    "docs/agent_navigation/subsystems/trainer_boss_roster.md",
    "docs/agent_navigation/subsystems/pokemon_balance.md",
    "docs/agent_navigation/subsystems/qol_map_scripts.md",
    "docs/agent_navigation/subsystems/checkpoint_handoff.md",
)


def discover_agent_navigation_docs() -> tuple[str, ...]:
    nav_root = ROOT / "docs" / "agent_navigation"
    if not nav_root.exists():
        return ()
    return tuple(
        sorted(path.relative_to(ROOT).as_posix() for path in nav_root.rglob("*.md"))
    )


HELPER_DOCS = (
    *CORE_HELPER_DOCS,
    *tuple(sorted(set(REQUIRED_AGENT_NAVIGATION_DOCS) | set(discover_agent_navigation_docs()))),
)

REQUIRED_PATHS = (
    *HELPER_DOCS,
    "docs/boss_ai_spec.md",
    "docs/mechanics_changes_from_base.md",
    "docs/balance_intent.md",
    "docs/evolution_policy.md",
    "docs/buff_backlog.md",
    "docs/generated/balance_audit.md",
    "docs/manifest.md",
    "docs/RELEASE_NOTES.md",
    "docs/build.md",
    "audit/boss_ai_trace/live_capture_ledger.md",
    "audit/boss_ai_trace/live_capture_manifest.json",
    "scripts/generate_dev_index.py",
    "scripts/generate_balance_audit.py",
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
    "data/default_options.asm",
    "engine/overworld",
    "engine/events/move_reminder.asm",
    "engine/items/pack.asm",
    "maps/GoldenrodBikeShop.asm",
    "ram/wram.asm",
    "ram/sram.asm",
    "ram/hram.asm",
    "layout.link",
    "pokegold.map",
    "pokegold.sym",
)

OBJECTIVE_PHRASES = (
    "First-Playthrough Promise",
    "The goal is restored uncertainty",
    "being small in Johto again",
    "without cheating",
    "Fairness is non-negotiable",
    "Quality-of-life changes support the main game",
    "Weak Pokemon should become usable",
    "Audience: future Codex/helper agents, not human readers",
    "Human readability is secondary to machine-searchable facts and auditability",
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

OPTIONAL_LOCAL_PATH_PREFIXES = (
    ".local",
    "dist",
    "outbox",
    "workspace",
)

PLANNED_MISSING_ARTIFACTS = (
    "audit/boss_ai_trace/morty_live.txt",
    "audit/boss_ai_trace/jasmine_live.txt",
    "audit/boss_ai_trace/clair_live.txt",
    "audit/boss_ai_trace/koga_live.txt",
    "audit/boss_ai_trace/champion_lance_live.txt",
    "audit/boss_ai_trace/shared_switch_loop_live.txt",
)

AGENT_NAVIGATION_CONTRACT_SNIPPETS = {
    "docs/agent_navigation/start_card.md": (
        "## First Thirty Seconds",
        "## Pick A Lane",
        "## Minimum Safe Stop",
        "docs/agent_navigation/navigation_health_check.md",
        "python tools\\audit\\check_docs_navigation.py",
    ),
    "docs/agent_navigation/README.md": (
        "## Complexity Budget",
        "## Navigation Contract",
        "## Subsystem Micro-Indexes",
        "docs/agent_navigation/start_card.md",
        "docs/agent_navigation/navigation_health_check.md",
    ),
    "docs/agent_navigation/doc_roles.md": (
        "## Role Matrix",
        "## Where To Put New Information",
        "## Duplication Rule",
        "docs/project_roadmap.md",
        "docs/generated/dev_index.md",
    ),
    "docs/agent_navigation/navigation_health_check.md": (
        "## Acceptance Criteria",
        "## Expansion Rules",
        "## Pruning Rules",
        "## Smoke Route Table",
        "continue making it beautiful",
        "is Morty boss AI proven?",
        "what owns pokegold.sym?",
        "without broad source search",
    ),
    "docs/project_roadmap.md": (
        "| NAV-001 | `REFERENCE` | Agent navigation beauty pass | `COMPLETE` |",
        "Follow-up simplification folded the fresh-session dry run into `docs/agent_navigation/navigation_health_check.md`",
        "merged path classification into `docs/agent_navigation/source_output_ownership.md`",
        "`tools/audit/check_docs_navigation.py` now auto-discovers `docs/agent_navigation/**/*.md`",
    ),
}


def normalize_lines(text: str) -> str:
    return "\n".join(text.splitlines()) + "\n"


def normalize_dev_index(text: str) -> str:
    text = normalize_lines(text)
    return re.sub(r"^Generated: .*$", "Generated: <date>", text, flags=re.MULTILINE)


def normalize_balance_audit(text: str) -> str:
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


def is_optional_local_path_ref(ref: str) -> bool:
    return ref in OPTIONAL_LOCAL_PATH_PREFIXES or ref.startswith(
        tuple(prefix + "/" for prefix in OPTIONAL_LOCAL_PATH_PREFIXES)
    )


def is_planned_missing_artifact_ref(ref: str) -> bool:
    return ref in PLANNED_MISSING_ARTIFACTS


def read_repo_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def section(text: str, start_marker: str, end_marker: str | None = None) -> str | None:
    start = text.find(start_marker)
    if start == -1:
        return None
    if end_marker is None:
        return text[start:]
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        return None
    return text[start:end]


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
            if is_optional_local_path_ref(ref):
                continue
            if is_planned_missing_artifact_ref(ref):
                continue
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


def check_helper_entrypoint(errors: list[str]) -> None:
    readme_path = ROOT / "docs/README.md"
    if not readme_path.exists():
        errors.append("missing docs/README.md helper-doc entrypoint")
        return

    text = readme_path.read_text(encoding="utf-8")
    required = (
        "READ THIS FIRST",
        "Audience: future Codex/helper agents, not human readers",
        "## Required Read Order",
        "## Truth Precedence",
        "## Task Routing",
        "python tools\\audit\\check_docs_navigation.py",
    )
    missing = [phrase for phrase in required if phrase not in text]
    for phrase in missing:
        errors.append(f"docs/README.md missing helper-entrypoint phrase: {phrase!r}")
    if not missing:
        print("PASS: helper-doc entrypoint is present")


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


def check_generated_balance_audit(errors: list[str]) -> None:
    committed_path = ROOT / "docs/generated/balance_audit.md"
    generator = ROOT / "scripts/generate_balance_audit.py"
    if not committed_path.exists() or not generator.exists():
        errors.append("cannot check generated balance audit freshness; audit or generator is missing")
        return

    tmp_root = ROOT / ".local" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
        out_path = Path(tmp) / "balance_audit.md"
        proc = subprocess.run(
            [
                sys.executable,
                str(generator),
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
                "failed to regenerate docs/generated/balance_audit.md for comparison: "
                + (proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}")
            )
            return

        committed = normalize_balance_audit(committed_path.read_text(encoding="utf-8"))
        regenerated = normalize_balance_audit(out_path.read_text(encoding="utf-8"))
        if committed != regenerated:
            diff = list(
                difflib.unified_diff(
                    committed.splitlines(),
                    regenerated.splitlines(),
                    fromfile="docs/generated/balance_audit.md",
                    tofile="regenerated balance_audit.md",
                    lineterm="",
                )
            )
            preview = "\n".join(diff[:40])
            errors.append(
                "docs/generated/balance_audit.md is stale relative to current Pokemon data"
                + (f"\n{preview}" if preview else "")
            )
            return

    print("PASS: generated balance audit matches current Pokemon data")


def check_python_command_paths(errors: list[str]) -> None:
    missing: list[tuple[str, str]] = []
    command_re = re.compile(r"\bpython(?:3)?\s+([A-Za-z0-9_./\\-]+\.py)\b")
    for helper in HELPER_DOCS:
        helper_path = ROOT / helper
        if not helper_path.exists():
            continue
        text = helper_path.read_text(encoding="utf-8")
        for raw in sorted(set(command_re.findall(text))):
            ref = raw.replace("\\", "/")
            if not (ROOT / ref).exists():
                missing.append((helper, ref))

    for helper, ref in missing:
        errors.append(f"broken Python command path in {helper}: {ref}")
    if not missing:
        print("PASS: listed Python command paths resolve")


def check_boss_ai_budget_doc(errors: list[str]) -> None:
    dev_index = read_repo_text("docs/generated/dev_index.md")
    boss_spec = read_repo_text("docs/boss_ai_spec.md")

    tier_match = re.search(r"\| `wBossAITier` \| (?P<address>[0-9a-f]{2}:[0-9a-f]{4}) \|", dev_index)
    end_match = re.search(r"\| `wBossAIStateEnd` \| (?P<address>[0-9a-f]{2}:[0-9a-f]{4}) \|", dev_index)
    normal_match = re.search(r"\| Normal \| (?P<used>\d+) \| (?P<free>\d+) \|", dev_index)
    trace_match = re.search(
        r"\| With `BOSS_AI_TRACE` fields \| (?P<used>\d+) \| (?P<free>\d+) \|",
        dev_index,
    )

    missing_index_data: list[str] = []
    if tier_match is None:
        missing_index_data.append("wBossAITier address")
    if end_match is None:
        missing_index_data.append("wBossAIStateEnd address")
    if normal_match is None:
        missing_index_data.append("normal Boss AI budget")
    if trace_match is None:
        missing_index_data.append("trace Boss AI budget")
    if missing_index_data:
        errors.append("cannot validate Boss AI budget doc; missing " + ", ".join(missing_index_data))
        return

    assert tier_match is not None
    assert end_match is not None
    assert normal_match is not None
    assert trace_match is not None

    expected_snippets = (
        f"`wBossAITier = {tier_match.group('address')}`",
        f"`wBossAIStateEnd = {end_match.group('address')}`",
        f"uses `{normal_match.group('used')}` bytes and leaves `{normal_match.group('free')}`",
        f"would use `{trace_match.group('used')}` bytes and leave `{trace_match.group('free')}`",
        "`docs/generated/dev_index.md`",
    )
    missing = [snippet for snippet in expected_snippets if snippet not in boss_spec]
    for snippet in missing:
        errors.append(f"docs/boss_ai_spec.md missing current Boss AI budget fact: {snippet}")
    if not missing:
        print("PASS: Boss AI budget doc matches generated index")


def check_qol_handoff_status(errors: list[str]) -> None:
    qol_doc = read_repo_text("docs/qol_handoff.md")
    default_options = read_repo_text("data/default_options.asm")
    move_reminder = read_repo_text("engine/events/move_reminder.asm")
    bike_shop = read_repo_text("maps/GoldenrodBikeShop.asm")
    implemented = section(qol_doc, "## Already Implemented", "## Remaining Candidates")
    remaining = section(qol_doc, "## Remaining Candidates", "## Verification Checklist")
    if implemented is None or remaining is None:
        errors.append("docs/qol_handoff.md must split QoL work into Already Implemented and Remaining Candidates")
        return

    implemented_features: list[tuple[str, bool]] = [
        (
            "Default Text Speed FAST",
            "DefaultOptions:" in default_options and "db TEXT_DELAY_FAST" in default_options,
        ),
        (
            "Move Reminder Page Size",
            re.search(
                r"^DEF\s+MOVE_REMINDER_PAGE_SIZE\s+EQU\s+4\b",
                move_reminder,
                re.MULTILINE,
            )
            is not None,
        ),
        (
            "Auto-Register Bicycle If Empty",
            "callasm GoldenrodBikeShopAutoRegisterBicycle" in bike_shop
            and "GoldenrodBikeShopAutoRegisterBicycle:" in bike_shop
            and "CheckRegisteredItem" in bike_shop,
        ),
    ]
    for title, active in implemented_features:
        if not active:
            continue
        heading = f"### {title}"
        if heading not in implemented:
            errors.append(f"docs/qol_handoff.md must list active QoL feature under Already Implemented: {title}")
        if heading in remaining:
            errors.append(f"docs/qol_handoff.md still lists active QoL feature as remaining candidate: {title}")

    remaining_features = (
        "Clearer Custom Item Text",
        "Day-Care Service Signage",
        "Repel Renewal Prompt",
        "Pokemon Center Friction Trim",
    )
    for title in remaining_features:
        if f"### {title}" not in remaining:
            errors.append(f"docs/qol_handoff.md missing remaining QoL candidate: {title}")

    stale_phrases = (
        "Candidate: raise `MOVE_REMINDER_PAGE_SIZE` from `3` to `4`",
        "Change only the first `wOptions` byte from medium text delay to fast text delay",
    )
    for phrase in stale_phrases:
        if phrase in qol_doc:
            errors.append(f"docs/qol_handoff.md still contains stale future-work wording: {phrase}")

    if not any(error.startswith("docs/qol_handoff.md") for error in errors):
        print("PASS: QoL handoff current/remaining status matches source")


def check_agent_navigation_contract(errors: list[str]) -> None:
    missing: list[tuple[str, str]] = []
    for path, snippets in AGENT_NAVIGATION_CONTRACT_SNIPPETS.items():
        text = read_repo_text(path)
        for snippet in snippets:
            if snippet not in text:
                missing.append((path, snippet))

    for path, snippet in missing:
        errors.append(f"{path} missing agent-navigation contract snippet: {snippet!r}")
    if not missing:
        print("PASS: agent navigation contract is intact")


def check_trace_manifest_doc_sync(errors: list[str]) -> None:
    manifest_path = ROOT / "audit/boss_ai_trace/live_capture_manifest.json"
    roadmap = read_repo_text("docs/project_roadmap.md")
    ledger = read_repo_text("audit/boss_ai_trace/live_capture_ledger.md")
    trace_doc = read_repo_text("docs/boss_ai_trace_capture.md")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"audit/boss_ai_trace/live_capture_manifest.json invalid JSON: {exc}")
        return
    if not isinstance(manifest, dict):
        errors.append("audit/boss_ai_trace/live_capture_manifest.json root must be an object")
        return

    trace_rom = manifest.get("trace_rom")
    trace_hash = manifest.get("trace_rom_sha256")
    symbols = manifest.get("trace_symbols")
    symbols_hash = manifest.get("trace_symbols_sha256")
    missing = [
        key
        for key, value in (
            ("trace_rom", trace_rom),
            ("trace_rom_sha256", trace_hash),
            ("trace_symbols", symbols),
            ("trace_symbols_sha256", symbols_hash),
        )
        if not isinstance(value, str) or not value
    ]
    if missing:
        errors.append(
            "audit/boss_ai_trace/live_capture_manifest.json missing trace basis fields: "
            + ", ".join(missing)
        )
        return

    assert isinstance(trace_rom, str)
    assert isinstance(trace_hash, str)
    assert isinstance(symbols, str)
    assert isinstance(symbols_hash, str)

    expected_snippets = (
        ("docs/project_roadmap.md", roadmap, trace_hash),
        ("audit/boss_ai_trace/live_capture_ledger.md", ledger, "pins the current trace ROM and symbol SHA256 hashes"),
        ("audit/boss_ai_trace/live_capture_ledger.md", ledger, "`trace_rom`, `trace_rom_sha256`, `trace_symbols`, and `trace_symbols_sha256`"),
        ("docs/boss_ai_trace_capture.md", trace_doc, "The manifest pins the trace ROM and symbol file by SHA256."),
        ("docs/boss_ai_trace_capture.md", trace_doc, "Formatted live excerpts include `trace_rom`, `trace_rom_sha256`,"),
        ("docs/boss_ai_trace_capture.md", trace_doc, trace_rom),
        ("docs/boss_ai_trace_capture.md", trace_doc, symbols),
    )
    for path, text, snippet in expected_snippets:
        if snippet not in text:
            errors.append(f"{path} missing trace-manifest sync snippet: {snippet}")

    if not any("trace-manifest sync" in error or "live_capture_manifest" in error for error in errors):
        print("PASS: trace capture docs match pinned manifest basis")


def main() -> int:
    errors: list[str] = []
    check_required_paths(errors)
    check_backtick_references(errors)
    check_objective_text(errors)
    check_helper_entrypoint(errors)
    check_generated_index(errors)
    check_generated_balance_audit(errors)
    check_python_command_paths(errors)
    check_boss_ai_budget_doc(errors)
    check_qol_handoff_status(errors)
    check_agent_navigation_contract(errors)
    check_trace_manifest_doc_sync(errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("ALL DOC NAVIGATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
