from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from tools.trace import boss_ai_trace_capture as capture
from tools.trace.boss_ai_trace_capture import (
    Symbol,
    build_trace_basis_metadata,
    csv_bytes,
    csv_score_deltas,
    decode_move,
    decode_risk_flags,
    format_addr,
    format_capture,
    format_metadata_lines,
    format_symbols,
    has_completed_move_decision,
    has_decision_values,
    hex_bytes,
    parse_move_names,
    require_symbols,
    trace_signature,
)


def _make_trace_values(**overrides) -> dict[str, list[int]]:
    """Return a complete capture-values dict with all-zero defaults plus overrides."""
    base = {
        "wBossAITraceTopMoves": [0, 0, 0],
        "wBossAITraceTopScores": [0, 0, 0],
        "wBossAITracePreModelScores": [0, 0, 0, 0],
        "wBossAITracePostModelScores": [0, 0, 0, 0],
        "wBossAITraceChosenMove": [0],
        "wBossAITraceSwitchConfidence": [0],
        "wBossAITracePlanId": [0],
        "wBossAITracePlanPhase": [0],
        "wBossAITracePlanConfidence": [0],
        "wBossAITracePlausibleMask": [0, 0, 0, 0],
        "wBossAITraceRiskFlags": [0],
        "wBossAITraceLookaheadBonusTop": [0, 0, 0],
        "wBossAIRevealedMovesBitmap": [0] * 24,
        "wBossAITier": [0],
        "wEnemyMonMoves": [0, 0, 0, 0],
        "wEnemyAIMoveScores": [0, 0, 0, 0],
        "wCurEnemyMoveNum": [0],
        "wCurEnemyMove": [0],
        "wEnemySwitchMonParam": [0],
        "wEnemySwitchMonIndex": [0],
        "wBossAILastSwitchedOut": [0],
        "wBossAISwitchCooldown": [0],
        "wCurOTMon": [0],
    }
    base.update(overrides)
    return base


class FormatAddrTests(unittest.TestCase):
    def test_format_is_two_digit_bank_colon_four_digit_address(self) -> None:
        self.assertEqual(format_addr(Symbol(0, 0x0150)), "00:0150")
        self.assertEqual(format_addr(Symbol(0x0A, 0xD200)), "0a:d200")
        self.assertEqual(format_addr(Symbol(0xFF, 0xFFFF)), "ff:ffff")


class HexAndCsvBytesTests(unittest.TestCase):
    def test_hex_bytes_lowercase_space_separated(self) -> None:
        self.assertEqual(hex_bytes([0xAB, 0x01, 0xFF]), "ab 01 ff")

    def test_hex_bytes_empty_list_returns_empty_string(self) -> None:
        self.assertEqual(hex_bytes([]), "")

    def test_csv_bytes_decimal_comma_separated(self) -> None:
        self.assertEqual(csv_bytes([20, 21, 255]), "20,21,255")

    def test_csv_bytes_empty_list_returns_empty_string(self) -> None:
        self.assertEqual(csv_bytes([]), "")


class CsvScoreDeltasTests(unittest.TestCase):
    def test_signed_deltas_include_plus_for_zero_and_positive(self) -> None:
        self.assertEqual(
            csv_score_deltas([20, 20, 80], [14, 21, 80]),
            "-6,+1,+0",
        )

    def test_ff_sentinel_in_either_input_maps_to_na(self) -> None:
        self.assertEqual(
            csv_score_deltas([20, 0xFF, 0xFF, 50], [21, 0, 0xFF, 0xFF]),
            "+1,na,na,na",
        )

    def test_mixed_lengths_truncate_to_shortest(self) -> None:
        # `zip` semantics; documents current behavior so future drift is caught.
        self.assertEqual(csv_score_deltas([1, 2, 3], [10, 20]), "+9,+18")


class DecodeMoveTests(unittest.TestCase):
    def test_known_id_returns_name(self) -> None:
        names = {1: "POUND", 2: "KARATE_CHOP"}
        self.assertEqual(decode_move(1, names), "POUND")

    def test_unknown_id_falls_back_to_hashed_hex(self) -> None:
        self.assertEqual(decode_move(0xAB, {}), "#ab")

    def test_zero_id_with_empty_names_uses_hashed_hex(self) -> None:
        # `decode_move` treats falsy `name` as "missing", which includes
        # both unmapped ids and an explicit empty-string mapping.
        self.assertEqual(decode_move(0, {}), "#00")


class DecodeRiskFlagsTests(unittest.TestCase):
    def test_no_flags_returns_none(self) -> None:
        self.assertEqual(decode_risk_flags(0), "none")

    def test_single_flag_returns_label(self) -> None:
        self.assertEqual(decode_risk_flags(1 << 0), "plausible-risk-or-scout-trigger")
        self.assertEqual(decode_risk_flags(1 << 3), "haki-oracle-fired")

    def test_multiple_flags_are_comma_joined_in_bit_order(self) -> None:
        value = (1 << 0) | (1 << 2) | (1 << 3)
        self.assertEqual(
            decode_risk_flags(value),
            "plausible-risk-or-scout-trigger,scout-pivot-switch,haki-oracle-fired",
        )

    def test_unknown_high_bits_are_ignored(self) -> None:
        # Only bits 0..3 are documented; bit 7 should not appear in output.
        self.assertEqual(decode_risk_flags(1 << 7), "none")


class FormatMetadataLinesTests(unittest.TestCase):
    def test_only_truthy_documented_keys_are_emitted_in_declared_order(self) -> None:
        meta = {
            "trace_rom": "trace.gbc",
            "trace_rom_sha256": "DEADBEEF",
            "trace_symbols": "",
            "boss": "MORTY",
            "turn": "1",
            "enemy": "GENGAR",
            "player": "DRAGONITE",
            "frame": "42",
            "capture_index": "3",
            "notes": "first capture",
            "extra_key_not_in_keylist": "ignored",
        }
        self.assertEqual(
            format_metadata_lines(meta),
            [
                "trace_rom=trace.gbc",
                "trace_rom_sha256=DEADBEEF",
                "boss=MORTY",
                "turn=1",
                "enemy=GENGAR",
                "player=DRAGONITE",
                "frame=42",
                "capture_index=3",
                "notes=first capture",
            ],
        )

    def test_empty_metadata_returns_empty_list(self) -> None:
        self.assertEqual(format_metadata_lines({}), [])


class TraceSignatureTests(unittest.TestCase):
    def test_signature_flattens_only_trace_fields_in_declared_order(self) -> None:
        values = _make_trace_values(
            wBossAITraceTopMoves=[1, 2, 3],
            wBossAITraceTopScores=[10, 20, 30],
            wBossAITraceChosenMove=[7],
        )
        sig = trace_signature(values)
        # The first three entries match wBossAITraceTopMoves' order.
        self.assertEqual(sig[0:3], (1, 2, 3))
        # SELECTOR_REPLAY_FIELDS values like wBossAITier are NOT in the
        # signature: signature should equal the flattened TRACE_FIELDS only.
        expected_len = sum(size for _name, size in capture.TRACE_FIELDS)
        self.assertEqual(len(sig), expected_len)
        self.assertIn(7, sig)  # the chosen-move byte

    def test_signature_changes_when_any_trace_field_changes(self) -> None:
        before = trace_signature(_make_trace_values())
        after = trace_signature(_make_trace_values(wBossAITraceChosenMove=[1]))
        self.assertNotEqual(before, after)

    def test_signature_stable_when_selector_only_fields_change(self) -> None:
        before = trace_signature(_make_trace_values())
        after = trace_signature(_make_trace_values(wBossAITier=[3]))
        self.assertEqual(before, after)


class DecisionPredicateTests(unittest.TestCase):
    def test_has_completed_move_decision_requires_nonzero_chosen(self) -> None:
        self.assertFalse(has_completed_move_decision(_make_trace_values()))
        self.assertTrue(
            has_completed_move_decision(
                _make_trace_values(wBossAITraceChosenMove=[5])
            )
        )

    def test_has_decision_values_fires_on_chosen(self) -> None:
        self.assertTrue(
            has_decision_values(_make_trace_values(wBossAITraceChosenMove=[5]))
        )

    def test_has_decision_values_fires_on_top_moves(self) -> None:
        self.assertTrue(
            has_decision_values(_make_trace_values(wBossAITraceTopMoves=[0, 0, 9]))
        )

    def test_has_decision_values_fires_on_switch_confidence(self) -> None:
        self.assertTrue(
            has_decision_values(
                _make_trace_values(wBossAITraceSwitchConfidence=[1])
            )
        )

    def test_has_decision_values_fires_on_risk_flags(self) -> None:
        self.assertTrue(
            has_decision_values(_make_trace_values(wBossAITraceRiskFlags=[1]))
        )

    def test_has_decision_values_false_on_pure_zero_capture(self) -> None:
        self.assertFalse(has_decision_values(_make_trace_values()))


class RequireSymbolsTests(unittest.TestCase):
    def test_complete_symbol_set_passes(self) -> None:
        symbols = {
            name: Symbol(0, 0xD000)
            for name, _size in (
                capture.TRACE_FIELDS
                + capture.SELECTOR_REPLAY_FIELDS
                + capture.CONTEXT_FIELDS
            )
        }
        # Should not raise.
        require_symbols(symbols)

    def test_missing_symbol_exits_with_named_message(self) -> None:
        stderr_buffer = io.StringIO()
        with redirect_stderr(stderr_buffer):
            with self.assertRaises(SystemExit):
                require_symbols({})  # everything missing
        err = stderr_buffer.getvalue()
        self.assertIn("missing required trace symbols", err)
        # At least the first declared TRACE_FIELDS entry name appears.
        self.assertIn(capture.TRACE_FIELDS[0][0], err)


class ParseMoveNamesTests(unittest.TestCase):
    def test_parses_const_def_block_until_def_num_attacks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "move_constants.asm"
            path.write_text(
                "; header comment\n"
                "const_def\n"
                "    const NO_MOVE  ; 00\n"
                "    const POUND    ; 01\n"
                "    const KARATE_CHOP\n"
                "    const DOUBLESLAP\n"
                "DEF NUM_ATTACKS EQU const_value - 1\n"
                "    const SHOULD_BE_IGNORED\n",
                encoding="utf-8",
            )
            names = parse_move_names(path)
        self.assertEqual(names[0], "NO_MOVE")
        self.assertEqual(names[1], "POUND")
        self.assertEqual(names[2], "KARATE_CHOP")
        self.assertEqual(names[3], "DOUBLESLAP")
        self.assertNotIn(4, names)

    def test_missing_file_returns_empty_dict(self) -> None:
        self.assertEqual(parse_move_names(Path("absent.asm")), {})


class FormatCaptureTests(unittest.TestCase):
    def test_format_capture_emits_all_documented_lines(self) -> None:
        values = _make_trace_values(
            wBossAITier=[3],
            wBossAITraceTopMoves=[1, 2, 0],
            wBossAITraceTopScores=[14, 20, 255],
            wBossAITracePreModelScores=[20, 20, 80, 255],
            wBossAITracePostModelScores=[14, 20, 80, 255],
            wBossAITraceChosenMove=[1],
            wBossAITraceSwitchConfidence=[7],
            wBossAITracePlanId=[2],
            wBossAITracePlanPhase=[1],
            wBossAITracePlanConfidence=[9],
            wBossAITracePlausibleMask=[0xAA, 0xBB, 0xCC, 0xDD],
            wBossAITraceRiskFlags=(1 << 1) | (1 << 3),
            wBossAITraceLookaheadBonusTop=[2, 3, 4],
            wBossAIRevealedMovesBitmap=[0x10] + [0] * 23,
            wEnemyMonMoves=[1, 2, 3, 0],
            wEnemyAIMoveScores=[13, 20, 80, 80],
            wCurEnemyMoveNum=[0],
            wCurEnemyMove=[1],
            wEnemySwitchMonParam=[0x11],
            wEnemySwitchMonIndex=[0x22],
            wBossAILastSwitchedOut=[0x33],
            wBossAISwitchCooldown=[0x44],
            wCurOTMon=[0x55],
        )
        # `wBossAITraceRiskFlags` must be a list per the format-capture contract;
        # rebuild the override with the integer wrapped.
        values["wBossAITraceRiskFlags"] = [(1 << 1) | (1 << 3)]

        text = format_capture(
            values,
            {1: "POUND", 2: "KARATE_CHOP", 3: "DOUBLESLAP"},
            {"boss": "MORTY", "turn": "1", "notes": "ok"},
        )

        # Metadata block.
        self.assertIn("boss=MORTY\n", text)
        self.assertIn("turn=1\n", text)
        self.assertIn("notes=ok\n", text)
        # Core decision lines.
        self.assertIn("tier=3", text)
        self.assertIn("move_ids=1,2,3,0", text)
        self.assertIn("move_scores=13,20,80,80", text)
        self.assertIn("pre_model_scores=20,20,80,255", text)
        self.assertIn("post_model_scores=14,20,80,255", text)
        self.assertIn("model_score_deltas=-6,+0,+0,na", text)
        self.assertIn("chosen_slot=0", text)
        self.assertIn("cur_enemy_move_id=1", text)
        self.assertIn("top_moves=POUND:14,KARATE_CHOP:20,#00:255", text)
        self.assertIn("chosen=POUND", text)
        self.assertIn("chosen_id=1", text)
        self.assertIn("switch_confidence=7", text)
        self.assertIn("plan_id=2", text)
        self.assertIn("plan_phase=1", text)
        self.assertIn("plan_confidence=9", text)
        self.assertIn("plausible_mask=aa bb cc dd", text)
        self.assertIn("risk_flags=0a (scout-move-chosen,haki-oracle-fired)", text)
        self.assertIn("lookahead_bonus_top=2,3,4", text)
        self.assertIn(
            "switch_context=param=11,index=22,last_out=33,cooldown=44,cur_ot=55",
            text,
        )
        # Revealed-mask line includes the first byte and 23 zero bytes.
        self.assertIn("revealed_masks=10 " + "00 " * 22 + "00", text)
        # Output ends with a trailing newline.
        self.assertTrue(text.endswith("\n"))

    def test_format_capture_with_empty_metadata_starts_with_tier(self) -> None:
        text = format_capture(_make_trace_values(wBossAITier=[2]), {}, {})
        first_line = text.splitlines()[0]
        self.assertEqual(first_line, "tier=2")


class FormatSymbolsTests(unittest.TestCase):
    def test_single_byte_field_renders_as_bare_addr(self) -> None:
        symbols = {
            name: Symbol(1, 0xD200 + offset * 0x40)
            for offset, (name, _size) in enumerate(
                capture.TRACE_FIELDS
                + capture.SELECTOR_REPLAY_FIELDS
                + capture.CONTEXT_FIELDS
            )
        }
        text = format_symbols(symbols)
        self.assertIn("Boss AI trace symbols:", text)
        # wBossAITraceChosenMove is declared size=1 — should not include a range.
        chosen_symbol = symbols["wBossAITraceChosenMove"]
        self.assertIn(
            f"wBossAITraceChosenMove={format_addr(chosen_symbol)}\n",
            text,
        )
        # wBossAITraceTopMoves is declared size=3 — should include end + byte count.
        top_symbol = symbols["wBossAITraceTopMoves"]
        end_addr = top_symbol.address + 3 - 1
        self.assertIn(
            f"wBossAITraceTopMoves={format_addr(top_symbol)}-{end_addr:04x} (3 bytes)\n",
            text,
        )


class BuildTraceBasisMetadataTests(unittest.TestCase):
    def test_includes_path_and_sha256_for_rom_and_symbols(self) -> None:
        class _NS:
            pass

        with tempfile.TemporaryDirectory() as tempdir:
            rom = Path(tempdir) / "trace.gbc"
            sym = Path(tempdir) / "trace.sym"
            rom.write_bytes(b"ROM")
            sym.write_text("00:0150 EntryPoint\n", encoding="utf-8")

            args = _NS()
            args.rom = rom
            args.symbols = sym

            meta = build_trace_basis_metadata(args)
        self.assertEqual(set(meta.keys()), {
            "trace_rom", "trace_rom_sha256",
            "trace_symbols", "trace_symbols_sha256",
        })
        self.assertEqual(len(meta["trace_rom_sha256"]), 64)
        self.assertEqual(meta["trace_rom_sha256"], meta["trace_rom_sha256"].upper())


if __name__ == "__main__":
    unittest.main()
