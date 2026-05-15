from __future__ import annotations

import unittest

from tools.audit.check_boss_ai_debugger_done import (
    format_done_gate_report,
    GATE_COMMANDS,
    tail,
)


class DoneGateTests(unittest.TestCase):
    def test_tail_keeps_last_nonblank_lines(self) -> None:
        self.assertEqual(
            tail("a\n\nb\nc\n", max_lines=2),
            ["b", "c"],
        )

    def test_format_done_gate_reports_blockers(self) -> None:
        text = format_done_gate_report(
            {
                "passed": False,
                "command_count": 2,
                "failed_command_count": 1,
                "roadmap_ready": False,
                "roadmap_blocking_gap_count": 1,
                "roadmap_blocking_gaps": ["coverage gap"],
                "commands": [
                    {"gate_id": "ok", "returncode": 0},
                    {"gate_id": "bad", "returncode": 1},
                ],
            }
        )

        self.assertIn("passed=False", text)
        self.assertIn("bad", text)
        self.assertIn("coverage gap", text)

    def test_done_gate_includes_changed_ai_suite_command(self) -> None:
        commands = {command.gate_id: command.command for command in GATE_COMMANDS}

        command = commands["changed_ai_suite"]

        self.assertIn("run-suite", command)
        self.assertIn("--profile", command)
        self.assertIn("changed-ai", command)
        self.assertIn("--rebuild-roms", command)
        self.assertIn("--refresh-live-traces", command)


if __name__ == "__main__":
    unittest.main()
