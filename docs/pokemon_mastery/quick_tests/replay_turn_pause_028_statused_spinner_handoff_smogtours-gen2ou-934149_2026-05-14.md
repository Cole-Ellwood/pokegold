# Replay Turn-Pause 028 Statused Spinner Handoff - smogtours-gen2ou-934149 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934149`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer check after `replay_turn_pause_027`: once the spinner
or hazard support piece is poisoned, choose between immediate Spikes / Rapid
Spin and handing off to a pressure piece that exploits the statused target.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused local logs: Spikes, Rapid Spin, Gengar, Misdreavus, Cloyster,
  Forretress, Starmie, Toxic, Thunder Wave, Body Slam, Snorlax, Raikou, Zapdos,
  Recover, and Surf.
- The selected replay had Spikes, Rapid Spin, Cloyster, Starmie, Toxic,
  Snorlax, Raikou, and Zapdos counts. The screen did not reveal turn number,
  actor, target, move order, outcome, or later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.

Local docs checked:

- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_027_spinblock_transfer_smogtours-gen2ou-934144_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/spinblock_route_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`

Source note: GSC Spikes planning is a route sequence. Statusing the spinner or
support piece is only the first part; the next move should exploit the forced
Recover, switch, Spin, or damage response rather than automatically continuing
the hazard mirror.

## Score Summary

Turns scored: target phase turns 4-16.

Decisions scored: 26 side-decisions.

Top-match: 13 / 26.

Acceptable-match: 16 / 26.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 5.

Largest route error: turn 7.

## Context Before Target Phase

- Turn 1: p1 switched Cloyster to Raikou into p2 Raikou Thunder.
- Turn 2: p1 Raikou missed Thunder; p2 Raikou Thunder paralyzed p1 Raikou.
- Turn 3: p2 switched Snorlax; p1 Raikou used Rest.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 4 | sleeping p1 Raikou vs p2 Snorlax | p1 Sleep Talk or Cloyster; p2 Curse/attack | p1 Cloyster; p2 Curse | both top | Correctly found the Snorlax route and physical answer. |
| 5 | Cloyster vs +1 Snorlax | p1 Toxic; p2 attack/setup | p2 Cloyster; p1 Toxic | p1 top, p2 miss | Toxic hit the support piece, not Snorlax; I missed p2 preserving Snorlax through Cloyster. |
| 6 | Cloyster mirror; p2 Cloyster poisoned | p1 Spikes; p2 Spikes/Rapid Spin | both Spikes | both top | Setting the layer before the handoff was correct because no layer existed yet. |
| 7 | Cloyster mirror; both sides Spikes, p2 Cloyster poisoned | p1/p2 Spin or continue the hazard mirror | p1 Zapdos; p2 Raikou | both miss | Main miss: after status and Spikes, both sides handed off to pressure pieces instead of continuing the support mirror. |
| 8 | p1 Zapdos vs p2 Raikou, both sides Spikes | p1 attack; p2 Thunder | p1 Raikou; p2 Thunder | p1 miss, p2 top | p1 preserved Zapdos by absorbing Electric pressure with sleeping RestTalk Raikou. |
| 9 | sleeping p1 Raikou vs p2 Raikou | p1 Sleep Talk if available or switch; p2 Thunder | p2 Snorlax; p1 Sleep Talk -> Rest | p1 acceptable, p2 miss | Sleeping RestTalk Raikou was still an active resource; p2 used Snorlax to resume pressure. |
| 10 | sleeping p1 Raikou vs p2 Snorlax | p1 physical answer; p2 attack | p1 Tyranitar; p2 Body Slam | both acceptable | The handoff chain kept using role pieces rather than returning to hazards. |
| 11 | Tyranitar vs Snorlax | p1 Rock Slide/Screech; p2 Earthquake | p1 Curse; p2 Earthquake | p1 miss, p2 top | I underpriced p1 using Tyranitar as a boosted phaze/pressure piece. |
| 12 | +1 Tyranitar vs Snorlax | p1 switch or attack; p2 Earthquake/Curse | p2 Curse; p1 Rock Slide | p1 miss, p2 acceptable | p1 kept pressure instead of abandoning the matchup after one Earthquake. |
| 13 | +1 Tyranitar vs +1 Snorlax | p1 Rock Slide; p2 Earthquake | p2 Earthquake; p1 Roar to Heracross | p1 miss, p2 top | Phazing with Spikes was the real endpoint of the handoff. |
| 14 | low Tyranitar vs Heracross | p1 Zapdos; p2 attack | p2 Raikou; p1 Zapdos | p1 top, p2 miss | p1 preserved low Tyranitar; p2 doubled back to Electric pressure. |
| 15 | Zapdos vs Raikou | p1 Raikou or special sponge; p2 Thunder | p1 Raikou; p2 Thunder | both top | Correct pressure absorption under Spikes. |
| 16 | sleeping p1 Raikou vs p2 Raikou | p1 Sleep Talk/special answer; p2 Snorlax | both Snorlax | p1 miss, p2 top | Both sides kept handing off through pressure pieces rather than immediate hazard resets. |

## Error Classes

- The previous lesson only partially transferred. I correctly valued Toxic and
  Spikes before the handoff, but on turn 7 I still treated the position as a
  hazard mirror when both players moved to pressure pieces.
- The stronger rule is: statusing a spinner or support piece is not the payoff.
  The payoff is the forced switch, forced recovery, worse re-entry, or pressure
  handoff that status makes possible.
- No severe blunder was counted because the missed hazard handoffs did not
  immediately lose an irreplaceable route, but they were real route errors.

## Policy Update

After Toxic or another status lands on the opposing spinner / setter, ask:

1. Has our hazard or removal job already been delivered this cycle?
2. Which pressure piece now punishes the statused support: Snorlax, Electric,
   Tyranitar, phazer, trapper, or Explosion user?
3. Does staying in only let the support mirror continue while the opponent
   escapes the status cost?
4. If we hand off, what happens to the next Rapid Spin, Recover, Rest, or
   forced switch?

## Next Study Target

Build a compact regression from this turn-7 miss: six scenarios where a
spinner / setter is statused and a support mirror tempts Spikes or Rapid Spin,
but the right answer may be a pressure handoff, phaze, direct attack, or
delayed reset.
