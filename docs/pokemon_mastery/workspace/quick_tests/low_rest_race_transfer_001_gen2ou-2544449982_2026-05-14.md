# Low Rest Race Transfer 001 - gen2ou-2544449982 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2544449982-h3w37s4ld0qjafggb4uanfpx1ajhioipw`

Context source:
Smogon, `GSC OU Winter Seasonal #8: Round 3 (Loser's Bracket)`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-3-losers-bracket.3777885/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Fresh transfer after `low_rest_race_cashout_probe_001`, with the low-HP
Rest-race gate active. The exact low-HP Rest race did not appear in turns 1-15,
so this packet tests adjacent discipline only: avoid severe cash-out errors
while still selecting route-positive moves.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/low_rest_race_cashout_probe_001_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #8 Round 3 thread above.
- Pokemon Showdown replay source above.
- Raw log:
  `https://replay.pokemonshowdown.com/gen2ou-2544449982-h3w37s4ld0qjafggb4uanfpx1ajhioipw.log`

## Contamination Control

Local search found no prior `2544449982` artifact before selection. The raw
log was downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not
inspected; each prompt was generated with
`tools/pokemon_mastery/replay_turn_pause.py` and revealed only after the answer
was frozen.

Stopped after turn 15 for a 30-side-decision packet.

## Score Summary

Turns scored: 1-15.

Scorable side decisions: 30.

Top-match: 16 / 30.

Acceptable-match: 23 / 30.

Severe blunders: 0.

State errors: 1.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 22 / 30.

Route-converting move chosen: 13 / 22 target converter decisions.

Branch-punish chosen: 11 / 17 named-branch decisions.

Main result:
Catastrophic control held, and acceptable-match reached the provisional 70%
gate. This is not broad improvement: top-match stayed just under the 55% target
and the exact low-HP Rest-race pattern did not appear. The useful evidence is
that the Rest-race correction did not immediately create a new severe
cash-out error, but positive move selection still depends on branch-action
accuracy.

Earliest meaningful error:
Turn 5. I did not price that p2 still had an unused sleep source available and
therefore missed Jynx entering as the sleep absorber into Gengar's Hypnosis.

## Focused Turn Table

| Turn | Side | Frozen top-three | Actual | Top | Accept | Positive | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss; Thief/utility; Psychic chip | Lovely Kiss | 1 | 1 | 1 | Correct sleep claim before Cloyster's support. |
| 1 | p2 | Switch sleep absorber; Spikes if accepting sleep; attack only as low branch | Zapdos switch | 1 | 1 | 1 | Correct sleep-absorber class. |
| 2 | p1 | Thief/utility; own Spikes handoff; Psychic/Ice Beam chip | Psychic | 0 | 1 | 1 | Active chip into Snorlax was acceptable; top overvalued utility. |
| 2 | p2 | Switch sleeper out; stay only with active job; counter-pressure | Snorlax switch | 1 | 1 | 1 | Correctly preserved sleeping Zapdos. |
| 3 | p1 | Switch Normal owner; active chip only if no owner; no second sleep | Cloyster switch | 1 | 1 | 1 | Correct handoff into Double-Edge. |
| 3 | p2 | Double-Edge; Curse on hard switch; set read only after reveal | Double-Edge | 1 | 1 | 1 | Correct active pressure. |
| 4 | p1 | Spikes; Surf chip; Explosion only as branch | Spikes | 1 | 1 | 1 | Correct support-before-cash-out. |
| 4 | p2 | Double-Edge; Gengar/absorber if covering Explosion; Curse | Gengar switch | 0 | 1 | 0 | Named absorber branch but did not choose it. |
| 5 | p1 | Surf; switch to special owner; Explosion not into Gengar | Jynx switch | 0 | 0 | 0 | State error: missed p2 Hypnosis and sleep-absorber need. |
| 5 | p2 | Thunderbolt/coverage; Thief/utility; switch | Hypnosis | 0 | 0 | 0 | Missed unused sleep-source route. |
| 6 | p1 | Switch sleeping Jynx out; stay only with active job; preserve Cloyster | Jolteon switch | 1 | 1 | 1 | Correct saved-sleeper handoff. |
| 6 | p2 | Thunderbolt/coverage; utility into switch; preserve Gengar | Thunderbolt | 1 | 1 | 1 | Correct active coverage. |
| 7 | p1 | Thunderbolt; switch owner; Hidden Power if Ground branch is strongest | Substitute | 0 | 0 | 0 | Missed Substitute as branch-punish into the immunity switch. |
| 7 | p2 | Ground/Steel switch; active coverage; preserve Gengar | Steelix switch | 1 | 1 | 1 | Correct Electric-immunity branch. |
| 8 | p1 | Baton Pass/handoff; Hidden Power Water if available; hard switch | Hidden Power | 0 | 1 | 1 | Own hidden coverage made active pressure better than my top. |
| 8 | p2 | Earthquake; Roar if mechanics/position support it; preserve Steelix | Earthquake | 1 | 1 | 1 | Correctly broke Jolteon's Substitute pressure. |
| 9 | p1 | Switch Cloyster; Substitute only if it beats EQ loop; Hidden Power is bad if it fails to KO | Cloyster switch | 1 | 1 | 1 | Correct speed/order and survival preservation. |
| 9 | p2 | Earthquake; preserve only if Surf owner is obvious; Roar if needed | Earthquake | 1 | 1 | 1 | Correct active punish. |
| 10 | p1 | Surf; Explosion only with exact converter; preserve Cloyster if branch is covered | Surf | 1 | 1 | 1 | Correct active pressure instead of self-KO. |
| 10 | p2 | Switch Steelix out; use Water/sleep owner; stay only if Cloyster lacks Surf | Zapdos switch | 0 | 1 | 1 | Correct preserve-Steelix class, wrong owner. |
| 11 | p1 | Surf; handoff if Zapdos can use Sleep Talk; do not boom into Gengar branch | Snorlax switch | 0 | 0 | 0 | Underpriced revealed sleep absorber's active job. |
| 11 | p2 | Switch sleeping Zapdos out; Sleep Talk only if own set supports it; preserve route piece | Sleep Talk Rest | 0 | 0 | 1 | Hidden own move explains actual; no hidden-info error. |
| 12 | p1 | Curse; Double-Edge if Zapdos stays; switch only if p2 must answer Snorlax | Zapdos switch | 0 | 0 | 0 | Missed counter-handoff into the Gengar branch. |
| 12 | p2 | Switch physical/Ghost answer; Sleep Talk if no owner; preserve Zapdos | Gengar switch | 1 | 1 | 1 | Correct answer class. |
| 13 | p1 | Switch to boom owner; Thunderbolt if active pressure is stronger; Hidden Power into Steelix branch | Thunderbolt | 0 | 1 | 0 | Overcalled full-health Gengar Explosion. |
| 13 | p2 | Explosion; Ice Punch/Thunderbolt active pressure; switch Steelix | Ice Punch | 0 | 1 | 0 | Same overcash: active coverage was better. |
| 14 | p1 | Hidden Power into Steelix branch; Thunderbolt if Gengar stays; preserve Zapdos if Snorlax enters | Gengar switch | 0 | 0 | 1 | Missed the actual counter-handoff to Snorlax. |
| 14 | p2 | Switch Steelix/Ground; switch Snorlax as broader owner; stay only if paralysis risk is acceptable | Snorlax switch | 0 | 1 | 1 | Correct preserve-Gengar switch class, wrong top owner. |
| 15 | p1 | DynamicPunch; utility/Thief; switch if Earthquake owner is obvious | Dynamic Punch | 1 | 1 | 1 | Correct Snorlax pressure without Explosion. |
| 15 | p2 | Earthquake if available; switch if no coverage; Double-Edge is blocked | Earthquake | 1 | 1 | 1 | Correct conditional hidden coverage after role reveal. |

## Lessons

1. The low-HP Rest-race severe did not repeat, but the exact trigger did not
   appear, so the fix is not proven.
2. Sleep-source accounting is still live. Turn 5 showed I can preserve a
   sleeping Pokemon correctly after the fact, but still miss that the opponent
   has not used sleep yet.
3. Substitute must be treated as a branch action. Turn 7 punished looking only
   at attack/switch when the opponent's Electric immunity branch was likely.
4. The self-KO correction can overfire. Turn 13 was not a low Gengar cash-out
   position: full-health Gengar had active Ice Punch pressure, and Explosion
   did not deserve to dominate the line.
5. Hidden-info discipline held. I did not claim Zapdos Sleep Talk, Snorlax
   Earthquake, Gengar DynamicPunch, or Jolteon Hidden Power as facts before
   reveal; when I used them, they were marked conditional or strong-prior.

## Next Rep

Short targeted review of turns 5, 7, and 13 before another fresh replay:

- turn 5: unused sleep-source accounting and sleep absorber handoff;
- turn 7: Substitute/setup as the action that beats an obvious receiver;
- turn 13: full-health Gengar active pressure versus low-Gengar cash-out.
