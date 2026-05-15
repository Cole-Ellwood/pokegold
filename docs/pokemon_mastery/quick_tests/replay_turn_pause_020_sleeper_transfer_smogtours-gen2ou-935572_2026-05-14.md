# Replay Turn-Pause 020 Sleeper Transfer - smogtours-gen2ou-935572 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935572`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: test whether `sleeping_piece_later_job_probe_001` transfers into a
fresh replay with real RestTalk and wake-and-act pressure.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only whether broad move names appeared
  somewhere in the log: `Sleep Talk`, `Heal Bell`, and induced sleep moves.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local replay helper after answers
  were frozen.
- This is a semi-blind replay score, not a final exam.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/sleeping_piece_later_job_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/source_to_policy_ledger.md`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon GSC Snorlax analysis thread:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the relevant transfer rule is not "always switch the sleeper" or
"always cash out into the sleeper." GSC sleep must be priced with Sleep Talk,
Heal Bell, wake-and-act timing, one-time trades, and the Spikes/Rapid Spin
switch economy.

## Score Summary

Target turns scored: 12-23.

Context turns 1-11 established: p1 led Snorlax into p2 Cloyster, then switched
to Cloyster; p2 got first Spikes; both Cloyster traded Toxic; p1 Cloyster
cashed out with Explosion; p1 Gengar preserved the spinblock route while p2
went Raikou; p2 Golem later removed p1's Spikes with Rapid Spin.

Target decisions scored: 23 side-decisions. p2 turn 13 was excluded because
Sleep Powder moved first and prevented the selected move from being logged.

Top-match: 11 / 23.

Acceptable-match: 16 / 23.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful target error: turn 14.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 12 | Exeggutor 73 vs Raikou 91 | p1 Sleep Powder; p2 switch Snorlax or another sleep absorber | p2 Snorlax switch; p1 Sleep Powder miss | both top | Correctly found the sleep route and the absorber branch. |
| 13 | Exeggutor 79 vs Snorlax 100 after miss | p1 Sleep Powder again; p2 stay or punish if not slept | p1 Sleep Powder hit; p2 slept before action | p1 top; p2 excluded | Correct re-solve after miss: sleep was still live and not blocked by clause. |
| 14 | Exeggutor 85 vs sleeping Snorlax 100 | p1 Psychic; p2 switch out to preserve Sleep Clause material | p1 Psychic; p2 stayed asleep | p1 top; p2 miss | I over-applied the switch-out default. Staying was defensible because Psychic was steady pressure, not immediate route conversion. |
| 15 | Exeggutor 91 vs sleeping Snorlax 85 | p1 Psychic; p2 can still stay if the punish remains low | p1 Psychic; p2 stayed asleep | p1 top; p2 acceptable | Corrected the exception: staying to burn turns was still live. |
| 16 | Exeggutor 97 vs sleeping Snorlax 68 | p1 Explosion; p2 likely switch or continue burning turns | p1 Psychic; p2 stayed asleep | both miss | I overcorrected into a premature one-time trade. Cash-out was not required yet. |
| 17 | Exeggutor 100 vs sleeping Snorlax 50 | p1 Explosion; p2 likely stay/wake branch | p1 Psychic; p2 stayed asleep | p1 miss; p2 acceptable | Same calibration miss: name wake risk, but do not spend Explosion before the route trade is necessary. |
| 18 | Exeggutor 100 vs sleeping Snorlax 33 | p1 Psychic; p2 stay and may wake-act | p1 Psychic; p2 woke and used Self-Destruct | p1 top; p2 acceptable | Wake-and-act was live. I named the wake branch too generically; Self-Destruct needed to be explicit. |
| 19 | Gengar 88 vs poisoned Cloyster 21 | p1 Thunderbolt or attack; p2 likely spend low Cloyster | p2 Vaporeon switch; p1 Thunderbolt | p1 top; p2 miss | The low Cloyster was not automatically spent; p2 used Vaporeon to take the Gengar hit and reveal the next RestTalk route. |
| 20 | Gengar 94 vs Vaporeon 67 | p1 Thunderbolt; p2 switch Raikou, with Rest as serious | p1 Hypnosis miss; p2 Rest | p1 miss; p2 acceptable | I missed that Sleep Clause was free again after p2 Snorlax fainted. Gengar could re-open sleep pressure. |
| 21 | Gengar 100 vs Resting Vaporeon 100 | p1 Thunderbolt; p2 Sleep Talk | p1 Ice Punch; p2 Sleep Talk Surf | p1 miss; p2 top | Transfer success on p2: sleeping Vaporeon was active through Sleep Talk. I missed p1's Ice Punch scout into possible switch coverage. |
| 22 | Gengar 60 vs RestTalk Vaporeon 99 | p1 switch Zapdos; p2 Sleep Talk | p1 Zapdos switch; p2 Sleep Talk Surf | both top | Correctly preserved Gengar and treated the sleeping Vaporeon as live. |
| 23 | Zapdos 60 vs RestTalk Vaporeon 100 | p1 Thunder; p2 switch Raikou | p2 Raikou switch; p1 Thunder miss | both top | Correctly priced the sleeping RestTalk user as active but switchable once Zapdos created stronger direct pressure. |

## Context Errors Worth Keeping

- Turn 1: I expected lead Snorlax to act; p1 instead switched to Cloyster to
  contest the Spikes mirror.
- Turn 5: I over-preserved poisoned Cloyster; p1 cashed it out with Explosion
  after it had set Spikes and landed Toxic pressure.
- Turn 6: I expected Zapdos pressure; p1 switched Gengar, preserving a
  spinblock route against low Cloyster.
- Turn 8: I did call p2 Golem Rapid Spin as a serious branch, but I missed
  p1's Zapdos switch to punish the spin turn.

## Error Classes

- Switch-out default overreach: turn 14 repeated the old overcorrection. Sleep
  Clause material should be preserved when the board demands it, but steady
  low-punish pressure can justify staying asleep.
- Premature cash-out: turns 16-17 showed the opposite error. I saw wake risk
  and reached for Explosion before proving Exeggutor had to be spent.
- Wake-trade underspecification: turn 18 was an acceptable branch call but not
  precise enough. Against Snorlax, wake-and-act must include Self-Destruct when
  the route trade matters.
- Sleep Clause reset miss: turn 20 showed I forgot that after the induced
  sleeping Snorlax fainted, Gengar's Hypnosis route was legal again.
- RestTalk transfer success: turns 21-23 showed improvement. I immediately
  treated sleeping Vaporeon as active through Sleep Talk and preserved Gengar
  once Sleep Talk Surf was revealed.

## Policy Update

Add to sleep policy: cashing out into a sleeper requires a threshold. Use
steady pressure when the sleeper's wake branch is not yet route-ending and the
opponent can still switch to absorb Explosion. Cash out only when the wake
move, Rest, Sleep Talk, or endgame role would otherwise undo the route.

## Next Study Target

Run a short fresh replay or constructed mini-probe on "cash-out threshold into
sleeping targets": when to keep attacking, when to switch to a wake absorber,
and when to spend Explosion/Self-Destruct.
