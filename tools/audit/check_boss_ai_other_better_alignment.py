#!/usr/bin/env python3
"""Other-better-label alignment audit: scorer's top action must match the
explicit `preferred_action_id` on every `other_better` pairwise label.

The pairwise regression at `check_boss_ai_preference_regression.py` grades
only strict `a_better` / `b_better` labels — labels where neither A nor B
is the right choice (`choice == "other_better"`) are skipped because they
need a third option. These labels DO carry an explicit
`preferred_action_id` for the third option, and that is a strong signal
of where the scorer should land. This audit gates that signal at 100%
agreement.

Today the `other_better` corpus has four labels:
  - chuck_poliwrath_vs_pidgeotto_ice_punch -> switch_sudowoodo
  - pryce_cloyster_vs_quilava_explosion_line -> switch_slowking
  - pryce_slowking_vs_ampharos_ground_pivot -> switch_piloswine
  - clair_dragonair_vs_suicune_hidden_ice_beam -> switch_kingdra

All four pass after iter 23's `sacrifice_cheapness_pivot` rule. Locking
in a 1.0 gate prevents silent regression on this slice of the corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.boss_ai_debugger.scorer import score_action
from tools.boss_ai_preference.data import (
    fixture_map,
    load_fixtures,
    load_preferences,
)


def main(argv: list[str] | None = None) -> int:
    fixtures = load_fixtures()
    fmap = fixture_map(fixtures)
    prefs = load_preferences(fixtures=fixtures)

    other_better = [p for p in prefs if p.get("choice") == "other_better"]
    if not other_better:
        print("PASS: no `other_better` pairwise labels to grade")
        return 0

    mismatches: list[tuple[str, str, str, int]] = []
    aligned_count = 0
    for label in other_better:
        fixture_id = label.get("fixture_id") or ""
        preferred = label.get("preferred_action_id") or ""
        if not preferred:
            # other_better with no preferred_action_id is malformed; skip
            # silently — the schema validator handles that case.
            continue
        fixture = fmap.get(fixture_id)
        if not fixture:
            mismatches.append((fixture_id, preferred, "<missing fixture>", 0))
            continue
        scored = [
            (a["id"], score_action(fixture, a)["score"])
            for a in fixture.get("actions", [])
        ]
        if not scored:
            mismatches.append((fixture_id, preferred, "<no actions>", 0))
            continue
        scored.sort(key=lambda item: -item[1])
        top_action, top_score = scored[0]
        if top_action == preferred:
            aligned_count += 1
        else:
            mismatches.append((fixture_id, preferred, top_action, top_score))

    graded = aligned_count + len(mismatches)
    if mismatches:
        print(
            f"FAIL: {aligned_count}/{graded} other_better labels aligned with "
            f"scorer top action",
            file=sys.stderr,
        )
        for fixture_id, preferred, top_action, top_score in mismatches:
            print(
                f"  {fixture_id}: preferred={preferred} but top={top_action} (score {top_score})",
                file=sys.stderr,
            )
        return 1

    print(
        f"PASS: {aligned_count}/{graded} other_better labels aligned with scorer top action"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
