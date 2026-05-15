# Replay Turn-Pause 022 Receiver Counterplay Transfer - smogtours-gen2ou-935551 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935551`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: test whether the post-oracle Self-Destruct receiver lesson transfers
to a fresh Baton Pass receiver segment. The target was to price Explosion,
Self-Destruct, phazing, and immediate attack before boosting, without
hallucinating counterplay that is not public.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move-name presence: Baton Pass,
  Agility, and one-time trade moves.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.
- The helper omitted passed Speed and Substitute state in later prompts, so the
  manual public state kept Snorlax's passed Speed and Substitute state after
  they were revealed.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/selfdestruct_receiver_branch_regression_001_smogtours-gen2ou-934904_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`

Web sources checked:

- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Mean Look / Spider Web + Baton Pass in GSC OU:
  `https://www.smogon.com/forums/threads/mean-look-spider-web-baton-pass-in-gsc-ou.3696148/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`

Source note: GSC Baton Pass receivers can end games quickly, and accepted
counterplay includes phazing, Explosion, status, direct damage, and forcing
Spikes chip. The lesson from this run is to price those branches without
inventing a revealed counterplay move.

## Score Summary

Target turns scored: 5-14.

Context turns 1-4: p2 switched Cloyster to Raikou into Exeggutor; Exeggutor
used Psychic and Leech Seed to pressure Raikou/Snorlax; p1 then used Explosion
to trade Exeggutor for Raikou after Raikou revealed Crunch.

Target decisions scored: 16 side-decisions. p2 turns 13-14 were excluded
because the active fainted before a move could resolve or the switch was
forced.

Top-match: 12 / 16.

Acceptable-match: 15 / 16.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful target error: turn 6.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 5 | Smeargle 100 vs Cloyster 100 after Exeggutor/Raikou trade | p1 Agility; p2 Spikes or direct pressure | p1 Agility; p2 Spikes | both top | Correctly found the pass setup and p2's hazard clock. |
| 6 | Smeargle `spe+2` vs Cloyster 100 with Spikes up | p1 Baton Pass or Encore if Cloyster repeats support; p2 continue pressure | p1 Encore; p2 Spikes | p1 acceptable; p2 top | Encore was better than immediate pass because it locked the support turn. |
| 7 | Smeargle `spe+2` vs Encored Cloyster / likely switch | p1 Spore into the counterplay slot; p2 switch to sleep absorber | p2 Snorlax switch; p1 Spore slept Snorlax | both top | Correctly valued sleep before the pass and p2's Snorlax absorber. |
| 8 | Smeargle `spe+2` vs sleeping Snorlax 100 | p1 Baton Pass promptly; p2 preserve sleeping Snorlax and bring active counterplay | p2 Cloyster; p1 Baton Pass to Snorlax | both top | Good transfer: pass before wasting the sleep window, and preserve the sleeper. |
| 9 | Passed-Speed Snorlax 94 vs Cloyster 100; Spikes on p1 side | p1 Substitute to scout/control Cloyster; p2 Surf or Explosion as worst branch | p1 Substitute; p2 Surf | p1 top; p2 acceptable | Correctly priced Explosion as a branch without assuming it was real; actual counterplay was Surf chip. |
| 10 | Snorlax behind Sub 75 vs Cloyster 100 | p1 Belly Drum if Surf does not break the route; p2 Surf | p1 Belly Drum; p2 Surf | both top | The setup turn was justified because Substitute covered immediate damage and no phaze/self-KO was revealed. |
| 11 | Drum Snorlax 32 with Sub pressure vs Cloyster 100 | p1 renew Substitute or attack depending on sub state; p2 Surf | p1 Substitute; p2 Surf | p1 acceptable; p2 top | Correct enough: preserve the receiver's hit buffer before attacking. |
| 12 | Drum Snorlax 13 with active route vs Cloyster 100 | p1 Frustration; p2 Surf | p1 Frustration; p2 Surf | both top | Cash the receiver instead of adding more setup. |
| 13 | Drum Snorlax 19 vs Cloyster 23 | p1 Frustration KO | p1 Frustration KO; p2 Golem forced in | p1 top; p2 excluded | Correct conversion after Cloyster was in range. |
| 14 | Drum Snorlax 25 vs Golem 100 | p1 Earthquake | p1 Earthquake KO; p2 fainted before action | p1 top; p2 excluded | Correctly identified coverage and did not overthink another setup turn. |

## Error Classes

- Mild pass-timing miss: turn 6 showed Encore was better than immediate pass
  because it locked Cloyster into support before the receiver entered.
- Counterplay calibration improved: unlike `replay_turn_pause_021`, I named
  Explosion/Self-Destruct/phazing as worst branches but did not hallucinate
  them. Cloyster's actual line was Surf chip.
- Receiver conversion improved: once Belly Drum Snorlax had the route, the
  correct action was Substitute or attack, not extra setup.
- Helper-state risk: passed Speed and Substitute state need manual tracking
  because the prompt helper currently drops them.

## Policy Update

Add to receiver policy: before boosting, price Explosion, Self-Destruct,
phazing, status, and immediate damage; then ask which of those is actually
public or strongly inferable. If the only revealed counterplay is damage and
Substitute covers it, setup can be correct. Do not turn "price counterplay" into
"invent counterplay."

## Next Study Target

Run a fresh receiver segment where the defensive side has a revealed phazing or
Explosion move before the pass resolves, and score whether I switch, attack,
boost, or preserve correctly.
