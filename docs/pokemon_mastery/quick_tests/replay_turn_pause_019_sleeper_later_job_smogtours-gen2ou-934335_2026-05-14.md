# Replay Turn-Pause 019 Sleeper Later Job - smogtours-gen2ou-934335 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934335`.

Mode: spectator public continuation, semi-blind candidate-screened.

Purpose: continue `replay_turn_pause_018` after the first sleep preservation
branch and test whether I track later jobs for sleeping Pokemon: Sleep Talk,
cleric reset, forced switches, and absorption of predicted coverage.

Contamination control:

- Turns 1-8 were known from `replay_turn_pause_018`.
- Turns 9-24 were revealed one turn at a time with the local helper.
- The replay was originally candidate-screened only for the presence of an
  induced sleep move name somewhere in the log.
- This is quick-probe evidence, not final-exam-clean evidence.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_018_sleep_clause_absorber_fresh_smogtours-gen2ou-934335_2026-05-14.md`

Web sources checked:

- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Jynx GSC OU analysis thread:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon GSC Snorlax analysis thread:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the GSC status article names Sleep Talk and Heal Bell as reasons
sleep is not a permanent ownership claim. The Jynx analysis specifically treats
Sleep Talk users such as Snorlax, Raikou, and Moltres as sleep absorbers that
can activate Sleep Clause while threatening back. The Snorlax analysis warns
that Rest without Sleep Talk gives the opponent phazing or setup windows.

## Score Summary

Target turns scored: 17-24.

Context turns 9-16 were used to reach the second sleep event and establish the
support map: p2 Cloyster removed p1's Spikes with Rapid Spin, p1 Snorlax
revealed Rest, p2 Skarmory phazed through p1's sleeping Snorlax, and p1
Jolteon revealed Growth.

Target decisions scored: 16 side-decisions.

Top-match: 3 / 16.

Acceptable-match: 7 / 16.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful target error: turn 17.

Helper limitation: after p2 Miltank used Heal Bell on turn 23, the raw replay
logged `-cureteam`, but the local prompt helper still displayed p2's inactive
Snorlax as asleep on turn 24. I did not count an exact inactive-status update
claim from that helper display.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 17 | p1 Jolteon `spa+1` 99 vs p2 Nidoking 100 | p1 Baton Pass or move to Zapdos; p2 Earthquake, with Lovely Kiss as a risk | p1 hard switched Zapdos; p2 Lovely Kiss slept Zapdos | p1 acceptable; p2 miss | I saw the Zapdos receiver but underpriced p2's own sleep route into that receiver. Sleep Clause is per sleep user, not globally spent by p1's earlier Hypnosis. |
| 18 | sleeping Zapdos 100 vs Nidoking 100 | p1 switch Alakazam; p2 Ice Beam/coverage | p1 Alakazam; p2 Earthquake | p1 top; p2 miss | Correctly preserved sleeping Zapdos as Sleep Clause material, but p2's best immediate punish was Earthquake into the likely grounded switch. |
| 19 | Alakazam 34 vs Nidoking 100 | p1 Psychic; p2 switch Skarmory | p1 Recover; p2 Earthquake | both miss | I missed the Recover damage loop: Alakazam could recover around Earthquake instead of gambling on immediate Psychic. |
| 20 | Alakazam 37 vs Nidoking 100 | p1 Psychic; p2 Earthquake | p1 Recover; p2 Earthquake | p1 miss; p2 top | Same error repeated. Track the damage loop before choosing the active-looking attack. |
| 21 | Alakazam 40 vs Nidoking 100 | p1 Recover; p2 Earthquake | p1 switched sleeping Snorlax; p2 Thunder | both miss | I missed a sleeping RestTalk Snorlax as the coverage absorber. Sleeping does not make a piece inert if it still covers a predicted move and may have Sleep Talk. |
| 22 | sleeping p1 Snorlax 72 vs Nidoking 100 | p1 stay and burn/wake; p2 attack | p2 switched Miltank; p1 Sleep Talk called Earthquake | p1 acceptable; p2 miss | Rest plus Double-Edge should have raised the RestTalk inference earlier. Miltank entering made cleric reset a live p2 route. |
| 23 | sleeping p1 Snorlax 78 vs Miltank 87 | p1 Sleep Talk; p2 Heal Bell | p2 Heal Bell; p1 woke and used Double-Edge | p1 acceptable; p2 top | I caught the cleric route once Miltank was active. Also remember GSC wake-and-act branches when a sleeper has spent turns on-field. |
| 24 | p1 Snorlax 78 vs Miltank 57 | p1 Double-Edge; p2 Milk Drink | p1 switched Gengar; p2 Growl | p1 miss; p2 acceptable | Once Miltank showed Heal Bell, p1 valued preserving Snorlax and denying Growl more than immediate damage. |

## Context Error Worth Keeping

Turn 11 was not part of the target score, but it exposed a linked route error.
After p1 Cloyster fainted, p2 Cloyster's Rapid Spin was high value because it
removed p1's Spikes and made future preservation switches cheaper. I overcalled
Explosion/Toxic pressure and did not give Rapid Spin enough weight.

## Error Classes

- Opponent sleep route underpricing: turn 17 showed I tracked p1's sleep route
  but forgot p2 still had its own legal sleep route through Nidoking.
- RestTalk inference lag: Rest plus Double-Edge on Snorlax should trigger a
  Sleep Talk branch before the move is revealed.
- Cleric route lag: Miltank should immediately raise Heal Bell as a way to
  reset a slept teammate or status map. I caught Heal Bell on turn 23, but not
  the turn-22 Miltank entry.
- Damage-loop miss: Alakazam's Recover loop against Earthquake was better than
  the active-looking Psychic until a survival threshold changed.
- Support-state miss: with p1 Cloyster gone, p2 Cloyster's Rapid Spin changed
  the future switch economy for every preserved piece.

## Policy Update

Add to sleep policy: a sleeping Pokemon's next job can be active before it
wakes. Price Sleep Talk, cleric support, forced-switch absorption, predicted
coverage absorption, wake-and-act timing, and whether hazard removal changes
the cost of preserving it.

## Next Study Target

Run a compact quick probe on "sleeping piece still has a job" with six prompts:
Sleep Talk attack, Heal Bell reset, phaze bait, coverage absorber, wake-and-act
attack, and hazard-removal enabling preservation.
