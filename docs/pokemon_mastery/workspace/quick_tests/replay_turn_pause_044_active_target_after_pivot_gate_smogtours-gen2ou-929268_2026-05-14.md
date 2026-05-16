# Replay Turn-Pause 044 Active Target After Pivot Gate - smogtours-gen2ou-929268 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-929268`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_043_named_pivot_gate_transfer_smogtours-gen2ou-930771_2026-05-14.md`.
The target was four p1 decisions with two forced checks:

```text
Named pivot:
Selected action affects pivot? yes/no
After that, is active target still the bigger branch? yes/no
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-929268`.
- Turn 2 was quarantined because a header check accidentally showed p2's first
  turn-2 action line. The scored run starts at turn 3 after turn 2 was fully
  revealed.
- Turns 3-6 were answered before reveal, then the run stopped after four p1
  decisions.

Local docs checked:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/study_roadmap_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/named_pivot_coverage_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_043_named_pivot_gate_transfer_smogtours-gen2ou-930771_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`
- Smogon Forums, GSC OU Discussion Thread page 3:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/page-3`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

Source note: the useful external reminder was not a new romhack mechanic. GSC
sources keep emphasizing route-making pressure: phazing and prediction force
entry damage, Electrics can either attack, Roar, or double based on the likely
response, and Gengar/Pursuit/Explosion interactions make role ordering matter.
This replay tests whether that reminder changes the move choice after a pivot
has been named.

## Score Summary

Scored decisions: 8 side decisions.

Top-match: 4 / 8.

Acceptable-match: 6 / 8.

Branch-ordering checks: 5 / 8.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 3 p2. I treated Zapdos's active attack into
Skarmory as the bigger branch, but the revealed Raikou response made the
Snorlax double more valuable.

Main improvement:

- The named-pivot gate did not collapse into "always hit the pivot." The
  answers usually asked whether the active target was still the bigger branch.

Main errors:

- Turn 3 p2: missed that Zapdos attacking Skarmory was easy to cover with the
  already revealed Raikou, so the Snorlax double was the higher-value branch.
- Turn 4 p2: overcorrected into the Zapdos double. Snorlax could make progress
  with Curse into the expected Skarmory response, so the active progress move
  was enough.
- Turn 5 p1: missed the side-known Misdreavus pivot. From spectator-public
  state, Whirlwind was still a defensible anti-Curse route, but it was not the
  player-side best move.
- Turn 6 p1: chose Perish Song pressure from Misdreavus rather than the
  player's double to Skarmory. This was not a severe blunder, but it did not
  match the expert's information set or line.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Forced check |
|---|---|---|---|---|---|
| 3 | Skarmory 80 vs Zapdos 100 | p1 switch Raikou; p2 Thunder / attack | p2 switched Snorlax; p1 switched Raikou | p1 top, p2 miss | Named Snorlax pivot. Raikou does not affect it; I judged active Zapdos bigger, but the pivot was real. |
| 4 | Raikou 100 vs Snorlax 100 | p1 switch Skarmory; p2 switch Zapdos | p1 switched Skarmory; p2 Curse | p1 top, p2 acceptable | Named Zapdos pivot. Skarmory does not affect it, but active Snorlax was bigger for p1. For p2, Curse made progress through the expected check. |
| 5 | Skarmory 86 vs +1 Snorlax 100 | p1 Whirlwind; p2 Double-Edge | p1 switched Misdreavus; p2 Double-Edge | p1 acceptable, p2 top | Named Zapdos pivot. Whirlwind covers the active setup and can cover a switch; side-known Ghost pivot was stronger. |
| 6 | Misdreavus 100 vs +1 Snorlax 100 | p1 Perish Song; p2 switch Zapdos | both switched: p1 Skarmory, p2 Zapdos | p1 miss, p2 top | Named Zapdos pivot. Perish Song would affect the switch, but the player-side line used a double instead. |

## Reusable Update

After the pivot gate, split active-target pressure into two classes:

1. Active attack that only hits the current foe.
2. Active progress move that still improves the board through the expected
   response.

The second class can beat a double-switch temptation. In this replay, Zapdos
attacking Skarmory was easy for Raikou to answer, so p2 doubled to Snorlax.
One turn later, Snorlax did not need the immediate Zapdos double because Curse
improved through the expected Skarmory response and kept the Snorlax route
live.

## Next Rep

Build a short pivot-progress regression:

- active attack is too easy to cover, so double;
- active setup/status improves through the expected check, so do not double;
- phazing/Perish Song covers both stay and pivot;
- side-known own-team answer beats the spectator-public generic answer.
