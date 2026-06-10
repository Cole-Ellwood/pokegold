from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.audit.check_boss_ai_pre_choice_replay import (
    BASELINE_FIELD_KEYS,
    PRE_CHOICE_REPLAY_EVIDENCE_ID,
    build_audit_report,
)


class PreChoiceReplayAuditTests(unittest.TestCase):
    def test_build_audit_report_declares_exact_match_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "audit" / "boss_ai_trace" / "live_capture_manifest.json"
            manifest_path.parent.mkdir(parents=True)
            rom_path = root / "pokegold_trace.gbc"
            symbols_path = root / "pokegold_trace.sym"
            rom_path.write_bytes(b"rom")
            symbols_path.write_text("00:4000 Symbol\n", encoding="utf-8")
            manifest = {
                "trace_rom": "pokegold_trace.gbc",
                "trace_symbols": "pokegold_trace.sym",
                "trace_rom_sha256": hashlib.sha256(rom_path.read_bytes()).hexdigest().upper(),
                "trace_symbols_sha256": hashlib.sha256(symbols_path.read_bytes()).hexdigest().upper(),
            }
            manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

            report = build_audit_report(
                manifest=manifest,
                entries=[{"id": "falkner"}, {"id": "bugsy"}],
                replay_report={
                    "capture_count": 2,
                    "checked_count": 2,
                    "failure_count": 0,
                    "partial_count": 0,
                    "exact_count": 2,
                    "exact_match_count": 2,
                    "exact_agreement_rate": 1.0,
                    "verdict_counts": {"exact_match": 2},
                },
                rom_path=rom_path,
                symbols_path=symbols_path,
                manifest_path=manifest_path,
                root=root,
            )

        self.assertEqual(report["kind"], "boss_ai_pre_choice_replay_audit")
        self.assertEqual(report["proof_status"], "complete")
        self.assertEqual(report["missing_evidence"], [])
        self.assertEqual(report["blocking_gaps"], [])
        self.assertIn(PRE_CHOICE_REPLAY_EVIDENCE_ID, report["closed_evidence_ids"])
        self.assertEqual(report["baseline_field_keys"], list(BASELINE_FIELD_KEYS))
        self.assertEqual(report["excluded_capture_ids"][0]["id"], "shared_switch_loop")
        self.assertEqual(report["verdict_counts"], {"exact_match": 2})
        self.assertEqual(report["state_basis"]["manifest_sha256"], report["manifest_sha256"])
        self.assertEqual(report["rom_sha256"], report["trace_rom_sha256"])
        self.assertEqual(report["symbols_sha256"], report["trace_symbols_sha256"])


if __name__ == "__main__":
    unittest.main()
