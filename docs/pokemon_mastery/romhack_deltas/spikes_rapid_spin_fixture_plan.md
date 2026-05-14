# Romhack Fixture Plan: Spikes And Rapid Spin

Purpose: define the emulator/debugger fixtures needed before Spikes-heavy boss
simulations count as evidence for Pokemon mastery. This plan separates
source-verified mechanics from runtime facts that still need capture.

Status: fixture plan with partial runtime smoke. Source behavior is inspected;
WRAM layer transitions, Spikes damage fraction helpers, and Flying immunity are
runtime-smoked in `../mechanics_fixtures/spikes_rapid_spin/README.md`; text,
PP, grounded switch-in HP subtraction, failure branches, and exact turn timing
are not yet captured here.

Source evidence:

- Spikes command: `engine/battle/move_effects/spikes.asm`.
- Rapid Spin hazard clear command:
  `engine/battle/move_effects/rapid_spin.asm`.
- Switch-in damage: `engine/battle/core.asm`, `SpikesDamage`.
- Layer bits: `constants/battle_constants.asm`, `SCREENS_SPIKES_MASK`.
- Battle text: `data/text/battle.asm`, `SpikesText`,
  `BlewSpikesText`, `ButItFailedText`, and `ItFailedText`.
- AI redundancy: `engine/battle/ai/redundant.asm`.
- Boss policy layer bias: `engine/battle/ai/boss_policy_move.asm`,
  `.ApplySpikesLayerBias`.
- Mechanics delta summary: `spikes_and_rapid_spin.md`.

Expert baseline:

- Smogon GSC Spikes material:
  <https://www.smogon.com/gs/articles/gsc_spikes>.

## Source-Verified Claims

These are already supported by assembly, but still useful to confirm in a
runtime smoke fixture:

- Spikes increments the target side from 0, 1, or 2 layers.
- Spikes fails when the target side already has 3 layers.
- Switch-in damage is:
  - 1 layer: `maxHP/8`;
  - 2 layers: `maxHP/6`;
  - 3 layers: `maxHP/4`.
- Flying-type Pokemon take no Spikes damage.
- Rapid Spin clears both Spikes bits, so it removes all layers.
- AI redundancy treats Spikes as redundant at 3 layers.
- Boss policy is layer-aware rather than treating all Spikes clicks alike.

## Runtime Claims Still Needed

These should not be used as boss-sim proof until captured:

- Exact text for fourth Spikes click at max layers.
- Whether PP is consumed on the fourth Spikes failure branch.
- Whether failed Spikes triggers the same animation/text path for player and
  enemy users.
- Exact timing of switch-in Spikes damage relative to forced switches, ordinary
  switches, Pursuit, Roar/Whirlwind, Baton Pass, and Ditto Imposter.
- Exact timing of Rapid Spin hazard clearing after damage, KO, Leech Seed,
  wrap/bind release, miss/fail/immunity, and Substitute interactions.
- Whether any boss-specific policy creates live behavior that differs from the
  generic source-level layer bias.

## Runtime Smoke Already Captured

`python -m tools.damage_debugger.hazard_smoke` verifies these WRAM state
transitions:

```text
GLL-SPIKES-001:
  0 -> 1, 1 -> 2, and 2 -> 3 target-side layer transitions.
  player and enemy side selection for at least one layer.

GLL-SPIKES-002:
  fourth Spikes click at 3 layers leaves the target side at 3 layers.

GLL-SPIN-001:
  Rapid Spin hazard-clear command removes 1, 2, and 3 layers from the user's
  side.

GLL-SPIN-002:
  no-layer hazard-clear control leaves 0 layers unchanged.

GLL-SPIKES-003:
  120 max HP fraction helpers return 15, 20, and 30 HP for 1, 2, and 3 layers.

GLL-SPIKES-004:
  Flying type in either type slot returns before Spikes damage for player-side
  and enemy-side incoming targets.
```

This is not full battle-turn verification. The direct move-effect calls can
enter text/animation code without returning to the sentinel, so this smoke
should be cited only for layer-bit transitions, fraction-helper output, and the
Flying early-return path.

## Fixture Matrix

Use deterministic states with HP values divisible by 24 when possible. A
120-HP grounded target gives clean expected damage:

```text
1 layer: 15 HP
2 layers: 20 HP
3 layers: 30 HP
```

### GLL-SPIKES-001: Layer Increment

Setup:

```text
target side Spikes layers: 0, then 1, then 2 in separate subcases
Spikes user: any Pokemon with Spikes
target: grounded Pokemon
```

Assertions:

```text
0 -> 1, 1 -> 2, and 2 -> 3 layer transitions occur.
SpikesText is shown: "SPIKES scattered all around <TARGET>!"
PP change is recorded.
No switch-in damage occurs until a switch or forced entry.
```

Strategic implication:

- Layer 2 and layer 3 can be real progress in the romhack, but only if the
  layer changes a route before removal or punishment.

### GLL-SPIKES-002: Fourth Click Failure

Setup:

```text
target side Spikes layers: 3
Spikes user: any Pokemon with Spikes
opponent: any Pokemon that cannot end the battle before text/PP capture
```

Assertions:

```text
layer count remains 3
failure text is captured exactly
PP before and after is captured
animation path is noted
opponent action and turn order are recorded
```

Strategic implication:

- If PP is consumed, the fourth click is both a no-progress turn and a PP cost.
  If PP is not consumed, it is still a catastrophic no-progress turn when the
  opponent can set up, attack, spin, phaze, recover, or sleep.

### GLL-SPIKES-003: Grounded Switch-In Damage

Setup:

```text
target side Spikes layers: 1, 2, then 3 in separate subcases
incoming Pokemon: grounded, 120 max HP if possible
entry type: ordinary switch
```

Assertions:

```text
1 layer deals 15 HP on 120 max HP
2 layers deals 20 HP on 120 max HP
3 layers deals 30 HP on 120 max HP
"hurt by SPIKES!" timing is captured relative to switch text and turn action
```

Strategic implication:

- Route advice can use layer thresholds only after rounding and timing are
  verified in live battle state.

### GLL-SPIKES-004: Flying Immunity

Setup:

```text
target side Spikes layers: 3
incoming Pokemon: Flying-type in either type slot
entry type: ordinary switch
```

Assertions:

```text
no Spikes text
no Spikes damage
no hidden Levitate-style check is needed for this fixture
```

Strategic implication:

- Do not count Spikes as a clock on Flying pivots when choosing a boss route.

### GLL-SPIN-001: Rapid Spin Clears All Layers

Setup:

```text
spinner: any Pokemon with Rapid Spin
spinner's side Spikes layers: 1, 2, then 3 in separate subcases
target: legal hit target
```

Assertions:

```text
after successful Rapid Spin, spinner's side layer mask is 0
"<USER> blew away SPIKES!" text is shown when layers existed
all layer counts clear, not just one layer
PP, damage, and turn timing are recorded
```

Strategic implication:

- A three-layer stack is not secure if a successful Rapid Spin can erase the
  whole route without sufficient punish.

### GLL-SPIN-002: Rapid Spin No-Layers Control

Setup:

```text
spinner's side Spikes layers: 0
spinner uses Rapid Spin
```

Assertions:

```text
no Spikes-clear text is shown
damage and any other move effect still resolve normally
PP and turn timing are recorded
```

Strategic implication:

- Do not treat Rapid Spin as purely hazard removal; it may still be a damaging
  or tempo move when no layers exist.

### GLL-SPIN-003: Rapid Spin Failure Boundary

Setup:

```text
spinner's side Spikes layers: 3
Rapid Spin fails to connect or cannot affect the target in separate subcases
```

Assertions:

```text
whether layers remain after miss/fail/immunity is captured
whether clear text appears is captured
PP and failure text are captured
```

Strategic implication:

- Spin-denial advice depends on whether the denial branch actually preserves
  layers or only changes damage/tempo.

### GLL-SPIKES-TIMING-001: Forced Switch Timing

Setup:

```text
target side Spikes layers: 1 and 3 in separate subcases
forced-switch move or effect: Roar / Whirlwind / Baton Pass as applicable
incoming target: grounded 120 max HP if possible
```

Assertions:

```text
Spikes timing relative to forced-entry text is captured
damage occurs or does not occur according to source behavior
turn order and next action availability are recorded
```

Strategic implication:

- Phazing-plus-hazard advice should not count damage until the exact forced
  switch timing is verified.

## Capture Output Shape

Save the first fixture batch here:

```text
docs/pokemon_mastery/mechanics_fixtures/spikes_rapid_spin/
  README.md
  gll-spikes-001-layer-increment.md
  gll-spikes-002-fourth-click-failure.md
  gll-spikes-003-grounded-switch-damage.md
  gll-spikes-004-flying-immunity.md
  gll-spin-001-clear-all-layers.md
  gll-spin-002-no-layers-control.md
  gll-spin-003-failure-boundary.md
  gll-spikes-timing-001-forced-switch.md
```

Each fixture result should include:

```text
ROM build/hash:
fixture setup:
starting WRAM hazard bits:
starting HP and PP:
turn transcript:
text shown:
ending WRAM hazard bits:
ending HP and PP:
pass/fail:
mechanics claim validated:
boss-sim routes unblocked:
```

## Boss-Sim Gate

Before a Spikes-heavy boss simulation counts toward the 50-battle / 80% target,
these must pass:

```text
required:
  GLL-SPIKES-001
  GLL-SPIKES-002
  GLL-SPIKES-003
  GLL-SPIKES-004
  GLL-SPIN-001

required before claiming spin-denial or phazing policy:
  GLL-SPIN-003
  GLL-SPIKES-TIMING-001

optional but useful:
  GLL-SPIN-002
```

Until then, Spikes-heavy advice should be labeled:

```text
source-verified but not runtime-fixture-verified
```

## Notebook Lesson

The useful Pokemon lesson is not "always stack three layers." It is:

```text
Layer value is a state transition. A layer matters when it changes the next
switch, forced-entry, Rest, KO, sacrifice, or endgame route before the opponent
spins, phazes, sets up, sleeps, or attacks through the free turn.
```

The fourth-click fixture is especially important because it tests a common bad
policy shape: continuing a good heuristic after the state has made it illegal
or no-progress.
