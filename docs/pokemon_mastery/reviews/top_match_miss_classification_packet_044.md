# Top-Match Miss Classification - Packet 044 - 2026-05-16

## Bottom line

Of packet 044's 15 exact-top misses, **10 (67%) trace to a single cause:
the cards that contain the route-budget / preservation tiebreaker were
NOT in the pre-freeze context.** The plateau is not "the model has not
learned the tiebreaker." The plateau is "the model has not been loading
the textbook that contains the tiebreaker."

Recommended intervention: **enforced load triggers** in `live_core.md`,
plus a relaxation of the "at most one heuristic_core card" rule for
trigger-matched boards. Not new card content. Not more prose. A 10-15
line block that turns the existing tiny-card selector from "load when
decision-relevant" (model discretion, single-card cap) into "MUST load
when this board feature is present" (mandatory, multi-card allowed).

## Method

Classify each top-match miss against the **frozen reasoning** in the
packet (no retroactive rationalization), using four mutually exclusive
modes:

- **H1 card-not-loaded**: the heuristic_core card that encodes the
  decision rule was NOT in the pre-freeze load set, and a literal read
  of that card would have flipped the ranking. Includes the
  candidate-not-generated subtype (H1-CG) where the missing card would
  have surfaced the actual move as a candidate.
- **H2 card-loaded-but-ignored**: the relevant card WAS loaded, its
  rule applied to this board, the frozen reasoning even cites the rule
  or names the branch, but the ranking still violated it.
- **H3 card-content-vague**: the relevant card was loaded but does not
  contain a sharp dominance rule for this specific contest, so the
  ranking became a coin flip between plausible moves.
- **H4 oracle-noise**: actual move depended on hidden info, opponent
  style, lead-RPS variance, or was one of multiple defensible options
  with no public-info-only basis for ranking the actual first.

Pre-freeze load set per packet header (line 7):
`active_context, playbook_manifest, live_core, replay_turn_pause_protocol,
heuristic_core/role_package_ledger, heuristic_core/branch_punish_ranking,
heuristic_core/public_info_tiers, heuristic_core/name_next_board_owner,
canon/gsc_lead_rps`.

**NOT loaded**: `heuristic_core/reset_loop_denial.md`,
`heuristic_core/spend_or_save_piece.md`,
`heuristic_core/converter_before_script.md`,
`heuristic_core/name_current_owner.md`,
`heuristic_core/rescore_after_reveal.md`.

Note: this worktree's `live_core.md` says "at most one heuristic_core
card per turn." Packet 044 loaded four heuristic_core cards plus a
canon card, so the cap was already being routinely violated in practice.
The intervention formalizes that "multiple cards are allowed when
triggers fire" rather than fighting the existing one-card cap.

## Per-miss classification

| Turn | Predicted top | Actual | Failure mode | Card that would have flipped it |
|---|---|---|---|---|
| 1 | Double-Edge | switch Raikou | **H4** | (lead RPS variance; no card flips this reliably) |
| 4 | Toxic | Hidden Power | **H1-CG** | converter_before_script + branch_punish (HP beats Forretress branch); also possibly Issue-12 sparse side-known |
| 6 | Toxic | switch Tyranitar | **H1-CG** | spend_or_save_piece (preserve Skarmory via Normal-resist handoff) |
| 9 | switch Skarmory | switch Cloyster | **H1** | reset_loop_denial (Lax-Rest read → free Cloyster Spikes turn) |
| 11 | Surf | switch Skarmory | **H1** | spend_or_save_piece (don't spend spinner Cloyster to Sleep Talk EQ); reset_loop_denial (RestTalk wake clock) |
| 12 | Toxic | Whirlwind | **H1-CG** | reset_loop_denial ("on the wake-and-act turn, re-sleep, status, phaze, cash-out can outrank generic damage") |
| 15 | switch Cloyster | switch Skarmory | **H1** | spend_or_save_piece (preserve Cloyster as hazard mirror) |
| 18 | switch Cloyster | stay (asleep) | **H1** | spend_or_save_piece + reset_loop_denial ("before bringing in spinner on sleep turn, do they enter and get punished harder later?") |
| 19 | Whirlwind | Hidden Power | **H2** | branch_punish_ranking WAS loaded; named Snorlax receiver; rule explicitly says HP > generic phaze |
| 20 | Whirlwind | Toxic | **H3** | reset_loop_denial would partially fire ("Toxic-vs-Recover/Rest race"); but no card has a sharp Whirlwind-vs-Toxic dominance rule on a fresh-Rested target |
| 22 | Toxic | Whirlwind (dragged Zapdos) | **H2** (also state error) | branch_punish_ranking WAS loaded; reasoning named sleeping Snorlax branch; Toxic into sleeping target is dead; rule says "do not name a branch and leave its punish below a generic safe move" |
| 24 | Thunderbolt | Rest | **H1** | spend_or_save_piece + reset_loop_denial (preserve statused absorber when chip does not change next forced choice) |
| 27 | Double-Edge | switch sleeping Raikou | **H4** | hidden Whirlwind reveal; no public-info path |
| 28 | Megahorn | switch Raikou | **H1** | spend_or_save_piece (Heracross has later job; Raikou is the typed Zapdos owner; owner > branch-punish when accuracy/coverage is mixed) |
| 30 | Double-Edge | Rest | **H1** | spend_or_save_piece + reset_loop_denial ("when named grounded counter-owner arrives as absorber near future-entry failure, Rest beats chip") |

## Aggregate

| Mode | Count | Share |
|---|---|---|
| H1 card-not-loaded (incl. H1-CG candidate-not-generated) | 10 | 67% |
| H2 card-loaded-but-ignored | 2 | 13% |
| H3 card-content-vague | 1 | 7% |
| H4 oracle-noise | 2 | 13% |

Of the 10 H1 misses, the absent cards break down as:
- `reset_loop_denial.md` would have fired on Turns 9, 11, 12, 18, 24, 30 (six misses)
- `spend_or_save_piece.md` would have fired on Turns 6, 11, 15, 18, 24, 28, 30 (seven misses, with overlap)
- `converter_before_script.md` would have helped on Turn 4 (one miss)

The same two cards (`reset_loop_denial`, `spend_or_save_piece`) cover the
overwhelming majority of H1 misses. Most H1 misses are over-determined —
either card alone would have flipped them.

## Why this matters

The inventory at `top_match_wall_issue_inventory_2026-05-16.md` and
`training_method_review_007_2026-05-16.md` identified the wall as
"route-budget ordering after candidate generation succeeds" and proposed
patching `reset_loop_denial.md` with a sharper carry-forward rule. The
annotation at `route_budget_tiebreaker_annotation_001_2026-05-16.md`
extracted the exact tiebreakers from 5 of the misses.

All three diagnoses are **correct about the rule** but missed the prior
question: **the rule was already written**, in `reset_loop_denial.md`
lines 10-13 ("Fast tiebreaker: if Spikes, Rest, phaze, status, or
correct-owner handoff already created pressure, chip/status/coverage is
top only when it forces the next choice...") and in `spend_or_save_piece.md`
lines 89-91 ("Do not spend a low RestTalker, spinblocker, spinner, or
phazer on chip after poison, Spikes, or Rest pressure has already created
the route").

The training loop has been **adding more rules to cards that are not
being loaded**. That is why fix-as-document hit a wall. The signal cannot
reach the ranker if the cards encoding it are not in the prompt.

A secondary observation: this worktree's `live_core.md` enforces a
"at most one heuristic_core card per turn" cap, but packet 044 already
loaded four heuristic_core cards plus canon. That cap is not being
honored in practice, and trying to satisfy it would forbid loading the
two cards (reset_loop_denial + spend_or_save_piece) that the diagnosis
needs to fire simultaneously on the majority of misses. The intervention
explicitly relaxes the cap for trigger-matched boards.

## Recommended intervention (primary)

Replace the "At most one heuristic_core/*.md card" line in
`live_core.md`'s Fresh Replay Routing with "Any heuristic_core cards
triggered by the Load-Required Triggers section below; otherwise the
smallest discretionary set."

Add a **Load-Required Triggers** block near the top of `live_core.md`:

```
## Load-Required Triggers

For these boards, the listed card MUST be in pre-freeze context.
The selector below is mandatory for these triggers, not discretionary:

- Spikes (either side), Rest in any package, Sleep Talk, any sleeping
  target, or any phaze move in any revealed package
  → heuristic_core/reset_loop_denial.md
- Unique-role piece (spinner, phazer, RestTalker, breaker, last typed
  absorber) at <80% HP, statused, or facing future Spikes-entry tax
  → heuristic_core/spend_or_save_piece.md
- Tempted by Toxic / Spikes / Rapid Spin / safe-switch when a converter
  (damage, coverage, phaze-on-sleeping-target, cash-out, lower-cost
  handoff) is available
  → heuristic_core/converter_before_script.md

Pre-freeze audit: for each top-three candidate, name the branch it
beats AND the branch it loses to. A dead move into a named branch
(Toxic into a sleeping target, status into a Steel that blanks it,
Electric into a Ground, generic phaze when direct chip on the named
receiver is available) demotes itself.

Record the actual loaded-card set in the packet per turn so H1
(card-not-loaded) and H2 (card-loaded-but-ignored) misses are
distinguishable in post-score diagnosis.
```

Cost: ~20 lines of `live_core.md` net (block addition plus one-card-cap
relaxation). Plus raising the hard-cap from 80 to 100. No new card
content. Enforces use of cards that already exist.

## Recommended intervention (secondary, for H2 misses)

Turns 19 and 22 are H2 — the right card was loaded but its rule was not
obeyed at ranking time. The fix is the **end-of-rank audit** baked into
the trigger block above: before freezing, walk each candidate against
the named branches and confirm the top candidate actually beats them.

This is Inventory Issue 24's "stronger end-of-ranking audit" condensed
to a single requirement: "for each top-3 candidate, name the branch
it beats and the branch it loses to." A dead move into a named branch
(Turn 22 Toxic into sleeping Snorlax) fails this audit visibly.

Cost: 1 line of the trigger block plus 1-2 lines of `live_core.md`'s
Answer Shape section. No new card.

## Residual (H3, H4) — accept

- Turn 20 (H3): Whirlwind-vs-Toxic on a fresh-Rested target is a real
  dominance question. Could add a new line to `reset_loop_denial.md`,
  but a single miss does not justify expansion until repeated.
- Turn 1 (H4): lead RPS opening-turn variance.
- Turn 27 (H4): hidden Whirlwind reveal.

These three misses bound the achievable improvement from the primary
intervention alone. **Floor under the intervention: 12/30 misses
addressable → 27/30 top-match possible** (15 baseline + 10 H1 + 2 H2),
with 3 residual.

## Expected lift and falsification gate

If the primary intervention works as predicted, packet 045 on a similar
board mix should produce:

- exact-top: materially above the 048/089 ≈ 54% recent flat band; the
  packet-044-equivalent would be ~25/30 (10 H1 misses flipped) if every
  H1 fix lands, or ~20/30 (half flip) as a conservative target
- acceptable: stay at or above 29/30 (interventions add cards, not
  removed cards; should not degrade)
- severe/hidden/state/mechanics: stay clean; especially state, where the
  end-of-rank audit explicitly catches Turn-22-class errors
- route-conversion / branch-punish: stay at or above the 22/30 and 21/30
  baselines

**Falsification**: if packet 045 produces exact-top below ~20/30 despite
the trigger block being honored (verifiable by inspecting the per-turn
"loaded cards" field, which we should make explicit in the packet
format), then load-discipline is NOT the dominant cause and the diagnosis
was wrong. Pivot at that point to:

1. H2 mode dominance: cards loaded but not obeyed → audit the ranking
   pass directly, possibly via pairwise contrastive drills (Inventory
   Issue 21).
2. H3 mode dominance: card content too vague → restructure cards as
   decision trees rather than prose.
3. H4 mode dominance: oracle ceiling → switch to multi-oracle
   scoreboard (Inventory Issue 22).

## Caveats and uncertainties

- The packet header lists cards loaded "before freezing." It is possible
  but not documented that the model loaded additional cards mid-turn
  silently. If so, the H1 diagnosis shifts toward H2. To test: make the
  per-turn "loaded cards" field explicit in packet 045.
- Turn 4 sits at H1-CG / Issue-12 boundary (sparse side-known own moves
  vs no card surfacing the candidate). Either way, the system-level
  failure is the same family: the candidate was not generated.
- The 67% / 13% / 7% / 13% split is from 15 misses on one packet. Noise
  is significant. A second packet under the intervention will narrow the
  estimate.
- The main-repo working tree has a parallel uncommitted modification to
  `live_core.md` from a different branch (codex/cleanup-gsc-rebalance-split)
  that relaxes the one-card cap independently. This patch and that
  pending work need to be reconciled at merge time.

## Next action

Patch `live_core.md` in this worktree with the Load-Required Triggers
block and the one-card-cap relaxation. Keep the existing
`reset_loop_denial.md` and `spend_or_save_piece.md` unchanged (they
already have the rules). Run one fresh side-known packet 045 with the
new trigger block live. The packet format should add an explicit
"Pre-freeze cards loaded" list per turn so future diagnostics can
distinguish H1 from H2 without ambiguity.
