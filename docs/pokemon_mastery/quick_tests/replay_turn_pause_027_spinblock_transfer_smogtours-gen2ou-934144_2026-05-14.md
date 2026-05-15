# Replay Turn-Pause 027 Spinblock Transfer - smogtours-gen2ou-934144 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934144`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer check after `spinblock_route_probe_001`: when Spikes
are up and a spinner is active, name the Ghost/spinblock branch before treating
Rapid Spin as clean progress.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused local logs: Spikes, Rapid Spin, Gengar, Misdreavus, Cloyster,
  Forretress, Starmie, Tentacruel, Golem, Tyranitar, Pursuit, Toxic, Roar, and
  Whirlwind.
- The selected replay had Spikes, Rapid Spin, Gengar, Forretress, Cloyster,
  and Starmie counts, but the screen did not reveal turn number, actor, target,
  move order, outcome, or later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.

Local docs checked:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_026_hazard_spinblock_transfer_smogtours-gen2ou-934842_2026-05-14.md`
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

Source note: the main GSC Spikes source made the target branch explicit:
Gengar and Misdreavus are the available spinblockers, but Starmie, Cloyster,
and Forretress pressure that map differently. The replay then tested the
spinner-side version: remove hazards when the spinblock branch is priced, not
because Spin is assumed safe.

## Score Summary

Turns scored: target phase turns 4-12.

Decisions scored: 18 side-decisions.

Top-match: 9 / 18.

Acceptable-match: 14 / 18.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 5.

Largest route error: turn 12.

## Context Before Target Phase

- Turn 1: p2 Zapdos used Thunder into p1 Snorlax; p1 Snorlax used
  Double-Edge.
- Turn 2: p2 Zapdos missed Thunder; p1 Snorlax used Double-Edge.
- Turn 3: p2 switched Forretress into p1 Snorlax Double-Edge.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 4 | Snorlax 69 vs Forretress 88, no hazards | p1 switch to pressure Forretress; p2 Spikes | p1 Zapdos; p2 Spikes | both top | Correctly expected the hazard turn and pressure pivot. |
| 5 | Zapdos 100 vs Forretress 94, p1 side Spikes | p1 Thunder; p2 switch to Snorlax/Electric sponge | p1 Cloyster; p2 Snorlax | p1 acceptable, p2 top | p1 chose to enter the hazard subgame immediately instead of only attacking the setter. |
| 6 | Cloyster 94 vs Snorlax 100 | p1 Toxic or Spikes; p2 attack/setup | p2 Starmie; p1 Spikes | p1 acceptable, p2 miss | I underweighted the immediate spinner entry after Cloyster came in. |
| 7 | Cloyster 99 vs Starmie 100, both sides Spikes | p1 Toxic or Ghost branch if available; p2 Rapid Spin | p1 Starmie; p2 Rapid Spin | p1 acceptable, p2 top | p2 removed the layer; p1 chose spinner mirror rather than status or revealed blocker. |
| 8 | Starmie mirror; p1 side Spikes, p2 side clear | p1 Rapid Spin while naming possible Gengar branch; p2 Ghost if available, otherwise status | p1 Rapid Spin; p2 Thunder Wave | p1 top, p2 acceptable | Transfer held: Spin was chosen, but not treated as clean if a Ghost entered. Actual branch let Spin resolve. |
| 9 | p1 paralyzed Starmie vs p2 Starmie, no hazards | p1 switch to pressure; p2 switch to Snorlax/Forretress | p2 Snorlax; p1 Psychic | p1 miss, p2 top | I overpreserved the paralyzed spinner; actual used Psychic chip before leaving. |
| 10 | p1 paralyzed Starmie vs Snorlax 87 | p1 Cloyster/physical answer; p2 Double-Edge or Curse | p1 Cloyster; p2 Double-Edge | both top | Correctly returned to the Snorlax answer. |
| 11 | Cloyster 74 vs Snorlax 89, no hazards | p1 Spikes; p2 Starmie or preserve | p2 Starmie; p1 Toxic | p1 acceptable, p2 top | Toxic on the spinner was stronger than resetting Spikes into immediate removal. |
| 12 | Cloyster 80 vs poisoned Starmie 100, no hazards | p1 Spikes; p2 Recover/status/switch | p1 Snorlax; p2 Surf | both miss | Main new error: after poisoning the spinner, handoff pressure can outrank immediate Spikes. |

## Error Classes

- Spinblock branch transfer improved. On turn 8, Rapid Spin was selected only
  after naming the possible Gengar branch and the need to punish it if it
  entered.
- The next miss moved one step later in the chain: after Starmie was poisoned,
  I wanted to set Spikes immediately, while the expert line used Snorlax
  pressure to exploit the poisoned spinner before resetting hazards.
- No hidden-information error was counted because the broad Gengar count was
  treated only as a candidate-screened prior, not as a public fact.

## Policy Update

Add a second-stage hazard-control reminder: once the spinner is poisoned or
otherwise pressured, do not automatically set Spikes. Ask whether a handoff to
Snorlax, Raikou, Zapdos, Tyranitar, or another pressure piece forces the
spinner to switch, Recover, or lose HP before the next hazard reset.

## Next Study Target

Run a fresh unseen replay segment where a poisoned or statused spinner faces a
support handoff. Score whether the next move is Spikes, Rapid Spin, direct
pressure, or a switch to the pressure piece.
