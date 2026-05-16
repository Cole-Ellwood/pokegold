# Replay Turn-Pause 011 Support-Choice Drill - smogtours-gen2ou-928706 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-928706`.

Tournament source: Smogon `GSC OU Winter Seasonal #8: Round 12 [REPLAYS Required]`.

Mode: spectator public.

Purpose: fresh replay drill for the error from
`replay_turn_pause_010_pta057_regression`: choosing the correct support action,
not just avoiding Explosion. The specific question was whether I could rank
Spikes, Toxic, Roar, Rapid Spin, handoff, attack, and cash-out by the route
they serve.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_010_pta057_regression_smogtours-gen2ou-928703_2026-05-14.md`

Web sources checked:

- Smogon, `Playing with Spikes in GSC`:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, `Explosion in GSC`:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, `GSC OU Sample Teams Breakdown`:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: the narrow source check reinforced that GSC support pieces can
compress Spikes, Rapid Spin, Explosion, status, and handoff roles. The correct
question is not "which support move is generally best?" but "which support job
changes this route now?"

Contamination control:

- Local docs were searched for `928706`; the only prior hit was a note in the
  previous artifact saying it had not yet been reviewed.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-19 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Turn 10 p1 was excluded because sleep prevented any chosen move from being
  logged.

## Score Summary

Turns: 1-19.

Decisions scored: 37 side-decisions.

Top-match: 14 / 37.

Acceptable-match: 23 / 37.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 1.

Support-choice result: improved but still uneven. I correctly hit several
support jobs: p2 Spikes on turn 1, p1 Spikes and p2 Toxic on turn 2, p1
Steelix answer on turn 11, p1 Charizard preserve on turn 16, and p2 Starmie
Rapid Spin on turn 19. The main misses were p1 Toxic before Spikes in the
Cloyster mirror, both Raikou handoffs on turn 3, and Charizard's Roar/Toxic
support pattern on turns 12-18.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Cloyster mirror, no hazards | both Spikes | p1 Toxic; p2 Spikes | p1 miss, p2 top | Toxic can be the first support action in a mirror; I over-forced symmetric Spikes. |
| 2 | p1 side Spikes, p1 Cloyster has Toxic | p1 Spikes; p2 Toxic | p1 Spikes; p2 Toxic missed | both top | Correct: reciprocal Spikes plus status pressure before cash-out. |
| 3 | both Cloyster, both sides Spikes | both Toxic | both switched Raikou | both miss | After both Spikes are up, handoff to the Electric route can outrank more status. |
| 4 | Raikou mirror | both Thunder | both Thunder | both top | Direct exchange was right before other support became urgent. |
| 5 | p1 Raikou paralyzed | p1 switch or preserve; p2 attack | p1 Rest; p2 Hidden Power | both acceptable | Rest was the preservation version I missed. |
| 6 | p1 Raikou asleep vs p2 Raikou | p1 Sleep Talk; p2 attack | p1 Sleep Talk; p2 switched Snorlax | p1 top, p2 miss | I missed the Snorlax handoff after Raikou forced Rest. |
| 7 | p1 sleeping Raikou vs p2 Snorlax | p1 switch; p2 Curse | p1 switched Snorlax; p2 Lovely Kiss missed | p1 acceptable, p2 miss | Lovely Kiss Snorlax changed the risk map; sleep pressure was live. |
| 8 | Snorlax mirror | p1 Double-Edge; p2 Lovely Kiss | both Double-Edge | p1 top, p2 miss | Once sleep missed, direct damage became the immediate route. |
| 9 | both Snorlax low/mid HP | p1 Rest; p2 attack | p1 Rest; p2 switched Steelix | p1 top, p2 miss | Steelix was the normal-resist handoff I did not price. |
| 10 | p1 sleeping Snorlax vs Steelix | p2 Roar | p2 Curse | p1 unscored, p2 miss | Steelix used setup before phazing or Explosion. |
| 11 | p1 sleeping Snorlax vs +1 Steelix | p1 switch to Steelix answer; p2 Earthquake | p1 switched Charizard; p2 Earthquake | p1 acceptable, p2 top | Correct class: preserve Snorlax and answer the setup route. |
| 12 | Charizard vs Steelix | p1 Fire Blast; p2 switch | p1 Roar; p2 switched Starmie | p1 miss, p2 acceptable | Charizard's job was support phazing, not immediate fire damage. |
| 13 | Charizard with Roar vs Steelix | p1 Fire Blast; p2 switch Starmie | p1 Toxic; p2 switched Raikou | p1 miss, p2 acceptable | Charizard used status to punish the Electric handoff. |
| 14 | Charizard vs poisoned Raikou | p1 switch Snorlax; p2 Thunder | both switched Snorlax | p1 top, p2 miss | Snorlax handoff preserved Charizard from Thunder. |
| 15 | p1 sleeping Snorlax vs p2 Snorlax | p1 stay/Double-Edge if possible; p2 Rest | p1 Sleep Talk into Double-Edge; p2 switched Heracross | p1 top, p2 miss | I missed Heracross as the route handoff, but p1's stay-and-hit line was right. |
| 16 | p1 sleeping Snorlax vs low Heracross | p1 switch Charizard; p2 attack | p1 switched Charizard; p2 Rest | p1 top, p2 miss | Charizard was the correct preserve answer; Heracross chose reset over immediate damage. |
| 17 | Charizard vs sleeping Heracross | p1 attack, Roar as alternative; p2 switch | p1 Roar; p2 switched Raikou | both acceptable | Roar was part of Charizard's support identity. |
| 18 | Charizard vs sleeping Heracross again | p1 Roar; p2 switch Starmie | p1 Toxic; p2 switched Starmie | p1 miss, p2 top | Toxic on the spinner was the support action that changed the next subgame. |
| 19 | Charizard vs toxic Starmie | p1 Roar; p2 Rapid Spin | p1 switched Snorlax; p2 Rapid Spin | p1 miss, p2 top | I saw the Spin, but missed that p1 chose preservation over trying to deny it. |

## Error Classes

- Handoff timing: turn 3 repeated the problem from the prior run. After both
  sides had Spikes, the correct route was Electric handoff, not more Cloyster
  status.
- Support identity misread: Charizard was a Roar/Toxic support piece in this
  game; I kept trying to make it an immediate Fire Blast attacker.
- Spinner subgame mismatch: I predicted Starmie's Rapid Spin on turn 19, but
  mispriced p1's answer. The player preserved Charizard and accepted Spin
  rather than over-contesting without a revealed spinblocker.
- Sleep and handoff route misses: Lovely Kiss Snorlax, Steelix, and Heracross
  entries all appeared before I named them.

## Next Study Target

Turn this into a compact checklist for future support turns:

```text
Support-choice order:
1. Has the current route already been changed by Spikes/status/phaze/Spin?
2. Which teammate becomes better if this support lands?
3. Which opposing route becomes live if I skip Spin or phaze?
4. Is a handoff better than another support move?
5. Is Explosion actually required now, or does it spend the support piece too
   early?
```
