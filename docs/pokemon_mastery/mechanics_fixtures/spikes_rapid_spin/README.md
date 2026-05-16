# Spikes And Rapid Spin Runtime Fixtures

Status: partial runtime smoke. These fixtures verify WRAM Spikes layer bits,
Spikes damage fraction helpers, and Flying-type immunity after direct debugger
calls. They do not yet verify battle text, PP consumption, animation, full turn
timing, grounded switch-in HP subtraction through the textbox path, or failure
branches inside a complete battle turn.

Harness:

```text
python -m tools.damage_debugger.hazard_smoke
```

Log:

```text
audit/damage_debugger/hazard_smoke.log
```

## Verified In Runtime Smoke

The smoke harness ran against `pokegold_debug.gbc` and passed 17 cases:

```text
GLL-SPIKES-001:
  player Spikes targets enemy side:
    0 -> 1 layer
    1 -> 2 layers
    2 -> 3 layers
  enemy Spikes targets player side:
    0 -> 1 layer

GLL-SPIKES-002:
  player fourth Spikes click at 3 layers leaves enemy side at 3 layers

GLL-SPIN-001:
  player hazard clear removes own-side 1, 2, and 3 Spikes layers
  enemy hazard clear removes own-side 3 Spikes layers

GLL-SPIN-002:
  player hazard clear with 0 own-side layers leaves 0 layers unchanged

GLL-SPIKES-003:
  damage fraction helpers on a 120-HP target return:
    1 layer: 15 HP
    2 layers: 20 HP
    3 layers: 30 HP

GLL-SPIKES-004:
  Flying type in slot 1 or slot 2 returns before damage on both player-side
  and enemy-side incoming targets
```

Expected non-return note:

- Direct calls to `BattleCommand_Spikes` and successful
  `BattleCommand_ClearHazards` enter animation or textbox code and do not reach
  the HRAM sentinel in this harness. The WRAM hazard bits are already updated
  before the timeout, so these cases are valid state-transition smoke checks.
- Direct calls to grounded `SpikesDamage` enter textbox code before HP
  subtraction. The current smoke verifies the fraction helpers and Flying
  early-return path, not grounded HP subtraction in a full switch-in sequence.
- The no-layer Rapid Spin control returns immediately because it does not show
  Spikes-clear text.

## Still Unverified

These remain required before Spikes-heavy boss simulations count as proof:

- Exact fourth-click failure text.
- Whether PP is consumed by the fourth Spikes failure branch.
- Whether the same text / animation path is used for player and enemy Spikes.
- Grounded switch-in HP subtraction at 1, 2, and 3 layers in a full switch-in
  sequence.
- Whether a grounded switch-in KO from Spikes cancels the opponent's selected
  move and creates the replacement prompt in the same way as vanilla Showdown.
- Flying-type immunity in live switch-in timing.
- Rapid Spin miss, immunity, Substitute, KO, and failure boundaries.
- Rapid Spin hazard-clear timing relative to damage and other move effects.
- Forced-switch timing for Roar / Whirlwind / Baton Pass and Spikes damage.

## Battle-Advice Translation

This fixture is enough to strengthen these advice claims:

```text
The romhack can hold 0, 1, 2, or 3 Spikes layers in WRAM.
The third layer is a real state transition.
A fourth Spikes click does not create a fourth layer.
A successful Rapid Spin hazard-clear command clears all Spikes layers from the
user's side.
The damage fractions for a grounded 120-HP target are 15, 20, and 30 HP before
full switch-in text/timing is considered.
Flying-type incoming targets skip Spikes damage through the checked early-return
path.
```

This fixture is not enough to write exact advice about PP, text, grounded
switch-in HP subtraction timing, or complete-turn ordering. Keep those claims
labeled source-verified or unverified until the next fixture batch captures
them.
