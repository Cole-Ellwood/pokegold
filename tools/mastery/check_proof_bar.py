"""Proof-bar verifier for the GSC mastery training-loop /pgoal.

Checks the three remaining proof-bar conditions (cross-model dropped per
Cole 2026-05-16):

  C1  cross-replay  >= 5 distinct fresh replays show top-match lift in
                    the intervention arm vs the baseline arm
  C2  cross-packet  >= 2 consecutive packets sustain the lift
  C3  counterfactual same-replay baseline arm regresses to ~15/30 while
                    intervention arm exceeds it by a delta significant
                    against the baseline noise floor

Reads `docs/pokemon_mastery/measurement_progress_ledger.csv` for scored
runs. A/B arm runs are tagged in the run-id field (suffix `_baseline`
vs `_intervention`).

Exit code 0 always; status is reported on stdout for the harness to
parse. Use --status for a single STATUS=<state> line, or --report for
the full breakdown.

States:
  proof_met         all three conditions pass; manual gate next
  diagnosis_ready   docs/pokemon_mastery/reviews/proof_bar_diagnosis.md
                    exists and the harness has run >= 2 packets producing
                    no lift; manual gate to accept the diagnosis
  iterating         neither completion path satisfied yet

Designed to be cheap: pure CSV read, no replay download, no model call.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = REPO_ROOT / "docs" / "pokemon_mastery" / "measurement_progress_ledger.csv"
DIAGNOSIS = REPO_ROOT / "docs" / "pokemon_mastery" / "reviews" / "proof_bar_diagnosis.md"

# Cross-replay floor: distinct fresh replays in the intervention arm.
CROSS_REPLAY_MIN = 5
# Cross-packet floor: consecutive packets sustaining lift.
CROSS_PACKET_MIN = 2
# Top-match delta (intervention - baseline) considered significant.
# 15/30 is the established plateau; 18/30 is +1 sigma above the
# Codex/Claude/044/045 cluster. Tightens after we have a real noise
# floor from packet 046+ baseline arms.
LIFT_DELTA_MIN = 3


@dataclass
class Run:
    """One row of the measurement ledger that maps to a /pgoal arm run."""

    run_id: str
    date: str
    replay: str
    top_match: int
    decisions: int
    arm: str  # "baseline" | "intervention" | "legacy" (pre-A/B rows)
    packet: str  # e.g. "045", "046"
    raw: dict = field(default_factory=dict)


def parse_int(value: str) -> int | None:
    """Pull the numerator out of '15/30' style cells, or return None."""
    if not value:
        return None
    m = re.match(r"\s*(\d+)\s*/\s*\d+", value)
    if m:
        return int(m.group(1))
    if value.strip().isdigit():
        return int(value.strip())
    return None


def parse_decisions(value: str) -> int | None:
    if not value:
        return None
    if value.strip().isdigit():
        return int(value.strip())
    return None


# Packet 046+ runs MUST use the run_id format
#   pgoal_<NNN>_<arm>_<replay-id>_<date>
# where <NNN> is the 3-digit packet number, <arm> is exactly
# "baseline" or "intervention", and <replay-id> is the smogtours/showdown
# replay slug. Anything not matching this is treated as legacy (pre-A/B)
# and ignored by the proof-bar checks.
PGOAL_RUN_ID_RE = re.compile(r"^pgoal_(\d{3})_(baseline|intervention)_")


def detect_arm(run_id: str) -> str:
    m = PGOAL_RUN_ID_RE.match(run_id)
    return m.group(2) if m else "legacy"


def detect_packet(run_id: str) -> str:
    m = PGOAL_RUN_ID_RE.match(run_id)
    return m.group(1) if m else "?"


REPLAY_RE = re.compile(r"(smogtours-gen2ou-\d+|gen2ou-\d+)")


def detect_replay(pool: str, run_id: str) -> str:
    """Replay id from the ledger 'pool' column, falling back to run_id."""
    for source in (pool, run_id):
        if not source:
            continue
        m = REPLAY_RE.search(source)
        if m:
            return m.group(1)
    return ""


def load_runs() -> list[Run]:
    if not LEDGER.exists():
        return []
    runs: list[Run] = []
    with LEDGER.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            run_id = (row.get("run_id") or row.get("﻿run_id") or "").strip()
            if not run_id:
                continue
            top = parse_int(row.get("top_move_agreement", ""))
            dec = parse_decisions(row.get("scenario_count", ""))
            if top is None or dec is None:
                continue
            runs.append(
                Run(
                    run_id=run_id,
                    date=row.get("date_utc", "").strip(),
                    replay=detect_replay(row.get("pool", ""), run_id),
                    top_match=top,
                    decisions=dec,
                    arm=detect_arm(run_id),
                    packet=detect_packet(run_id),
                    raw=row,
                )
            )
    return runs


def evaluate(runs: list[Run]) -> dict:
    """Compute per-condition status. Pure function over the loaded runs."""

    intervention_runs = [r for r in runs if r.arm == "intervention"]
    baseline_runs = [r for r in runs if r.arm == "baseline"]

    # C1 cross-replay: distinct replays where the intervention arm beats
    # its same-replay baseline by >= LIFT_DELTA_MIN.
    baseline_by_replay = {r.replay: r for r in baseline_runs}
    lifted_replays = []
    pair_diagnostics = []
    for ir in intervention_runs:
        b = baseline_by_replay.get(ir.replay)
        if b is None:
            continue
        delta = ir.top_match - b.top_match
        pair_diagnostics.append(
            {
                "replay": ir.replay,
                "baseline": b.top_match,
                "intervention": ir.top_match,
                "delta": delta,
                "decisions": ir.decisions,
            }
        )
        if delta >= LIFT_DELTA_MIN:
            lifted_replays.append(ir.replay)
    c1_pass = len(set(lifted_replays)) >= CROSS_REPLAY_MIN

    # C2 cross-packet: at least CROSS_PACKET_MIN consecutive packets
    # where the intervention arm beats its same-replay baseline on at
    # least one replay in that packet.
    by_packet: dict[str, list[Run]] = defaultdict(list)
    for ir in intervention_runs:
        b = baseline_by_replay.get(ir.replay)
        if b is None:
            continue
        if ir.top_match - b.top_match >= LIFT_DELTA_MIN:
            by_packet[ir.packet].append(ir)
    sorted_packets = sorted(p for p in by_packet if p.isdigit())
    consecutive = 0
    longest = 0
    last = None
    for p in sorted_packets:
        if last is None or int(p) == int(last) + 1:
            consecutive += 1
            longest = max(longest, consecutive)
        else:
            consecutive = 1
        last = p
    c2_pass = longest >= CROSS_PACKET_MIN

    # C3 counterfactual: baseline arm should sit near plateau (~15/30
    # +/- 2) while intervention exceeds it. Operationalized as: across
    # all baseline runs of packet 046+, the mean top-match is in
    # [12, 18] AND there exists at least one (baseline, intervention)
    # same-replay pair with delta >= LIFT_DELTA_MIN.
    eligible_baselines = [r for r in baseline_runs if r.packet.isdigit() and int(r.packet) >= 46]
    if eligible_baselines:
        baseline_mean = sum(r.top_match for r in eligible_baselines) / len(eligible_baselines)
    else:
        baseline_mean = None
    c3_pass = (
        baseline_mean is not None
        and 12 <= baseline_mean <= 18
        and any(p["delta"] >= LIFT_DELTA_MIN for p in pair_diagnostics)
    )

    diagnosis_exists = DIAGNOSIS.exists() and DIAGNOSIS.stat().st_size > 200
    eligible_packets_with_runs = sorted({r.packet for r in runs if r.packet.isdigit() and int(r.packet) >= 46})

    if c1_pass and c2_pass and c3_pass:
        status = "proof_met"
    elif diagnosis_exists and len(eligible_packets_with_runs) >= 2:
        status = "diagnosis_ready"
    else:
        status = "iterating"

    return {
        "status": status,
        "c1_cross_replay": {
            "pass": c1_pass,
            "lifted_replays": sorted(set(lifted_replays)),
            "needed": CROSS_REPLAY_MIN,
        },
        "c2_cross_packet": {
            "pass": c2_pass,
            "longest_run": longest,
            "needed": CROSS_PACKET_MIN,
            "lifted_packets": sorted_packets,
        },
        "c3_counterfactual": {
            "pass": c3_pass,
            "baseline_mean_top_match": baseline_mean,
            "eligible_baseline_runs": len(eligible_baselines),
            "lift_delta_min": LIFT_DELTA_MIN,
        },
        "diagnosis_doc_exists": diagnosis_exists,
        "eligible_packets_with_runs": eligible_packets_with_runs,
        "pair_diagnostics": pair_diagnostics,
        "total_runs_seen": len(runs),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true", help="emit STATUS=<state> only")
    ap.add_argument("--report", action="store_true", help="emit human-readable breakdown")
    args = ap.parse_args()

    runs = load_runs()
    result = evaluate(runs)
    status = result["status"]

    if args.status or not args.report:
        print(f"STATUS={status}")
        if not args.report:
            return 0

    print()
    print(f"Proof bar status: {status}")
    print(f"  Total runs in ledger: {result['total_runs_seen']}")
    print(f"  Eligible packets (>=046): {', '.join(result['eligible_packets_with_runs']) or '(none)'}")
    print()
    c1 = result["c1_cross_replay"]
    print(f"C1 cross-replay  ({'PASS' if c1['pass'] else 'fail'}): "
          f"{len(c1['lifted_replays'])}/{c1['needed']} replays with intervention lift")
    if c1["lifted_replays"]:
        for r in c1["lifted_replays"]:
            print(f"    - {r}")
    c2 = result["c2_cross_packet"]
    print(f"C2 cross-packet  ({'PASS' if c2['pass'] else 'fail'}): "
          f"longest consecutive lift run = {c2['longest_run']}/{c2['needed']}")
    if c2["lifted_packets"]:
        print(f"    lifted packets: {', '.join(c2['lifted_packets'])}")
    c3 = result["c3_counterfactual"]
    print(f"C3 counterfactual ({'PASS' if c3['pass'] else 'fail'}): "
          f"baseline mean = {c3['baseline_mean_top_match']}; "
          f"eligible baseline runs = {c3['eligible_baseline_runs']}; "
          f"lift threshold = +{c3['lift_delta_min']}")
    print()
    if result["pair_diagnostics"]:
        print("Same-replay pairs:")
        for p in result["pair_diagnostics"]:
            print(f"  {p['replay']:40s} baseline={p['baseline']:>2} intervention={p['intervention']:>2} delta={p['delta']:+d}")
    print()
    print(f"Diagnosis doc present: {result['diagnosis_doc_exists']} ({DIAGNOSIS})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
