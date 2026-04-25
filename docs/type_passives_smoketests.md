# Type Passives V1 Smoke Tests

Build the current source with the normal Gold target before running these manual smoke tests.

## 1) Normal STAB multiplier changes
- Monotype Normal user with a Normal damaging move:
  - Expected STAB path: `1.60x`.
- Dual-type user including Normal with a Normal damaging move:
  - Expected STAB path: `1.55x`.

## 2) Flying accuracy multiplier changes
- Use a mon with Flying in typing and repeat a non-perfect-accuracy move.
- Expected:
  - Full Flying passive: final accuracy multiplied by `1.08`.
  - Half Flying passive: final accuracy multiplied by `1.04`.

## 3) Poison retaliation proc rates
- Defender with Poison in typing gets hit by a contact damaging move.
- Expected retaliation (poison attacker, if attacker is eligible):
  - Full Poison passive: `20%`.
  - Half Poison passive: `10%`.

## 4) Dark first-status negation behavior
- Use a non-damaging status move that would affect a Dark-typed target.
- Expected:
  - Full Dark passive: first eligible status move fails.
  - Half Dark passive: first eligible status move has `50%` fail chance.
  - Shield is consumed on first eligible attempt.

## 5) Psychic proc behavior (0 damage, still hit semantics)
- Repeatedly hit a Psychic-typed defender with damaging moves.
- Expected:
  - Full Psychic passive: `13/256` proc to set damage to `0`.
  - Half Psychic passive: `6/256` proc to set damage to `0`.
  - Move is still treated as a hit for downstream flow.

## 6) Steel recoil removal behavior
- Use recoil moves (for example `TAKE_DOWN`, `DOUBLE_EDGE`) with Steel-typed users.
- Expected:
  - Full Steel passive: recoil is `0`.
  - Half Steel passive: recoil is multiplied by `0.5`.
