from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest
import json

from tools.debugger.runtime_experiment import replay_experiment_report, run_runtime_experiment


class FakePyBoy:
    def __init__(self):
        self.register_file = SimpleNamespace(
            A=0, F=0, B=0, C=0, D=203, E=7, H=0, L=0, SP=0xC100, PC=0x4000,
        )
        self.memory = defaultdict(int, {0xC001: 44})
        self.hooks = {}
        self.closed = False

    def load_state(self, handle):
        assert handle.read() == b"initial state"

    def hook_register(self, bank, pc, callback, context):
        if (bank, pc) in self.hooks:
            raise ValueError("duplicate hook")
        self.hooks[bank, pc] = callback

    def hook_deregister(self, bank, pc):
        del self.hooks[bank, pc]

    def tick(self, *_args):
        for pc in (0x4000, 0x4001):
            self.register_file.PC = pc
            if pc == 0x4001:
                self.memory[0xC001] = 46 if self.register_file.D == 2 else 45
            if (1, pc) in self.hooks:
                self.hooks[1, pc](None)

    def stop(self, save=False):
        assert save is False
        self.closed = True


class RuntimeExperimentTests(unittest.TestCase):
    def test_recorded_experiment_replays_and_checks_observations(self):
        report = self.run_experiment()
        path = self.root / "experiment.json"
        path.write_text(json.dumps(report))
        self.factory.return_value = FakePyBoy()
        with patch("tools.debugger.runtime_experiment.trace_runtime.load_pyboy", return_value=FakePyBoy):
            replay = replay_experiment_report(path)
        self.assertTrue(replay["valid"], replay["errors"])
        self.assertEqual(replay["events"], report["events"])
        report["final"]["watch_values"]["wBattleMonHP"] = "FFFF"
        path.write_text(json.dumps(report))
        self.factory.return_value = FakePyBoy()
        with patch("tools.debugger.runtime_experiment.trace_runtime.load_pyboy", return_value=FakePyBoy):
            replay = replay_experiment_report(path)
        self.assertFalse(replay["valid"])
        self.assertIn("replayed final differs", str(replay["errors"]))

    def test_stale_recording_identity_rejects_before_emulator_is_opened(self):
        report = self.run_experiment()
        path = self.root / "experiment.json"
        self.factory.reset_mock()
        for filename in ("unit.gbc", "test.sym", "initial.state"):
            with self.subTest(filename=filename):
                target = self.root / filename
                original = target.read_bytes()
                target.write_bytes(b"changed")
                path.write_text(json.dumps(report))
                with self.assertRaisesRegex(ValueError, "stale"):
                    replay_experiment_report(path)
                target.write_bytes(original)
        for key, value in (("frames", 2), ("backend_sha256", "other"), ("valid", False), ("executed", False)):
            changed = {**report, key: value}
            path.write_text(json.dumps(changed))
            with patch("tools.debugger.runtime_experiment.trace_runtime.load_pyboy", return_value=FakePyBoy):
                with self.assertRaises(ValueError):
                    replay_experiment_report(path)
        self.factory.assert_not_called()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "unit.gbc").write_bytes(bytes(0x8000))
        (self.root / "test.sym").write_text(
            "01:4000 Before\n01:4001 After\n00:C000 wBattleMonHP\n", encoding="utf-8",
        )
        (self.root / "initial.state").write_bytes(b"initial state")
        self.emulator = FakePyBoy()
        self.factory = self.enterContext(patch(
            "tools.debugger.runtime_experiment.trace_runtime.open_pyboy",
            return_value=self.emulator,
        ))
        self.patch = {"at": "Before", "register": "D", "expected": 203, "value": 2}

    def run_experiment(self, **overrides):
        args = dict(
            rom_path="unit.gbc", symbols_path="test.sym", save_state="initial.state",
            frames=1, observe=("Before", "After"), watch_symbols=("wBattleMonHP",),
            interventions=(self.patch,), root=self.root,
        )
        args.update(overrides)
        return run_runtime_experiment(**args)

    def test_observes_intervention_and_result_without_saving_input_files(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        report = self.run_experiment()
        self.assertTrue(report["valid"], report["errors"])
        self.assertTrue(report["executed"])
        event = report["events"][0]
        self.assertEqual(event["registers"]["register_d"], "CB")
        self.assertEqual(event["after_registers"]["register_d"], "02")
        self.assertEqual(report["final"]["watch_values"]["wBattleMonHP"], "002E")
        self.assertTrue(report["interventions"][0]["applied"])
        self.assertTrue(self.emulator.closed)
        self.assertFalse(self.emulator.hooks)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_baseline_has_no_mutation(self):
        report = self.run_experiment(interventions=())
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["final"]["watch_values"]["wBattleMonHP"], "002D")
        self.assertEqual(self.emulator.register_file.D, 203)

    def test_hl_only_backend_preserves_the_other_byte(self):
        for register, expected, value, pair in (("H", 0xAB, 0x12, 0x12CD), ("L", 0xCD, 0x34, 0xAB34)):
            with self.subTest(register=register):
                self.emulator = FakePyBoy()
                del self.emulator.register_file.H
                del self.emulator.register_file.L
                self.emulator.register_file.HL = 0xABCD
                self.factory.return_value = self.emulator
                report = self.run_experiment(interventions=(
                    {"at": "Before", "register": register, "expected": expected, "value": value},
                ))
                self.assertTrue(report["valid"], report["errors"])
                self.assertEqual(self.emulator.register_file.HL, pair)
                self.assertEqual(report["events"][0]["registers"]["register_h"], "AB")
                self.assertEqual(report["events"][0]["registers"]["register_l"], "CD")

    def test_invalid_arguments_reject_before_opening_emulator(self):
        cases = [dict(frames=value) for value in (0, -1, True, "1")]
        cases += [dict(observe=(value,)) for value in ("", "Missing", "Before+-1", "Before+16384")]
        cases += [dict(watch_symbols=("Missing",))]
        for key in ("rom_path", "symbols_path", "save_state"):
            cases.append({key: "missing.file"})
            cases.append({key: ""})
        for key, values in (("register", ("", "SP", "unknown")),
                            ("value", (-1, 256, True, "2", None)),
                            ("expected", (-1, 256, True, "203", None))):
            for value in values:
                cases.append(dict(interventions=({**self.patch, key: value},)))
            incomplete = dict(self.patch)
            del incomplete[key]
            cases.append(dict(interventions=(incomplete,)))
        cases += [dict(interventions=({**self.patch, "at": "Missing"},))]
        cases += [dict(interventions=({**self.patch, "at": value},)) for value in (None, [], "")]
        cases += [dict(interventions=(self.patch, self.patch))]
        for args in cases:
            with self.subTest(args=args):
                report = self.run_experiment(**args)
                self.assertFalse(report["valid"])
                self.assertFalse(report["executed"])
        self.factory.assert_not_called()

    def test_preimage_mismatch_prevents_every_change_at_that_hook(self):
        report = self.run_experiment(interventions=(
            self.patch, {"at": "Before", "register": "E", "expected": 99, "value": 4},
        ))
        self.assertFalse(report["valid"])
        self.assertEqual(self.emulator.register_file.D, 203)
        self.assertEqual(self.emulator.register_file.E, 7)
        self.assertTrue(all(not item["applied"] for item in report["interventions"]))
        self.assertTrue(self.emulator.closed)

    def test_unreached_hook_and_unapplied_intervention_are_not_success(self):
        report = self.run_experiment(interventions=({**self.patch, "at": "Before+2"},))
        self.assertFalse(report["valid"])
        self.assertFalse(report["interventions"][0]["applied"])
        self.assertIn("Before+2", " ".join(report["errors"]))

    def test_emulator_failure_cleans_up_hooks_and_does_not_save(self):
        def fail(*args):
            raise RuntimeError("replay failed")
        self.emulator.tick = fail
        report = self.run_experiment()
        self.assertFalse(report["valid"])
        self.assertIn("replay failed", " ".join(report["errors"]))
        self.assertFalse(self.emulator.hooks)
        self.assertTrue(self.emulator.closed)


if __name__ == "__main__":
    unittest.main()
