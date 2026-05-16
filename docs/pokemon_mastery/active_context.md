# Active Context Packet

Date: 2026-05-15

Purpose: keep future Pokemon mastery work routed through the small live core
instead of the archive. This file is a compact status packet and not the
default pre-freeze move-choice context.

Hard cap: keep this file near 80-120 lines. If it grows, move details into the
archive or `heuristic_core/migration_map.md`.

## Current Objective

Become a measurably stronger Pokemon singles advisor, using "1500 Elo" as a
training proxy rather than proof. The live target is better unseen move choice:
plan multiple turns ahead, re-solve after new information, and preserve or
improve realistic win routes.

Pokemon Showdown ladder ratings are only proxies. PS documents Elo, GXE, and
Glicko-1 separately and says there is no official universal Elo standard.

## Startup Spine

Open first by task:

- Fresh unseen move choice: `live_core.md`, the public prompt, and any
  `heuristic_core/*.md` cards forced by live_core's Load-Required Triggers
  block; otherwise the smallest discretionary set.
- Scoring or progress claims: `measurement_minigoal_2026-05.md` and the
  frozen answer artifact after answers are recorded.
- Postmortem or cleanup: `heuristic_core/migration_map.md`, then the linked
  old policy card, review, quick test, ledger row, or mechanics fixture.
- Boss live advice: `live_core.md`, `boss_turn_advice_template.md`, current
  board/sheet, and only decision-relevant local mechanics status.

Do not load `cookbook.md`, `source_to_policy_ledger.md`, `paused_turn_atlas.md`,
`worked_examples/live_turn_drills.md`, long `policy_cards/*.md`, scored quick
tests, reviews, or external research returns before freezing fresh answers.

## Context Packets

- `live_turn`: `live_core.md`, boss template, current board/sheet, local
  mechanics status, and any heuristic_core cards forced by Load-Required
  Triggers (otherwise smallest discretionary set).
- `replay_turn_pause`: `live_core.md`, protocol, prompt, and any
  heuristic_core cards forced by Load-Required Triggers before freezing.
  Keep future turns and answer labels hidden. Record the pre-freeze
  loaded-card set per turn so H1/H2 misses are distinguishable post-score.
- `quick_probe_generation`: parent fresh replay miss, relevant card, and
  measurement rules. Regression only, not proof.
- `mechanics_verification`: romhack deltas, fixtures, source/debugger/emulator
  evidence, and pending index. No unverified decision mechanics.
- `study_review`: current bottleneck plus one expert source or replay. End with
  a score, fixture, policy-card update, or reject note.

## Current Measurement Snapshot

Latest measurement read: severe blunders improved, but total errors did not;
claim only catastrophic-error improvement until hidden/state/mechanics errors
decline too.

Keep constructed probes separate from fresh replay evidence; they are nonblind
regression checks, not proof.

Latest fresh transfer: `resttalk_growth_item_transfer_001`: turn-30 stop,
29/58 top, 50/58 acceptable, 0 severe/state/hidden/mechanics, 45/58 positive,
40/58 route, 31/47 branch. Useful study packet, not progress proof: top stayed
below gate and repeated item-first Thief, active-removal, Espeon Growth package,
and CurseLax/RestTalk timing misses. Latest review:
`resttalk_growth_item_review_001`.

Latest regression drill: `resttalk_growth_item_probe_001` passed 6/6, but is
constructed/nonblind and proves only local policy obedience.

## Compressed Live Error Families

Use `live_core.md` and one tiny card rather than this section for decisions.
The repeated old lessons are mapped in `heuristic_core/migration_map.md`.

- Owner naming: name current owner and next-board owner before choosing.
- Converter ranking: promote route-changing moves above safe scripts.
- Branch punish: after naming a receiver, rank the action that beats it.
- Spend/save: preserve live route jobs; spend only for named converters.
- Reset denial: hazards, Spin, Rest, Recover, phaze, Sleep Talk, and pass
  routes count only when converted or denied in time.
- Reveal re-score: Growth, Baton Pass, Substitute, Curse, RestTalk, Thief,
  lure coverage, Roar, or Whirlwind can change the whole package.
- Public tiers: preserve revealed / strong-prior / possible-only discipline.
- Romhack firewall: vanilla GSC is source material, not local truth.

## Approved Gates

Primary proof: sealed replay-transfer packets, 30-50 fresh side decisions,
target at least 55% top-match, at least 70% acceptable-match, 0 severe
blunders, at least 60% positive-selection on converter decisions, and no
repeated uncorrected error class twice in the same packet.

Secondary proof: targeted regression probes. Use at most one small constructed
probe per fresh replay miss by default, split only separate boundaries, and
never count artifact volume as progress.

## Web Search And Local-Only Triggers

Use web search when selecting fresh Smogon/GSC material, checking current
competitive sources, extracting a new source-to-policy rule, verifying current
Showdown rating docs, or investigating a repeated error not explained locally.

Do not web search before freezing a sealed answer. Do not use web search to
settle romhack mechanics that require local docs, source, fixtures, debugger
output, or emulator traces.

## Latest Diagnosis (2026-05-16, parallel branch)

Packet 044 (on the codex/cleanup-gsc-rebalance-split branch's WIP, not
yet on this branch) was 15/30 top, 29/30 acceptable, 25/30 actual-in-
top-3, 27/30 branch named, clean severe/hidden/mechanics, 1 state.
Diagnosis at `docs/pokemon_mastery/reviews/top_match_miss_classification_packet_044.md`:
**67% of exact-top misses (10/15) trace to card-not-loaded** — the
`reset_loop_denial.md` and `spend_or_save_piece.md` cards that contain
the route-budget tiebreaker were NOT in pre-freeze context for packet
044. The rule was already written; the model just had no access to it
at decision time.

Intervention shipped: `live_core.md` now has a Load-Required Triggers
block that makes those cards mandatory on Spikes/Rest/phaze and
preservation boards; the one-card cap was relaxed (it was already
being violated in practice — packet 044 loaded four heuristic_core
cards); a pre-freeze branch-punish audit was added to catch Turn-22-
class state errors. The packet protocol now requires per-turn
loaded-cards recording.

## Next Concrete Rep

Run packet 045 on an unseen Smogon GSC tournament replay obeying
`live_core.md`'s Load-Required Triggers. Expected outcomes:

- **Plateau broken**: exact-top materially up (target ~25/30 if every
  H1 miss flips, ~20/30 conservative) with clean severe/hidden/state/
  mechanics gates and route-conversion/branch-punish metrics not
  falling. Keep training under triggers.
- **Diagnosis falsified**: exact-top <20/30 despite trigger compliance.
  Pivot to pairwise contrastive drills (Inventory Issue 21) or
  multi-oracle pivot (Inventory Issue 22).

Do not claim progress without the triggers actually firing on the
relevant boards — verify in the per-turn "Pre-freeze loaded cards"
field.
