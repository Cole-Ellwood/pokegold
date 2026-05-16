# Replay Turn-Pause 040 Branch Coverage Spin Phaze - smogtours-gen2ou-931130 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-931130`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`.
The target was not only move agreement. It was whether the recommended action
actually covered the named worst branch in trap, phaze, Rapid Spin, and support
loop positions.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, count of
  broad route moves, and file size.
- The selected start was turn 5, the first broad route-move turn. Turns 5-20
  were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_039_sleep_talk_pursuit_transfer_smogtours-gen2ou-931710_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, GSC OU Houndoom:
  `https://www.smogon.com/forums/threads/houndoom-ou-revamp-qc-2-2-gp-2-2.3653682/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

Source note: the Spikes source explicitly frames Rapid Spin, phazing, pressure,
and spinblocking as a subgame. This replay tested the exact gate from the
previous miss: naming a branch is not enough if the move chosen does not
actually cover it.

## Score Summary

Scored decisions: 32 side decisions.

Top-match: 10 / 32.

Acceptable-match: 18 / 32.

Branch-coverage checks: 9 / 16 p1 decisions.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 5 p1. I saw the Raikou-vs-Golem attack/phaze
fork but missed Golem's clean Rapid Spin window on the expected switch. The
actual move removed p1's Spikes before p2 could punish.

Main improvements:

- Correctly used Zapdos pressure into poisoned Cloyster and Raikou on turns
  6-7.
- Correctly switched out of the Leech Seed / Protect loop on turn 12.
- Correctly punished the dragged-in Gengar spinblocker with Earthquake on turn
  18.
- Correctly used Double-Edge to punish the Espeon-to-Snorlax pivot on turn 20.

Main errors:

- Missed Golem's Rapid Spin window on turn 5.
- Overcalled sleep/Explosion into Exeggutor and underpriced Leech Seed +
  Protect on turns 10-11.
- Covered Lovely Kiss on turn 16 but missed that the actual branch was another
  Rapid Spin window.
- Missed Golem's Roar on turn 17 as a way to preserve itself, tax the opponent
  with Spikes, and force the spinblocker into Earthquake range.
- Overpreserved 14% Golem on turn 19 despite Spikes making future re-entry
  nearly worthless; the actual line sacked it for clean Snorlax entry.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Branch coverage |
|---|---|---|---|---|---|
| 5 | Golem 93 vs Raikou 93, Spikes both sides | p1 Earthquake; p2 switch | p1 Rapid Spin; p2 Cloyster | p1 miss, p2 top | Miss: did not price clean Spin on the switch. |
| 6 | Golem 99 vs poisoned Cloyster 71 | p1 Zapdos; p2 Surf/Toxic | p1 Zapdos; p2 Spikes | p1 top, p2 miss | Partial: switch covered Surf, not the immediate reset. |
| 7 | Zapdos vs poisoned Cloyster 65 | p1 Thunder; p2 Toxic/Raikou | p2 Raikou; p1 Thunder | both top | Hit: Thunder covered the pivot. |
| 8 | Zapdos vs Raikou 66 | p1 Golem; p2 HP punish or Thunder | p1 Snorlax; p2 Thunder miss | p1 acceptable, p2 acceptable | Hit class, but hidden special-sponge conditional should have been named. |
| 9 | Snorlax vs Raikou 72 | p1 attack; p2 Cloyster/Roar | p2 Exeggutor; p1 Double-Edge | p1 acceptable, p2 acceptable | Hit class: direct attack punished the pivot. |
| 10 | Snorlax 92 vs Exeggutor 52 | p1 Golem; p2 Sleep/Explosion | p2 Leech Seed; p1 Double-Edge | both miss | Miss: overcalled the high-commitment fork. |
| 11 | seeded Snorlax vs Exeggutor 36 | p1 switch; p2 switch/Sleep/Explosion | p2 Protect; p1 Double-Edge | both miss | Advice covered seed loop, but did not match actual expert line. |
| 12 | seeded Snorlax vs Exeggutor 58 | p1 Zapdos/Golem switch; p2 sleep/trade/switch | p1 Zapdos; p2 Psychic | p1 top, p2 miss | Hit: switch cleared Leech Seed and preserved Snorlax. |
| 13 | Zapdos 73 vs Exeggutor 64 | p1 Thunder; p2 Leech/pivot | p1 Hidden Power; p2 Protect | p1 acceptable, p2 miss | Partial: pressure move right, exact HP conditional missed. |
| 14 | Zapdos 79 vs Exeggutor 70 | p1 Hidden Power; p2 Leech/pivot | p1 HP; p2 Explosion | p1 top, p2 acceptable | Accepted trade: HP did not cover Explosion, but forced the route trade. |
| 15 | Snorlax 65 vs Snorlax 93 | p1 Self-Destruct if available, else Golem; p2 Curse/DE | p1 Golem; p2 Lovely Kiss miss | p1 acceptable, p2 miss | Hit as alternative: Golem covered the sleep attempt. |
| 16 | Golem 93 vs Snorlax 99 with Lovely Kiss revealed | p1 Cloyster sleep absorb; p2 Lovely Kiss | p1 Rapid Spin; p2 Cloyster | both miss | Miss: covered sleep but missed the Spin window. |
| 17 | Golem 99 vs poisoned Cloyster 43 | p1 Cloyster; p2 Rapid Spin/Surf | p2 Spikes; p1 Roar to Gengar | both miss | Miss: Roar was the branch-covering move. |
| 18 | Golem 100 vs Gengar 93 | p1 Earthquake; p2 coverage/switch | p2 Hidden Power; p1 Earthquake KO | p1 top, p2 acceptable | Hit: punished the spinblocker instead of clicking Spin. |
| 19 | low Golem 14 vs Espeon 93 | p1 Snorlax switch; p2 Psychic/Growth | p2 Psychic KO; p1 sacked Golem | p1 miss, p2 top | Miss: future Golem re-entry was fake because Spikes were up. |
| 20 | Snorlax 59 vs Espeon 99 | p1 Double-Edge; p2 Snorlax | p2 Snorlax; p1 Double-Edge | both top | Hit: attack covered the obvious special-wall pivot. |

## Reusable Update

Branch coverage is a separate skill from naming branches. Before locking a
move, ask:

1. What bad branch did I name?
2. Does the selected action actually improve or cover that branch?
3. If not, am I deliberately accepting the branch because the trade opens a
   stronger route?
4. Is there a support move, phaze, Spin, Rest, or sack that covers more of the
   tree than direct damage?

Turn 18 was the model: Gengar blocked Rapid Spin, so Golem did not try to Spin;
it used Earthquake and removed the spinblocker. Turn 19 was the mirror error:
I preserved a 14% Golem even though Spikes meant it had no realistic future
entry, while the actual line used it as a spacer sack.

## Next Rep

Build a compact branch-coverage regression probe from this run:

- clean Spin on a forced switch;
- Spikes reset after Spin;
- Roar into a spinblocker;
- direct attack into the spinblocker;
- low-resource sack for clean entry;
- accepting Explosion as a priced trade rather than a covered branch.
