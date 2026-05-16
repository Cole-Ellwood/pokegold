# Thief/Thunder Lure Handoff Probe 001 - 2026-05-15

Type: focused regression probe after `thief_thunder_lure_handoff_transfer_001`.

Status: nonblind constructed drill. This checks whether the item/lure handoff
lesson can be stated as concrete move choices without breaking information
tiering. It is not fresh replay proof and must not count as mastery progress.

Source basis:

- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/thief_thunder_lure_handoff_review_001_2026-05-15.md`
- Smogon Forums GSC Nidoking:
  `https://www.smogon.com/forums/threads/gsc-nidoking.3681149/`
- Smogon Forums An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`

## Score Summary

Scenarios: 6.
Top-match: 6 / 6.
Acceptable-match: 6 / 6.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 6 / 6.
Route-converting move chosen: 6 / 6.
Branch-punish chosen: 6 / 6.

Result: pass as regression only. The answers ranked item removal, support-job
handoff, revealed-lure absorber, and no-Team-Preview class fallbacks without
claiming hidden exact teammates.

## Scenario 1 - Nidoking Lead Item Route

Public state:
p1 Nidoking leads against p2 Tyranitar. No moves are revealed. p2 is likely to
move to a bulky Zapdos/Snorlax-style Nidoking answer. p1 Nidoking is known to
have no item from team context; the exact p2 receiver is hidden.

Frozen answer:
Top action: Thief. Confidence: medium.

Ranked candidates:

1. Thief into the bulky receiver class.
2. Lovely Kiss if sleep value beats item denial or the receiver is not likely
   to lose a route from item removal.
3. Earthquake if Tyranitar staying is the best branch.

Reason:
Item removal changes the later recovery and hazard clock. The exact receiver
stays hidden, but the route class is public enough from the lead matchup.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Item Job Complete, Coverage Threat Live

Public state:
p1 Nidoking has just used Thief into p2 Zapdos. Zapdos has not revealed moves,
but standard Hidden Power coverage is a strong prior with Thunder rejected into
Nidoking's Ground immunity. p1 has Snorlax available and no Spikes are up.

Frozen answer:
Top action: switch Snorlax. Confidence: medium.

Ranked candidates:

1. Switch Snorlax.
2. Lovely Kiss if Zapdos staying and accepting sleep is more likely than
   coverage.
3. Ice Beam/Thunder only if revealed or side-known and it changes the route.

Reason:
The item job is complete for the current board. The handoff preserves Nidoking
and catches the likely coverage line without anchoring on an exact hidden move.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Snorlax Thunder Reveal, Second Turn

Public state:
p1 Snorlax has revealed Double-Edge and Thunder into p2 Cloyster. Thunder
missed. p2 Cloyster has set Spikes and is still healthy enough to leave. p2 has
unrevealed bench.

Frozen answer:
Top action: counter-handoff to the Steelix/Golem/Tyranitar absorber owner if
available; otherwise keep Thunder as fallback. Confidence: medium.

Ranked candidates:

1. Counter-handoff to the expected Thunder/Normal absorber owner.
2. Thunder if Cloyster cannot leave profitably or no absorber owner is likely.
3. Double-Edge only if accuracy damage matters more than the absorber branch.

Reason:
Thunder being public makes the second-turn receiver live. The recommendation
names a class, not an exact hidden Steelix.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Cloyster After Spikes Versus ThunderLax

Public state:
p2 Cloyster has set Spikes and faces p1 Snorlax that revealed Thunder last
turn. p2 has Steelix revealed and healthy. Cloyster still has future Spin,
Explosion, and checking value.

Frozen answer:
Top action: switch Steelix. Confidence: high.

Ranked candidates:

1. Switch Steelix.
2. Explosion only if preserving Cloyster fails and the trade opens a named
   converter.
3. Toxic/Surf if it hits the incoming owner more than Steelix preserves.

Reason:
Cloyster's support job landed, but that does not make Explosion automatic.
Steelix blocks the obvious lure and preserves Cloyster's future jobs.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Opposite Boundary: Active Removal Beats Speculation

Public state:
p1 Snorlax has revealed Thunder. p2 Cloyster is at 22%, p2 has no revealed
Ground/Steel/Rock absorber, and Cloyster must stay or lose the Spikes war.

Frozen answer:
Top action: Thunder. Confidence: medium-high.

Ranked candidates:

1. Thunder.
2. Double-Edge if Thunder miss risk loses the route and Double-Edge KOs.
3. Counter-handoff only if a receiver branch is stronger than removing
   Cloyster.

Reason:
The second-turn lure rule does not ban repeating coverage. If the active
target cannot leave profitably and removal converts now, pressure stays top.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Hidden Exact Discipline

Public state:
p1 Snorlax has revealed Thunder into Cloyster, but p1 has not revealed any
Water-type or Steelix answer. p2 might have Steelix, Golem, Tyranitar, or no
clean absorber.

Frozen answer:
Top action: state the class conditionally: if a Steelix/Golem/Tyranitar
absorber is likely, the best p1 line is the matching counter-handoff owner by
class; if not, repeat Thunder or Double-Edge by active route. Confidence:
medium.

Ranked candidates:

1. Conditional class-based counter-handoff.
2. Thunder into Cloyster if the absorber class is unavailable or too risky.
3. Exact hidden Cloyster/Starmie/Suicune call only as a high-risk read with
   fallback.

Reason:
No-Team-Preview permits class reasoning but not hidden exact-team anchoring.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. When item removal
or a lure move appears, freeze this sequence:

1. Did the item/lure move already complete its current job?
2. Which receiver now blanks or punishes the revealed move?
3. Which owner meets that receiver by class, not hidden exact name?
4. Does repeating the active move remove the target now, or merely hit the old
   board?
5. Is cash-out better than preservation after the support job, and what
   converter does it open?
