# damage_debugger — bug-check log

This file documents what's been verified about the harness itself, so
future findings can be trusted without redoing the work. Append, don't
rewrite, when adding more checks.

## 2026-05-05 — initial bug-check before feature expansion

Goal: confirm the 8-scenario harness wouldn't false-positive into "fixing"
working code, and wouldn't false-negative through a real clobber.

### Negative control — synthesize the bug the harness was built to catch

Removed the `push bc` / `pop bc` AG-08 preservation pair around
`call TypePassive_GetEffectiveMoveCategory_Far` at the top of
`ApplyLateGenDamageStatsItemMods_Far` (engine/battle/late_gen_held_items.asm:31-36)
— exactly the May 2026 5x-physical-damage bug from commit `ac769ca5`.

Result: 8/8 FAIL, exit 1. Footprint:

| scenario | clean | clobbered | delta |
| --- | --- | --- | --- |
| physical_no_items | 4 | 16 | 4.0x — exact original-bug shape |
| physical_critical | 6 | 31 | 5.2x |
| physical_choice_band | 4 | 24 | 6.0x |
| physical_eviolite_def | 3 | 16 | 5.3x |
| special_no_items | 13 | 4 | 0.31x — special branch hits a floor |
| special_choice_specs | 18 | 6 | 0.33x |
| special_assault_vest | 10 | 4 | 0.40x |
| special_eviolite_spd | 10 | 4 | 0.40x |

Physical-side spikes (consistent with the c-clobber: defender def low byte
overwritten with move-type byte, divided by 1 instead of real def). Special-
side hits a floor through a different mechanism but is still flagged. Both
directions trip the ranges — the harness catches the recurrence.

Reverted, rebuilt, 8/8 PASS restored.

### Positive control — paper-math each PASS scenario

Gen 2 formula path (per engine/battle/effect_commands.asm:2790):

```
Q = floor(floor(floor(floor((2*L)/5 + 2) * BP * Atk) / Def) / 50)
crit: Q *= 2
wCurDamage = (wCurDamage + Q + 2)  # capped at 999
STAB:      wCurDamage = wCurDamage + wCurDamage/2  if move type matches
```

| scenario | hand-computed | harness | range | margin |
| --- | --- | --- | --- | --- |
| physical_no_items | 4 | 4 | 3-5 | ±1 |
| physical_critical | 6 | 6 | 5-8 | -1/+2 |
| physical_choice_band | 4 | 4 | 3-7 | -1/+3 |
| physical_eviolite_def | 3 | 3 | 2-5 | ±2 |
| special_no_items | 13 | 13 | 11-16 | -2/+3 |
| special_choice_specs | 18 | 18 | 16-24 | -2/+6 |
| special_assault_vest | 10 | 10 | 6-12 | -4/+2 |
| special_eviolite_spd | 10 | 10 | 6-12 | -4/+2 |

All ranges are sized to absorb integer-floor noise but tight enough that a
4-10x clobber-class spike trips. No range needed tightening.

The `physical_choice_band` integer-floor docstring claim is correct: at lvl
2, atk=6 vs atk=9 (after `*3/2`) both produce Q=1 because 80*6=480/9=53/50=0
and 80*9=720/9=80/50=1, then both round to wCurDamage=4 post-STAB. The
boost is invisible at this level. Range 3-7 still trips on the synthetic
break (24 > 7).

### find_artifact across worktrees

`paths.find_artifact` walks up from the harness's own location, picking the
first ancestor that contains the named ROM. Confirmed:

- Worktree at `.claude/worktrees/<name>` with its own built ROM → uses
  worktree-local copy.
- Same worktree without a built ROM → silently falls back to an ancestor's
  (typically the main repo's) ROM.

The silent-fallback mode is a real footgun. Reproduced during this check:
running the harness from the worktree before building it locally produced
a `special_eviolite_spd` damage of 241 (vs expected 6-12), because the
main-repo ROM was at `f438afae` (pre-Eviolite-fix). That looks like a
regression but is actually "wrong ROM."

Mitigation landed in this commit: harness now prints the absolute ROM path
in its startup line. If a result looks wrong, first check the path is
inside the expected tree.

### Encoding

Original `4831906b` clobber_smoke.py used `→` and `—` in scenario notes. On
Windows native Python (cp1252 stdout), printing those crashes mid-table and
leaves a partial log. Current notes are all ASCII (`->`), so this isn't
biting today, but it would the moment someone added a unicode glyph.

Mitigation landed in this commit: `sys.stdout.reconfigure(encoding="utf-8")`
at the top of `main()`. Future scenario authors don't need to police their
notes character-by-character.

### Still latent (not addressed by this pass)

- No coverage for type-effective branches (super-effective, not-very-
  effective, immune). A clobber on the type-matchup loop in
  `BattleCommand_Stab` would not be caught by current scenarios. (Pass 2
  feature #1.)
- No coverage for `BattleCommand_DamageVariation` (the final 0.85-1.0
  random multiplier). Each scenario currently runs at fixed RNG. A
  clobber that survives integer truncation but corrupts the variation
  path is invisible. (Pass 2 feature #2.)
- No coverage for `HandleLateGenAfterHitEffects_Far` (Rocky Helmet, Life
  Orb, Shell Bell). Whole second damage chain.
- Range setting is hand-picked, not formula-derived. A future Python
  oracle would let scenarios specify expected damage as exact, not
  range. (Dream feature #4.)

### How to redo this check

1. From a worktree that has a fresh `pokegold_debug.gbc`, run
   `python -m tools.damage_debugger.clobber_smoke` and confirm 8/8 PASS.
2. Edit `engine/battle/late_gen_held_items.asm`: in
   `ApplyLateGenDamageStatsItemMods_Far`, delete lines `push bc` and the
   matching `pop bc` around `call TypePassive_GetEffectiveMoveCategory_Far`.
3. Rebuild `pokegold_debug.gbc`. Rerun the harness. Expect 8/8 FAIL with
   the footprint table above. Confirm exit code is 1.
4. Revert the asm edit, rebuild, rerun. Expect 8/8 PASS, exit 0.

If step 3 produces fewer than 8 FAILs, the ranges are too loose and need
tightening before more features are added. If step 4 doesn't restore 8/8
PASS, something else regressed during the check — investigate before
adding features.

## 2026-05-05 — Tier 2.2 Hypothesis fuzz lands; finds 1 ROM bug + 4 oracle gaps

The fuzz harness (`python -m tools.damage_debugger.fuzz`) generates
random `BattleInputs` records and compares the on-ROM `wCurDamage`
against `oracle.predict_damage`. Hypothesis auto-shrinks failures to
the minimal repro.

In the first 5000 examples, the harness surfaced four oracle gaps in
quick succession (each fixed before the next ran):

1. **Type-matchup NO_EFFECT writeback semantics**: I had originally
   modeled "immune leaves wCurDamage unchanged" based on a naive read
   of the asm. The math UNION (`ram/hram.asm:60-79`) aliases
   `hMultiplicand[1..3]` with `hProduct[1..3]`, so a multiply-by-zero
   actually overwrites the writeback bytes with zero. NO_EFFECT zeroes
   wCurDamage. (Caught at example 5.)

2. **`TypePassive_ApplyDamageModifiers_Far` missing**: the hack runs a
   nine-branch `farcall` after the matchup loop
   (`engine/battle/type_passive_damage_mods.asm:44`) that applies
   small fractional modifiers gated on attacker types, defender types,
   move type, status, HP, and crit. Oracle hadn't modeled it. Added
   `_type_passive_modifiers` mirroring all nine branches in asm order.
   (Caught at example 23 — `physical NORMAL/DRAGON vs NORMAL/GHOST`,
   ROM=2 vs oracle=4 explained by Dragon-resist branch.)

3. **`TruncateHL_BC` (effect_commands.asm:2590) missing**: when atk
   or def exceeds 255, the asm shifts BOTH stats right by 2 bits,
   minimum-clamped to 1. Oracle was using the raw 16-bit values and
   diverging on high-stat scenarios. Added `_truncate_hl_bc`. (Caught
   at example ~50, special FIRE atk=256 def=5 → ROM truncated to
   atk=64 def=1 → Q=25 vs oracle's Q=20.)

4. **Damage cap order**: oracle was capping `dmg = q + 2` to 997, but
   the asm caps `q` first (writes wCurDamage = $03E5) then adds
   MIN_DAMAGE (= 2) for a final 999. STAB on 999 vs STAB on 997
   diverges by 3-5 damage at high quotients. Fixed cap-then-add
   ordering. (Caught at level 5 atk=334 def=5 BP=50 crit Choice Band.)

5. **Dragon's Majesty multiplier**: the hack converts NO_EFFECT to
   NOT_VERY_EFFECTIVE for DRAGON-typed attackers. Oracle was
   short-circuiting on NO_EFFECT without checking if Dragon's Majesty
   would reroute. Added `_dragons_majesty_applies`. (Caught at
   `attacker (NORMAL, DRAGON) vs (NORMAL, GHOST)` -- Dragon's Majesty
   converted the immunity to 0.5x.)

After those fixes, fuzz finds **a real, previously unknown ROM bug**:

### ROM bug: `.GetUserHPAndMax` / `.GetOpponentHPAndMax` d-clobber

`engine/battle/type_passive_damage_mods.asm:322-340` and
`engine/battle/type_passive_damage_mods.asm:342-360` both use this
pattern:

```asm
ld a, [de]
ld d, a       ; <-- clobbers d, the high byte of de
inc de        ; de now points at $00(low_byte+1) -- ROM low addresses
ld a, [de]    ; reads from ROM[$000F] (= 0) instead of MaxHP[lo]
ld e, a       ; e = 0 always for MaxHP < 256
```

Net effect for any MaxHP < 256 (basically every realistic battle):
- `IsUserBelowOneThirdHP` always returns "not below 1/3" -- **the FIRE-
  low-HP Type Passive boost never fires.**
- `IsOpponentAboveHalfHP` returns carry-set iff HP > 0 -- the comparison
  collapses to "any HP" because the bugged MaxHP/2 reads as 0.

Reproduce: `attacker (NORMAL, FIRE) at HP=1 / MaxHP=10, FIRE move,
attacker_below_third_hp=True` → oracle predicts 11/10 boost (e.g.
21 → 23) but ROM gives 21 because the boost doesn't fire.

Fix shape (escalated to user as a gameplay-affecting decision since
it changes a balance feature from "broken" to "active"):

```asm
ld a, [de]
push af
inc de
ld a, [de]
ld e, a
pop af
ld d, a
ret
```

Or use a different scratch register that isn't part of the addressing
pair. Both `.GetUserHPAndMax` and `.GetOpponentHPAndMax` need the
same fix.

Oracle currently mirrors the buggy behavior (Branch 2 in
`_type_passive_modifiers` is gated by `if False`, with a recurrence
note pointing here) so the fuzz harness stays green. When the ROM is
fixed, drop the gate, regenerate `pokegold_debug.gbc`, and re-run
`tools/damage_debugger.fuzz` -- the harness will validate the fix.

### Final state

- `oracle.py` self-test: 8/8 match paper math.
- `clobber_smoke`: 8/8 PASS in 0.5s (Tier 1.1 boot cache).
- `fuzz`: PASS at 10000 examples in 70s on this machine.
- Real ROM bug found, escalated, oracle adapted.

The harness has now demonstrably done its job:
- Found the May 2026 AG-08 c-clobber (commit `ac769ca5`, pre-fuzz era).
- Found the Eviolite `bc/hl` clobber (commit `2ad4ca2c`, this session).
- Found the GetUserHPAndMax d-clobber (commit `<this commit>`,
  this session, via Hypothesis fuzz).
