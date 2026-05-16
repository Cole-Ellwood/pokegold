# Toxic Recover Clock Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_023_gen2ou-2608738130`. This is not fresh progress proof.

Source basis:

- `reviews/toxic_recover_clock_review_001_2026-05-15.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/spend_or_save_piece.md`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, Corsola analysis:
  `https://www.smogon.com/forums/threads/corsola-qc-3-3-gp-2-2.3460776/`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Poison Owns Recover

Prompt:
Snorlax at 94% faces Corsola at 45%, badly poisoned, with Recover public. The
toxic counter is already high enough that Corsola can Recover and still be put
back into danger before it creates offense. Snorlax has Curse and Double-Edge;
one unrevealed Water remains after Corsola.

Frozen answer:
Top action: Curse. The poison clock is the active converter, so boosting while
Recover fails to reset progress improves the next board more than immediate
Double-Edge.

Answer key: hit.

## Scenario 2 - Attack When The Clock Is Not Free

Prompt:
Snorlax at 52% faces a badly poisoned Recover user at 31%. The opponent's next
Pokemon is a fast special attacker that enters safely if Snorlax spends a free
turn, and Double-Edge KOs after poison this turn. Curse does not change the
next matchup enough to justify the extra attack taken.

Frozen answer:
Top action: Double-Edge. Toxic being present is not automatic setup; attack
when it removes the blocker and prevents the next owner from entering with a
free hit.

Answer key: hit.

## Scenario 3 - Exact Removal Must Move First

Prompt:
Paralyzed Raikou at 66% faces Shellder. Thunder KOs if Raikou moves, but
paralysis makes Shellder faster. Shellder has no revealed moves, but
Explosion is a live self-KO branch and Forretress or Tyranitar can absorb the
trade while preserving Raikou.

Frozen answer:
Top action: switch to the resist/sack owner. Thunder is not exact removal if
Shellder can move first and trade with the route piece.

Answer key: hit.

## Scenario 4 - Exact Removal Still Beats Overguarding

Prompt:
Healthy Raikou faces a low Cloyster. Thunderbolt KOs, Raikou moves first, and
Cloyster cannot survive to use Explosion. Switching to a resist preserves
Raikou but leaves the support piece alive.

Frozen answer:
Top action: Thunderbolt. Exact removal is real here because move order and
range both remove Cloyster before self-KO, reset, or handoff.

Answer key: hit.

## Next Use

Resume fresh side-known transfer. Before guarding or attacking a self-KO user,
freeze `range + move order + status`. Before attacking a Recover user, freeze
`does recovery reset progress, or does the timer make setup/preservation top?`.

