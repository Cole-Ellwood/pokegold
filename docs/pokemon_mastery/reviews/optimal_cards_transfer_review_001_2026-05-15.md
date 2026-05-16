# Optimal Cards Transfer Review 001 - 2026-05-15

Reviewed packet:
`docs/pokemon_mastery/workspace/quick_tests/optimal_cards_transfer_001_smogtours-gen2ou-932864_2026-05-15.md`

## Verdict

The protocol fix helped but did not prove broad improvement.

- Better than the strict one-card diagnostic: acceptable-match recovered to
  29/40, severe/state/hidden/mechanics stayed at 0, and support-loop decisions
  around Forretress, Starmie, Spikes, and Rapid Spin were coherent.
- Worse than the first compressed-core transfer on top-match: 16/40 is below
  the 55% gate and below `compressed_core_transfer_001` by rate.
- The run is useful evidence that the compressed docs are usable only if card
  retrieval is flexible. It is not evidence of 1500-proxy strength.

## Study Notes

Current GSC sources support the missed lesson:

- Smogon's GSC Spikes article frames Spikes as a route subgame that must be
  paired with status, offensive pressure, phazing, or spin control; it also
  calls out Forretress as a long-term Spikes and Spin piece, while Cloyster is
  more offensive but on a poison/special-pressure timer.
- The same article says phazers with Spikes force repeated entry damage and
  specifically treats Raikou and Steelix as Spikes partners; this directly
  explains why Tyranitar/Steelix-style Roar lines can beat generic damage when
  the opponent is switching or resting.
- The GSC lead-cycle forum analysis says Electrics into Snorlax/Ground/Cloyster
  naturally create early double-switch chances. That matches the missed
  Steelix into Raikou and Zapdos into Starmie counter-handoffs.
- Smogon Starmie material emphasizes Rapid Spin plus Recover as Starmie's GSC
  differentiator. In this run, once Substitute was revealed, the correct lesson
  was not "Sub is always top"; it was "Sub changes the spin timing and
  double-switch safety."
- Snorlax analysis confirms Earthquake + Curse + Rest threatens phazers and
  non-Ghost checks; my p2 turn 18 miss under-ranked revealed Earthquake after
  it became public.

Sources:

- https://www.smogon.com/gs/articles/gsc_spikes
- https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/
- https://www.smogon.com/smog/issue35/remembering-our-roots
- https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/
- https://www.smogon.com/articles/generation-defining-mechanics

## Local Doc Updates

- `live_core.md`, `active_context.md`, and `heuristic_core/README.md` now allow
  the useful number of tiny cards instead of a fixed one-card cap.
- `heuristic_core/name_next_board_owner.md` now asks for the owner after the
  opponent's counter-handoff.
- `heuristic_core/reset_loop_denial.md` now explicitly checks whether
  Roar/Whirlwind with Spikes converts better than direct damage.

## Next Rep

Run another fresh compressed-core packet with flexible tiny-card retrieval.
Before locking each answer, add one sentence:

`If my handoff is obvious, their counter-handoff is ___, and my move still beats it by ___.`

Do not claim progress unless top-match rises while acceptable, positive,
route, branch, and zero severe/hidden/state/mechanics gates hold.
