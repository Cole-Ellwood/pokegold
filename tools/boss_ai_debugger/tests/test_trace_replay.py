from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.boss_ai_debugger.__main__ import main as debugger_main
from tools.boss_ai_debugger.trace_replay import (
    parse_trace_file,
    replay_capture_fields,
    replay_trace_paths,
)


MOVE_NAMES = {
    1: "POUND",
    2: "KARATE_CHOP",
    3: "DOUBLESLAP",
    4: "COMET_PUNCH",
}


class TraceReplayTests(unittest.TestCase):
    def test_exact_capture_matches_possible_second_slot(self) -> None:
        verdict = replay_capture_fields(
            {
                "boss": "Exact",
                "tier": "3",
                "move_ids": "1,2,3,0",
                "move_scores": "20,20,20,80",
                "chosen_id": "2",
                "chosen_slot": "1",
            },
            "Exact#1",
            Path("trace.txt"),
            MOVE_NAMES,
        )

        self.assertTrue(verdict.match)
        self.assertEqual(verdict.mode, "exact")

    def test_exact_capture_can_use_current_move_when_trace_chosen_is_zero(self) -> None:
        verdict = replay_capture_fields(
            {
                "boss": "Exact",
                "tier": "3",
                "move_ids": "1,2,3,0",
                "move_scores": "20,20,20,80",
                "chosen_id": "0",
                "cur_enemy_move_id": "2",
                "chosen_slot": "1",
            },
            "Exact#1",
            Path("trace.txt"),
            MOVE_NAMES,
        )

        self.assertTrue(verdict.match)
        self.assertEqual(verdict.chosen_id, 2)

    def test_exact_capture_rejects_tied_third_slot(self) -> None:
        verdict = replay_capture_fields(
            {
                "boss": "Exact",
                "tier": "3",
                "move_ids": "1,2,3,0",
                "move_scores": "20,20,20,80",
                "chosen_id": "3",
                "chosen_slot": "2",
            },
            "Exact#1",
            Path("trace.txt"),
            MOVE_NAMES,
        )

        self.assertFalse(verdict.match)
        self.assertEqual(verdict.reason, "chosen slot is outside selector's possible best/second slots")

    def test_partial_top_three_capture_accepts_top_two_only(self) -> None:
        verdict = replay_capture_fields(
            {
                "boss": "Partial",
                "top_moves": "POUND:20,KARATE_CHOP:20,DOUBLESLAP:20",
                "chosen_id": "2",
            },
            "Partial#1",
            Path("trace.txt"),
            MOVE_NAMES,
        )

        self.assertTrue(verdict.match)
        self.assertEqual(verdict.mode, "partial_top3")

    def test_trace_file_multiple_blocks_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "boss_live.txt"
            trace.write_text(
                "\n".join(
                    [
                        "boss=One",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,20,20,80",
                        "chosen_id=1",
                        "chosen_slot=0",
                        "---",
                        "boss=Two",
                        "tier=3",
                        "move_ids=1,2,3,0",
                        "move_scores=20,20,20,80",
                        "chosen_id=3",
                        "chosen_slot=2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            blocks = parse_trace_file(trace)
            report = replay_trace_paths([trace], move_names=MOVE_NAMES)
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    ["trace-replay", "--trace", str(trace), "--fail-on-mismatch"]
                )

        self.assertEqual(len(blocks), 2)
        self.assertEqual(report["checked_count"], 2)
        self.assertEqual(report["match_count"], 1)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
