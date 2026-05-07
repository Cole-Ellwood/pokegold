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
  `BattleCommand_Stab` would not be caught by current scenarios. (Closed
  by H4 on 2026-05-06.)
- No coverage for `BattleCommand_DamageVariation` (the final 0.85-1.0
  random multiplier). Each scenario currently runs at fixed RNG. A
  clobber that survives integer truncation but corrupts the variation
  path is invisible. (Closed by H4 range coverage on 2026-05-06.)
- No coverage for `HandleLateGenAfterHitEffects_Far` (Rocky Helmet, Life
  Orb, Shell Bell). Whole second damage chain. (Closed by H4 HP
  side-effect coverage on 2026-05-06.)
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

## 2026-05-05 — 50k fuzz finds a second ROM bug

Pass A from the 2026-05-05 oracle bug-test handoff. Ran fuzz at
`--max-examples=50000`. Hypothesis surfaced this counterexample at
~6 minutes wall-clock:

```
inputs: attacker_level=3, move_bp=27, move_type=GROUND, is_physical=True,
        attacker_atk=62, defender_def=5,
        attacker_types=(NORMAL, DRAGON), defender_types=(GHOST, GROUND),
        is_critical=True
rom_damage=19, oracle_damage=21
```

### ROM bug: `CheckTypeMatchup.Yup` hl-clobber via Dragon's Majesty farcall

`engine/battle/effect_commands.asm:1493-1512` — the running-product
matchup loop's `.Yup` block does `call CheckTypeMatchup_ApplyDragonsMajestyMultiplier`
without `push hl`. That call chains into `BattleCommand_ApplyDragonsMajestyMultiplier`
(line 1415-1424) which `farcall`s `TypePassive_ApplyDragonsMajestyMultiplier_Far`.
Per the asm guide §3.2, `farcall` clobbers caller's `hl`. The matchup
loop then continues with `hl` pointing at random stack memory.

Trace (probe5):

```
Yup #1: hl=0x4e92 — real (GROUND, GHOST, mult=NO_EFFECT) row in TypeMatchups
Yup #2: hl=0xdfd5 — STACK garbage (wStackTop=$dfff)
Yup #3: hl=0xdfe1 — STACK garbage
End: wTypeMatchup = 85 (instead of intended 5)
```

In TypePassive, `wTypeMatchup = 85` makes Branch 5 (GROUND-super-eff
resist) fire when it shouldn't, dropping damage from 21 → 19 via the
19/20 dual-GROUND fraction.

### Fires when

Both conditions:
1. The matchup row would have mult `NO_EFFECT` (NORMAL→GHOST,
   ELECTRIC→GROUND, POISON→STEEL, GROUND→FLYING/GHOST, PSYCHIC→DARK,
   GHOST→NORMAL/STEEL, FIGHTING→GHOST).
2. Attacker has DRAGON contribution > 0 (so Dragon's Majesty re-routes
   instead of returning early).

The neighboring per-row matchup loop in `BattleCommand_Stab.GotMatchup`
(line 1331-1390) handles this safely — it has `push hl` at line 1332.
Only `CheckTypeMatchup.Yup` is missing the save.

### Severity

Damage against type-immunity defenders by DRAGON-contribution attackers
is **non-deterministic** — the corrupted hl reads stack memory whose
contents depend on prior call history. Real-world examples:
Dragonite/Salamence using ELECTRIC vs GROUND (NVE via DM in spec, but
ROM reads garbage); any DRAGON dual-type using NORMAL/POISON/etc vs the
matching immunity defender.

### Fix shape

```asm
.Yup:
    xor a
    ldh [hDividend + 0], a
    ldh [hMultiplicand + 0], a
    ldh [hMultiplicand + 1], a
    ld a, [hli]
    push hl                                ; <-- add
    call CheckTypeMatchup_ApplyDragonsMajestyMultiplier
    pop hl                                 ; <-- add
    ldh [hMultiplicand + 2], a
    ...
```

**Don't ship.** The HP-d-clobber fix from earlier in this session is
still pending user review for the same reason — both bugs change a
balance-affecting mechanic from "broken" to "active." Escalate.

### Disposition

Oracle currently models the as-intended math (matchup_total = 5 for
NVE-via-DM). The 50k fuzz divergence is a positive signal: when this
ROM bug is fixed, fuzz on this counterexample will report PASS and the
divergence will go away. Until then, leave as-is — it's a permanent
regression guard.

Audit report covering all phases of the chain
(`tools/damage_debugger/ORACLE_AUDIT_2026-05-05.md`) lists this plus
two undocumented Stab-side oracle gaps (`DoWeatherModifiers`,
`DoBadgeTypeBoosts`).

### Final state (after this pass)

- `oracle.py` self-test: 8/8 match paper math.
- `clobber_smoke`: 8/8 PASS.
- `fuzz` at 50k: 1 divergence (this ROM bug).
- 2 ROM bugs identified by the harness this session
  (HP-d-clobber + DM-hl-clobber), both escalated, both pending user
  review. Audit doc captures the full picture.

## 2026-05-05 — both ROM bugs fixed; oracle pristine-flag retired

User approved fixing both bugs via `/go fix it`. Both shipped this
session.

### DM-hl-clobber fix

`engine/battle/effect_commands.asm:1499` — added `push hl` / `pop hl`
around `call CheckTypeMatchup_ApplyDragonsMajestyMultiplier`.
Verification:
- 50k fuzz counterexample (NORMAL/DRAGON crit GROUND vs GHOST/GROUND):
  rom=21 oracle=21 (was rom=19).
- clobber_smoke 8/8 PASS, fuzz @ 5000 PASS, release_smoke +
  cross_bank_call + farcall_hl/a_clobber audits all PASS.

### HP-d-clobber fix

`engine/battle/type_passive_damage_mods.asm:322` and `:342` — replaced
the `ld d, a; inc de; ld a, [de]; ld e, a` pattern (which clobbers
de's high byte before the second read) with a `push af`-protected
sequence that reads MaxHP_low first, then restores MaxHP_high. Both
`.GetUserHPAndMax` and `.GetOpponentHPAndMax` updated.

Verification: `find --bug hp_d_clobber` reports rom=14 oracle=14
("No bug"). Branch 2 (FIRE-low-HP boost) and Branch 9
(ICE-above-half-HP resist) now fire correctly.

### Oracle cleanup

The `pristine` parameter on `predict_damage` / `predict_damage_trace`
was the temporary mirror for the d-clobber bug. With the asm fixed,
oracle's default mode now matches the as-shipped ROM directly. The
parameter signature is kept for backwards compatibility but no
longer gates any branch.

Branch 2 docstring updated to reflect the fix. Branch 9 docstring
updated similarly. `find.py`'s `hp_d_clobber` entry repurposed as a
regression guard.

### Final state (after both fixes)

- `oracle.py` self-test: 8/8 match paper math.
- `clobber_smoke`: 8/8 PASS.
- `fuzz` at 5000: PASS, no divergence.
- `find --bug hp_d_clobber`: PASS, no divergence (regression guard
  active).
- 2 ROM bugs found AND fixed AND verified by the harness this
  session. Round-trip complete.

## 2026-05-06 — H1 multiprocessing fuzz worker mode

Roadmap item: H1, multi-process fuzz parallelization.

Change:
- Added `--workers N` to `tools.damage_debugger.fuzz`.
- Split the Hypothesis example budget across spawned Python worker
  processes. Each worker owns its own PyBoy instance and boot cache.
- Added deterministic per-worker seeds (`base_seed + worker_id`) so a
  failing worker report can be reproduced.
- Added `--self-check-workers N`, a debugger self-check that runs a fixed
  six-case corpus once in-process and once split across workers, then
  compares the exact `(ROM damage, oracle damage, ok)` tuple per case.
- Fixed a debugger hygiene bug in the existing single-process path: the
  fuzz cache was not explicitly stopped, causing Windows/PyBoy shutdown
  to print repeated `Error in sys.excepthook` noise after an otherwise
  passing fuzz run.

Verification:
- `python -m tools.damage_debugger.oracle` — PASS, 8/8 oracle self-tests.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 8/8 scenarios.
- `python -m tools.damage_debugger.fuzz --self-check-workers=2` — PASS,
  six-case corpus equivalent between single-process and two-worker runs.
- `python -m tools.damage_debugger.fuzz --max-examples=20 --workers=1 --verbose`
  — PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=20 --workers=2 --verbose`
  — PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=40 --workers=4` — PASS.

Remaining risk:
- The verification budget here proves worker plumbing and representative
  fuzz behavior, not the roadmap's eventual 50k/8-worker performance target.
  Run the larger budget before release delivery.

## 2026-05-06 — H2 Claude PreToolUse clobber smoke gate

Roadmap item: H2, pre-commit smoke hook.

Change:
- Added `tools.damage_debugger.precommit_check`.
- Wired `.claude/settings.json` `PreToolUse` for Bash commands to run the
  checker before Claude executes shell commands.
- The checker skips non-commit commands, inspects the pending commit's
  staged files (plus `git commit -a` tracked changes and explicit target
  pathspecs), and runs `clobber_smoke` only when the commit touches:
  - `engine/battle/late_gen_held_items.asm`
  - `engine/battle/type_passive_damage_mods.asm`
- Added `--self-test`, which creates a temporary Git repository and verifies
  the hook's decision logic without touching the real repo index.

Verification:
- `python -m tools.damage_debugger.precommit_check --self-test` — PASS.
  Covered non-commit skip, untouched-file skip, touched-file smoke execution,
  and touched-file smoke failure propagation.
- `{"tool_input":{"command":"git status"}} | python -m tools.damage_debugger.precommit_check`
  — PASS, skipped.
- `{"tool_input":{"command":"git commit -m test"}} | python -m tools.damage_debugger.precommit_check --dry-run`
  — PASS, skipped because no target damage-chain asm was staged.
- `.claude/settings.json` parsed as JSON.
- `python -m compileall -q tools\damage_debugger` — PASS.

Remaining risk:
- This guards Claude Code Bash-tool commits. A manual Git commit outside
  Claude Code will not run this hook unless a separate Git hook is installed.

## 2026-05-06 — H3 weather + badge oracle/fuzz axes

Roadmap item: H3, Pass C weather + badges.

Change:
- Added weather fields to `BattleInputs` and modeled `DoWeatherModifiers`
  in `oracle.py`:
  - rain boosts WATER by 15/10 and halves FIRE;
  - sun boosts FIRE by 15/10 and halves WATER;
  - rain halves SolarBeam-effect moves only when no weather type row matched.
- Added badge fields to `BattleInputs` and modeled `DoBadgeTypeBoosts`:
  player turn only, `wLinkMode == 0`, Johto badge bits followed by Kanto
  badge bits, matching move type, add `max(1, damage // 8)` capped at `$ffff`.
- Extended `fuzz.py` to generate weather and matching-badge axes and seed
  `wBattleWeather`, `wJohtoBadges`, `wKantoBadges`, `wLinkMode`, and the
  move-effect byte.
- Added deterministic clobber-smoke scenarios:
  - `special_sun_fire`: FIRE move under sun, ROM/oracle damage 19.
  - `special_rain_fire`: FIRE move under rain, ROM/oracle damage 6.
  - `special_fire_badge`: FIRE move with VolcanoBadge, ROM/oracle damage 15.
- Updated `find.py` scenario mapping and report output for the new axes.
- Updated `ORACLE_AUDIT_2026-05-05.md` to mark the weather/badge gaps closed.

Verification:
- `python -m tools.damage_debugger.oracle` — PASS, 11/11 oracle self-tests.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 11/11 scenarios.
- `python -m tools.damage_debugger.fuzz --self-check-workers=2` — PASS,
  nine-case corpus equivalent between single-process and two-worker runs.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1` — PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2` — PASS.
- `python -m tools.damage_debugger.find special_sun_fire` — PASS, no divergence.
- `python -m tools.damage_debugger.find special_fire_badge` — PASS, no divergence.

Remaining risk:
- H3 covers the weather/badge modifier routines themselves. It does not close
  still-documented gaps around nonzero `wCurDamage` entering DamageCalc,
  BP=0 multi-hit/conversion bypasses, or later DamageVariation/after-hit
  effects.

## 2026-05-06 — M1 cap-add endian investigation

Roadmap item: M1, cap-add endian investigation.

Change:
- Added `tools.damage_debugger.cap_add_probe`.
- Added `BattleInputs.initial_cur_damage` so the debugger can seed a
  synthetic multi-hit-style nonzero `wCurDamage` between DamageStats and
  DamageCalc.
- Added `oracle.predict_damagecalc_only`, with a switch for the current
  shipped asm behavior vs the likely intended endian-neutral accumulation.
- Extended `fuzz.py` to include the synthetic nonzero-`wCurDamage` axis and
  a fixed worker self-check case at `$0100`.

Finding:
- The ROM matches current asm behavior, not intended endian-neutral behavior.
- Incoming `wCurDamage = $0100` before DamageCalc yields:
  - ROM: 289
  - current-asm model: 289
  - intended model: 288
- Root cause is the audit-suspected line sequence at
  `engine/battle/effect_commands.asm:2939`: the high byte of
  `wCurDamage` is added to `hQuotient+3` before the full 16-bit incoming
  damage is added, so incoming damage >= 256 gets an extra
  `high(wCurDamage)` added.

Disposition:
- Documented as a real ROM bug, but not fixed here because changing it would
  alter gameplay behavior for high-damage multi-hit accumulation. The oracle
  models the shipped asm by default so fuzz remains a regression guard for
  debugger/ROM agreement.

Verification:
- `python -m tools.damage_debugger.cap_add_probe` — PASS/classified:
  `$0000` and `$00ff` match both models; `$0100` matches current asm only.
- `python -m tools.damage_debugger.oracle` — PASS, 11/11 oracle self-tests.
- `python -m tools.damage_debugger.fuzz --self-check-workers=2` — PASS,
  ten-case corpus including `$0100` initial damage.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1` — PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2` — PASS.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 11/11 scenarios.

## 2026-05-06 — H4 type-effectiveness, DamageVariation, after-hit scenarios

Roadmap item: H4, type-effectiveness + DamageVariation +
AfterHitEffects scenarios.

Change:
- Extended `clobber_smoke.Scenario` with an optional call chain, post-check
  hook, call budget, and explicit non-return allowance for handlers that
  tail into battle text/HUD loops after applying their side effects.
- Added deterministic type-effectiveness smoke scenarios:
  - `special_super_effective`: FIRE vs GRASS/BUG, ROM/oracle damage 52.
  - `special_not_very_effective`: FIRE vs WATER/FIRE, ROM/oracle damage 2.
  - `physical_immune`: NORMAL vs GHOST/GHOST, ROM/oracle damage 0.
- Added `special_super_effective_variation`, which runs
  `BattleCommand_DamageVariation` after the normal damage chain and asserts
  the final damage remains in the 0.85-1.0 range.
- Added isolated `HandleLateGenAfterHitEffects_Far` smoke scenarios with HP
  post-checks:
  - `afterhit_rocky_helmet`: player HP 30 -> 25.
  - `afterhit_shell_bell`: player HP 10 -> 12.
  - `afterhit_life_orb`: player HP 30 -> 27.
- Added exact oracle self-test cases for the deterministic type-effectiveness
  scenarios.
- Fixed a `find.py` debugger bug: the Stab bucket was reading the
  post-matchup value from `BattleCommand_Stab.end`, so type-effectiveness
  scenarios falsely reported Stab divergence while final damage matched.
  `find.py` now hooks `BattleCommand_Stab.SkipStab` for the pre-matchup
  bucket and has `--self-test` coverage for the bucket boundaries.

Debugger self-check:
- `clobber_smoke` now fails if after-hit HP state is wrong, not only if
  `wCurDamage` is out of range.
- `python -m tools.damage_debugger.find --self-test` fails if Stab,
  TypeMatchup, and TypePassive buckets collapse or point at the wrong label.

Verification:
- `python -m tools.damage_debugger.clobber_smoke` — PASS before H4, 11/11.
- `python -m tools.damage_debugger.oracle` — PASS, 14/14 oracle self-tests.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 18/18 scenarios.
- `python -m tools.damage_debugger.find special_super_effective` — PASS,
  no divergence.
- `python -m tools.damage_debugger.find special_not_very_effective` — PASS,
  no divergence.
- `python -m tools.damage_debugger.find physical_immune` — PASS, no
  divergence.
- `python -m tools.damage_debugger.find --self-test` — PASS.
- `python -m tools.damage_debugger.find --json special_super_effective` —
  PASS, JSON shape includes all five trace buckets and no divergence.
- `python -m tools.damage_debugger.fuzz --self-check-workers=2` — PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=1` —
  PASS.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2` —
  PASS.
- `python -m compileall -q tools\damage_debugger` — PASS.
- `python tools\audit\check_navigation_floor.py` — PASS.
- `git diff --check` — PASS.

Remaining risk:
- DamageVariation remains range-checked rather than exactly oracle-modeled
  because the debugger does not yet seed the battle RNG deterministically
  across all call sites.
- After-hit scenarios are isolated state checks, not full move-script
  integration tests. They cover the handler side effects that H4 targeted.

## 2026-05-06 — M2 reusable hook instrumentation in find.py

Roadmap item: M2, promote the "HL + memory at hook" probe pattern into
supported `find.py` tooling.

Change:
- Added `--instrument-hook <symbol>` to `tools.damage_debugger.find`.
- Added a reusable hook recorder that captures CPU registers and the
  three bytes at `mem[HL-2..HL]` on every hook hit.
- Text output now prints per-hit PC, registers, HL, SP, and the memory
  window; JSON output includes the same data under `instrumentation`.
- Added `--bug dm_hl_clobber`, the Dragon's Majesty
  `CheckTypeMatchup.Yup` regression guard from the 2026-05-05 audit.
- Extended `find --self-test` so it asserts the DM repro produces exactly
  one `CheckTypeMatchup.Yup` hit on the real `GROUND -> GHOST` type-table
  row (`$04 $08 $00`) and no stack-window hits.

Debugger self-check:
- `python -m tools.damage_debugger.find --self-test` now fails if the
  instrumented hook misses, points at stack memory, loses the HL window,
  or if the existing Stab/TypeMatchup bucket checks regress.
- Invalid hook names return exit code 2 before running the scenario.

Verification:
- `python -m compileall -q tools\damage_debugger` — PASS.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 18/18 scenarios.
- `python -m tools.damage_debugger.oracle` — PASS, 14/14 self-tests.
- `python -m tools.damage_debugger.find --self-test` — PASS.
- `python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup`
  — PASS. Output shows one hit at `CheckTypeMatchup.Yup` with
  `mem[HL-2..HL]=$04 $08 $00`, matching the pre-fix probe's first real
  row and no stack garbage hits.
- `python -m tools.damage_debugger.find --bug dm_hl_clobber --instrument-hook CheckTypeMatchup.Yup --json`
  — PASS, JSON contains the instrumentation payload.
- `python -m tools.damage_debugger.find special_super_effective --instrument-hook NoSuch.Symbol`
  — exit 2 as expected.
- `python tools\audit\check_navigation_floor.py` — PASS.
- `git diff --check` — PASS.

Remaining risk:
- `--instrument-hook` records one symbol per run. That matches the M2 probe
  use case; multi-hook workflows can build on the same `HookRecorder` later.

## 2026-05-06 — H5 SM83 taint tracker

Roadmap item: H5, SM83 byte-level taint tracker.

Change:
- Added `tools.damage_debugger.taint`.
- Implemented byte-level taint state for A/F/B/C/D/E/H/L and memory.
- Added propagation for the SM83 data movement, direct/indirect memory,
  HRAM, stack, ALU, rotate/shift, flag, and common control-flow opcodes
  used by the damage path.
- Added `analyze_tracer(...)`, which consumes a populated
  `tracer.Tracer` instruction/frame stream and returns taint findings.
- Added sink reporting for memory ranges such as `wCurDamage`.
- Added JSON report output for the synthetic fixture path.

Debugger self-check:
- `python -m tools.damage_debugger.taint --self-test` fails if taint no
  longer propagates through register copies, `[hl]` memory loads/stores,
  stack push/pop, ALU combination, the `analyze_tracer` bridge, or memory
  sink reporting.
- `python -m tools.damage_debugger.taint --json-self-test` fails if the
  JSON shape lacks a sink finding.

Verification:
- `python -m compileall -q tools\damage_debugger` — PASS.
- `python -m tools.damage_debugger.taint --self-test` — PASS.
- `python -m tools.damage_debugger.taint --json-self-test` — PASS.
- `python -m tools.damage_debugger.tracer` — PASS, captured VBlank frames
  through the existing per-instruction hook path.
- `python -m tools.damage_debugger.clobber_smoke` — PASS, 18/18 scenarios.
- `python -m tools.damage_debugger.find --self-test` — PASS.

Remaining risk:
- H5 records label/PC origins and sink instructions; source file/line
  rendering still depends on a future source-map layer.
- Unsupported opcodes are counted and clear known destinations rather than
  preserving stale taint. Add handlers as new traced functions demand them.
