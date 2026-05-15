# Replay Turn-Pause 037 Low Support Pressure - smogtours-gen2ou-931699 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-931699`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_036_selfko_absorber_transfer_smogtours-gen2ou-932597_2026-05-14.md`.
The target was to score low support Pokemon under pressure: direct chip,
self-KO cash-out, preserving a support piece, and using an already-sleeping
Pokemon as sleep-clause and matchup material.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and explicitly excluded contaminated candidates `932611`, `933818`, and
  `934420`.
- Screening printed only replay ID, broad species or move counts, and a start
  turn. It did not print future public-state summaries for this replay.
- The later restart at turn 51 was selected by turn number only, after the
  first segment was scored. No future turn states were printed before answers.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/explosion_absorber_resource_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_036_selfko_absorber_transfer_smogtours-gen2ou-932597_2026-05-14.md`

Web sources checked:

- Smogon, GSC Forum:
  `https://www.smogon.com/forums/forums/gsc/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Pokemon Showdown, Ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: the Spikes and Explosion sources support treating support and
self-KO moves as route tools, not checkboxes. The Jynx analysis gives the sleep
absorber pattern directly: Sleep Talk users can absorb sleep to activate Sleep
Clause while still threatening the sleeper. In this replay, that translated
into preserving or reusing sleeping Raikou and sleeping Kingdra according to
their remaining board jobs.

## Score Summary

Scored decisions: 24 side decisions.

Top-match: 12 / 24.

Acceptable-match: 14 / 24.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 14 p2, where I overcalled Cloyster Explosion
from 31% into Tyranitar. The actual Surf damaged Tyranitar before Cloyster
fainted, showing that a low support Pokemon does not always cash out
immediately.

Main improvement: turns 51-53 transferred the sleep-clause absorber rule. I
correctly accepted Gengar Explosion into sleeping Kingdra, then correctly
switched sleeping Raikou into Zapdos Thunder and used Sleep Talk while p2
switched Snorlax.

Main misses:

- Missed the hidden Water or physical-resist conditional on turn 15; under no
  Team Preview, the right phrasing was "Forretress, or Water/physical resist if
  available."
- Missed Kingdra Rest on turn 16, treating attack as the default instead of
  preserving the RestTalk board job.
- Missed sleeping Raikou as the better Gengar/Zapdos absorber on turns 18 and
  21 before correcting it on turn 52.
- Overcalled self-KO from Cloyster on turn 14, but correctly called Gengar's
  later Explosion on turn 51 once its target and lost role were clear.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 14 | p1 Tyranitar 100 vs p2 Cloyster 31; Spikes both sides | p1 Rock Slide; p2 Explosion | p2 Surf, p1 Rock Slide KO | p1 top, p2 miss | Low Cloyster still had useful direct chip; Explosion was not forced. |
| 15 | p1 Tyranitar 51 vs p2 Tyranitar 93 | p1 Forretress; p2 attack pressure | p1 Kingdra; p2 Dynamic Punch | both miss | Name unrevealed Water/physical-resist if available instead of locking onto the revealed support piece. |
| 16 | p1 Kingdra 65 vs p2 Tyranitar 100 | p1 Surf; p2 attack | p1 Rest; p2 Rock Slide | p1 miss, p2 top | RestTalk preservation can outrank immediate damage. |
| 17 | sleeping p1 Kingdra 77 vs p2 Tyranitar 100 | p1 Sleep Talk; p2 pressure | p2 Zapdos, p1 Sleep Talk Ice Beam | p1 top, p2 miss | Sleep Talk is real action, but the opponent can still preserve into a new route. |
| 18 | sleeping p1 Kingdra 83 vs p2 Zapdos 67 | p1 Sleep Talk; p2 Thunder | p1 Raikou, p2 Thunder | p1 miss, p2 top | This was the first missed sleeping-Raikou absorber branch. |
| 19 | sleeping p1 Raikou 71 vs p2 Zapdos 73 | p1 Sleep Talk; p2 Thunder or Snorlax | p2 Snorlax, p1 Sleep Talk HP crit | p1 top, p2 acceptable | Sleep Talk kept the sleeping absorber useful without clearing Sleep Clause. |
| 20 | sleeping p1 Raikou 77 vs p2 Snorlax 70 | p1 Skarmory; p2 Curse/Double-Edge | p1 Skarmory; p2 Gengar | p1 top, p2 miss | Correctly left the sleeping Electric when Snorlax became the live route. |
| 21 | p1 Skarmory 100 vs p2 Gengar 93 | p1 Tyranitar; p2 Hypnosis/Thunderbolt | p1 Raikou, p2 Thunderbolt | p1 miss, p2 top | Because Raikou was already asleep, it was the cleaner sleep-clause and Electric absorber. |
| 22 | sleeping p1 Raikou 60 vs p2 Gengar 100 | p1 Sleep Talk; p2 Explosion/Thunderbolt | both switched Tyranitar | both miss | Re-score after the absorber is in; staying is not automatic. |
| 51 | sleeping p1 Kingdra 79 vs p2 Gengar 13 | p1 stay/Sleep Talk; p2 Explosion | Gengar Explosion into Kingdra | both top | Spending the sleeper was correct because it preserved higher-value pieces and opened the Zapdos endgame. |
| 52 | p1 Tyranitar 39 vs p2 Zapdos 100 | p1 Raikou; p2 Snorlax, Thunder acceptable | p1 Raikou, p2 Thunder | p1 top, p2 acceptable | This is the clean sleep-clause transfer: switch the already-sleeping mon into pressure instead of waking it. |
| 53 | sleeping p1 Raikou 72 vs p2 Zapdos 100 | p1 Sleep Talk; p2 Snorlax | p2 Snorlax, p1 Sleep Talk HP | both top | After preserving the sleeper, use its board job; do not treat the switch as the whole plan. |

## Reusable Update

When a Pokemon is put to sleep by the opponent, the default GSC question is not
"how do I wake it quickly?" It is "does this sleeping Pokemon still need to
block future sleep or absorb a matchup later?" Switching it out immediately is
common because waking clears Sleep Clause and can let the opponent sleep a more
valuable piece. Staying or burning turns is correct only when Sleep Talk, Rest
timing, a sacrifice, phazing, support, or direct pressure improves the route
more than preserving the sleep-clause shield.

For self-KO pressure, separate low HP from spent role. Cloyster at 31% still
used Surf before fainting; Gengar at 13% correctly Exploded once the sleeping
target was the piece p1 could afford to lose and the post-trade Zapdos route
was clear.

## Next Rep

Run a compact sleep-clause absorber probe with unlabeled choices:
switch the sleeper out, stay with Sleep Talk, attack before switching, or
sacrifice the sleeper. Score whether the answer preserves Sleep Clause for a
future sleep user or spends the sleeping Pokemon because its board job is more
valuable now.
