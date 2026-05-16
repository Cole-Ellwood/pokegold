# Replay Turn-Pause 026 Hazard Spinblock Transfer - smogtours-gen2ou-934842 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934842`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: attempted fresh final-gate Explosion transfer. The intended low
exploder spot did not appear in the first 15 turns, but the replay produced a
useful hazard-control transfer segment: Toxic into CurseLax, Forretress
Spikes, Tentacruel Rapid Spin into Gengar, and poisoned Snorlax pressure.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused logs: Explosion, Self-Destruct, Snorlax, Cloyster, Forretress,
  Golem, Steelix, Gengar, Toxic, Spikes, Rapid Spin, Rest, and Curse.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.
- The helper omitted species for nicknamed Pokemon, so the public lead species
  were checked from the initial switch lines only. No future turn order was
  exposed by that check.

Local docs checked:

- `docs/pokemon_mastery/workspace/quick_tests/route_trade_final_gate_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`

Source note: the Spikes sources were more relevant than Explosion in this
actual segment: setting Spikes, blocking Rapid Spin with Gengar, and poisoning
Snorlax created the live route.

## Score Summary

Turns scored: 1-15.

Target phase: turns 2-12, from CurseLax pressure through Toxic, Forretress
Spikes, failed Rapid Spin into Gengar, and poisoned Snorlax re-entry.

Decisions scored: 30 side-decisions.

Top-match: 17 / 30.

Acceptable-match: 25 / 30.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 1.

Largest route error: turn 8.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Raikou vs Forretress lead | p1 Thunder; p2 Spikes or switch Snorlax | p1 Tentacruel; p2 Snorlax | both acceptable | p1 chose spinner/Protect scout; p2 immediately started Snorlax route. |
| 2 | Tentacruel vs Snorlax | p1 Protect/scout; p2 Curse | p1 Protect; p2 Curse | both top | Correctly found the scout into unknown Snorlax. |
| 3 | Tentacruel vs +1 Snorlax | p1 Skarmory; p2 Curse/attack | p1 Skarmory; p2 Curse | p1 top, p2 acceptable | Correctly brought the physical wall; p2 continued setup. |
| 4 | Skarmory vs +2 Snorlax | p1 Toxic; p2 Double-Edge | p1 Toxic miss; p2 Double-Edge | both top | Toxic first transferred; miss did not change policy. |
| 5 | Skarmory low vs +2 Snorlax | p1 Toxic again; p2 Double-Edge | p1 Toxic; p2 Double-Edge | both top | Correctly stayed until Snorlax was on a clock. |
| 6 | Skarmory 44 vs poisoned Snorlax | p1 Rest; p2 preserve Snorlax / go support | p2 Forretress; p1 Rest | both top | Good branch: after status, both sides reset resources rather than force damage. |
| 7 | Sleeping Skarmory vs Forretress | p1 spinner/pressure pivot; p2 Spikes | p1 Tentacruel; p2 Spikes | both top | Correctly shifted to the hazard subgame. |
| 8 | Tentacruel vs Forretress with Spikes up | p1 Rapid Spin; p2 stay or Gengar spinblock | p2 Gengar; p1 Rapid Spin immune | p1 acceptable, p2 top | I should have weighted the spinblock branch more heavily once Gengar was plausible. |
| 9 | Tentacruel vs Gengar | p1 Protect scout; p2 Thunderbolt | p1 Protect; p2 Thunderbolt | both top | Correctly scouted the Gengar attack. |
| 10 | Tentacruel vs Gengar Thunderbolt | p1 Snorlax; p2 Thunderbolt | p1 Snorlax; p2 Thunderbolt | both top | Correctly used the special sponge after the scout. |
| 11 | Snorlax vs Gengar | p1 Raikou or broad special answer; p2 Zapdos/pivot | p2 Zapdos; p1 Raikou | both top | Good double-pivot to Electric mirror. |
| 12 | Raikou vs Zapdos; poisoned Snorlax in back | p1 Thunder into switch; p2 Snorlax | p2 Snorlax; p1 Thunder | both top | Correctly punished Snorlax re-entry; poison plus damage advanced the route. |
| 13 | Raikou vs poisoned Snorlax 62 | p1 Thunder; p2 Electric pivot | p2 Raikou; p1 Thunder | both top | Correctly kept pressure; p2 preserved poisoned Snorlax. |
| 14 | Raikou mirror | both Thunder or pivot | both Thunder; p2 miss | both acceptable | Low-signal Electric mirror. |
| 15 | Raikou mirror | both Thunder or pivot | both Thunder; p2 miss | both acceptable | Low-signal Electric mirror; stopped after this. |

## Error Classes

- Final-gate target did not appear. This replay should not be counted as a
  direct transfer test for `route_trade_final_gate_probe_001`.
- Hazard-control transfer was strong: Toxic first, resource reset, Forretress
  Spikes, Tentacruel Spin attempt, Gengar spinblock, and Raikou pressure on
  poisoned Snorlax were mostly correct.
- Main miss: on turn 8, I treated Rapid Spin as the clean route and did not
  price the spinblock pivot strongly enough. The actual Gengar switch made
  Spin fail.
- Sleep-clause discipline held: sleeping Skarmory was preserved or reset by
  Rest context, not treated as inert.

## Policy Update

No route-trade policy change from this run. Add only the hazard-control
reminder: after Spikes go up, ask whether the opponent has a plausible
spinblocker before valuing Rapid Spin as successful route progress.

## Next Study Target

Run a fresh replay target for the actual final-gate Explosion spot, or build a
spinblock-transfer probe if the next replay again shifts toward hazard control.
