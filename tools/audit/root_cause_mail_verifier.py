"""Evaluator-owned whole-SRAM replay for the known mail-removal development case.

This module must not be imported by the diagnostic runner. Fixture identities
and accepted source locations belong to the evaluator, not the submission.
"""
from __future__ import annotations

import json
import argparse
import sys
from pathlib import Path

from tools.audit.root_cause_fixtures import verify_export
from tools.audit.root_cause_evaluator import BASIS_FIELDS, score_diagnosis
from tools.debugger.provenance import parse_symbol_table
from tools.debugger.report_envelope import replay_state_basis, sha256_file
from tools.trace import runtime


CAUSE = {"source_file": "engine/pokemon/mon_menu.asm",
         "source_symbol": "MonMailAction.RemoveMailToBag", "source_line": 533}
INVARIANT = {"at": "ClearPartyMonMail", "register": "A", "expected": 2}
INTERVENTION = {"at": "ClearPartyMonMail", "register": "A", "expected": 17, "value": 2}
REGRESSION = {"bank": 0, "start": 0xA000, "length": 8192,
              "clear": "sPartyMon3Mail", "clear_bytes": 47,
              "preserve_other_bytes": True, "at": "caller_return"}


def verify_mail_regression(fixtures: dict) -> dict:
    """Replay baseline, slot restoration, wrong-slot control, and fixed source.

    Fixture identities belong to the evaluator. Validate both bases before
    opening an emulator. Only the two intervention runs change A, at callee
    entry with its expected bank-byte value; source, ROM, and state stay read-only.
    Compare all 8 KiB of physical SRAM bank zero at caller return.
    """
    prepared = {}
    backend = runtime.load_pyboy("PyBoy is required to verify the mail regression")
    backend_name = f"{backend.__module__}.{backend.__name__}"
    backend_hash = sha256_file(sys.modules[backend.__module__].__file__)
    for side in ("broken", "fixed"):
        fixture = fixtures[side]
        root, recording = Path(fixture["root"]), Path(fixture["recording"])
        if not verify_export(root, fixture):
            raise ValueError(f"{side} source identity differs")
        for name, digest in (("pokegold.gbc", "rom_sha256"), ("pokegold.sym", "symbols_sha256")):
            if sha256_file(root / name) != fixture[digest]:
                raise ValueError(f"{side} {name} identity differs")
        if (replay_state_basis(recording / "initial.state", 1) != fixture["state_basis"]
                or sha256_file(recording / "inputs.json") != fixture["recording_sha256"]
                or json.loads((recording / "inputs.json").read_text()) != {"frames": 1, "buttons": []}):
            raise ValueError(f"{side} recording identity or schedule differs")
        if (fixture["backend"] != backend_name or fixture["backend_sha256"] != backend_hash
                or fixture["selected_slot"] != 2 or fixture["mail_record_bytes"] != 47):
            raise ValueError(f"{side} backend or mail fixture contract differs")
        table = parse_symbol_table(root / "pokegold.sym")
        party, mailbox, callee = (table[name] for name in ("sPartyMail", "sMailboxes", "ClearPartyMonMail"))
        symbol, separator, offset = fixture["return_checkpoint"].partition("+")
        target = table[symbol]
        return_pc = target["address"] + (int(offset, 0) if separator else 0)
        if (party["bank"] != 0 or mailbox["bank"] != 0
                or not 0xA000 <= party["address"] <= 0xC000 - 282
                or not 0xA000 <= mailbox["address"] <= 0xC000 - 470
                or return_pc // 0x4000 != target["address"] // 0x4000):
            raise ValueError(f"{side} mail region or return checkpoint differs")
        call_offset = target["bank"] * 0x4000 + (return_pc - 6) % 0x4000
        call_bytes = (root / "pokegold.gbc").read_bytes()[call_offset:call_offset + 6]
        if call_bytes != bytes((0x3E, callee["bank"], 0x21,
                                callee["address"] & 255, callee["address"] >> 8, 0xCF)):
            raise ValueError(f"{side} farcall instruction contract differs")
        points = {name: (table[symbol]["bank"], table[symbol]["address"])
                  for name, symbol in (("multiply", "AddNTimes"),
                                       ("iteration", "AddNTimes.loop"), ("fill", "ByteFill"))}
        prepared[side] = (root, recording, party, mailbox, callee, (target["bank"], return_pc), points)

    replays = {}
    for mode, side, slot in (("baseline", "broken", None), ("restore", "broken", 2),
                             ("control", "broken", 3), ("fixed", "fixed", None)):
        root, recording, party, mailbox, callee, returned, points = prepared[side]
        pb = runtime.open_pyboy(root / "pokegold.gbc", "PyBoy is required to verify the mail regression")
        hooked = []
        snapshots, changes = [], []
        pointer_events = []
        caller_events, return_events = [], []
        event_count = 0
        callback_errors = []
        try:
            if type(pb) is not backend:
                raise ValueError(f"{mode} runtime backend differs")
            runtime.disable_realtime(pb)
            with (recording / "initial.state").open("rb") as handle:
                pb.load_state(handle)

            def snapshot():
                return bytes(pb.memory[0, address] for address in range(0xA000, 0xC000))

            before = snapshot()
            for name, entry, length in (("party", party, 282), ("mailbox", mailbox, 470)):
                start = entry["address"] - 0xA000
                if before[start:start + length].hex().upper() != fixtures[side]["before"][name]:
                    raise ValueError(f"{mode} initial {name} bytes differ")

            def capture(name, point):
                nonlocal event_count
                registers = {key: int(getattr(pb.register_file, key)) for key in ("A", "B", "C", "HL", "E")}
                registers["BC"] = registers["B"] * 256 + registers["C"]
                event = {"seq": event_count, "point": name, "bank": point[0], "pc": point[1], "registers": registers}
                event_count += 1
                return event

            def enter(_context):
                if snapshots:
                    return
                if pointer_events or int(pb.register_file.A) != callee["bank"]:
                    # PyBoy may swallow exceptions raised inside hook callbacks.
                    callback_errors.append(f"{mode} intervention preimage or hit count differs")
                    return
                pointer_events.append(capture("entry", (callee["bank"], callee["address"])))
                if slot is not None:
                    changes.append({"register": "A", "before": int(pb.register_file.A), "after": slot})
                    pb.register_file.A = slot

            point = (callee["bank"], callee["address"])
            pb.hook_register(*point, enter, None)
            hooked.append(point)
            for name, point in points.items():
                def observe(_context, name=name, point=point):
                    if pointer_events and not snapshots:
                        pointer_events.append(capture(name, point))
                pb.hook_register(*point, observe, None)
                hooked.append(point)
            for name, offset in (("slot", -6), ("bank_load", -4)):
                point = (returned[0], returned[1] + offset)
                def observe_caller(_context, name=name, point=point):
                    if not snapshots:
                        caller_events.append(capture(name, point))
                pb.hook_register(*point, observe_caller, None)
                hooked.append(point)
            def observe_return(_context):
                return_events.append(capture("return", returned))
                snapshots.append(snapshot())
            pb.hook_register(*returned, observe_return, None)
            hooked.append(returned)
            pb.tick(1, False, False)
            if callback_errors:
                raise ValueError(callback_errors[0])
            if len(snapshots) != 1 or len(changes) != int(slot is not None):
                raise ValueError(f"{mode} return or intervention was not observed exactly once")
            after = snapshots[0]
            intended = bytearray(before)
            start = party["address"] - 0xA000 + 2 * 47
            intended[start:start + 47] = bytes(47)
            expected = bytearray(before)
            affected = (mailbox["address"] - 0xA000 + 234 if mode == "baseline" else
                        party["address"] - 0xA000 + (3 if mode == "control" else 2) * 47)
            expected[affected:affected + 47] = bytes(47)
            # Independently check the observed loop, not diagnostic taint flags.
            # The fixed routine recovers the slot from E after farcall; the two
            # intervention runs replace A at entry on the broken source only.
            count = callee["bank"] if mode == "baseline" else 3 if mode == "control" else 2
            expected_chain = [("entry", {"A": callee["bank"]}),
                              ("multiply", {"A": count, "BC": 47, "HL": party["address"]})]
            if mode == "fixed":
                expected_chain[0][1]["E"] = 2
            expected_chain.extend(("iteration", {"A": count - index, "BC": 47,
                                                  "HL": party["address"] + index * 47})
                                  for index in range(count))
            expected_chain.append(("fill", {"A": 0, "BC": 47, "HL": 0xA000 + affected}))
            chain_verified = len(pointer_events) == len(expected_chain) and all(
                event["seq"] == index + 2 and event["point"] == name
                and all(event["registers"][key] == value for key, value in registers.items())
                for index, (event, (name, registers)) in enumerate(zip(pointer_events, expected_chain)))
            chain_verified = chain_verified and return_events[0]["seq"] == len(expected_chain) + 2
            replays[mode] = {
                "initial_sram": before.hex().upper(), "return_sram": after.hex().upper(),
                "matches_exact_effect": after == expected, "passes_intended_contract": after == intended,
                "interventions": changes, "return_checkpoint": fixtures[side]["return_checkpoint"],
                "pointer_chain_verified": chain_verified, "pointer_events": pointer_events,
                "caller_events": caller_events, "return_event": return_events[0],
                "caller_verified": (len(caller_events) == 2
                                    and [event["point"] for event in caller_events] == ["slot", "bank_load"]
                                    and [event["seq"] for event in caller_events] == [0, 1]
                                    and [event["registers"]["A"] for event in caller_events] == [2, callee["bank"]]),
                "changed_addresses": [f"{0xA000 + index:04X}" for index, (old, new) in enumerate(zip(before, after)) if old != new],
                "basis": {key: fixtures[side][key] for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256", "state_basis")},
            }
        finally:
            try:
                for point in hooked:
                    pb.hook_deregister(*point)
            finally:
                pb.stop(save=False)
    checks = {f"{mode}_exact_effect": result["matches_exact_effect"] for mode, result in replays.items()}
    checks.update({f"{mode}_pointer_chain": result["pointer_chain_verified"] for mode, result in replays.items()})
    checks.update({f"{mode}_caller": result["caller_verified"] for mode, result in replays.items()})
    checks["intended_contract_contrast"] = {mode: result["passes_intended_contract"] for mode, result in replays.items()} == {
        "baseline": False, "restore": True, "control": False, "fixed": True}
    return {"valid": all(checks.values()), "checks": checks, "replays": replays,
            "known_limits": ["Known, staged development case; not blind or fresh-game navigation evidence.",
                             "Whole SRAM bank-zero regression at caller return; not verification of a submitted causal explanation."]}


def verify_mail_diagnosis(report: dict, *, fixtures: dict, artifact_root: Path) -> dict:
    """Match submitted instruction citations to independent execution checkpoints.

    Only the fixed one-frame recipe and evaluator-owned interventions execute.
    No command or success flag from the submission is used. Source location and
    complete envelope validation remain the scorer's responsibility.
    """
    claims = [atom for atom in report["evidence_atoms"] if atom.get("claim_type") == "diagnosis.root_cause"]
    if len(claims) != 1:
        raise ValueError("one mail root-cause claim is required")
    detail = claims[0]["detail"]
    if detail.get("invariant") != INVARIANT or detail.get("intervention") != INTERVENTION:
        raise ValueError("mail invariant or intervention differs")

    def artifact(name):
        if not isinstance(name, str) or not name:
            raise ValueError("evidence artifact path is missing")
        path = (artifact_root / name).resolve()
        if not path.is_relative_to(artifact_root.resolve()):
            raise ValueError("evidence artifact is outside the submission directory")
        return path

    recipe = json.loads(artifact(detail["reproducer"]).read_text(encoding="utf-8"))
    regression = json.loads(artifact(detail["regression"]).read_text(encoding="utf-8"))
    if recipe != {"state": "recording/initial.state", "frames": 1, "buttons": []}:
        raise ValueError("reproducer is not the minimal recorded one-frame trigger")
    if regression != REGRESSION:
        raise ValueError("regression must clear the selected mail and preserve the rest of SRAM")

    chain = detail.get("causal_chain")
    if not isinstance(chain, list) or not chain:
        raise ValueError("causal chain is missing")
    cited, traces = [], {}
    for reference in chain:
        name, seq = reference["trace"], reference["seq"]
        if type(seq) is not int or seq < 0:
            raise ValueError("causal trace sequence must be a nonnegative integer")
        if "trace_sha256" in reference and sha256_file(artifact(name)) != reference["trace_sha256"]:
            raise ValueError("stale causal trace content hash")
        if name not in traces:
            traces[name] = [json.loads(line) for line in artifact(name).read_text(encoding="utf-8").splitlines() if line.strip()]
            # Native instruction captures store their identity on the first
            # frame. A later explicit basis must agree with that same fixture.
            bases = [traces[name][0].get("basis", {})] if traces[name] else [{}]
            bases.extend(event["basis"] for event in traces[name][1:] if "basis" in event)
            for basis in bases:
                for key in ("rom_sha256", "symbols_sha256", "backend", "backend_sha256", "state_basis"):
                    if basis.get(key) != fixtures["broken"][key]:
                        raise ValueError(f"stale causal trace {key}")
        matches = [event for event in traces[name] if type(event.get("seq")) is int and event["seq"] == seq]
        if len(matches) != 1:
            raise ValueError("causal trace sequence is missing or duplicated")
        event = matches[0]
        if event.get("event_type") != "instruction":
            raise ValueError("causal citation is not an instruction event")
        cited.append(event)

    replay = verify_mail_regression(fixtures)
    baseline = replay["replays"]["baseline"]
    expected = baseline["caller_events"] + baseline["pointer_events"] + [baseline["return_event"]]
    rom = (Path(fixtures["broken"]["root"]) / "pokegold.gbc").read_bytes()
    chain_matches = len(cited) == len(expected)
    for event, actual in zip(cited, expected):
        registers = event.get("regs", {})
        chain_matches = chain_matches and all(type(event.get(key)) is int and event[key] == actual[key]
                                              for key in ("bank", "pc"))
        rom_offset = actual["bank"] * 0x4000 + actual["pc"] % 0x4000
        chain_matches = chain_matches and type(event.get("opcode")) is int and event["opcode"] == rom[rom_offset]
        chain_matches = chain_matches and all(type(registers.get(key)) is int and registers[key] == actual["registers"][key]
                                              for key in ("A", "B", "C", "HL", "E"))
    broken = baseline["matches_exact_effect"] and not baseline["passes_intended_contract"]
    fixed = replay["replays"]["fixed"]
    return {
        "failure_reproduced": broken,
        "causal_chain_replayed": replay["valid"] and chain_matches,
        "alternatives_rejected": replay["valid"],
        "minimized_reproducer_replayed": broken and baseline["initial_sram"] != baseline["return_sram"],
        "regression_failed_broken": broken,
        "regression_passed_control": fixed["matches_exact_effect"] and fixed["passes_intended_contract"],
        "evidence": replay,
        "known_limits": ["Known staged development case; not blind or fresh-game navigation evidence.",
                         "One-frame input minimization; materialized RAM is not minimized."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", type=Path, help="Evaluator-owned fixture identity JSON")
    parser.add_argument("submission", type=Path, help="Diagnosis JSON with relative evidence paths")
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    report = json.loads(args.submission.read_text(encoding="utf-8"))
    verification = {}

    def replay(submission):
        verification.update(verify_mail_diagnosis(submission, fixtures=fixtures, artifact_root=args.submission.parent))
        return verification

    score = score_diagnosis(report, expected_basis={key: fixtures["broken"][key] for key in BASIS_FIELDS},
                            accepted_causes=[CAUSE], verify_replay=replay,
                            assistance_events=["Evaluator author supplied known development cause and staged reproduction"])
    print(json.dumps({"score": score, "verification": verification}, indent=2))
    return 0 if score["solved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
