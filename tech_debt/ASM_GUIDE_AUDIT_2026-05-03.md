# ASM Guide Audit — 2026-05-03

**Author:** Opus 4.7 audit pass.
**Scope:** Codebase-wide check against `docs/asm_authoring_guide.md`
(938 lines), focusing on the ranked-mistakes section (§3) and best-
practices section (§4). The intent was to find guide-flagged patterns
that aren't already covered by `tech_debt/TECH_DEBT_REPORT.md` or its
addendum.
**Status:** Findings only — no code edited. Items marked **PROMOTE**
are recommended for TD-A### addendum entries if the user agrees.

---

## TL;DR

| ID | Sev | Title | Location |
|----|-----|-------|----------|
| **AG-07** | **CRIT** | **Paralysis fail check is dead — `farcall` a-clobber bug, paralyzed Pokémon never miss a turn** | `engine/battle/effect_commands.asm:334-340, 586-592` |
| AG-01 | HIGH | No automated audit for `farcall` `hl`-clobber (§3.2) | `tools/audit/` (gap) |
| AG-02 | HIGH | **SHIPPED** (audit `d5b8b6a3`, fixes `13a6e3a3`, promote-to-floor `17937d94`) — `tools/audit/check_farcall_a_clobber.py` added; surfaced 5 latent live bugs (4× GetBattleVar farcall callers, 1× TypePassive_IsDarkShieldEligibleEffect_Far) | `tools/audit/check_farcall_a_clobber.py` |
| **AG-08** | **HIGH** | **FIXED** (commit `a6a00ea8`) — Latent §3.3 bug in `Battle_GetEffectiveMoveCategory` — caller never sees the move category in `a`; was masked by accidental `c < 19` at all call sites. Option A applied to both targets (mirror `a -> c` before pop chain). | `engine/battle/type_passive_damage_mods.asm:513-520, 564-571` |
| AG-03 | MED | `check_cross_bank_call.py` failing with 39 known hits in `boss.asm` | `engine/battle/ai/boss.asm` |
| AG-04 | LOW | **SHIPPED** — `tools/audit/check_ld_a_zero.py` added; codemod applied at 40 SAFE sites (per-flag Z/C dataflow analysis); 32 flag-preserving sites correctly preserved | `tools/audit/check_ld_a_zero.py` |
| AG-05 | LOW | **SHIPPED** — `tools/audit/check_cp_zero.py` added; codemod applied at 9 SAFE sites (forward N-flag dataflow); 1 UNSAFE site at `home/map_objects.asm:24` preserved (label boundary at `.loop`) | `tools/audit/check_cp_zero.py` |
| AG-06 | INFO | **SHIPPED** (audio doc `92a187a5`, cold-path conversion `8e93a627`) — audio sites DOCUMENTED as intentional perf (header comment in `home/audio.asm`); 4 cold-path text/battle sites converted to `rst Bankswitch` (`TextCommand_FAR` in `home/text.asm`, `FarCopyRadioText` in `home/battle.asm`) — 16 bytes recovered, ROM SHAs refreshed. | `home/audio.asm`, `home/text.asm`, `home/battle.asm` |

**REVISION HISTORY**
- 2026-05-03 first draft — claimed no live `farcall` bugs.
- 2026-05-03 second pass — found AG-07. The first pass delegated the
  audit to a subagent that hallucinated a target's body and missed
  the paralysis bug. Rerunning the audit directly via a Python
  pattern-scan on the 780 farcall sites, then verifying each hit by
  reading source, surfaced the live bug. Lesson: don't trust subagent
  farcall analysis without verifying every claim against source.
- 2026-05-03 third pass (this revision) — found AG-08 while tracing
  the Falkner damage-inflation bug. Same shape as AG-07; currently
  benign because all callers happen to pass `c < SPECIAL` at the call
  site, so `cp SPECIAL; jr nc` routes correctly anyway. Promoting
  the §3.3 audit (AG-02) would catch both AG-07 and AG-08
  mechanically — strong signal that AG-02 should ship.

Several guide pitfalls were checked and found clean — see "What was
checked clean" at the end.

---

## HIGH — process gaps

### AG-01 — No automated audit for `farcall` `hl`-clobber (§3.2)

**Why this matters.** Per CLAUDE.md, this exact bug class shipped
twice in 6 weeks (April 2026 one-shot damage; May 2026 rival 1
softlock). `farcall` expands to `ld a, BANK :: ld hl, target :: rst
FarCall`, so any caller pattern of the form

```
ld hl, <data>
farcall <Target>     ; Target reads hl as input → bug
```

is silently wrong. CLAUDE.md explicitly notes: *"No automated audit
yet — class-2 audit is on the backlog; for now, manual check on
every new `farcall` whose target reads hl."*

**Spot-check result.** I delegated a class audit. After verifying the
agent's claims against the source, **no live bugs of this shape were
found.** All `ld hl, X` → `farcall Y` sites with safe-looking Y had
intervening code that explicitly mutated hl (so the developer was
already aware), or the hl was being passed as data the farcall macro
itself overwrites with the target address. The repo is clean *today*
for this pattern.

**Risk.** The bug is easy to reintroduce on the next `farcall` added
to a hot file. The lack of an audit means it ships before anyone
notices.

**Recommendation (PROMOTE).** Add `tools/audit/check_farcall_hl_clobber.py`:
1. Parse all `farcall <Target>` sites.
2. For each target, check whether its first ~8 instructions read `hl`
   as input (`ld a, [hl]`, `ld e, [hl]`, `ld b, h`, `inc hl`, `add hl, *`,
   etc.).
3. For each such target, scan callers for the pattern `ld hl, X` (or
   `ld h, * :: ld l, *`) within N instructions before the `farcall`,
   with no intervening `push hl`, `homecall` thunk, or `b/c/d/e`
   reload of hl.
4. Output: list of suspect call sites, similar to `check_cross_bank_call.py`.

This is feasible from static analysis without running the ROM.

---

### AG-02 — No automated audit for `farcall` return-`a` clobber (§3.3)

**Why this matters.** `home/farcall.asm:13-28` ends with
`ld a, [wFarCallBC + 1] :: ld c, a :: ret`, so caller's `a` after a
`farcall` holds **target's exit `c`**, not `a`. CLAUDE.md: *"Not
audited; spot-check by reading target's exit `c`."* This shipped in
May 2026 as the wild-floor no-op (commit `1f5fd6af`).

**Spot-check result.** First pass (delegated to a subagent) returned
"no live bugs found." This was wrong — see **AG-07** below for the
live shipped bug a second-pass scan caught. The subagent had
hallucinated the structure of one of the target functions
(`ProfOaksPC`), which made me trust the rest of its analysis too far.

The second-pass scan (Python regex over all 780 `farcall` sites,
checking the next 1-3 instructions for `a` consumption, then reading
each target by hand) surfaced 10 candidates. Of those:
- **2 are live bugs** (both at AG-07 — same shape, sister sites).
- 5 are legitimate b/c-as-I/O patterns (target sets `c` or `b` at
  exit, caller intentionally reads through the farcall passthrough).
- 3 are false-positive false flags (carry-flag returns,
  hl-consumers, the engine's `and a :: ret` carry-clear idiom).

**Risk.** Same as AG-01 — reintroducible on every new cross-bank
function returning a value in `a`. The fact that AG-07 has been
shipped and not noticed for ~3 months reinforces that humans don't
catch this class without tooling.

**Recommendation (PROMOTE).** Add `tools/audit/check_farcall_a_clobber.py`:
1. Identify cross-bank functions that "return in `a`" (heuristic: last
   instruction before `ret` is `ld a, *` or an arithmetic op leaving a
   meaningful value in `a`, AND no `ld c, a` immediately before).
2. Scan callers of those targets via `farcall` for code that consumes
   `a` (`cp N`, `ld <reg>, a`, `ldh [hX], a`, conditional jumps tied
   to flag-from-a) — excluding the carry-clear idiom (`and a :: ret`,
   `and a :: ret z` followed by no further `a` consumption).
3. Suggest fix: add `ld c, a` before each `ret` in the target.

Trickier than AG-01 because of the carry-clear idiom — but doable.

### AG-08 — Latent §3.3 bug in `Battle_GetEffectiveMoveCategory`

**Status:** **FIXED** (commit `a6a00ea8`). Option A (mirror `a -> c`
at the shared `.done` exit) applied to both
`TypePassive_GetEffectiveMoveCategory_Far` and
`TypePassive_GetLastCounterMoveCategory_Far`. Net +4 bytes of code,
both within bank headroom. The home wrapper text and same-bank caller
shape are unchanged, so `check_battle_math_safety.py`'s
`require_text` invariants continue to pass without loosening.
Verified: pokegold + pokesilver rebuilt, SHAs refreshed in
`roms.sha1`, `check_release_smoke.py` (modulo pre-existing FAILs
unrelated to this work), `check_battle_math_safety.py`,
`check_farcall_hl_clobber.py` all pass.

**(Original finding preserved below for the audit trail.)**

Currently asymptomatic. Same shape as AG-07; only escapes
manifesting because all callers happen to have `c < SPECIAL` at the
call site, so the `cp SPECIAL; jr nc` dispatch routes correctly
anyway. Will fire the moment any caller passes `c >= 19`.

**Sites:**
- Wrapper: `home/battle.asm:259-261`
  ```asm
  Battle_GetEffectiveMoveCategory::
      farcall TypePassive_GetEffectiveMoveCategory_Far
      ret
  ```
- Target: `engine/battle/type_passive_damage_mods.asm:478-518`
  ```asm
  TypePassive_GetEffectiveMoveCategory_Far::
      push hl
      push de
      push bc                ; saves caller's bc on entry
      ; ... compute move category in e ...
  .done
      ld a, e                ; intent: return category in a
      pop bc                 ; ❌ restores c to entry value
      pop de
      pop hl
      ret                    ; ❌ exit c is entry c, NOT category
  ```
- Cross-bank callers of the wrapper:
  - `engine/battle/effect_commands.asm:2516` (PlayerAttackDamage)
  - `engine/battle/effect_commands.asm:2672` (EnemyAttackDamage)

**Why it's broken (mechanism):** per `home/farcall.asm:13-28` (and
guide §3.3), after `farcall` the caller's `a` = target's exit `c`.
The target's `pop bc` restores `c` to whatever was on the stack from
the matching `push bc` at entry — i.e., the caller's pre-call `c`.
So the farcall passthrough delivers `c -> a` of caller's *own* `c`,
not the move category.

**Why it's currently benign:** PlayerAttackDamage / EnemyAttackDamage
both reach this farcall with `c` set to the defender's defense low
byte (an 8-bit stat, typically < 256, often < 19) OR to the move
effect byte (set by `DoMove` at `effect_commands.asm:55`, preserved
through the script dispatcher's `push bc / pop bc`). Many move
effects are < SPECIAL=19 (NORMAL_HIT=0, SLEEP_HIT, POISON_HIT,
etc.). Those route to `.physical` regardless of which value is in
`a` — accidentally correct for physical-typed moves.

The bug surfaces when:
- A caller has `c >= 19` at the call site, AND
- The move's actual category disagrees with the routing the wrong-`a`
  comparison produces.

For physical moves with effect byte ≥ 19 (e.g. EFFECT_DRAGON_DANCE =
0x82, but that's a status move so doesn't reach DamageStats), or when
`c` has been clobbered by a recent BattleCommand_* handler that left
junk in it, the `cp SPECIAL; jr nc, .special` would silently route a
physical move through `.special` (wEnemyMonSpclDef instead of
wEnemyMonDefense), or vice versa.

**The audit is currently load-bearing-wrong.** `tools/audit/check_battle_math_safety.py:314-318`
hardcodes the literal text `"Battle_GetEffectiveMoveCategory::\n\tfarcall TypePassive_GetEffectiveMoveCategory_Far"`
as a require_text invariant. The cleanest fix (option A: mirror
`a -> c` at every `ret` in the target) doesn't change the wrapper, so
the audit doesn't break — but if anyone reaches for option C
(switching the wrapper to `homecall` to dodge the passthrough
entirely), the audit will reject the fix. The audit text should be
loosened to allow either form.

**Recommendation (PROMOTE).** Fix shape, mirroring AG-07's resolution:

```asm
; type_passive_damage_mods.asm:478-518
TypePassive_GetEffectiveMoveCategory_Far::
    push hl
    push de
    push bc
    ; ... existing logic ...
.done
    ld a, e
    ld c, a            ; ✅ mirror a -> c so farcall passthrough works
    pop hl             ; (drop bc/de/hl — note we no longer pop into bc)
    ; ...
    ret
```

Or — equivalently — change the home wrapper to `homecall`:
```asm
Battle_GetEffectiveMoveCategory::
    homecall TypePassive_GetEffectiveMoveCategory_Far
    ret
```
`homecall` doesn't go through `rst FarCall`, so `a` survives intact.
Either fix works. Option A keeps the function safe even if a third
caller is added later that uses `farcall` directly; option C is one
line and matches the existing `SpeciesItemBoost` / `ApplyLateGenDamageStatsItemMods`
home wrappers (`home/battle.asm:267-277`).

`Battle_GetLastCounterMoveCategory` (`home/battle.asm:263-265`) has
**identical shape** wrapping `TypePassive_GetLastCounterMoveCategory_Far`
(`type_passive_damage_mods.asm:545-566`), with a sister `pop bc; ret`
exit. Same fix applies. Both functions should be patched together.

If the §3.3 audit (AG-02) ships, both AG-07 and AG-08 would be
caught mechanically — strong argument for promoting AG-02.

---

## CRITICAL — live shipped bug

### AG-07 — Paralysis fail check is dead; paralyzed Pokémon never miss a turn

**Sites:** `engine/battle/effect_commands.asm:334-340` (player check)
and `engine/battle/effect_commands.asm:586-592` (enemy check). Same
shape both places. Introduced in commit `80c2d5c6` ("battle: add
tactical AI and late-gen mechanics") when the type-passive paralysis
threshold was added.

**TWO independent bugs in the same path** (both shipped together,
both have to be fixed for paralysis to work):

1. **The farcall `a`-clobber** in the caller (described below).
2. **A logic bug in the target** at
   `engine/battle/type_passive_damage_mods.asm:790-801`: the
   original code did `and a; ld a, 25 percent; ret z; cp 2; ld a,
   20 percent; ret nz; ld a, 15 percent; ret`. The `cp 2` runs
   AFTER `ld a, 25 percent`, so it compares the threshold byte
   (64) to 2 — never zero — so `ret nz` always fires. The 15%
   (full Fighting) branch is unreachable, and the function
   collapses to "0 contribution → 25%, anything else → 20%."
   Other passives in the same file get this right by doing `cp 2`
   BEFORE clobbering `a` (e.g. lines 58-66, 76-86, 93-103).

So even before considering the farcall a-clobber, the function would
have returned 25% baseline / 20% half/full Fighting — never the
intended 15%. Combined with the farcall bug, neither branch fires
at runtime, and paralysis is fully dead.

**The buggy code (player side):**
```asm
334    call BattleRandom        ; a = random byte 0..255
335    ld c, a                  ; save random into c
336    farcall TypePassive_GetUserParalysisFailThreshold_Far
337    ld b, a                  ; ❌ author thinks: a = threshold
338    ld a, c                  ; ❌ author thinks: c still = random
339    cp b                     ; ❌ random vs threshold
340    ret nc                   ; ❌ if random ≥ threshold, skip paralysis
```

**Why it's broken:** per `home/farcall.asm:13-28` (and guide §3.3):
- After `farcall`, caller's `a` = target's exit `c` (NOT exit `a`).
- After `farcall`, caller's `b` = target's exit `b`.
- After `farcall`, caller's `c` = target's exit `c`.
- The `ld c, a` at line 335 is silently overwritten.

The target function:
```asm
TypePassive_GetUserParalysisFailThreshold_Far:
    ld a, FIGHTING
    call TypePassive_GetUserTypeContribution_Far
    and a
    ld a, 25 percent  ; threshold goes into a, NEVER into c
    ret z
    cp 2
    ld a, 20 percent
    ret nz
    ld a, 15 percent
    ret
```

Target sets `a` = 64 / 51 / 38 (depending on Fighting-type
contribution). Target's exit `c` is whatever
`TypePassive_GetUserTypeContribution_Far` left there — unrelated to
the threshold.

**What actually executes at runtime:**
- After the farcall: caller's `a` = caller's `c` = target's exit `c`
  (some byte from the type-contribution helper).
- Line 337 `ld b, a` → `b` = target's exit `c`.
- Line 338 `ld a, c` → `a` = target's exit `c` (same value as `b`).
- Line 339 `cp b` → `a == b` always → Z=1, C=0 (no carry).
- Line 340 `ret nc` → C=0 → `nc` is true → return without firing
  paralysis text.

**Effect:** the paralysis-fail RNG check ALWAYS returns at line 340
(player side) and 592 (enemy side) without printing
"FullyParalyzedText" or calling `CantMove`. **Paralyzed Pokémon
always act on every turn.** The Fighting-type half/full reduction is
also moot because the whole check is short-circuited.

**Severity:** CRITICAL.
- Paralysis is a load-bearing status condition for Gen 2 difficulty.
  Thunder Wave / Body Slam / Glare / Stun Spore have effectively no
  passive turn-skip effect in this hack right now. Speed-drop is
  still applied (separate code path), but the 25% miss-a-turn is
  silently disabled.
- This affects every battle in the game where any Pokémon is
  paralyzed — bosses, wilds, rivals.
- It survived through the May 2026 wild-floor fix audit because
  that audit only touched `engine/pokemon/experience.asm`. The same
  bug class lives here, untouched.

**Fix shipped in this branch.** Combined fix for both bugs:

1. **Target restructured** at
   `engine/battle/type_passive_damage_mods.asm:790-810`: do `cp 2`
   BEFORE clobbering `a` (matching the surrounding passives'
   convention), and add `ld c, a` before each `ret` so caller's `a`
   after farcall = threshold:
   ```asm
   TypePassive_GetUserParalysisFailThreshold_Far:
       ld a, FIGHTING
       call TypePassive_GetUserTypeContribution_Far
       cp 2
       jr z, .full
       and a
       jr z, .baseline
       ld a, 20 percent
       ld c, a
       ret
   .baseline
       ld a, 25 percent
       ld c, a
       ret
   .full
       ld a, 15 percent
       ld c, a
       ret
   ```

2. **Both callers** (`effect_commands.asm:334-340` and `586-592`)
   replace `ld c, a` (broken random save) with `push af`, and
   `ld a, c` (broken random restore) with `pop af`:
   ```asm
   call BattleRandom
   push af                                                   ; preserve random
   farcall TypePassive_GetUserParalysisFailThreshold_Far
   ld b, a                                                   ; b = threshold
   pop af                                                    ; a = random
   cp b
   ret nc
   ```

Net delta: target +7 bytes, callers ±0 bytes per site. Both within
bank 0x0e headroom (568 bytes free per the TD-001 addendum).

**Verification after fix.** Save state with player Pokémon paralyzed;
attempt to attack 50 times; expect ~12 turn-skips (25% baseline). If
attacker is part-Fighting, expect lower (15-20%). No turn-skips at
all in current ROM = bug confirmed; turn-skips post-fix = fix
working.

**Audit script.** AG-02 (`check_farcall_a_clobber.py`) would have
caught this. The textbook tell is `ld c, a` immediately before
`farcall X` paired with code that uses `a` post-farcall as if it
were target's exit `a`. Adding the script before fixing this bug
would also surface any other similar cases (5 candidate patterns
that the manual scan classified as legitimate — script could
auto-confirm by checking that target's exit `c` is intentional).

---

## MEDIUM — known but un-actioned

### AG-03 — `check_cross_bank_call.py` failing with 39 known hits in `boss.asm`

Already documented in CLAUDE.md `Build & verification` section:
*"Currently FAIL with 39 known-hits in `engine/battle/ai/boss.asm`;
treat as diagnostic until those are fixed, then promote to
release-smoke floor."*

The guide §3.4 ranks this as the single most common load-bearing
mistake. 39 plain-`call`-cross-bank sites in boss.asm means each call
silently jumps to whatever ROMX bank happens to be paged in at the
moment. Boss AI ships with a fixed bank discipline today, so the bugs
are masked — but any future bank-layout change (e.g. moving boss AI
out of bank 0x0e, which the TD-001 addendum suggests is an option)
will surface them as real crashes.

**Recommendation.** This is a deferred fix already in the project's
awareness, so I'm not flagging it as a new finding — only noting that
it remains the highest-severity guide-§3 violation in the codebase.
Closing it would unblock promoting `check_cross_bank_call.py` to the
release-smoke floor (per CLAUDE.md). Likely scope: convert each
plain `call` to `farcall` or relocate the target to ROM0. Should be
sequenced *after* TD-005 (bank pressure) so there's room to maneuver
if conversions push bytes around.

Not promoting as a TD-A### entry — already tracked in CLAUDE.md and
the audit script itself.

---

## LOW — style / size

### AG-04 — `ld a, 0` instead of `xor a` (73 sites originally)

**Status:** **SHIPPED.** `tools/audit/check_ld_a_zero.py` added,
classifier-plus-codemod applied. 40 SAFE sites rewritten to `xor a`;
32 sites correctly classified UNSAFE and preserved (mostly
`ld a, 0; adc r` 16-bit-pointer-add idioms and `ld a, 0; jr cc`
flag-preserving patterns); 1 INDETERMINATE site preserved
(`home/video.asm:42`, inside a `rept` block where the walk runs out of
budget). Audit promoted to the release-smoke floor so future drift is
caught. Net ~40 bytes recovered, distributed across 24 files / many
banks; per-bank impact small (1-3 bytes typical).

Guide §3.9 / Appendix B: `ld a, 0` is 2 bytes / 2 cycles; `xor a` is
1 byte / 1 cycle. The replacement is **NOT** flag-equivalent — `xor a`
sets Z=1 and clears N/H/C, while `ld a, 0` preserves all four flags.
Mechanical replacement therefore needs per-site safety analysis: walk
forward from each site, track which of {Z, C} are still alive
(unkilled), and treat the site as SAFE only if both are overwritten
before any flag reader runs (or if an unconditional control transfer or
flag-clobbering call/farcall ends the dependency). The `check_ld_a_zero.py`
audit implements exactly this dataflow.

**(Original finding preserved below for the audit trail.)**

The codebase prefers `xor a` consistently in newer code; the
remaining `ld a, 0` sites were mostly inherited from upstream pret.

**Sample sites** (~70 total, not exhaustively listed):
- `engine/movie/credits.asm:10, 508, 543, 553`
- `engine/movie/intro.asm:89, 798`
- `engine/menus/start_menu.asm:424, 437, 458, 471, 478, 488, 534`
- `engine/overworld/player_movement.asm:528, 536, 628, 824`
- `engine/battle/effect_commands.asm:2002, 2381, 3056, 3088, 3109`
- `engine/battle/core.asm:889, 7013, 7914`
- `home/video.asm:42, 142`
- `home/map.asm:6, 1108, 1885`
- `home/print_num.asm:330`
- `audio/engine.asm:928, 986, 989`
- (and ~50 more in tilesets, items, RTC, menus, overworld, etc.)

### AG-05 — `cp 0` instead of `and a` (10 sites originally)

**Status:** **SHIPPED.** `tools/audit/check_cp_zero.py` added,
classifier-plus-codemod applied. 9 SAFE sites rewritten to `and a`;
1 site correctly classified UNSAFE and preserved
(`home/map_objects.asm:24` — the walk crosses the `.loop` label which
is also a back-edge target from `jr nz, .loop`, so other entry points
could carry different flag state). Audit promoted to the release-smoke
floor.

Guide §3.9: `cp 0` is 2 bytes / 2 cycles; `and a` is 1 byte / 1 cycle.
Z and C are identical between the two; N and H differ (`cp 0` sets
N=1, H=0; `and a` sets N=0, H=1). Only `daa` reads N/H, and `daa`
appears only in `home/audio.asm` and `engine/games/slot_machine.asm` —
neither contains a `cp 0` site, so the substitution is universally
safe in this codebase. The audit's forward walk (N-only dataflow,
`daa`-as-reader, arith/shift/call as N-killers, label boundary as
UNSAFE-conservatively) still runs on every build to catch future drift.

**(Original finding preserved below for the audit trail.)**

Initial finding listed 8 sites; full audit found 10 once `cp $0` /
`cp $00` syntactic variants were included.

**All 10 sites:**
- `home/map_objects.asm:24`             — UNSAFE (label boundary)
- `engine/menus/start_menu.asm:525`     — SAFE
- `engine/menus/menu.asm:564`           — SAFE
- `engine/smallflag.asm:56`             — SAFE
- `engine/items/item_effects.asm:1642`  — SAFE
- `engine/overworld/player_movement.asm:232, 550, 798` — SAFE
- `engine/printer/printer_serial.asm:199` (`cp $0`) — SAFE
- `engine/pokemon/mon_menu.asm:623` (`cp $0`) — SAFE

---

## INFO — observed pattern, not a defect

### AG-06 — Inline bank-switch instead of `rst Bankswitch`

Guide §4.6 says *"Don't write to `rROMB` directly; use `rst
Bankswitch`."* But ~25 sites in the codebase do this:

```asm
ldh a, [hROMBank]
push af
ld a, BANK(target)
ldh [hROMBank], a    ; manual hROMBank update
ld [rROMB], a        ; direct rROMB write — bypasses rst Bankswitch
```

**Sites:**
- `home/audio.asm` — 21 instances (every audio entry point: InitSound,
  UpdateSound, _LoadMusicByte, PlayMusic, PlayMusic2, PlayCry, PlaySFX,
  etc.)
- `home/text.asm:680, 690` (text-command engine)
- `home/battle.asm:167, 177` (FarCopyRadioText)

**Verdict.** All 25 sites correctly maintain `hROMBank` shadow (they
do `ldh [hROMBank], a` immediately before `ld [rROMB], a`). So they
**don't** trigger the bug §4.6 warns against — `hROMBank` stays in
sync, subsequent `farcall`s work correctly. The sites just expand the
helper inline instead of calling through `rst Bankswitch`.

**Trade-off.** Each inline expansion is ~4 bytes larger than `rst
Bankswitch` (which is 1 byte vs 5 bytes for `ldh [hROMBank], a` + `ld
[rROMB], a`). But `rst` adds a `call`/`ret` round-trip cost (~6
cycles). For audio, which runs every frame, the inline form is
plausibly intentional perf — but `home/text.asm` and `home/battle.asm`
are colder paths where the trade is less obvious.

**Estimated recovery if all converted:** ~25 × 4 = 100 bytes,
distributed across ROM0. Not in tight banks per TD-001 dev_index.

**Recommendation.** **Not promoting** as a codemod.

**Status (2026-05-04):** **DOCUMENTED.** Header comment added to
`home/audio.asm` explaining that the inline bank-switch pattern is
intentional — `UpdateSound` is in the vblank-driven audio update
path, the entry points each pay two switches (in + restore), and the
~6-cycle-per-switch dispatch overhead of `rst Bankswitch` would
compound across the per-frame audio budget. The comment also notes
that the inline form correctly maintains the `hROMBank` shadow so it
does not trip the §4.6 footgun, and tells future readers not to
codemod the audio sites.

**Cold-path conversion (2026-05-04):** **SHIPPED.** The 4 cold-path
sites at `home/text.asm` (`TextCommand_FAR`, both set + restore) and
`home/battle.asm` (`FarCopyRadioText`, both set + restore) were
converted from inline `ldh [hROMBank], a; ld [rROMB], a` to
`rst Bankswitch`. Bankswitch handler at `home/header.asm:11-15` is
byte-equivalent to the inline pattern (same `a`-preservation, same
`hROMBank` shadow update, same `rROMB` write), and the same idiom is
already used elsewhere in `home/battle.asm` (`StdBattleTextbox`,
`GetBattleAnimPointer`). Net: 16 bytes recovered (4 sites × 4 bytes),
4 ROM SHAs refreshed in `roms.sha1`, 2 .patch SHAs unchanged
(delta-stable — vc and main shifted identically).

---

## What was checked clean

These guide-flagged patterns were searched and produced **zero hits**
or all-correct usage:

| Check | Source | Result |
|-------|--------|--------|
| `callba` (deprecated macro form, Appendix B) | all `.asm` | 0 hits — clean |
| `(hl)` / `(de)` / `(bc)` parenthesized memory (§3.6) | all `.asm` | 0 hits — clean (RGBDS-only `[ ]` syntax used) |
| `jp [hl]` (deprecated, Appendix B) | all `.asm` | 0 hits — clean |
| `ld [$2000], a` direct ROM-bank write (§4.6) | all `.asm` | 0 hits — clean |
| `ld [$FFxx], a` instead of `ldh` (§1.4) | all `.asm` | 0 hits — clean |
| `ld a, [$FFxx]` instead of `ldh` (§1.4) | all `.asm` | 0 hits — clean |
| Capital letters in `INCLUDE` paths (§3.12) | all `.asm` | All matches resolve to real CamelCase filenames (map convention) — clean |
| `\n` in dialog text (§5.7) | `data/text/` | 0 hits — clean |
| Literal `'@'` displayed as glyph (§5.7) | `data/text/common_3.asm`, others | All `@` uses are correct string-terminator usage — clean |
| `table_width` without `assert_table_length` (§4.5) | `data/`, `home/`, `audio/`, `engine/` | 0 files missing the assert — clean (118 files use the pattern) |
| `farcall` `hl`-clobber pattern (§3.2) | second-pass scan over 780 farcall sites | 0 live bugs found — but unaudited (see AG-01) |
| `farcall` return-`a` clobber pattern (§3.3) | second-pass scan over 780 farcall sites | **2 live bugs found at the same site (sister sites) — see AG-07.** Five other save-to-c-then-restore-from-c patterns reviewed manually and confirmed legitimate (target uses `c`/`b` as I/O). |

---

## Recommended sequencing

If the user wants to act on this:

1. **AG-07** — fix the paralysis bug at both sites. Smallest possible
   patch: ~6 lines added (2 per ret in target + HRAM stash in caller).
   Escalate to user before patching — gameplay-impacting change to a
   load-bearing status condition; user owns balance taste. **Do this
   FIRST** because it's a real shipped bug and the fix is small.
2. **AG-02** — write `check_farcall_a_clobber.py`. Will reproduce the
   AG-07 finding and surface any others. Without this, the next
   regression of the same class is inevitable.
3. **AG-01** — write `check_farcall_hl_clobber.py`. Repo is currently
   clean for this pattern but the bug shipped twice in 6 weeks.
4. **AG-04** — codemod `ld a, 0` → `xor a`. Mechanical, safe, ~70
   bytes recovered. Pair with a check script so it doesn't drift back.
5. **AG-05** — codemod `cp 0` → `and a`. Same shape, 8 bytes.
6. **AG-03** — fix the 39 boss.asm cross-bank calls. Larger scope,
   sequenced after TD-005 has freed bank headroom. Promotes
   `check_cross_bank_call.py` to release-smoke floor on completion.
7. **AG-06** — fully closed 2026-05-04. Audio comment shipped (perf
   reason confirmed via `home/vblank.asm` calling UpdateSound on every
   frame; header comment in `home/audio.asm` documents the design
   intent — leave audio inlines alone). 4 cold-path text/battle sites
   converted to `rst Bankswitch` in the same wave (16 bytes recovered).

---

## Caveats

- The audit was static-only — no ROM execution, no runtime tracing.
  AG-01 and AG-02 spot-checks could miss bugs that depend on dynamic
  call-graph reachability.
- The `ld a, 0` / `cp 0` counts came from `^\s*ld a, 0\s*$` /
  `^\s*cp 0\s*$` regexes; they may miss tab-or-not edge cases. Real
  fix would round-trip through a proper RGBDS-aware tokenizer.
- I did not enumerate every `INCLUDE` path, only the suspicious ones.
  Random spot-check of `maps/SproutTower1F.asm` confirmed CamelCase
  filenames are the convention.
- I deliberately skipped `ram/` for guide §3.7 (reordering/resizing
  fields) because TD-002, TD-009 already cover save-format risk.
