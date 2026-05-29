from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.shrink_input_log import format_report, shrink_input_log


def write_log(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ShrinkInputLogTests(unittest.TestCase):
    def test_shrink_input_log_canonical(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "ag08_inputs.txt"
            lines = [
                *["WAIT 1" for _ in range(12)],
                "A",
                *["WAIT 1" for _ in range(12)],
                "START",
                *["WAIT 1" for _ in range(4)],
            ]
            write_log(log, lines)

            report = shrink_input_log(
                input_log="ag08_inputs.txt",
                root=root,
                predicate=lambda candidate: "A" in candidate and "START" in candidate,
            )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["original_event_count"], 30)
        self.assertLessEqual(report["shrunk_event_count"], 2)
        self.assertEqual(set(report["shrunk_lines"]), {"A", "START"})
        self.assertGreater(report["reduction_step_count"], 0)

    def test_shrink_input_log_writes_minimized_artifact(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "route.txt"
            write_log(log, ["WAIT 1", "LEFT", "WAIT 1", "A"])

            report = shrink_input_log(
                input_log="route.txt",
                root=root,
                out_log=".local/tmp/shrunk/route.txt",
                predicate=lambda candidate: "LEFT" in candidate and "A" in candidate,
            )
            out_log = root / ".local/tmp/shrunk/route.txt"
            written_lines = out_log.read_text(encoding="utf-8").splitlines()

        self.assertTrue(report["valid"], report)
        self.assertTrue(report["out_log"]["written"])
        self.assertEqual(written_lines, ["LEFT", "A"])
        self.assertIn("shrunk_log=.local/tmp/shrunk/route.txt", format_report(report))

    def test_shrink_input_log_refuses_non_reproducing_baseline(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "route.txt"
            write_log(log, ["WAIT 1", "A"])

            report = shrink_input_log(
                input_log="route.txt",
                root=root,
                predicate=lambda _candidate: False,
            )

        self.assertFalse(report["valid"])
        self.assertIn("baseline input log does not reproduce", report["errors"][0])
        self.assertEqual(report["shrunk_lines"], ["WAIT 1", "A"])

    def test_shrink_input_log_reports_parse_errors(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "route.txt"
            write_log(log, ["NOPE"])

            report = shrink_input_log(
                input_log="route.txt",
                root=root,
                predicate=lambda _candidate: True,
            )

        self.assertFalse(report["valid"])
        self.assertIn("unknown button", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
