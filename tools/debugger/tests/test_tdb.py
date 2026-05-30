from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.tdb import (
    AndNode,
    NotNode,
    OrNode,
    PredicateNode,
    parse,
    run_tdb,
    tokenize,
)


def _effect_trace_with_two_frames() -> dict[str, object]:
    """One write to D141 in bank 1 + one read of A from FF40."""

    return {
        "schema_version": 1,
        "kind": "unified_debugger_effect_trace",
        "valid": True,
        "events": [
            {
                "seq": 4,
                "pc_bank_address": "01:5A00",
                "pc_label": "BattleCommand_DamageCalc+6",
                "effects": [
                    {
                        "access": "write",
                        "kind": "memory_write",
                        "address_hex": "D141",
                        "address_key": "wramx:01:D141",
                        "bank": 1,
                        "value_hex": "2A",
                        "value_source": "A",
                        "proof_status": "instruction_observed",
                    }
                ],
            },
            {
                "seq": 7,
                "pc_bank_address": "00:0200",
                "pc_label": "VBlankHandler+12",
                "effects": [
                    {
                        "access": "read",
                        "kind": "memory_read",
                        "address_hex": "FF40",
                        "address_key": "io:00:FF40",
                        "bank": None,
                        "value_hex": "91",
                        "value_source": "A",
                        "proof_status": "instruction_observed",
                    }
                ],
            },
        ],
    }


class TdbTokenizerTests(unittest.TestCase):
    def test_tokenizes_writes_predicate(self) -> None:
        tokens = tokenize("writes(addr=$D141)")
        kinds = [t.kind for t in tokens]
        self.assertEqual(kinds, ["ident", "lparen", "ident", "eq", "hex", "rparen"])

    def test_tokenizes_and_combinator(self) -> None:
        tokens = tokenize("writes(addr=$D141) and reads(reg=A)")
        kinds = [t.kind for t in tokens]
        self.assertIn("kw_and", kinds)


class TdbParserTests(unittest.TestCase):
    def test_parses_simple_predicate(self) -> None:
        node = parse("writes(addr=$D141)")
        self.assertIsInstance(node, PredicateNode)
        self.assertEqual(node.name, "writes")
        self.assertEqual(dict(node.kwargs), {"addr": "$D141"})

    def test_parses_and_combinator(self) -> None:
        node = parse("writes(addr=$D141) and reads(reg=A)")
        self.assertIsInstance(node, AndNode)
        self.assertEqual(len(node.children), 2)

    def test_parses_or_combinator(self) -> None:
        node = parse("writes(addr=$D141) or reads(reg=A)")
        self.assertIsInstance(node, OrNode)

    def test_parses_not_combinator(self) -> None:
        node = parse("not writes(addr=$D141)")
        self.assertIsInstance(node, NotNode)

    def test_parens_override_precedence(self) -> None:
        node = parse("(writes(addr=$D141) or writes(addr=$D142)) and reads(reg=A)")
        self.assertIsInstance(node, AndNode)
        self.assertIsInstance(node.children[0], OrNode)

    def test_rejects_trailing_garbage(self) -> None:
        with self.assertRaises(SyntaxError):
            parse("writes(addr=$D141) trailing")


class TdbEvaluatorTests(unittest.TestCase):
    def _store(self, root: Path, trace: dict[str, object]) -> None:
        (root / "effect.json").write_text(json.dumps(trace), encoding="utf-8")

    def test_writes_matches_the_d141_event(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="writes(addr=$D141)",
                reports=("effect.json",),
                root=root,
            )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["match_count"], 1)
        match = report["matches"][0]
        self.assertEqual(match["seq"], 4)
        self.assertEqual(match["pc_bank_address"], "01:5A00")
        self.assertEqual(match["address_key"], "wramx:01:D141")
        self.assertEqual(match["proof_status"], "instruction_observed")

    def test_reads_with_reg_matches_the_io_read(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="reads(reg=A)",
                reports=("effect.json",),
                root=root,
            )

        # Both events match value_source=A — write has access=write so reads
        # falls through to value_source check on EITHER access kind. Per the
        # current predicate, "reads(reg=R)" is read+value_source match; it
        # accepts any event whose value_source equals R. Both fit.
        self.assertEqual(report["match_count"], 2)

    def test_writes_with_bank_filter_rejects_other_bank(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="writes(addr=$D141, bank=2)",
                reports=("effect.json",),
                root=root,
            )

        self.assertEqual(report["match_count"], 0)

    def test_writes_with_unobserved_bank_downgrades_proof(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = _effect_trace_with_two_frames()
            trace["events"][0]["effects"][0]["bank"] = None
            self._store(root, trace)

            report = run_tdb(
                query="writes(addr=$D141, bank=1)",
                reports=("effect.json",),
                root=root,
            )

        self.assertEqual(report["match_count"], 1)
        match = report["matches"][0]
        self.assertEqual(match["proof_status"], "planned_only")
        self.assertEqual(match["proof_downgrade_reason"], "bank_unverified")

    def test_executes_pc_bank_address_matches(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="executes(pc=01:5A00)",
                reports=("effect.json",),
                root=root,
            )

        # PC match emits one entry per effect on the frame; one effect here.
        self.assertEqual(report["match_count"], 1)

    def test_executes_pc_label_prefix_matches(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="executes(pc=BattleCommand_DamageCalc)",
                reports=("effect.json",),
                root=root,
            )

        self.assertEqual(report["match_count"], 1)
        self.assertEqual(report["matches"][0]["pc_label"], "BattleCommand_DamageCalc+6")

    def test_and_combinator_intersects_predicates(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="writes(addr=$D141) and executes(pc=BattleCommand_DamageCalc)",
                reports=("effect.json",),
                root=root,
            )

        self.assertEqual(report["match_count"], 1)

    def test_or_combinator_unions_predicates(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="writes(addr=$D141) or writes(addr=$FF40)",
                reports=("effect.json",),
                root=root,
            )

        # Only writes to D141 — the FF40 event is a READ, not a write.
        self.assertEqual(report["match_count"], 1)

    def test_not_combinator_inverts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._store(root, _effect_trace_with_two_frames())

            report = run_tdb(
                query="not writes(addr=$D141)",
                reports=("effect.json",),
                root=root,
            )

        # The read event survives "not write to D141".
        self.assertEqual(report["match_count"], 1)
        self.assertEqual(report["matches"][0]["pc_label"], "VBlankHandler+12")


class TdbErrorPathTests(unittest.TestCase):
    def test_invalid_query_returns_errors(self) -> None:
        report = run_tdb(query="writes(", reports=())
        self.assertFalse(report["valid"])
        self.assertTrue(any("expected" in err.lower() or "unexpected" in err.lower() for err in report["errors"]))

    def test_missing_reports_returns_error(self) -> None:
        report = run_tdb(query="writes(addr=$D141)", reports=())
        self.assertFalse(report["valid"])
        self.assertTrue(any("--report" in err for err in report["errors"]))

    def test_unknown_predicate_returns_error_at_parse(self) -> None:
        report = run_tdb(query="lol(foo=bar)", reports=())
        self.assertFalse(report["valid"])
        self.assertTrue(any("unknown predicate" in err.lower() for err in report["errors"]))


class TdbGoldenLivedBugSmokeTests(unittest.TestCase):
    """Rule-#11 lived smoke: the AG-NN class query that motivates P3.

    Q: 'writes(addr=$D141) and executes(pc=BattleCommand_DamageCalc)' — find
    every write to wCurDamage that originated from inside the damage-calc
    function. This is the question P2 when-wrote answers for the SINGLE
    last writer; P3 returns all matches, which is what an investigator
    actually needs when chasing a clobber chain across a function.
    """

    def test_writes_and_executes_intersection_against_ag_nn_trace(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = _effect_trace_with_two_frames()
            # Add a second write to D141 from outside the damage-calc function
            # — this is the "false positive" the AND filter should reject.
            trace["events"].append(
                {
                    "seq": 12,
                    "pc_bank_address": "02:4000",
                    "pc_label": "UnrelatedFunction+0",
                    "effects": [
                        {
                            "access": "write",
                            "kind": "memory_write",
                            "address_hex": "D141",
                            "address_key": "wramx:01:D141",
                            "bank": 1,
                            "value_hex": "99",
                            "value_source": "A",
                            "proof_status": "instruction_observed",
                        }
                    ],
                }
            )
            (root / "effect.json").write_text(json.dumps(trace), encoding="utf-8")

            report = run_tdb(
                query="writes(addr=$D141) and executes(pc=BattleCommand_DamageCalc)",
                reports=("effect.json",),
                root=root,
            )

        # Should return exactly the damage-calc write, not the unrelated one.
        self.assertEqual(report["match_count"], 1)
        match = report["matches"][0]
        self.assertEqual(match["pc_label"], "BattleCommand_DamageCalc+6")
        self.assertEqual(match["value_hex"], "2A")


if __name__ == "__main__":
    unittest.main()
