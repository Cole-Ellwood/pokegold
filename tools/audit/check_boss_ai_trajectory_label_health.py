#!/usr/bin/env python3
"""Trajectory-label schema-health audit.

Strict trajectory labels (`a_better` / `b_better` / `other_better`) name a
specific plan-pair by `trajectory_a_id` and `trajectory_b_id`. The plan
generator at `tools/boss_ai_preference/plans.py` is the source of truth for
which plan ids exist for each fixture; when the generator changes (rename, new
shape, dropped option) older labels can silently point at non-existent plan
ids. Strict labels with invalid plan ids are dead — the regression verifier
returns `tie` for them with a `plan_id is not generated` reason and the
disagreement falls out of the metrics, so the rot is invisible.

This audit fails on any strict label whose `trajectory_a_id` or
`trajectory_b_id` does not match a currently-generated plan. It IGNORES
non-strict labels (`both_good`, `needs_context`, `other_better` without
strict trajectory_b_id, `neither_best_plan_missing`) because those use
plan-id slots to encode missing-plan markers and intentionally point at
plans that should not yet exist.

Run as part of release smoke; complements the regression gates that grade
agreement on the labels they CAN evaluate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_preference.data import fixture_map, load_fixtures
from tools.boss_ai_preference.plans import generate_plan_cards
from tools.boss_ai_preference.trajectory_data import (
    DEFAULT_TRAJECTORY_PREFERENCES_PATH,
)


STRICT_TRAJECTORY_CHOICES = {"a_better", "b_better"}


def main(argv: list[str] | None = None) -> int:
    fixtures = load_fixtures()
    fmap = fixture_map(fixtures)
    valid_plans_by_fixture: dict[str, set[str]] = {
        fid: {p["id"] for p in generate_plan_cards(fix)} for fid, fix in fmap.items()
    }

    bad: list[tuple[int, str, str, str]] = []
    strict_count = 0
    for line_index, raw_line in enumerate(
        DEFAULT_TRAJECTORY_PREFERENCES_PATH.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            label = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                f"FAIL: malformed JSON at line {line_index}: {exc.msg}",
                file=sys.stderr,
            )
            return 1
        if label.get("choice") not in STRICT_TRAJECTORY_CHOICES:
            continue
        strict_count += 1
        fixture_id = label.get("fixture_id") or ""
        valid_plans = valid_plans_by_fixture.get(fixture_id)
        if valid_plans is None:
            bad.append((line_index, fixture_id, "(unknown fixture)", ""))
            continue
        for slot in ("trajectory_a_id", "trajectory_b_id"):
            plan_id = label.get(slot)
            if not plan_id:
                continue
            if plan_id not in valid_plans:
                bad.append((line_index, fixture_id, slot, plan_id))

    if bad:
        print(
            f"FAIL: {len(bad)} invalid plan reference(s) on strict trajectory labels "
            f"(graded {strict_count})",
            file=sys.stderr,
        )
        for line_index, fixture_id, slot, plan_id in bad:
            print(
                f"  line {line_index} fixture={fixture_id} {slot}={plan_id}",
                file=sys.stderr,
            )
        return 1

    print(
        f"PASS: trajectory label health: {strict_count} strict labels have valid plan ids"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
