# Replay Turn-Pause 033 Pressure Handoff After Spin - smogtours-gen2ou-934324 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934324`.

Players: ziloXX vs melancholy0. Uploaded 2026-05-09.

Mode: spectator public, semi-blind count-screened transfer.

Purpose: fresh transfer after
`poison_clock_spin_loop_unlabeled_probe_001`: test whether I can re-score a
live Starmie hazard-control turn without carrying the previous answer forward.
The run became a pressure-handoff test: sometimes letting Rapid Spin resolve
is correct if the next board gives Zapdos, Gengar, or Cloyster a better route.

## Contamination Control

- The replay ID was not referenced in local Pokemon mastery docs before this
  run.
- Candidate screening used current Pokemon Showdown replay search against
  strong/relevant GSC accounts and cached raw logs. The screen checked broad
  counts only: Starmie, Cloyster, Rapid Spin, Spikes, and Toxic.
- The screen did not reveal the target turn's actor, move order, outcome, or
  answer key.
- Start turns were selected by a script using only public state before that
  turn. The public prompts were then revealed one turn at a time with
  `tools/pokemon_mastery/replay_turn_pause.py`.
- After scoring through turn 51, I fetched the replay JSON to verify metadata;
  that exposed turns 52-66, so no score after turn 51 should be counted.

## Local Docs Checked

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/poison_clock_spin_loop_unlabeled_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/poison_clock_spin_loop_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_032_spin_vs_damage_boundary_transfer_smogtours-gen2ou-852072_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

## Web Sources Checked

- Smogon GSC OU Global Championship 2026 Round 1 Stage 2:
  `https://www.smogon.com/forums/threads/gsc-ou-global-championship-2026-round-1-stage-2.3781519/`
- Smogon GSC OU statistics thread:
  `https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

Source note: the statistics thread justified using current Smogtours replay
search as a source of live GSC material, while the Spikes and Cloyster sources
remain the policy anchor: Starmie, Cloyster, Toxic, Rapid Spin, Spikes, and
Explosion are route pieces, not standalone checkboxes.

## Score Summary

Target phases: turns 15-23, 36-41, and 46-51.

Decisions scored: 41 side-decisions. Turn 22 p1 was excluded because no chosen
move was logged during sleep.

Top-match: 24 / 41.

Acceptable-match: 28 / 41.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 2.

Hidden-information errors: 0.

Earliest meaningful error: turn 15 p1.

Largest errors:

- turns 15 and 48: missed Cloyster as the correct hazard reset into a
  sleeping or Resting Snorlax;
- turn 46: overprotected the layer with Gengar instead of allowing Rapid Spin
  into Zapdos pressure;
- turn 50: preserved a spent Cloyster instead of cashing it out with Explosion
  after Spikes had been reset.

## Context Before Target

- p2 Forretress set Spikes on p1's side on turn 3.
- p1 Cloyster had shown Toxic and later Spikes; p1 Gengar had slept Umbreon
  with Hypnosis, making Sleep Clause material relevant.
- p2 Starmie entered through Spikes on turn 13 and used Rapid Spin on turn 14
  as p1 switched Zapdos in.
- By turn 15, p2's side was clear, p1's side still had Spikes, p2 Starmie was
  facing p1 Zapdos, and p2 had a sleeping RestTalk Snorlax available.

## Turn Notes

### Turn 15

Frozen answers: p1 Thunder with Zapdos; p2 switch Starmie to sleeping Snorlax.

Actual: p2 switched Snorlax; p1 switched Cloyster.

Grade: p1 miss, p2 top. I priced the Starmie danger but missed the second
half: if Snorlax is the likely absorber, Cloyster can re-enter to reset the
hazard route.

### Turn 16

Frozen answers: p1 Spikes; p2 Sleep Talk.

Actual: p2 switched Moltres; p1 used Spikes.

Grade: p1 top, p2 miss. I got the layer but missed the pressure switch that
kept Cloyster from getting a free second support turn.

### Turn 17

Frozen answers: p1 switch Zapdos; p2 Fire Blast.

Actual: p1 switched Snorlax; p2 used Sunny Day.

Grade: both miss. Snorlax was the sturdier Fire sponge, and Moltres's route was
to create a sun clock before attacking.

### Turn 18

Frozen answers: p1 Double-Edge; p2 Fire Blast.

Actual: p2 Fire Blast; p1 Rest.

Grade: p1 miss, p2 top. I underpriced Rest as the route-preserving response to
sun-boosted Fire Blast.

### Turns 19-20

Frozen answers: p1 Sleep Talk; p2 Fire Blast.

Actual: p2 Fire Blast both turns; p1 Sleep Talk both turns, including a
Sleep Talk Rest reset on turn 20.

Grade: both top on both turns.

### Turn 21

Frozen answers: p1 Sleep Talk; p2 Fire Blast.

Actual: p2 renewed Sunny Day; p1 Sleep Talked Double-Edge.

Grade: p1 top, p2 miss. State error: I failed to track the sun clock and did
not price renewal before another Fire Blast.

### Turn 22

Frozen answer: p2 Fire Blast. P1 excluded because no chosen move was logged.

Actual: p2 Fire Blast.

Grade: p2 top.

### Turn 23

Frozen answers: p1 Rest if awake, otherwise Sleep Talk; p2 Fire Blast.

Actual: p2 Fire Blast missed; p1 woke and used Rest.

Grade: both top.

### Turn 36

Frozen answers: p1 Thunder; p2 switch Starmie to sleeping Snorlax.

Actual: p2 switched Snorlax; p1 Thunder missed.

Grade: both top. At 70%, Starmie was too valuable to spend into Zapdos Thunder
and a live Gengar branch.

### Turn 37

Frozen answers: p1 Thunder; p2 Sleep Talk.

Actual: p1 Thunder missed; p2 woke and used Curse.

Grade: p1 top, p2 miss. State error: I failed to name the wake-and-Curse branch
before recommending Sleep Talk.

### Turn 38

Frozen answers: p1 switch Machamp; p2 Double-Edge.

Actual: p1 switched Gengar; p2 Double-Edge failed into immunity.

Grade: p1 acceptable, p2 top. Machamp was a real Snorlax answer, but Gengar was
cleaner because p2 Snorlax's full public set could not hit it.

### Turn 39

Frozen answers: p1 Thunderbolt; p2 switch to a Gengar absorber.

Actual: p1 Thunderbolt; p2 Double-Edge failed into immunity.

Grade: p1 top, p2 miss.

### Turn 40

Frozen answers: p1 Thunderbolt; p2 switch.

Actual: p1 Ice Punch; p2 Rest.

Grade: p1 acceptable, p2 miss. Thunderbolt and Ice Punch were the same chip
route, but I underpriced Rest as Snorlax's way to keep the boosted sponge live.

### Turn 41

Frozen answers: p1 Thunderbolt; p2 Sleep Talk.

Actual: p1 Thunderbolt; p2 Sleep Talk called Double-Edge into Gengar.

Grade: both top.

### Turn 46

Frozen answers: p1 switch Gengar to block Rapid Spin; p2 use Psychic or direct
damage, not Rapid Spin.

Actual: p1 switched Zapdos; p2 used Rapid Spin and cleared p2's Spikes.

Grade: p1 acceptable, p2 miss. This is the key anti-overcorrection miss:
Gengar preserved the layer, but Zapdos gave the better next board by making
Starmie answer Thunder or switch to sleeping Snorlax.

### Turn 47

Frozen answers: p1 Thunder; p2 switch Starmie to sleeping Snorlax.

Actual: p2 switched Snorlax; p1 Thunder hit.

Grade: both top.

### Turn 48

Frozen answers: p1 Thunder; p2 Rest if awake, otherwise Sleep Talk.

Actual: p1 switched Cloyster; p2 woke and used Rest.

Grade: p1 miss, p2 top. This repeated the turn-15 error: when Snorlax's Rest is
the live branch, Cloyster can reset Spikes instead of Zapdos taking another
Thunder roll.

### Turn 49

Frozen answers: p1 Spikes; p2 switch Moltres.

Actual: p1 Spikes; p2 Sleep Talk called Double-Edge into Cloyster.

Grade: p1 top, p2 miss. Staying in kept direct pressure on Cloyster after the
layer was reset.

### Turn 50

Frozen answers: p1 switch Gengar; p2 Sleep Talk.

Actual: p2 switched Moltres; p1 used Explosion, KOing both Cloyster and
Moltres.

Grade: both miss. Cloyster had reset Spikes and was too low to preserve as a
real support piece; Explosion was the correct route trade into the predicted
Moltres pressure switch.

### Turn 51

Frozen answers: p1 Thunderbolt; p2 switch Starmie to sleeping Snorlax.

Actual: p2 switched Snorlax; p1 Thunderbolt.

Grade: both top. With Gengar active, Rapid Spin was not live and Starmie had to
preserve itself.

## Error Classes

1. I still default to the active Electric's damage too often when a sleeping or
   Resting Snorlax gives Cloyster a clean hazard reset.
2. I overcorrected toward spinblocking on turn 46; sometimes the better line is
   to let Spin resolve and punish the spinner with a stronger pressure piece.
3. Weather and sleep clocks must be explicitly carried in the branch bundle;
   the helper prompt does not display them reliably.
4. A low Cloyster that has already reset Spikes should be priced for Explosion
   before being preserved.

## Extracted Check

On a Starmie hazard-control turn:

1. If we block Rapid Spin, what board do we get immediately afterward?
2. If we allow Rapid Spin, does Zapdos, Gengar, Machamp, or another pressure
   piece force Starmie out or make it pay enough?
3. If Starmie switches to sleeping Snorlax, can Cloyster reset Spikes on the
   Rest or Sleep Talk turn?
4. After Cloyster resets Spikes, is it still a support piece or now Explosion
   material?
5. Did a wake, Rest, Sleep Talk result, or weather renewal change the timing?

## Next Rep

Construct a six-scenario pressure-handoff-after-spin probe: allow Spin into
Zapdos pressure, block Spin with Gengar when the layer is irreplaceable, reset
Spikes on a Resting Snorlax, and cash out a spent Cloyster with Explosion.
