# Pokemon Mastery Docs Cleanup Audit - 2026-05-14

Default action: keep. The current docs are large because they preserve
different kinds of evidence: source lessons, battle reviews, distilled recipes,
practice prompts, local mechanics, and measurement. Deleting or merging by
surface similarity would lose useful provenance.

## Objective

Audit the Pokemon mastery docs for navigation, redundancy, simplification, and
future usefulness. The cleanup should make future Pokemon decision training
faster without turning into meta-work.

## Current Inventory

| Area | Files | Status |
| --- | ---: | --- |
| Root mastery docs | 16 | Useful, but entrypoint needed a clearer master index. |
| `boss_route_maps/` | 25 | Keep. Route maps are local roster artifacts. |
| `worked_examples/` | 111 | Keep. This is the main concrete practice library. |
| `reviews/` | 39 | Keep. Reviews preserve source context and lesson provenance. |
| `romhack_deltas/` | 8 | Keep. These are the local-mechanics firewall. |
| `pro_notes/` | 6 | Keep as archive/process input, not daily curriculum. |
| `external_research_returns/` | 2 | Keep raw; filter before integration. |
| `mechanics_fixtures/` | 1 | Expand. Runtime evidence is underbuilt. |
| `battle_captures/` | 1 | Expand. Real boss attempts are the missing proof layer. |

## Changes Made In This Audit

- Added `master_index.md` as the top-level routing table.
- Added `study_roadmap_2026-05-14.md` as the forward plan.
- Added this cleanup audit as the keep/merge/delete policy.
- Updated `README.md` to point at the new index, roadmap, and audit.
- Incorporated the requested "not fun" sanity check: the roadmap now prioritizes
  Quick Test 001, a real Pryce attempt, mechanics fixtures, and failure-mode
  lookup over aesthetic organization.

## Redundancy Review

| Apparent redundancy | Verdict | Reason |
| --- | --- | --- |
| `cookbook.md` and `source_to_policy_ledger.md` | Keep both. | Cookbook is reusable advice; ledger preserves source-to-policy provenance. |
| `paused_turn_atlas.md` and `worked_examples/live_turn_drills.md` | Keep both. | Atlas indexes reviewed positions; drills force answer-flip practice. |
| `boss_route_maps/*` and `worked_examples/*_pre_battle_route_sheet.md` | Keep both. | Route maps describe boss threats; worked sheets show how to use the planning worksheet. |
| `reviews/` and `worked_examples/smogtours_*` | Keep both. | Reviews preserve battle narrative; worked examples distill one reusable pattern. |
| `active_goal.md` and `goal_restart_prompt.md` | Keep, but mark state clearly. | `active_goal.md` is broad history/pending replacement; `goal_restart_prompt.md` is the current restart text. |
| `external_research_prompts_*` and `external_research_returns/*` | Keep raw. | They are reproducibility/provenance for outside research. |
| `pro_notes/*` and current operating docs | Keep archive. | They contain method ideas, but current behavior should be governed by restart prompt and measurement docs. |
| Many boss stress tests around hazards/status/route preservation | Keep. | Surface themes repeat, but they cover different boss rosters, public states, and failure branches. |

## Do Not Remove Without A Specific Reason

- Any battle review that has not been distilled into at least one policy entry,
  paused-turn prompt, or worked example.
- Any romhack delta or mechanics fixture.
- Any route sheet tied to a local boss roster.
- Raw external research returns.
- Measurement ledger rows, including poor scores.
- Historical handoff/snapshot docs that explain why a goal or policy changed.

## Safe Simplifications

These are allowed when there is clear evidence and a small patch:

- Add cross-links from a review to the exact STP/PTA/worked example it created.
- Add one-line index entries for newly created docs.
- Move repeated prose out of future docs by linking to the cookbook recipe.
- Mark stale status lines as superseded rather than deleting the old artifact.
- Split a huge file only if the old path keeps a short index and redirects.

## Unsafe Simplifications

Avoid these unless the user explicitly asks and there is a reviewed migration
plan:

- Merging all reviews into the cookbook.
- Deleting "duplicate" boss route sheets because another boss has a similar
  route family.
- Turning the worked examples into one giant file.
- Removing vanilla GSC examples just because the romhack differs; keep them and
  label transfer limits.
- Replacing local mechanics docs with generic Pokemon Showdown assumptions.
- Cleaning up raw external research by rewriting its conclusions as fact.

## Sanity-Check Findings Adopted

- Navigation should answer "what mistake am I trying to stop making?", not just
  "where is this file?"
- The next roadmap step must be scored reps, especially Quick Test 001.
- Add labels such as `semi_blind`, `source_grounded`, `runtime_verified`, and
  `romhack_unverified` gradually instead of rewriting old prose.
- Do not move or rename lots of files until retrieval or scoring actually
  fails because of the current names.
- Route maps are not exact turn advice without player-team state.

## Concrete Cleanup Backlog

1. Add `Source Linkage` sections to older reviews that already produced STP or
   PTA entries.
2. Add a compact tag index for worked examples by skill family:
   hazards, spin, sleep, status, Explosion, phazing, setup, PP, endgame,
   no-preview opener, romhack mechanic.
3. Add a `mechanics_verified` / `mechanics_pending` marker to boss route maps
   where local type/passive, Rapid Spin, phazing, or item behavior matters.
4. Convert the external hidden-info atlas JSONL block into a small generated
   CSV/index for practice selection, while preserving the raw return.
5. Fill `battle_captures/` with the first real recorded boss attempt before any
   50-battle validation claim.
6. Add quick-test rows to `measurement_progress_ledger.csv` whenever a real
   probe is run.
7. Build only search/index tooling that answers a live training question, such
   as "show me five hazard-retention drills I have not recently practiced."

## Cleanup Gate

Before removing or combining a doc, answer:

1. What exact future decision does this file no longer help?
2. Has its useful lesson already been copied into a better artifact?
3. Does the new artifact preserve source, public state, hidden-info limits, and
   romhack transfer limits?
4. Would deletion make it harder to audit a future wrong answer?

If any answer is uncertain, keep the file and add a pointer instead.
