from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.debugger.handoff_log import (
    EVENT_KINDS,
    CONFIDENCE_LABELS,
    GATE_VALID_LABELS,
    HandoffRow,
    append_row,
    audit_store,
    is_mutual_verified,
    load_rows,
    validate_row,
)


def _ack_start(model: str, primary: str, phase: str = "P0") -> HandoffRow:
    return HandoffRow(
        phase=phase,
        event="ack_start",
        status="in_progress",
        model=model,
        primary=primary,
        confidence="repo-proven",
        claim=f"{model} acked {phase}",
        write_set=("tools/debugger/handoff_log.py",),
    )


def _slice_update(model: str, primary: str, phase: str = "P0") -> HandoffRow:
    return HandoffRow(
        phase=phase,
        event="slice_update",
        status="ready_for_review",
        model=model,
        primary=primary,
        confidence="repo-proven",
        claim=f"{model} slice ready for review on {phase}",
        files_changed=("tools/debugger/handoff_log.py",),
        verification=("python -B -m unittest discover tools/debugger/tests -> 700 passed",),
    )


def _slice_review(
    reviewer: str,
    primary: str,
    *,
    status: str = "slice_accepted",
    confidence: str = "repo-proven",
    phase: str = "P0",
) -> HandoffRow:
    return HandoffRow(
        phase=phase,
        event="slice_review",
        status=status,
        model=reviewer,
        primary=primary,
        reviewer=reviewer,
        confidence=confidence,
        claim=f"{reviewer} reviewed {primary}'s slice on {phase}",
        verification_replayed=("python -m tools.debugger audit -> ready=True",),
    )


class HandoffLogValidateTests(unittest.TestCase):
    def test_constants_match_pairing_rules(self) -> None:
        self.assertIn("repo-proven", CONFIDENCE_LABELS)
        self.assertIn("memory-derived", CONFIDENCE_LABELS)
        self.assertIn("judgment", CONFIDENCE_LABELS)
        self.assertEqual(GATE_VALID_LABELS, frozenset({"repo-proven"}))
        self.assertIn("ack_start", EVENT_KINDS)
        self.assertIn("slice_update", EVENT_KINDS)
        self.assertIn("slice_review", EVENT_KINDS)
        self.assertIn("phase_done", EVENT_KINDS)

    def test_validate_row_accepts_minimum_required_fields(self) -> None:
        row = _ack_start("claude", "claude").as_dict()
        self.assertEqual(validate_row(row), [])

    def test_validate_row_rejects_unknown_event(self) -> None:
        row = _ack_start("claude", "claude").as_dict()
        row["event"] = "wat"
        errors = validate_row(row)
        self.assertTrue(any("event" in err for err in errors), errors)

    def test_validate_row_rejects_unknown_confidence(self) -> None:
        row = _ack_start("claude", "claude").as_dict()
        row["confidence"] = "totally-sure"
        errors = validate_row(row)
        self.assertTrue(any("confidence" in err for err in errors), errors)

    def test_validate_row_rejects_status_event_mismatch(self) -> None:
        row = _slice_update("claude", "claude").as_dict()
        row["status"] = "slice_accepted"  # not valid for slice_update
        errors = validate_row(row)
        self.assertTrue(any("status" in err for err in errors), errors)

    def test_validate_row_rejects_slice_review_without_reviewer(self) -> None:
        row = HandoffRow(
            phase="P0",
            event="slice_review",
            status="slice_accepted",
            model="claude",
            primary="codex",
            confidence="repo-proven",
            claim="reviewed",
        ).as_dict()
        errors = validate_row(row)
        self.assertTrue(any("reviewer" in err for err in errors), errors)


class MutualVerifiedGateTests(unittest.TestCase):
    def _store(self, rows: list[HandoffRow]) -> list[dict[str, object]]:
        return [{**row.as_dict(), "_line": idx + 1} for idx, row in enumerate(rows)]

    def test_phase_with_only_primary_ack_is_not_verified(self) -> None:
        rows = self._store([_ack_start("codex", "codex")])
        verified, reasons = is_mutual_verified(rows, "P0")
        self.assertFalse(verified)
        self.assertTrue(any("ready_for_review" in r for r in reasons), reasons)

    def test_phase_with_primary_finished_but_no_other_signoff_is_not_verified(
        self,
    ) -> None:
        rows = self._store(
            [
                _ack_start("codex", "codex"),
                _slice_update("codex", "codex"),
            ]
        )
        verified, reasons = is_mutual_verified(rows, "P0")
        self.assertFalse(verified)
        self.assertTrue(any("non-primary" in r for r in reasons), reasons)

    def test_phase_with_other_judgment_review_does_not_pass_gate(self) -> None:
        rows = self._store(
            [
                _ack_start("codex", "codex"),
                _slice_update("codex", "codex"),
                _slice_review("claude", "codex", confidence="judgment"),
            ]
        )
        verified, reasons = is_mutual_verified(rows, "P0")
        self.assertFalse(
            verified,
            "judgment-confidence review must not pass the mutual-verification gate",
        )

    def test_phase_with_other_repo_proven_accept_is_verified(self) -> None:
        rows = self._store(
            [
                _ack_start("codex", "codex"),
                _slice_update("codex", "codex"),
                _slice_review("claude", "codex"),
            ]
        )
        verified, reasons = is_mutual_verified(rows, "P0")
        self.assertTrue(verified, reasons)

    def test_phase_with_rejection_anywhere_is_not_verified(self) -> None:
        rows = self._store(
            [
                _ack_start("codex", "codex"),
                _slice_update("codex", "codex"),
                _slice_review("claude", "codex"),
                _slice_review("claude", "codex", status="slice_rejected"),
            ]
        )
        verified, reasons = is_mutual_verified(rows, "P0")
        self.assertFalse(verified)
        self.assertTrue(any("rejected" in r for r in reasons), reasons)

    def test_self_review_by_primary_does_not_count(self) -> None:
        rows = self._store(
            [
                _ack_start("codex", "codex"),
                _slice_update("codex", "codex"),
                # Codex reviewing its own slice — should NOT satisfy the gate.
                _slice_review("codex", "codex"),
            ]
        )
        verified, _ = is_mutual_verified(rows, "P0")
        self.assertFalse(verified, "self-review by primary cannot satisfy mutual gate")

    def test_legacy_partial_p0_review_does_not_verify_whole_phase(self) -> None:
        with TemporaryDirectory() as tmp:
            store = Path(tmp) / "handoff.jsonl"
            store.write_text(
                "\n".join(
                    json.dumps(row)
                    for row in [
                        {
                            "phase": "P0",
                            "event": "codex_ack_start",
                            "status": "in_progress",
                            "primary": "codex",
                            "model": "codex",
                            "confidence": "repo-proven",
                            "claim": "Codex started P0.",
                        },
                        {
                            "phase": "P0",
                            "event": "codex_slice_update",
                            "status": "ready_for_claude_review",
                            "primary": "codex",
                            "model": "codex",
                            "confidence": "repo-proven",
                            "claim": "Codex first P0 slice ready for review.",
                        },
                        {
                            "phase": "P0",
                            "event": "claude_slice_review",
                            "status": "slice_accepted_partial_P0",
                            "primary": "codex",
                            "reviewer": "claude",
                            "model": "claude-opus-4-7[1m]",
                            "confidence": "repo-proven",
                            "claim": "Slice accepted; P0 is not phase-complete.",
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = load_rows(store)
            report = audit_store(store=store, root=Path(tmp))

        review = next(row for row in rows if row["event"] == "slice_review")

        self.assertEqual(review["status"], "slice_accepted")
        self.assertEqual(review["legacy_status"], "slice_accepted_partial_P0")
        self.assertTrue(review["legacy_partial_phase"])
        self.assertEqual(report["row_errors"], [])
        self.assertFalse(report["phase_status"]["P0"]["mutual_verified"])
        self.assertTrue(
            any("partial" in reason for reason in report["phase_status"]["P0"]["reasons"]),
            report["phase_status"]["P0"]["reasons"],
        )


class AppendRowIntegrationTests(unittest.TestCase):
    def test_append_then_audit_full_lifecycle(self) -> None:
        with TemporaryDirectory() as tmp:
            store = Path(tmp) / "handoff.jsonl"
            append_row(_ack_start("codex", "codex"), store=store, root=Path(tmp))
            append_row(_slice_update("codex", "codex"), store=store, root=Path(tmp))
            append_row(_slice_review("claude", "codex"), store=store, root=Path(tmp))
            report = audit_store(store=store, root=Path(tmp))
            self.assertEqual(report["row_count"], 3)
            self.assertEqual(report["row_errors"], [])
            self.assertEqual(report["phases"], ["P0"])
            self.assertTrue(report["phase_status"]["P0"]["mutual_verified"])

    def test_append_rejects_invalid_row(self) -> None:
        bad = HandoffRow(
            phase="P0",
            event="slice_review",
            status="slice_accepted",
            model="claude",
            primary="codex",
            confidence="repo-proven",
            claim="missing reviewer field",
        )
        with TemporaryDirectory() as tmp:
            store = Path(tmp) / "handoff.jsonl"
            with self.assertRaises(ValueError):
                append_row(bad, store=store, root=Path(tmp))


class GoldenLivedBugSmokeTests(unittest.TestCase):
    """Rule-#11 golden lived-bug smoke.

    The scenario this gate is designed to refuse: a single LLM declaring
    a fix verified without the other model running an adversarial pass.
    The May 2026 5x physical damage class (AG-NN transitive register
    clobber) ate multiple iterations before catching the root cause; if
    one LLM had signed it off alone, the broken fix could have landed.
    This test reproduces that pattern in the handoff log and asserts the
    gate refuses.
    """

    def test_ag_nn_class_solo_signoff_refused(self) -> None:
        with TemporaryDirectory() as tmp:
            store = Path(tmp) / "handoff.jsonl"
            # Codex claims the AG-08 fix is done and signs its OWN slice review.
            append_row(
                HandoffRow(
                    phase="ag_nn_fix",
                    event="ack_start",
                    status="in_progress",
                    model="codex",
                    primary="codex",
                    confidence="repo-proven",
                    claim="AG-08 c-mirror clobber fix candidate",
                ),
                store=store,
                root=Path(tmp),
            )
            append_row(
                HandoffRow(
                    phase="ag_nn_fix",
                    event="slice_update",
                    status="ready_for_review",
                    model="codex",
                    primary="codex",
                    confidence="repo-proven",
                    claim="fix shipped; clobber_smoke green locally",
                ),
                store=store,
                root=Path(tmp),
            )
            # Solo sign-off attempt by the same primary.
            append_row(
                HandoffRow(
                    phase="ag_nn_fix",
                    event="slice_review",
                    status="slice_accepted",
                    model="codex",
                    primary="codex",
                    reviewer="codex",
                    confidence="repo-proven",
                    claim="codex self-approves the fix",
                ),
                store=store,
                root=Path(tmp),
            )
            report = audit_store(store=store, root=Path(tmp))
            self.assertEqual(
                report["row_errors"],
                [],
                "rows are individually well-formed",
            )
            self.assertFalse(
                report["phase_status"]["ag_nn_fix"]["mutual_verified"],
                "solo self-review must not pass the gate; "
                "the May 2026 AG-08 class is the lived bug this prevents",
            )


if __name__ == "__main__":
    unittest.main()
