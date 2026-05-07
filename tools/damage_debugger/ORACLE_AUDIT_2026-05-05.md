# Oracle audit — 2026-05-05 (post-50k fuzz)

Pass B from the 2026-05-05 handoff: phase-by-phase audit of
`tools/damage_debugger/oracle.py` against the actual asm chain. Goal: produce
the "really 1:1" confidence assessment the user asked for, with concrete
file:line references for every gap and every divergence.

## Tl;dr

- **Pass A (50k fuzz) found a real, previously unknown ROM bug.** The
  matchup loop in `CheckTypeMatchup.Yup` clobbers its own `hl` whenever
  Dragon's Majesty fires, then continues reading the matchup table from
  random stack memory. See "ROM BUG: CheckTypeMatchup hl-clobber" below.
- **Two undocumented oracle gaps in Stab** (DoWeatherModifiers,
  DoBadgeTypeBoosts) were found in this audit. **Closed 2026-05-06 (H3):**
  the oracle and fuzz seed now model both, with deterministic clobber-smoke
  scenarios for sun, rain, and VolcanoBadge.
- **One small fuzz-seed bug** that's harmless today: writes `0x10` (=16)
  for "EFFECTIVE" but `EFFECTIVE = 10`.
- TypePassive's 9-branch logic in the oracle is line-by-line correct.
  The Pass A divergence was 100% upstream (wTypeMatchup was corrupted by
  the new ROM bug, not by an oracle modeling error).

## ROM BUG: CheckTypeMatchup hl-clobber via Dragon's Majesty farcall

### Where

`engine/battle/effect_commands.asm:1493-1512` — the `.Yup` block of
`CheckTypeMatchup`:

```asm
.Yup:
    xor a
    ldh [hDividend + 0], a
    ldh [hMultiplicand + 0], a
    ldh [hMultiplicand + 1], a
    ld a, [hli]                                ; reads mult, hl points at next row
    call CheckTypeMatchup_ApplyDragonsMajestyMultiplier   ; <-- clobbers hl
    ldh [hMultiplicand + 2], a
    ld a, [wTypeMatchup]
    ldh [hMultiplier], a
    call Multiply
    ld a, 10
    ldh [hDivisor], a
    push bc
    ld b, 4
    call Divide
    pop bc
    ldh a, [hQuotient + 3]
    ld [wTypeMatchup], a
    jr .TypesLoop
```

The `call CheckTypeMatchup_ApplyDragonsMajestyMultiplier` chains into
`BattleCommand_ApplyDragonsMajestyMultiplier` (effect_commands.asm:1415-
1424), which `farcall`s into bank 0x0e:

```asm
BattleCommand_ApplyDragonsMajestyMultiplier:
    and a
    ret nz
    push bc
    ld c, a
    farcall TypePassive_ApplyDragonsMajestyMultiplier_Far    ; clobbers hl
    ld a, c
    pop bc
    ret
```

Per `docs/asm_authoring_guide.md` §3.2, the `farcall` macro expands to
`ld hl, target ; ld a, BANK(target) ; rst FarCall`. The `ld hl, target`
clobbers caller's `hl`. The matchup loop's `hl` is therefore gone after
DM fires.

The neighboring per-row matchup block in `BattleCommand_Stab.GotMatchup`
(line 1331-1390) handles this correctly with `push hl` / `pop hl`. The
copy in `CheckTypeMatchup.Yup` does not — that's the bug.

### When it fires

Both conditions:

1. The current matchup row would have mult `NO_EFFECT` (i.e. would make
   the move immune): NORMAL→GHOST, ELECTRIC→GROUND, POISON→STEEL,
   GROUND→FLYING, GROUND→GHOST, PSYCHIC→DARK, GHOST→NORMAL, GHOST→STEEL,
   FIGHTING→GHOST.
2. Attacker has DRAGON contribution > 0, so Dragon's Majesty re-routes
   the row to `NOT_VERY_EFFECTIVE` instead of returning early.

The earlier per-row matchup loop (`BattleCommand_Stab.GotMatchup`) is also
hit by the same DM call but saves `hl` first, so the writeback to
`wCurDamage` is correct. The bug is specifically in the *running-product*
calculation that feeds `wTypeMatchup`, which TypePassive then reads.

### Observed effect

Counterexample from the 50k fuzz pass:
- attacker=lvl 3 NORMAL/DRAGON, GROUND-type physical move BP=27, atk=62, crit
- defender=GHOST/GROUND, def=5
- ROM=19, oracle=21

Trace via `_oracle_audit_probe5.py` (see this directory):

```
Yup: hl=0x4e92  row=(att=0x04, def=0x08, mult=0)   ; real GROUND/GHOST row
Yup: hl=0xdfd5  row=(att=0x04, def=0x04, mult=132) ; STACK garbage (wStackTop=$dfff)
Yup: hl=0xdfe1  row=(att=0x04, def=0x08, mult=13)  ; STACK garbage
End: wTypeMatchup = 85
```

The first match is real. The next two are reading from `0xdfd5` and
`0xdfe1` — both inside the call stack region (wStackTop is at `$dfff`).
The garbage bytes happened to look like (att=4, def=4, mult=132) and
(att=4, def=8, mult=13), which the loop applies as legitimate matchups.
The running product collapses to `wTypeMatchup = 85`.

In TypePassive at `.after_dragon` (line 124): `cp EFFECTIVE + 1` against
85 fails (no carry), so Branch 5 (GROUND-super-eff resist) fires. With
defender having dual GROUND contribution, Branch 5 applies 19/20:
`21 * 19 // 20 = 19`. ROM lands at 19, oracle at 21.

### Severity

This bug means **any DRAGON-contribution attacker hitting a type-immunity
row produces non-deterministic damage** because the corrupted `hl` reads
stack memory whose contents depend on prior call history.

Real-world examples this would affect in the hack:
- Dragonite/Salamence-class attackers using ELECTRIC moves vs GROUND-
  types (would normally be NVE via DM; now random).
- Any DRAGON dual-typed mon using NORMAL or POISON or similar moves vs
  the corresponding immunity-typed defender.
- Importantly, the existing `physical_critical` and similar smoke
  scenarios DO NOT exercise this — they all use Pidgey vs Cyndaquil with
  NORMAL move and no NO_EFFECT row, so DM never fires.

### Why fuzz found this and clobber_smoke didn't

`clobber_smoke.SCENARIOS` only has 8 hand-built scenarios, none of which
have a DRAGON-contribution attacker AND a NO_EFFECT defender row.
Hypothesis at 50k examples explored that corner.

### Suggested fix shape

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

**Don't ship.** Per the 2026-05-05 handoff, the FIRE-low-HP d-clobber
fix is already pending user review — the user wants gameplay-affecting
bug fixes escalated rather than auto-applied. This one materially
changes how Dragon's Majesty interacts with the matchup chart, which is
a balance call.

### Oracle disposition

The oracle currently models the as-intended math (matchup_total = 5 for
NVE-via-DM in this case). After the fix, oracle and ROM will agree. Until
then, the fuzz harness will keep finding this counterexample (and similar
ones) at high example counts — the right call is to mark this scenario
class as a known-bug skip in the same style as the HP-d-clobber, OR
simply leave the divergence as a self-test.

Recommendation: leave the divergence. It serves as a permanent regression
guard — if the bug is fixed, fuzz will report PASS, which is a positive
signal.

## DamageCalc audit (engine/battle/effect_commands.asm:2790-3034)

Oracle reproduces the formula correctly EXCEPT:

| Line(s) | What | Oracle status |
| --- | --- | --- |
| 2809-2813 | `EFFECT_MULTI_HIT` and `EFFECTABLE_CONVERSION` bypass the `BP == 0` early-return | **Not modeled.** Oracle treats `move_bp == 0` as 0 damage unconditionally. |
| 2820-2823 | `xor a; ld [wIsConfusionDamage], a` — entry to `BattleCommand_DamageCalc` (vs `ConfusionDamageCalc`) zeros the confusion-damage flag | **Not modeled.** Confusion-damage path entirely outside oracle scope. |
| 2879-2920 | `TypeBoostItems` loop — Charcoal +10% FIRE, Mystic Water +10% WATER, etc. | **Not modeled.** Documented as a TODO in `oracle.py:25-27` but no fuzz scenario triggers it. |
| 2924 | `callfar ApplyLateGenDamageMultipliers_Far` — Muscle Band, Wise Glasses, Expert Belt, Metronome, Life Orb post-quotient modifiers | **Not modeled.** Documented as a TODO in `oracle.py:23-24`. |
| 2935-2978 | Cap-add-MIN_DAMAGE block. Adds incoming `wCurDamage` to the freshly computed quotient for multi-hit accumulation | **Modeled as of 2026-05-06 M1.** `BattleInputs.initial_cur_damage` lets fuzz/probes seed nonzero incoming damage before DamageCalc. |
| 2935-2939 | `ld b, [hl] ; ldh a, [hQuotient+3] ; add b` reads `[wCurDamage]` (high byte of big-endian) and adds to `hQuotient+3` (LOW byte of quotient). Looks endian-mismatched if `wCurDamage` is nonzero. | **Confirmed ROM bug as of 2026-05-06 M1.** `python -m tools.damage_debugger.cap_add_probe` shows incoming `$0100` produces ROM/current-asm damage 289 vs intended 288. Current oracle/fuzz model the shipped asm so coverage stays green; gameplay fix deferred. |
| 3013-3034 | `.CriticalMultiplier` — `sla` + `rl` doubles `hQuotient[2..3]`, caps at $FFFF on carry | **Modeled correctly.** |

The Q-formula computation lines 2838-2876 (`(2L/5+2)*BP*atk/def/50`) is
modeled correctly including the `c==0 → c=1` minimum-defense clamp.

## Stab audit (engine/battle/effect_commands.asm:1223-1413)

Oracle reproduces this phase EXCEPT:

| Line(s) | What | Oracle status |
| --- | --- | --- |
| 1227-1228 | `cp STRUGGLE; ret z` — STRUGGLE bypasses Stab (and the TypePassive farcall) entirely | **Not modeled.** Documented as a known gap in oracle.py docstring. Benign because the fuzz seed always uses move ID 0x21 (Tackle), but if future scenarios use STRUGGLE this will surface. |
| 1255 | `ld [wCurType], a` — writes the move type to `wCurType`, which **aliases** `wTypeMatchup` (ram/wram.asm:2185-2200, multiple `::` labels at the same address) | **Not modeled.** Harmless because `BattleCheckTypeMatchup` always re-initializes `wTypeMatchup = EFFECTIVE` before using it. Worth knowing about: the probe trace shows wTypeMatchup transition `16 → 4 → 10 → 5 → corrupt → 85` due to this alias. |
| 1260 | `farcall DoWeatherModifiers` — rain/sun weather damage modifiers | **Modeled as of 2026-05-06 H3.** Oracle scans type modifiers before move-effect modifiers, matching asm order; fuzz seeds `wBattleWeather`; clobber_smoke covers sun/rain FIRE cases. |
| 1267 | `farcall DoBadgeTypeBoosts` — player-side badge boost (1.125× damage if player has matching badge for move type) | **Modeled as of 2026-05-06 H3.** Oracle honors `wLinkMode == 0`, player turn only, Johto+Kanto badge bit order, `max(1, damage // 8)`, and `$ffff` cap; fuzz seeds matching badge bits; clobber_smoke covers VolcanoBadge. |
| 1311-1319 | Foresight bypass — `cp -2` marker followed by `bit SUBSTATUS_IDENTIFIED, a` to skip the post-marker rows (NORMAL→GHOST, FIGHTING→GHOST) | **Not modeled** in the per-row matchup loop or in `_matchup_total`. Oracle includes those entries in `_TYPE_MATCHUPS` unconditionally. Not currently a divergence because fuzz seeds `wEnemySubStatus1` zero (= no Foresight), but if a scenario sets it the GHOST-immunity bypass will mismatch. |
| 1338-1344 | `BattleCommand_ApplyDragonsMajestyMultiplier` here, with `push hl` at line 1332 protecting hl across the call. **THIS path is hl-safe**, unlike `CheckTypeMatchup.Yup`. | **Modeled correctly via `_dragons_majesty_applies`.** |
| 1398 | `call BattleCheckTypeMatchup` — recomputes `wTypeMatchup` as a running product. Has the hl-clobber ROM bug (see top of doc). | **Oracle's `_matchup_total` models the as-intended math, not the buggy ROM behavior.** |

## TypePassive audit (engine/battle/type_passive_damage_mods.asm:44-208)

Oracle's `_type_passive_modifiers` reproduces all 9 branches in asm
order with correct fractions. Confirmed by hand against:

- Branch 1 (NORMAL+STAB): line 51-69 — `if has_stab and move_type==NORMAL`,
  `c == 2 → 16/15`, `c == 1 → 31/30`. ✓
- Branch 2 (FIRE-low-HP): line 71-87 — gated by `pristine` flag on the
  oracle side, mirrors known `IsUserBelowOneThirdHP` ROM bug. ✓
- Branch 3 (GHOST-status): line 89-104 — checks `.GetOpponentStatus`
  nonzero, defender GHOST contribution. ✓
- Branch 4 (DRAGON-resist): line 106-121 — gated by `wTypeMatchup <= 10`,
  defender DRAGON contribution. ✓ (but reads buggy `wTypeMatchup` from
  the upstream hl-clobber)
- Branch 5 (GROUND-super-eff): line 123-138 — gated by `wTypeMatchup >= 11`,
  defender GROUND contribution. ✓ (same upstream caveat)
- Branch 6 (ROCK-crit): line 140-155 — checks `wCriticalHit` nonzero,
  defender ROCK contribution. ✓
- Branch 7 (BUG-physical): line 157-172 — `cp SPECIAL` < gate,
  defender BUG contribution. ✓
- Branch 8 (WATER-special): line 174-189 — `cp SPECIAL` >= gate,
  defender WATER contribution. ✓
- Branch 9 (ICE-above-half): line 191-205 — gated by
  `IsOpponentAboveHalfHP` carry-set, defender ICE contribution. ✓
  (Same `pristine` mirror gate as Branch 2.)

The 9 branch bodies are line-by-line correct. The Pass A counterexample's
TypePassive *logic* was right; the divergence was a corrupted
`wTypeMatchup` flowing in.

## Other findings

### Fuzz seed: wTypeMatchup encoding

`tools/damage_debugger/fuzz.py:154`:

```python
write_byte(pyboy, "wTypeMatchup", syms, 0x10)
```

`EFFECTIVE` is 10 (decimal) per `constants/battle_constants.asm`. `0x10`
is 16. The seed value is harmless because `BattleCheckTypeMatchup` always
re-initializes `wTypeMatchup = EFFECTIVE` before using it, but the
constant should be `0x0a` (or just `10`) to match the asm semantics.

### `wCurType` / `wTypeMatchup` aliasing

`ram/wram.asm:2185-2200` declares many labels (`wNamedObjectIndex`,
`wTextDecimalByte`, ..., `wTypeMatchup`, `wCurType`, ..., `wUsePPUp`)
at the same address (no `db`/`ds` between them). `wCurType` and
`wTypeMatchup` are physically the same byte. This is intentional design
(scratch register reuse) but worth noting because `BattleCommand_Stab.go`
overwrites `wTypeMatchup` via the `wCurType` alias before the matchup
loop uses it. The asm explicitly re-initializes via `BattleCheckTypeMatchup`,
so this is benign.

## Confidence assessment

The oracle is line-by-line correct against the asm for the *modeled*
phases (DamageCalc base formula, Stab matchup loop, all 9 TypePassive
branches). The gaps are clearly enumerated above and split into:

- **Documented gaps**: TypeBoostItems, ApplyLateGenDamageMultipliers_Far,
  STRUGGLE, Foresight-substatus, the two HP-d-clobber bug-mirrors.
  H4 on 2026-05-06 added smoke coverage for DamageVariation's ROM range
  and `HandleLateGenAfterHitEffects_Far` HP side effects, but those remain
  outside the exact point oracle.
- **Undocumented gaps surfaced today**: `EFFECT_MULTI_HIT`/`EFFECT_CONVERSION`
  BP=0 bypass. `wCurDamage` non-zero on entry to DamageCalc is now modeled,
  and the cap-add block endian question is confirmed as a ROM bug by M1.
  `DoWeatherModifiers` and
  `DoBadgeTypeBoosts` were on this list when the audit was written; both
  were closed by H3 on 2026-05-06.

For Pass C (extending fuzz to cover gaps), weather and badges were the
highest-leverage oracle axes and are now modeled. H4 also added
deterministic ROM-vs-oracle scenarios for super-effective, resisted, and
immune type rows, plus smoke-only range/state checks for DamageVariation
and after-hit effects.

## Probe scripts kept in this directory (untracked)

- `_oracle_audit_probe.py` — bucket-localized diff (calls find-style
  trace) for arbitrary BattleInputs.
- `_oracle_audit_probe2.py` — hooks every `.after_*` / `.apply_*` /
  `.ApplyCurDamageFraction` label inside TypePassive_ApplyDamageModifiers_Far;
  identifies which branch fires.
- `_oracle_audit_probe3.py` — captures `wCurDamage` / `wTypeMatchup` /
  `wTypeModifier` at entry to TypePassive plus four interior labels.
- `_oracle_audit_probe4.py` — full Stab + CheckTypeMatchup label trace
  with TypesLoop / SkipType / Next / Nope filtered out.
- `_oracle_audit_probe5.py` — captures CPU `hl` register and the bytes
  at `(hl-2, hl-1, hl)` at every `CheckTypeMatchup.Yup` hit. This is
  what surfaced the hl-clobber bug. **Promoted in M2 on 2026-05-06:**
  `find.py --instrument-hook <symbol>` now captures this pattern as
  supported tooling.

These were ad-hoc but encode useful instrumentation patterns. The
`_oracle_audit_probe5.py` pattern is now supported by `find.py`; leave the
remaining probes untracked unless their patterns are promoted by a later
roadmap item.
