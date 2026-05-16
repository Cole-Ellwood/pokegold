# Replay Turn-Pause 029 Spin vs Setup Handoff - smogtours-gen2ou-935409 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935409`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: fresh transfer check after `statused_spinner_handoff_probe_001`.
The intended target was a statused spinner or setter, but the replay produced a
sharper boundary: when a spinner enters, blocking Rapid Spin is not always the
route. A pressure handoff may deliberately allow Spin if the handoff creates a
stronger route, such as Curse Snorlax.

Contamination control:

- The replay was not referenced in local docs before this run.
- A local candidate screen checked only broad move and Pokemon-name counts
  across unused local logs: Spikes, Rapid Spin, Gengar, Misdreavus, Cloyster,
  Forretress, Starmie, Toxic, Thunder Wave, Body Slam, Snorlax, Raikou, Zapdos,
  Recover, and Surf.
- The selected replay had Spikes, Rapid Spin, Toxic, Cloyster, Forretress,
  Gengar, Snorlax, and Zapdos counts. The screen did not reveal turn number,
  actor, target, move order, outcome, or later branches.
- Turns were revealed one at a time with the local helper after answers were
  frozen.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_028_statused_spinner_handoff_smogtours-gen2ou-934149_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Playing with Spikes in GSC forum thread:
  `https://www.smogon.com/forums/threads/playing-with-spikes-in-gsc-qc-2-2-gp-2-2-done.3475184/post-4501581`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`

Source note: the GSC Spikes source says Starmie can be worn down by repeatedly
forcing it with a Sleep Talk Electric, and the same structure generalizes:
the spinner's presence asks whether to block, punish, or use the spin turn to
start the route that the hazard position enabled. Retention is not a command to
block every Spin.

## Score Summary

Turns scored: target phase turns 17-26.

Decisions scored: 18 side-decisions. Sleeping no-action decisions where the
chosen move was not logged were excluded.

Top-match: 5 / 18.

Acceptable-match: 8 / 18.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 17.

Largest route error: turn 19.

## Context Before Target Phase

- Turns 1-6: p1 Jynx led into p2 Exeggutor. p2 switched Shuckle into Thief.
  p1 brought Gengar into Shuckle Toxic. Gengar pressured Shuckle with Ice
  Punch, Thunder, and Dynamic Punch until Shuckle used Rest.
- Turn 7: p1 switched Cloyster as p2 switched Zapdos.
- Turns 8-10: p1 and p2 maneuvered into p1 Zapdos vs p2 Forretress. p2 set
  Spikes; p1 Zapdos hit Forretress with Thunder; p2 Forretress landed Toxic on
  Zapdos.
- Turns 11-16: p1 Zapdos kept pressure, Rested, used Sleep Talk once, then p1
  switched Cloyster into p2 Snorlax Double-Edge.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 17 | p1 Cloyster 60 vs p2 Snorlax 69; p1 side Spikes | p1 Rapid Spin; p2 Double-Edge | p2 Zapdos; p1 Spikes | both miss | I overvalued clearing our layer; actual first put a layer on p2's side before pressure handoff. |
| 18 | p1 Cloyster 66 vs p2 Zapdos 66; both sides Spikes | p1 switch to Electric/Ground answer; p2 Electric attack | p2 Donphan; p1 Snorlax | p1 miss, p2 miss | p2 entered the spinner; p1 chose Snorlax as the pressure handoff. |
| 19 | p1 Snorlax 94 vs p2 Donphan 94; both sides Spikes | p1 switch Gengar to block Spin; p2 Rapid Spin | p2 Rapid Spin; p1 Curse | p1 miss, p2 top | Main error: blocking Spin was plausible, but Snorlax setup was the real handoff and accepted losing the layer. |
| 20 | +1 p1 Snorlax 96 vs p2 Donphan 99; p1 side Spikes, p2 side clear | p1 attack; p2 Earthquake/Roar | p2 Forretress; p1 Curse | p1 acceptable, p2 miss | The setup route continued after Spin resolved; p2 went to support containment. |
| 21 | +2 p1 Snorlax 100 vs p2 Forretress 51 | p1 Earthquake; p2 Toxic/Explosion | p2 Defense Curl; p1 Earthquake | p1 top, p2 miss | I found the attack, but missed Forretress using Defense Curl as containment. |
| 22 | +2 p1 Snorlax 100 vs p2 Forretress 34 def+1 | p1 Earthquake; p2 Toxic | p2 Toxic; p1 Earthquake | both top | Correct: Forretress put Snorlax on a poison clock while Snorlax kept attacking. |
| 23 | +2 poisoned p1 Snorlax 100 vs p2 Forretress 13 | p1 Earthquake; p2 switch/Explosion | p2 Rest; p1 Earthquake | p1 top, p2 miss | I missed Rest Forretress as the defensive reset after Toxic. |
| 24 | +2 poisoned p1 Snorlax 94 vs sleeping p2 Forretress 82 | p1 Earthquake | p1 Double-Edge; p2 asleep | p1 acceptable | Wrong coverage, but still direct pressure during the sleep window. |
| 25 | +2 poisoned p1 Snorlax 79 vs sleeping p2 Forretress 67 | p1 Earthquake | p1 Curse; p2 asleep | p1 miss | I wanted damage; actual used the sleep turn to increase the setup route. |
| 26 | +3 poisoned p1 Snorlax 60 vs p2 Forretress 73 waking | p1 attack; p2 no-action or switch | p2 Defense Curl; p1 Rest | both miss | I underpriced the poison clock and Rest timing after the setup handoff. |

## Error Classes

- The handoff checklist improved the question but overcorrected the answer. I
  saw Donphan's Rapid Spin and wanted Gengar, but the stronger line was to let
  Spin happen while Snorlax used the turn to Curse.
- New boundary: hazard retention is not automatically more important than the
  route created by the hazard position. If the pressure piece gets a setup,
  Rest, phaze, KO, or forced switch route from the spin turn, current Spin may
  be an acceptable cost.
- Secondary miss: after committing to Curse Snorlax, I underpriced the poison
  clock and Forretress Rest / Defense Curl containment.

## Policy Update

When a spinner enters after our hazard pressure is live, ask three gates before
auto-blocking Spin:

1. If Spin resolves, what route do we get this turn: Curse, attack, phaze,
   Rest, Explosion, status, or a forced switch?
2. Is preserving the current layer better than starting that route?
3. If the pressure handoff starts, what contains it: Toxic, Rest, Defense
   Curl, phazing, Explosion, or a pivot?

## Next Study Target

Build a compact spin-vs-setup handoff regression from turn 19: six scenarios
where a spinner can remove Spikes, but the active pressure piece may prefer
setup, attack, Rest, phaze, or sacrifice over spinblocking.
