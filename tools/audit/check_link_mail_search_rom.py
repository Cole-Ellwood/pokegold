"""Known historical link-mail scan development fixture; never diagnostic input.

Run with two sanitized historical exports and a new output directory. This
stages malformed parser input, not a peer exchange or fresh-game navigation.
It checks the two searches only, not the later mail-copy/decode routines.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

from tools.audit.root_cause_fixtures import verify_export
from tools.damage_debugger.emulator import DebugSession
from tools.damage_debugger.safe_call import write_byte_banked
from tools.damage_debugger.symbols import SymbolTable
from tools.debugger.report_envelope import sha256_file
from tools.trace import runtime


def check_link_mail_search(broken: Path, fixed: Path, destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError(destination)
    prepared = {}
    for side, root in (("broken", broken), ("fixed", fixed)):
        root = root.resolve()
        identity = json.loads((root / "source_manifest.json").read_text())
        if not verify_export(root, identity):
            raise ValueError(f"{side} source identity differs")
        symbols = SymbolTable.load(root / "pokegold.sym")
        rom = (root / "pokegold.gbc").read_bytes()
        points = {name: symbols[f"Gen2ToGen2LinkComms.{name}"]
                  for name in ("next1", "loop2", "loop3", "loop4", "skip_mail")}
        bank = points["loop2"].bank
        if any(point.bank != bank for point in points.values()):
            raise ValueError("parser checkpoints must share a ROM bank")

        def code(start, end):
            return rom[bank * 0x4000 + (start & 0x3FFF):bank * 0x4000 + (end & 0x3FFF)]

        lo, hi = (symbols[name] for name in ("wLinkOTMail", "wLinkOTMailEnd"))
        pattern = bytes((0x21, lo.address & 255, lo.address >> 8))
        prefix = code(points["next1"].address, points["loop2"].address)
        if prefix.count(pattern) != 1 or hi.address - lo.address != 390 or lo.bank != hi.bank:
            raise ValueError("expected one parser buffer load and the historical 390-byte buffer")
        entry = points["next1"].address + prefix.index(pattern)
        reads = []
        for name, end, compare in (("loop2", "loop3", 0x20), ("loop3", "loop4", 0xFE)):
            fragment = code(points[name].address, points[end].address)
            matches = [i for i in range(len(fragment)) if any(fragment[i:].startswith(pattern)
                       for pattern in (bytes((0x2A, 0xFE, compare)), bytes((0x2A, 0x0B, 0xFE, compare))))]
            if len(matches) != 1:
                raise ValueError(f"{side} {name}: expected one native read/compare sequence")
            reads.append((name, points[name].address + matches[0]))
        prepared[side] = (root, identity, symbols, bank, entry, lo, hi, reads, points["skip_mail"].address)

    backend = runtime.load_pyboy("PyBoy is required for link-mail scan verification")
    report = {"development_only": True, "autonomous": False,
              "backend": f"{backend.__module__}.{backend.__name__}",
              "backend_sha256": sha256_file(sys.modules[backend.__module__].__file__),
              "known_limits": ["Staged parser entry; no live peer or navigation witness.",
                               "Known historical cause, not a blind diagnosis.",
                               "Search bounds only; later copy/decode behavior is outside this check."],
              "fixtures": {}, "cases": {}}
    recordings = {}
    schedule = json.dumps({"frames": 10, "buttons": []}) + "\n"
    for side, (root, identity, symbols, bank, entry, lo, hi, reads, skip_pc) in prepared.items():
        report["fixtures"][side] = {"root": str(root), "source_tree_sha256": identity["source_tree_sha256"],
                                    "rom_sha256": sha256_file(root / "pokegold.gbc"),
                                    "symbols_sha256": sha256_file(root / "pokegold.sym")}
        for case, payload in (("no_preamble", bytes(390)), ("only_preamble", bytes([0x20]) * 390),
                              ("preamble_then_no_data", bytes([0x20]) + bytes([0xFE]) * 389),
                              ("last_byte_preamble", bytes(389) + bytes([0x20]))):
            with DebugSession.open(str(root / "pokegold")) as session:
                pb = session.pyboy
                pb.tick(600, False, False)
                for offset, value in enumerate(payload):
                    write_byte_banked(pb, lo.address + offset, value, lo.bank)
                # Isolate parser execution from interrupt handlers. This setup is
                # part of the saved state and is not a runtime intervention.
                pb.memory[0xFFFF] = 0
                pb.memory[0x2000] = bank
                pb.memory[symbols["hROMBank"].address] = bank
                pb.register_file.SP = 0xDFFF
                pb.register_file.PC = entry
                state = io.BytesIO()
                pb.save_state(state)
            replays = []
            for _ in range(2):
                pb = runtime.open_pyboy(root / "pokegold.gbc", "PyBoy is required")
                hooks, events, terminal = [], [], []
                try:
                    runtime.disable_realtime(pb)
                    pb.load_state(io.BytesIO(state.getvalue()))
                    for name, pc in reads:
                        def observe(_context, name=name, pc=pc):
                            if terminal:
                                return
                            address = int(pb.register_file.HL)
                            events.append({"loop": name, "bank": bank, "pc": pc,
                                           "address": address, "value": int(pb.memory[address])})
                            if not lo.address <= address < hi.address:
                                terminal.append("out_of_bounds_read")
                        pb.hook_register(bank, pc, observe, None)
                        hooks.append(pc)

                    def skip(_context):
                        if not terminal:
                            terminal.append("skip_mail")

                    pb.hook_register(bank, skip_pc, skip, None)
                    hooks.append(skip_pc)
                    pb.tick(10, False, False)
                finally:
                    for pc in hooks:
                        pb.hook_deregister(bank, pc)
                    pb.stop(save=False)
                replays.append({"reads": events, "terminal": terminal})
            expected = "out_of_bounds_read" if side == "broken" else "skip_mail"
            count = 391 if side == "broken" else 390
            expected_loops = (["loop2"] * 390 if case in ("no_preamble", "last_byte_preamble")
                              else ["loop2"] + ["loop3"] * 389)
            if side == "broken":
                expected_loops.append("loop2" if case == "no_preamble" else "loop3")
            if (replays[0] != replays[1] or terminal != [expected]
                    or [e["address"] for e in events] != list(range(lo.address, lo.address + count))
                    or [e["loop"] for e in events] != expected_loops
                    or bytes(e["value"] for e in events[:390]) != payload):
                raise AssertionError(f"{side}/{case}: native scan or fresh replay differs")
            name = f"{side}_{case}"
            recordings[name] = state.getvalue()
            report["cases"][name] = {"entry_bank": bank, "entry_pc": entry,
                                      "buffer_start": lo.address, "buffer_end": hi.address,
                                      "read_count": count, "replay_equal": True, **replays[0]}
        if (not verify_export(root, identity)
                or sha256_file(root / "pokegold.gbc") != report["fixtures"][side]["rom_sha256"]
                or sha256_file(root / "pokegold.sym") != report["fixtures"][side]["symbols_sha256"]):
            raise ValueError(f"{side} source or build changed during capture")
    destination.mkdir(parents=True)
    for name, state in recordings.items():
        recording = destination / name / "recording"
        recording.mkdir(parents=True)
        (recording / "initial.state").write_bytes(state)
        (recording / "inputs.json").write_text(schedule, encoding="utf-8")
        report["cases"][name]["state_sha256"] = sha256_file(recording / "initial.state")
        report["cases"][name]["inputs_sha256"] = sha256_file(recording / "inputs.json")
    report["passed"] = True
    (destination / "evaluator_observations.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("broken", type=Path)
    parser.add_argument("fixed", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    result = check_link_mail_search(args.broken, args.fixed, args.destination)
    print(json.dumps({"passed": result["passed"], "development_only": True,
                      "cases": {name: {key: case[key] for key in ("read_count", "terminal", "replay_equal")}
                                for name, case in result["cases"].items()}}, indent=2))
