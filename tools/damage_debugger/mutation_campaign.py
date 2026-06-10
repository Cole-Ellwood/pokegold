"""ROM-backed mutation campaign for selected damage-chain assumptions.

This is intentionally narrower than the roadmap's full mutation-campaign
requirement. It mutates a small set of known ROM-golden damage-chain bases,
runs each mutated state through the existing ROM/oracle checker, and writes a
durable proof artifact. The broad `expanded_mutation_campaigns` blocker stays
open until after-hit order, status/item interactions, damage variation, and
divergence minimization are covered at the roadmap scope.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from tools.debugger.canonical_state_class import build_canonical_state_class, stable_json_hash
from tools.debugger.report_envelope import (
    proof_dirty_diff_hash,
    proof_source_tree_hash,
    sha256_file,
)

from .boot_cache import BootStateCache
from .clobber_smoke import SCENARIOS, parse_sym, run_scenario
from .fuzz import _hash_basis_json, _shutdown_cache, check_one
from .oracle import (
    BattleInputs,
    DARK,
    DRAGON,
    EFFECT_SOLARBEAM,
    FIGHTING,
    FIRE,
    FLYING,
    GHOST,
    GRASS,
    GROUND,
    HELD_ASSAULT_VEST,
    HELD_BLACKBELT_I,
    HELD_EVOLITE,
    HELD_LIFE_ORB,
    HELD_METRONOME,
    HELD_NONE,
    HELD_WISE_GLASSES,
    ICE,
    NORMAL,
    POISON,
    ROCK,
    STEEL,
    WATER,
    WEATHER_RAIN,
    WEATHER_SUN,
)
from .paths import find_rom, find_sym
from .replay import hit_to_dict, replay_scenario
from .safe_call import call_function_safe, read_be_u16_banked, read_byte_banked, write_byte_banked


DEFAULT_TOLERANCE = 1
ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "damage_debugger_phase6_initial_mutation_campaign.passed"
RNG_DISTRIBUTION_EVIDENCE_ID = "damage_debugger_phase6_rng_distribution_mutation_campaign.passed"
SPECIES_WIDE_EVIOLITE_EVIDENCE_ID = "damage_debugger_phase6_species_wide_eviolite_fuzz.passed"
AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID = (
    "damage_debugger_auto_minimized_divergence_artifacts.passed"
)
SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID = (
    "damage_debugger_selected_status_side_effects_rom_components.passed"
)
SPECIES_WIDE_EVIOLITE_PREFIX = "species_wide_eviolite"
AUTO_MINIMIZED_DIVERGENCE_CASE_ID = "synthetic_forced_wise_glasses_status_divergence_route"
SELECTED_STATUS_SIDE_EFFECT_CASE_IDS = (
    "component_ember_burn_success",
    "component_sludge_poison_success",
    "component_body_slam_paralyze_success",
    "component_body_slam_paralyze_effectchance_fail",
    "component_full_restore_clears_burn",
    "component_full_restore_clears_paralyze",
    "component_full_restore_clears_toxic_and_poison",
    "component_full_restore_clears_sleep_and_nightmare",
    "component_full_restore_clears_confusion_only",
)
REQUIRED_CAMPAIGNS = (
    "oracle_assumptions",
    "damage_variation_and_type_matchup",
    "status_item_interactions",
    "after_hit_order",
    "recoil",
    "replay_watchpoints",
)
SMOKE_SCENARIOS = (
    ("afterhit_rocky_helmet", "after_hit_order"),
    ("afterhit_shell_bell", "after_hit_order"),
    ("afterhit_rocky_helmet_before_shell_bell", "after_hit_order"),
    ("afterhit_life_orb", "after_hit_order"),
    ("special_super_effective_variation", "damage_variation_and_type_matchup"),
    ("recoil_basic_no_steel", "recoil"),
    ("recoil_ko_clamp", "recoil"),
)
REPLAY_SPECS = (
    ("afterhit_rocky_helmet_before_shell_bell", "wBattleMonHP", 2),
    ("special_super_effective_variation", "wCurDamage", None),
    ("recoil_basic_no_steel", "wBattleMonHP", 2),
)


@dataclass(frozen=True)
class MutationCase:
    case_id: str
    campaign_id: str
    base_id: str
    mutated_fields: tuple[str, ...]
    inputs: BattleInputs
    rationale: str
    metadata: tuple[tuple[str, Any], ...] = ()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _base_inputs() -> dict[str, BattleInputs]:
    return {
        "physical_normal": BattleInputs(
            attacker_level=12,
            move_bp=45,
            move_type=NORMAL,
            is_physical=True,
            attacker_atk=30,
            defender_def=22,
            attacker_types=(NORMAL, FLYING),
            defender_types=(FIRE, FIRE),
        ),
        "special_fire": BattleInputs(
            attacker_level=18,
            move_bp=60,
            move_type=FIRE,
            is_physical=False,
            attacker_atk=55,
            defender_def=45,
            attacker_types=(FIRE, FIRE),
            defender_types=(GRASS, POISON),
        ),
        "special_grass_rain": BattleInputs(
            attacker_level=18,
            move_bp=60,
            move_type=GRASS,
            is_physical=False,
            attacker_atk=55,
            defender_def=45,
            attacker_types=(GRASS, POISON),
            defender_types=(WATER, GROUND),
            weather=WEATHER_RAIN,
            move_effect=EFFECT_SOLARBEAM,
        ),
        "status_item_base": BattleInputs(
            attacker_level=50,
            move_bp=60,
            move_type=FIRE,
            is_physical=False,
            attacker_atk=90,
            defender_def=70,
            attacker_types=(WATER, WATER),
            defender_types=(GRASS, NORMAL),
        ),
    }


def load_species_evolution_catalog(*, root: Path = ROOT) -> list[dict[str, Any]]:
    species = parse_species_constants(root / "constants" / "pokemon_constants.asm")
    pointers = parse_evos_attacks_pointers(root / "data" / "pokemon" / "evos_attacks_pointers.asm")
    can_evolve_by_label = parse_evos_attacks_evolution_flags(root / "data" / "pokemon" / "evos_attacks.asm")
    catalog: list[dict[str, Any]] = []
    for index, item in enumerate(species):
        pointer_label = pointers[index] if index < len(pointers) else ""
        catalog.append(
            {
                **item,
                "evos_attacks_label": pointer_label,
                "can_evolve": bool(can_evolve_by_label.get(pointer_label, False)),
                "has_evos_attacks_pointer": bool(pointer_label),
            }
        )
    return catalog


def parse_species_constants(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    species: list[dict[str, Any]] = []
    value = 0
    active = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("const_def"):
            if not species:
                value = 1
                active = True
            continue
        if line.startswith("DEF NUM_POKEMON"):
            break
        if not active:
            continue
        match = re.match(r"const\s+([A-Z0-9_]+)\b", line)
        if match:
            species.append({"species_id": value, "species_name": match.group(1)})
            value += 1
            continue
        if line.startswith("const_skip"):
            value += 1
    return species


def parse_evos_attacks_pointers(path: Path) -> list[str]:
    if not path.exists():
        return []
    labels: list[str] = []
    active = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line == "EvosAttacksPointers::":
            active = True
            continue
        if not active:
            continue
        if line.startswith("assert_table_length"):
            break
        match = re.match(r"dw\s+([A-Za-z0-9_.$]+)\b", line)
        if match:
            labels.append(match.group(1))
    return labels


def parse_evos_attacks_evolution_flags(path: Path) -> dict[str, bool]:
    if not path.exists():
        return {}
    flags: dict[str, bool] = {}
    current = ""
    scanning_evos = False
    can_evolve = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split(";", 1)[0].strip()
        label_match = re.match(r"([A-Za-z0-9_.$]+EvosAttacks):$", line)
        if label_match:
            if current:
                flags[current] = can_evolve
            current = label_match.group(1)
            scanning_evos = True
            can_evolve = False
            continue
        if not current or not scanning_evos or not line.startswith("db"):
            continue
        args = [part.strip() for part in line[2:].split(",")]
        first = args[0] if args else ""
        if first == "0":
            flags[current] = can_evolve
            scanning_evos = False
        elif first.startswith("EVOLVE_"):
            can_evolve = True
    if current:
        flags[current] = can_evolve
    return flags


def build_mutation_cases() -> list[MutationCase]:
    bases = _base_inputs()
    physical = bases["physical_normal"]
    special_fire = bases["special_fire"]
    special_grass = bases["special_grass_rain"]
    status_base = bases["status_item_base"]
    return [
        MutationCase(
            case_id="oracle_assumption_critical_flip",
            campaign_id="oracle_assumptions",
            base_id="physical_normal",
            mutated_fields=("is_critical",),
            inputs=replace(physical, is_critical=True),
            rationale="critical multiplier is a compact oracle assumption with a ROM-golden path",
        ),
        MutationCase(
            case_id="oracle_assumption_initial_damage_cap_add",
            campaign_id="oracle_assumptions",
            base_id="physical_normal",
            mutated_fields=("initial_cur_damage",),
            inputs=replace(physical, initial_cur_damage=0x0100),
            rationale="nonzero incoming wCurDamage guards cap/add accumulation semantics",
        ),
        MutationCase(
            case_id="oracle_assumption_truncate_high_stats",
            campaign_id="oracle_assumptions",
            base_id="physical_normal",
            mutated_fields=("attacker_level", "move_bp", "attacker_atk", "defender_def"),
            inputs=replace(
                physical,
                attacker_level=50,
                move_bp=90,
                attacker_atk=320,
                defender_def=280,
                attacker_types=(ROCK, GROUND),
                defender_types=(FIRE, DRAGON),
            ),
            rationale="high stat inputs exercise TruncateHL_BC instead of the common low-byte path",
        ),
        MutationCase(
            case_id="damage_variation_sun_fire_stab",
            campaign_id="damage_variation_and_type_matchup",
            base_id="special_fire",
            mutated_fields=("weather",),
            inputs=replace(special_fire, weather=WEATHER_SUN),
            rationale="weather mutation keeps a ROM-golden special path while changing STAB-side damage",
        ),
        MutationCase(
            case_id="damage_variation_rain_solarbeam",
            campaign_id="damage_variation_and_type_matchup",
            base_id="special_grass_rain",
            mutated_fields=("weather", "move_effect"),
            inputs=special_grass,
            rationale="SolarBeam-in-rain mutation covers move-effect-specific weather reduction",
        ),
        MutationCase(
            case_id="damage_variation_immunity_zero_damage",
            campaign_id="damage_variation_and_type_matchup",
            base_id="physical_normal",
            mutated_fields=("defender_types",),
            inputs=replace(physical, defender_types=(GHOST, GHOST)),
            rationale="normal-vs-ghost mutation proves the zero-damage matchup escape path",
        ),
        MutationCase(
            case_id="status_item_life_orb_special",
            campaign_id="status_item_interactions",
            base_id="status_item_base",
            mutated_fields=("user_item",),
            inputs=replace(status_base, user_item=HELD_LIFE_ORB),
            rationale="Life Orb changes the late-gen damage multiplier without changing stat stages",
        ),
        MutationCase(
            case_id="status_item_metronome_count",
            campaign_id="status_item_interactions",
            base_id="status_item_base",
            mutated_fields=("user_item", "metronome_count"),
            inputs=replace(status_base, user_item=HELD_METRONOME, metronome_count=3),
            rationale="Metronome item mutation covers counter-indexed late-gen damage scaling",
        ),
        MutationCase(
            case_id="status_item_wise_glasses_status_pressure",
            campaign_id="status_item_interactions",
            base_id="status_item_base",
            mutated_fields=("user_item", "opponent_has_status", "opponent_above_half_hp"),
            inputs=replace(
                status_base,
                user_item=HELD_WISE_GLASSES,
                opponent_has_status=True,
                opponent_above_half_hp=True,
            ),
            rationale="status and item mutation keeps public flags explicit for type-passive branches",
        ),
        MutationCase(
            case_id="status_item_assault_vest_defender",
            campaign_id="status_item_interactions",
            base_id="status_item_base",
            mutated_fields=("opponent_item", "defender_types"),
            inputs=replace(status_base, opponent_item=HELD_ASSAULT_VEST, defender_types=(ICE, DARK)),
            rationale="defender-held item mutation exercises special-defense item scaling",
        ),
        MutationCase(
            case_id="status_item_type_boost_physical",
            campaign_id="status_item_interactions",
            base_id="physical_normal",
            mutated_fields=("move_type", "user_item", "attacker_types", "defender_types"),
            inputs=replace(
                physical,
                move_type=FIGHTING,
                user_item=HELD_BLACKBELT_I,
                attacker_types=(FIGHTING, NORMAL),
                defender_types=(DARK, STEEL),
            ),
            rationale="type-boost item mutation covers a physical item multiplier with matchup rows",
        ),
    ]


def build_species_wide_eviolite_cases(*, root: Path = ROOT) -> tuple[list[MutationCase], dict[str, Any]]:
    catalog = load_species_evolution_catalog(root=root)
    cases: list[MutationCase] = []
    physical_base = BattleInputs(
        attacker_level=35,
        move_bp=70,
        move_type=NORMAL,
        is_physical=True,
        attacker_atk=95,
        defender_def=70,
        attacker_types=(NORMAL, NORMAL),
        defender_types=(NORMAL, NORMAL),
        opponent_item=HELD_EVOLITE,
    )
    special_base = replace(
        physical_base,
        move_type=FIRE,
        is_physical=False,
        attacker_atk=95,
        defender_def=70,
        attacker_types=(FIRE, FIRE),
    )
    for species in catalog:
        species_id = int(species.get("species_id", 0))
        species_name = str(species.get("species_name", ""))
        can_evolve = bool(species.get("can_evolve", False))
        safe_name = species_name.lower()
        for axis, base in (
            ("physical_defense", physical_base),
            ("special_defense", special_base),
        ):
            cases.append(
                MutationCase(
                    case_id=f"{SPECIES_WIDE_EVIOLITE_PREFIX}_{safe_name}_{axis}",
                    campaign_id="status_item_interactions",
                    base_id=f"species_{species_name}",
                    mutated_fields=(
                        "opponent_item",
                        "defender_species_id",
                        "can_evolve_defender",
                        "is_physical",
                    ),
                    inputs=replace(
                        base,
                        defender_species_id=species_id,
                        can_evolve_defender=can_evolve,
                    ),
                    rationale=(
                        "species-wide Eviolite ROM/oracle agreement for "
                        f"{species_name} ({axis}) using live EvosAttacks evolution data"
                    ),
                    metadata=(
                        ("species_wide_eviolite", True),
                        ("species_id", species_id),
                        ("species_name", species_name),
                        ("eviolite_axis", axis),
                        ("expected_can_evolve_defender", can_evolve),
                        ("evos_attacks_label", str(species.get("evos_attacks_label", ""))),
                    ),
                )
            )
    proof = {
        "kind": "damage_debugger_species_wide_eviolite_fuzz",
        "schema_version": 1,
        "evidence_id": SPECIES_WIDE_EVIOLITE_EVIDENCE_ID,
        "proof_status": "complete" if catalog else "missing_evidence",
        "rom_backed": True,
        "species_count": len(catalog),
        "expected_case_count": len(catalog) * 2,
        "expected_axes": ["physical_defense", "special_defense"],
        "can_evolve_species_count": sum(1 for item in catalog if item.get("can_evolve")),
        "species": catalog,
    }
    return cases, proof


def build_auto_minimized_divergence_proof(*, tolerance: int = DEFAULT_TOLERANCE) -> dict[str, Any]:
    from .minimize import COUPLED_FIELDS, DEFAULTS, minimize

    seed = BattleInputs(
        attacker_level=42,
        move_bp=75,
        move_type=FIRE,
        is_physical=False,
        attacker_atk=118,
        defender_def=76,
        attacker_types=(FIRE, NORMAL),
        defender_types=(GRASS, NORMAL),
        user_item=HELD_WISE_GLASSES,
        opponent_has_status=True,
        opponent_above_half_hp=True,
        weather=WEATHER_SUN,
        initial_cur_damage=3,
    )
    errors: list[str] = []
    check_count = 0

    def forced_divergence_route(inp: BattleInputs) -> bool:
        nonlocal check_count
        check_count += 1
        rom_damage, oracle_damage, ok = check_one(inp, tolerance=tolerance)
        if not ok:
            errors.append(
                "real ROM/oracle divergence appeared while proving the synthetic auto-minimize route"
            )
            return False
        return (
            not inp.is_physical
            and inp.move_type == FIRE
            and inp.user_item == HELD_WISE_GLASSES
            and inp.opponent_has_status is True
        )

    minimized, story = minimize(seed, forced_divergence_route)
    route_still_fires = forced_divergence_route(minimized)
    rom_damage, oracle_damage, check_ok = check_one(minimized, tolerance=tolerance)
    forced_oracle_damage = oracle_damage + tolerance + 1
    input_field_names = [field.name for field in fields(BattleInputs)]
    reduced_fields = [
        name
        for name in input_field_names
        if name not in COUPLED_FIELDS
        and getattr(seed, name) != getattr(DEFAULTS, name)
        and getattr(minimized, name) == getattr(DEFAULTS, name)
    ]
    preserved_fields = [
        name
        for name in input_field_names
        if name not in COUPLED_FIELDS
        and getattr(seed, name) != getattr(DEFAULTS, name)
        and getattr(minimized, name) == getattr(seed, name)
    ]
    non_default_minimized_fields = [
        name
        for name in input_field_names
        if getattr(minimized, name) != getattr(DEFAULTS, name)
    ]
    if not check_ok:
        errors.append("minimized synthetic route no longer has normal ROM/oracle agreement")
    if not route_still_fires:
        errors.append("minimized synthetic route no longer satisfies the forced divergence predicate")
    if not reduced_fields:
        errors.append("auto-minimized route did not reduce any input fields")
    if not preserved_fields:
        errors.append("auto-minimized route did not preserve any load-bearing input fields")
    if story and "nothing to minimize" in story[0]:
        errors.append("auto-minimized route predicate did not fire on the initial inputs")

    materialized_case = {
        "kind": "damage_debugger_materialized_divergence_case",
        "schema_version": 1,
        "case_id": AUTO_MINIMIZED_DIVERGENCE_CASE_ID,
        "synthetic_forced_divergence": True,
        "reason": (
            "The live campaign has no real divergence; this case forces the same "
            "materialize/minimize handoff path over a ROM-checked BattleInputs row."
        ),
        "inputs": asdict(minimized),
        "rom_damage": rom_damage,
        "oracle_damage": oracle_damage,
        "forced_oracle_damage": forced_oracle_damage,
        "delta": rom_damage - forced_oracle_damage,
        "tolerance": tolerance,
        "ok": False,
    }
    materialized_hash = stable_json_hash(materialized_case)
    commands = {
        "minimize_command": (
            "python -m tools.damage_debugger.minimize --bug hp_d_clobber"
        ),
        "replay_command": (
            "python -m tools.damage_debugger.replay --scenario "
            "audit\\damage_debugger\\auto_minimized_divergence_probe.json "
            "--watch wCurDamage --json"
        ),
        "taint_command": (
            "python -m tools.debugger dynamic-taint --trace <instruction-trace.jsonl> "
            "--sink-symbol wCurDamage --source-reg <register-or-origin>"
        ),
    }
    return {
        "kind": "damage_debugger_auto_minimized_divergence_artifacts",
        "schema_version": 1,
        "evidence_id": AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID,
        "proof_status": "complete" if not errors else "missing_evidence",
        "route_proof_status": "complete" if not errors else "missing_evidence",
        "route_proof_kind": "synthetic_forced_divergence_over_rom_checked_case",
        "campaign_fail_count": 0,
        "real_divergence_count": 0,
        "check_one_call_count": check_count,
        "initial_inputs": asdict(seed),
        "minimized_inputs": asdict(minimized),
        "minimization_story": story,
        "reduced_fields": reduced_fields,
        "preserved_fields": preserved_fields,
        "non_default_minimized_fields": non_default_minimized_fields,
        "materialized_case": materialized_case,
        "materialized_case_sha256": materialized_hash,
        "materialized_artifacts": [
            {
                "path": "audit/damage_debugger/mutation_campaign.json#/auto_minimized_divergence_proof/materialized_case",
                "sha256": materialized_hash,
                "kind": "inline_materialized_divergence_case",
            }
        ],
        "commands": commands,
        "known_limits": [
            "The campaign found no real divergence; this is a forced route proof that the handoff produces a minimized materialized case when a divergence exists.",
        ],
        "errors": errors,
    }


def _case_to_json(case: MutationCase, *, tolerance: int) -> dict[str, Any]:
    rom_damage, oracle_damage, ok = check_one(case.inputs, tolerance=tolerance)
    row = {
        "mutation_id": case.case_id,
        "case_id": case.case_id,
        "category": case.campaign_id,
        "campaign_id": case.campaign_id,
        "base_id": case.base_id,
        "method": "fuzz.check_one",
        "rom_backed": True,
        "mutated_fields": list(case.mutated_fields),
        "rationale": case.rationale,
        "inputs": asdict(case.inputs),
        "rom_damage": rom_damage,
        "oracle_damage": oracle_damage,
        "delta": rom_damage - oracle_damage,
        "tolerance": tolerance,
        "ok": ok,
        "on_divergence": {
            "minimize_command": (
                "python -m tools.damage_debugger.minimize --bug <new_mutation_divergence>"
            ),
            "replay_command": (
                "python -m tools.damage_debugger.replay --scenario <materialized_case> "
                "--watch wCurDamage --json"
            ),
            "taint_command": (
                "python -m tools.damage_debugger.taint --sink-symbol wCurDamage"
            ),
        },
    }
    for key, value in case.metadata:
        row[key] = value
    return row


def _run_smoke_cases() -> list[dict[str, Any]]:
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    by_name = {scenario.name: scenario for scenario in SCENARIOS}
    cache = BootStateCache(rom)
    cache.prime()
    rows: list[dict[str, Any]] = []
    try:
        for scenario_name, category in SMOKE_SCENARIOS:
            scenario = by_name[scenario_name]
            damage, _snapshots, seed_state, check_failures = run_scenario(scenario, syms, cache)
            in_range = scenario.expected_low <= damage <= scenario.expected_high
            ok = in_range and not check_failures and not scenario.xfail
            rows.append(
                {
                    "mutation_id": f"smoke_{scenario_name}",
                    "case_id": scenario_name,
                    "category": category,
                    "campaign_id": category,
                    "method": "clobber_smoke.run_scenario",
                    "rom_backed": True,
                    "damage": damage,
                    "expected_low": scenario.expected_low,
                    "expected_high": scenario.expected_high,
                    "seed_state": seed_state,
                    "check_failures": check_failures,
                    "xfail": scenario.xfail,
                    "ok": ok,
                    "replay_verified": None,
                    "rationale": scenario.note,
                }
            )
    finally:
        cache.stop()
    return rows


def _run_replay_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario_name, watch, size in REPLAY_SPECS:
        hit, failures = replay_scenario(scenario_name, watch, size=size)
        replay_verified = bool(hit is not None and hit.replay_verified)
        rows.append(
            {
                "mutation_id": f"replay_{scenario_name}_{watch}",
                "case_id": scenario_name,
                "category": "replay_watchpoints",
                "campaign_id": "replay_watchpoints",
                "method": "replay.replay_scenario",
                "rom_backed": True,
                "watch": watch,
                "size": size,
                "hit": hit_to_dict(hit) if hit is not None else None,
                "failures": failures,
                "replay_verified": replay_verified,
                "ok": replay_verified and not failures,
                "rationale": "snapshot-ring replay proves the watched ROM state transition is reproducible",
            }
        )
    return rows


def build_selected_status_side_effects_proof() -> dict[str, Any]:
    from tools.headless_battle.rom_differential import (
        compare_damaging_status_component,
        compare_full_restore_status_cure,
    )

    damaging_status = compare_damaging_status_component()
    full_restore = compare_full_restore_status_cure()
    differentials = (damaging_status, full_restore)
    errors: list[str] = []
    cases: dict[str, dict[str, Any]] = {}
    for result in differentials:
        if not result.ok:
            errors.extend(result.errors)
        for case_id, rom in result.rom.items():
            headless = result.headless.get(case_id, {})
            if not isinstance(headless, dict) or not headless:
                errors.append(f"{case_id}: missing headless status side-effect evidence")
                continue
            cases[case_id] = {
                "case_id": case_id,
                "component_differential_id": result.scenario_id,
                "rom_backed": True,
                "ok": result.ok,
                "rom": rom,
                "headless": headless,
            }
    missing = [
        case_id
        for case_id in SELECTED_STATUS_SIDE_EFFECT_CASE_IDS
        if case_id not in cases
    ]
    if missing:
        errors.append(f"missing selected status side-effect cases: {missing}")
    selected_cases = {
        case_id: cases[case_id]
        for case_id in SELECTED_STATUS_SIDE_EFFECT_CASE_IDS
        if case_id in cases
    }
    failed_cases = [
        case_id
        for case_id, row in selected_cases.items()
        if row.get("ok") is not True
    ]
    if failed_cases:
        errors.append(f"non-passing selected status side-effect cases: {failed_cases}")
    return {
        "kind": "damage_debugger_selected_status_side_effects_rom_components",
        "schema_version": 1,
        "evidence_id": SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID,
        "proof_status": "complete" if not errors else "missing_evidence",
        "rom_backed": True,
        "source": "tools.headless_battle.rom_differential",
        "component_differential_ids": [result.scenario_id for result in differentials],
        "required_case_ids": list(SELECTED_STATUS_SIDE_EFFECT_CASE_IDS),
        "case_count": len(selected_cases),
        "pass_count": len(selected_cases) - len(failed_cases),
        "fail_count": len(failed_cases),
        "cases": selected_cases,
        "failures": failed_cases,
        "errors": errors,
        "known_limits": [
            "Selected damaging status and Full Restore side effects are ROM-backed component differentials; this is not exhaustive full-battle status, text, animation, inventory, script, or action-choice parity.",
        ],
    }


def _oracle_only_limits(*, selected_status_side_effects_ready: bool) -> list[dict[str, Any]]:
    if selected_status_side_effects_ready:
        return []
    return [
        {
            "mutation_id": "full_battle_status_side_effects",
            "rom_backed": False,
            "reason_not_rom_backed": "freeze/confusion/status application are broader headless-battle mechanics",
        },
    ]


def build_report(*, tolerance: int = DEFAULT_TOLERANCE) -> dict[str, Any]:
    species_cases, species_wide_eviolite_proof = build_species_wide_eviolite_cases()
    cases = [*build_mutation_cases(), *species_cases]
    rows: list[dict[str, Any]] = []
    identity = damage_mutation_identity()
    auto_minimized_divergence_proof: dict[str, Any] = {}
    selected_status_side_effects_proof: dict[str, Any] = {}
    try:
        for case in cases:
            rows.append(_case_to_json(case, tolerance=tolerance))
        auto_minimized_divergence_proof = build_auto_minimized_divergence_proof(tolerance=tolerance)
    finally:
        _shutdown_cache()
    selected_status_side_effects_proof = build_selected_status_side_effects_proof()
    rows.extend(_run_smoke_cases())
    rows.extend(_run_replay_cases())
    rng_distribution_proof = _run_rng_distribution_proof()
    rows = [stamp_damage_mutation_class(row, identity=identity) for row in rows]
    failures = [
        row
        for row in rows
        if row.get("ok") is not True or row.get("canonical_state_class_valid") is not True
    ]
    rng_failures = list(rng_distribution_proof.get("failures", []))
    species_rows = [
        row
        for row in rows
        if row.get("species_wide_eviolite") is True
    ]
    species_failures = [
        row.get("mutation_id", "")
        for row in species_rows
        if row.get("ok") is not True or row.get("canonical_state_class_valid") is not True
    ]
    species_wide_eviolite_proof = {
        **species_wide_eviolite_proof,
        "case_count": len(species_rows),
        "pass_count": len(species_rows) - len(species_failures),
        "fail_count": len(species_failures),
        "case_ids": [str(row.get("mutation_id", "")) for row in species_rows],
        "failures": species_failures,
        "proof_status": "complete" if not species_failures and species_rows else "missing_evidence",
    }
    campaign_ids = sorted({str(row.get("campaign_id", "")) for row in rows})
    auto_minimized_divergence_ready = (
        auto_minimized_divergence_proof.get("proof_status") == "complete"
    )
    selected_status_side_effects_ready = (
        selected_status_side_effects_proof.get("proof_status") == "complete"
    )
    complete = (
        not failures
        and not rng_failures
        and not species_failures
        and auto_minimized_divergence_ready
        and selected_status_side_effects_ready
    )
    closed_evidence_ids = (
        [
            EVIDENCE_ID,
            RNG_DISTRIBUTION_EVIDENCE_ID,
            SPECIES_WIDE_EVIOLITE_EVIDENCE_ID,
            AUTO_MINIMIZED_DIVERGENCE_EVIDENCE_ID,
            SELECTED_STATUS_SIDE_EFFECTS_EVIDENCE_ID,
        ]
        if complete
        else []
    )
    return {
        "kind": "damage_debugger_phase6_initial_mutation_campaign",
        "schema_version": 1,
        "generated_at": _utc_now(),
        "command": (
            "python -m tools.damage_debugger.mutation_campaign "
            "--json-out audit\\damage_debugger\\mutation_campaign.json"
        ),
        "hash_basis": _hash_basis_json(),
        "canonical_state_class_identity": identity,
        "backend": "pyboy",
        "proof_status": "complete" if complete else "missing_evidence",
        "closed_evidence_ids": closed_evidence_ids,
        "does_not_close": ["expanded_mutation_campaigns"],
        "campaign_scope": (
            "initial curated damage-chain, after-hit, sampled variation, "
            "recoil, and replay-watchpoint mutations"
        ),
        "required_campaigns": list(REQUIRED_CAMPAIGNS),
        "campaign_ids": campaign_ids,
        "campaign_count": len(campaign_ids),
        "case_count": len(rows),
        "pass_count": len(rows) - len(failures),
        "fail_count": len(failures),
        "rom_backed_cases": rows,
        "rng_distribution_proof": rng_distribution_proof,
        "species_wide_eviolite_proof": species_wide_eviolite_proof,
        "auto_minimized_divergence_proof": auto_minimized_divergence_proof,
        "selected_status_side_effects_proof": selected_status_side_effects_proof,
        "oracle_only_cases": _oracle_only_limits(
            selected_status_side_effects_ready=selected_status_side_effects_ready
        ),
        "failures": failures,
        "rng_distribution_failures": rng_failures,
        "cases": rows,
        "known_limits": [
            "This is an initial ROM-backed damage-chain mutation campaign, not the roadmap's full mutation matrix.",
            "Status application side effects remain broader full-battle roadmap work.",
            "Auto-minimized divergence evidence is a forced route proof because this campaign found no real divergences.",
            "Selected status side-effect evidence is component differential proof, not automatic full-battle action-choice parity.",
            "A passing mutation row proves agreement for that concrete mutated class, not exhaustive absence of damage bugs.",
        ],
    }


def _run_rng_distribution_proof() -> dict[str, Any]:
    base_damage = 255
    accepted = list(range(217, 256))
    cases: list[dict[str, Any]] = []
    failures: list[str] = []
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    syms = parse_sym(sym)
    cache = BootStateCache(rom)
    cache.prime()
    try:
        for multiplier in accepted:
            row = _run_damage_variation_case(
                cache=cache,
                syms=syms,
                case_id=f"damage_variation_rng_multiplier_{multiplier}",
                base_damage=base_damage,
                rng_values=(raw_for_rrca_result(multiplier),),
                expected_damage=expected_damage_variation_damage(base_damage, multiplier),
                expected_rng_consumed=1,
                expected_multiplier=multiplier,
            )
            cases.append(row)
            if not row["ok"]:
                failures.append(row["case_id"])
        rejection = _run_damage_variation_case(
            cache=cache,
            syms=syms,
            case_id="damage_variation_rng_reject_216_then_accept_217",
            base_damage=base_damage,
            rng_values=(raw_for_rrca_result(216), raw_for_rrca_result(217)),
            expected_damage=expected_damage_variation_damage(base_damage, 217),
            expected_rng_consumed=2,
            expected_multiplier=217,
            rejected_multipliers=(216,),
        )
        cases.append(rejection)
        if not rejection["ok"]:
            failures.append(rejection["case_id"])
    finally:
        cache.stop()

    observed_multipliers = sorted(
        {
            int(row.get("observed_multiplier", -1))
            for row in cases
            if row.get("case_kind") == "accepted_multiplier" and row.get("ok") is True
        }
    )
    rejection_loop_verified = bool(
        cases
        and cases[-1].get("case_kind") == "rejection_loop"
        and cases[-1].get("ok") is True
        and cases[-1].get("rng_consumed") == 2
    )
    if observed_multipliers != accepted:
        failures.append("accepted multiplier corpus incomplete")
    if not rejection_loop_verified:
        failures.append("rejection loop was not verified")
    return {
        "kind": "damage_debugger_rng_distribution_proof",
        "schema_version": 1,
        "evidence_id": RNG_DISTRIBUTION_EVIDENCE_ID,
        "proof_status": "complete" if not failures else "missing_evidence",
        "rom_backed": True,
        "method": "BattleCommand_DamageVariation direct-call with deterministic link RNG",
        "base_damage": base_damage,
        "accepted_multiplier_min": accepted[0],
        "accepted_multiplier_max": accepted[-1],
        "expected_multipliers": accepted,
        "observed_multipliers": observed_multipliers,
        "case_count": len(cases),
        "pass_count": sum(1 for row in cases if row.get("ok") is True),
        "fail_count": sum(1 for row in cases if row.get("ok") is not True) + len(
            [item for item in failures if item not in {row["case_id"] for row in cases}]
        ),
        "rejection_loop_verified": rejection_loop_verified,
        "cases": cases,
        "failures": failures,
        "known_limits": [
            "This proof covers BattleCommand_DamageVariation's accepted 85%-100% multiplier corpus and one rejection loop from deterministic link RNG; it is not a full-battle RNG scheduling proof.",
        ],
    }


def _run_damage_variation_case(
    *,
    cache: BootStateCache,
    syms: dict[str, tuple[int, int]],
    case_id: str,
    base_damage: int,
    rng_values: tuple[int, ...],
    expected_damage: int,
    expected_rng_consumed: int,
    expected_multiplier: int,
    rejected_multipliers: tuple[int, ...] = (),
) -> dict[str, Any]:
    pyboy = cache.restore()
    write_symbol_u16(pyboy, syms, "wCurDamage", base_damage)
    write_symbol_byte(pyboy, syms, "wLinkMode", 1)
    write_symbol_byte(pyboy, syms, "wLinkBattleRNCount", 0)
    for offset, value in enumerate(rng_values):
        write_symbol_byte(pyboy, syms, "wLinkBattleRNs", value, offset=offset)
    ticks, returned, post_pc = call_function_safe(
        pyboy,
        syms,
        "BattleCommand_DamageVariation",
        budget=10000,
    )
    actual_damage = read_symbol_u16(pyboy, syms, "wCurDamage")
    rng_consumed = read_symbol_byte(pyboy, syms, "wLinkBattleRNCount")
    ok = returned and actual_damage == expected_damage and rng_consumed == expected_rng_consumed
    return {
        "case_id": case_id,
        "case_kind": "rejection_loop" if rejected_multipliers else "accepted_multiplier",
        "rom_backed": True,
        "base_damage": base_damage,
        "rng_values": list(rng_values),
        "rrca_values": [rrca(value) for value in rng_values],
        "rejected_multipliers": list(rejected_multipliers),
        "expected_multiplier": expected_multiplier,
        "observed_multiplier": actual_damage if base_damage == 255 else None,
        "expected_damage": expected_damage,
        "actual_damage": actual_damage,
        "expected_rng_consumed": expected_rng_consumed,
        "rng_consumed": rng_consumed,
        "returned": returned,
        "ticks": ticks,
        "post_pc": f"{post_pc:04X}",
        "ok": ok,
    }


def raw_for_rrca_result(value: int) -> int:
    value &= 0xFF
    return ((value << 1) & 0xFF) | (value >> 7)


def rrca(value: int) -> int:
    value &= 0xFF
    return ((value >> 1) | ((value & 1) << 7)) & 0xFF


def expected_damage_variation_damage(base_damage: int, multiplier: int) -> int:
    return (int(base_damage) * int(multiplier)) // 255


def write_symbol_byte(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    name: str,
    value: int,
    *,
    offset: int = 0,
) -> None:
    bank, address = syms[name]
    write_byte_banked(pyboy, address + offset, value, bank)


def read_symbol_byte(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    name: str,
    *,
    offset: int = 0,
) -> int:
    bank, address = syms[name]
    return read_byte_banked(pyboy, address + offset, bank)


def write_symbol_u16(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    name: str,
    value: int,
) -> None:
    write_symbol_byte(pyboy, syms, name, (value >> 8) & 0xFF)
    write_symbol_byte(pyboy, syms, name, value & 0xFF, offset=1)


def read_symbol_u16(
    pyboy: Any,
    syms: dict[str, tuple[int, int]],
    name: str,
) -> int:
    bank, address = syms[name]
    return read_be_u16_banked(pyboy, address, bank)


def damage_mutation_identity(*, root: Path = ROOT) -> dict[str, str]:
    rom = find_rom("pokegold_debug")
    sym = find_sym("pokegold_debug")
    return {
        "rom_sha256": sha256_file(rom, root=root) or "missing",
        "symbols_sha256": sha256_file(sym, root=root) or "missing",
        "map_sha256": sha256_file(rom.with_suffix(".map"), root=root) or "missing",
        "rule_map_sha256": stable_json_hash(
            {
                "surface": "damage_mutation_campaign",
                "schema_version": 1,
                "required_campaigns": list(REQUIRED_CAMPAIGNS),
                "smoke_scenarios": list(SMOKE_SCENARIOS),
                "replay_specs": list(REPLAY_SPECS),
                "mutation_case_ids": [case.case_id for case in build_mutation_cases()],
            }
        ),
        "source_tree_sha256": proof_source_tree_hash(root),
        "dirty_diff_hash": proof_dirty_diff_hash(root),
    }


def stamp_damage_mutation_class(row: dict[str, Any], *, identity: dict[str, str]) -> dict[str, Any]:
    canonical = build_canonical_state_class(
        surface="damage_debugger",
        identity=identity,
        public_facts=damage_mutation_public_facts(row),
        surface_facts={
            "damage": {
                "mutation_campaign": "phase6_initial",
                "campaign_id": row.get("campaign_id", ""),
                "method": row.get("method", ""),
                "rom_backed": bool(row.get("rom_backed", False)),
            }
        },
        backend="pyboy",
        proof_status="emulator_evidence" if row.get("ok") is True else "missing_evidence",
        raw_state_provenance={
            "kind": "damage_mutation_campaign_case",
            "mutation_id": row.get("mutation_id", ""),
            "case_id": row.get("case_id", ""),
            "campaign_id": row.get("campaign_id", ""),
            "method": row.get("method", ""),
        },
        reachable_proof=damage_mutation_reachable_proof(row),
        missing_evidence=[] if row.get("ok") is True else ["damage_mutation_case_failed"],
        blocking_gaps=[] if row.get("ok") is True else ["damage_mutation_case_failed"],
        known_limits=[
            "Damage mutation class ids identify concrete PyBoy-backed mutation campaign rows, not exhaustive damage behavior.",
        ],
        source_refs=[
            "tools/damage_debugger/mutation_campaign.py",
            "tools/damage_debugger/fuzz.py",
            "tools/damage_debugger/clobber_smoke.py",
            "tools/damage_debugger/replay.py",
        ],
    )
    out = dict(row)
    out["canonical_state_class"] = canonical
    out["class_id"] = str(canonical.get("class_id", ""))
    out["class_fingerprint"] = str(canonical.get("class_fingerprint", ""))
    out["canonical_state_class_valid"] = bool(canonical.get("valid", False))
    out["canonical_state_class_errors"] = list(canonical.get("validation_errors", []))
    if not canonical.get("valid"):
        out["ok"] = False
    return out


def damage_mutation_public_facts(row: dict[str, Any]) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "mutation_id": row.get("mutation_id", ""),
        "case_id": row.get("case_id", ""),
        "campaign_id": row.get("campaign_id", ""),
        "category": row.get("category", ""),
        "method": row.get("method", ""),
        "rom_backed": bool(row.get("rom_backed", False)),
        "ok": bool(row.get("ok", False)),
    }
    for key in (
        "base_id",
        "mutated_fields",
        "inputs",
        "rom_damage",
        "oracle_damage",
        "delta",
        "tolerance",
        "damage",
        "expected_low",
        "expected_high",
        "watch",
        "size",
        "replay_verified",
    ):
        if key in row:
            facts[key] = row.get(key)
    hit = row.get("hit")
    if isinstance(hit, dict):
        facts["hit"] = {
            key: hit.get(key)
            for key in ("watch", "function", "old_hex", "new_hex", "replay_verified")
            if key in hit
        }
    return facts


def damage_mutation_reachable_proof(row: dict[str, Any]) -> dict[str, Any]:
    method = str(row.get("method", ""))
    if method == "fuzz.check_one":
        return {
            "method": method,
            "rom_damage": row.get("rom_damage"),
            "oracle_damage": row.get("oracle_damage"),
            "delta": row.get("delta"),
            "tolerance": row.get("tolerance"),
        }
    if method == "clobber_smoke.run_scenario":
        return {
            "method": method,
            "damage": row.get("damage"),
            "expected_low": row.get("expected_low"),
            "expected_high": row.get("expected_high"),
            "check_failure_count": len(row.get("check_failures", []) or []),
            "xfail": bool(row.get("xfail", False)),
        }
    if method == "replay.replay_scenario":
        hit = row.get("hit") if isinstance(row.get("hit"), dict) else {}
        return {
            "method": method,
            "watch": row.get("watch", ""),
            "replay_verified": row.get("replay_verified", False),
            "hit_replay_verified": hit.get("replay_verified", False),
        }
    return {"method": method}


def write_report(path: str | None, report: dict[str, Any]) -> None:
    if not path:
        return
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def self_test() -> int:
    cases = build_mutation_cases()
    species_cases, species_proof = build_species_wide_eviolite_cases()
    failures: list[str] = []
    if len(cases) < 9:
        failures.append("expected at least 9 mutation cases")
    campaigns = (
        {case.campaign_id for case in cases}
        | {category for _name, category in SMOKE_SCENARIOS}
        | {"replay_watchpoints"}
    )
    missing = set(REQUIRED_CAMPAIGNS) - campaigns
    if missing:
        failures.append(f"missing campaigns: {sorted(missing)}")
    smoke_names = {name for name, _category in SMOKE_SCENARIOS}
    for required in {
        "afterhit_rocky_helmet_before_shell_bell",
        "special_super_effective_variation",
        "recoil_basic_no_steel",
    }:
        if required not in smoke_names:
            failures.append(f"missing smoke scenario {required}")
    for case in cases:
        if not case.mutated_fields:
            failures.append(f"{case.case_id}: missing mutated fields")
        if case.inputs.user_item != HELD_NONE and "item" not in case.campaign_id and "type_boost" not in case.case_id:
            failures.append(f"{case.case_id}: item mutation is not assigned to item/status campaign")
    if not species_cases:
        failures.append("missing species-wide Eviolite cases")
    if len(species_cases) != int(species_proof.get("expected_case_count", 0) or 0):
        failures.append("species-wide Eviolite case count mismatch")
    route_proof = build_auto_minimized_divergence_proof()
    if route_proof.get("proof_status") != "complete":
        failures.append("auto-minimized divergence route proof is incomplete")
    _shutdown_cache()
    status_side_effects = build_selected_status_side_effects_proof()
    if status_side_effects.get("proof_status") != "complete":
        failures.append("selected status side-effect proof is incomplete")
    for multiplier in (217, 230, 255):
        raw = raw_for_rrca_result(multiplier)
        if rrca(raw) != multiplier:
            failures.append(f"RRCA inverse failed for multiplier {multiplier}")
        if expected_damage_variation_damage(255, multiplier) != multiplier:
            failures.append(f"damage variation expectation failed for multiplier {multiplier}")
    if failures:
        print("mutation campaign self-test: FAIL")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"mutation campaign self-test: PASS ({len(cases)} cases, {len(campaigns)} campaigns)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ROM-backed damage mutation campaign")
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--json-out", default=None, help="write JSON report to this path")
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE)
    parser.add_argument("--self-test", action="store_true", help="run pure campaign shape checks")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.tolerance < 0:
        parser.error("--tolerance must be >= 0")
    if args.self_test:
        return self_test()

    report = build_report(tolerance=args.tolerance)
    write_report(args.json_out, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "mutation campaign: "
            f"{report['pass_count']}/{report['case_count']} passed across "
            f"{report['campaign_count']} campaign(s)"
        )
        for row in report["cases"]:
            marker = "PASS" if row["ok"] else "FAIL"
            if row.get("method") == "fuzz.check_one":
                detail = (
                    f"rom={row['rom_damage']} oracle={row['oracle_damage']} "
                    f"delta={row['delta']}"
                )
            elif row.get("method") == "clobber_smoke.run_scenario":
                detail = (
                    f"damage={row['damage']} expected={row['expected_low']}-{row['expected_high']}"
                )
            else:
                detail = f"watch={row.get('watch')} replay_verified={row.get('replay_verified')}"
            print(f"{marker} {row['mutation_id']}: {detail}")
    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
