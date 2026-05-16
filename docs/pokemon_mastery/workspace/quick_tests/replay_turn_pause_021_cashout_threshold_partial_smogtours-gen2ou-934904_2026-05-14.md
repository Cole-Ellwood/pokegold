# Replay Turn-Pause 021 Cash-Out Threshold Partial - smogtours-gen2ou-934904 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934904`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: test whether the sleeping-target cash-out threshold transfers to a
fresh replay. The exact "Explosion into the sleeping target" position did not
occur before the state shifted, so this is a partial transfer: sleep was live,
and the key one-time trade hit the current route piece instead.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move-name presence: induced
  sleep, Sleep Talk, and one-time trade moves.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- I accidentally exposed turns 1-2 while checking the p2 lead nickname species
  in the raw log header. Turns 1-2 are context only and not scored.
- Turns 3 onward were revealed one at a time with the local helper after
  answers were frozen.
- The local helper omitted passed Speed after Baton Pass, so the manual public
  state kept Marowak's passed Speed for turn 14.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/sleeping_target_cashout_threshold_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon GSC Snorlax analysis thread:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

Source note: Explosion is a route trade. This replay reinforced that the trade
target is the live route piece, not automatically the sleeping Pokemon.

## Score Summary

Target turns scored: 8-14.

Context from exposed turns 1-2: p1 led Snorlax into p2 Snorlax, switched to
Cloyster, p2 used Double-Edge, then p1 set Spikes while p2 continued
Double-Edge.

Target decisions scored: 14 side-decisions.

Top-match: 7 / 14.

Acceptable-match: 10 / 14.

Severe blunders: 1.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful target error: turn 14.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 8 | p1 Snorlax 100 `def-2` vs p2 Tyranitar 100 after Screech | p1 attack or reset the Defense drop; p2 Earthquake/Rock pressure | p2 Earthquake; p1 Lovely Kiss hit | p1 miss; p2 top | I undercalled sleep as the direct answer to the Screech Tyranitar. |
| 9 | p1 Snorlax 61 `def-2` vs sleeping Tyranitar 100 | p1 attack if it has Earthquake, with switch-reset as serious; p2 switch out to preserve sleeping Tyranitar | p1 switched Zapdos; p2 switched Forretress | p1 acceptable; p2 top | Correct preservation branch for p2; p1 valued reset plus matchup over attacking the sleeper. |
| 10 | Zapdos 100 vs Forretress 94 | p1 Thunder; p2 support or trade | p2 switched Raikou; p1 Thunder miss | p1 top; p2 miss | Forretress did not have to spend support immediately; p2 used Raikou as the Electric answer. |
| 11 | Zapdos 100 vs Raikou 94 | p1 switch to an Electric answer; p2 Thunder | p1 Jolteon; p2 Thunder miss | p1 acceptable; p2 top | Correct class of p1 switch, though I named generic Electric/Ground absorption rather than Jolteon specifically. |
| 12 | Jolteon 100 vs Raikou 99 | p1 set up or pass; p2 switch Snorlax | p2 Snorlax; p1 Agility | both acceptable/top | Correctly found the Baton Pass route shape and p2's Snorlax answer. |
| 13 | Jolteon `spe+2` vs Snorlax 94 | p1 Baton Pass to the receiver; p2 attack | p1 Baton Pass to Marowak; p2 Double-Edge | both top | Correctly identified the receiver route once Agility was revealed. |
| 14 | Marowak with passed Speed at 53 vs Snorlax 93 | p1 Earthquake; p2 attack | p1 Swords Dance; p2 Self-Destruct KOed both | p1 miss; p2 miss; severe branch miss | I failed to price Self-Destruct as the route-ending punish. The cash-out target was Marowak, the active converter, not the sleeping Tyranitar. |

## Context After Target Segment

- Turn 18: p2 switched Zapdos into Jolteon while p1 Baton Passed to Snorlax.
- Turn 28: p2 Raikou used Rest after Jolteon used Agility, creating a
  RestTalk branch.
- Turn 29: p1 passed to Tyranitar while p2 Raikou used Sleep Talk into Rest.
- Turns 32-33: I overcalled immediate Forretress Explosion into boosted
  Tyranitar. Actual Forretress used Toxic first, then Spikes. This is the same
  cash-out threshold lesson from another angle: support and status can outrank
  immediate Explosion even into a boosted route piece.

## Error Classes

- Sleep answer undercall: turn 8 showed Lovely Kiss was the route answer to
  Screech Tyranitar, not just damage or switching.
- Cash-out target identification: turn 14 showed the one-time trade should be
  priced around the current converter. Snorlax spent Self-Destruct into
  Marowak; the sleeping Tyranitar was not the trade target.
- Severe branch pricing miss: before boosting or attacking with a passed
  Marowak, name Snorlax Self-Destruct as a worst plausible branch.
- Explosion overcall after correction: later turns 32-33 showed I can still
  overcorrect. Forretress chose Toxic and Spikes before any Explosion.

## Policy Update

Add to cash-out threshold policy: first identify the current route piece. The
one-time trade target may be a boosted receiver or irreplaceable converter,
not the sleeping Pokemon. Against Snorlax, Self-Destruct must be named before
choosing setup with a passed receiver.

## Next Study Target

Run a narrower replay screen for a sleeping target where the active side has a
revealed one-time trade, or build a three-scenario post-oracle regression from
turn 14: attack, switch to absorber, or setup into Self-Destruct.
