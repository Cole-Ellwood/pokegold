# Steelix Curse/Roar Split Probe 001 - 2026-05-15

Type: focused regression probe after `steelix_curse_roar_split_transfer_001`.

Status: nonblind constructed drill. This checks whether the Steelix
Curse/Roar split can be stated as concrete move choices without breaking
information tiering. It is not fresh replay proof and must not count as
mastery progress.

Source basis:

- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `reviews/steelix_curse_roar_split_review_001_2026-05-15.md`
- Smogon Forums GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums GSC OU Skarmory:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`

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

Result: pass as regression only. The answers separated Curse-before-Roar,
stable Roar loops, active Earthquake, coverage damage clocks, RestTalk
switch-outs, and no-Team-Preview exact-owner discipline.

## Scenario 1 - Curse Before Roar

Public state:
p1 Steelix enters on p2 Raikou as p2 side has Spikes. Raikou is likely to
leave to Skarmory or Tyranitar. Steelix has revealed Curse and Roar, is healthy,
and Skarmory has not revealed coverage.

Frozen answer:
Top action: Curse. Confidence: medium-high.

Ranked candidates:

1. Curse.
2. Roar if the switch loop is already stable or the boost is not needed.
3. Earthquake only if Raikou staying is the strongest branch.

Reason:
The expected receiver gives Steelix a boost turn. Curse makes later Roar and
Earthquake convert harder than immediate hazard chip.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Stable Phaze Loop

Public state:
p1 Steelix is already at +1, has Roar revealed, and p2 side has Spikes. p2
Skarmory is active, has not revealed Hidden Power, and cannot immediately force
Steelix out.

Frozen answer:
Top action: Roar. Confidence: high.

Ranked candidates:

1. Roar.
2. Curse only if the next receiver gives another safe boost and Roar chip is
   less valuable.
3. Switch only if a revealed breaker can enter for free.

Reason:
Once the phaze loop is stable, Roar is the converter. More setup risks giving
the opponent a public loop-breaker.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Active Earthquake Boundary

Public state:
p1 Steelix is at +1 against p2 Tyranitar at 60%. p2 has no safe Flying or
Water receiver revealed, and Tyranitar staying loses to Earthquake.

Frozen answer:
Top action: Earthquake. Confidence: medium-high.

Ranked candidates:

1. Earthquake.
2. Roar if a revealed receiver branch is stronger than removing Tyranitar.
3. Curse only if Tyranitar is leaving and the receiver cannot punish.

Reason:
The split does not demote active pressure. If the current target cannot leave
profitably, Earthquake is the route-converting move.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Revealed Skarmory Coverage Clock

Public state:
p1 Steelix at 90% and +2 faces p2 Skarmory. Skarmory has revealed Hidden Power
that hits Steelix super effectively for about a quarter per hit before crits.
p2 side has Spikes.

Frozen answer:
Top action: Roar. Confidence: medium.

Ranked candidates:

1. Roar while Steelix survives the next coverage hit.
2. Switch to preserve Steelix if the coverage damage plus crit risk makes Roar
   fail.
3. Curse only if the extra boost changes the next damage threshold before
   Hidden Power removes Steelix.

Reason:
After coverage reveal, Steelix must price the damage clock. Roar stays top only
while it still resolves and converts hazard damage.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Rested Raikou Switch-Out

Public state:
p2 Raikou has just used Rest and is asleep at full HP in front of p1 Steelix.
Sleep Talk is not revealed. p2 has Skarmory and Starmie revealed. p2 side has
Spikes.

Frozen answer:
Top action: Curse. Confidence: medium.

Ranked candidates:

1. Curse if Skarmory/Starmie switching is the strongest branch and Steelix can
   use the boost.
2. Roar if the hazard loop is already converting or Sleep Talk/stay is likely.
3. Earthquake if Raikou staying without Sleep Talk is the strongest branch.

Reason:
Rest does not make the sleeper the only target. The switch-out branch can be a
free Steelix boost before the phaze loop.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Hidden Exact Owner Discipline

Public state:
p1 Steelix has Roar and Curse revealed. p2 has shown an Electric and a physical
wall class, but the exact Skarmory/Forretress/Starmie owner has not been
revealed.

Frozen answer:
Top action: name the class conditionally: Curse if the physical wall/spinner
class enters and cannot punish immediately; Roar if the loop is already stable;
Earthquake if the active Electric stays. Confidence: medium.

Ranked candidates:

1. Conditional class-based Curse/Roar/Earthquake split.
2. Exact Skarmory or Forretress call only as a high-risk read with fallback.
3. Generic Roar only if no branch changes the route.

Reason:
No-Team-Preview allows class reasoning but not hidden exact-team anchoring.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. When a phazer or
setup phazer appears, freeze this sequence:

1. Is the phaze loop stable now?
2. Does the expected receiver give a free setup turn first?
3. Does active damage remove the current target before it escapes?
4. Has coverage been revealed that puts the phazer on a damage clock?
5. Which exact owners are revealed, strong-prior, or possible-only?
