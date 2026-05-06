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
