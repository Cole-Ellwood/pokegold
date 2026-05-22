from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.when_wrote import run_when_wrote


def _golden_effect_trace_with_writer_at_d141() -> dict[str, object]:
    """Synthetic effect trace where a single bank-0x01 write to D141 occurs at
    seq=4 with pc 01:5A00 labeled BattleCommand_DamageCalc+6.

    This is the AG-NN-shape: a clobber to wCurDamage (01:D141) from inside the
    damage-calc function. The when-wrote query should pull this writer back
    with proof_status=instruction_observed and exact bank-key match.
    """

    key = "wramx:01:D141"
    return {
        "schema_version": 1,
        "kind": "unified_debugger_effect_trace",
        "valid": True,
        "proof_status": "instruction_observed",
        "write_index": [
            {
                "address": "D141",
                "address_key": key,
                "space": "wramx",
                "bank": 1,
                "write_count": 1,
                "last_writer_seq": 4,
                "last_writer_pc": "01:5A00",
                "last_value_hex": "2A",
            }
        ],
        "events": [
            {
                "seq": 4,
                "trace_source": "ag_nn_golden.jsonl",
                "pc_bank_address": "01:5A00",
                "pc_label": "BattleCommand_DamageCalc+6",
                "pre_registers": {"A": 0x2A},
                "bank_state": {"wram": 1},
                "bank_state_sources": {"wram": "bank_state.wram"},
                "effects": [
                    {
                        "access": "write",
                        "kind": "memory_write",
                        "operation": "ld [hl], a",
                        "address_hex": "D141",
                        "address_key": key,
                        "value_hex": "2A",
                        "value_source": "A",
                        "bank": 1,
                        "bank_source": "bank_state.wram",
                        "space": "wramx",
                        "post_value_hex": "2A",
                        "post_value_status": "matched",
                        "post_observed_seq": 5,
                        "post_observed_pc": "01:5A03",
                        "proof_status": "instruction_observed",
                    }
                ],
            }
        ],
    }


class WhenWroteCoreTests(unittest.TestCase):
    def _store_effect(self, root: Path, trace: dict[str, object]) -> None:
        (root / "pokegold.sym").write_text("01:5A00 BattleCommand_DamageCalc\n", encoding="utf-8")
        (root / "effect.json").write_text(json.dumps(trace), encoding="utf-8")

    def test_returns_concrete_observed_writer_for_banked_address(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store_effect(root, _golden_effect_trace_with_writer_at_d141())

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                root=root,
            )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["answer_count"], 1)
        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "instruction_observed")
        writer = answer["last_writer"]
        self.assertEqual(writer.get("seq"), 4)
        self.assertEqual(writer.get("pc"), "01:5A00")
        self.assertEqual(writer.get("pc_label"), "BattleCommand_DamageCalc+6")
        self.assertEqual(writer.get("value_hex"), "2A")
        self.assertEqual(answer["address_key"], "wramx:01:D141")

    def test_since_symbol_anchor_filters_pre_anchor_writer(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = _golden_effect_trace_with_writer_at_d141()
            trace["events"][0]["pc_label"] = "SomeOtherFunction+10"
            self._store_effect(root, trace)

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                since_symbol="BattleCommand_DamageCalc",
                root=root,
            )

        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "planned_only")
        self.assertEqual(answer["last_writer"], {})
        self.assertEqual(
            answer["proof_downgrade_reason"], "writer_pc_does_not_match_since_symbol"
        )

    def test_since_frame_anchor_filters_pre_anchor_writer(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store_effect(root, _golden_effect_trace_with_writer_at_d141())

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                since_frame=10,
                root=root,
            )

        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "planned_only")
        self.assertEqual(answer["last_writer"], {})
        self.assertEqual(
            answer["proof_downgrade_reason"], "writer_seq_before_since_frame"
        )

    def test_since_frame_anchor_filters_seq_zero_writer(self) -> None:
        """Codex revision (P2 review): the old guard `if writer_seq and ...`
        short-circuited on seq=0 and let a legitimate frame-0 writer through.
        The fix uses an explicit known/unknown branch."""

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = _golden_effect_trace_with_writer_at_d141()
            trace["write_index"][0]["last_writer_seq"] = 0
            trace["events"][0]["seq"] = 0
            self._store_effect(root, trace)

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                since_frame=10,
                root=root,
            )

        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "planned_only")
        self.assertEqual(answer["last_writer"], {})
        self.assertEqual(
            answer["proof_downgrade_reason"], "writer_seq_before_since_frame"
        )

    def test_since_symbol_anchor_fails_closed_on_missing_pc_label(self) -> None:
        """Codex revision (P2 review): a writer with no pc_label cannot
        satisfy a requested since_symbol anchor. The fix downgrades with
        writer_pc_label_missing_for_since_symbol so the answer states
        WHY it failed instead of silently passing the writer through."""

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = _golden_effect_trace_with_writer_at_d141()
            trace["events"][0].pop("pc_label", None)
            self._store_effect(root, trace)

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                since_symbol="BattleCommand_DamageCalc",
                root=root,
            )

        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "planned_only")
        self.assertEqual(answer["last_writer"], {})
        self.assertEqual(
            answer["proof_downgrade_reason"],
            "writer_pc_label_missing_for_since_symbol",
        )


class WhenWroteBankExactnessTests(unittest.TestCase):
    """Per the P0 proof boundary: banked targets must NOT fall back to
    bus-address matching against the wrong bank's writer."""

    def test_refuses_bus_address_fallback_for_banked_target(self) -> None:
        """Trace has a bank-2 writer to D141; when-wrote asked for bank-1 D141.
        The answer must NOT return the bank-2 writer as a confirmed write.
        Two valid behaviors satisfy the P0 proof boundary: either return zero
        answers (no target match at all), or return an answer whose proof_status
        is not promoted to instruction_observed."""

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            bank2_trace = _golden_effect_trace_with_writer_at_d141()
            bank2_trace["write_index"][0]["bank"] = 2
            bank2_trace["write_index"][0]["address_key"] = "wramx:02:D141"
            event = bank2_trace["events"][0]
            event["bank_state"] = {"wram": 2}
            effect = event["effects"][0]
            effect["bank"] = 2
            effect["address_key"] = "wramx:02:D141"

            (root / "pokegold.sym").write_text("", encoding="utf-8")
            (root / "effect.json").write_text(json.dumps(bank2_trace), encoding="utf-8")

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                root=root,
            )

        # Either no answer at all, or an answer whose writer is not
        # promoted to instruction_observed (proof-boundary preserved).
        if not report["answers"]:
            return
        answer = report["answers"][0]
        self.assertNotEqual(
            answer["proof_status"],
            "instruction_observed",
            f"banked target must not fall back to bus-address bank-2 writer; got {answer}",
        )


class WhenWroteGoldenLivedBugSmokeTests(unittest.TestCase):
    """Rule-#11 golden lived-bug smoke for the AG-NN class.

    The bug class this query exists to collapse: agent sees "physical damage
    5x too high in wild encounters" and needs to know who last wrote D141
    before BattleCommand_DamageCalc returned. Today: 4+ iterations of
    hand-rolled watch + re-run + grep. With when-wrote: one command.
    """

    def test_ag_nn_class_golden_smoke(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pokegold.sym").write_text(
                "01:5A00 BattleCommand_DamageCalc\n",
                encoding="utf-8",
            )
            (root / "effect.json").write_text(
                json.dumps(_golden_effect_trace_with_writer_at_d141()),
                encoding="utf-8",
            )

            report = run_when_wrote(
                addresses=("01:D141",),
                reports=("effect.json",),
                since_symbol="BattleCommand_DamageCalc",
                root=root,
            )

        self.assertTrue(report["valid"], report)
        answer = report["answers"][0]
        self.assertEqual(answer["proof_status"], "instruction_observed")
        writer = answer["last_writer"]
        self.assertEqual(writer.get("pc_label"), "BattleCommand_DamageCalc+6")
        self.assertEqual(writer.get("pc"), "01:5A00")
        self.assertEqual(writer.get("value_hex"), "2A")
        self.assertEqual(answer["address_key"], "wramx:01:D141")


if __name__ == "__main__":
    unittest.main()
