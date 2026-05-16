# Irreversible Converter Calibration Drill 001 - 2026-05-15

Parent review:
`reviews/training_method_review_004_2026-05-15.md`

Parent miss:
`workspace/quick_tests/side_known_transfer_037_gen2ou-2584124058_p1_2026-05-15.md`

Mode: constructed nonblind regression probe. This checks whether the repaired
spend/save rule is retrievable after study; it is not fresh replay proof.

## Score Summary

Scenarios: 4.
Top-match / policy-match: 4/4.
Acceptable-match: 4/4.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 4/4.
Route-converting move chosen: 4/4.
Branch-punish chosen: 4/4.

Reusable rule: if reversible pressure covers the active target and named
branch while keeping Explosion, Self-Destruct, Baton Pass, or another
one-shot converter live, rank the reversible line first. Spend now only when
delay allows reset, escape, removal of the user, or route invalidation.

## Scenario 1 - Heracross Into Zapdos Branch

Prompt:
Your Heracross faces Nidoking. Earthquake hits the active harder, but Zapdos is
a strong-prior branch and nothing public says Nidoking must stay. Seismic Toss
chips Nidoking and Zapdos neutrally while preserving the same route.

Frozen answer:
Seismic Toss first. Earthquake is acceptable only when the Nidoking removal or
range change is named and worth losing Zapdos-branch coverage.

Grade: pass.

## Scenario 2 - CurseLax One Turn Before Cash-Out

Prompt:
Your Snorlax has Curse and Self-Destruct. The opposing Snorlax is sleeping or
boxed into a slow mirror, and one more Curse improves both the active matchup
and next-turn Self-Destruct range. No public branch shows an immediate Rest,
phaze, or removal that invalidates delay.

Frozen answer:
Curse before Self-Destruct. Cash-out becomes top after the extra Curse if the
trade then creates a named free-entry owner or prevents a reset.

Grade: pass.

## Scenario 3 - Steelix Pressure Before Explosion

Prompt:
Your Steelix can Earthquake or Explode into a loop involving Exeggutor,
sleeping Cloyster, and Alakazam. Earthquake covers the active and common
switch branch while keeping Explosion for a later forced reset or escape.

Frozen answer:
Earthquake or the preserving handoff first. Explosion is top only if the named
target can otherwise wake, reset, escape, remove Steelix, or invalidate the
route before Steelix gets another useful action.

Grade: pass.

## Scenario 4 - Low Snorlax Into Faster Zapdos

Prompt:
Your low Snorlax has Self-Destruct and faces Zapdos. Public speed and damage
show Zapdos attacks first. In branch A, revealed Thunder removes Snorlax before
Self-Destruct can move. In branch B, Snorlax survives Thunder and Zapdos is the
named blocker to the endgame owner.

Frozen answer:
Branch A: preserve or hand off; Self-Destruct is a read with a named miss or
switch fallback, not the main line. Branch B: Self-Destruct can be top when
the trade creates the named owner and no better reversible move covers both
active and branch.

Grade: pass.
