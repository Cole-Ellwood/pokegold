# Replay Turn-Pause 055 Low Cloyster Preserve Ghost Pivot - smogtours-gen2ou-922579 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-922579`.

Mode: spectator-public vanilla GSC replay practice. The p1 lead species was
read only from the public pre-turn-1 switch line because the replay used a
custom nickname.

Selected measurable action: fresh transfer after
`hazard_loop_spin_window_probe_001_2026-05-14.md`. The target was hazard-loop
Spin windows after support-cash-out threats. The replay instead sharpened the
nearby boundary: even low Cloyster is not forced to explode if Toxic,
preservation, or a Ghost pivot changes the route first.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- The selected replay was the next fresh metadata-only candidate:
  `smogtours-gen2ou-922579`, a 68-turn Gen 2 OU replay.
- Only public pre-turn-1 switch lines were inspected to map p1's lead nickname
  to Zapdos.
- Turns 1-6 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/hazard_loop_spin_window_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Cloyster source emphasizes that Cloyster's value is not only
Spikes plus Explosion; its fourth slot and team context change whether Toxic,
Surf, Rapid Spin, Explosion, or preservation is the route move.

## Score Summary

Scored decisions: 12 side decisions.

Top-match: 4 / 12.

Acceptable-match: 7 / 12.

Classification hits: 6 / 12.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 1 p1. I kept Zapdos in to Thunder, while the
actual line used Cloyster as the Snorlax Double-Edge absorber immediately.

Main improvement:

- Turn 2 correctly identified Spikes before cash-out.
- Turn 4 correctly expected Snorlax's side to preserve Snorlax with a Ghost or
  other absorber if Explosion was likely.

Main errors:

- Turn 1 p1: again missed the immediate lower-value Cloyster absorber that
  preserves Zapdos.
- Turn 3 p1: overcalled Explosion from 48% Cloyster. The actual line tried
  Toxic first, despite the miss and incoming Double-Edge.
- Turn 4 p1: overcalled Explosion again from 23% Cloyster. The actual line
  preserved Cloyster and switched Gengar while the opponent switched
  Misdreavus.
- Turn 5 p1: reduced Gengar's options to Thunder/Hypnosis/Explosion pressure
  and missed Thief as the Ghost-vs-Ghost route move.
- Turn 6 p1: stayed too active with Gengar in my branch map; the actual line
  handed to Raikou as both sides left the Ghost matchup.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | Zapdos vs Snorlax | p1 Thunder; p2 Double-Edge or LK | p1 Cloyster; p2 Double-Edge | p1 miss, p2 top | Preserve Zapdos with a lower-value Cloyster absorber. |
| 2 | Cloyster 72 vs Snorlax | p1 Spikes; p2 leave or Double-Edge | p1 Spikes; p2 Double-Edge | p1 top, p2 acceptable | Spikes before cash-out transferred. |
| 3 | Cloyster 48 vs Snorlax | p1 Explosion; p2 absorber switch | p1 Toxic miss; p2 Double-Edge | both miss | Low Cloyster can still try Toxic before boom. |
| 4 | Cloyster 23 vs Snorlax | p1 Explosion; p2 Ghost/absorber | p1 Gengar; p2 Misdreavus | p1 miss, p2 top | Both sides preserved the central pieces through Ghost pivots. |
| 5 | Gengar 100 vs Misdreavus 94 | p1 Thunder/Hypnosis pressure; p2 Thunder/status | p1 Thief; p2 Thunderbolt | p1 acceptable, p2 top | Thief can be the Ghost matchup progress move. |
| 6 | Gengar 83 vs Misdreavus 70 | p1 continue pressure; p2 pivot acceptable | both switched Raikou | p1 miss, p2 acceptable | After item/progress, handoff can beat forcing the Ghost mirror. |

## Reusable Lessons

Low Cloyster is not automatically spent. The cash-out threshold depends on the
route job still available: Toxic into Snorlax, preserving Zapdos, preserving
Snorlax from Explosion, stealing Leftovers in the Ghost matchup, or forcing an
Electric handoff can all beat immediate Explosion.

The opponent can preserve the target and the exploder can preserve itself on
the same turn. Turn 4 looked like a clean Explosion gate, but both sides
switched: Gengar for p1 and Misdreavus for p2.

Ghost matchups are not only Thunder or Explosion. Thief can be the concrete
progress move when removing Leftovers or item utility changes the later
spinblock, wall, or Explosion map.

## Source-To-Policy Extraction

Trigger:
  Cloyster is low after setting Spikes, a valuable Snorlax is active, and
  Ghosts or other absorbers are plausible.

Default:
  Rank Explosion against Toxic, preservation, Spin, direct damage, and Ghost
  pivot. Boom only when the trade opens a named route and the other support
  jobs are weaker.

Exceptions:
  Explosion rises when Cloyster cannot re-enter or act, the active target is
  the route blocker, the absorber is not available, or status/preservation does
  not change the route.

Worst branch:
  The advisor treats low HP as permission to boom, misses a support move or
  double switch, and loses the chance to preserve both the route piece and the
  one-time trade.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  local Explosion damage, Ghost immunity, Spikes entry timing, Toxic behavior,
  and item/Thief mechanics.

Drill:
  Build a four-prompt regression: Zapdos into Snorlax chooses Cloyster
  absorber; 48% Cloyster chooses Toxic before boom; 23% Cloyster preserves with
  Gengar into Misdreavus; Gengar chooses Thief as progress.

## Next Rep

Run a fresh replay transfer focused on low-support preservation before
cash-out. The regression artifact is
`quick_tests/low_support_preserve_before_cashout_probe_001_2026-05-14.md`.
