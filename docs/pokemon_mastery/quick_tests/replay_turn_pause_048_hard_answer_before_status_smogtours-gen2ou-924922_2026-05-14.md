# Replay Turn-Pause 048 Hard Answer Before Status - smogtours-gen2ou-924922 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-924922`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`forced_switch_pivot_damage_probe_001_2026-05-14.md`. The target was the same
checklist as `replay_turn_pause_047`, with a hard stop after two meaningful
misses:

```text
status before hazard / hazard after clock / damage before setup /
coverage into Ground-Steel pivot / recurring answer before cash-out
```

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-924922`.
- The selected start was turn 1. Turns 1-3 were answered before reveal.
- The run stopped after turn 3 because turns 2 and 3 produced meaningful
  checklist misses.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_047_special_wall_pivot_ladder_transfer_smogtours-gen2ou-925686_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/forced_switch_pivot_damage_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Cloyster source supports Toxic as a way to wear down Curse
Snorlax, but also frames Explosion as a trade after Spikes. The replay added
the missing exception: if Spikes are already delivered and a hard answer is
clean, the hard answer can come before the status clock. The lead-analysis
source also supports treating lead Snorlax and Electrics as branch-selection
positions, not one fixed script.

## Score Summary

Scored decisions: 6 side decisions.

Top-match: 2 / 6.

Acceptable-match: 4 / 6.

Classification hits: 3 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 2 p2. I chose Toxic from Cloyster after Spikes
were up, but the actual line preserved Cloyster and used Skarmory as the clean
recurring answer to +1 Snorlax.

Main improvement:

- The turn-1 opening was framed correctly as Snorlax progress versus Cloyster
  hazard progress. Cloyster set Spikes and Snorlax used Curse.

Main errors:

- Turn 2 p2: overapplied the Toxic-before-hazard rule. Since Spikes were
  already down and Skarmory had clean entry into known Curse + Double-Edge,
  the recurring answer came before status.
- Turn 3 p2: assumed the hard answer would immediately Toxic or Whirlwind.
  Actual Skarmory used Curse, counter-setting while Snorlax was not yet showing
  coverage.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 1 | Snorlax lead vs Cloyster lead | p1 Lovely Kiss if available, Curse fallback; p2 Spikes | p2 Spikes; p1 Curse | p1 acceptable, p2 top | Hazard progress plus setup progress. |
| 2 | +1 Snorlax 100 vs Cloyster 100, Spikes on p1 | p1 Double-Edge; p2 Toxic | p2 switched Skarmory; p1 Double-Edge | p1 top, p2 miss | Recurring hard answer before status. |
| 3 | +1 Snorlax 100 vs Skarmory 80 | p1 coverage if available; p2 Whirlwind or Toxic | p2 Curse; p1 Double-Edge | p1 acceptable, p2 miss | Counter-setup with hard answer. |

## Reusable Lessons

The status-before-hazard rule needs a clean-answer exception:

```text
If the support action is already delivered and a recurring hard answer can
enter without losing the route, use the answer before adding status.
```

Skarmory showed a second branch: after entering as the hard answer, the move
may be counter-setup, not just Toxic or Whirlwind. If the attacker has only
shown resisted physical damage, the wall can use setup to improve the mirror
before phazing becomes necessary.

## Next Rep

Construct a compact regression:

- Cloyster has already set Spikes versus +1 Snorlax: switch Skarmory before
  Toxic if Skarmory is clean.
- Skarmory versus +1 Snorlax with no coverage revealed: Curse can be a
  counter-setup move before Whirlwind.
- If Snorlax reveals Fire Blast or Thunder, abandon counter-setup and use the
  coverage-pivot rule.
