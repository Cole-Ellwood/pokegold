from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.boss_ai_debugger.rom_contribution_trace import (
    CONTROL_HOOKS,
    DelayedMemoryPatch,
    PREDICATE_BRANCH_HOOKS,
    drive_replay_to_choice,
    drive_replay_to_switch_observation,
    HookTarget,
    MemoryPatch,
    replay_tick_count,
    RomContributionTracer,
    RuleFrame,
    build_report,
    format_rom_contribution_trace,
    parse_delayed_memory_patch,
    parse_memory_patch,
    should_issue_replay_button,
    resolve_rom_contribution_trace_paths,
    stamp_rom_contribution_trace_class,
    summarize_rom_contribution_trace,
    SymbolIndex,
)
from tools.trace.runtime import Symbol


class FakeRegisters:
    A = 0
    HL = 0
    SP = 0xFF00


class FakeMemory:
    def __init__(self) -> None:
        self.values: dict[tuple[int, int], int] = {}

    def __getitem__(self, key):
        if isinstance(key, tuple):
            bank, address = key
        else:
            bank, address = 0, key
        return self.values.get((bank, address), self.values.get((0, address), 0))

    def __setitem__(self, key, value: int) -> None:
        if isinstance(key, tuple):
            bank, address = key
        else:
            bank, address = 0, key
        self.values[(bank, address)] = value & 0xFF


class FakePyBoy:
    def __init__(self) -> None:
        self.register_file = FakeRegisters()
        self.memory = FakeMemory()


class FakeReplayPyBoy:
    def __init__(self, *, chosen_at_frame: int = 9999, switch_at_frame: int = 9999) -> None:
        self.frame = 0
        self.chosen_at_frame = chosen_at_frame
        self.switch_at_frame = switch_at_frame
        self.buttons: list[tuple[int, str, int]] = []
        self.ticks: list[int] = []

    def button(self, button_name: str, *, delay: int) -> None:
        self.buttons.append((self.frame, button_name, delay))

    def tick(self, count: int, _render: bool, _sound: bool) -> None:
        self.ticks.append(count)
        self.frame += count


class FakeSymbolIndex:
    rule = {
        "rule_id": "move.apply_test_bias",
        "source_label": ".ApplyTestBias",
        "classification": "public_info",
        "public_reads": ["wPlayerUsedMoves"],
    }

    def nearest_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyMoveModel.test_callsite"

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyMoveModel.ApplyTestBias"

    def rule_for(self, full_symbol: str):
        return self.rule


class AdaptiveRuleSymbolIndex:
    first_rule = {
        "rule_id": "move.maybe_pick_adaptive_enemy_lead.find_first_alive_otmon",
        "source_label": ".FindFirstAliveOTMon",
        "classification": "internal",
        "public_reads": [],
    }
    next_rule = {
        "rule_id": "move.maybe_pick_adaptive_enemy_lead.find_next_alive_otmon",
        "source_label": ".FindNextAliveOTMon",
        "classification": "internal",
        "public_reads": [],
    }

    def nearest_symbol(self, bank: int, address: int) -> str:
        return ""

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return ""

    def rule_for(self, full_symbol: str):
        if full_symbol == "MaybePickAdaptiveEnemyLead.FindFirstAliveOTMon":
            return self.first_rule
        if full_symbol == "MaybePickAdaptiveEnemyLead.FindNextAliveOTMon":
            return self.next_rule
        return None


class HelperRuleSymbolIndex:
    callsite_rule = {
        "rule_id": "move.apply_lookahead_to_top_move_candidates",
        "source_label": "BossAI_ApplyLookaheadToTopMoveCandidates",
        "classification": "platform_boundary",
        "public_reads": [],
    }
    helper_rule = {
        "rule_id": "move.apply_signed_delta_to_score",
        "source_label": "BossAI_ApplySignedDeltaToScore",
        "classification": "platform_boundary",
        "public_reads": [],
    }

    def nearest_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyLookaheadToTopMoveCandidates.after_helper"

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return "BossAI_ApplyLookaheadToTopMoveCandidates"

    def rule_for(self, full_symbol: str):
        if full_symbol == "BossAI_ApplySignedDeltaToScore":
            return self.helper_rule
        if full_symbol == "BossAI_ApplyLookaheadToTopMoveCandidates":
            return self.callsite_rule
        return None


class UtilityStatusRuleSymbolIndex:
    utility_rule = {
        "rule_id": "move.apply_move_model.utility_move_would_fail_publicly",
        "source_label": ".UtilityMoveWouldFailPublicly",
        "classification": "internal",
        "public_reads": [],
    }
    status_rule = {
        "rule_id": "move.apply_move_model.status_move_would_fail_publicly",
        "source_label": ".StatusMoveWouldFailPublicly",
        "classification": "public_info",
        "public_reads": ["wBattleMonStatus"],
    }

    def nearest_symbol(self, bank: int, address: int) -> str:
        return ""

    def nearest_rule_symbol(self, bank: int, address: int) -> str:
        return ""

    def rule_for(self, full_symbol: str):
        if full_symbol == "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly":
            return self.utility_rule
        if full_symbol == "BossAI_ApplyMoveModel.StatusMoveWouldFailPublicly":
            return self.status_rule
        return None


class RomContributionTraceTests(unittest.TestCase):
    def test_default_trace_discovery_includes_promoted_god_route_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            default_dir = root / "audit" / "boss_ai_debugger"
            route_dir = (
                default_dir
                / "god_level_benchmark"
                / "artifacts"
                / "changed_ai_rom_contribution_routes"
            )
            default_dir.mkdir(parents=True)
            route_dir.mkdir(parents=True)
            smoke = default_dir / "rom_contribution_trace_smoke.json"
            jasmine = route_dir / "jasmine.json"
            smoke.write_text("{}", encoding="utf-8")
            jasmine.write_text("{}", encoding="utf-8")

            with patch(
                "tools.boss_ai_debugger.rom_contribution_trace.DEFAULT_ROM_CONTRIBUTION_TRACE_SOURCES",
                (
                    (default_dir, "rom_contribution_trace_*.json"),
                    (route_dir, "*.json"),
                ),
            ):
                resolved = resolve_rom_contribution_trace_paths(None)

        self.assertEqual(resolved, [smoke, jasmine])

    def test_selector_control_hook_records_after_lookahead(self) -> None:
        self.assertEqual(CONTROL_HOOKS["BossAI_SelectMove.first_pass"], "selector_start")
        self.assertNotIn("BossAI_SelectMove", CONTROL_HOOKS)

    def test_score_helper_event_uses_score_pointer_candidate_and_active_rule(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.memory[1, 0xD768] = 0xD0
        pyboy.memory[1, 0xD769] = 0xD3
        pyboy.memory[0xFF00] = 0x34
        pyboy.memory[0xFF01] = 0x56
        pyboy.register_file.A = 5
        pyboy.register_file.HL = 0xC000
        pyboy.register_file.SP = 0xFF00
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
                "wBossAIScorePtr": Symbol(1, 0xD768),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyMoveModel.ApplyTestBias",
                rule=FakeSymbolIndex.rule,
            )
        )

        tracer.handle_score_helper(
            HookTarget(
                kind="score_helper",
                full_symbol="BossAI_EncourageScoreHL",
                operation="encourage_score",
                bank=0x0E,
                address=0x6983,
            )
        )
        pyboy.memory[1, 0xD0D3] = 15
        tracer.close_pending(trigger="unit_test")

        self.assertEqual(len(tracer.events), 1)
        event = tracer.events[0]
        self.assertEqual(event["candidate"]["slot_index"], 0)
        self.assertEqual(event["candidate"]["move_name"], "SURF")
        self.assertEqual(event["source"]["rule_id"], "move.apply_test_bias")
        self.assertEqual(
            event["source"]["static_public_read_hints"],
            ["wPlayerUsedMoves"],
        )
        self.assertEqual(event["score_before"], 20)
        self.assertEqual(event["score_after"], 15)
        self.assertEqual(event["delta"], -5)

    def test_score_helper_records_helper_rule_entry_without_stealing_delta_attribution(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.memory[0xFF00] = 0x34
        pyboy.memory[0xFF01] = 0x56
        pyboy.register_file.A = 5
        pyboy.register_file.HL = 0xD0D3
        pyboy.register_file.SP = 0xFEF0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
            },
            HelperRuleSymbolIndex(),
            {57: "SURF"},
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyLookaheadToTopMoveCandidates",
                rule=HelperRuleSymbolIndex.callsite_rule,
            )
        )

        tracer.handle_score_helper(
            HookTarget(
                kind="score_helper",
                full_symbol="BossAI_ApplySignedDeltaToScore",
                operation="apply_signed_lookahead_delta",
                bank=0x0E,
                address=0x6900,
            )
        )
        pyboy.memory[1, 0xD0D3] = 15
        tracer.close_pending(trigger="unit_test")

        self.assertEqual(len(tracer.rule_entries), 1)
        self.assertEqual(
            tracer.rule_entries[0]["source"]["rule_id"],
            "move.apply_signed_delta_to_score",
        )
        self.assertEqual(
            tracer.events[0]["source"]["rule_id"],
            "move.apply_lookahead_to_top_move_candidates",
        )
        self.assertEqual(tracer.events[0]["helper_symbol"], "BossAI_ApplySignedDeltaToScore")

    def test_rule_hook_records_dynamic_rule_entry_separate_from_score_events(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD768] = 0xD0
        pyboy.memory[1, 0xD769] = 0xD3
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.memory[0, 0xCBE8] = 1
        pyboy.memory[0, 0xCBE9] = 2
        pyboy.memory[0, 0xCBEA] = 3
        pyboy.memory[0, 0xCBEB] = 4
        pyboy.register_file.SP = 0xFEF0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
                "wBossAIScorePtr": Symbol(1, 0xD768),
                "wPlayerUsedMoves": Symbol(0, 0xCBE8),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )

        tracer.handle_rule(
            HookTarget(
                kind="rule",
                full_symbol="BossAI_ApplyMoveModel.ApplyTestBias",
                operation="",
                bank=0x0E,
                address=0x5100,
            )
        )

        self.assertEqual(tracer.events, [])
        self.assertEqual(len(tracer.rule_entries), 1)
        entry = tracer.rule_entries[0]
        self.assertEqual(entry["event_type"], "rule_enter")
        self.assertEqual(entry["candidate"]["move_name"], "SURF")
        self.assertEqual(entry["source"]["rule_id"], "move.apply_test_bias")
        self.assertEqual(
            entry["source"]["static_public_read_hints"],
            ["wPlayerUsedMoves"],
        )
        self.assertEqual(
            entry["public_input_snapshot"]["wPlayerUsedMoves"]["values"],
            [1, 2, 3, 4],
        )

    def test_predicate_branch_records_selected_outcome(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD768] = 0xD0
        pyboy.memory[1, 0xD769] = 0xD3
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        for offset in range(6):
            pyboy.memory[1, 0xD742 + offset] = 0x10 + offset
        for offset in range(24):
            pyboy.memory[1, 0xD777 + offset] = 0x80 + offset
        pyboy.register_file.SP = 0xFEF0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
                "wBossAIScorePtr": Symbol(1, 0xD768),
                "wBossAISeenPlayerSpecies": Symbol(1, 0xD742),
                "wBossAISpeciesUsedMoves": Symbol(1, 0xD777),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )

        tracer.handle_predicate_branch(
            HookTarget(
                kind="predicate_branch",
                full_symbol="BossAI_ApplyMoveModel.bench_spin_yes_pop",
                operation="found",
                bank=0x0E,
                address=0x53F0,
                predicate_id="seen_bench_revealed_rapid_spin",
                outcome="found",
                parent_symbol="BossAI_ApplyMoveModel.ApplyTestBias",
                legal_inputs=("wBossAISeenPlayerSpecies", "wBossAISpeciesUsedMoves"),
            )
        )

        self.assertEqual(tracer.events, [])
        self.assertEqual(tracer.rule_entries, [])
        self.assertEqual(len(tracer.predicate_branch_entries), 1)
        entry = tracer.predicate_branch_entries[0]
        self.assertEqual(entry["event_type"], "predicate_branch")
        self.assertEqual(entry["candidate"]["move_name"], "SURF")
        self.assertEqual(
            entry["predicate"]["predicate_id"],
            "seen_bench_revealed_rapid_spin",
        )
        self.assertEqual(entry["predicate"]["outcome"], "found")
        self.assertEqual(
            entry["predicate"]["legal_inputs"],
            ["wBossAISeenPlayerSpecies", "wBossAISpeciesUsedMoves"],
        )
        self.assertEqual(entry["source"]["rule_id"], "move.apply_test_bias")
        self.assertEqual(
            entry["source"]["dynamic_branch_legal_inputs"],
            ["wBossAISeenPlayerSpecies", "wBossAISpeciesUsedMoves"],
        )
        snapshot = entry["public_input_snapshot"]
        self.assertEqual(
            snapshot["wBossAISeenPlayerSpecies"]["values"],
            [0x10, 0x11, 0x12, 0x13, 0x14, 0x15],
        )
        self.assertEqual(snapshot["wBossAISeenPlayerSpecies"]["width"], 6)
        self.assertEqual(snapshot["wBossAISpeciesUsedMoves"]["width"], 24)
        self.assertEqual(
            snapshot["wBossAISpeciesUsedMoves"]["values"][:4],
            [0x80, 0x81, 0x82, 0x83],
        )

    def test_player_cant_act_boundary_hook_declares_public_status_input(self) -> None:
        hook = PREDICATE_BRANCH_HOOKS["BossAI_ApplyMoveModel.player_cant_act"]

        self.assertEqual(
            hook["predicate_id"],
            "player_cant_act_this_turn_publicly",
        )
        self.assertEqual(hook["outcome"], "status_prevents_action")
        self.assertEqual(
            hook["parent_symbol"],
            "BossAI_ApplyMoveModel.PlayerCantActThisTurnPublicly",
        )
        self.assertEqual(hook["legal_inputs"], ("wBattleMonStatus",))

    def test_enemy_is_ghost_type_boundary_hook_declares_public_type_inputs(
        self,
    ) -> None:
        hook = PREDICATE_BRANCH_HOOKS["BossAI_EnemyIsGhostType.yes"]

        self.assertEqual(hook["predicate_id"], "enemy_is_ghost_type")
        self.assertEqual(hook["outcome"], "ghost_type_present")
        self.assertEqual(hook["parent_symbol"], "BossAI_EnemyIsGhostType")
        self.assertEqual(hook["legal_inputs"], ("wEnemyMonType1", "wEnemyMonType2"))

    def test_move_model_outcome_boundary_hooks_declare_concrete_parents(self) -> None:
        cases = {
            "BossAI_ApplyMoveModel.status_fail": (
                "utility_or_status_public_fail",
                "public_failure",
                "$active_frame",
            ),
            "BossAI_ApplyMoveModel.status_type_fail": (
                "status_move_type_immunity",
                "type_immunity",
                "BossAI_ApplyMoveModel.EnemyStatusMoveTypeMissesPlayer",
            ),
            "BossAI_ApplyMoveModel.skip_utility_fail": (
                "utility_move_would_fail_publicly",
                "not_publicly_failed",
                "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
            ),
            "BossAI_ApplyMoveModel.setup_punish": (
                "setup_punish_bias",
                "setup_punish_move",
                "BossAI_ApplyMoveModel.ApplySetupPunishBias",
            ),
            "BossAI_ApplyMoveModel.discourage_recovery": (
                "recovery_timing_discipline",
                "recovery_too_slow",
                "BossAI_ApplyMoveModel.ApplyRecoveryTimingDiscipline",
            ),
            "BossAI_ApplyMoveModel.yes_recovery": (
                "current_enemy_recovery_move",
                "recovery_move",
                "BossAI_ApplyMoveModel.IsCurrentEnemyRecoveryMove",
            ),
            "BossAI_ApplyMoveModel.phaze_good": (
                "phazing_plan_bias",
                "phaze_good",
                "BossAI_ApplyMoveModel.ApplyPhazingPlanBias",
            ),
            "BossAI_ApplyMoveModel.baton_bad": (
                "baton_pass_bias",
                "bad_pass_context",
                "BossAI_ApplyMoveModel.ApplyBatonPassBias",
            ),
            "BossAI_ApplyMoveModel.baton_good": (
                "baton_pass_bias",
                "boost_pass_available",
                "BossAI_ApplyMoveModel.ApplyBatonPassBias",
            ),
            "BossAI_ApplyMoveModel.boost_setup_yes": (
                "boost_setup_move",
                "boost_setup_move",
                "BossAI_ApplyMoveModel.IsBoostSetupMove",
            ),
        }

        for symbol, (predicate_id, outcome, parent_symbol) in cases.items():
            with self.subTest(symbol=symbol):
                hook = PREDICATE_BRANCH_HOOKS[symbol]
                self.assertEqual(hook["predicate_id"], predicate_id)
                self.assertEqual(hook["outcome"], outcome)
                self.assertEqual(hook["parent_symbol"], parent_symbol)
                self.assertTrue(hook["legal_inputs"])

    def test_adaptive_lead_boundary_hooks_declare_public_inputs(self) -> None:
        should_use = PREDICATE_BRANCH_HOOKS["MaybePickAdaptiveEnemyLead.enabled"]
        disabled = PREDICATE_BRANCH_HOOKS["MaybePickAdaptiveEnemyLead.loop"]
        first_alive = PREDICATE_BRANCH_HOOKS["MaybePickAdaptiveEnemyLead.first_found"]
        next_alive = PREDICATE_BRANCH_HOOKS["MaybePickAdaptiveEnemyLead.next_found"]
        none_found = PREDICATE_BRANCH_HOOKS["MaybePickAdaptiveEnemyLead.none_found"]

        self.assertEqual(should_use["predicate_id"], "adaptive_lead_trainer_match")
        self.assertEqual(should_use["outcome"], "enabled")
        self.assertEqual(
            should_use["parent_symbol"],
            "MaybePickAdaptiveEnemyLead.ShouldUseAdaptiveLeadForTrainer",
        )
        self.assertEqual(
            should_use["legal_inputs"],
            ("wOtherTrainerClass", "wOtherTrainerID", "AdaptiveLeadMap"),
        )
        self.assertEqual(disabled["predicate_id"], "adaptive_lead_trainer_match")
        self.assertEqual(disabled["outcome"], "disabled")
        self.assertEqual(
            disabled["parent_symbol"],
            "MaybePickAdaptiveEnemyLead.ShouldUseAdaptiveLeadForTrainer",
        )
        self.assertEqual(
            disabled["legal_inputs"],
            ("wOtherTrainerClass", "wOtherTrainerID", "AdaptiveLeadMap"),
        )
        self.assertEqual(disabled["condition"], "hl_points_to_zero_byte")
        self.assertEqual(
            first_alive["predicate_id"],
            "adaptive_lead_first_alive_party_mon",
        )
        self.assertEqual(first_alive["outcome"], "found")
        self.assertEqual(
            first_alive["parent_symbol"],
            "MaybePickAdaptiveEnemyLead.FindFirstAliveOTMon",
        )
        self.assertEqual(first_alive["legal_inputs"], ("wOTPartyCount", "wOTPartyMon1HP"))
        self.assertEqual(next_alive["predicate_id"], "adaptive_lead_next_alive_party_mon")
        self.assertEqual(next_alive["outcome"], "found")
        self.assertEqual(
            next_alive["parent_symbol"],
            "MaybePickAdaptiveEnemyLead.FindNextAliveOTMon",
        )
        self.assertEqual(next_alive["legal_inputs"], ("wOTPartyCount", "wOTPartyMon1HP"))
        self.assertEqual(none_found["predicate_id"], "adaptive_lead_alive_party_mon")
        self.assertEqual(none_found["outcome"], "not_found")
        self.assertEqual(none_found["parent_symbol"], "$active_frame")
        self.assertEqual(none_found["legal_inputs"], ("wOTPartyCount", "wOTPartyMon1HP"))

    def test_adaptive_lead_start_hook_reapplies_replay_patches(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD200] = 3
        tracer = RomContributionTracer(
            pyboy,
            {
                "wOTPartyCount": Symbol(1, 0xD200),
            },
            FakeSymbolIndex(),
            {},
            memory_patches=[MemoryPatch("wOTPartyCount", 0, 0)],
        )

        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="MaybePickAdaptiveEnemyLead",
                operation="adaptive_lead_start",
                bank=0x0E,
                address=0x4300,
            )
        )

        self.assertEqual(pyboy.memory[1, 0xD200], 0)

    def test_adaptive_none_found_hook_uses_active_rule_frame_parent(self) -> None:
        pyboy = FakePyBoy()
        pyboy.register_file.SP = 0xFEF0
        pyboy.memory[1, 0xD200] = 0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wOTPartyCount": Symbol(1, 0xD200),
                "wOTPartyMon1HP": Symbol(1, 0xD300),
            },
            AdaptiveRuleSymbolIndex(),
            {},
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="MaybePickAdaptiveEnemyLead.FindFirstAliveOTMon",
                rule=AdaptiveRuleSymbolIndex.first_rule,
            )
        )

        tracer.handle_predicate_branch(
            HookTarget(
                kind="predicate_branch",
                full_symbol="MaybePickAdaptiveEnemyLead.none_found",
                operation="not_found",
                bank=0x0E,
                address=0x4334,
                predicate_id="adaptive_lead_alive_party_mon",
                outcome="not_found",
                parent_symbol="$active_frame",
                legal_inputs=("wOTPartyCount", "wOTPartyMon1HP"),
            )
        )

        entry = tracer.predicate_branch_entries[0]
        self.assertEqual(
            entry["predicate"]["parent_symbol"],
            "MaybePickAdaptiveEnemyLead.FindFirstAliveOTMon",
        )
        self.assertEqual(
            entry["source"]["rule_id"],
            "move.maybe_pick_adaptive_enemy_lead.find_first_alive_otmon",
        )
        self.assertEqual(entry["public_input_snapshot"]["wOTPartyCount"]["values"], [0])

    def test_status_fail_outcome_hook_uses_active_rule_frame_parent(self) -> None:
        pyboy = FakePyBoy()
        pyboy.register_file.SP = 0xFEF0
        pyboy.memory[1, 0xD210] = 0x58
        pyboy.memory[1, 0xD211] = 0x02
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyMoveStructEffect": Symbol(1, 0xD210),
                "wBattleMonStatus": Symbol(1, 0xD211),
            },
            UtilityStatusRuleSymbolIndex(),
            {},
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
                rule=UtilityStatusRuleSymbolIndex.utility_rule,
            )
        )

        tracer.handle_predicate_branch(
            HookTarget(
                kind="predicate_branch",
                full_symbol="BossAI_ApplyMoveModel.status_fail",
                operation="public_failure",
                bank=0x0E,
                address=0x4963,
                predicate_id="utility_or_status_public_fail",
                outcome="public_failure",
                parent_symbol="$active_frame",
                legal_inputs=("wEnemyMoveStructEffect", "wBattleMonStatus"),
            )
        )

        entry = tracer.predicate_branch_entries[0]
        self.assertEqual(
            entry["predicate"]["parent_symbol"],
            "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
        )
        self.assertEqual(
            entry["source"]["rule_id"],
            "move.apply_move_model.utility_move_would_fail_publicly",
        )
        self.assertEqual(entry["public_input_snapshot"]["wEnemyMoveStructEffect"]["values"], [0x58])
        self.assertEqual(entry["public_input_snapshot"]["wBattleMonStatus"]["values"], [0x02])

    def test_negative_predicate_conditions_check_public_state(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD100] = 0x00
        pyboy.memory[1, 0xD200] = 7
        pyboy.memory[1, 0xD201] = 7
        pyboy.memory[1, 0xD202] = 7
        pyboy.memory[1, 0xD203] = 7
        pyboy.memory[1, 0xD204] = 7
        pyboy.memory[1, 0xD205] = 7
        pyboy.memory[1, 0xD206] = 7
        pyboy.memory[1, 0xD300] = 8
        pyboy.memory[1, 0xD301] = 3
        pyboy.memory[1, 0xD302] = 0
        pyboy.memory[1, 0xD400] = 0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wBattleMonStatus": Symbol(1, 0xD100),
                "wEnemyStatLevels": Symbol(1, 0xD200),
                "wEnemyMonType1": Symbol(1, 0xD300),
                "wEnemyMonType2": Symbol(1, 0xD301),
                "wEnemySubStatus1": Symbol(1, 0xD302),
                "wBossAISwitchCooldown": Symbol(1, 0xD400),
            },
            FakeSymbolIndex(),
            {},
        )

        self.assertTrue(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="battle_mon_can_act")
            )
        )
        self.assertTrue(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="enemy_has_no_boost_to_pass")
            )
        )
        self.assertTrue(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="enemy_active_spinblock_available")
            )
        )
        self.assertTrue(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="symbol_zero:wBossAISwitchCooldown")
            )
        )

        pyboy.memory[1, 0xD100] = 0x20
        pyboy.memory[1, 0xD203] = 8
        pyboy.memory[1, 0xD302] = 0x08
        pyboy.memory[1, 0xD400] = 1
        self.assertFalse(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="battle_mon_can_act")
            )
        )
        self.assertFalse(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="enemy_has_no_boost_to_pass")
            )
        )
        self.assertFalse(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="enemy_active_spinblock_available")
            )
        )
        self.assertFalse(
            tracer.predicate_branch_condition_matches(
                HookTarget("predicate_branch", "", "", 0, 0, condition="symbol_zero:wBossAISwitchCooldown")
            )
        )

    def test_conditional_predicate_branch_requires_hl_zero_byte(self) -> None:
        pyboy = FakePyBoy()
        pyboy.register_file.HL = 0x7000
        pyboy.memory[0x7000] = 1
        target = HookTarget(
            kind="predicate_branch",
            full_symbol="MaybePickAdaptiveEnemyLead.loop",
            operation="disabled",
            bank=0x0E,
            address=0x430B,
            predicate_id="adaptive_lead_trainer_match",
            outcome="disabled",
            parent_symbol="MaybePickAdaptiveEnemyLead.ShouldUseAdaptiveLeadForTrainer",
            legal_inputs=("wOtherTrainerClass", "wOtherTrainerID", "AdaptiveLeadMap"),
            condition="hl_points_to_zero_byte",
        )
        tracer = RomContributionTracer(pyboy, {}, FakeSymbolIndex(), {})

        tracer.handle_predicate_branch(target)

        self.assertEqual(tracer.predicate_branch_entries, [])
        tracer.handle_public_read_probe(
            HookTarget(
                kind="public_read_probe",
                full_symbol=target.full_symbol,
                operation=target.operation,
                bank=target.bank,
                address=target.address,
                predicate_id=target.predicate_id,
                outcome=target.outcome,
                parent_symbol=target.parent_symbol,
                legal_inputs=target.legal_inputs,
                condition=target.condition,
            )
        )
        self.assertEqual(tracer.public_read_probe_entries, [])

        pyboy.memory[0x7000] = 0
        tracer.handle_predicate_branch(target)
        tracer.handle_public_read_probe(
            HookTarget(
                kind="public_read_probe",
                full_symbol=target.full_symbol,
                operation=target.operation,
                bank=target.bank,
                address=target.address,
                predicate_id=target.predicate_id,
                outcome=target.outcome,
                parent_symbol=target.parent_symbol,
                legal_inputs=target.legal_inputs,
                condition=target.condition,
            )
        )

        self.assertEqual(len(tracer.predicate_branch_entries), 1)
        entry = tracer.predicate_branch_entries[0]
        self.assertEqual(entry["predicate"]["outcome"], "disabled")
        self.assertEqual(
            entry["predicate"]["predicate_id"],
            "adaptive_lead_trainer_match",
        )
        self.assertEqual(len(tracer.public_read_probe_entries), 1)
        self.assertEqual(
            tracer.public_read_probe_entries[0]["probe"]["outcome"],
            "disabled",
        )

    def test_switch_boundary_hooks_declare_public_inputs(self) -> None:
        seen_revenge = PREDICATE_BRANCH_HOOKS[
            "BossAI_ShouldRespectPotentialPlayerRevenge.seen_yes"
        ]
        low_hp = PREDICATE_BRANCH_HOOKS[
            "BossAI_SwitchCandidateLowHPBlock.at_quarter"
        ]
        immune = PREDICATE_BRANCH_HOOKS[
            "BossAI_CandidateImmuneToPlayerSTAB.immune_yes"
        ]

        self.assertEqual(seen_revenge["predicate_id"], "known_seen_revenge_threat")
        self.assertEqual(seen_revenge["outcome"], "seen_revenge_threat")
        self.assertEqual(
            seen_revenge["parent_symbol"],
            "BossAI_ShouldRespectPotentialPlayerRevenge.KnownSeenRevengeThreat",
        )
        self.assertEqual(
            seen_revenge["legal_inputs"],
            (
                "wBossAITier",
                "wBossAISeenPlayerSpeciesCount",
                "wBossAISeenPlayerSpecies",
                "wBossAISeenPlayerAliveMask",
                "wBattleMonSpecies",
                "wBattleMonType1",
                "wBattleMonType2",
                "wBossAISpeciesUsedMoves",
            ),
        )
        self.assertEqual(low_hp["predicate_id"], "switch_candidate_low_hp")
        self.assertEqual(low_hp["outcome"], "at_or_below_quarter")
        self.assertEqual(low_hp["parent_symbol"], "BossAI_SwitchCandidateLowHPBlock")
        self.assertEqual(low_hp["legal_inputs"], ("wEnemySwitchMonParam", "wOTPartyMon1HP"))
        self.assertEqual(immune["predicate_id"], "candidate_immune_to_player_stab")
        self.assertEqual(immune["outcome"], "immune")
        self.assertEqual(immune["parent_symbol"], "BossAI_CandidateImmuneToPlayerSTAB")
        self.assertEqual(
            immune["legal_inputs"],
            (
                "wEnemySwitchMonParam",
                "wOTPartySpecies",
                "wBattleMonType1",
                "wBattleMonType2",
                "BaseData",
            ),
        )

    def test_public_gate_boundary_hooks_declare_public_inputs(self) -> None:
        revealed_effect = PREDICATE_BRANCH_HOOKS[
            "BossAI_ApplyMoveModel.PlayerHasRevealedEffectA"
        ]
        revealed_super_effective = PREDICATE_BRANCH_HOOKS[
            "BossAI_HasRevealedSuperEffectiveMove"
        ]
        revealed_priority = PREDICATE_BRANCH_HOOKS[
            "BossAI_PlayerHasRevealedPriorityThreat"
        ]
        rapid_spin = PREDICATE_BRANCH_HOOKS[
            "BossAI_ApplyMoveModel.ApplyRapidSpinBias"
        ]
        anti_setup = PREDICATE_BRANCH_HOOKS[
            "BossAI_ApplyMoveModel.ApplyRevealedAntiSetupAvoidance"
        ]
        effect_matrix = PREDICATE_BRANCH_HOOKS[
            "BossAI_ApplyMoveModel.ApplyRevealedEffectMatrixBias"
        ]

        self.assertEqual(revealed_effect["predicate_id"], "player_revealed_effect_scan")
        self.assertEqual(revealed_effect["outcome"], "entered")
        self.assertEqual(
            revealed_effect["parent_symbol"],
            "BossAI_ApplyMoveModel.PlayerHasRevealedEffectA",
        )
        self.assertEqual(
            revealed_effect["legal_inputs"],
            ("wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
        )
        self.assertEqual(
            revealed_super_effective["predicate_id"],
            "revealed_super_effective_move",
        )
        self.assertEqual(revealed_super_effective["outcome"], "entered")
        self.assertEqual(
            revealed_super_effective["parent_symbol"],
            "BossAI_HasRevealedSuperEffectiveMove",
        )
        self.assertEqual(
            revealed_super_effective["legal_inputs"],
            (
                "wBattleMonSpecies",
                "wBossAISeenPlayerSpecies",
                "wBossAISpeciesUsedMoves",
                "wEnemyMonType1",
                "wEnemyMonType2",
            ),
        )
        self.assertEqual(revealed_priority["predicate_id"], "revealed_priority_threat")
        self.assertEqual(revealed_priority["outcome"], "entered")
        self.assertEqual(
            revealed_priority["parent_symbol"],
            "BossAI_PlayerHasRevealedPriorityThreat",
        )
        self.assertEqual(
            revealed_priority["legal_inputs"],
            (
                "wPlayerUsedMoves",
                "Moves + MOVE_EFFECT",
                "wEnemyMonType1",
                "wEnemyMonType2",
            ),
        )
        self.assertEqual(rapid_spin["predicate_id"], "rapid_spin_bias_public_gate")
        self.assertEqual(rapid_spin["outcome"], "entered")
        self.assertEqual(
            rapid_spin["parent_symbol"],
            "BossAI_ApplyMoveModel.ApplyRapidSpinBias",
        )
        self.assertEqual(rapid_spin["legal_inputs"], ("wEnemyScreens", "Moves + MOVE_EFFECT"))
        self.assertEqual(anti_setup["predicate_id"], "revealed_anti_setup_avoidance")
        self.assertEqual(anti_setup["outcome"], "entered")
        self.assertEqual(
            anti_setup["parent_symbol"],
            "BossAI_ApplyMoveModel.ApplyRevealedAntiSetupAvoidance",
        )
        self.assertEqual(
            anti_setup["legal_inputs"],
            ("wBossAITier", "wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
        )
        self.assertEqual(effect_matrix["predicate_id"], "revealed_effect_matrix_bias")
        self.assertEqual(effect_matrix["outcome"], "entered")
        self.assertEqual(
            effect_matrix["parent_symbol"],
            "BossAI_ApplyMoveModel.ApplyRevealedEffectMatrixBias",
        )
        self.assertEqual(
            effect_matrix["legal_inputs"],
            ("wBossAITier", "wPlayerUsedMoves", "Moves + MOVE_EFFECT"),
        )

    def test_public_input_snapshot_records_byte_party_and_static_inputs(self) -> None:
        pyboy = FakePyBoy()
        pyboy.register_file.A = 0x7C
        pyboy.memory[0, 0xCBE8] = 0xE5
        pyboy.memory[0, 0xCBE9] = 0x00
        pyboy.memory[0, 0xCBEA] = 0x33
        pyboy.memory[0, 0xCBEB] = 0x44
        pyboy.memory[1, 0xDD56] = 0x5E
        pyboy.memory[1, 0xDD57] = 0x5F
        for slot_index in range(6):
            base = 0xDD7F + (slot_index * 48)
            for offset in range(4):
                pyboy.memory[1, base + offset] = (slot_index * 4) + offset + 1
            pyboy.memory[1, 0xD200 + (slot_index * 48)] = 0x10 + slot_index
        tracer = RomContributionTracer(
            pyboy,
            {
                "wPlayerUsedMoves": Symbol(0, 0xCBE8),
                "wOTPartySpecies": Symbol(1, 0xDD56),
                "wOTPartyMon1HP": Symbol(1, 0xDD7F),
                "wOTPartyMon1Status": Symbol(1, 0xD200),
                "AdaptiveLeadMap": Symbol(0x0E, 0x7FD4),
                "BaseData": Symbol(0x14, 0x5AB9),
                "EvosAttacksPointers": Symbol(0x10, 0x685C),
                "Moves": Symbol(0x0E, 0x4000),
                "TypeBoostItems": Symbol(0x0D, 0x57DB),
            },
            FakeSymbolIndex(),
            {},
        )

        snapshot = tracer.public_input_snapshot(
            (
                "wPlayerUsedMoves",
                "wOTPartySpecies",
                "wOTPartyMon1HP",
                "wOTPartyMon1Status",
                "register:A",
                "AdaptiveLeadMap",
                "BaseData",
                "EvosAttacks",
                "Moves + MOVE_EFFECT",
                "TypeBoostItems",
                "MissingPublicInput",
            )
        )

        self.assertEqual(snapshot["wPlayerUsedMoves"]["kind"], "byte_range")
        self.assertEqual(
            snapshot["wPlayerUsedMoves"]["values"],
            [0xE5, 0, 0x33, 0x44],
        )
        self.assertEqual(snapshot["wOTPartySpecies"]["width"], 7)
        self.assertEqual(snapshot["wOTPartySpecies"]["values"][:2], [0x5E, 0x5F])
        party_hp = snapshot["wOTPartyMon1HP"]
        self.assertEqual(party_hp["kind"], "party_hp_slots")
        self.assertEqual(party_hp["slot_count"], 6)
        self.assertEqual(party_hp["slots"][0]["values"], [1, 2, 3, 4])
        self.assertEqual(party_hp["slots"][5]["values"], [21, 22, 23, 24])
        party_status = snapshot["wOTPartyMon1Status"]
        self.assertEqual(party_status["kind"], "party_status_slots")
        self.assertEqual(party_status["slots"][0]["status"], 0x10)
        self.assertEqual(party_status["slots"][5]["status"], 0x15)
        self.assertEqual(snapshot["register:A"]["kind"], "cpu_register")
        self.assertEqual(snapshot["register:A"]["value"], 0x7C)
        self.assertEqual(snapshot["AdaptiveLeadMap"]["kind"], "static_table_reference")
        self.assertEqual(snapshot["AdaptiveLeadMap"]["symbol"], "AdaptiveLeadMap")
        self.assertEqual(snapshot["BaseData"]["kind"], "static_table_reference")
        self.assertEqual(snapshot["EvosAttacks"]["symbol"], "EvosAttacksPointers")
        self.assertEqual(snapshot["Moves + MOVE_EFFECT"]["symbol"], "Moves")
        self.assertEqual(snapshot["TypeBoostItems"]["symbol"], "TypeBoostItems")
        self.assertFalse(snapshot["MissingPublicInput"]["available"])

    def test_register_input_hooks_declare_register_snapshots(self) -> None:
        cases = {
            "BossAI_PlayerHasRevealedEffectA_Coach": ("register:A",),
            "BossAI_GetRevealedMoveThreatTypeAndSeverity": ("register:A",),
            "BossAI_AdjustThreatSeverityForEnemyKnownDefense": ("register:B", "register:C"),
            "BossAI_EnemyKnownItemNullifiesThreatType": ("register:A",),
            "BossAI_ApplyDamageDominanceBias.ApplySTABToRank": ("register:A", "register:C"),
            "BossAI_ScaleMovePowerByBaseStatRatio.ApplyStatStagesToScored": ("register:A",),
            "BossAI_ApplyEnemyKnownPressureModifiers": ("register:B",),
            "BossAI_ApplyMoveModel.PlayerHasRevealedCounterCoatCategory": ("register:B",),
        }

        for symbol, required_inputs in cases.items():
            with self.subTest(symbol=symbol):
                hook = PREDICATE_BRANCH_HOOKS[symbol]
                for required in required_inputs:
                    self.assertIn(required, hook["legal_inputs"])

    def test_utility_failure_helper_has_own_boundary_predicate(self) -> None:
        hook = PREDICATE_BRANCH_HOOKS[
            "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly"
        ]

        self.assertEqual(hook["predicate_id"], "utility_move_would_fail_publicly")
        self.assertEqual(hook["outcome"], "entered")
        self.assertEqual(
            hook["parent_symbol"],
            "BossAI_ApplyMoveModel.UtilityMoveWouldFailPublicly",
        )
        self.assertIn("wEnemyMoveStructEffect", hook["legal_inputs"])
        self.assertIn("wPlayerScreens", hook["legal_inputs"])

    def test_selector_start_records_score_phase_boundary(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 14
        pyboy.memory[1, 0xD0D4] = 10
        pyboy.memory[1, 0xD0D5] = 19
        pyboy.memory[1, 0xD0D6] = 28
        tracer = RomContributionTracer(
            pyboy,
            {"wEnemyAIMoveScores": Symbol(1, 0xD0D3)},
            FakeSymbolIndex(),
            {},
        )

        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="BossAI_SelectMove",
                operation="selector_start",
                bank=0x0E,
                address=0x5000,
            )
        )

        self.assertEqual(tracer.selector_entry_scores, [14, 10, 19, 28])

    def test_candidate_end_records_direct_score_write_residual(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD0D4] = 20
        pyboy.memory[1, 0xD0D5] = 20
        pyboy.memory[1, 0xD0D6] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.register_file.SP = 0xFEF0
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )
        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="BossAI_ApplyMoveModel.ScoreMove",
                operation="candidate_start",
                bank=0x0E,
                address=0x5000,
            )
        )
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyDamageDominanceBias",
                rule={
                    **FakeSymbolIndex.rule,
                    "rule_id": "move.apply_damage_dominance_bias",
                    "source_label": "BossAI_ApplyDamageDominanceBias",
                },
            )
        )
        pyboy.memory[1, 0xD0D3] = 28
        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="BossAI_ApplyMoveModel.TracePostModelScore",
                operation="candidate_end",
                bank=0x0E,
                address=0x5100,
            )
        )

        self.assertEqual(len(tracer.events), 1)
        event = tracer.events[0]
        self.assertEqual(event["operation"], "direct_score_write")
        self.assertEqual(event["score_before"], 20)
        self.assertEqual(event["score_after"], 28)
        self.assertEqual(event["delta"], 8)
        self.assertEqual(event["candidate"]["move_name"], "SURF")
        self.assertEqual(event["source"]["rule_id"], "move.apply_damage_dominance_bias")

    def test_direct_score_write_does_not_double_count_helper_delta(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.register_file.A = 5
        pyboy.register_file.HL = 0xD0D3
        pyboy.register_file.SP = 0xFF00
        tracer = RomContributionTracer(
            pyboy,
            {
                "wEnemyAIMoveScores": Symbol(1, 0xD0D3),
                "wEnemyMonMoves": Symbol(1, 0xD100),
            },
            FakeSymbolIndex(),
            {57: "SURF"},
        )

        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="BossAI_ApplyMoveModel.ScoreMove",
                operation="candidate_start",
                bank=0x0E,
                address=0x5000,
            )
        )
        tracer.handle_score_helper(
            HookTarget(
                kind="score_helper",
                full_symbol="BossAI_ApplyMoveModel.EncourageScoreByA",
                operation="encourage_score",
                bank=0x0E,
                address=0x6983,
            )
        )
        pyboy.memory[1, 0xD0D3] = 15
        tracer.handle_control(
            HookTarget(
                kind="control",
                full_symbol="BossAI_ApplyMoveModel.TracePostModelScore",
                operation="candidate_end",
                bank=0x0E,
                address=0x5100,
            )
        )

        self.assertEqual([event["operation"] for event in tracer.events], ["encourage_score"])

    def test_replay_button_schedule_repeats_at_interval(self) -> None:
        frames = [
            frame
            for frame in range(140)
            if should_issue_replay_button(
                frame=frame,
                button="a",
                button_presses=3,
                button_interval_frames=45,
                presses_issued=sum(
                    1
                    for prior in (0, 45, 90)
                    if prior < frame
                ),
            )
        ]

        self.assertEqual(frames, [0, 45, 90])

    def test_replay_tick_count_stops_on_next_button_frame(self) -> None:
        tick_count = replay_tick_count(
            frame=0,
            watch_frames=700,
            button="a",
            button_presses=12,
            button_interval_frames=45,
            presses_issued=1,
        )

        self.assertEqual(tick_count, 45)

    def test_drive_replay_to_choice_ticks_between_repeated_buttons(self) -> None:
        pyboy = FakeReplayPyBoy(chosen_at_frame=96)

        def fake_trace_values(_pyboy, _symbols):
            chosen = 1 if pyboy.frame >= pyboy.chosen_at_frame else 0
            return {"wBossAITraceChosenMove": [chosen]}

        with patch(
            "tools.boss_ai_debugger.rom_contribution_trace.capture.read_trace_values",
            fake_trace_values,
        ):
            values, presses = drive_replay_to_choice(
                pyboy,
                {},
                button="a",
                button_delay=8,
                button_presses=3,
                button_interval_frames=45,
                watch_frames=200,
            )

        self.assertEqual(values, {"wBossAITraceChosenMove": [1]})
        self.assertEqual(presses, 3)
        self.assertEqual(pyboy.buttons, [(0, "a", 8), (45, "a", 8), (90, "a", 8)])
        self.assertEqual(pyboy.ticks, [45, 45, 45])

    def test_drive_replay_to_switch_observation_finishes_on_switch_bytes(self) -> None:
        pyboy = FakeReplayPyBoy(switch_at_frame=135)

        def fake_trace_values(_pyboy, _symbols):
            switch_confidence = 70 if pyboy.frame >= pyboy.switch_at_frame else 0
            return {
                "wBossAITraceChosenMove": [0],
                "wBossAITraceSwitchConfidence": [switch_confidence],
                "wEnemySwitchMonParam": [0],
                "wEnemySwitchMonIndex": [0],
            }

        with patch(
            "tools.boss_ai_debugger.rom_contribution_trace.capture.read_trace_values",
            fake_trace_values,
        ):
            values, presses, frame = drive_replay_to_switch_observation(
                pyboy,
                {},
                button="",
                button_delay=8,
                button_presses=1,
                button_interval_frames=0,
                watch_frames=200,
            )

        self.assertEqual(values["wBossAITraceSwitchConfidence"], [70])
        self.assertEqual(presses, 0)
        self.assertEqual(frame, 135)
        self.assertEqual(pyboy.buttons, [])

    def test_drive_replay_to_switch_observation_ignores_proposal_only_param(self) -> None:
        pyboy = FakeReplayPyBoy(switch_at_frame=135)

        def fake_trace_values(_pyboy, _symbols):
            switch_param = 0x31 if pyboy.frame >= 45 else 0
            switch_confidence = 70 if pyboy.frame >= pyboy.switch_at_frame else 0
            return {
                "wBossAITraceChosenMove": [0],
                "wBossAITraceSwitchConfidence": [switch_confidence],
                "wEnemySwitchMonParam": [switch_param],
                "wEnemySwitchMonIndex": [0],
            }

        with patch(
            "tools.boss_ai_debugger.rom_contribution_trace.capture.read_trace_values",
            fake_trace_values,
        ):
            values, presses, frame = drive_replay_to_switch_observation(
                pyboy,
                {},
                button="",
                button_delay=8,
                button_presses=1,
                button_interval_frames=0,
                watch_frames=200,
            )

        self.assertEqual(values["wEnemySwitchMonParam"], [0x31])
        self.assertEqual(values["wBossAITraceSwitchConfidence"], [70])
        self.assertEqual(presses, 0)
        self.assertEqual(frame, 135)

    def test_drive_replay_to_switch_observation_returns_timeout_state(self) -> None:
        pyboy = FakeReplayPyBoy()

        def fake_trace_values(_pyboy, _symbols):
            return {
                "wBossAITraceChosenMove": [0],
                "wBossAITraceSwitchConfidence": [0],
                "wEnemySwitchMonParam": [0],
                "wEnemySwitchMonIndex": [0],
            }

        with patch(
            "tools.boss_ai_debugger.rom_contribution_trace.capture.read_trace_values",
            fake_trace_values,
        ):
            values, presses, frame = drive_replay_to_switch_observation(
                pyboy,
                {},
                button="",
                button_delay=8,
                button_presses=1,
                button_interval_frames=0,
                watch_frames=3,
            )

        self.assertEqual(values["wBossAITraceSwitchConfidence"], [0])
        self.assertEqual(presses, 0)
        self.assertEqual(frame, 3)
        self.assertEqual(pyboy.ticks, [1, 1, 1, 1])

    def test_build_report_snapshots_mutable_trace_lists(self) -> None:
        events = [
            {
                "changed": True,
                "source": {"rule_id": "move.test"},
                "candidate": {"slot_index": 0},
            }
        ]
        report = build_report(
            save_state=Path(__file__),
            basis={},
            values={
                "wBossAITraceChosenMove": [1],
                "wCurEnemyMoveNum": [0],
                "wEnemyMonMoves": [1, 2, 3, 4],
                "wEnemyAIMoveScores": [1, 2, 3, 4],
                "wBossAITracePreModelScores": [20, 20, 20, 20],
                "wBossAITracePostModelScores": [19, 20, 20, 20],
            },
            events=events,
            rule_entries=[],
            predicate_branch_entries=[],
            public_read_probe_entries=[],
            delayed_patch_entries=[
                {
                    "event_type": "delayed_memory_patch",
                    "hook_symbol": "BossAI_GetSwitchThreshold",
                }
            ],
            selector_entry_scores=[19, 20, 20, 20],
            move_names={1: "TEST"},
            memory_patches=[],
            delayed_memory_patches=[
                DelayedMemoryPatch(
                    hook_symbol="BossAI_GetSwitchThreshold",
                    patch=MemoryPatch(
                        symbol_name="wBossAISwitchConfidence",
                        offset=0,
                        value=0,
                    ),
                )
            ],
        )
        events.clear()

        self.assertEqual(report["event_count"], 1)
        self.assertEqual(len(report["events"]), 1)
        self.assertEqual(report["delayed_patch_entry_count"], 1)
        self.assertEqual(
            report["delayed_memory_patches"][0]["hook_symbol"],
            "BossAI_GetSwitchThreshold",
        )
        self.assertRegex(report["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertTrue(report["canonical_state_class"]["valid"])
        report["trace_id"] = "unit_trace"
        stamp_rom_contribution_trace_class(report)
        self.assertEqual(
            report["canonical_state_class"]["raw_state_provenance"]["trace_id"],
            "unit_trace",
        )

    def test_build_report_marks_switch_dispatch_surface(self) -> None:
        report = build_report(
            save_state=Path(__file__),
            basis={},
            values={
                "wBossAITraceChosenMove": [0],
                "wCurEnemyMoveNum": [0],
                "wEnemyMonMoves": [1, 2, 3, 4],
                "wEnemyAIMoveScores": [20, 20, 20, 20],
                "wBossAITracePreModelScores": [20, 20, 20, 20],
                "wBossAITracePostModelScores": [20, 20, 20, 20],
            },
            events=[],
            rule_entries=[
                {
                    "source": {
                        "rule_id": "switch.compute_switch_candidate_risk",
                        "classification": "platform_boundary",
                    }
                }
            ],
            predicate_branch_entries=[],
            public_read_probe_entries=[],
            delayed_patch_entries=[],
            selector_entry_scores=[],
            move_names={},
            memory_patches=[],
            delayed_memory_patches=[],
            decision_surface="switch_dispatch",
            switch_observation={
                "frame": 120,
                "status": "switch_confidence_observed",
                "switch_confidence": 70,
                "switch_param": 0,
                "switch_index": 0,
                "chosen_move": 0,
            },
        )

        self.assertEqual(report["decision_surface"], "switch_dispatch")
        self.assertEqual(report["switch_observation"]["status"], "switch_confidence_observed")
        self.assertEqual(
            report["canonical_state_class"]["surface_facts"]["boss_ai"]["decision_surface"],
            "switch_dispatch",
        )
        self.assertIn(
            "switch.compute_switch_candidate_risk",
            report["canonical_state_class"]["public_facts"]["executed_rule_ids"],
        )


    def test_tracer_reset_clears_events_and_updates_patches(self) -> None:
        tracer = RomContributionTracer(
            FakePyBoy(),
            {},
            FakeSymbolIndex(),
            {},
            memory_patches=[MemoryPatch("wPlayerScreens", 0, 1)],
        )
        tracer.score_start_patches_applied = True
        tracer.events.append({"event_type": "score_delta"})
        tracer.rule_entries.append({"event_type": "rule_enter"})
        tracer.predicate_branch_entries.append({"event_type": "predicate_branch"})
        tracer.public_read_probe_entries.append({"event_type": "public_read_probe"})
        tracer.selector_entry_scores = [1, 2, 3, 4]
        tracer.frames.append(
            RuleFrame(
                sp=0xFEF0,
                full_symbol="BossAI_ApplyMoveModel.ApplyTestBias",
                rule=FakeSymbolIndex.rule,
            )
        )

        tracer.reset(memory_patches=[MemoryPatch("wPlayerScreens", 0, 2)])

        self.assertFalse(tracer.score_start_patches_applied)
        self.assertEqual(tracer.events, [])
        self.assertEqual(tracer.rule_entries, [])
        self.assertEqual(tracer.predicate_branch_entries, [])
        self.assertEqual(tracer.public_read_probe_entries, [])
        self.assertEqual(tracer.selector_entry_scores, [])
        self.assertEqual(tracer.frames, [])
        self.assertEqual(tracer.memory_patches[0].value, 2)

    def test_hook_targets_skip_static_boss_ai_tables(self) -> None:
        rule_map = {
            "rules": [
                {
                    "rule_id": "move.boss_airisky_effects",
                    "source_label": "BossAIRiskyEffects",
                    "classification": "internal",
                    "public_reads": [],
                },
                {
                    "rule_id": "move.apply_move_model",
                    "source_label": "BossAI_ApplyMoveModel",
                    "classification": "platform_boundary",
                    "public_reads": [],
                },
            ]
        }
        index = SymbolIndex(
            {
                "BossAIRiskyEffects": Symbol(0x0E, 0x724F),
                "BossAI_ApplyMoveModel": Symbol(0x0E, 0x5000),
            },
            rule_map,
        )

        hook_symbols = {target.full_symbol for target in index.hook_targets()}

        self.assertNotIn("BossAIRiskyEffects", hook_symbols)
        self.assertIn("BossAI_ApplyMoveModel", hook_symbols)

    def test_format_marks_changed_events(self) -> None:
        text = format_rom_contribution_trace(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:unit",
                "event_count": 1,
                "changed_event_count": 1,
                "chosen": {"move_name": "SURF", "move_id": 57, "slot_index": 0},
                "pre_model_scores": [20, 20, 20, 20],
                "post_model_scores": [20, 20, 20, 20],
                "move_scores": [15, 20, 20, 20],
                "rule_entry_count": 1,
                "predicate_branch_entry_count": 1,
                "public_read_probe_entry_count": 1,
                "rule_entries": [
                    {
                        "index": 1,
                        "event_type": "rule_enter",
                        "candidate": {"slot_index": 0, "move_name": "SURF"},
                        "source": {"rule_id": "move.apply_test_bias"},
                    }
                ],
                "predicate_branch_entries": [
                    {
                        "index": 1,
                        "event_type": "predicate_branch",
                        "candidate": {"slot_index": 0, "move_name": "SURF"},
                        "predicate": {
                            "predicate_id": "seen_bench_revealed_rapid_spin",
                            "outcome": "found",
                        },
                    }
                ],
                "public_read_probe_entries": [
                    {
                        "index": 1,
                        "event_type": "public_read_probe",
                        "candidate": {"slot_index": 0, "move_name": "SURF"},
                        "probe": {
                            "probe_id": "seen_bench_revealed_rapid_spin",
                            "outcome": "found",
                        },
                    }
                ],
                "events": [
                    {
                        "index": 1,
                        "changed": True,
                        "candidate": {"slot_index": 0, "move_name": "SURF"},
                        "operation": "encourage_score",
                        "amount_register_a": 5,
                        "score_before": 20,
                        "score_after": 15,
                        "delta": -5,
                        "source": {
                            "rule_id": "move.apply_test_bias",
                            "callsite_symbol": "BossAI_ApplyMoveModel.test_callsite",
                        },
                    }
                ],
                "known_limits": ["unit limit"],
            }
        )

        self.assertIn("* 001 slot=0 SURF encourage_score a=5 20->15 delta=-5", text)
        self.assertIn("move.apply_test_bias", text)
        self.assertIn("rule_entries=1", text)
        self.assertIn("predicate_branches=1", text)
        self.assertIn("public_read_probes=1", text)
        self.assertIn("First 1 public-read probes:", text)
        self.assertIn("First 1 rule entries:", text)
        self.assertIn("seen_bench_revealed_rapid_spin=found", text)

    def test_summary_counts_changed_and_executed_rules_separately(self) -> None:
        summary = summarize_rom_contribution_trace(
            {
                "source": "trace_rom_pyboy_hooks",
                "save_state": "route:unit",
                "event_count": 2,
                "changed_event_count": 1,
                "rule_entry_count": 1,
                "predicate_branch_entry_count": 1,
                "public_read_probe_entry_count": 1,
                "chosen": {"move_name": "SURF", "move_id": 57, "slot_index": 0},
                "trace_basis": {"trace_rom_sha256": "ROM", "trace_symbols_sha256": "SYM"},
                "rule_entries": [
                    {
                        "source": {
                            "rule_id": "move.rule_entry_only",
                            "classification": "public_info",
                        }
                    }
                ],
                "predicate_branch_entries": [
                    {
                        "predicate": {
                            "predicate_id": "seen_bench_revealed_rapid_spin",
                            "outcome": "found",
                        },
                        "public_input_snapshot": {
                            "wBossAISeenPlayerSpecies": {"values": [1, 2, 3]},
                        },
                        "source": {
                            "rule_id": "move.predicate_rule",
                            "classification": "public_info",
                        },
                    }
                ],
                "public_read_probe_entries": [
                    {
                        "probe": {
                            "probe_id": "active_revealed_rapid_spin",
                            "outcome": "not_revealed_for_layer2",
                        },
                        "public_input_snapshot": {
                            "wPlayerUsedMoves": {"values": [0, 0, 0, 0]},
                        },
                        "source": {
                            "rule_id": "move.public_probe_rule",
                            "classification": "public_info",
                        },
                    }
                ],
                "events": [
                    {
                        "changed": True,
                        "operation": "encourage_score",
                        "candidate": {"kind": "move", "slot_index": 0, "move_id": 57},
                        "source": {
                            "rule_id": "move.changed_rule",
                            "classification": "public_info",
                        },
                    },
                    {
                        "changed": False,
                        "operation": "discourage_score",
                        "candidate": {"kind": "move", "slot_index": 1, "move_id": 58},
                        "source": {
                            "rule_id": "move.executed_only",
                            "classification": "public_info",
                        },
                    },
                ],
                "known_limits": ["unit limit"],
            }
        )

        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["changed_event_count"], 1)
        self.assertEqual(summary["rule_entry_count"], 1)
        self.assertEqual(summary["predicate_branch_entry_count"], 1)
        self.assertEqual(
            summary["covered_rule_ids"],
            ["move.changed_rule", "move.executed_only"],
        )
        self.assertEqual(
            summary["executed_rule_ids"],
            [
                "move.changed_rule",
                "move.executed_only",
                "move.predicate_rule",
                "move.public_probe_rule",
                "move.rule_entry_only",
            ],
        )
        self.assertEqual(summary["changed_rule_ids"], ["move.changed_rule"])
        self.assertEqual(summary["executed_rule_count"], 5)
        self.assertRegex(summary["class_id"], r"^csc_[0-9A-F]{20}$")
        self.assertTrue(summary["canonical_state_class_valid"])
        self.assertEqual(
            summary["operation_counts"],
            {"discourage_score": 1, "encourage_score": 1},
        )
        self.assertEqual(summary["changed_operation_counts"], {"encourage_score": 1})
        self.assertEqual(
            summary["predicate_counts"],
            {"seen_bench_revealed_rapid_spin": 1},
        )
        self.assertEqual(
            summary["predicate_outcome_counts"],
            {"seen_bench_revealed_rapid_spin:found": 1},
        )
        self.assertEqual(summary["predicate_public_input_snapshot_count"], 1)
        self.assertEqual(summary["public_read_probe_entry_count"], 1)
        self.assertEqual(summary["public_read_probe_snapshot_count"], 1)
        self.assertEqual(
            summary["public_read_probe_counts"],
            {"active_revealed_rapid_spin": 1},
        )
        self.assertEqual(
            summary["public_read_probe_outcome_counts"],
            {"active_revealed_rapid_spin:not_revealed_for_layer2": 1},
        )

    def test_parse_memory_patch_supports_symbol_offsets_and_hex_values(self) -> None:
        patch = parse_memory_patch("wPlayerUsedMoves+2=0xe5")

        self.assertEqual(patch.symbol_name, "wPlayerUsedMoves")
        self.assertEqual(patch.offset, 2)
        self.assertEqual(patch.value, 0xE5)

    def test_parse_delayed_memory_patch_supports_hook_symbol(self) -> None:
        delayed = parse_delayed_memory_patch(
            "BossAI_GetSwitchThreshold:wBossAISwitchConfidence=0x00"
        )

        self.assertEqual(delayed.hook_symbol, "BossAI_GetSwitchThreshold")
        self.assertEqual(delayed.patch.symbol_name, "wBossAISwitchConfidence")
        self.assertEqual(delayed.patch.offset, 0)
        self.assertEqual(delayed.patch.value, 0)


if __name__ == "__main__":
    unittest.main()
