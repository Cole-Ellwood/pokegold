from __future__ import annotations

import unittest

from tools.debugger.evidence import (
    BankState,
    bank_state_record,
    bank_state_records,
    evidence_atom,
)


class EvidenceSchemaTests(unittest.TestCase):
    def test_evidence_atom_has_shared_proof_vector_axes(self) -> None:
        atom = evidence_atom(
            claim_type="reverse_query.last_writer",
            origin="reverse_query",
            observation_type="bounded_effect_window",
            proof_status="instruction-observed",
            source_report="reverse.json",
            source_kind="effect_trace",
            scope={"frame_range": "4:8", "empty": ""},
            subjects={"symbols": ["wCurDamage", "wCurDamage"], "addresses": ["D141"]},
            precision={"match_precision": "exact_bank_key"},
            validation={"post_memory_match": True},
            detail={"note": "unit"},
        )

        self.assertEqual(atom["schema_version"], 1)
        self.assertEqual(atom["proof_status"], "instruction_observed")
        self.assertEqual(atom["scope"], {"frame_range": "4:8"})
        self.assertEqual(atom["subjects"]["symbols"], ["wCurDamage"])
        self.assertEqual(atom["precision"]["match_precision"], "exact_bank_key")
        self.assertEqual(atom["validation"]["post_memory_match"], True)

    def test_bank_state_records_distinguish_runtime_inferred_and_disabled(self) -> None:
        records = {
            item["name"]: item
            for item in bank_state_records(
                (
                    ("wram", 2),
                    ("sram", 3),
                    ("sram_inferred", 1),
                    ("sram_enabled", 0),
                ),
                source_for_name=lambda name: (
                    f"inferred_bank_state.{name}" if name == "sram" else f"bank_state.{name}"
                ),
            )
        }

        self.assertEqual(records["wram"]["state_kind"], "runtime_observed")
        self.assertEqual(records["sram"]["state_kind"], "inferred_from_io_write")
        self.assertEqual(records["sram"]["source_kind"], "inferred_bank_state")
        self.assertEqual(records["sram_enabled"]["state_kind"], "sram_disabled")
        self.assertNotIn("sram_inferred", records)

    def test_bank_state_record_supports_default_mapper_and_unknown_sources(self) -> None:
        bank_state = BankState(
            (
                bank_state_record(name="rom", value=1, source="default_bank_state.rom"),
                bank_state_record(name="sram", value=2, source="mapper_bank_state.sram"),
                bank_state_record(name="vram", value=None, source=""),
            )
        )

        by_name = {record["name"]: record for record in bank_state.as_records()}
        self.assertEqual(by_name["rom"]["state_kind"], "default")
        self.assertEqual(by_name["sram"]["state_kind"], "mapper_derived")
        self.assertEqual(by_name["vram"]["state_kind"], "unknown")
        self.assertNotIn("value", by_name["vram"])
        self.assertEqual(bank_state.as_state(), {"rom": 1, "sram": 2})


if __name__ == "__main__":
    unittest.main()
