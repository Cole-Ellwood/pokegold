# Boss AI Pairwise Label Coverage Gaps

Status: surfaced 2026-05-16 (boss-ai-loop iter 28). Not a blocker; this is
a queue for future labeling sessions.

## Method

For every fixture in `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
count how many pairwise labels in
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`
attach to it, then aggregate by `leader` field.

## Current coverage

| Leader | Fixtures | Labels | Note |
| --- | ---: | ---: | --- |
| Blue | 1 | 0 | UNLABELED — Kanto Champion, 1 fixture |
| Bruno | 3 | 0 | UNLABELED — E4, 3 fixtures |
| Brock | 1 | 2 | |
| Bugsy | 3 | 5 | |
| Champion Lance | 6 | 5 | |
| Chuck | 3 | 1 | under-labeled |
| Clair | 4 | 3 | |
| Erika | 1 | 3 | |
| External GSC | 1 | 3 | |
| Falkner | 3 | 1 | under-labeled |
| Janine | 4 | 8 | |
| Jasmine | 3 | 2 | |
| Karen | 3 | 0 | UNLABELED — E4, 3 fixtures |
| Koga | 3 | 1 | under-labeled |
| Mechanics Drill | 1 | 3 | |
| Misty | 1 | 1 | |
| Morty | 3 | 2 | |
| Pryce | 3 | 5 | |
| Red | 5 | 3 | |
| Sabrina | 1 | 3 | |
| Whitney | 3 | 2 | |
| Will | 3 | 3 | |

## Why this matters

Pairwise labels are the strict-grader's signal for "what move would Claude
pick?" — the boss-AI-loop's whole alignment metric depends on them. A leader
with zero labels:

- has no contribution to the strict pairwise corpus (47/47 = 100% today
  doesn't include any Blue/Bruno/Karen fixture);
- doesn't surface scorer divergences for that leader's playstyle in audits;
- can't be canonical-scope-converted because there's no existing label to
  cite.

This is a labeler-time investment, not an autonomous task: the labels carry
taste judgments that need a human in the loop. The runbook describes how
to label safely without overfitting (no review of generated plans before
freezing).

## Recommended priority

1. **Karen + Bruno** — three fixtures each, both E4. Filling these directly
   improves Champion-tier corpus density.
2. **Chuck / Falkner / Koga** — under-labeled at 1/3. Two more labels per
   leader balances the coverage.
3. **Blue** — only one fixture, but a Kanto-side label gives a Champion-tier
   sample beyond Lance.

## Not in scope

- Auto-generating labels from the scorer would just embed today's scorer in
  the ground-truth; the labels would no longer be a Claude-judgment signal.
  Skip.
- Adding the gap to the audit floor as a fail-gate would block all releases
  until labeled. Skip — surface as a TODO, not a blocker.

## How to consume this doc

Future Claude or Codex labeling sessions can:

1. Open `tools/boss_ai_preference/app.py` (the preference labeler MVP).
2. Filter the fixture list to one of the unlabeled leaders.
3. Make pairwise judgments under the loop's canonical scope
   (`public_plus_common_meta`).
4. Save through the labeler — appends to
   `boss_ai_pairwise_preferences.jsonl`.

After landing labels, re-run the boss-AI alignment audit floor:

```bash
python tools/audit/check_boss_ai_preference_regression.py
python tools/audit/check_boss_ai_trajectory_regression.py
python tools/audit/check_boss_ai_other_better_alignment.py
```

New disagreements that surface from the new labels become the next round
of boss-ai-loop iters (per `docs/boss_ai_loop_runbook.md`).
