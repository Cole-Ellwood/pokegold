"""Verifier rejection contracts; real-ROM replay is a separate audit command."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.audit import root_cause_grass_verifier as verifier


class GrassVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        identity = {
            "rom_sha256": "rom", "symbols_sha256": "sym", "backend_sha256": "backend",
            "state_basis": {"initial_state_sha256": "state", "input_log_sha256": "inputs"},
        }
        self.fixtures = {side: {**copy.deepcopy(identity), "root": str(self.root / side)}
                         for side in ("input", "control")}
        self.trace = {
            "rom_sha256": "rom", "symbols_sha256": "sym", "initial_state_sha256": "state",
            "backend_sha256": "backend", "valid": True, "errors": [],
            "initial": {"watch_values": {"wBattleMonHP": "002C"}},
            "final": {"watch_values": {"wBattleMonHP": "002D"}}, "events": [],
        }
        for seq, point in enumerate(verifier.POINTS):
            regs = {"register_d": "02" if seq < 3 else "CB", "register_a": "06"}
            self.trace["events"].append({
                "seq": seq, "targets": [point], "bank": 1, "pc": 100 + seq,
                "registers": regs, "after_registers": dict(regs),
                "watch_values": {"wBattleMonHP": "002D" if point == "SwitchTurnCore" else "002C"},
            })
        self.detail = {
            "invariant": verifier.INVARIANT,
            "reproducer": "reproducer.json", "regression": "regression.json",
            "causal_chain": [{"trace": "trace.json", "seq": event["seq"]}
                             for event in self.trace["events"]],
            "intervention": {"at": verifier.CONSUMER, "register": "D", "expected": 203, "value": 2},
        }
        self.report = {"evidence_atoms": [{"claim_type": "diagnosis.root_cause", "detail": self.detail}]}
        self.write("trace.json", self.trace)
        self.write("reproducer.json", {"state": "recording/initial.state", "frames": 1, "buttons": []})
        self.write("regression.json", verifier.REGRESSION)
        self.export = self.enterContext(patch.object(verifier, "verify_export", return_value=True))
        self.enterContext(patch.object(verifier, "sha256_file", side_effect=lambda path: {
            "pokegold.gbc": "rom", "pokegold.sym": "sym", "initial.state": "state", "inputs.json": "inputs",
        }[path.name]))
        self.run = self.enterContext(patch.object(verifier, "run_runtime_experiment", side_effect=self.replay))

    def write(self, name, data):
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def replay(self, **kwargs):
        result = copy.deepcopy(self.trace)
        intervention = next(iter(kwargs["interventions"]), {})
        fixed = kwargs["root"].name == "control"
        restored = fixed or intervention.get("register") == "D" and intervention.get("value") == 2
        suppressed = intervention.get("register") == "A"
        if restored or suppressed:
            result["final"]["watch_values"]["wBattleMonHP"] = "002E"
        if restored:
            for event in result["events"]:
                if fixed or event["targets"][0] == verifier.SHIFT:
                    event["registers"]["register_d"] = "02"
                event["after_registers"]["register_d"] = "02"
        return result

    def verify(self):
        return verifier.verify_grass_diagnosis(self.report, fixtures=self.fixtures, artifact_root=self.root)

    def test_complete_chain_and_invariant_restoration_pass(self):
        result = self.verify()
        self.assertTrue(all(result[key] for key in (
            "failure_reproduced", "causal_chain_replayed", "alternatives_rejected",
            "minimized_reproducer_replayed", "regression_failed_broken", "regression_passed_control")))
        self.assertEqual(self.run.call_count, 5)

    def test_other_evidence_can_precede_root_cause(self):
        self.report["evidence_atoms"].insert(0, {"claim_type": "runtime.observation"})
        self.assertTrue(self.verify()["causal_chain_replayed"])

    def test_stale_source_and_each_artifact_rejected_before_emulation(self):
        for side in ("input", "control"):
            with self.subTest(side=side, artifact="source"):
                self.export.side_effect = lambda root, identity: root.name != side
                with self.assertRaisesRegex(ValueError, "stale"):
                    self.verify()
            self.export.side_effect = None
            for key in ("rom_sha256", "symbols_sha256", "initial_state_sha256", "input_log_sha256"):
                with self.subTest(side=side, artifact=key):
                    identity = self.fixtures[side]
                    target = identity if key in identity else identity["state_basis"]
                    old = target[key]
                    target[key] = "stale"
                    with self.assertRaisesRegex(ValueError, "stale"):
                        self.verify()
                    target[key] = old
        self.run.assert_not_called()

    def test_wrong_invariant_recipe_and_regression_rejected_before_emulation(self):
        self.detail["invariant"] = {"expected": 2}
        with self.assertRaisesRegex(ValueError, "invariant"):
            self.verify()
        self.detail["invariant"] = verifier.INVARIANT
        for name, bad in (("reproducer.json", {"frames": 0}), ("regression.json", {"expected": "002E"})):
            old = (self.root / name).read_text()
            self.write(name, bad)
            with self.assertRaises(ValueError):
                self.verify()
            (self.root / name).write_text(old)
        self.run.assert_not_called()

    def test_artifact_escape_rejected_before_emulation(self):
        self.detail["reproducer"] = "../outside.json"
        with self.assertRaisesRegex(ValueError, "outside"):
            self.verify()
        self.run.assert_not_called()

    def test_missing_reordered_and_forged_causal_events_fail(self):
        original = copy.deepcopy(self.detail["causal_chain"])
        for chain in (original[1:], list(reversed(original)), original + original[:1]):
            self.detail["causal_chain"] = chain
            self.assertFalse(self.verify()["causal_chain_replayed"])
        self.detail["causal_chain"] = original
        self.trace["events"][3]["registers"]["register_d"] = "02"
        self.write("trace.json", self.trace)
        self.trace["events"][3]["registers"]["register_d"] = "CB"
        self.assertFalse(self.verify()["causal_chain_replayed"])

    def test_stale_trace_identity_and_backend_fail(self):
        for key in ("rom_sha256", "symbols_sha256", "initial_state_sha256", "backend_sha256"):
            trace = copy.deepcopy(self.trace)
            trace[key] = "stale"
            self.write("trace.json", trace)
            with self.assertRaisesRegex(ValueError, "stale causal trace"):
                self.verify()
        self.write("trace.json", self.trace)
        self.fixtures["input"]["backend_sha256"] = "other backend"
        with self.assertRaisesRegex(ValueError, "backend differs"):
            self.verify()

    def test_bad_event_sequences_fail(self):
        for seq in (-1, True, "0", 99):
            self.detail["causal_chain"][0]["seq"] = seq
            with self.assertRaisesRegex(ValueError, "sequence"):
                self.verify()

    def test_symptom_suppression_and_unrelated_intervention_fail(self):
        for register in ("A", "E"):
            self.detail["intervention"] = {"at": verifier.SHIFT, "register": register, "expected": 6, "value": 5}
            self.assertFalse(self.verify()["alternatives_rejected"])

    def test_broken_control_does_not_pass_regression(self):
        self.fixtures["control"]["root"] = str(self.root / "input")
        self.assertFalse(self.verify()["regression_passed_control"])


if __name__ == "__main__":
    unittest.main()
