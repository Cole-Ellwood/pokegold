# Hazard Pressure Move Taxonomy Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_030` misses into six compact prompts
that force the pressure move on a hazard-control turn: direct damage, setup,
Rest, phaze, sacrifice, or spinblock.

This is not final-exam evidence. The prompts were built after seeing the miss,
so the score is a regression/checklist result, not a fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_030_spinblock_pressure_boundary_smogtours-gen2ou-934312_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/spin_vs_setup_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC Spikes forum thread:
  `https://www.smogon.com/forums/threads/playing-with-spikes-in-gsc-qc-2-2-gp-2-2-done.3475184/post-4501581`

Source note: the GSC Spikes source frames hazards as enabling forced-switch
and pressure sequences, not as self-contained progress. Cloyster sources make
Surf part of hazard control because it hits common spinners and switch-ins.
The GSC threat material notes Jolteon can use Baton Pass and Growth, so setup
can be the pressure move when it forces the opponent to answer the route.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 1 and 2 need fresh replay transfer
because they were the exact misses in `replay_turn_pause_030`: ordinary damage
and setup were underweighted as pressure moves.

## Scenario 1 - Direct Damage Is The Pressure Move

Public state: vanilla GSC, spectator-public style. Our Cloyster is active at
100%, badly poisoned, with Spikes and Surf revealed. Both sides have Spikes.
Opposing Forretress is active at 100% with Spikes and Toxic revealed, and is
likely to switch to Zapdos, Tyranitar, Gengar, or another absorber if it fears
Surf or Explosion. Our own side has Golem or Starmie available to spin later,
but no immediate entry is collapsing this turn.

Frozen answer: use Surf. Confidence: high. The route is to punish the support
pivot now; Surf damages the spinner, the Electric pivot, and several Explosion
absorbers, while Rapid Spin risks spending the turn into a switch that makes
Cloyster passive. Serious alternatives: Rapid Spin only if our grounded core
cannot take another entry; switch only if Cloyster must be preserved for a
later Explosion. Worst branch: Forretress stays and spins or resets later, but
it still takes pressure and the hazard route has not been abandoned.

Policy key: ordinary damage is a hazard-control move when it punishes the
spinner or the expected support pivot.

Grade: complete.

## Scenario 2 - Setup Is The Pressure Move

Public state: vanilla GSC, spectator-public style. Our Jolteon is active at
99% against opposing Forretress at 79%. Spikes are up on the opponent's side;
our side is clear. Forretress has Rapid Spin / Spikes / Toxic revealed. Our
Jolteon has Growth revealed or is a known Baton Pass Jolteon. The opponent's
Snorlax and Tyranitar are the likely absorbers, but both take Spikes on entry.

Frozen answer: use Growth. Confidence: medium-high. The route is to convert
Forretress's support passivity into a setup threat, forcing the opponent to
answer Jolteon or a Baton Pass receiver. Serious alternatives: attack if
Forretress is in range or if a Ground-type is too likely; switch only if
Tyranitar enters freely and ruins the route. Worst branch: Snorlax enters with
Earthquake and forces Jolteon out after one hit, making Growth only a chip
trade.

Policy key: setup can be the pressure handoff when it creates a route the
support Pokemon cannot ignore.

Grade: complete.

## Scenario 3 - Rest Preserves The Converter

Public state: vanilla GSC, player-side known set. Our Snorlax is active at
47%, paralyzed, with Double-Edge / Rest revealed. Opposing Forretress is active
at 73% with Rapid Spin / Spikes / Toxic revealed. Spikes are up on the
opponent's side. Our Gengar can block Rapid Spin, but Snorlax is the only piece
that can still punish Zapdos and Tyranitar over the next sequence.

Frozen answer: use Rest. Confidence: high. The route is preservation before
spinblock: if Snorlax stays low and paralyzed, the pressure plan collapses, but
after Rest we can block Spin or pressure again. Serious alternatives: switch
Gengar only if the layer is the entire win route and Snorlax has no future job.
Worst branch: Forretress sets Spikes or spins while Snorlax sleeps, forcing a
later cleanup problem.

Policy key: Rest can be the pressure move when it keeps the converter alive
for the next hazard sequence.

Grade: complete.

## Scenario 4 - Phaze Converts The Layer

Public state: vanilla GSC, player-side known set. Our Steelix is active at
84% with Roar / Earthquake / Curse / Rest. Spikes are up on the opponent's
side. Opposing Forretress is active at 62% and can Rapid Spin, but the
opponent's Zapdos, Snorlax, and Raikou are all in meaningful Spikes ranges.
Our Gengar is healthy but switching it in would give up Steelix's current
phaze window.

Frozen answer: use Roar. Confidence: medium-high. The route is immediate
conversion: one forced entry matters more than merely preserving the layer for
later. Serious alternatives: Gengar only if Forretress spinning now erases the
only route; Earthquake if it KOs or forces Forretress out. Worst branch:
Forretress spins before the phaze payoff is large enough, or Steelix is worn
below its future check threshold.

Policy key: phazing can be the pressure move when it converts hazards now.

Grade: complete.

## Scenario 5 - Sacrifice Removes The Spinner

Public state: vanilla GSC, player-side known team. Our Cloyster is active at
28% with Explosion / Surf / Spikes / Toxic. Opposing Starmie is active at 54%,
poisoned, and has Rapid Spin / Recover / Surf revealed. Spikes are up on the
opponent's side and are required for our Marowak or Machamp cleanup. Our Ghost
is too low to enter Starmie, and if Starmie spins then Recovers the cleanup
route likely dies.

Frozen answer: use Explosion. Confidence: medium-high. The route is to spend
the support piece to remove the spinner before it resets the endgame. Serious
alternatives: Surf only if it KOs or forces Starmie below a guaranteed revenge
range; switch only if a real blocker can enter. Worst branch: Starmie switches
to a low-value absorber or survives and removes the layer later.

Policy key: sacrifice is the pressure move when the spinner must be removed
and no block, setup, Rest, or phaze line covers the turn.

Grade: complete.

## Scenario 6 - Spinblock Is The Pressure Move

Public state: vanilla GSC, spectator-public style. Our Snorlax is active at
66% against opposing Forretress at 79%. Both sides have Spikes. Forretress has
Rapid Spin / Spikes / Toxic revealed. Our Gengar is healthy and can enter the
Rapid Spin turn. Snorlax has only Double-Edge revealed, is not in a setup or
Rest position, and attacking Forretress does not create a meaningful route.

Frozen answer: switch Gengar. Confidence: high. The route is current
retention: no active pressure move compensates for losing the layer, so the
Ghost entry is the route-preserving action. Serious alternatives: Double-Edge
only if Forretress is in range or a predicted pivot is more important than the
layer. Worst branch: Forretress predicts Gengar with a pivot or Toxic support,
but Rapid Spin is blocked and the hazard route remains live.

Policy key: spinblock is correct when the active cannot convert a stronger
route and the layer is still material.

Grade: complete.

## Resulting Rule

On a hazard-control turn, classify the pressure move before choosing:

1. Direct damage: punishes the spinner or expected pivot.
2. Setup: creates a route the support Pokemon cannot ignore.
3. Rest: preserves the converter that will exploit the hazard sequence.
4. Phaze: converts the current layer immediately.
5. Sacrifice: removes the spinner or support piece when no other line covers
   the turn.
6. Spinblock: preserves the layer when no stronger active route compensates.

## Next Study Target

Run a fresh unseen replay segment with a hazard-control turn and force this
six-class taxonomy before revealing the move. Score whether the chosen class,
not just the exact move, matches the expert route.
