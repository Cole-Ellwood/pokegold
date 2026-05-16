# Early-Cycle Counter-Handoff Probe 001 - 2026-05-15

Type: focused regression probe after
`snorlax_forretress_counter_handoff_transfer_001`.

Status: nonblind constructed drill. This checks whether the Snorlax,
Forretress, Zapdos, and Cloyster lead-cycle lesson can be restated as concrete
move choices. It is not fresh replay proof and must not count as mastery
progress.

Source basis:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

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

Result: pass as regression only. The answers obeyed the early-cycle checklist:
name the next-board owner, then choose active pressure, handoff, coverage, or
status according to what converts through that owner. The prompts were authored
from known misses, so this is not unseen progress.

## Scenario 1 - Rest-Capable Pressure Before Preservation

Public state:
p1 Snorlax is active at 88% and toxic-poisoned against p2 Forretress at 83%.
p1 Snorlax has revealed Double-Edge. p2 Forretress has revealed Toxic. No
Spikes are down yet. p1 has a healthy Zapdos in back, but no revealed Ghost.
Snorlax has not revealed Rest, but Rest is a strong-prior Snorlax route and the
current hit changes Forretress's future job.

Frozen answer:
Top action: Double-Edge. Confidence: medium.

Ranked candidates:

1. Double-Edge.
2. Switch Zapdos if Forretress's next action is clearly Spikes or Explosion
   pressure and Snorlax cannot reset.
3. Fire coverage only as an explicit high-risk read if the set supports it.

Reason:
Toxic does not automatically force preservation. Double-Edge pushes Forretress
toward a later Explosion, Spin, or support threshold, and Snorlax may still
clear the clock with Rest later. The fallback is Zapdos if Forretress's support
job becomes more important than the damage threshold.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Handoff Into RestLax

Public state:
p2 Snorlax is active at 100% against p1 Snorlax at 69%, poisoned, with Spikes
on p1's side. p1 Snorlax has revealed Double-Edge and is likely to Rest or
switch soon. p2 Forretress is revealed at 66% with Toxic, Spikes, and Hidden
Power. p2 Snorlax has no moves revealed.

Frozen answer:
Top action: switch Forretress. Confidence: medium.

Ranked candidates:

1. Forretress handoff.
2. Curse if p1 Snorlax cannot Rest or leave safely.
3. Double-Edge if immediate damage forces the route before Forretress enters.

Reason:
The next board belongs to the RestLax / sleep-cycle branch, not to a healthy
Snorlax mirror by default. Forretress has already delivered support but still
compresses Normal resistance, Toxic pressure, coverage, and possible cash-out.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Status Into The Pressure Handoff

Public state:
p2 Forretress is active at 66% against p1 sleeping Snorlax at 100%. p1 has
revealed Zapdos at 76%. p2 Forretress has revealed Toxic, Spikes, and Hidden
Power. p1 Snorlax is likely to leave to preserve sleep turns or bring Zapdos
back in against Forretress.

Frozen answer:
Top action: Toxic. Confidence: medium.

Ranked candidates:

1. Toxic into Zapdos.
2. Hidden Power if the branch is a direct Zapdos or Ghost entry and damage is
   the needed threshold.
3. Snorlax handoff if p1 stays asleep and Forretress's job is done.

Reason:
The named branch is Zapdos, not the sleeping Snorlax. Toxic misses if Zapdos
does not enter, but it is the branch-punish that changes the pressure owner's
future value. Hidden Power is the fallback if damage matters more than the
timer.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Counter-Handoff From Electric Pressure

Public state:
p1 Zapdos is active at 82% against p2 Forretress at 66%. p1 has a sleeping
Snorlax and a healthy unrevealed Cloyster; p2 has revealed Snorlax at 100%.
Spikes are on p1's side. p2 has already moved Snorlax into Zapdos once.

Frozen answer:
Top action: switch Cloyster. Confidence: medium-low.

Ranked candidates:

1. Cloyster handoff.
2. Thunder if p2 Forretress stays or the expected Snorlax branch is less likely.
3. Snorlax if preserving Cloyster's HP is more important than meeting Snorlax.

Reason:
The repeated next-board owner is p2 Snorlax. Cloyster meets that board while
also threatening Spikes, Surf, Toxic, or Explosion later. Thunder is acceptable
only if the active Forretress is likely to stay or if Cloyster cannot afford
the entry tax.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Do Not Over-Handoff Through Active Coverage

Public state:
p1 Zapdos is active at 82% against p2 Forretress at 35%. p2 Snorlax is revealed
at 100%, but p1 Zapdos has revealed Thunder and Hidden Power that meaningfully
hits the expected Ground or Normal-resist pivot. p1 Cloyster exists but is at
42% and would enter through Spikes.

Frozen answer:
Top action: Thunder. Confidence: medium.

Ranked candidates:

1. Thunder.
2. Hidden Power if the named receiver is the coverage target.
3. Cloyster handoff only if the Snorlax branch is certain and Cloyster's entry
   preserves more than it costs.

Reason:
The handoff is real, but active pressure already improves through the expected
branch and avoids spending a low Cloyster through Spikes. The correction is
not to double-switch every time; it is to choose the move that affects the next
board.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Possible-Only Coverage Cannot Anchor

Public state:
p1 Snorlax is active at 88% and toxic-poisoned against p2 Forretress at 83%.
p1 Snorlax has revealed only Double-Edge. p1 may legally have Fire Blast, but
there is no public clue. p1 has Zapdos in back. p2 Forretress has revealed
Toxic, and no Spikes are down yet.

Frozen answer:
Top action: Double-Edge. Confidence: medium.

Ranked candidates:

1. Double-Edge.
2. Zapdos handoff if the next board is Forretress support and Snorlax cannot
   convert.
3. Fire Blast only as a high-risk read with Double-Edge fallback.

Reason:
Possible-only Fire coverage cannot anchor the recommendation. The public route
is active damage into Forretress's HP/job while keeping Rest and handoff
fallbacks explicit.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. Before each
nontrivial early-cycle decision, write:

1. current pressure route;
2. next-board owner;
3. whether active pressure hits the owner;
4. whether the handoff enters safely through Spikes/status;
5. fallback if the named owner is only a strong prior.
