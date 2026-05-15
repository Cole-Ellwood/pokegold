# Replay Turn-Pause 038 Sleep Clause Overcorrection - smogtours-gen2ou-934314 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934314`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh replay transfer after
`replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`.
The target was the sleep-clause absorber rule under pressure: when should a
Pokemon put to sleep be switched out and preserved, and when should it stay
because its active route is stronger than the preserve-default?

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and excluded replays exposed by an earlier broad grep snippet.
- Screening printed only replay ID, total turns, first induced-sleep turn,
  induced-sleep count, and file size.
- The turn 31 reveal was used only as past public context: Gengar's Hypnosis
  had just put Snorlax to sleep. Turns 32-38 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/sleeping_piece_later_job_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_037_low_support_pressure_smogtours-gen2ou-931699_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Forums, GSC OU Jynx analysis discussion:
  `https://www.smogon.com/forums/threads/gsc-ou-jynx.3699576/`
- Smogon Forums, GSC Sleep Trap:
  `https://www.smogon.com/forums/threads/gsc-sleep-trap.3622522/`
- Smogon Forums, Sleep Talk mechanics discussion:
  `https://www.smogon.com/forums/threads/new-mechanic-sleep-talk-doesnt-burn-sleep-turns.3544205/`
- Smogon Forums, GSC Introduction to Status:
  `https://www.smogon.com/forums/threads/gsc-introduction-to-status-sleep-paralysis-and-poison-gp-2-2.103998/`

Source note: the Jynx material supports the sleep-absorber idea: Sleep Talk
users can absorb Lovely Kiss to activate Sleep Clause while still threatening
Jynx. This replay tested the overcorrection. A sleeping Pokemon is not
automatically bench material if it is already the active win condition and the
opponent's current punishment is too slow.

## Score Summary

Scored decisions: 14 side decisions.

Top-match: 8 / 14.

Acceptable-match: 11 / 14.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 32 p2, where I overapplied the "switch the
slept Pokemon out to preserve Sleep Clause" rule. The actual line kept a +3
Snorlax in front of Gengar because Thunderbolt chip was not enough punishment
and wake into Rest could convert the route.

Main improvement:

- Re-solved after the turn 32 reveal and correctly accepted p2 staying asleep
  on turns 33-34 and the wake-into-Rest line on turns 36-37.

Main errors:

- Turn 32: overcorrected from the prior lesson and wanted a Gengar switch
  instead of staying with the boosted active route.
- Turn 35: over-raised conditional Explosion from p1 Gengar based on species
  pressure. This was not counted as a hidden-information error because it was
  stated as "if available," but it was still the wrong top branch against the
  actual set/line.
- Turn 38: over-switched to Raikou for stronger damage and undervalued
  preserving Gengar's safe stopgap role while Snorlax was still asleep.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 32 | p1 Gengar 100 vs +3 sleeping p2 Snorlax 91 | p1 Thunderbolt; p2 switch Gengar | p1 Thunderbolt; p2 stayed asleep | p1 top, p2 miss | The preserve-sleeper default failed because Snorlax was already the active win route. |
| 33 | Gengar vs +3 sleeping Snorlax 80 | p1 Thunderbolt; p2 stay | p1 Thunderbolt; p2 stayed asleep | both top | After the reveal, staying was coherent: chip was slow and wake/Rest was the payoff. |
| 34 | Gengar vs +3 sleeping Snorlax 71 | p1 Thunderbolt; p2 stay | p1 Thunderbolt; p2 stayed asleep | both top | Do not switch a boosted sleeper just because it is asleep if the active punish is weak. |
| 35 | Gengar vs +3 sleeping Snorlax 61 | p1 Explosion if available, otherwise Thunderbolt; p2 switch Gengar | p1 Thunderbolt; p2 stayed asleep | p1 acceptable, p2 miss | Private-set uncertainty matters; do not make unrevealed Explosion the hard top line. |
| 36 | Gengar vs +3 sleeping Snorlax 50 | p1 Explosion if available, otherwise Thunderbolt; p2 stay for wake/Rest | p1 Thunderbolt; p2 stayed asleep | p1 acceptable, p2 top | The wake/Rest branch was the real route, not passive sleep-turn burning. |
| 37 | Gengar vs +3 sleeping Snorlax 41 | p1 steady chip; p2 stay and Rest if wake | p1 Ice Punch; p2 woke and used Rest | p1 acceptable, p2 top | Staying paid off: the Hypnosis sleep became a full-health Resting +3 Snorlax. |
| 38 | Gengar vs +3 Rest-sleeping Snorlax 100 | p1 switch Raikou; p2 stay | p1 Thunderbolt crit; p2 stayed asleep | p1 miss, p2 top | After Rest, stronger damage was tempting, but exposing Raikou through Spikes was not forced. |

## Reusable Update

"Switch out the slept Pokemon" is a strong default when the sleeper's best
value is preserving Sleep Clause or a future support job. It is not a script.
Do not switch a sleeping Pokemon out if all of these are true:

- it is already the active win condition or route blocker;
- switching would erase boosts, board position, or the chance to wake into
  recovery;
- the opponent's active punishment is only slow chip or a conditional
  unrevealed cash-out;
- staying keeps the route live without risking an irreplaceable support piece.

In that case, the correct plan may be to stay asleep, accept chip, and play for
wake/Rest or wake/action. The question is not "asleep means bench" but "which
line preserves or improves the live route before the next reveal?"

## Next Rep

Run an unlabeled four-choice probe that mixes:

- slept support piece that should switch out;
- slept boosted win condition that should stay;
- slept RestTalk absorber that should Sleep Talk;
- slept self-KO target where the opponent must choose between steady damage,
  absorber switch, and cash-out.
