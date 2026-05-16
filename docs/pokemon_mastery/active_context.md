# Active Context Packet

Date: 2026-05-16

Purpose: route mastery work through the small live core instead of the archive.

Hard cap: keep this file near 80-120 lines. If it grows, move details into the
archive or `heuristic_core/migration_map.md`.

## Current Objective

Become a stronger Pokemon singles advisor, using "1500 Elo" as a training
proxy. Improve unseen move choice, multi-turn re-solves, and realistic routes.

## Startup Spine

Open first by task:

- Work-block startup: `playbook_manifest.md`, then `live_core.md`.
- Fresh unseen move choice: `live_core.md`, the public prompt, and the smallest
  useful set of tiny `heuristic_core/*.md` cards plus compact `canon/*.md` or
  `romhack_deltas/*.md` lookups only when the public board needs them.
- Scoring or progress claims: `measurement_minigoal_2026-05.md` and the
  frozen answer artifact after answers are recorded.
- Postmortem or cleanup: `heuristic_core/migration_map.md`, then the linked
  old policy card, review, quick test, ledger row, or mechanics fixture.
- Boss live advice: `live_core.md`, `boss_turn_advice_template.md`, current
  board/sheet, and only decision-relevant local mechanics status.

Do not load `cookbook.md`, `source_to_policy_ledger.md`, `paused_turn_atlas.md`,
`worked_examples/live_turn_drills.md`, long `policy_cards/*.md`, scored quick
`workspace/quick_tests/`, reviews, or raw `workspace/external_research_returns/`
before freezing fresh answers.

## Context Packets

- `live_turn`: `live_core.md`, boss template, current board/sheet, local
  mechanics status, and decision-relevant tiny heuristics if needed.
- `replay_turn_pause`: `live_core.md`, protocol, prompt, useful tiny
  heuristics, and any compact topic lookup before freezing. Keep future turns
  and answer labels hidden.
- `quick_probe_generation`: parent fresh replay miss, relevant card, and
  measurement rules. Regression only, not proof.
- `mechanics_verification`: romhack deltas, fixtures, source/debugger/emulator
  evidence, and pending index. No unverified decision mechanics.
- `study_review`: current bottleneck plus one expert source or replay. End with
  a score, fixture, policy-card update, or reject note.

## Current Measurement Snapshot

Latest plateau diagnosis: `plateau_diagnosis_001`. Working hypothesis: the
current wall is live role/package synthesis, not missing notes. Public support
reveals must update the job ledger before move ranking.

Constructed probes are nonblind regression checks, not fresh proof.

Older samples: role-package plateau flat; post-Spikes/Spin limited positive;
spectator checks regressed from exact-move noise; pre-tempo side-known flat.
See `measurement_progress_ledger.csv` for full counts and review links.

Post-tempo packet 006: 13/21 top, 20/21 acceptable, clean gates. Packets
007-017: repair loops, then 16/31 top, 29/31 acceptable. Packets 020-043:
353/681 top, 589/681 acceptable, 6 severe, 7 hidden, 6 mechanics; no proof.
Post-repair packets 032-043 are 186/361 top and 319/361 acceptable with 0
severe/hidden but 1 state/mechanics error. Packets 041-043 were 48/89 top and
72/89 acceptable after the side-known prefilter: essentially flat versus
packets 038-040, so `training_method_review_006` added branch-ranking labels.
Packet 044 tested the labels: 15/30 top, 29/30 acceptable, 25/30 actual in top
three, 27/30 actual branch named, 0 severe/hidden/mechanics, 1 state error.
Exact ranking is still flat; `training_method_review_007` and
`route_budget_tiebreaker_annotation_001` identify the next target as
route-budget tiebreaking after candidate generation succeeds.

## Compressed Live Error Families

Use `live_core.md` and relevant tiny cards rather than this section for
decisions.
The repeated old lessons are mapped in `heuristic_core/migration_map.md`.

- Owner naming: name current owner and next-board owner before choosing.
- Converter ranking: promote route-changing moves above safe scripts.
- Branch punish: after naming a receiver, rank the action that beats it.
- Spend/save: preserve live route jobs; spend only for named converters.
- Reset denial: hazards, Spin, Rest, Recover, phaze, Sleep Talk, and pass
  routes count only when converted or denied in time.
- Role package ledger: screen, Charm/Pursuit, trap/perish, phaze, Spin, Curse,
  RestTalk, lure, lead item/status, pass, and cleric reveals change the job.
- Plateau loop: after a structural repair, collect 3 packets or 90 fresh side
  decisions; if flat/regressing or a miss repeats twice, study/repair first.
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

## Next Concrete Rep

Next gate: run one fresh side-known packet. On boards with
Spikes/Rest/phaze/entry-tax pressure, load `reset_loop_denial.md` and apply its
fast tiebreaker before ranking chip/status/coverage first. Do not claim
progress unless exact top improves without losing severe/hidden/state/mechanics
gates or route/branch metrics.
