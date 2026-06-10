from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.debugger.__main__ import main as debugger_main
from tools.debugger.rom_index import build_rom_byte_lookup_report, build_rom_index_report


class RomIndexTests(unittest.TestCase):
    def test_exact_symbol_lookup_returns_source_and_byte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="00:0100",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["target"]["bank_address"], "00:0100")
        self.assertEqual(report["target"]["offset"], 0x100)
        self.assertEqual(report["rom_byte"]["value_hex"], "42")
        self.assertEqual(report["lookup"]["confidence"], "exact_symbol_start")
        self.assertEqual(report["lookup"]["best"]["label"], "Start")
        self.assertEqual(
            report["lookup"]["best"]["source_refs"],
            [{"path": "home/main.asm", "line": 2, "kind": "definition"}],
        )

    def test_interior_byte_uses_nearest_label_without_claiming_exact_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="00:0102",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["rom_byte"]["value_hex"], "44")
        self.assertEqual(report["lookup"]["confidence"], "nearest_label")
        self.assertEqual(report["lookup"]["best"]["label"], "Start")
        self.assertEqual(report["lookup"]["best"]["distance_bytes"], 2)

    def test_empty_linker_range_is_reported_as_padding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="00:0105",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["lookup"]["confidence"], "empty_or_padding")
        self.assertEqual(report["lookup"]["empty_range"]["bank_range"], "00:0104-0107")

    def test_offset_query_maps_to_bank_and_address(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                offset="0x4000",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["target"]["bank_address"], "01:4000")
        self.assertEqual(report["rom_byte"]["value_hex"], "99")
        self.assertEqual(report["lookup"]["confidence"], "exact_symbol_start")
        self.assertEqual(report["lookup"]["best"]["label"], "BankLabel")
        self.assertEqual(report["lookup"]["section"]["name"], "Bank 1")

    def test_exact_bare_local_label_resolves_to_source_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="00:0103",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["lookup"]["confidence"], "exact_symbol_start")
        self.assertEqual(report["lookup"]["best"]["label"], "Start.done")
        self.assertEqual(
            report["lookup"]["best"]["source_refs"],
            [{"path": "home/main.asm", "line": 4, "kind": "definition"}],
        )

    def test_symbol_without_source_does_not_claim_nearest_label_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))
            (root / "test.sym").write_text("00:0100 MissingLabel\n", encoding="utf-8")

            report = build_rom_byte_lookup_report(
                address="00:0100",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertTrue(report["valid"])
        self.assertEqual(report["lookup"]["confidence"], "section_owned")
        self.assertEqual(report["lookup"]["best"]["kind"], "section")
        self.assertNotEqual(report["lookup"]["best"].get("label"), "MissingLabel")

    def test_first_byte_after_rom_file_is_rejected_before_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                offset="0x8000",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertEqual(report["lookup"]["confidence"], "missing_input")
        self.assertTrue(any("beyond the ROM file size" in error for error in report["errors"]))

    def test_offset_beyond_bank_ff_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                offset="0x400000",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("offset resolves beyond max ROM bank 0xFF", report["errors"])

    def test_romx_address_without_bank_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="4000",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("ROMX address lookup requires a bank prefix", report["errors"][0])
        self.assertEqual(report["lookup"]["confidence"], "missing_input")

    def test_missing_inputs_fail_before_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            report = build_rom_byte_lookup_report(
                address="00:0100",
                rom_path="missing.gbc",
                symbols_path="missing.sym",
                map_path="missing.map",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertEqual(report["index_summary"]["section_count"], 0)
        self.assertEqual(report["lookup"]["confidence"], "missing_input")
        self.assertTrue(any("missing rom file" in error for error in report["errors"]))
        self.assertTrue(any("missing symbols file" in error for error in report["errors"]))
        self.assertTrue(any("missing map file" in error for error in report["errors"]))

    def test_duplicate_query_inputs_fail_before_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))

            report = build_rom_byte_lookup_report(
                address="00:0100",
                offset="0x100",
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
            )

        self.assertFalse(report["valid"])
        self.assertIn("--address and --offset are mutually exclusive", report["errors"])
        self.assertEqual(report["index_summary"]["section_count"], 0)

    def test_cli_rom_byte_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))
            out = root / "rom-byte.json"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "rom-byte",
                        "--root",
                        str(root),
                        "--rom",
                        "test.gbc",
                        "--symbols",
                        "test.sym",
                        "--map",
                        "test.map",
                        "--address",
                        "00:0100",
                        "--json-out",
                        str(out),
                    ]
                )

            data = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_rom_byte_lookup")
        self.assertEqual(data["lookup"]["confidence"], "exact_symbol_start")
        self.assertEqual(data["rom_byte"]["value_hex"], "42")

    def test_rom_index_writes_surface_and_byte_span_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))
            surface_out = root / "rom_surface_index.jsonl"
            byte_out = root / "rom_byte_index.jsonl"
            mirror_report = root / "content.json"
            mirror_report.write_text(
                json.dumps(
                    {
                        "kind": "unified_debugger_content_mirror",
                        "byte_span_rows": [
                            {
                                "kind": "rom_byte_index_row",
                                "row_id": "content-mirror:unit",
                                "confidence": "content_mirror_exact_span",
                                "rom_span": {"offset_start": 0x100, "bank_range": "00:0100-0100"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = build_rom_index_report(
                rom_path="test.gbc",
                symbols_path="test.sym",
                map_path="test.map",
                root=root,
                surface_index_out=surface_out,
                byte_index_out=byte_out,
                content_mirror_report_path=mirror_report,
            )
            surface_rows = read_jsonl(surface_out)
            byte_rows = read_jsonl(byte_out)

        self.assertTrue(report["valid"])
        self.assertTrue(report["outputs"]["surface_index_written"])
        self.assertTrue(report["outputs"]["byte_index_written"])
        self.assertEqual(report["index_summary"]["content_mirror_exact_span_count"], 1)
        self.assertGreater(report["index_summary"]["surface_row_count"], 0)
        self.assertGreater(report["index_summary"]["byte_span_row_count"], 0)
        local_label_rows = [
            row
            for row in surface_rows
            if row["surface_kind"] == "symbol" and row["nearest_label"] == "Start.done"
        ]
        self.assertEqual(local_label_rows[0]["source_refs"], [{"path": "home/main.asm", "line": 4, "kind": "definition"}])
        self.assertEqual(local_label_rows[0]["rom_span"]["bank_range"], "00:0103-0103")
        first_bank_rows = [
            row
            for row in byte_rows
            if row["rom_span"]["bank_range"] == "01:4000-4003"
        ]
        self.assertEqual(first_bank_rows[0]["section"], "Bank 1")
        self.assertFalse([row for row in byte_rows if row.get("section") == "Zero Size"])
        content_rows = [row for row in byte_rows if row.get("confidence") == "content_mirror_exact_span"]
        self.assertTrue(content_rows)
        self.assertEqual(content_rows[0]["input_hashes"], report["input_hashes"])

    def test_cli_rom_index_writes_report_and_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_rom_index_fixture(Path(tmp))
            report_out = root / "rom-index.json"
            surface_out = root / "surface.jsonl"
            byte_out = root / "byte.jsonl"
            with redirect_stdout(io.StringIO()):
                code = debugger_main(
                    [
                        "rom-index",
                        "--root",
                        str(root),
                        "--rom",
                        "test.gbc",
                        "--symbols",
                        "test.sym",
                        "--map",
                        "test.map",
                        "--surface-index-out",
                        str(surface_out),
                        "--byte-index-out",
                        str(byte_out),
                        "--content-mirror-report",
                        str(root / "missing-content.json"),
                        "--json-out",
                        str(report_out),
                    ]
                )

            data = json.loads(report_out.read_text(encoding="utf-8"))
            surface_exists = surface_out.exists()
            byte_exists = byte_out.exists()

        self.assertEqual(code, 0)
        self.assertEqual(data["kind"], "unified_debugger_rom_index")
        self.assertTrue(data["outputs"]["surface_index_written"])
        self.assertTrue(data["outputs"]["byte_index_written"])
        self.assertTrue(surface_exists)
        self.assertTrue(byte_exists)


def make_rom_index_fixture(root: Path) -> Path:
    (root / "home").mkdir(parents=True)
    (root / ".claude" / "worktrees" / "old-copy" / "home").mkdir(parents=True)
    rom = bytearray(0x8000)
    rom[0x100] = 0x42
    rom[0x101] = 0x43
    rom[0x102] = 0x44
    rom[0x105] = 0xEE
    rom[0x4000] = 0x99
    (root / "test.gbc").write_bytes(rom)
    (root / "test.sym").write_text(
        "00:0100 Start\n00:0103 Start.done\n01:4000 BankLabel\n",
        encoding="utf-8",
    )
    (root / "test.map").write_text(
        "\n".join(
            [
                "ROM0 bank #0:",
                '\tSECTION: $0100-$0103 ($0004 bytes) ["Home"]',
                "\t    $0100 = Start",
                "\tEMPTY: $0104-$0107 ($0004 bytes)",
                "ROMX bank #1:",
                '\tSECTION: $4000 ($0000 bytes) ["Zero Size"]',
                '\tSECTION: $4000-$4003 ($0004 bytes) ["Bank 1"]',
                "\t    $4000 = BankLabel",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    (root / "home" / "main.asm").write_text(
        "\n".join(
            [
                'SECTION "Home", ROM0[$0100]',
                "Start::",
                "\tret",
                ".done",
                'SECTION "Bank 1", ROMX[$4000], BANK[$1]',
                "BankLabel:",
                "\tret",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    (root / ".claude" / "worktrees" / "old-copy" / "home" / "main.asm").write_text(
        "\n".join(
            [
                'SECTION "Home", ROM0[$0100]',
                "Start::",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    return root


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
