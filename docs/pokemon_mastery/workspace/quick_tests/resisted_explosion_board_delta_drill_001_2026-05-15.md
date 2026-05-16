# Resisted Explosion Board Delta Drill 001 - 2026-05-15

Parent review:
`reviews/resisted_explosion_board_delta_review_001_2026-05-15.md`

Mode: constructed nonblind regression probe from packet 038 misses. This is
repair scaffolding only, not fresh proof.

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

## Scenario 1 - Ghost Branch

Public state: Golem faces sleeping Snorlax. Gengar is revealed and can enter
freely on Explosion. Earthquake hits Snorlax and Gengar but not Skarmory.
Zapdos is available to preserve Golem.

Frozen answer: do not rank Explosion first unless the Gengar read and fallback
are explicit. Earthquake or Zapdos is the branch-aware line because it covers
more public branches while preserving the one-shot converter.

Grade: pass.

## Scenario 2 - Resistant Skarmory Opens Special Owner

Public state: Golem faces sleeping Snorlax. Skarmory is revealed at 55-60% and
is the likely branch. If Explosion hits Skarmory, Skarmory survives but falls
into range where Vaporeon or Zapdos enters for free and forces the next board.
Earthquake fails to touch Skarmory, and preserving Golem gives Skarmory another
Whirlwind/Toxic reset.

Frozen answer: Explosion can be top. The target is not removal; the converter
is chip plus action denial plus free special-owner entry.

Grade: pass.

## Scenario 3 - True Snorlax Blocker

Public state: Snorlax is awake or about to wake, blocks the endgame owner, and
can Rest or attack before slow play improves the position. Golem survives the
turn and Explosion either removes Snorlax or puts it in exact free-entry range.

Frozen answer: Explosion is top when the post-trade owner is named. Do not
preserve Golem as generic insurance if Snorlax is the actual blocker and delay
lets it reset.

Grade: pass.

## Scenario 4 - Handoff Cost Ledger

Public state: Zapdos, Snorlax, and a low support piece all answer the visible
Electric or Water pressure. Zapdos is the win pressure, Snorlax is the broad
special wall, and the low support piece has already delivered Spikes and can
absorb one hit before dying.

Frozen answer: rank by route budget, not by "all are safe." Use the lowest
future-job absorber when it preserves the irreplaceable win pressure and broad
wall; use the win pressure only when it creates the next action immediately.

Grade: pass.
