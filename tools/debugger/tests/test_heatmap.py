from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.heatmap import REGIONS, build_heatmap, main


def _write_trace(path: Path, events: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(ev) for ev in events) + "\n",
        encoding="utf-8",
    )


class HeatmapTests(unittest.TestCase):
    def test_io_grid_has_one_row_per_address_and_one_column_per_frame(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 0, "pc_bank_address": "00:0150"},
                    {"kind": "write", "address": "0xFF40", "frame": 1, "seq": 1, "pc_bank_address": "00:0150"},
                    {"kind": "write", "address": "0xFF42", "frame": 1, "seq": 2, "pc_bank_address": "00:0160"},
                ],
            )

            report = build_heatmap(traces=(trace,), region="io", root=root)

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["region"], "io")
        self.assertEqual(report["cell_count"], 3)
        self.assertEqual(report["frame_count"], 2)
        grid_lines = [line for line in report["grid"].splitlines() if line.startswith("$")]
        self.assertEqual(len(grid_lines), 2)
        for line in grid_lines:
            self.assertEqual(len(line) - len("$FFXX  "), report["frame_count"])

    def test_address_outside_region_is_filtered(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xC100", "frame": 0, "seq": 0},
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 1},
                    {"kind": "write", "address": "0xD200", "frame": 0, "seq": 2},
                ],
            )

            io_report = build_heatmap(traces=(trace,), region="io", root=root)
            wramx_report = build_heatmap(traces=(trace,), region="wramx", root=root)

        io_addresses = {cell["address_hex"] for cell in io_report["cells"]}
        wramx_addresses = {cell["address_hex"] for cell in wramx_report["cells"]}
        self.assertEqual(io_addresses, {"$FF40"})
        self.assertEqual(wramx_addresses, {"$D200"})

    def test_frame_range_filter_clips_outside_window(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 0},
                    {"kind": "write", "address": "0xFF40", "frame": 5, "seq": 1},
                    {"kind": "write", "address": "0xFF40", "frame": 10, "seq": 2},
                ],
            )

            report = build_heatmap(traces=(trace,), region="io", frame_range=(2, 8), root=root)

        self.assertEqual(report["frames"], [5])
        self.assertEqual(report["cell_count"], 1)

    def test_last_write_pc_tracks_highest_seq_per_cell(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 1, "pc_bank_address": "00:0150", "pc_label": "First"},
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 2, "pc_bank_address": "00:0180", "pc_label": "Second"},
                ],
            )

            report = build_heatmap(traces=(trace,), region="io", root=root)

        cell = next(c for c in report["cells"] if c["address_hex"] == "$FF40")
        self.assertEqual(cell["write_count"], 2)
        self.assertEqual(cell["last_write_pc"], "00:0180")
        self.assertEqual(cell["last_write_pc_label"], "Second")

    def test_last_write_pc_unknown_seq_does_not_replace_known_seq(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xFF40", "frame": 0, "seq": 2, "pc_bank_address": "00:0180", "pc_label": "Known"},
                    {"kind": "write", "address": "0xFF40", "frame": 0, "pc_bank_address": "00:0200", "pc_label": "Unknown"},
                ],
            )

            report = build_heatmap(traces=(trace,), region="io", root=root)

        cell = next(c for c in report["cells"] if c["address_hex"] == "$FF40")
        self.assertEqual(cell["write_count"], 2)
        self.assertEqual(cell["last_write_pc"], "00:0180")
        self.assertEqual(cell["last_write_pc_label"], "Known")

    def test_frame_zero_uses_explicit_frame_before_frame_index_fallback(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [
                    {"kind": "write", "address": "0xFF40", "frame": 0, "frame_index": 9, "seq": 0},
                ],
            )

            report = build_heatmap(traces=(trace,), region="io", root=root)

        self.assertEqual(report["frames"], [0])
        self.assertEqual(report["cells"][0]["frame"], 0)

    def test_missing_trace_is_invalid_instead_of_empty_success(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_heatmap(traces=("missing.jsonl",), region="io", root=root)

        self.assertFalse(report["valid"])
        self.assertIn("missing trace", report["errors"][0])
        self.assertIn("no writes in window", report["grid"])

    def test_cli_invalid_frame_range_fails_closed(self) -> None:
        import contextlib
        import io as io_mod

        err = io_mod.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stderr(err):
                main(["--frame-range", "10:2", "--json"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("hi greater than lo", err.getvalue())

    def test_unknown_region_returns_invalid_packet(self) -> None:
        report = build_heatmap(traces=(), region="vram")
        self.assertFalse(report["valid"])
        self.assertIn("unknown region", report["errors"][0])
        self.assertEqual(report["cells"], [])

    def test_empty_window_renders_no_writes_placeholder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_heatmap(traces=(), region="io", root=root)

        self.assertTrue(report["valid"], report)
        self.assertIn("no writes in window", report["grid"])

    def test_cli_json_emission_writes_machine_parseable_payload(self) -> None:
        import contextlib
        import io as io_mod

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / "effect.jsonl"
            _write_trace(
                trace,
                [{"kind": "write", "address": "0xFF40", "frame": 0, "seq": 0}],
            )

            buf = io_mod.StringIO()
            with contextlib.redirect_stdout(buf):
                exit_code = main(["--trace", str(trace), "--region", "io", "--json"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["kind"], "unified_debugger_io_heatmap")
        self.assertEqual(payload["region"], "io")
        self.assertEqual(payload["cell_count"], 1)


if __name__ == "__main__":
    unittest.main()
