# Replay Turn-Pause 035 Unlabeled Hazard Cash-Out Transfer - smogtours-gen2ou-933816 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-933816`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: run a fresh, unlabeled Starmie/Cloyster
hazard-control transfer after
`quick_tests/pressure_handoff_after_spin_probe_001_2026-05-14.md`. The target
was to choose moves without being pre-labeled as spinblock, pressure handoff,
Spikes reset, or Explosion cash-out.

Contamination control:

- The replay ID was not referenced in local mastery docs before this run.
- Candidate selection used broad cached-log counts: Starmie, Cloyster, Rapid
  Spin, Spikes, Ghosts, Zapdos, Toxic, Recover, and Explosion.
- `smogtours-gen2ou-932611` and `smogtours-gen2ou-933818` were discarded
  because screening printed future public-state summaries before answers were
  frozen.
- For this counted run, only the start turn, broad counts, summary, and current
  prompt were exposed before turn 13. Turns 13-20 were revealed one at a time
  with `tools/pokemon_mastery/replay_turn_pause.py`.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_033_pressure_handoff_after_spin_smogtours-gen2ou-934324_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/pressure_handoff_after_spin_probe_001_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Discussion Thread:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`
- Smogon Forums, GSC OU statistics resource:
  `https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/`

Source note: Smogon's Spikes article and Cloyster analysis both frame Cloyster,
Starmie, Rapid Spin, Toxic, Surf, and Explosion as one route subgame. The
current replay tested a hard version: preserving a sleeping anchor is worse if
the switch exposes the only hazard-control piece to a likely Explosion.

## Score Summary

Scored decisions: 16 side decisions.

Top-match: 6 / 16.

Acceptable-match: 9 / 16.

Severe blunders: 1.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 13 p1.

Primary error class: wrong resource preservation. I tried to preserve a
sleeping Snorlax from Cloyster's Explosion, but the better route was to let the
sleeping, low-agency piece absorb the trade and preserve Starmie/Forretress for
the hazard-control and anti-Electric sequence.

Secondary errors:

- Turn 14: overvalued Rapid Spin from Forretress and missed the immediate
  Explosion cash-out into Zapdos.
- Turn 15: failed to state "Ground if available" as the natural public
  conditional into Raikou.
- Turn 18: after Starmie entered Machamp, overcalled direct attack and missed
  the clean Rapid Spin window before Machamp became too threatening.
- Turns 18-19: underpriced Machamp's setup and revealed Hidden Power coverage
  against Starmie.

## Turn 13

Public state:

```text
p1 Snorlax 100% asleep vs p2 Cloyster 100%.
p1 side has Spikes; p2 side is clear.
p1 has revealed Starmie at 87% with Thunder Wave.
p2 Cloyster has revealed Spikes. p2 Snorlax is fainted; Raikou is paralyzed;
p2 Machamp is unrevealed except Cross Chop.
```

My p1 answer: switch Starmie if it has Rapid Spin, preserving sleeping Snorlax
and threatening removal.

My p2 answer: Explosion, because Cloyster's Spikes job is complete and both
sleeping Snorlax and the likely spinner are valuable targets.

Actual choices:

```text
Cloyster used Explosion.
Snorlax and Cloyster fainted.
p1 sent Forretress; p2 sent Zapdos.
```

Grade: p1 severe miss; p2 top.

Reusable lesson: do not preserve the sleeper by switching the spinner or
hazard-control piece into an obvious Cloyster Explosion. Sometimes the sleeping
anchor is the correct absorber because it has less future agency than the
pieces that can still remove hazards or answer the next attacker.

## Turn 14

Public state:

```text
p1 Forretress 94% vs p2 Zapdos 100%.
p1 side still has Spikes; p2 side is clear.
p1 Forretress has revealed no moves. Zapdos has revealed no moves.
```

My p1 answer: Rapid Spin if available, because this may be the last clean
hazard-removal chance before Zapdos pressures Forretress.

My p2 answer: Electric attack to pressure Forretress immediately.

Actual choices:

```text
Zapdos used Thunderbolt.
Forretress used Explosion.
Forretress and Zapdos fainted.
p1 sent Starmie; p2 sent Raikou.
```

Grade: p1 miss; p2 acceptable.

Reusable lesson: a support Pokemon at high HP can still be cash-out material if
its spin/reset job is less important than removing the current route threat.
Do not ask only "can it Spin?" Ask whether spinning leaves Zapdos with the
better board.

## Turn 15

Public state:

```text
p1 Starmie 81% vs p2 paralyzed Raikou 100%.
p1 side has Spikes; p2 side is clear.
p1 Starmie has revealed Thunder Wave. Raikou has revealed Thunder.
```

My p1 answer: Rapid Spin if Starmie has it; otherwise switch to an Electric
immune if one exists.

My p2 answer: Thunder.

Actual choices:

```text
p1 switched Marowak into Spikes.
Raikou used Thunder; Marowak was immune.
```

Grade: p1 miss because the conditional was not the top recommendation; p2 top.

Reusable lesson: in spectator-public mode, own hidden-team conditionals must be
ranked when the public route screams for them. "Ground if available" was the
correct first branch before forcing Starmie to Spin into Raikou.

## Turn 16

Public state:

```text
p1 Marowak 88% vs p2 paralyzed Raikou 100%.
p1 side has Spikes; p2 side is clear.
```

My p1 answer: Earthquake.

My p2 answer: switch Machamp as the visible Ground punishment route.

Actual choices:

```text
p2 switched Machamp.
Marowak used Earthquake, leaving Machamp at 48% after Leftovers.
```

Grade: both top.

Reusable lesson: once the Electric is boxed by a Ground, the route is not
"attack forever"; the opponent's visible physical punish must be priced.

## Turn 17

Public state:

```text
p1 Marowak 88% vs p2 Machamp 48%.
p1 side has Spikes. Machamp has revealed Cross Chop.
```

My p1 answer: switch Starmie to preserve Marowak from Cross Chop and keep the
Raikou endgame covered.

My p2 answer: Cross Chop.

Actual choices:

```text
p1 switched Starmie into Spikes.
Machamp used Cross Chop and missed.
```

Grade: both top.

Reusable lesson: preserving Marowak was right after it forced Raikou out; the
Starmie entry also reopened the hazard-removal route.

## Turn 18

Public state:

```text
p1 Starmie 75% vs p2 Machamp 54%.
p1 side has Spikes. Starmie has revealed Thunder Wave only.
Machamp has revealed Cross Chop.
```

My p1 answer: attack with Psychic if available, otherwise use the best direct
damage or status.

My p2 answer: switch Raikou or attack if Machamp must trade damage.

Actual choices:

```text
Starmie used Rapid Spin, clearing p1's Spikes.
Machamp used Curse.
```

Grade: both miss.

Reusable lesson: resisted or low-pressure contact windows are often the actual
Rapid Spin window. I kept tunnel vision on removing Machamp immediately and
missed that Starmie could clear the entry tax before the Machamp route matured.

## Turn 19

Public state:

```text
p1 Starmie 81% vs p2 Machamp 56%, atk+1 def+1 spe-1.
No hazards are up. Starmie has Rapid Spin and Thunder Wave revealed.
```

My p1 answer: attack; Psychic if available, otherwise Surf.

My p2 answer: attack with Cross Chop or strongest coverage.

Actual choices:

```text
Starmie used Surf, leaving Machamp at 30% after Leftovers.
Machamp used Hidden Power, super effectively, leaving Starmie at 19%.
```

Grade: p1 acceptable; p2 miss.

Reusable lesson: after a setup move, "coverage if available" must be named
explicitly. Hidden Power was not known, but the worst branch was a
Starmie-targeting coverage move, not just Cross Chop.

## Turn 20

Public state:

```text
p1 Starmie 19% vs p2 Machamp 30%, atk+1 def+1 spe-1.
No hazards are up. Machamp has revealed Cross Chop, Curse, and Hidden Power.
```

My p1 answer: Surf to remove Machamp before it attacks, assuming the damage
range is sufficient.

My p2 answer: preserve Machamp only if a switch covers Surf; otherwise attack
with Hidden Power.

Actual choices:

```text
Starmie used Recover.
Machamp used Hidden Power and KOed Starmie.
p1 sent Marowak.
```

Grade: p1 acceptable disagreement; p2 miss.

Reusable lesson: this is a replay-oracle caution. The actual Recover line lost
Starmie to revealed coverage, so it should not be treated as automatically
better than attacking. The useful part for training is that after Hidden Power
is revealed, the next answer must check damage range before assuming Recover is
safe.

## Error Classes

- Severe resource-preservation miss: switched the likely spinner into the
  obvious Explosion branch to save a sleeping Snorlax.
- Support cash-out miss: treated Forretress primarily as a spinner when its
  actual route was Explosion into Zapdos.
- Public conditional miss: did not make "Ground if available" the top answer
  against Raikou before forcing Starmie to stay.
- Rapid Spin window miss: attacked Machamp immediately instead of using the
  low-pressure turn to clear Spikes.
- Coverage branch miss: did not name Hidden Power or equivalent Starmie-target
  coverage before the reveal.

## Next Rep

Build a small regression probe from this miss: choose which piece should absorb
Explosion when a sleeping anchor, spinner, and hazard setter all have different
future jobs.
