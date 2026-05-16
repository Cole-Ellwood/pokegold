#!/usr/bin/env python3
"""Trajectory-regression audit: scorer must keep agreeing with strict trajectory
preference labels at a high rate.

The trajectory verifier grades the Python scorer against the strict
`a_better` / `b_better` rows in `boss_ai_trajectory_preferences.jsonl`. After
iters 12-16 the agreement rate sits at 43/44 = 97.7% (the one remaining
disagreement is a legacy public_only scope label whose canonical-scope
companion already agrees via `--canonical-scope public_plus_common_meta`).

This audit gates the floor at 0.93 so future scorer changes that break the
established alignment will trip CI before the regression becomes invisible.
The threshold is deliberately just below the current 0.977 rate to allow
one new disagreement to land without immediately failing, but tight enough
that the fix MUST keep most of the established alignment.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_preference.trajectory_regression import run_trajectory_regression


AUDIT_THRESHOLD = 0.93


def main(argv: list[str] | None = None) -> int:
    result = run_trajectory_regression()
    label = (
        f"trajectory regression: {result.strict_agreement_count}/"
        f"{result.strict_label_count} strict labels "
        f"({result.agreement_rate * 100:.1f}%)"
    )
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
            for v in result.disagreements[:10]:
                print(
                    f"    {v.fixture_id}: label={v.label_choice} scorer={v.scorer_choice} "
                    f"(score_a={v.score_a} score_b={v.score_b} "
                    f"resolved_by={v.resolved_by})",
                    file=sys.stderr,
                )
        return 1
    print(f"PASS: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
