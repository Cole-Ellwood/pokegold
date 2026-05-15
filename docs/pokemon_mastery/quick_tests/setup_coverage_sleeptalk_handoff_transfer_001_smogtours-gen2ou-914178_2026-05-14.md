# Setup Coverage SleepTalk Handoff Transfer 001 - smogtours-gen2ou-914178 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-914178`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: transfer
`setup_coverage_sleeptalk_handoff_probe_001` to a fresh replay. The intended
score buckets were setup-before-pressure, revealed-coverage receiver,
SleepTalk-vs-phaze handoff, and paired handoff.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/quick_tests/setup_coverage_sleeptalk_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-914178`.

Contamination control:

- Local docs were searched for `914178`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from the GSC Trios source list before content
  screening.

## Score Summary

Focused branch-scored decisions: 22 from turns 1-11.

Top-match: 6 / 22.

Acceptable-match: 11 / 22.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Probe-category coverage:

- Setup-before-pressure: 0 / 1. I did not understand Shuckle's Defense Curl
  setup turn after Snorlax's Lovely Kiss missed.
- Revealed-coverage receiver: not materially tested before the stop.
- SleepTalk-vs-phaze handoff: not materially tested before the stop.
- Paired handoff: 1 / 4 clean. This was the repeated failure class.

Earliest focused error: turn 1 p2. I over-assigned Exeggutor's sleep job and
missed the paired handoff from Snorlax/Exeggutor to Umbreon/Forretress.

Repeated error: paired handoff. I found some first-order branches, but missed
the second-board answer: Forretress to Gengar, Gengar to Exeggutor, Shuckle to
Skarmory while Forretress went Exeggutor, and Skarmory into Umbreon/Snorlax
sleep lines.

## Focused Turn Notes

### Turn 1

Public state: p1 Snorlax vs p2 Exeggutor.

Frozen p1 answer: switch the sleep absorber, with Umbreon or another
nonessential absorber preferred if available.

Frozen p2 answer: Sleep Powder.

Actual choices: p1 switched Umbreon; p2 switched Forretress.

Grade: p1 top, p2 miss. Lesson: p2 did not complete the obvious sleep script;
the paired handoff was Exeggutor to Forretress as p1 left Snorlax.

### Turn 2

Public state: p1 Umbreon vs p2 Forretress.

Frozen p1 answer: hand off to the hazard-control or pressure piece.

Frozen p2 answer: Spikes.

Actual choices: p1 switched Starmie; p2 used Spikes.

Grade: both top. Lesson: this was the clean branch-handoff hit.

### Turn 3

Public state: p1 Starmie vs p2 Forretress with Spikes on p1's side.

Frozen p1 answer: Rapid Spin.

Frozen p2 answer: Toxic, with spinblock as a serious branch if a Ghost exists.

Actual choices: p2 switched Gengar; p1 used Rapid Spin into immunity.

Grade: p1 top, p2 miss. Lesson: the spin branch was found, but the exact
handoff to Gengar was not obeyed as the recommendation.

### Turn 4

Public state: p1 Starmie vs p2 Gengar.

Frozen p1 answer: switch a Gengar answer such as Umbreon.

Frozen p2 answer: Thunder or direct coverage into Starmie.

Actual choices: p2 switched Exeggutor; p1 used Psychic.

Grade: both miss. Lesson: Gengar's handoff to Exeggutor made Starmie's Psychic
a branch action, not a visible-matchup mistake.

### Turn 5

Public state: p1 Starmie vs p2 Exeggutor 82%, Stun Spore unrevealed.

Frozen p1 answer: switch a sleep/status absorber.

Frozen p2 answer: sleep or status.

Actual choices: p1 switched Skarmory; p2 used Stun Spore and missed.

Grade: both acceptable. Lesson: the absorber class transferred, exact identity
and status type did not.

### Turn 6

Public state: p1 Skarmory vs p2 Exeggutor.

Frozen p1 answer: Toxic into a likely receiver.

Frozen p2 answer: switch a special or support receiver.

Actual choices: p2 switched Forretress; p1 used Drill Peck.

Grade: p1 miss, p2 acceptable. Lesson: active Drill Peck still punished the
Forretress receiver enough; I overvalued generic Toxic.

### Turn 7

Public state: p1 Skarmory vs p2 Forretress.

Frozen p1 answer: switch Starmie or another support-control piece.

Frozen p2 answer: Toxic or Explosion.

Actual choices: p2 switched Snorlax; p1 used Drill Peck.

Grade: both miss. Lesson: another paired handoff: Forretress did not take the
support mirror; Snorlax entered and Drill Peck still hit the receiver.

### Turn 8

Public state: p1 Skarmory vs p2 Snorlax.

Frozen p1 answer: Toxic; I named Lovely Kiss as a serious Snorlax branch but
did not make the sleep absorber the recommendation.

Frozen p2 answer: coverage or Thunder-style pressure, with Lovely Kiss as a
serious alternative.

Actual choices: p1 switched Shuckle; p2 used Lovely Kiss and missed.

Grade: p1 miss, p2 acceptable. Lesson: Shuckle was the intended sleep/utility
handoff. The Snorlax set ambiguity card remains live.

### Turn 9

Public state: p1 Shuckle vs p2 Snorlax after Lovely Kiss missed.

Frozen p1 answer: Toxic or other direct progress.

Frozen p2 answer: try Lovely Kiss again.

Actual choices: p2 switched Forretress; p1 used Defense Curl.

Grade: both miss. Lesson: setup-before-pressure appeared, but I did not price
Shuckle's setup route or Snorlax's handoff out.

### Turn 10

Public state: p1 Shuckle at `def+1` vs p2 Forretress.

Frozen p1 answer: switch Starmie.

Frozen p2 answer: Toxic or Explosion.

Actual choices: p1 switched Skarmory; p2 switched Exeggutor.

Grade: p1 acceptable, p2 miss. Lesson: paired handoff again. My p1 switch-out
class was right, but the exact Skarmory/Exeggutor next board was missed.

### Turn 11

Public state: p1 Skarmory vs p2 Exeggutor.

Frozen p1 answer: Drill Peck.

Frozen p2 answer: switch Forretress.

Actual choices: p2 switched Forretress; p1 used Drill Peck.

Grade: both top. Lesson: after repeated handoffs, this exact receiver branch
finally transferred.

## Error Classes

- Paired handoff remains unstable: turns 1, 3, 4, 7, and 10.
- Setup-before-pressure did not transfer for Shuckle on turn 9.
- Sleep absorber/set ambiguity remains active around Lovely Kiss Snorlax.
- No mechanics, hidden-info, state, or severe-blunder errors were scored.

## Next Rep

Make a four-scenario paired-handoff micro-probe from this transfer:

1. Obvious sleep branch creates a double handoff.
2. Hazard control branch requires spinblock handoff.
3. Active pressure still punishes the receiver enough.
4. Setup route is correct only after naming the opponent's handoff out.
