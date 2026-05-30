#!/usr/bin/env python3
"""Autonomous bug-watcher for ROM code landings (P19).

When faulty new code lands in the ROM -- via ``debugger rom-edit propose`` or
via a ``git commit`` on the dev branch -- auto-watch runs the relevant
detectors and emits findings to ``audit/auto_watch_findings.jsonl`` so
regressions surface on the next build without having to ask.

First-slice scope (this module):

- The finding-row dataclass + JSONL append-only writer.
- A first detector wrapping ``tools.debugger.register_flow`` for the AG-NN
  transitive register-clobber class (the most-recurring failure class in
  this repo per docs/asm_authoring_guide.md sections 3.13 / 3.14).
- The ``--self-test`` entry point: synthesizes an AG-NN-class clobber
  regression in a tmp asm tree, runs the register_flow detector, asserts a
  detection finding is emitted for the broken function but NOT for the
  fixed function, and round-trips the finding through the writer.

Out of scope for this first slice (follow-up slices, with explicit
collision-risk re-declaration):

- CLI dispatch in ``tools/debugger/__main__.py``.
- Selftest component registration in ``tools/debugger/selftest.py``.
- The ``--on rom-edit-propose`` / ``--on commit`` triggers (post-commit
  trigger plumbing in ``scripts/install_debugger_hooks.py``).
- Heavy detectors: ``release_smoke`` floor, ``clobber_smoke``, full debugger
  selftest replay.
- Call-site correlation for AG-NN findings (caller's ``c`` load-bearing
  post-dispatch). First-slice detector is intentionally conservative: it
  flags any function whose clobber set contains ``c``. A follow-up slice
  will add caller analysis to reduce false positives.

Bug-class labels are provisional until the P20 catalog lands; first-slice
labels follow the names already in repo docs.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from . import register_flow
from .catalog import ROOT


SCHEMA_VERSION = 1
KIND = "auto_watch_finding"

DEFAULT_FINDINGS_STORE = Path("audit") / "auto_watch_findings.jsonl"

TRIGGER_KINDS = ("self-test", "rom-edit-propose", "commit")

# Provisional bug-class labels. The P20 bug-class catalog will tighten
# this list; first-slice labels follow names already in repo docs
# (asm_authoring_guide.md, audit/check_*.py, llm_pairing_rules.md).
KNOWN_BUG_CLASSES = (
    "ag_nn_register_clobber",       # AG-NN transitive register clobber
    "farcall_hl_clobber",           # farcall clobbers caller hl pre-target
    "farcall_a_clobber",            # farcall returns target c, not a
    "cross_bank_call",              # plain call to a label in another bank
    "save_format_drift",            # SAVE_FORMAT_VERSION unbumped on ram/ edit
    "release_smoke_regression",     # any release-smoke audit flipped red
    "selftest_regression",          # any v2 selftest component flipped red
    "clobber_smoke_regression",     # damage_debugger.clobber_smoke flipped red
    "watcher_unavailable",          # the watcher itself couldn't run
)

STATUS_VALUES = ("detected", "watcher_unavailable", "no_new_bug")
SEVERITY_VALUES = ("high", "medium", "low")


@dataclass(frozen=True)
class AutoWatchFinding:
    """One auto-watch finding row.

    The row carries both the generalized trigger/trigger_id/detector/status
    fields (covering self-test, rom-edit-propose, and commit triggers
    uniformly) AND the roadmap-named commit_hash / evidence_atoms /
    command_replay fields (§3 P19 "Findings file" contract). When
    ``trigger == "commit"`` and ``commit_hash`` is empty, ``as_dict()``
    auto-mirrors ``trigger_id`` into ``commit_hash`` so consumers that
    indexed on the roadmap-named field continue to work; same for
    ``proposal_id`` when ``trigger == "rom-edit-propose"``. The hook
    fallback in ``scripts/install_debugger_hooks.py`` writes rows in this
    same shape so ``audit/auto_watch_findings.jsonl`` stays single-shape
    regardless of which writer emits a given row.
    """

    trigger: str
    trigger_id: str
    bug_class: str
    detector: str
    status: str = "detected"
    severity: str = "medium"
    evidence_command: str = ""
    evidence_exit_code: int | None = None
    evidence_summary: str = ""
    evidence_atoms: tuple[dict[str, Any], ...] = ()
    command_replay: str = ""
    commit_hash: str = ""
    proposal_id: str = ""
    files: tuple[str, ...] = ()
    symbols: tuple[str, ...] = ()
    llm_next_step: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "kind": KIND,
            "ts": now_iso(),
            "trigger": self.trigger,
            "trigger_id": self.trigger_id,
            "bug_class": self.bug_class,
            "detector": self.detector,
            "status": self.status,
            "severity": self.severity,
        }
        # Roadmap-named trigger-specific aliases (auto-mirror from trigger_id
        # when not explicitly set, so consumers indexing on the roadmap
        # field name don't need to look at trigger/trigger_id).
        if self.trigger == "commit":
            out["commit_hash"] = self.commit_hash or self.trigger_id
        elif self.commit_hash:
            out["commit_hash"] = self.commit_hash
        if self.trigger == "rom-edit-propose":
            out["proposal_id"] = self.proposal_id or self.trigger_id
        elif self.proposal_id:
            out["proposal_id"] = self.proposal_id
        evidence: dict[str, Any] = {}
        if self.evidence_command:
            evidence["command"] = self.evidence_command
        if self.evidence_exit_code is not None:
            evidence["exit_code"] = self.evidence_exit_code
        if self.evidence_summary:
            evidence["summary"] = self.evidence_summary
        if evidence:
            out["evidence"] = evidence
        # evidence_atoms is the §4.2 proof-vector array. May be empty in
        # first-slice findings; tightens once the P20 catalog lands.
        if self.evidence_atoms:
            out["evidence_atoms"] = [dict(atom) for atom in self.evidence_atoms]
        # command_replay is a single runnable string the LLM-pair can
        # re-invoke to reproduce the detector output that produced this
        # finding. Falls back to the evidence command when not set.
        replay = self.command_replay or self.evidence_command
        if replay:
            out["command_replay"] = replay
        if self.files:
            out["files"] = list(self.files)
        if self.symbols:
            out["symbols"] = list(self.symbols)
        if self.llm_next_step:
            out["llm_next_step"] = self.llm_next_step
        for key, value in self.extra.items():
            if key not in out:
                out[key] = value
        return out


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_finding(row: dict[str, Any]) -> list[str]:
    """Return a list of validation errors for the given finding row.

    Empty list = row is valid. First-slice validation is intentionally
    lenient on bug_class (the P20 catalog will tighten that surface).
    """
    errors: list[str] = []
    for required in ("trigger", "trigger_id", "bug_class", "detector", "status"):
        if not row.get(required):
            errors.append(f"missing required field: {required}")
    trigger = row.get("trigger", "")
    if trigger and trigger not in TRIGGER_KINDS:
        errors.append(f"trigger {trigger!r} not in {TRIGGER_KINDS}")
    status = row.get("status", "")
    if status and status not in STATUS_VALUES:
        errors.append(f"status {status!r} not in {STATUS_VALUES}")
    severity = row.get("severity", "medium")
    if severity not in SEVERITY_VALUES:
        errors.append(f"severity {severity!r} not in {SEVERITY_VALUES}")
    return errors


def append_finding(
    finding: AutoWatchFinding,
    *,
    store_path: Path | None = None,
    root: Path = ROOT,
) -> Path:
    """Append a finding to the findings store (JSONL, append-only).

    Returns the store path actually written to.
    """
    if store_path is None:
        path = Path(root) / DEFAULT_FINDINGS_STORE
    else:
        path = Path(store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = finding.as_dict()
    errs = validate_finding(row)
    if errs:
        raise ValueError(
            f"invalid finding row: {'; '.join(errs)}; row={json.dumps(row)}"
        )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=False) + "\n")
    return path


# ---------- Detectors ----------

def run_register_flow_detector(
    symbol: str,
    *,
    root: Path = ROOT,
    suspicious_writes: frozenset[str] = frozenset({"c"}),
) -> AutoWatchFinding | None:
    """Run register_flow.analyze_function and emit a finding if the
    clobber set includes a "suspicious" write (default: ``c``, the
    AG-NN class signature in this repo).

    Returns None if the symbol cannot be located or no suspicious write
    is detected. A ``watcher_unavailable`` finding is returned only when
    the analyzer itself raises (best-effort posture).

    First-slice conservatism: any ``c``-writer is flagged. A follow-up
    slice will add caller analysis (only flag when a same-bank caller's
    ``c`` is load-bearing post-dispatch). False positives here are
    expected; the deliverable is "the detector noticed."
    """
    try:
        report = register_flow.analyze_function(symbol, root=root)
    except Exception as exc:  # pragma: no cover -- best-effort posture
        return AutoWatchFinding(
            trigger="self-test",
            trigger_id=f"register_flow:{symbol}",
            bug_class="watcher_unavailable",
            detector="register_flow",
            status="watcher_unavailable",
            severity="low",
            evidence_summary=f"register_flow.analyze_function raised: {exc!r}",
            symbols=(symbol,),
        )
    if not report.get("valid", True):
        return None
    clobber_set = set(report.get("clobber_set", []))
    flagged = clobber_set & suspicious_writes
    if not flagged:
        return None
    replay = f"python -m tools.debugger clobbers --symbol {symbol}"
    return AutoWatchFinding(
        trigger="self-test",
        trigger_id=f"register_flow:{symbol}",
        bug_class="ag_nn_register_clobber",
        detector="register_flow",
        status="detected",
        severity="medium",
        evidence_command=replay,
        evidence_summary=(
            f"register_flow clobber set includes {sorted(flagged)} for symbol "
            f"{symbol!r}; recurring AG-NN class signature (c-mirror at exit)."
        ),
        evidence_atoms=(
            {
                "kind": "register_flow_clobber",
                "symbol": symbol,
                "flagged_writes": sorted(flagged),
            },
        ),
        command_replay=replay,
        symbols=(symbol,),
        llm_next_step=(
            "Inspect the function's exit path. If the c-mirror is intentional, "
            "audit every same-bank caller's c load-bearing post-dispatch. See "
            "docs/asm_authoring_guide.md sections 3.13 / 3.14."
        ),
    )


# ---------- Self-test synthesis ----------

# A synthetic AG-NN-class regression: function that writes c at exit
# (the c-mirror pattern shipped twice in this repo as 5x physical damage).
_SYNTH_BROKEN_ASM = """\
SECTION "test_synth_broken", ROMX

TestStubBroken::
    ld a, [hl]
    ld c, a
    ret
"""

# Counterpart that does NOT clobber c -- detector should NOT fire.
_SYNTH_FIXED_ASM = """\
SECTION "test_synth_fixed", ROMX

TestStubFixed::
    ld a, [hl]
    ret
"""


def run_self_test(*, verbose: bool = False) -> int:
    """Synthesize an AG-NN regression in a tmp asm tree, run the
    register_flow detector, and assert it fires on the broken function
    but not on the fixed one.

    Returns 0 on success, non-zero on failure. Writes a status line to
    stdout on success (so callers can assert
    "auto-watch synthetic regression detected").
    """
    with tempfile.TemporaryDirectory(prefix="auto_watch_selftest_") as tmpdir:
        root = Path(tmpdir)
        engine_dir = root / "engine"
        engine_dir.mkdir()
        (engine_dir / "synth_broken.asm").write_text(
            _SYNTH_BROKEN_ASM, encoding="utf-8"
        )
        (engine_dir / "synth_fixed.asm").write_text(
            _SYNTH_FIXED_ASM, encoding="utf-8"
        )

        store_path = root / "auto_watch_findings.jsonl"

        broken_finding = run_register_flow_detector(
            "TestStubBroken", root=root
        )
        fixed_finding = run_register_flow_detector(
            "TestStubFixed", root=root
        )

        if broken_finding is None:
            sys.stderr.write(
                "auto-watch self-test FAIL: broken synth function did not "
                "trigger a register_flow finding\n"
            )
            return 1
        if broken_finding.status != "detected":
            sys.stderr.write(
                f"auto-watch self-test FAIL: broken synth finding status was "
                f"{broken_finding.status!r}, expected 'detected'\n"
            )
            return 1
        if broken_finding.bug_class != "ag_nn_register_clobber":
            sys.stderr.write(
                f"auto-watch self-test FAIL: broken synth bug_class was "
                f"{broken_finding.bug_class!r}, expected 'ag_nn_register_clobber'\n"
            )
            return 1
        if fixed_finding is not None:
            sys.stderr.write(
                f"auto-watch self-test FAIL: fixed synth function triggered "
                f"a finding ({fixed_finding.bug_class!r}); detector is too noisy\n"
            )
            return 1

        # Round-trip through the finding-row writer.
        append_finding(broken_finding, store_path=store_path)
        rows = store_path.read_text(encoding="utf-8").splitlines()
        if len(rows) != 1:
            sys.stderr.write(
                f"auto-watch self-test FAIL: expected 1 finding row, got "
                f"{len(rows)}\n"
            )
            return 1
        parsed = json.loads(rows[0])
        errs = validate_finding(parsed)
        if errs:
            sys.stderr.write(
                f"auto-watch self-test FAIL: finding row failed validation: "
                f"{'; '.join(errs)}\n"
            )
            return 1

        if verbose:
            sys.stdout.write(json.dumps(parsed, indent=2) + "\n")
        sys.stdout.write("auto-watch synthetic regression detected\n")
        sys.stdout.write("auto-watch self-test PASS\n")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.debugger.auto_watch",
        description=(
            "Autonomous bug-watcher for ROM code landings (P19). "
            "First-slice surface: --self-test only."
        ),
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help=(
            "Run the synthetic-regression self-test: synthesize an AG-NN "
            "clobber regression in a tmp dir, assert detection."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the detected finding row as JSON before the PASS line.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test(verbose=args.verbose)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
