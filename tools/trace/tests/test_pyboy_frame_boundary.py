"""Real-backend regression for a hook reached as the emulated frame ends."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


def probe(backend_root: str) -> dict:
    sys.path.insert(0, backend_root)
    from pyboy import PyBoy

    # A self-contained synthetic ROM: scan zeroed RAM, then loop on a match.
    # No game asset or historical answer is needed to exercise the backend.
    rom = bytearray(32768)
    rom[0x150:0x15A] = bytes((0x21, 0, 0xC0, 0x2A, 0xFE, 0x20, 0x20, 0xFB, 0x18, 0xFE))
    rom[0x14D] = (-sum(rom[0x134:0x14D]) - 25) & 255
    results = []
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "frame_loop.gb"
        path.write_bytes(rom)
        for lcd in (0, 0x91):
            for frames in (1, 2, 10):
                snapshots = []
                for hooked in (False, True):
                    pb = PyBoy(str(path), window="null", sound=False, log_level="ERROR")
                    points = (0x150, 0x153, 0x154, 0x156, 0x158)
                    hits = []
                    try:
                        pb.set_emulation_speed(0)
                        pb.memory[0xFF50] = 1
                        pb.memory[0xFF40] = lcd
                        pb.memory[0xFFFF] = 0
                        pb.register_file.PC = 0x150
                        if hooked:
                            for pc in points:
                                pb.hook_register(0, pc, lambda _, pc=pc: hits.append(pc), None)
                        pb.tick(frames, False, False)
                        if pb.frame_count != frames or hooked and not hits:
                            raise AssertionError("requested frames or instruction hooks did not execute")
                        snapshots.append({
                            "registers": {name: int(getattr(pb.register_file, name))
                                          for name in ("A", "F", "B", "C", "D", "E", "HL", "SP", "PC")},
                            "vram": bytes(pb.memory[0x8000:0xA000]),
                            "wram": bytes(pb.memory[0xC000:0xE000]),
                            "oam": bytes(pb.memory[0xFE00:0xFEA0]),
                            "io_hram": bytes(pb.memory[0xFF00:0x10000]),
                        })
                    finally:
                        if hooked:
                            for pc in points:
                                try:
                                    pb.hook_deregister(0, pc)
                                except ValueError:
                                    # The hook at the frame boundary can already
                                    # be removed while its instruction is pending.
                                    if int(pb.memory[0, pc]) != rom[pc]:
                                        raise
                        pb.stop(save=False)
                if snapshots[0] != snapshots[1]:
                    raise AssertionError(f"hooks changed CPU or visible memory: LCD={lcd}, frames={frames}")
                results.append({"lcd": lcd, "frames": frames, "hook_count": len(hits), "same_state": True})
    return {"passed": True, "cases": results}


class PyBoyFrameBoundaryTests(unittest.TestCase):
    def test_dense_hooks_finish_frames_and_preserve_cpu_and_visible_memory(self):
        from tools.trace.runtime import load_pyboy
        try:
            backend = load_pyboy("PyBoy is needed for this real-backend regression")
        except SystemExit:
            self.skipTest("PyBoy is not installed")
        backend_root = Path(sys.modules[backend.__module__].__file__).parent.parent
        # The unfixed native backend loops without advancing emulated cycles.
        # Isolate it so this regression fails rather than hanging the test suite.
        try:
            result = subprocess.run(
                [sys.executable, "-m", "tools.trace.tests.test_pyboy_frame_boundary", "--probe", str(backend_root)],
                cwd=Path(__file__).resolve().parents[3], capture_output=True, text=True, timeout=15,
            )
        except subprocess.TimeoutExpired:
            self.fail("PyBoy did not complete the frame-boundary hook probe within 15 seconds")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 6)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe":
        print(json.dumps(probe(sys.argv[2])))
    else:
        unittest.main()
