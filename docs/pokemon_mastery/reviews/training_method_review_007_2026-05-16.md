# Training Method Review 007 - 2026-05-16

Trigger:
After the playbook manifest, canon split, role/package ledger step, and
branch-ranking labels were added, packet 044 produced 30 fresh side-known
decisions from `smogtours-gen2ou-821941`:

- 15/30 top-match.
- 29/30 acceptable-match.
- 28/30 positive-selection.
- 22/30 route-converting move chosen.
- 21/30 branch-punish chosen.
- 25/30 actual in frozen top three.
- 27/30 actual branch named before reveal.
- 0 severe, 0 hidden-info, 1 state, 0 mechanics errors.

This is not progress versus the recent side-known baseline. Packets 041-043
were 48/89 top and 72/89 acceptable; packet 044 is 15/30 top with higher
acceptable but still flat exact ranking. The clean severe/hidden/mechanics
gates are necessary, not proof of improvement.

## Diagnosis

The compact docs are usable. The new packet did not fail because the relevant
knowledge was missing from context:

- candidate generation was broad enough: actual move/switch appeared in the
  top three 25/30 times;
- branch construction was mostly present: the actual branch was named 27/30
  times;
- public information discipline held: no hidden-info errors, and Zapdos
  Whirlwind was not anchored before reveal;
- mechanics mostly held: Rest wake prompts and negative-priority phazing were
  used correctly.

The wall is still the final ranking tiebreaker after a route is already
created. I repeatedly over-ranked active chip, generic status, or an eager
branch punish when the replay's better route was to preserve the correct owner,
Rest before the counter-owner arrived, absorb a sleep turn, or phaze during a
sleep/reset window.

The single unacceptable decision, Turn 22, was sharper: I named sleeping
Snorlax as a branch but still ranked Toxic first. That is a public state
obedience error, not a missing GSC concept.

## Method Repair

Do not add another broad heuristic card yet. `reset_loop_denial.md` and
`spend_or_save_piece.md` already contain the core rule:

- once Spikes, Rest, phaze, or the correct owner handoff has created pressure,
  extra chip/status is not automatically progress;
- Rest, staying with the absorber, phazing the sleeping/resetting target, or
  the lower-cost handoff can be the converter.

Patch the existing `reset_loop_denial.md` front-door tiebreaker instead of
creating a new card, so fresh packets can load one relevant card instead of a
new review.

The next block should be expert replay annotation rather than another fresh
prediction packet. Use packet 044 turns where `actual_in_top_three=1` but
`top_match=0` and write the tiebreaker that made the actual first:

- Turn 18: last sleep turn spent versus immediate hazard contest.
- Turn 19: direct Hidden Power chip into Snorlax switch versus phaze.
- Turn 24: Raikou Rest before Snorlax switch versus Thunderbolt pressure.
- Turn 28: type-owner Raikou handoff versus Heracross branch punish.
- Turn 30: Snorlax Rest before Rhydon enters versus Double-Edge chip.

For each annotation, answer only:

1. What pressure already existed before the move?
2. Which route piece became scarce if I attacked or switched?
3. Which branch did the actual move cover that my top move failed to cover?
4. What one-sentence tiebreaker would have ranked the actual first?

## Next Loop

Run one non-fresh expert annotation block on those five packet-044 turns, then
only after that run another fresh side-known packet. The next fresh target is
not allowed to claim progress unless exact top rises above the recent flat
band while severe/hidden/state/mechanics remain clean and route/branch metrics
do not fall.
