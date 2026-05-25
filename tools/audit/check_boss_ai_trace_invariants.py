#!/usr/bin/env python3
"""Audit post-patch Boss AI behavior invariants.

Thin runner. The 34 audit functions live in three sibling modules
(`trace_rom`, `trace_coverage`, `trace_logic`) and share asm-block
helpers via `_trace_helpers`. Split per
`audit/non_debugger_code_review_2026-05-26.md` §2 item #8 — the public
CLI surface (exit code + stdout summary) is unchanged.
"""

from __future__ import annotations

from _common import load
from _trace_helpers import (
    AI_TIERS,
    CONSTANTS,
    CORE,
    ITEMS,
    PARTIES,
    SCORING,
    SWITCH,
    WRAM,
    load_boss_source,
)
from trace_coverage import (
    audit_haki_quarantine,
    audit_last_move_encore_trap_bias,
    audit_no_per_class_role_bias,
    audit_public_threat_keeps_species_fallback,
    audit_revealed_coverage,
    audit_revealed_priority_pressure,
    audit_revealed_protect_commitment_risk,
    audit_revealed_recovery_denial_bias,
    audit_revealed_selfdestruct_protect_bias,
    audit_revenge_denial_uses_public_seen_species,
    audit_tier_only_switch_threshold,
)
from trace_logic import (
    audit_baton_pass_requires_living_bench,
    audit_immunity_tiebreak,
    audit_item_and_passive_reasoning,
    audit_poison_contact_risk,
    audit_setup_and_phazing,
    audit_spikes_and_status,
    audit_switch_loop,
)
from trace_rom import (
    audit_ai_get_enemy_move_thunk_preserves_move_id,
    audit_boss_move_attr_bank_safety,
    audit_constants,
    audit_legacy_switch_state_restoration,
    audit_lookahead_trace_preserves_score_cursor,
    audit_move_model_trace_snapshots,
    audit_no_battle_core_boss_labels,
    audit_predetermined_switch_index_guard,
    audit_primary_threat_fallback_preserves_register_state,
    audit_priority_trainers,
    audit_public_threat_scan_preserves_source_pointers,
    audit_switch_candidate_state_restoration,
    audit_trace_top_moves_preserves_pointer,
    audit_type_matchup_scan_preserves_table_cursor,
    audit_type_threat_severity_preserves_list_cursor,
)


def main() -> int:
    boss = load_boss_source()
    items = load(ITEMS)
    scoring = load(SCORING)
    switch = load(SWITCH)
    wram = load(WRAM)
    parties = load(PARTIES)
    tiers = load(AI_TIERS)
    constants = load(CONSTANTS)
    core = load(CORE)

    audit_revealed_coverage(boss, wram)
    audit_public_threat_keeps_species_fallback(boss)
    audit_switch_loop(boss)
    audit_haki_quarantine(boss)
    audit_revenge_denial_uses_public_seen_species(boss)
    audit_revealed_priority_pressure(boss)
    audit_revealed_protect_commitment_risk(boss)
    audit_revealed_recovery_denial_bias(boss)
    audit_last_move_encore_trap_bias(boss)
    audit_revealed_selfdestruct_protect_bias(boss)
    audit_spikes_and_status(boss)
    audit_setup_and_phazing(boss)
    audit_poison_contact_risk(boss)
    audit_immunity_tiebreak(boss)
    audit_switch_candidate_state_restoration(boss)
    audit_item_and_passive_reasoning(boss)
    audit_baton_pass_requires_living_bench(boss)
    audit_trace_top_moves_preserves_pointer(boss)
    audit_move_model_trace_snapshots(boss, wram)
    audit_lookahead_trace_preserves_score_cursor(boss)
    audit_boss_move_attr_bank_safety(boss)
    audit_ai_get_enemy_move_thunk_preserves_move_id(boss, scoring)
    audit_public_threat_scan_preserves_source_pointers(boss)
    audit_type_matchup_scan_preserves_table_cursor(boss)
    audit_type_threat_severity_preserves_list_cursor(boss)
    audit_primary_threat_fallback_preserves_register_state(boss)
    audit_legacy_switch_state_restoration(items, switch)
    audit_no_battle_core_boss_labels(core, boss)
    audit_predetermined_switch_index_guard(core)
    audit_tier_only_switch_threshold(boss)
    audit_no_per_class_role_bias(boss)
    audit_priority_trainers(parties, tiers)
    audit_constants(constants)

    print("Boss AI trace invariant audit passed.")
    print("Checked invariants:")
    for name in (
        "per-species revealed coverage",
        "four-revealed-move saturation guards",
        "public threat fallback after revealed-move scan",
        "source-weighted plausible threat confidence",
        "plausible threat source and seen-bench restoration",
        "public perish-count escape switching",
        "A->B->A loop penalty target check",
        "Uniform Haki oracle quarantine",
        "public seen-species revenge denial",
        "revealed priority pressure",
        "revealed Protect commitment risk",
        "revealed recovery denial bias",
        "revealed fast Encore avoidance",
        "last-move Encore trap bias",
        "revealed Selfdestruct Protect bias",
        "first-turn Spikes pressure gate",
        "public Rapid Spin risk before extra Spikes",
        "Ghost/Foresight spinblock adjustment",
        "bench revealed Rapid Spin public-memory risk",
        "active species Rapid Spin level-up prior",
        "public status fail gates",
        "public utility fail gates",
        "Disable/Encore public lock fail gates",
        "Mean Look public already-trapped fail gate",
        "Dream Eater public Substitute fail gate",
        "Nightmare public fail gates",
        "Ghost Curse self-KO hard gate",
        "Pain Split public value hard gate",
        "Imperial Scales pressure discount",
        "public +2 setup denial",
        "revealed anti-setup avoidance",
        "shared weather setup planning",
        "current non-Ghost Curse setup planning",
        "Spikes/setup projection overread floor",
        "Poison contact retaliation risk",
        "Spikes plus phazing pressure response",
        "per-class role bias removed",
        "primary-threat immunity pivot tie-break",
        "switch candidate base-data restoration",
        "Destiny Bond public trade-window bias",
        "revealed Destiny Bond KO avoidance",
        "Counter/Mirror Coat public trade-window bias",
        "revealed Counter/Mirror Coat avoidance",
        "Choice first-lock public counterplay risk",
        "Reversal/Flail public HP-band pressure",
        "known item and passive tactical reasoning",
        "Baton Pass living-bench gate",
        "trace top-move pointer preservation",
        "move-model trace score snapshots",
        "lookahead trace score-cursor preservation",
        "Boss AI bank-safe move attr reads",
        "AIGetEnemyMove_HL move-id preservation",
        "public threat scan source pointer preservation",
        "type-matchup scan table cursor preservation",
        "type-threat severity list cursor preservation",
        "primary-threat fallback register preservation",
        "legacy switch base-data restoration",
        "no Battle Core BossAI labels",
        "predetermined enemy switch index guard",
        "tier-only switch threshold",
    ):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
