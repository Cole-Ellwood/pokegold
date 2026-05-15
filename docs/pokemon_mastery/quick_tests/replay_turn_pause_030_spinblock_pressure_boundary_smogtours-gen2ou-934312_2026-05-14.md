# Replay Turn-Pause 030 Spinblock Pressure Boundary - smogtours-gen2ou-934312 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934312`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer check after `spin_vs_setup_handoff_probe_001`: with
Spikes up, an active spinner, a possible spinblocker, and live pressure pieces,
price both the spinblock and the pressure handoff without overcorrecting in
either direction.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused local logs: Spikes, Rapid Spin, Gengar, Misdreavus, Cloyster,
  Forretress, Starmie, Donphan, Golem, Snorlax, Curse, Rest, Roar, Growl,
  Toxic, Explosion, Self-Destruct, Zapdos, and Raikou.
- The selected replay had Spikes, Rapid Spin, Gengar, Forretress, Golem,
  Snorlax, Curse, Rest, Roar, Toxic, Explosion, Zapdos, and Raikou counts.
  The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_029_spin_vs_setup_handoff_smogtours-gen2ou-935409_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/spin_vs_setup_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Donphan:
  `https://www.smogon.com/forums/threads/gsc-donphan-done.3733724/post-9998513`
- Smogon GSC Donphan earlier analysis post:
  `https://www.smogon.com/forums/threads/gsc-donphan-done.3733724/post-9920297`
- Smogon GSC Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

Source note: Spikes sources emphasize forcing sequences and offensive pathways,
while Donphan sources warn that spinners can also carry anti-setup tools. The
transfer question is whether the active turn is best spent preserving the
layer, removing our own layer, or using the spin turn to start pressure.

## Score Summary

Turns scored: target phase turns 6-25.

Decisions scored: 39 side-decisions. Turn 23 p1 was excluded because full
paralysis hid the selected move.

Top-match: 20 / 39.

Acceptable-match: 27 / 39.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 8.

Largest route error: turn 18.

## Context Before Target Phase

- Turn 1: p2 switched Tyranitar into p1 Snorlax Double-Edge.
- Turns 2-5: both sides pivoted between Snorlax, Cloyster, Zapdos, and
  Forretress without hazards resolving.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 6 | Snorlax vs Forretress, no hazards | p1 Cloyster; p2 Spikes | p1 Cloyster; p2 Spikes | both top | Correctly expected p2's field job and p1's hazard answer. |
| 7 | Cloyster vs Forretress, p1 side Spikes | p1 Spikes first; p2 Toxic or pivot | p1 Spikes; p2 Toxic | both top | Good: first layer before arguing about handoff or Spin. |
| 8 | poisoned Cloyster vs Forretress, both sides Spikes | p1 Rapid Spin; p2 support/pivot | p2 Zapdos; p1 Surf | p1 miss, p2 acceptable | I overvalued Spin. Surf punished the pivot and kept Cloyster from being passive. |
| 9 | poisoned Cloyster vs Zapdos | p1 Snorlax; p2 Thunder | p1 Snorlax; p2 Thunder | both top | Correct special-sponge handoff. |
| 10 | Snorlax 62 vs Zapdos 84 | p1 Rest or attack; p2 Thunder | p2 Forretress; p1 Double-Edge | both miss | I underpriced the Forretress reset and Snorlax taking the damage turn. |
| 11 | Snorlax 66 vs Forretress 79, both sides Spikes | p1 Gengar if owned; p2 Rapid Spin | p1 Gengar; p2 Rapid Spin immune | both top | Clean transfer: no stronger Snorlax route, so block Spin. |
| 12 | Gengar vs Forretress | p1 attack; p2 pivot | p2 Zapdos; p1 Dynamic Punch | both top | Blocking Spin handed into immediate pressure rather than passive blocking. |
| 13 | Gengar vs Zapdos | p1 special sponge switch; p2 Thunder | p2 Raikou; p1 Ice Punch | both miss | Gengar stayed to chip the Electric pivot; I switched too quickly. |
| 14 | Gengar vs Raikou | p1 special pressure pivot; p2 Thunder/switch | p1 Jolteon; p2 Tyranitar | p1 acceptable, p2 miss | Jolteon was the pressure pivot, but p2 caught it with Tyranitar. |
| 15 | Jolteon vs Tyranitar | p1 Golem; p2 Rock Slide | p1 Golem; p2 Rock Slide | both top | Correctly used the Rock-resistant spinner/ground. |
| 16 | Golem vs Tyranitar, both sides Spikes | p1 Rapid Spin; p2 Zapdos or pivot | p2 Zapdos; p1 Rapid Spin | both top | Clean Spin transfer: removal preserved entries and no Ghost appeared. |
| 17 | Golem vs Zapdos, p1 side clear, p2 side Spikes | p1 switch; p2 Thunder | p1 Jolteon; p2 Forretress | p1 top, p2 miss | p1 kept pressure; p2 went straight back to support. |
| 18 | Jolteon vs Forretress, p2 side Spikes | p1 Thunder pressure; p2 Spin or sponge | p2 Snorlax; p1 Growth | p1 acceptable, p2 acceptable | Main route miss: the pressure route was setup, not direct damage. |
| 19 | +1 Jolteon vs Snorlax | p1 pass or special hit; p2 Earthquake | p1 Thunderbolt; p2 Earthquake | p1 miss, p2 top | Direct hit was chosen; Snorlax had the Earthquake containment. |
| 20 | low Jolteon vs Snorlax | p1 Gengar-style preserve; p2 attack | p1 Cloyster; p2 Double-Edge | p1 miss, p2 acceptable | I picked the wrong absorber; Cloyster was the lower-value contact target. |
| 21 | poisoned Cloyster 59 vs Snorlax 68 | p1 Surf; p2 switch | p2 Zapdos; p1 Surf | p1 top, p2 acceptable | Good: ordinary damage covered the pivot better than cash-out. |
| 22 | poisoned Cloyster vs Zapdos | p1 Snorlax; p2 Thunder | p1 Snorlax; p2 Thunder para | both top | Correct sponge entry, bad branch was paralysis. |
| 23 | paralyzed Snorlax vs Zapdos | p1 unscored full paralysis; p2 support pivot | p2 Forretress; p1 full para | p2 miss | p2 used the statused Snorlax to reset support. |
| 24 | paralyzed Snorlax 47 vs Forretress, p2 side Spikes | p1 Gengar; p2 Rapid Spin | p2 Spikes; p1 Rest | both miss | I missed the recovery-before-block branch and p2 resetting p1-side Spikes. |
| 25 | sleeping Snorlax vs Forretress, both sides Spikes | p1 Gengar; p2 Rapid Spin | p1 Gengar; p2 Rapid Spin immune | both top | Once Snorlax was asleep, no pressure route existed; block Spin. |

## Error Classes

- Transfer success: I separated three cases that had been collapsed earlier:
  first layer before handoff, clean Rapid Spin when no block appears, and
  Gengar block when the active cannot convert a stronger route.
- Transfer miss: I undercalled direct Surf and Growth as pressure moves. I was
  still thinking mostly in Spin / spinblock / switch terms, while the expert
  line also used ordinary damage and setup as the hazard-control payoff.
- Secondary miss: after status and chip changed Snorlax's role, I missed Rest
  before returning to the spinblock sequence.

## Policy Update

Spin-vs-pressure handoff now needs a wider action list. The compensating route
after letting Spin resolve is not only Curse or phazing; it can be ordinary
damage, Growth, Baton Pass pressure, or Rest to preserve the converter. Before
switching to a spinblocker, ask whether the active can punish the spinner or
its pivot immediately.

## Next Study Target

Run a small regression for "pressure move taxonomy" in hazard turns: direct
damage, setup, Rest, phaze, sacrifice, and spinblock, with one scenario where
each is correct.
