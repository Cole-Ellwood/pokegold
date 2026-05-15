# Replay Turn-Pause 015 Support Status Follow-Up - smogtours-gen2ou-935022 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935022`.

Discovery source: Pokemon Showdown replay search API,
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`.

Mode: spectator public.

Purpose: fresh regression for the `PTA-058` handoff clause. The target question
was: after support status lands, does the next route become reset, switch,
cash-out, or handoff?

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_014_pta058_handoff_defense_smogtours-gen2ou-935045_2026-05-14.md`

Web sources checked:

- Smogon GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`
- Smogon `GSC OU Winter Seasonal #8: Round 9 [REPLAYS Required]`:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-9-replays-required-losers-bracket.3779865/`
- Pokemon Showdown replay search API:
  `https://replay.pokemonshowdown.com/search.json?format=gen2ou`
- Pokemon Showdown replay:
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-935022`

Source note: web search found no indexed Smogon post for exact replay ID
`935022`; the replay was selected from the live public replay search API after
local search found no prior artifact.

Contamination control:

- Local search found no prior `935022` review, quick test, or worked example.
- I downloaded the raw `.log` to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI or inspect turns beyond the prompt/reveal
  helper.
- The initial switch species was checked from the opening log lines because the
  helper displayed p1's Nidoking nickname without species.
- Turns 1-19 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 1-19.

Decisions scored: 35 side-decisions. Three no-action turns were excluded where
the selected move was not logged because the Pokemon fainted first or remained
asleep.

Top-match: 12 / 35.

Acceptable-match: 16 / 35.

Severe blunders: 1.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 1.

Earliest meaningful error: turn 1.

Targeted result: partial improvement. I correctly called the support follow-up
on turns 13-14 as `Toxic -> Spikes -> Explosion`, and I named the preserve line
against Cloyster Explosion. The miss was that the actual line did not preserve
Snorlax; it stayed and lost to a critical Explosion. The bigger branch-pricing
failure was turn 16: I let Tyranitar stay at 52% against Nidoking without
pricing that Earthquake could KO before Tyranitar moved.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Nidoking mirror, no reveals | both Lovely Kiss | both switched Zapdos | both miss | Nido mirror can immediately pivot to Zapdos rather than gambling sleep/EQ. |
| 2 | Zapdos mirror | both Thunder | both Thunder, p1 missed | both top | Basic mirror pressure correctly priced. |
| 3 | p1 Zapdos behind after Thunder | both Thunder | both switched Snorlax | both miss | Behind in the Zapdos mirror, both players preserved by moving to the anchor. |
| 4 | Snorlax mirror, no set info | both Curse | p1 Cloyster; p2 Lovely Kiss | both miss | I undercalled sleep as the first route changer. |
| 5 | p1 sleeping Cloyster vs LK Snorlax | p1 stay/burn sleep; p2 Double-Edge | p1 Misdreavus; p2 Curse | both miss | Sleep absorption enabled a ghost handoff; staying in missed the Snorlax setup route. |
| 6 | Misdreavus vs +1 Snorlax | p1 Perish Song; p2 Earthquake/switch | p1 Toxic into Nidoking; p2 Nidoking | p1 miss, p2 acceptable | Snorlax did not need to attack the ghost; Nidoking reset the subgame. |
| 7 | Misdreavus vs Nidoking | p1 Zapdos; p2 Earthquake | p1 sleeping Cloyster; p2 Earthquake | p1 acceptable, p2 top | Correct class was preserve Misdreavus with an absorber; exact absorber was asleep Cloyster. |
| 8 | sleeping Cloyster vs Nidoking | p1 stay; p2 Thunder/EQ | p1 Zapdos; p2 Focus Energy | both miss | I missed Focus Energy as the route setup. |
| 9 | Zapdos vs Focus Energy Nidoking | p1 Hidden Power; p2 Ice Beam | p1 Hidden Power; p2 Counter KO | p1 top, p2 miss | After Focus Energy, Counter/coverage must be in the worst branch, not only Ice Beam. |
| 10 | p1 Nidoking vs p2 low Nidoking | p2 switch Zapdos | p2 Earthquake crit KO; p1 move unlogged | p2 miss, p1 excluded | I overexpected preservation; the low Nidoking stayed to contest speed and crit route. |
| 11 | Snorlax vs low Nidoking | p1 Earthquake; p2 Earthquake | p1 Curse; p2 Cloyster | both miss | The actual line preserved Nidoking and used Cloyster to answer Snorlax. |
| 12 | +1 Snorlax vs Cloyster | p1 Double-Edge; p2 Spikes | p1 Curse; p2 Toxic | p1 miss, p2 acceptable | Cloyster chose status before hazards into the boosting anchor. |
| 13 | +2 toxic Snorlax vs Cloyster | p1 Double-Edge; p2 Spikes | p1 Double-Edge; p2 Spikes | both top | Correct support follow-up: after Toxic lands, set Spikes before cashing out. |
| 14 | +2 toxic Snorlax vs low Cloyster | p1 preserve with Misdreavus; p2 Explosion | p1 stayed; p2 Explosion crit KO | p1 acceptable, p2 top | Cash-out call was right; preserve line was defensible, but not the pro comparison. |
| 15 | Tyranitar vs Nidoking after double KO | p1 sleeping Cloyster; p2 Earthquake | p1 Earthquake; p2 Earthquake | p1 miss, p2 top | I over-preserved; Tyranitar could nearly remove Nidoking. |
| 16 | Tyranitar 52% vs Nidoking 8% | p1 Rock Slide; p2 Earthquake | p2 Earthquake KO; p1 move unlogged | p2 top, p1 excluded | Severe branch-pricing miss: Earthquake could KO before Tyranitar acted. |
| 17 | sleeping Cloyster vs low Nidoking | p1 excluded asleep; p2 Earthquake | p1 slept; p2 Focus Energy | p2 miss | Focus Energy was again used to preserve the crit route rather than simple damage. |
| 18 | sleeping Cloyster vs Focus Energy Nidoking | p1 Surf; p2 Earthquake | p1 woke Surf KO; p2 Thunder | p1 top, p2 miss | Surf was correct if wake happened; p2's real damage move was Thunder. |
| 19 | low Cloyster vs Zapdos | p1 stay and cash out if possible; p2 Thunder | p1 Explosion after Thunder miss; p2 Thunder | both top | Low support piece correctly became a one-time trade attempt. |

## Error Classes

- Sleep absorber into handoff: turn 5 showed that absorbing Lovely Kiss is not
  the end of the sequence. The next question is which revealed teammate now
  blocks the setup route.
- Focus Energy branch pricing: turns 8-10 and 17-18 showed that Focus Energy
  was not decorative. It made Counter/coverage and crit routes material.
- Support-status follow-up improved: turns 12-14 were the target. Cloyster used
  Toxic, then Spikes, then Explosion. I got the Spikes-then-Explosion order
  right after the status landed.
- Cash-out defense remains conditional: I preferred preserving Snorlax into
  Cloyster Explosion, while the actual line stayed. The advice must state
  whether survival depends on non-crit rolls and whether the absorber is more
  valuable than the boosted anchor.
- Damage-range pricing: turn 16 was the severe miss. Tyranitar at 52% could
  die to Nidoking Earthquake before moving; I treated it as if survival was
  safe.

## Policy Update

Add this to `PTA-058`:

```text
After support status lands on a boosting anchor, re-score the exact follow-up
order. The sequence may be status -> hazards -> cash-out, with the defending
side choosing between staying on roll-dependent survival and preserving the
anchor with an absorber.
```

Add this branch-pricing reminder:

```text
If a revealed attacker uses Focus Energy, do not price the next turn as ordinary
coverage only. Counter, crit ranges, and whether our active piece can move
before being KOed become material.
```

## Next Study Target

Run a compact 8-10 turn drill on Focus Energy / Counter / crit-route branches,
because the support-status rep exposed a new severe branch-pricing error.
