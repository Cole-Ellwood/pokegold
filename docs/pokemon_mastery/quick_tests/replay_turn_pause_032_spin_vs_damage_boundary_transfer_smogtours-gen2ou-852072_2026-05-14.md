# Replay Turn-Pause 032 Spin vs Damage Boundary Transfer - smogtours-gen2ou-852072 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-852072`.

Tournament source: Smogon GSC OU Global Championship 2025 Round 3,
`https://www.smogon.com/forums/threads/gsc-ou-global-championship-2025-round-3.3766549/`.

Mode: spectator public, semi-blind limited-count candidate-screened.

Purpose: fresh transfer check after `spin_vs_damage_boundary_probe_001`: with
Starmie and Cloyster active in a live hazard war, choose between direct damage,
Rapid Spin, status, support handoff, and phazing without carrying the previous
turn's answer forward.

Contamination control:

- The replay ID was not referenced in local Pokemon mastery docs before this
  run.
- `smogtours-gen2ou-850459` was rejected before use because an exact web
  search exposed team-sheet snippets. No turn-pause score was taken from it.
- The selected candidate was screened only for broad counts of Spikes, Rapid
  Spin, Starmie, and Cloyster across raw logs. I did not screen for Ghost,
  Gengar, Misdreavus, Explosion, or team-sheet data.
- The screen did not reveal turn number, actor, target, move order, outcome, or
  later branches.
- The raw log was revealed one turn at a time with
  `tools/pokemon_mastery/replay_turn_pause.py`; answers were frozen before
  each reveal.
- The public pre-turn-1 switch lines were inspected because the helper can omit
  species names for nicknamed active Pokemon. No future turn events were
  inspected that way.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_031_hazard_pressure_taxonomy_transfer_smogtours-gen2ou-866835_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/spin_vs_damage_boundary_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/hazard_pressure_move_taxonomy_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon GSC OU Global Championship 2025 Round 3:
  `https://www.smogon.com/forums/threads/gsc-ou-global-championship-2025-round-3.3766549/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Discussion Thread:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`
- Smogon GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`

Source note: the Cloyster source frames Surf and Toxic as real hazard-war tools:
Surf deters some Rapid Spin users and common Explosion absorbers, while Toxic
pressures Starmie and opposing Cloyster. The replay transfer showed the same
idea in motion: Starmie sometimes clears hazards repeatedly while poison handles
Cloyster, but once damage actually removes the setter/spinner, Surf becomes
the route-converting move.

## Score Summary

Target phase: turns 21-34.

Decisions scored: 27 side-decisions. Turn 34 p2 was unscored because Cloyster
fainted before acting.

Top-match: 13 / 27.

Acceptable-match: 17 / 27.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0, with the caveat that this remains semi-blind due to
limited count screening.

Earliest meaningful target error: turn 21.

Largest target errors: turns 33-34, where I failed to switch from repeated
Rapid Spin to Surf at the exact KO threshold.

## Context Before Target Phase

- p1 Zapdos took early pressure, used Rest, and showed Sleep Talk.
- p1 switched already-sleeping Zapdos into Exeggutor's Sleep Powder on turn 9,
  preserving Starmie from sleep for the later hazard war.
- p1 Snorlax later took Sleep Powder and revealed Sleep Talk; this was a real
  exception to the default "switch the sleeper out" branch because Sleep Talk
  created Curse and Double-Edge pressure.
- p1 eventually preserved the low sleeping Snorlax by switching Tyranitar into
  Exeggutor's Psychic on turn 16.
- By turn 21, p1 had Starmie unrevealed in back, p1 Cloyster unrevealed, p2
  Cloyster unrevealed, and no hazards had yet been established.

## Target Turn Notes

### Turn 21

Public state: p1 sleeping Snorlax at 28% vs p2 Cloyster at 100%, no hazards.

Frozen answers: p1 switch Starmie to contest hazards; p2 Spikes.

Actual: p1 switched Cloyster; p2 used Surf.

Grade: p1 acceptable, p2 miss. I saw the support handoff but picked Starmie too
early; p2 used direct damage before starting the hazard layer.

### Turn 22

Public state: p1 Cloyster at 79% vs p2 Cloyster at 100%, no hazards.

Frozen answers: p1 Spikes; p2 Spikes.

Actual: p2 Spikes; p1 Toxic.

Grade: p1 miss, p2 top. I underweighted Toxic as future spinner/setter control
before matching the layer.

### Turn 23

Public state: p1 Cloyster at 85%, p2 Cloyster poisoned, Spikes on p1's side.

Frozen answers: p1 Spikes; p2 Toxic.

Actual: p2 Toxic; p1 Spikes.

Grade: both top.

### Turn 24

Public state: both Cloyster poisoned, both sides have Spikes.

Frozen answers: both sides Rapid Spin.

Actual: p1 switched Starmie; p2 switched Raikou.

Grade: both miss. I overfocused on immediate Spin and missed the support handoff
plus Electric punish sequence.

### Turn 25

Public state: p1 Starmie at 80% vs p2 Raikou, both sides have Spikes.

Frozen answers: p1 switch Steelix; p2 Thunder.

Actual: p1 switched Steelix; p2 Thunder failed into immunity.

Grade: both top.

### Turn 26

Public state: p1 Steelix at 94% vs p2 Raikou, both sides have Spikes.

Frozen answers: p1 Roar; p2 switch Exeggutor or another Steelix answer.

Actual: p2 switched Exeggutor; p1 Roar dragged Snorlax through Spikes.

Grade: both top. Phaze converted the layer immediately.

### Turn 27

Public state: p1 Steelix at 100% vs p2 Snorlax at 35%, both sides have Spikes.

Frozen answers: p1 Earthquake; p2 Rest if available.

Actual: p2 Earthquake; p1 Earthquake.

Grade: p1 top, p2 miss. I undercalled p2's willingness to spend Snorlax for
damage instead of recovery.

### Turn 28

Public state: p1 Steelix at 79% vs p2 Snorlax at 17%.

Frozen answers: p1 Earthquake; p2 switch Cloyster.

Actual: p2 Earthquake; p1 Earthquake KOed Snorlax.

Grade: p1 top, p2 miss.

### Turn 29

Public state: p1 Steelix at 55% vs p2 poisoned Cloyster at 94%, both sides have
Spikes.

Frozen answers: p1 switch Starmie; p2 Surf.

Actual: p1 switched Starmie; p2 Surf.

Grade: both top. This was the correct Starmie handoff after Steelix had
converted with Roar and Earthquake.

### Turn 30

Public state: p1 Starmie at 57% vs p2 poisoned Cloyster at 88%, both sides have
Spikes.

Frozen answers: p1 Rapid Spin; p2 Rapid Spin.

Actual: p1 Rapid Spin cleared p1's Spikes; p2 Toxic poisoned Starmie.

Grade: p1 top, p2 miss. Clean Spin was correct, but p2 chose status as future
spinner control instead of clearing its own side.

### Turn 31

Public state: p1 poisoned Starmie at 63% vs p2 poisoned Cloyster at 78%;
p1's side is clear, p2's side has Spikes.

Frozen answers: p1 direct damage; p2 Rapid Spin.

Actual: p1 Surf; p2 Spikes reset p1's side.

Grade: p1 acceptable, p2 miss. Direct damage was right for p1, but p2 kept the
hazard reset loop instead of spinning.

### Turn 32

Public state: p1 poisoned Starmie at 63% vs p2 poisoned Cloyster at 45%; both
sides have Spikes.

Frozen answers: p1 Rapid Spin; p2 Rapid Spin.

Actual: p1 Rapid Spin cleared p1's side; p2 Spikes reset p1's side.

Grade: p1 top, p2 miss. p1 correctly kept clearing while poison ticked
Cloyster down.

### Turn 33

Public state: p1 poisoned Starmie at 57% vs p2 poisoned Cloyster at 36%; both
sides have Spikes.

Frozen answers: p1 Surf; p2 switch or Spikes reset.

Actual: p1 Rapid Spin cleared p1's side; p2 Spikes reset p1's side.

Grade: p1 miss, p2 acceptable. This is the first overcorrection: I wanted
damage too early. Repeated Spin was still correct because poison was already
doing the removal work and the layer had to be cleared each time.

### Turn 34

Public state: p1 poisoned Starmie at 44% vs p2 poisoned Cloyster at 27%; both
sides have Spikes.

Frozen answers: p1 Rapid Spin; p2 unscored due likely faint branch.

Actual: p1 Surf KOed Cloyster before it could act.

Grade: p1 miss, p2 unscored. This is the second boundary: after repeated Spin
was correct on turns 30 and 32, Surf became correct once it actually removed
the setter/spinner and ended the reset loop.

## Error Classes

1. Starmie handoff timing: on turn 24 I jumped to Spin, missing the player
   handoff to Starmie and the opponent's Raikou answer.
2. Status before layer mirror: on turn 22 I missed Toxic as the first Cloyster
   mirror move before p1 set its own Spikes.
3. Spin loop threshold: on turn 33 I attacked too early; on turn 34 I spun too
   late. The correct action flipped only after Surf became a KO.
4. Sleep exception pricing: earlier context showed the default sleep-clause
   preservation rule, then the Sleep Talk exception. Snorlax stayed asleep and
   productive because Sleep Talk created Curse and Double-Edge pressure, then
   switched out when low.

## Reusable Lesson

In a poisoned Cloyster vs poisoned Starmie hazard loop, do not choose from a
static "damage or Spin" preference.

Re-score after each poison tick:

1. If Rapid Spin clears our side and poison already pressures Cloyster, Spin
   can be the route even if Cloyster sets Spikes again.
2. If direct damage does not KO or force removal yet, it may only let the layer
   remain while Starmie takes poison.
3. Once Surf or Thunder actually removes Cloyster or forces a decisive range,
   damage becomes the route-converting move.
4. Status from the Cloyster side can be correct even when it delays Spin,
   because poisoning Starmie changes the future removal loop.

## Next Study Target

Build a tiny poison-clock spin-loop probe: Starmie vs poisoned Cloyster at
three HP bands where the correct move flips from Rapid Spin to Surf only when
damage removes the setter or prevents the next reset.
