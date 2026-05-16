# Packet 045 — Codex Task Spec — 2026-05-16

## What this task is

You are running a fresh **side-known replay-turn-pause packet** for the
Pokemon mastery training loop. Packet 044 plateaued at 15/30 exact-top
match (vs the expert replay) despite 29/30 acceptable and 27/30 actual
branch named. Diagnosis at
`docs/pokemon_mastery/reviews/top_match_miss_classification_packet_044.md`
identified that 67% of misses were card-not-loaded (the relevant
heuristic_core card was not in pre-freeze context, so its rule could not
fire).

Intervention (committed on this worktree's branch
`claude/festive-solomon-57f845`, commit `cf87f141`):

- `live_core.md` gained a Load-Required Triggers block that **forces**
  loading specific cards on specific board features.
- `replay_turn_pause_protocol.md` gained a "Pre-freeze loaded cards"
  field per turn.

This packet measures whether the intervention flips exact-top.
**Parallel** with a Claude session running the same replay; the
comparison surfaces whether the intervention is model-agnostic or
Claude-specific.

## Required reading before starting

Read in this order:

1. `docs/pokemon_mastery/live_core.md` — the patched version with the
   Load-Required Triggers block. THIS is what you operate under.
2. `docs/pokemon_mastery/replay_turn_pause_protocol.md` — the packet
   workflow and scoring rubric.
3. `docs/pokemon_mastery/active_context.md` — current measurement state.
4. `docs/pokemon_mastery/heuristic_core/reset_loop_denial.md` and
   `docs/pokemon_mastery/heuristic_core/spend_or_save_piece.md` — the two
   cards the intervention forces on most boards.
5. `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_044_smogtours-gen2ou-821941_p1_2026-05-16.md`
   — the previous packet, for format reference.
6. `docs/pokemon_mastery/reviews/top_match_miss_classification_packet_044.md`
   — the diagnosis behind the intervention. Read so you understand WHAT
   the trigger block is trying to fix, not just THAT it exists.

## Inputs

| Parameter | Value |
|---|---|
| Replay URL | **(user to fill in)** — must be a Smogon/Smogon Tours GSC OU replay not used in any prior packet. Confirm with `rg "<replay-id>"` across `docs/pokemon_mastery/` returning no hits before starting. |
| Side perspective | **(user to fill in)** — `p1` or `p2`. Pick the side whose team you can reliably reconstruct (full sets known from external source / replay later in the match / paste sheet). |
| Side-known source | Either the Showdown search API team paste, or the team revealed in the replay's later turns (read those later turns ONLY for team reconstruction, never for future-turn outcomes). Note the source. |
| Target turns | 30 scored decisions; stop earlier ONLY if forced-switch / unscored conditions trigger per protocol §Exclusions. |
| Output path | `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_045_<replay-id>_<side>_2026-05-16.md` |
| Ledger path | append a new row to `docs/pokemon_mastery/measurement_progress_ledger.csv` |

## Pre-freeze loading rules (NEW — this is the intervention)

These are mandatory, not discretionary. The packet-044 diagnosis showed
67% of misses came from cards not being loaded. For packet 045, before
freezing each turn's answer, you MUST have the listed card in context
when its trigger fires:

- **Spikes on either side** OR **Rest in any package** OR **Sleep Talk**
  OR **any sleeping target on board or bench** OR **any phaze move in any
  revealed package**
  → load `heuristic_core/reset_loop_denial.md`
- **Unique-role piece** (spinner, phazer, RestTalker, breaker, last typed
  absorber) at <80% HP, statused, or facing future Spikes-entry tax
  → load `heuristic_core/spend_or_save_piece.md`
- **Tempted by Toxic / Spikes / Rapid Spin / safe-switch** when a
  converter (damage, coverage, phaze-on-sleeping-target, cash-out,
  lower-cost handoff) is available
  → load `heuristic_core/converter_before_script.md`

Always-load baseline: `active_context.md`, `live_core.md`,
`replay_turn_pause_protocol.md`, `heuristic_core/role_package_ledger.md`,
`heuristic_core/branch_punish_ranking.md`,
`heuristic_core/public_info_tiers.md`,
`heuristic_core/name_next_board_owner.md`, and any decision-relevant
`canon/*.md` or `romhack_deltas/*.md`.

## Pre-freeze branch-punish audit (NEW)

Before freezing each turn's top three, run this audit literally:

- For each top-3 candidate, name the branch it BEATS and the branch
  it LOSES TO.
- If your top candidate is a dead move into a named branch (Toxic
  into a sleeping target; status into a Steel that blanks it; Electric
  into a Ground; generic phaze when direct chip on the named receiver
  is available), demote it.

This catches the packet-044 Turn-22 class state error (Toxic ranked
first while reasoning named a sleeping Snorlax branch).

## Per-turn workflow (per protocol §Required Workflow)

1. Reveal log only up to the current decision turn. Use
   `python tools\pokemon_mastery\replay_turn_pause.py <log> prompt --turn N`.
2. Identify board features → load the required cards per the rules above.
3. Freeze an answer with these fields:
   - **Pre-freeze loaded cards**: list every card name in context.
   - Recommended move / switch.
   - Confidence (e.g., 60/30/10 across top-3).
   - Route reason in one sentence.
   - Ranked top three with one-sentence each.
   - Serious alternatives.
   - Rejected tempting safe/default line.
   - Worst plausible branch + fallback.
   - Public-info tier for any assumption: `revealed` / `strong prior` /
     `possible only`.
   - **Branch-punish audit** result: for each top-3, "beats X, loses to Y".
4. Reveal the turn:
   `python tools\pokemon_mastery\replay_turn_pause.py <log> reveal --turn N`.
5. Score per protocol §Scoring tags.
6. Stop at 30 scored decisions or earlier if protocol §Exclusions /
   §When To Stop And Study triggers.

## Required score summary fields

At the top of the output artifact:

```
Decisions:
Top-match:                      (target: ≥20/30 to claim intervention working)
Acceptable-match:
Positive-selection:
Route-converting move chosen:
Branch-punish chosen:
Role-package update obeyed:
Actual in frozen top three:
Actual branch named before reveal:
Severe blunders:                (must be 0)
Hidden-info errors:             (must be 0)
State errors:                   (must be 0)
Mechanics errors:               (must be 0)
Earliest meaningful error:
```

Also: per-turn `top_rank_failure` tag from the same taxonomy used in
packet 044 (`route_budget`, `branch_probability`, `preservation`,
`status_branch_obedience`, `missing_candidate`, `oracle_style`,
`hidden_package_reveal`, `candidate_weighting`, `type_owner`, `precision`,
`wake_count`, or `none`).

## Pass / fail gates

Per the falsification gate in
`reviews/top_match_miss_classification_packet_044.md`:

- **Plateau-broken claim** requires ALL:
  - Top-match ≥ 20/30 (preferably ≥ 25/30 to call the diagnosis
    confirmed strongly)
  - Severe/hidden/state/mechanics all stay 0 (state especially, since
    the audit was supposed to catch the Turn-22 class)
  - Route-conversion ≥ 22/30 (don't fall vs packet 044)
  - Branch-punish ≥ 21/30 (don't fall vs packet 044)
  - Pre-freeze loaded-cards field is filled for every turn

- **Ceiling-reached** (diagnosis was wrong) if exact-top < 20/30
  despite the trigger block being honored on every relevant turn. In
  that case, the per-turn loaded-cards field + per-turn
  top_rank_failure tag will tell us whether failures are H2 (cards
  loaded but ignored — pairwise contrastive drills next) or
  H3/H4 (oracle ceiling — multi-oracle pivot next).

- **Inconclusive** if the trigger block was not honored on every
  relevant turn (e.g., `reset_loop_denial.md` not loaded on a Spikes
  board). Re-run the affected turns with full compliance.

## Honesty rules

- Do NOT anchor on hidden information. Possible-only branches shape
  side-bets, not the main line.
- Do NOT read forward turns of the replay for anything except team
  reconstruction (and note exactly which turns you peeked at for
  reconstruction, before turn 1 starts).
- Do NOT promote a miss into a new card rule unless it repeats. Single
  misses go in the per-turn `top_rank_failure` field, not into card
  edits.
- Do NOT claim plateau-broken without ALL gates above. Partial wins
  are partial wins.
- Do NOT skip the pre-freeze branch-punish audit. It is the H2 fix.

## After scoring

Write the diagnosis paragraph at the end of the artifact under
`## Interpretation`. Cover:

- Did the trigger block fire on every relevant board? (List any
  trigger-relevant turn where the card was missed.)
- Of any remaining exact-top misses, what's the H1/H2/H3/H4 split?
- Recommended next action: keep the trigger block, expand it, fall
  back to pairwise contrastive drills (Issue 21), or pivot to
  multi-oracle (Issue 22).

Then append a new ledger row at
`docs/pokemon_mastery/measurement_progress_ledger.csv` with the full
metric set.

## Comparison protocol with Claude run

A parallel Claude session will run the same replay (same URL, same
side perspective, same side-known source). After both packets are
written, the comparison passes are:

1. **Pre-freeze loaded cards per turn**: do both runs load the same
   cards on the same triggers? Any mismatch indicates a trigger-block
   reading difference (model-specific) vs both honoring the same
   triggers (model-agnostic).
2. **Per-turn top-3 vs actual**: where Claude and Codex diverge, the
   top_rank_failure tag tells us whether divergence is style (H4) or
   reasoning (H1/H2/H3).
3. **Aggregate exact-top**: if both ≥20/30, the intervention is robust.
   If only one, the cards are tuned for that model.
4. **State/branch-obedience errors**: the audit's job. Both should be 0.

The comparison itself is a separate review doc, not part of this
packet. Aim: write your own packet honestly, don't try to match
Claude's choices.
