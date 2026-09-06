from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.audit import root_cause_mail_verifier as verifier
from tools.audit.root_cause_evaluator import BASIS_FIELDS, REPLAY_CHECKS, score_diagnosis
from tools.debugger.report_envelope import replay_state_basis, sha256_file


class Memory:
    def __init__(self, data):
        self.data = bytearray(data)

    def __getitem__(self, key):
        bank, address = key
        assert bank == 0
        return self.data[address - 0xA000]

    def __setitem__(self, key, value):
        raise AssertionError("verifier must not write memory or mapper registers")


class Backend:
    def __init__(self, before, fixed, failure):
        self.memory = Memory(before)
        self.fixed, self.failure = fixed, failure
        self.register_file = SimpleNamespace(A=17, B=0, C=47, HL=0xA600, E=2)
        self.hooks = {}
        self.stopped = False

    def load_state(self, handle):
        assert handle.read() == b"state"

    def hook_register(self, bank, pc, callback, context):
        self.hooks[bank, pc] = callback

    def hook_deregister(self, bank, pc):
        del self.hooks[bank, pc]

    def stop(self, *, save):
        assert save is False
        self.stopped = True

    def tick(self, frames, render, sound):
        assert (frames, render, sound) == (1, False, False)
        self.register_file.A = 1 if self.failure == "wrong_slot" else 2
        if (4, 0x700A) in self.hooks:
            self.hooks[4, 0x700A](None)
        self.register_file.A = 16 if self.failure == "wrong_bank_load" else 17
        if (4, 0x700C) in self.hooks and self.failure != "late_bank_load":
            self.hooks[4, 0x700C](None)
        self.register_file.A = 17
        if self.failure == "preimage":
            self.register_file.A = 16
        if (17, 0x4100) in self.hooks and self.failure != "missing_intervention":
            self.hooks[17, 0x4100](None)
            if self.failure == "duplicate_entry":
                self.hooks[17, 0x4100](None)
        if self.failure == "late_bank_load" and (4, 0x700C) in self.hooks:
            self.hooks[4, 0x700C](None)
        slot = 2 if self.fixed else self.register_file.A
        self.register_file.A = slot
        if (0, 0x3074) in self.hooks:
            self.hooks[0, 0x3074](None)
        for index in range(slot):
            pointer = 0xA600 + index * 47
            self.register_file.HL = pointer
            self.register_file.A = slot - index
            if self.failure == "wrong_counter":
                self.register_file.A ^= 1
            if self.failure == "wrong_pointer":
                self.register_file.HL += 1
            self.register_file.C = 46 if self.failure == "wrong_stride" else 47
            if (0, 0x3076) in self.hooks and self.failure != "missing_iteration":
                self.hooks[0, 0x3076](None)
                if self.failure == "duplicate_iteration":
                    self.hooks[0, 0x3076](None)
        pointer = 0xA600 + slot * 47
        self.register_file.HL = pointer
        self.register_file.A = 1 if self.failure == "wrong_fill_value" else 0
        self.register_file.C = 46 if self.failure == "wrong_fill_length" else 47
        if (0, 0x301D) in self.hooks:
            self.hooks[0, 0x301D](None)
        start = 0x600 + slot * 47
        self.memory.data[start:start + 47] = bytes(47)
        if self.failure == "extra_byte":
            self.memory.data[0x100] ^= 1
        for _ in range(0 if self.failure == "missing_return" else 2 if self.failure == "duplicate_return" else 1):
            self.hooks[4, 0x7010](None)


class MailVerifierTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.before = bytes(1 + index % 254 for index in range(8192))
        self.fixtures = {}
        for side in ("broken", "fixed"):
            root = self.root / side
            root.mkdir()
            rom = bytearray(0x48000)
            rom[0x1300A:0x13010] = bytes((0x3E, 17, 0x21, 0, 0x41, 0xCF))
            (root / "pokegold.gbc").write_bytes(rom)
            (root / "pokegold.sym").write_text("00:A600 sPartyMail\n00:A835 sMailboxes\n11:4100 ClearPartyMonMail\n04:7000 Caller\n00:3074 AddNTimes\n00:3076 AddNTimes.loop\n00:301d ByteFill\n")
            (root / "initial.state").write_bytes(b"state")
            (root / "inputs.json").write_text(json.dumps({"frames": 1, "buttons": []}))
            self.fixtures[side] = {
                "root": str(root), "recording": str(root),
                "rom_sha256": sha256_file(root / "pokegold.gbc"), "symbols_sha256": sha256_file(root / "pokegold.sym"),
                "state_basis": replay_state_basis(root / "initial.state", 1), "recording_sha256": sha256_file(root / "inputs.json"),
                "backend": f"{Backend.__module__}.{Backend.__name__}", "backend_sha256": sha256_file(sys.modules[Backend.__module__].__file__),
                "selected_slot": 2, "mail_record_bytes": 47, "return_checkpoint": "Caller+0x10",
                "before": {"party": self.before[0x600:0x600 + 282].hex().upper(), "mailbox": self.before[0x835:0x835 + 470].hex().upper()},
            }
        self.failure = ""
        self.instances = []
        def opened(path, message):
            backend = Backend(self.before, path.parent.name == "fixed", self.failure)
            self.instances.append(backend)
            return backend
        self.export = self.enterContext(patch.object(verifier, "verify_export", return_value=True))
        self.enterContext(patch.object(verifier.runtime, "load_pyboy", return_value=Backend))
        self.opened = self.enterContext(patch.object(verifier.runtime, "open_pyboy", side_effect=opened))
        self.enterContext(patch.object(verifier.runtime, "disable_realtime"))

    def test_complete_bank_comparison_and_control_contract(self):
        for failure in ("", "extra_byte"):
            with self.subTest(failure=failure):
                self.failure = failure
                report = verifier.verify_mail_regression(self.fixtures)
                self.assertEqual(report["valid"], not failure)
                self.assertEqual(list(report["replays"]), ["baseline", "restore", "control", "fixed"])
                for mode, replay in report["replays"].items():
                    self.assertEqual(len(replay["return_sram"]), 8192 * 2)
                    self.assertEqual(len(replay["changed_addresses"]), 48 if failure else 47)
                    self.assertEqual(replay["matches_exact_effect"], not failure)
                    self.assertEqual(replay["passes_intended_contract"], not failure and mode in ("restore", "fixed"))
                self.assertNotIn("diagnosis.root_cause", str(report))
        self.assertTrue(all(pb.stopped and not pb.hooks for pb in self.instances))

    def test_stale_basis_rejected_before_any_emulator_opens(self):
        for side in ("broken", "fixed"):
            for key in ("rom_sha256", "symbols_sha256", "state_basis", "recording_sha256", "backend", "backend_sha256", "selected_slot", "mail_record_bytes"):
                with self.subTest(side=side, key=key):
                    fixtures = copy.deepcopy(self.fixtures)
                    fixtures[side][key] = "stale"
                    with self.assertRaises(ValueError):
                        verifier.verify_mail_regression(fixtures)
                    self.opened.assert_not_called()
        self.export.return_value = False
        with self.assertRaises(ValueError):
            verifier.verify_mail_regression(self.fixtures)
        self.opened.assert_not_called()

    def test_replayed_pointer_chain_is_required_even_when_final_sram_matches(self):
        for failure in ("", "wrong_counter", "missing_iteration", "duplicate_iteration", "wrong_pointer",
                        "wrong_stride", "wrong_fill_value", "wrong_fill_length"):
            with self.subTest(failure=failure):
                self.failure = failure
                report = verifier.verify_mail_regression(self.fixtures)
                self.assertEqual(report["valid"], not failure)
                for mode, replay in report["replays"].items():
                    self.assertTrue(replay["matches_exact_effect"])
                    self.assertEqual(replay["pointer_chain_verified"], not failure)
                    events = replay["pointer_events"]
                    self.assertEqual(events[0]["point"], "entry")
                    self.assertEqual(events[1]["point"], "multiply")
                    self.assertEqual(events[-1]["point"], "fill")
                    if not failure:
                        iterations = 17 if mode == "baseline" else 3 if mode == "control" else 2
                        self.assertEqual(len(events), iterations + 3)
                        self.assertEqual(events[-1]["registers"]["HL"], 0xA600 + iterations * 47)
        self.assertTrue(all(pb.stopped and not pb.hooks for pb in self.instances))

    def test_caller_slot_and_bank_replacement_are_observed_independently(self):
        for failure in ("", "wrong_slot", "wrong_bank_load", "late_bank_load"):
            with self.subTest(failure=failure):
                self.failure = failure
                result = verifier.verify_mail_regression(self.fixtures)
                self.assertEqual(result["valid"], not failure)
                for replay in result["replays"].values():
                    self.assertTrue(replay["matches_exact_effect"])
                    self.assertEqual(replay["caller_verified"], not failure)
                    self.assertEqual([e["pc"] for e in replay["caller_events"]], [0x700A, 0x700C])
                    self.assertEqual(replay["return_event"]["pc"], 0x7010)

    def test_call_instruction_contract_is_checked_before_emulation(self):
        path = self.root / "broken" / "pokegold.gbc"
        rom = bytearray(path.read_bytes())
        rom[0x1300A] = 0
        path.write_bytes(rom)
        self.fixtures["broken"]["rom_sha256"] = sha256_file(path)
        with self.assertRaisesRegex(ValueError, "farcall"):
            verifier.verify_mail_regression(self.fixtures)
        self.opened.assert_not_called()

    def submission(self):
        replay = verifier.verify_mail_regression(self.fixtures)["replays"]["baseline"]
        events = replay["caller_events"] + replay["pointer_events"] + [replay["return_event"]]
        self.trace = [{"event_type": "instruction", "seq": index, "bank": event["bank"], "pc": event["pc"],
                       "regs": event["registers"], "basis": replay["basis"]} for index, event in enumerate(events)]
        rom = (self.root / "broken" / "pokegold.gbc").read_bytes()
        for event in self.trace:
            event["opcode"] = rom[event["bank"] * 0x4000 + event["pc"] % 0x4000]
        self.write_trace()
        (self.root / "recipe.json").write_text(json.dumps({"state": "recording/initial.state", "frames": 1, "buttons": []}))
        (self.root / "regression.json").write_text(json.dumps(verifier.REGRESSION))
        self.fixtures["broken"]["source_tree_sha256"] = "source"
        report = {key: self.fixtures["broken"][key] for key in BASIS_FIELDS}
        report.update({"proof_status": "complete", "repro_command": "descriptive command, never executed",
                       "evidence_atoms": [{"claim_type": "diagnosis.root_cause", "proof_status": "instruction_observed",
                                           "precision": dict(verifier.CAUSE), "detail": {
                                               "invariant": dict(verifier.INVARIANT), "intervention": dict(verifier.INTERVENTION),
                                               "reproducer": "recipe.json", "regression": "regression.json",
                                               "causal_chain": [{"trace": "trace.jsonl", "seq": event["seq"]} for event in self.trace],
                                               "scope": "known staged case", "uncertainty": "not blind"}}]})
        self.opened.reset_mock()
        return report

    def write_trace(self):
        (self.root / "trace.jsonl").write_text("\n".join(json.dumps(event) for event in self.trace))

    def diagnose(self, report):
        return verifier.verify_mail_diagnosis(report, fixtures=self.fixtures, artifact_root=self.root)

    def test_submitted_chain_replays_and_scores_as_assisted(self):
        report = self.submission()
        verification = self.diagnose(report)
        self.assertTrue(all(verification[key] is True for key in REPLAY_CHECKS))
        self.assertEqual(self.opened.call_count, 4)
        score = score_diagnosis(report, expected_basis=self.fixtures["broken"], accepted_causes=[verifier.CAUSE],
                                verify_replay=self.diagnose, assistance_events=["staged"])
        self.assertTrue(score["solved"])
        self.assertFalse(score["autonomous"])

    def test_native_first_frame_basis_is_supported_but_conflicting_later_basis_is_rejected(self):
        report = self.submission()
        for event in self.trace[1:]:
            del event["basis"]
        self.write_trace()
        self.assertTrue(self.diagnose(report)["causal_chain_replayed"])
        self.opened.reset_mock()
        self.trace[-1]["basis"] = {"rom_sha256": "stale"}
        self.write_trace()
        with self.assertRaisesRegex(ValueError, "stale causal trace"):
            self.diagnose(report)
        self.opened.assert_not_called()

    def test_success_markers_and_boolean_registers_cannot_replace_instruction_evidence(self):
        report = self.submission()
        self.trace[0]["event_type"] = "success"
        self.write_trace()
        with self.assertRaisesRegex(ValueError, "not an instruction"):
            self.diagnose(report)
        self.opened.assert_not_called()
        self.trace[0]["event_type"] = "instruction"
        self.trace[-2]["regs"]["A"] = False
        self.write_trace()
        self.assertFalse(self.diagnose(report)["causal_chain_replayed"])

    def test_wrong_source_location_rejected_without_emulation(self):
        original = self.submission()
        for key, value in (("source_line", 532), ("source_file", "engine/pokemon/mail.asm"),
                           ("source_symbol", "ClearPartyMonMail")):
            report = copy.deepcopy(original)
            report["evidence_atoms"][0]["precision"][key] = value
            score = score_diagnosis(report, expected_basis=self.fixtures["broken"], accepted_causes=[verifier.CAUSE],
                                    verify_replay=self.diagnose, assistance_events=[])
            self.assertFalse(score["solved"])
            self.assertIn("cause_location_mismatch", score["problems"])
        self.opened.assert_not_called()

    def test_submitted_missing_reordered_duplicate_and_forged_citations_rejected(self):
        report = self.submission()
        detail = report["evidence_atoms"][0]["detail"]
        chain = copy.deepcopy(detail["causal_chain"])
        for bad in (chain[1:], list(reversed(chain)), chain + chain[:1]):
            detail["causal_chain"] = bad
            self.assertFalse(self.diagnose(report)["causal_chain_replayed"])
        detail["causal_chain"] = chain
        self.trace[0]["regs"]["A"] = 3
        self.write_trace()
        self.assertFalse(self.diagnose(report)["causal_chain_replayed"])
        self.trace[0]["regs"]["A"] = 2
        self.trace[0]["opcode"] = 0
        self.write_trace()
        self.assertFalse(self.diagnose(report)["causal_chain_replayed"])

    def test_stale_submitted_basis_and_invalid_sequences_rejected_before_emulation(self):
        report = self.submission()
        original = copy.deepcopy(self.trace)
        for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256", "state_basis"):
            self.trace = copy.deepcopy(original)
            self.trace[0]["basis"][key] = "stale"
            self.write_trace()
            with self.assertRaisesRegex(ValueError, "stale causal trace"):
                self.diagnose(report)
        self.trace = original
        self.write_trace()
        ref = report["evidence_atoms"][0]["detail"]["causal_chain"][0]
        for seq in (-1, True, "0", 999):
            ref["seq"] = seq
            with self.assertRaisesRegex(ValueError, "sequence"):
                self.diagnose(report)
        ref["seq"] = 0
        self.trace.append(self.trace[0])
        self.write_trace()
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.diagnose(report)
        self.trace.pop()
        self.write_trace()
        ref["trace_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "content hash"):
            self.diagnose(report)
        self.opened.assert_not_called()

    def test_invalid_submission_contracts_rejected_before_emulation(self):
        original = self.submission()
        for key, value in (("invariant", {"expected": 2}),
                           ("intervention", {"at": "ByteFill", "register": "A", "expected": 0, "value": 1}),
                           ("causal_chain", []), ("reproducer", "../outside.json"), ("regression", "")):
            report = copy.deepcopy(original)
            report["evidence_atoms"][0]["detail"][key] = value
            with self.assertRaises(ValueError):
                self.diagnose(report)
        for name, bad in (("recipe.json", {"frames": 0}), ("regression.json", {"clear": "sPartyMon3Mail"})):
            path = self.root / name
            before = path.read_text()
            path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):
                self.diagnose(original)
            path.write_text(before)
        self.opened.assert_not_called()

    def test_unobserved_or_invalid_execution_cleans_up_and_rejects(self):
        for failure in ("preimage", "duplicate_entry", "missing_intervention", "missing_return", "duplicate_return"):
            with self.subTest(failure=failure):
                self.failure = failure
                with self.assertRaises(ValueError):
                    verifier.verify_mail_regression(self.fixtures)
                self.assertTrue(all(pb.stopped and not pb.hooks for pb in self.instances))

    def test_changed_schedule_is_not_authorized_by_a_matching_file_hash(self):
        path = self.root / "fixed" / "inputs.json"
        path.write_text(json.dumps({"frames": 1, "buttons": ["a"]}))
        self.fixtures["fixed"]["recording_sha256"] = sha256_file(path)
        with self.assertRaises(ValueError):
            verifier.verify_mail_regression(self.fixtures)
        self.opened.assert_not_called()

    def test_actual_backend_and_initial_bytes_are_checked_before_ticking(self):
        class DifferentBackend(Backend):
            pass
        for mismatch in ("backend", "initial_bytes"):
            with self.subTest(mismatch=mismatch):
                pb = (DifferentBackend if mismatch == "backend" else Backend)(self.before, False, "")
                if mismatch == "initial_bytes":
                    pb.memory.data[0x600] ^= 1
                self.opened.side_effect = None
                self.opened.return_value = pb
                with patch.object(pb, "tick") as tick, self.assertRaises(ValueError):
                    verifier.verify_mail_regression(self.fixtures)
                tick.assert_not_called()
                self.assertTrue(pb.stopped)
                self.assertFalse(pb.hooks)
