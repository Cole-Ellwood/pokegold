# Positive Selection Transfer 001 - smogtours-gen2ou-760016 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-760016`

Raw log used:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-760016.log`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected measurable action:
Test the new goal's positive-selection scoring on a fresh replay. The target
was not "avoid severe blunders"; it was whether my ranked top-three answers
chose moves that converted pressure, punished named branches, and preserved or
spent the right route piece.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`

Web/current sources:

- Pokemon Showdown replay source:
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-760016`
- Raw replay log:
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-760016.log`

## Contamination Control

Local search found no prior `760016` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`, but future turns were not read.
Each turn was prompted with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen. After turn 15, turn 16 did not
exist, so the tail was inspected only to confirm the battle had ended.

## Score Summary

Turns scored: 1-15.

Scorable side decisions: 29. Turn 14 p2 was skipped because confusion prevented
the selected move from appearing in the log.

Top-match: 14 / 29.

Acceptable-match: 22 / 29.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 20 / 29.

Route-converting move chosen: 7 / 15 converter-decision subset.

Branch-punish chosen: 7 / 14 named-branch subset.

Earliest meaningful miss: turn 1 p1. I chose preservation or generic support
for Smeargle and missed the one-time Mirror Coat conversion into Zapdos.

Main bottleneck: positive selection is improving only unevenly. I often named
the opponent branch, but the chosen top line was still the safe cover line
rather than the move that converted the branch into progress.

## Turn Score Table

| Turn | Side | Frozen top | Actual | Top | Accept | Positive | Route convert | Branch punish | Errors / note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Switch/preserve Smeargle or support | Mirror Coat | 0 | 0 | 0 | 0 | n/a | Missed one-time Zapdos cash-out. |
| 1 | p2 | Thunder/Thunderbolt | Thunder | 1 | 1 | 1 | 1 | n/a | Actual was punished by hidden Mirror Coat, but the denial idea was live. |
| 2 | p1 | Spore | Spore | 1 | 1 | 1 | 1 | n/a | Correct support conversion. |
| 2 | p2 | Switch to sleep absorber | Vaporeon switch | 1 | 1 | 1 | 1 | 1 | Correct sleep-clause resource class. |
| 3 | p1 | Spikes | Spikes | 1 | 1 | 1 | 1 | n/a | Converted sleep window into hazards. |
| 3 | p2 | Save sleeping Vaporeon, go Snorlax/attacker | Snorlax switch | 1 | 1 | 1 | 1 | 1 | Correctly did not burn the slept mon by habit. |
| 4 | p1 | Destiny Bond | Destiny Bond | 1 | 1 | 1 | 1 | 1 | Correct final Smeargle job. |
| 4 | p2 | Non-attack/Curse into likely Destiny Bond | Double-Edge | 0 | 1 | 1 | 1 | 1 | Replay line got punished; disagreement is not counted severe. |
| 5 | p1 | Electric attack into Cloyster | Hidden Power into Steelix | 0 | 0 | 0 | 0 | 0 | Named the Electric-absorber branch but did not choose coverage into it. |
| 5 | p2 | Switch Electric absorber | Steelix switch | 1 | 1 | 1 | 1 | 1 | Correct branch class. |
| 6 | p1 | Switch to Steelix answer/preserve Zapdos | Gengar switch | 0 | 1 | 1 | 0 | n/a | Correct preserve-Zapdos class, missed exact Ghost owner. |
| 6 | p2 | Rock Slide/Explosion pressure | Roar | 0 | 1 | 0 | 0 | 0 | Underpriced phaze as the route move. |
| 7 | p1 | Earthquake | Explosion | 0 | 0 | 1 | 0 | n/a | Active but not the one-time free-entry conversion. |
| 7 | p2 | Earthquake | Earthquake | 1 | 1 | 1 | 1 | n/a | Correct active punish. |
| 8 | p1 | Surf | Growth | 0 | 1 | 0 | 0 | 0 | Named switch risk but chose damage over the switch-punishing setup. |
| 8 | p2 | Switch water answer | Cloyster switch | 1 | 1 | 1 | 1 | 1 | Correct answer class. |
| 9 | p1 | Gengar to cover Spin/Explosion | Surf | 0 | 1 | 0 | 0 | 0 | Over-covered worst branch; Surf punished Spikes with damage. |
| 9 | p2 | Attack expected Gengar | Spikes | 0 | 0 | 0 | 0 | 0 | Missed hazard setup as the route-progress move. |
| 10 | p1 | Gengar to cover Explosion/Spin | Protect | 0 | 1 | 1 | 0 | 1 | Covered Explosion class but missed the boost-preserving Protect if available. |
| 10 | p2 | Attack expected Gengar | Explosion | 0 | 1 | 1 | 0 | 1 | Replay Explosion was punished; branch-attack line was defensible. |
| 11 | p1 | Surf | Surf | 1 | 1 | 1 | 1 | n/a | Correct forced conversion into Steelix. |
| 11 | p2 | Switch Steelix out | Steelix stayed and fainted | 0 | 0 | 1 | 0 | n/a | Suggested preservation; actual lost Steelix before action. |
| 12 | p1 | Growth | Gengar switch | 0 | 0 | 0 | 0 | 0 | Missed using sleeping Vaporeon as a free handoff into Gengar pressure. |
| 12 | p2 | Switch hidden check if available | Stayed asleep | 0 | 1 | 0 | 0 | n/a | Conditional was incomplete; no revealed hidden check yet. |
| 13 | p1 | Explosion into sleeping Vaporeon | Ice Punch into Tyranitar | 0 | 0 | 0 | 0 | 0 | Hidden-info error: over-anchored Explosion on no unrevealed absorber. |
| 13 | p2 | Switch hidden Gengar answer if available | Tyranitar switch | 1 | 1 | 1 | 1 | 1 | Correct branch class. |
| 14 | p1 | Dynamic Punch if available; otherwise Vaporeon | Dynamic Punch | 1 | 1 | 1 | 1 | 1 | Correct after the move tier was explicit. |
| 14 | p2 | Pursuit/attack Gengar | Unlogged due confusion | - | - | - | - | - | Skipped. |
| 15 | p1 | Ice Punch | Ice Punch | 1 | 1 | 1 | 1 | n/a | Correct low-risk finish. |
| 15 | p2 | Stay/sack Tyranitar | Stayed and fainted | 1 | 1 | 1 | n/a | n/a | Correctly recognized no clean save through Spikes. |

## Lessons

1. Positive-selection misses are not the same as severe blunders. This run had
   0 severe blunders, but only 7 / 15 converter decisions chose the
   route-converting move.
2. The repeat failure was branch-action obedience. Turns 5, 8, 9, 12, and 13
   all involved naming or implying a branch, then choosing a weaker safe line.
3. Protect/scout is not passive when it preserves the route piece and makes the
   opponent spend Explosion into nothing. Turn 10 was the cleanest example.
4. Explosion into a sleeping target is not automatically conversion. On turn
   13, the unrevealed last Pokemon could be the route piece that punishes
   Explosion; using Explosion as the main recommendation needed a fallback or
   a stronger no-absorber read.

## Next Rep

Run a short positive-selection correction probe with four unlabeled positions:

- named Electric absorber where coverage beats visible STAB;
- forced switch where setup beats safe damage;
- low support piece where Protect/scout preserves the converter better than a
  switch;
- sleeping target with unrevealed last Pokemon where Explosion must be checked
  against absorber, Ghost, Rock, Protect, and route-value branches before it is
  selected.
