# Positive Selection Transfer 004 - smogtours-gen2ou-690716 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-690716`

Context source:
Smogon, `GSC OU Winter Seasonal #5: Round 13`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-5-round-13.3720601/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Fresh transfer after `positive_selection_transfer_003`, forcing the
three-way branch check: active pressure, coverage/status/phaze/setup into the
expected branch, or handoff to the next-board owner.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/positive_selection_transfer_003_smogtours-gen2ou-828683_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #5 Round 13 thread above.
- Pokemon Showdown replay source above.
- Raw log: `https://replay.pokemonshowdown.com/smogtours-gen2ou-690716.log`

## Contamination Control

Local search found no prior `690716` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not inspected;
each prompt was generated with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen.

Stopped after turn 15 for a 30-side-decision packet. This packet is a
regression, not progress.

## Score Summary

Turns scored: 1-15.

Scorable side decisions: 30.

Top-match: 12 / 30.

Acceptable-match: 19 / 30.

Severe blunders: 1.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 16 / 30.

Route-converting move chosen: 10 / 22 target converter decisions.

Branch-punish chosen: 8 / 18 named-branch decisions.

Earliest meaningful error: turn 2 p1. I kept Cloyster active for Toxic instead
of preserving it and moving to the Normal-immune owner, while the replay used
Gengar to blank Double-Edge.

Severe error: turn 12 p1. I chose active Thunder into a low Gengar, but
Explosion was the worst plausible branch and Steelix was the route-preserving
owner. That line likely loses Zapdos without compensation.

Main bottleneck:
The three-way check is still unstable. I alternated between under-handoff
(turns 4, 7, 10), over-branch coverage (turn 11), and overactive pressure
(turn 12). The next fix should focus on one gate: when a low support Pokemon
can self-KO, answer the self-KO branch before active pressure or prediction.

## Focused Turn Table

| Turn | Side | Frozen top | Actual | Top | Accept | Positive | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Spikes | Spikes | 1 | 1 | 1 | Correct hazard route. |
| 1 | p2 | Double-Edge | Double-Edge | 1 | 1 | 1 | Correct active pressure. |
| 2 | p1 | Toxic | Gengar switch | 0 | 0 | 0 | Missed preserve-Cloyster plus Normal-immune owner. |
| 2 | p2 | Double-Edge | Double-Edge | 1 | 1 | 1 | Reasonable active pressure into unrevealed Ghost. |
| 3 | p1 | Hypnosis/support | Thief | 0 | 1 | 1 | Found disruption class, missed Thief's item route. |
| 3 | p2 | Earthquake | Earthquake | 1 | 1 | 1 | Correct coverage into Gengar. |
| 4 | p1 | Stay active with Gengar | Zapdos switch | 0 | 0 | 0 | Missed next-board handoff. |
| 4 | p2 | Earthquake | Gengar switch | 0 | 0 | 0 | Missed counter-handoff into expected Zapdos. |
| 5 | p1 | Thunder | Thunder | 1 | 1 | 1 | Correct active pressure. |
| 5 | p2 | Explosion/read with Gengar | Snorlax switch | 0 | 1 | 0 | Over-read active job; actual handoff absorbed Thunder. |
| 6 | p1 | Thunder | Snorlax switch | 0 | 0 | 0 | Missed p2 Rest window and matching owner. |
| 6 | p2 | Double-Edge | Rest | 0 | 1 | 0 | Rest was named but not chosen. |
| 7 | p1 | Curse | Zapdos switch | 0 | 0 | 0 | Missed counter-handoff into likely Golem/answer. |
| 7 | p2 | Switch sleeping Snorlax out | Golem switch | 0 | 1 | 1 | Correct class, wrong owner. |
| 8 | p1 | Hidden Power / coverage | Cloyster switch | 0 | 1 | 1 | Correct Golem-answer idea, wrong action. |
| 8 | p2 | Rock Slide | Snorlax switch | 0 | 0 | 0 | Overactive into Zapdos; sleeping Lax was the resource. |
| 9 | p1 | Surf | Surf | 1 | 1 | 1 | Correct non-Explosion pressure. |
| 9 | p2 | Switch sleeper out | Sleep Talk | 0 | 0 | 0 | Did not import Sleep Talk before reveal, but missed route. |
| 10 | p1 | Surf | Zapdos switch | 0 | 0 | 0 | Missed p2 Gengar handoff and our Zapdos owner. |
| 10 | p2 | Gengar switch | Gengar switch | 1 | 1 | 1 | Correct Explosion/Surf absorber. |
| 11 | p1 | Hidden Power coverage | Thunder | 0 | 0 | 0 | Over-covered Golem; active Thunder converted on Gengar. |
| 11 | p2 | Golem switch | Thief | 0 | 0 | 0 | Missed low-Gengar support action. |
| 12 | p1 | Thunder | Steelix switch | 0 | 0 | 0 | Severe: failed to cover obvious Explosion branch. |
| 12 | p2 | Explosion | Explosion | 1 | 1 | 1 | Correct low-Gengar cash-out. |
| 13 | p1 | Zapdos switch | Zapdos switch | 1 | 1 | 1 | Correct Cloyster answer. |
| 13 | p2 | Spikes | Spikes | 1 | 1 | 1 | Correct support on forced switch. |
| 14 | p1 | Thunder | Hidden Power | 0 | 1 | 0 | Named Golem branch but did not choose coverage. |
| 14 | p2 | Golem switch | Golem switch | 1 | 1 | 1 | Correct Electric immunity. |
| 15 | p1 | Hidden Power | Hidden Power | 1 | 1 | 1 | Correct coverage after reveal. |
| 15 | p2 | Cloyster switch | Snorlax switch | 0 | 1 | 1 | Correct preserve-Golem switch class, wrong owner. |

## Lessons

1. Severe-blunder control failed in this packet. Turn 12 is the kind of miss
   the current goal treats as a pass/fail gate.
2. The next-board check is not enough by itself. It must be preceded by "what
   one-turn resource can the current active spend right now?"
3. Rest does not equal Sleep Talk, but once Sleep Talk is revealed, staying in
   with the sleeper must be repriced immediately.
4. Active pressure can be correct even when a branch is available. Turn 11
   punished my over-coverage: Thunder into the low Gengar was better than
   covering Golem before Gengar committed to switching.
5. Coverage into the branch can be correct after the branch is strongly priced.
   Turn 14 punished the opposite error: Hidden Power into Golem was better
   than Thunder into Cloyster.

## Next Rep

Do not run another broad replay immediately. First do a tiny correction probe
for the severe gate:

- low Gengar / Cloyster / Forretress can self-KO into a valuable active;
- choose between active KO, defensive owner, and coverage into switch;
- require the answer to name whether the self-KO user is faster, whether the
  active survives, and which owner preserves the route.
