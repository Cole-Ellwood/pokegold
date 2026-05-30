from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tools.debugger.register_flow import (
    KIND,
    SCHEMA_VERSION,
    analyze_function,
    classify_control,
    find_function,
    main,
    render_text,
    writes_for_instruction,
)


class WritesForInstructionTests(unittest.TestCase):
    def test_ld_writes_destination_register(self) -> None:
        # `ld a, [hl]` reads memory at hl into a -- hl is unchanged. Only
        # the HLI/HLD variants modify hl. This distinction is load-bearing:
        # over-reporting hl as clobbered on every `ld a, [hl]` would
        # generate massive false positives in the battle engine.
        self.assertEqual(writes_for_instruction("ld a, [hl]"), ("a",))
        self.assertEqual(writes_for_instruction("ld b, 5"), ("b",))
        self.assertEqual(writes_for_instruction("ld c, a"), ("c",))

    def test_ld_pair_writes_both_halves(self) -> None:
        self.assertEqual(writes_for_instruction("ld bc, 0"), ("b", "c"))
        self.assertEqual(writes_for_instruction("ld de, wEnemyMonItem"), ("d", "e"))
        self.assertEqual(writes_for_instruction("ld hl, wBattleMonItem"), ("h", "l"))

    def test_pop_pair_writes_both_halves(self) -> None:
        self.assertEqual(writes_for_instruction("pop bc"), ("b", "c"))
        self.assertEqual(writes_for_instruction("pop de"), ("d", "e"))
        self.assertEqual(writes_for_instruction("pop hl"), ("h", "l"))
        self.assertEqual(writes_for_instruction("pop af"), ("a",))

    def test_inc_dec_pair_writes_both_halves(self) -> None:
        self.assertEqual(writes_for_instruction("inc bc"), ("b", "c"))
        self.assertEqual(writes_for_instruction("dec hl"), ("h", "l"))

    def test_xor_a_writes_a_to_zero(self) -> None:
        self.assertEqual(writes_for_instruction("xor a"), ("a",))

    def test_and_a_is_flag_test_only(self) -> None:
        # `and a` is the idiomatic flag-test (a is unchanged, flags updated).
        # The codebase uses it before conditional ret/jr, so it must NOT
        # be flagged as writing a -- otherwise the analyzer would over-
        # report clobbers for half the conditional ret prologues in the
        # battle engine.
        self.assertEqual(writes_for_instruction("and a"), ())

    def test_alu_ops_write_accumulator(self) -> None:
        self.assertEqual(writes_for_instruction("add b"), ("a",))
        self.assertEqual(writes_for_instruction("adc a, c"), ("a",))
        self.assertEqual(writes_for_instruction("sub d"), ("a",))
        self.assertEqual(writes_for_instruction("or e"), ("a",))

    def test_add_hl_writes_h_and_l(self) -> None:
        self.assertEqual(writes_for_instruction("add hl, bc"), ("h", "l"))

    def test_hli_load_writes_a_and_hl(self) -> None:
        self.assertEqual(writes_for_instruction("ld a, [hli]"), ("a", "h", "l"))
        self.assertEqual(writes_for_instruction("ld [hld], a"), ("h", "l"))

    def test_ldh_a_writes_a(self) -> None:
        self.assertEqual(writes_for_instruction("ldh a, [hBattleTurn]"), ("a",))

    def test_ldh_to_memory_does_not_write_a(self) -> None:
        # ldh [n], a stores a to HRAM -- does not write a register.
        self.assertEqual(writes_for_instruction("ldh [hBattleTurn], a"), ())

    def test_cp_is_flag_only(self) -> None:
        # cp computes a - X but does not write a; only flags.
        self.assertEqual(writes_for_instruction("cp 5"), ())
        self.assertEqual(writes_for_instruction("cp b"), ())

    def test_rotate_writes_target(self) -> None:
        self.assertEqual(writes_for_instruction("rl c"), ("c",))
        self.assertEqual(writes_for_instruction("srl b"), ("b",))
        self.assertEqual(writes_for_instruction("rla"), ("a",))

    def test_set_res_write_target(self) -> None:
        self.assertEqual(writes_for_instruction("set 3, e"), ("e",))
        self.assertEqual(writes_for_instruction("res 0, l"), ("l",))

    def test_empty_input_returns_empty_tuple(self) -> None:
        self.assertEqual(writes_for_instruction(""), ())

    def test_unknown_instruction_returns_empty_tuple(self) -> None:
        self.assertEqual(writes_for_instruction("nop"), ())
        self.assertEqual(writes_for_instruction("halt"), ())


class ClassifyControlTests(unittest.TestCase):
    def test_call_classified_with_target(self) -> None:
        result = classify_control("call Foo")
        self.assertEqual(result["kind"], "call")
        self.assertEqual(result["target"], "Foo")

    def test_conditional_call_classified_with_target(self) -> None:
        result = classify_control("call nz, Foo")
        self.assertEqual(result["kind"], "call_cond")
        self.assertEqual(result["condition"], "nz")
        self.assertEqual(result["target"], "Foo")

    def test_farcall_classified_with_target(self) -> None:
        result = classify_control("farcall TypePassive_GetEffectiveMoveCategory_Far")
        self.assertEqual(result["kind"], "farcall")
        self.assertEqual(result["target"], "TypePassive_GetEffectiveMoveCategory_Far")

    def test_jp_unconditional_tail_classified(self) -> None:
        result = classify_control("jp GetItemHeldEffect")
        self.assertEqual(result["kind"], "jp_unconditional")
        self.assertEqual(result["target"], "GetItemHeldEffect")

    def test_jp_hl_is_opaque(self) -> None:
        result = classify_control("jp [hl]")
        self.assertEqual(result["kind"], "jp_opaque")
        self.assertEqual(result["target"], "[hl]")
        self.assertTrue(result["opaque"])

    def test_jr_conditional_classified(self) -> None:
        result = classify_control("jr z, .skip")
        self.assertEqual(result["kind"], "jr_cond")
        self.assertEqual(result["condition"], "z")
        self.assertEqual(result["target"], ".skip")

    def test_ret_classified(self) -> None:
        self.assertEqual(classify_control("ret")["kind"], "ret")
        cond = classify_control("ret z")
        self.assertEqual(cond["kind"], "ret_cond")
        self.assertEqual(cond["condition"], "z")

    def test_non_control_returns_none(self) -> None:
        self.assertIsNone(classify_control("ld a, b"))
        self.assertIsNone(classify_control(""))


def _write_fixture_asm(tmp_root: Path, *, relative: str, content: str) -> None:
    target = tmp_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


class FindFunctionTests(unittest.TestCase):
    def test_returns_none_when_symbol_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="OtherFn:\n\tret\n",
            )
            self.assertIsNone(find_function("MissingFn", root=root))

    def test_returns_first_top_level_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content=(
                    "FirstFn:\n"
                    "\tld a, 1\n"
                    "\tret\n"
                    "\n"
                    "SecondFn::\n"
                    "\tld b, 2\n"
                    "\tret\n"
                ),
            )
            location = find_function("FirstFn", root=root)
            self.assertIsNotNone(location)
            self.assertEqual(location.symbol, "FirstFn")
            self.assertEqual(location.start_line, 1)
            self.assertIn("ld a, 1", location.body[0])
            self.assertNotIn(
                "ld b, 2", " ".join(location.body),
                "body should stop before the next top-level label",
            )


class AnalyzeFunctionSyntheticTests(unittest.TestCase):
    def test_get_user_item_shape_matches_real_function(self) -> None:
        # Synthetic copy of the real GetUserItem (engine/battle/effect_commands.asm:6415).
        # This is the canonical AG-NN-class function: push de + ld de, *
        # is bracketed by pop de, then ld b, [hl] writes b, then jp tail.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/battle/example.asm",
                content=(
                    "GetUserItem:\n"
                    "\tpush de\n"
                    "\tld hl, wBattleMonItem\n"
                    "\tld de, wEnemyMonItem\n"
                    "\tcall _GetSidedHL\n"
                    "\tpop de\n"
                    "\tld b, [hl]\n"
                    "\tjp GetItemHeldEffect\n"
                ),
            )
            report = analyze_function("GetUserItem", root=root)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["schema_version"], SCHEMA_VERSION)
        self.assertEqual(report["kind"], KIND)
        self.assertEqual(report["clobber_set"], ["b", "d", "e", "h", "l"])

        # de is written between push/pop and that pair should be tracked.
        self.assertEqual(len(report["push_pop_pairs"]), 1)
        self.assertEqual(report["push_pop_pairs"][0]["register_pair"], "de")

        # One in-bank call (to _GetSidedHL).
        self.assertEqual(len(report["calls"]), 1)
        self.assertEqual(report["calls"][0]["kind"], "call")
        self.assertEqual(report["calls"][0]["target"], "_GetSidedHL")

        # One tail branch (unconditional jp GetItemHeldEffect).
        self.assertEqual(len(report["branches"]), 1)
        self.assertEqual(report["branches"][0]["kind"], "jp_unconditional")
        self.assertEqual(report["branches"][0]["target"], "GetItemHeldEffect")

        # No explicit ret -- the tail jp serves as exit. Warning should
        # NOT fire because the unconditional jp is the exit.
        self.assertEqual(report["rets"], [])
        self.assertNotIn(
            "may be fall-through to next label",
            " ".join(report["warnings"]),
        )

    def test_unmatched_pop_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="LonelyPop:\n\tpop bc\n\tret\n",
            )
            report = analyze_function("LonelyPop", root=root)

        self.assertTrue(report["valid"])
        self.assertTrue(
            any("no matching push" in warning for warning in report["warnings"]),
            report["warnings"],
        )
        # pop bc still records the writes to b and c.
        self.assertIn("b", report["clobber_set"])
        self.assertIn("c", report["clobber_set"])

    def test_unmatched_push_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="LonelyPush:\n\tpush bc\n\tret\n",
            )
            report = analyze_function("LonelyPush", root=root)

        self.assertTrue(report["valid"])
        self.assertTrue(
            any("no matching pop" in warning for warning in report["warnings"]),
            report["warnings"],
        )

    def test_fall_through_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="FallThrough:\n\tld a, 1\n",
            )
            report = analyze_function("FallThrough", root=root)

        self.assertTrue(report["valid"])
        self.assertTrue(
            any(
                "fall-through" in warning for warning in report["warnings"]
            ),
            report["warnings"],
        )

    def test_local_labels_are_skipped(self) -> None:
        # Local labels (`.skip:`) are branch targets, not instructions.
        # The analyzer should skip them rather than try to match them
        # against the instruction regexes.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content=(
                    "WithLocal:\n"
                    "\tand a\n"
                    "\tjr z, .skip\n"
                    "\tld a, 1\n"
                    ".skip\n"
                    "\tret\n"
                ),
            )
            report = analyze_function("WithLocal", root=root)
        self.assertTrue(report["valid"])
        self.assertEqual(report["clobber_set"], ["a"])

    def test_missing_symbol_returns_invalid_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="SomeFn:\n\tret\n",
            )
            report = analyze_function("DoesNotExist", root=root)
        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])

    def test_opaque_jp_hl_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="DispatchTail:\n\tjp [hl]\n",
            )
            report = analyze_function("DispatchTail", root=root)
        self.assertTrue(report["valid"])
        self.assertEqual(report["branches"][0]["kind"], "jp_opaque")
        self.assertTrue(
            any("opaque branch" in warning for warning in report["warnings"]),
            report["warnings"],
        )
        self.assertFalse(
            any("fall-through" in warning for warning in report["warnings"]),
            report["warnings"],
        )


class RenderTextTests(unittest.TestCase):
    def test_renders_invalid_report_with_error(self) -> None:
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "valid": False,
            "symbol": "X",
            "errors": ["no match"],
        }
        text = render_text(report)
        self.assertIn("INVALID", text)
        self.assertIn("no match", text)

    def test_renders_summary_with_clobbers(self) -> None:
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "valid": True,
            "symbol": "GetUserItem",
            "path": "engine/battle/example.asm",
            "start_line": 1,
            "body_lines": 7,
            "clobber_set": ["b", "d", "e", "h", "l"],
            "direct_writes": {
                "b": [{"line": 7, "instruction": "ld b, [hl]"}],
            },
            "calls": [{"line": 5, "kind": "call", "target": "_GetSidedHL", "instruction": "call _GetSidedHL"}],
            "branches": [{"line": 8, "kind": "jp_unconditional", "target": "GetItemHeldEffect", "instruction": "jp GetItemHeldEffect"}],
            "rets": [],
            "push_pop_pairs": [{"register_pair": "de", "push_line": 2, "pop_line": 6}],
            "warnings": [],
            "errors": [],
        }
        text = render_text(report)
        self.assertIn("GetUserItem", text)
        self.assertIn("clobber set: b, d, e, h, l", text)
        self.assertIn("call _GetSidedHL", text)
        # Render shows raw instruction for branches, not the analyzer's
        # internal kind tag. (kind is JSON-only for tooling.)
        self.assertIn("jp GetItemHeldEffect", text)
        self.assertIn("de: push @ line 2 -> pop @ line 6", text)


class MainCliTests(unittest.TestCase):
    def test_json_flag_emits_report_dict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fixture_asm(
                root,
                relative="engine/example.asm",
                content="SmallFn:\n\tld a, 1\n\tret\n",
            )
            # We can't easily inject root via CLI; use analyze_function
            # directly to assert the shape, and check the CLI exit code
            # via a missing-symbol invocation against the real repo (we
            # use a deliberately unlikely name).
        buffer = StringIO()
        with redirect_stdout(buffer):
            code = main(["--symbol", "ZZZ_no_such_symbol_should_exist_anywhere_in_repo", "--json"])
        self.assertEqual(code, 1)
        payload = json.loads(buffer.getvalue())
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["symbol"], "ZZZ_no_such_symbol_should_exist_anywhere_in_repo")


if __name__ == "__main__":
    unittest.main()
