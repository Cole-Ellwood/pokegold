# Replay Turn-Pause 041 Branch Coverage Transfer - smogtours-gen2ou-931101 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-931101`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`branch_coverage_spin_phaze_probe_001_2026-05-14.md`. The target was to score
whether the chosen action covered the named branch, not just whether the route
was described in prose.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs, recent exposed candidates, and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected start was turn 54. Turns 54-60 were answered before reveal, then
  the run stopped because the named-punish-but-uncovered-action miss recurred.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_040_branch_coverage_spin_phaze_smogtours-gen2ou-931130_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Golem:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`

Source note: the Spikes article supports treating Spin, spinblocking, phazing,
Pursuit, and pressure as one route subgame. This replay added a sharper
distinction: identifying the opponent's next pivot is not enough if the chosen
move does not punish or cover that pivot.

## Score Summary

Scored decisions: 14 side decisions.

Top-match: 5 / 14.

Acceptable-match: 8 / 14.

P1 branch-coverage checks: 4 / 7.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 55 p1. I overfocused on removing p1-side
Spikes and missed Toxic into Starmie, which covered the spinner/recovery branch
before Starmie could begin looping.

Repeated error that stopped the run:

- Turn 59: named the Snorlax/Raikou pivot, then chose Thunderbolt instead of
  the Tyranitar double that covered Snorlax.
- Turn 60: named Misdreavus as a possible Snorlax-preservation pivot, then
  chose Dynamic Punch, which does nothing into Misdreavus.

Main improvements:

- Turn 56: identified that Zapdos pressure was a serious alternative to
  Gengar spinblock, and the actual Zapdos switch covered Starmie's Substitute.
- Turn 58: after Gengar blocked Rapid Spin, correctly used Thunderbolt to keep
  Starmie from freely Recovering or spinning.
- The run stopped at the correct time instead of drifting into generic
  midgame after the target error repeated.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Branch coverage |
|---|---|---|---|---|---|
| 54 | LK/EQ Snorlax-like active vs Skarmory with Spikes | p1 switch Tyranitar/Zapdos; p2 Whirlwind/Toxic | p1 Gengar, p2 Whirlwind dragged Cloyster | p1 acceptable, p2 top | Fail: switching preserved Snorlax but did not cover Whirlwind. |
| 55 | poisoned Cloyster vs Skarmory | p1 Rapid Spin if available; p2 Whirlwind or Misdreavus | p2 Starmie; p1 Toxic | both miss | Hit for named branch, miss for actual branch: Toxic was the Starmie-covering move. |
| 56 | poisoned Cloyster vs poisoned Starmie | p1 Gengar preferred, Zapdos alternative; p2 Rapid Spin | p1 Zapdos; p2 Substitute | p1 acceptable, p2 miss | Hit only by alternative: Zapdos covered Substitute better than Gengar. |
| 57 | Zapdos vs poisoned Starmie behind Substitute | p1 Thunder; p2 Recover/pivot | p1 Gengar; p2 Rapid Spin blocked | both miss | Branch identification miss: Rapid Spin was the key branch. |
| 58 | Gengar vs poisoned Starmie behind Substitute | p1 Thunderbolt; p2 Surf/Recover/pivot | p2 Recover; p1 Thunderbolt | both top | Hit: Gengar kept the block role while Thunderbolt punished Recover/Sub. |
| 59 | Gengar vs poisoned Starmie | p1 Thunderbolt; p2 Snorlax/Raikou pivot | both switched: p1 Tyranitar, p2 Snorlax | p1 miss, p2 top | Fail: I named Snorlax pivot but did not choose the double that covered it. |
| 60 | Tyranitar vs Snorlax 60 | p1 Dynamic Punch; p2 Skarmory/Misdreavus | p2 Misdreavus; p1 Dynamic Punch immune | p1 top by move, p2 acceptable | Fail: exact move matched, but it did not cover the named Misdreavus branch. |

## Reusable Update

For branch-heavy advice, split the turn into two scores:

1. Branch identification: did I name the opponent's live route?
2. Branch coverage: does my selected move or switch actually cover that route?

Turns 59 and 60 show why this matters. On turn 59, Thunderbolt into Starmie
looked active but did not cover the Snorlax pivot I had named. On turn 60,
Dynamic Punch matched the actual move but failed the branch-coverage test
because Misdreavus was immune and had already been named as a likely pivot.

The corrected move selection step is:

```text
If my top move does not affect one of my named serious branches, either
re-rank the move, explain why accepting that branch is worth it, or remove the
branch from the serious list.
```

## Next Rep

Run a constructed three-prompt micro-probe for "named pivot but move does not
hit it":

- Starmie to Snorlax pivot after Spin is blocked;
- Snorlax to Misdreavus pivot into Fighting/Ground coverage;
- Skarmory/Forretress pivot into Fire Blast versus non-Fire midground.
