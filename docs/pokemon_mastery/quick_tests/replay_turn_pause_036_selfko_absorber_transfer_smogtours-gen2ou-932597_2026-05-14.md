# Replay Turn-Pause 036 Self-KO Absorber Transfer - smogtours-gen2ou-932597 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-932597`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`explosion_absorber_resource_probe_001_2026-05-14.md`. The target was to score
support-resource choice around Forretress, Donphan, Spikes, Rapid Spin, Zapdos,
Gengar, and possible self-KO trades.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and explicitly excluded contaminated candidates `932611`, `933818`, and
  `934420`.
- Screening printed only replay ID, broad move/species counts, and a start
  turn. It did not print future public-state summaries for this replay.
- After selecting `932597`, turns were revealed one at a time with
  `tools/pokemon_mastery/replay_turn_pause.py`.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/explosion_absorber_resource_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_035_unlabeled_hazard_cashout_transfer_smogtours-gen2ou-933816_2026-05-14.md`

Web sources checked:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

Source note: the source lesson under test was that Explosion, Spikes, Toxic,
Rapid Spin, and spinblocking are route tools. The replay became a poisoned
spinner loop: Toxic Donphan, hand off to Zapdos, reset Spikes on RestTalk
Snorlax, then eventually use a Ghost to make the Spin block real.

## Score Summary

Scored decisions: 23 side decisions.

Top-match: 17 / 23.

Acceptable-match: 19 / 23.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 13 p1, where I still overvalued immediate
Explosion into Donphan compared with preserving Forretress and handing off to
Zapdos pressure.

Main improvements:

- Correctly used Toxic before handoff on turn 6.
- Correctly allowed Rapid Spin into Zapdos pressure on turns 7, 13, and 17.
- Correctly reset Spikes on sleeping or Resting Snorlax on turns 12, 16, and
  21.
- Correctly understood that poisoned Donphan was being put on a clock instead
  of needing immediate removal.

Remaining errors:

- Turn 13: Explosion into the poisoned spinner was overcalled as the first
  branch; preserving Forretress was better while Donphan was already poisoned.
- Turn 22: once a Ghost was conditionally available, I should have ranked
  "Ghost if available" above another Zapdos handoff.
- Turn 24: I overcalled Gengar Explosion into Raikou instead of preserving
  Gengar and using Snorlax as the Electric absorber.
- Turn 26: I overcalled a spinblock into Forretress, while direct Thunder
  punished Forretress and forced it into a support-only Spikes turn.
- Turn 27: I missed the defending side's preservation branch: low Forretress
  switched to sleeping Snorlax rather than forcing Rapid Spin or Explosion.

## Target Turn Notes

### Turn 6

Public state:

```text
p1 Forretress 100% vs p2 Donphan 100%.
p2 side has Spikes; p1 side is clear.
p1 Forretress has revealed Spikes. p2 Donphan has revealed no moves.
```

My answer: p1 Toxic if available; p2 Rapid Spin.

Actual:

```text
Donphan used Rapid Spin and cleared Spikes.
Forretress used Toxic on Donphan.
```

Grade: both top.

Lesson: when the spinner is active and we cannot retain the layer immediately,
status the spinner before handing off.

### Turn 7

Public state:

```text
p1 Forretress 100% vs poisoned p2 Donphan 100%.
No hazards are up. Donphan has Rapid Spin revealed.
```

My answer: p1 switch Zapdos to punish Earthquake and begin the pressure
handoff; p2 Earthquake.

Actual:

```text
p1 switched Zapdos.
Donphan used Earthquake into immunity.
```

Grade: both top.

Lesson: the payoff from Toxic is the handoff; do not stay in the support mirror
after the support job is done.

### Turn 12

Public state:

```text
p1 Forretress 100% vs sleeping p2 Snorlax 100%.
No hazards are up. Donphan is poisoned in back.
Snorlax has Rest and Sleep Talk revealed.
```

My answer: p1 Spikes; p2 switch Donphan or Sleep Talk.

Actual:

```text
p2 switched Donphan.
Forretress used Spikes.
```

Grade: both top.

Lesson: RestTalk Snorlax can still act, but it can also be the low-pressure
turn that lets the Spiker reset the route.

### Turn 13

Public state:

```text
p1 Forretress 100% vs poisoned p2 Donphan 93%.
p2 side has Spikes. Donphan has Earthquake and Rapid Spin revealed.
```

My answer: Explosion if Forretress has it, with Zapdos handoff as the
preservation alternative; p2 Rapid Spin.

Actual:

```text
p1 switched Zapdos.
Donphan used Rapid Spin and cleared Spikes.
```

Grade: p1 acceptable but not top; p2 top.

Lesson: immediate Explosion into the spinner is not mandatory once the spinner
is already poisoned and Forretress still has a live reset job.

### Turn 15

Public state:

```text
p1 Zapdos 100% vs sleeping p2 Snorlax 78%.
No hazards are up. Donphan is poisoned in back.
```

My answer: p1 switch Forretress to reset Spikes; p2 Sleep Talk or wake action.

Actual:

```text
p1 switched Forretress.
Snorlax Sleep Talk called Earthquake.
```

Grade: both top.

Lesson: the reset is correct, but Sleep Talk Earthquake is the worst branch
that makes Forretress HP matter for later loops.

### Turn 16

Public state:

```text
p1 Forretress 85% vs sleeping p2 Snorlax 84%.
No hazards are up. Donphan is poisoned in back.
```

My answer: p1 Spikes; p2 switch Donphan.

Actual:

```text
p2 switched Donphan.
Forretress used Spikes.
```

Grade: both top.

Lesson: the hazard reset is still correct when it forces the poisoned spinner
to keep spending turns and HP.

### Turn 17

Public state:

```text
p1 Forretress 91% vs poisoned p2 Donphan 81%.
p2 side has Spikes. Donphan has Earthquake and Rapid Spin revealed.
```

My answer: preserve Forretress and switch Zapdos; p2 Rapid Spin.

Actual:

```text
p1 switched Zapdos.
Donphan used Rapid Spin and cleared Spikes.
```

Grade: both top.

Lesson: this time the preservation branch transferred cleanly. Donphan is
losing the long loop to poison and pressure, so Forretress should not cash out.

### Turn 22

Public state:

```text
p1 Forretress 100% vs poisoned p2 Donphan 68%.
p2 side has Spikes. p1 has not yet revealed Gengar.
```

My answer: switch Zapdos, with Ghost if available not ranked strongly enough;
p2 Rapid Spin.

Actual:

```text
p1 switched Gengar.
Donphan used Rapid Spin into immunity.
```

Grade: p1 acceptable but not top; p2 top.

Lesson: in spectator-public mode, "Ghost if available" must be the first
conditional once the hazard route is valuable and the opponent's Spin is
obvious. Not knowing the slot exists is not a reason to omit the conditional.

### Turn 23

Public state:

```text
p1 Gengar 100% vs poisoned p2 Donphan 62%.
p2 side has Spikes. Donphan's Spin has just failed.
```

My answer: p1 Ice Punch or strongest Donphan punish.

Actual:

```text
Gengar used Ice Punch, crit, and KOed Donphan.
```

Grade: p1 top; p2 excluded because the chosen move did not resolve after the
KO.

Lesson: after the real spinblock enters, convert immediately before the spinner
can switch, heal, or leave the loop.

### Turn 24

Public state:

```text
p1 Gengar 100% vs p2 Raikou 83%.
p2 side has Spikes. Donphan is fainted. Raikou has Thunderbolt revealed.
```

My answer: Explosion if Gengar has it, otherwise Snorlax; p2 Thunderbolt.

Actual:

```text
p1 switched Snorlax.
Raikou used Thunderbolt.
```

Grade: p1 miss; p2 top.

Lesson: do not cash out the Ghost just because it can hit a major target.
Donphan is already gone, Spikes are retained, and Snorlax is the natural
Electric absorber.

### Turn 26

Public state:

```text
p1 Zapdos 68% vs p2 Forretress 93%.
p2 side has Spikes. p1 side is clear. Donphan is fainted.
```

My answer: switch Gengar to cover Rapid Spin or Explosion; p2 Rapid Spin or
Explosion.

Actual:

```text
Zapdos used Thunder, dropping Forretress to 25%.
Forretress used Spikes on p1's side.
```

Grade: both miss.

Lesson: after Donphan is gone, the active Forretress is not only a spinner or
exploder. Direct Thunder can punish it before it gets more support, and
Forretress may choose Spikes instead of either self-KO or removal.

### Turn 27

Public state:

```text
p1 Zapdos 74% vs p2 Forretress 25%.
Both sides have Spikes. Donphan is fainted.
```

My answer: p1 Thunder; p2 Rapid Spin or Explosion before fainting.

Actual:

```text
p2 switched sleeping Snorlax into Spikes.
Zapdos used Thunder into Snorlax.
```

Grade: p1 top; p2 miss.

Lesson: the defender can preserve a low support Pokemon by using a sleeping
anchor as the absorber. This is the mirror image of the replay 035 miss:
absorber choice depends on remaining route jobs, not on whether the absorber is
awake or famous.

## Error Classes

- Overcash-out tendency remains: I still wanted Explosion from Forretress or
  Gengar before fully pricing whether the route was already improving.
- Public conditional omission: I ranked Zapdos above "Ghost if available" on a
  turn where blocking Spin was the route.
- Support-action taxonomy miss: low Forretress could choose Spikes or
  preservation, not only Rapid Spin or Explosion.
- Wake/sleep absorber mirror improved in one direction but still needs more
  live transfer: a sleeping anchor can either absorb a trade or preserve a
  low support Pokemon depending on future jobs.

## Next Rep

Run a short fresh replay segment where a low support Pokemon faces direct
pressure after hazards are up. Score the three-way choice among support,
preservation switch, and self-KO trade before reveal.
