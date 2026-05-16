# Wake / Pass Critical Ledger Drill 001 - 2026-05-15

Parent review:
`reviews/training_method_review_002_2026-05-15.md`

Mode: constructed nonblind regression drill from packet 030. This is repair
scaffolding only, not fresh proof.

## Score Summary

Scenarios: 4.
Policy-match: 4/4.
Acceptable-match: 4/4.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Rest Wake/Act

Public state: Snorlax used Rest, then had two logged sleep actions with Sleep
Talk. The helper marks `Rest sleep actions 2; wake/act next in GSC`. Opposing
Marowak is at 47% with +2 Speed from Baton Pass.

Frozen answer: Double-Edge, not Sleep Talk. The critical ledger says wake/act
now, passed Speed, and Marowak's Swords Dance/Earthquake branch is lethal if it
survives. Sleep Talk is the stale script and can fail because Snorlax is awake.

Grade: pass.

## Scenario 2 - Sleep Talk Turn Still Valid

Public state: Snorlax used Rest last turn and has `Rest sleep actions 1` after
one logged Sleep Talk turn. Opposing Jolteon is at full and may AgilityPass.

Frozen answer: Sleep Talk. This is still a true sleep action, and Sleep Talk
can hit Jolteon or the receiver while preserving Snorlax. Do not switch unless
the named receiver needs a specific answer.

Grade: pass.

## Scenario 3 - Receiver Job Changes

Public state: Jolteon has revealed Agility + Baton Pass. Spikes are on our
side, Starmie is healthy and faster than +2 Snorlax, and Snorlax is expected as
the receiver.

Frozen answer: switch Starmie before the pass when the route job is Rapid Spin.
The receiver answer is not generic damage; it is the owner that removes Spikes
and survives the first passed attack.

Grade: pass.

## Scenario 4 - Same Pass, Different Job

Public state: Jolteon has revealed Agility + Baton Pass. Our side has already
cleared Spikes. Our Snorlax is awake and healthy, and the likely receiver can
be Tyranitar, Snorlax, or Marowak.

Frozen answer: Double-Edge. With no active Spin job, broad receiver damage
beats a speculative handoff. Earthquake is second because it wins if Jolteon
stays or Tyranitar receives, but it fails into Zapdos and is narrower into the
unknown receiver map.

Grade: pass.
