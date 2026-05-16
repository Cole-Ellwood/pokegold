#!/usr/bin/env python3
"""Canonical-scope trajectory regression: scorer must perfectly agree with
the canonical-scope (public_plus_common_meta) trajectory labels.

The iter-5 user direction is that public_plus_common_meta is the canonical
reasoning frame for this loop. The legacy public_only labels exist for
retrieval, but the canonical labels are the ground truth the scorer should
match exactly. This audit runs the trajectory regression with the canonical
scope filter and gates at 1.0 (100% agreement), so any scorer change that
breaks a canonical-scope label fails CI.

As of iter 18 the canonical-scope corpus has 5 labels (clair from iter 11,
plus jasmine/chuck/whitney/morty from iter 18). The audit will pick up new
canonical-scope labels automatically as they are added.

Companion to `check_boss_ai_trajectory_regression.py` which gates the
broader legacy corpus at 0.93.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_preference.trajectory_regression import run_trajectory_regression


CANONICAL_SCOPE = "public_plus_common_meta"
AUDIT_THRESHOLD = 1.0


def main(argv: list[str] | None = None) -> int:
    result = run_trajectory_regression(canonical_scope=CANONICAL_SCOPE)
    label = (
        f"canonical-scope ({CANONICAL_SCOPE}) trajectory regression: "
        f"{result.strict_agreement_count}/{result.strict_label_count} strict labels "
        f"({result.agreement_rate * 100:.1f}%)"
    )
    if result.strict_label_count == 0:
        # No canonical-scope labels exist yet. The audit cannot fail because
        # there is nothing to grade. Print so the operator knows the audit
        # ran and was vacuously true.
        print(f"PASS: {label} (no canonical-scope labels graded)")
        return 0
    if result.agreement_rate < AUDIT_THRESHOLD:
        print(
            f"FAIL: {label}; required >= {AUDIT_THRESHOLD * 100:.1f}%",
            file=sys.stderr,
        )
        if result.disagreements:
            print(
                f"  {len(result.disagreements)} disagreement(s):",
                file=sys.stderr,
            )
            for v in result.disagreements:
                print(
                    f"    {v.fixture_id}: label={v.label_choice} scorer={v.scorer_choice} "
                    f"(score_a={v.score_a} score_b={v.score_b} resolved_by={v.resolved_by})",
                    file=sys.stderr,
                )
        return 1
    print(f"PASS: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
