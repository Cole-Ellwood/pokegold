# Replay Turn-Pause 013 PTA-058 Preserve Boundary - smogtours-gen2ou-933556 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-933556`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 13 (Loser's Bracket) [REPLAYS Required]`.

Mode: spectator public.

Purpose: fresh regression for the `PTA-058` boundary clause. The target was
whether I could both call a correct support cash-out and preserve the right
piece against the opponent's cash-out.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_012_pta058_boundary_smogtours-gen2ou-930765_2026-05-14.md`

Web sources checked:

- Smogon `GSC OU Winter Seasonal #8: Round 13`:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-13-losers-bracket-replays-required.3781520/`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: this used the other Round 13 game from the same public tournament
source after local search showed no prior `933556` artifact.

Contamination control:

- Local search found no prior `933556` review, worked example, or quick test.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-12 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 1-12.

Decisions scored: 24 side-decisions.

Top-match: 11 / 24.

Acceptable-match: 16 / 24.

Severe blunders: 1.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Targeted result: partial correction with one serious miss. I correctly called
the p2 Cloyster cash-out on turn 8 after both Cloysters had delivered
Toxic/Spikes and p2's support piece was poisoned and low. I failed the matching
defensive half: I left p1 Snorlax in my frozen answer instead of preserving it
by switching to p1's poisoned Cloyster, which the expert line did.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Cloyster mirror, no hazards | p1 Toxic; p2 Spikes | both Toxic | p1 top, p2 miss | Toxic can be mutual before hazards in this mirror. |
| 2 | both Cloyster toxic, no hazards | both Spikes | both Spikes | both top | Correct: once both are poisoned, set reciprocal Spikes. |
| 3 | both Cloyster toxic, both sides Spikes | both hand off to Electric | p1 Surf; p2 switched Zapdos | p1 miss, p2 acceptable | p1 punished the Electric handoff with Surf instead of leaving immediately. |
| 4 | p1 toxic Cloyster vs p2 Zapdos 79% | p1 special-wall handoff; p2 attack | p1 switched Raikou; p2 Hidden Power | both acceptable | Receiver naming improved: Raikou was the correct p1 route receiver. |
| 5 | Raikou vs Zapdos | p1 Thunder; p2 Snorlax handoff | p1 Thunder; p2 switched Snorlax | both top | Correct support-to-handoff sequence after Spikes. |
| 6 | p1 Raikou vs p2 Snorlax 65% | p1 preserve Raikou; p2 Rest as main reset | p1 switched Snorlax; p2 Rest | both acceptable | Rest reset plus anchor handoff was correctly priced as live. |
| 7 | p1 Snorlax vs p2 sleeping Snorlax | p1 Double-Edge; p2 Sleep Talk/stay | p1 Double-Edge; p2 switched Cloyster | p1 top, p2 miss | I missed p2 using poisoned Cloyster as the next support/cash-out piece. |
| 8 | p1 Snorlax 96% vs p2 poisoned Cloyster 51% | p1 Double-Edge; p2 Explosion | p1 switched Cloyster; p2 Explosion | p1 severe miss, p2 top | I called the cash-out but failed to preserve the healthy Snorlax from it. |
| 9 | p1 Exeggutor vs p2 Donphan after double KO | p1 Sleep Powder; p2 switch Zapdos | p1 Giga Drain; p2 switched Zapdos | p1 miss, p2 top | Donphan correctly handed off before taking the Grass/Psychic route; p1 chose damage over sleep. |
| 10 | p1 Exeggutor vs p2 Zapdos 80% | p1 switch Raikou; p2 Hidden Power | p1 Psychic; p2 Hidden Power | p1 miss, p2 top | I over-preserved Exeggutor; the player took Psychic damage before yielding. |
| 11 | p1 Exeggutor 61% vs p2 Zapdos 49% | p1 Psychic; p2 Hidden Power | p1 switched Snorlax; p2 Hidden Power | p1 miss, p2 top | This time preservation was correct; I failed to re-score after HP damage. |
| 12 | p1 Snorlax 79% vs p2 Zapdos 55% | p1 Double-Edge; p2 Thunder | p1 Lovely Kiss missed; p2 Thunder | p1 miss, p2 top | I missed sleep as the route-changing move into Zapdos. |

## Error Classes

- Preservation half of cash-out: turn 8 was the main severe error. Calling the
  opponent's Explosion is not enough; the advised side must preserve the route
  piece when a lower-value absorber exists.
- Handoff timing: turns 3, 7, and 9 still show uncertainty about when to leave
  the support mirror or bring a support/cash-out piece back in.
- Preserve-versus-pressure sequencing: turns 10 and 11 split in opposite
  directions; I preserved Exeggutor too early, then failed to preserve it after
  Zapdos damage made the branch worse.
- Sleep route undercall: turn 12 missed Lovely Kiss as the move that could
  change the Zapdos/Snorlax subgame.

## Next Study Target

Add a cash-out defense clause to the support checklist:

```text
If I predict the opponent's cash-out, first name the piece I am willing to lose.
Stay in only if that piece is already expendable or the trade opens a better
route. If a lower-value absorber exists and the active piece is still a route
piece, preserve before attacking.
```
