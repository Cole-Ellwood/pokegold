from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from tools.boss_ai_debugger.rom_contribution_trace import (
    drive_replay_to_choice,
    HookTarget,
    MemoryPatch,
    replay_tick_count,
    RomContributionTracer,
    RuleFrame,
    build_report,
    format_rom_contribution_trace,
    parse_memory_patch,
    should_issue_replay_button,
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
    def __init__(self, *, chosen_at_frame: int) -> None:
        self.frame = 0
        self.chosen_at_frame = chosen_at_frame
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


class RomContributionTraceTests(unittest.TestCase):
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

    def test_rule_hook_records_dynamic_rule_entry_separate_from_score_events(self) -> None:
        pyboy = FakePyBoy()
        pyboy.memory[1, 0xD768] = 0xD0
        pyboy.memory[1, 0xD769] = 0xD3
        pyboy.memory[1, 0xD0D3] = 20
        pyboy.memory[1, 0xD100] = 57
        pyboy.register_file.SP = 0xFEF0
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

    def test_public_input_snapshot_records_byte_party_and_static_inputs(self) -> None:
        pyboy = FakePyBoy()
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
        tracer = RomContributionTracer(
            pyboy,
            {
                "wPlayerUsedMoves": Symbol(0, 0xCBE8),
                "wOTPartySpecies": Symbol(1, 0xDD56),
                "wOTPartyMon1HP": Symbol(1, 0xDD7F),
                "BaseData": Symbol(0x14, 0x5AB9),
                "EvosAttacksPointers": Symbol(0x10, 0x685C),
            },
            FakeSymbolIndex(),
            {},
        )

        snapshot = tracer.public_input_snapshot(
            (
                "wPlayerUsedMoves",
                "wOTPartySpecies",
                "wOTPartyMon1HP",
                "BaseData",
                "EvosAttacks",
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
        self.assertEqual(snapshot["BaseData"]["kind"], "static_table_reference")
        self.assertEqual(snapshot["EvosAttacks"]["symbol"], "EvosAttacksPointers")
        self.assertFalse(snapshot["MissingPublicInput"]["available"])

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
            selector_entry_scores=[19, 20, 20, 20],
            move_names={1: "TEST"},
            memory_patches=[],
        )
        events.clear()

        self.assertEqual(report["event_count"], 1)
        self.assertEqual(len(report["events"]), 1)

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
                "move.rule_entry_only",
            ],
        )
        self.assertEqual(summary["changed_rule_ids"], ["move.changed_rule"])
        self.assertEqual(summary["executed_rule_count"], 4)
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

    def test_parse_memory_patch_supports_symbol_offsets_and_hex_values(self) -> None:
        patch = parse_memory_patch("wPlayerUsedMoves+2=0xe5")

        self.assertEqual(patch.symbol_name, "wPlayerUsedMoves")
        self.assertEqual(patch.offset, 2)
        self.assertEqual(patch.value, 0xE5)


if __name__ == "__main__":
    unittest.main()
