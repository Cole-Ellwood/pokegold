# Pokemon Mastery Live Core — v2 Intervention Arm

Hard cap: 200 lines (raised from baseline 100 to fit the audit-first
workflow + probabilistic gating + cash-out justification). This is the
intervention-arm pre-freeze move-choice entrypoint for the /pgoal A/B
counterfactual armed 2026-05-16.
Baseline is `live_core.md`. See `heuristic_core_v2/ARM_README.md` for
the A/B rule.

## Fresh Replay Routing

Before answering a fresh unseen replay turn, load only:

1. This file (`live_core_v2.md`, NOT `live_core.md`).
2. The current replay prompt and public log state.
3. Any `heuristic_core_v2/*.md` cards forced by the Load-Required
   Triggers section below; otherwise the smallest discretionary set
   that answers the live uncertainty.

After answers are frozen, load scoring rules, old policy cards, reviews,
ledger rows, cookbook entries, or source notes for scoring and
postmortem only.

Do not load pre-freeze: `cookbook.md`, `source_to_policy_ledger.md`,
`paused_turn_atlas.md`, `worked_examples/live_turn_drills.md`, old long
`policy_cards/*.md`, scored quick tests, reviews, or external research
returns.

## Load-Required Triggers

For these boards, the listed card MUST be in pre-freeze context. The
selector below is mandatory for these triggers, not discretionary:

- Spikes (either side), Rest in any package, Sleep Talk, any sleeping
  target, or any phaze move in any revealed package
  → `heuristic_core_v2/reset_loop_denial.md`
- Unique-role piece (spinner, phazer, RestTalker, breaker, last typed
  absorber) at <80% HP, statused, or facing future Spikes-entry tax
  → `heuristic_core_v2/spend_or_save_piece.md`
- Tempted by Toxic / Spikes / Rapid Spin / safe-switch when a converter
  (damage, coverage, phaze-on-sleeping-target, cash-out, lower-cost
  handoff) is available
  → `heuristic_core_v2/converter_before_script.md`

Record the actual loaded-card set in the packet per turn so H1
(card-not-loaded) and H2 (card-loaded-but-ignored) misses are
distinguishable in post-score diagnosis.

## Audit-First Workflow (v2 intervention)

The structural change vs baseline. The artifact MUST be filled out in
the order listed. The audit runs BEFORE the ranking is committed.

### Step 1 — Generate candidate set (do NOT rank yet)

List 3-5 plausible candidates as a flat unordered set. No top pick.
Brainstorm; do not anchor on a default.

### Step 2 — Per-candidate audit

For EACH candidate, fill three fields:

- **Beats**: which named opponent branch this candidate is correct vs.
- **Loses to**: which named opponent branch this candidate is dead into
  (Toxic into a sleeping target; status into a Steel that blanks it;
  Electric into a Ground; generic phaze when direct chip on the named
  receiver is available; Explosion / Self-Destruct into a revealed
  Ghost; lock-into-Outrage when an Ice/Steel switch-in is on bench).
- **Dead-branch probability tag** (gates demotion in Step 3):
  - **HIGH**: dead-into target is REVEALED, on bench, AND either
    (a) opponent has pivoted to similar reads earlier this game, or
    (b) last turn's pattern strongly signals the switch (free pivot
    turn, predictable counter-swap chain, opponent's active is at low
    HP and that target is the obvious receiver). Hard demotion.
  - **MEDIUM**: dead-into target is revealed and on bench but no
    specific signal of switch this turn. Soft demotion.
  - **LOW**: dead-into target is unrevealed (only plausible from
    standard sets) OR revealed but opponent has no switch incentive
    (already on field, locked into a multi-turn move, low HP).
    Annotate only — no demotion.

### Step 3 — Apply demotion rule

- **HIGH dead-branch** → candidate cannot be top-1. Move to top-3 or
  out of frame. Avoiding the blunder dominates the lost top-match
  cases.
- **MEDIUM dead-branch** → candidate may be top-1 only if no
  alternative beats both its beats and loses-to branches.
- **LOW dead-branch** → keep candidate at its earned rank; annotate
  the risk in the Step 5 cash-out justification.

### Step 4 — Revised top

Produce the ranked top-3 from the audited candidates. Mark any rank
revised by Step 3 ("revised from #1 to #3 due to HIGH dead-branch on
Gengar pivot — opponent has revealed Gengar and pivoted to it twice
this game").

### Step 5 — Cash-out justification (mandatory when applicable)

If the revised top-1 is a high-variance cash-out (Explosion,
Self-Destruct, lock-into-Outrage, all-in coverage hit) and Step 2
found ANY dead-branch above LOW, write one sentence on why the
cash-out is still correct (e.g., "MEDIUM Gengar-pivot annotated;
alternative #2 loses board control to Spikes-stack on opponent's
free turn, so cash-out is +EV even with the soft risk").

This is the explicit hedge against the T30-class "strict audit demotes
a play the pro correctly cashed out on" failure mode. If you can write
the justification honestly, the cash-out stands. If you cannot, the
audit was right to demote.

## Pre-Move Solve (audit-aware — Step 1 candidate prompts)

Use these as candidate-generation prompts BEFORE Step 1. They are not
ranking criteria.

1. Name current owner: who owns the board right now, by what route?
2. Name next-board owner: if the active target leaves, who owns next?
3. Brainstorm converter candidates: damage, coverage, item removal,
   setup, phaze, cash-out, handoff, route-changing status.
4. Brainstorm preservation candidates: switch to keep a route piece
   alive; safe staple that doesn't burn a one-shot resource (sleep
   clause, para clause, Explosion piece, last typed absorber).
5. Brainstorm reset-denial candidates: Spikes-set turn, Spin turn,
   Rest-block, Recover-deny, phaze-on-sleeping-target.
6. Re-score after reveal: Growth, Substitute, Baton Pass, Curse,
   RestTalk, lure coverage, Thief, Roar, Whirlwind can reclassify the
   whole package — flag if relevant this turn.
7. State public tiers per assumption: `revealed`, `strong prior`,
   `possible only`.

## Guardrails

- No Team Preview: do not use hidden teams, moves, items, PP, or
  future turns.
- Possible-only information can shape a branch, not anchor the main
  line.
- Side-known information must be labeled when spectator-public prompts
  omit it.
- Vanilla GSC knowledge is source material; romhack advice needs local
  status.

## Answer Shape (v2 — fill in this order, no skipping)

1. Pre-freeze loaded cards (always-load + triggered cards listed).
2. Candidate set (3-5 unranked).
3. Per-candidate audit table (beats / loses-to / probability tag).
4. Demotion notes (which candidates were demoted by Step 3 and why).
5. Revised ranked top-3 with one-sentence route reason each.
6. Cash-out justification for top-1 (if applicable per Step 5).
7. Worst plausible branch + fallback.
8. Public-info tier for any unrevealed assumption.

## One-Card Selector (v2 paths)

- `heuristic_core_v2/name_current_owner.md`: unclear current converter.
- `heuristic_core_v2/name_next_board_owner.md`: active may leave.
- `heuristic_core_v2/converter_before_script.md`: safe status / spike
  / spin / switch tempts.
- `heuristic_core_v2/public_info_tiers.md`: lure / item / coverage
  ambiguity.
- `heuristic_core_v2/spend_or_save_piece.md`: low support / cash-out
  / sack / preservation.
- `heuristic_core_v2/reset_loop_denial.md`: Spikes/Spin/Rest/Recover/
  phaze/pass loop.
- `heuristic_core_v2/rescore_after_reveal.md`: package move or set
  detail just became public.
- `heuristic_core_v2/branch_punish_ranking.md`: branch named but not
  yet punished.

## Post-Score Route

Use `heuristic_core_v2/migration_map.md` for compressed old lessons.
Use `policy_cards/` as expanded reference, not live default context.
Keep measured progress tied to fresh top-match, acceptable-match,
route-conversion, and branch-punish movement, not note volume.
