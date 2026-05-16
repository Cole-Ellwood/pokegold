# Pursuit Trap Spend Drill 001 - 2026-05-15

Parent review:
`reviews/pursuit_trap_and_oracle_review_001_2026-05-15.md`

Mode: constructed nonblind regression drill from packet 034 misses. This is
repair scaffolding only, not fresh proof.

## Score Summary

Scenarios: 4.
Top-match / policy-match: 4/4.
Acceptable-match: 4/4.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Before Pursuit Reveal

Public state: Gengar faces newly entered Umbreon. Pursuit is a strong prior but
not public. Gengar is healthy, Spikes are up on Umbreon's side, and Gengar
still has spinblock value.

Frozen answer: pressure first or switch only with a fallback. DynamicPunch,
Thunder, Hypnosis, Explosion, or Destiny Bond can all be valid by set; Steelix
handoff is acceptable only if the answer explicitly prices Pursuit as a branch.

Grade: pass.

## Scenario 2 - After Pursuit Reveal

Public state: Umbreon has revealed Pursuit and remains in against Gengar.
Switching Gengar will take the Pursuit branch and may leave it unable to block
Tentacruel or Starmie later.

Frozen answer: do not call the switch preservation by default. Compare the HP
and job Gengar has after switching with the pressure it can spend now. If the
escape does not preserve a named future job, attack, status, boom, or trade.

Grade: pass.

## Scenario 3 - Low Trapped Gengar

Public state: Gengar is low enough that switching through Pursuit probably
removes it. Umbreon is chipped or statused. Gengar still has one useful attack
before it dies.

Frozen answer: spend the trapped piece with the best pressure. Switching is
not preservation if the Pursuit branch removes the same piece or leaves it too
low to perform the named future job.

Grade: pass.

## Scenario 4 - Passive Skarmory Reopens Spikes

Public state: Skarmory is passive or likely to Rest/Whirlwind, Tentacruel is
still the spinner branch, and Cloyster can re-enter without losing a central
job.

Frozen answer: bring Cloyster and reset Spikes. Safe chip is acceptable only if
the hazard reset cannot be maintained or the active move removes the spinner
branch immediately.

Grade: pass.
