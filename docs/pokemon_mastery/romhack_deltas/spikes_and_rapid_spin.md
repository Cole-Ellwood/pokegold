# Romhack Delta: Spikes And Rapid Spin

Status: source-verified from local docs and assembly, with partial runtime
smoke coverage. Runtime smoke verifies WRAM layer transitions, successful
hazard-clear state for 1-3 Spikes layers, damage fraction helpers, and
Flying-type early return. Full battle text, PP, complete switch-in HP
subtraction, Rapid Spin failure branches, and same-turn timing remain
unverified.

Scope: Pokemon Gold romhack / Gym Leader Lab. Do not use this as a vanilla GSC
claim.

## Vanilla GSC Baseline

Smogon GSC resources describe vanilla GSC Spikes as one layer of persistent
passive damage that stays until Rapid Spin. Strategically, vanilla Spikes are
valuable because passive damage is scarce, Rest is common, and forced switches
can turn one layer into route progress.

## Romhack Facts

Sources:

- `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- `docs/mechanics_changes_from_base.md`
- `constants/battle_constants.asm`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/move_effects/rapid_spin.asm`
- `engine/battle/core.asm`
- `engine/battle/ai/redundant.asm`
- `engine/battle/ai/boss_policy_move.asm`

Verified facts:

- Spikes is the only entry hazard listed in the local mechanics overview.
- Spikes supports three layers in this hack. The two screen bits
  `SCREENS_SPIKES` and `SCREENS_SPIKES_2` encode the layer count through
  `SCREENS_SPIKES_MASK`.
- Clicking Spikes increments the layer count at 0, 1, or 2 layers.
- Clicking Spikes fails only when the target side already has three layers.
- Switch-in damage is:
  - 1 layer: `maxHP/8`
  - 2 layers: `maxHP/6`
  - 3 layers: `maxHP/4`
- Flying-type Pokemon are unaffected. The source checks the active Pokemon's
  type slots for `FLYING`; there is no Levitate-style ability check.
- Rapid Spin clears both Spikes bits, so it removes all layers.
- AI redundancy treats Spikes as redundant only at three layers.
- Boss policy is layer-aware:
  - layer 1 is broadly encouraged, especially early or when a switch is likely;
  - layer 2 is treated as lower immediate gain unless layer 3 looks reachable;
  - layer 3 is strongly encouraged unless the enemy is under immediate danger;
  - layer 2 and layer 3 are discouraged when the active opposing Pokemon has
    publicly revealed Rapid Spin;
  - clicking at three layers is discouraged.

## Strategic Translation

Do not transfer the vanilla rule "one layer is enough" into this hack. The
transferable principle is:

```text
Hazards are route multipliers when they change switch costs, Rest timing,
phazing value, KO thresholds, sacrifice math, or opponent recovery pressure.
```

The romhack-specific question is:

```text
Which layer changes the route, and can we afford the turn?
```

Layer implications:

- 0 -> 1: creates the basic switch tax and makes repeated grounded pivots
  costly.
- 1 -> 2: smaller marginal jump than 2 -> 3 in many routes; justify it with
  expected repeated switches, phazing, Rest pressure, or a realistic path to the
  third layer.
- 2 -> 3: major route pressure because grounded switch-ins lose one quarter
  max HP.
- 3 -> 3: no progress. Treat a fourth click as a mechanics error unless there
  is some separate move-effect bug being intentionally tested.

## Before Advising Spikes

Ask:

1. Current layer count on the target side?
2. Is the target side already at three layers?
3. How many remaining opposing Pokemon are non-Flying and likely to switch?
4. Does the next layer change a KO range, Rest cycle, phazing route, or forced
   switch sequence?
5. Has the active opponent publicly revealed Rapid Spin, and can we punish or
   block it?
6. Does the setter survive the worst plausible branch?
7. Is the setter still needed for another role, such as Rapid Spin, Explosion,
   walling, or a future sacrifice?
8. Is there an immediate opposing setup or KO route that must be denied instead
   of stacking hazards?

## Benchmark / Mutation Ideas

- `gll-spikes-0-to-1`: first layer is correct because the opponent has repeated
  grounded switch traffic and no cheap spin.
- `gll-spikes-1-to-2-boundary`: second layer loses to attacking if the opponent
  has an immediate setup punish.
- `gll-spikes-2-to-3`: third layer is correct because 1/4 switch-in damage
  flips a Rest or KO threshold.
- `gll-spikes-3-to-3`: fourth click fails and is catastrophic if it gives a
  setup threat a free turn.
- `gll-spin-all-layers`: Rapid Spin removes all layers, so a three-layer stack
  is not secure without spin pressure.
- `gll-flying-immunity`: Flying-type switch-in ignores Spikes; do not count the
  hazard clock on Flying pivots.

## Remaining Verification

- Use `spikes_rapid_spin_fixture_plan.md` and
  `mechanics_fixtures/spikes_rapid_spin/README.md` as the concrete fixture
  plan/status before counting Spikes-heavy boss simulations as mastery
  evidence.
- Build or run an emulator/debugger fixture for exact text, PP, and timing on a
  fourth Spikes click at three layers.
- Build or run a fixture confirming Rapid Spin clears all layers in a live
  battle state.
- Check whether any trainer-specific boss policies add role-specific Spikes
  incentives beyond the generic layer-aware bias.
