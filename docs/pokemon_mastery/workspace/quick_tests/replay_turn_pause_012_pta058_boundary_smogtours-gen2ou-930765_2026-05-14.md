# Replay Turn-Pause 012 PTA-058 Boundary - smogtours-gen2ou-930765 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-930765`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 13 (Loser's Bracket) [REPLAYS Required]`.

Mode: spectator public.

Purpose: fresh replay test of `PTA-058: Support Choice Before Handoff Or
Cash-Out`. The target was the boundary between continuing support, handing off
to the next route, and cashing out after the support Pokemon has already done
its job.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_011_support_choice_smogtours-gen2ou-928706_2026-05-14.md`

Web sources checked:

- Smogon `GSC OU Winter Seasonal #8: Round 13`:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-13-losers-bracket-replays-required.3781520/`
- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, `Explosion in GSC`:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: the web check reinforced the same boundary: GSC support pieces
can set hazards, spread status, phaze, spin, hand off, or Explode. Explosion
is wrong as a default, but correct when it removes the current route piece
after the support job is complete.

Contamination control:

- Local search found `930759` and `933547` were already reviewed, so they were
  rejected for this scored run.
- Local search found no prior `930765` review or quick test.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-12 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 1-12.

Decisions scored: 24 side-decisions.

Top-match: 11 / 24.

Acceptable-match: 12 / 24.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Targeted result: mixed. The support-choice checklist improved the early
Cloyster sequence: I hit p1 Spikes, p2 Toxic, p1 Toxic into Raikou, and the
Raikou handoff after both Spikes were up. The boundary error was the opposite
of the earlier Explosion overcall: I undercalled Steelix Explosion on
Exeggutor and Cloyster Explosion on low Snorlax after both support pieces had
already changed the route.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 Snorlax lead vs p2 Cloyster | p1 Curse or attack; p2 Spikes | p1 switched Cloyster; p2 Spikes | p1 miss, p2 top | I missed immediate support mirror as the Snorlax-side answer to lead Cloyster. |
| 2 | p1 Cloyster vs p2 Cloyster, p1 side has Spikes | p1 Spikes; p2 Toxic | p1 Spikes; p2 Toxic | both top | Correct: reciprocal Spikes plus status pressure. |
| 3 | both Cloyster, both sides have Spikes; p1 Cloyster toxic | p1 Toxic; p2 hand off to Raikou | p1 Toxic hit Raikou; p2 switched Raikou | both top | PTA-058 worked: after both Spikes were up, status into the handoff was better than more mirror support. |
| 4 | toxic Cloyster vs toxic Raikou | p1 switch Snorlax; p2 Thunder | both switched Snorlax | p1 top, p2 miss | I named the p1 preserve handoff but missed p2's matching Snorlax handoff. |
| 5 | Snorlax mirror, both sides Spikes | p1 Curse; p2 Lovely Kiss | p1 Double-Edge crit; p2 Curse | both miss | I still misprice direct Snorlax pressure versus setup/sleep in the mirror. |
| 6 | p1 Snorlax 79% vs p2 +1 Snorlax 19% | p1 Double-Edge; p2 Rest | p1 Double-Edge; p2 switched Steelix | p1 top, p2 miss | I missed Steelix as the normal-resist handoff after low Snorlax had drawn the hit. |
| 7 | p1 Snorlax vs p2 Steelix | p1 switch Cloyster; p2 Roar | p1 Earthquake; p2 Roar | p1 miss, p2 top | p2 phazed correctly; p1 had coverage and did not need to switch immediately. |
| 8 | p1 Exeggutor dragged into p2 Steelix 59% | p1 Sleep Powder; p2 preserve or sleep-absorb handoff | p1 Psychic; p2 Explosion | both miss | Boundary failure: Steelix had phazed, absorbed the normal route, and now removed Exeggutor. Cash-out was correct. |
| 9 | p1 Zapdos vs p2 Machamp after double KO | p1 attack; p2 switch Raikou | p1 switched Snorlax; p2 switched Raikou | p1 miss, p2 top | I saw the Electric handoff but missed p1's anchor handoff. |
| 10 | p1 Snorlax vs poisoned p2 Raikou | p1 Double-Edge; p2 Thunder or Rest | p1 Double-Edge; p2 switched Cloyster | p1 top, p2 miss | p2 preserved poisoned Raikou and used Cloyster as the next support/cash-out piece. |
| 11 | p1 Snorlax 79% vs p2 Cloyster 62% | p1 switch to absorb possible Explosion; p2 Explosion or Toxic | p1 Double-Edge; p2 Surf crit | both miss | I overcorrected toward Explosion; Cloyster first used damage to bring Snorlax into forced trade range. |
| 12 | p1 Snorlax 45% vs p2 Cloyster 37% | p1 switch to preserve Snorlax; p2 Explosion | p1 stayed; p2 Explosion | p1 miss, p2 top | Boundary split: I correctly identified cash-out for p2, but over-preserved p1's damaged Snorlax compared to the expert line. |

## Error Classes

- Cash-out boundary miss: turn 8 undercalled Steelix Explosion when the support
  piece had already phazed and the target was a real route piece.
- Handoff underpricing: turns 4, 6, 9, and 10 missed matching or defensive
  handoffs after the previous support action changed the board.
- Snorlax mirror pricing: turn 5 repeated the mirror issue: I overcalled
  setup/sleep and undercalled direct damage.
- Explosion overcorrection oscillation: turn 11 overcalled Explosion one turn
  early, while turn 12 correctly called p2 Explosion but over-preserved p1.

## Next Study Target

Update the support-choice checklist with a cash-out boundary clause:

```text
After a support piece has done its job, cash out when the current target is a
route piece and the support user no longer gains more by preserving, phazing,
spinning, or handing off. Do not delay the trade just because earlier drills
punished premature Explosion.
```
