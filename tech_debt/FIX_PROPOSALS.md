# Fix Proposals

One section per finding (TD-001 .. TD-013). For each: recommended approach,
files to touch, verification floor, risk, recommended order.

This file **is** editable — future agents can refine recipes as they learn
more. Preserve original proposals: when updating, add an "Updated
YYYY-MM-DD by <session>" subsection and explain what changed. Don't
silently overwrite.

---

## Recommended order

Pick the lowest-numbered open item whose verification floor you can meet
in your session. Quick wins first to recover bytes for the byte-tight
banks; structural work last; release-gated items wait.

### Original order (2026-05-02)

| # | ID | Severity | Why this position |
|---|----|----------|-------------------|
| 1 | TD-010 | MEDIUM | Trivial, no risk, demonstrates workflow |
| 2 | TD-011 | LOW | Trivial, no risk |
| 3 | TD-009 | MEDIUM | Reclaims 30+ WRAM bytes; bounded scope |
| 4 | TD-005 | HIGH | Largest byte-recovery lever (500-700 bytes); relieves TD-001 |
| 5 | TD-013 | LOW | Small file, contained refactor |
| 6 | TD-007 | MEDIUM | Selective pruning of tight banks; relieves TD-001 |
| 7 | TD-006 | HIGH | Readability win; many small touches |
| 8 | TD-004 | HIGH | Structural; do after byte recovery makes bank moves possible |
| 9 | TD-012 | LOW | Cosmetic Makefile cleanup |
| 10 | TD-008 | MEDIUM | RGBDS upgrade; needs validation budget |
| 11 | TD-001 | CRITICAL | Re-evaluate after #4, #6 done — strategic, not localized |
| 12 | TD-002 | CRITICAL | Release-gated (waits for SAVE_FORMAT_VERSION bump) |
| 13 | TD-003 | CRITICAL | Release-gated; partial fix possible after TD-005 byte recovery |

### Updated 2026-05-02 — current ranking

After closing TD-010 and disputing TD-011, plus splitting TD-009 into
TD-009a (HRAM, escalation-gated) and TD-009b (WRAM, release-gated):

| # | ID | State | Severity | Why this position |
|---|----|-------|----------|-------------------|
| — | TD-010 | **done** | MED | closed via corrected recipe; ADDENDUM 2026-05-02 |
| — | TD-011 | **disputed** | LOW | script IS used by docs/manifest.md; ADDENDUM 2026-05-02. Skip. |
| — | TD-009a | **escalation** | MED | dead-write removal needed; ADDENDUM 2026-05-02. Wait for user OK. |
| 1 | TD-005 | open | HIGH | byte-recovery lever (now scoped 150-450 bytes per "Updated 2026-05-02"); relieves TD-001 |
| 2 | TD-007 | open | MED | selective pruning of tight banks; relieves TD-001. Beta blocks first. |
| 3 | TD-006 | open | HIGH | constants naming; gameplay-side escalation on values AND names |
| 4 | TD-004 | open | HIGH | structural boss.asm split; do AFTER TD-005 frees bank space |
| 5 | TD-013 | open | LOW * | EXP cleanup; SHA1 must match (see "Updated 2026-05-02"). * effective MEDIUM per ADDENDUM |
| 6 | TD-012 | open | LOW | optional Makefile shell-hack cleanup |
| 7 | TD-008 | open | MED | RGBDS upgrade; research current version first ("Updated 2026-05-02") |
| 8 | TD-001 | open | CRIT | re-evaluate after TD-005 + TD-007 close — strategic, not localized |
| 9 | TD-009b | open | MED | WRAM unused fields; release-gated alongside TD-002 (next save-format bump) |
| 10 | TD-002 | pending-trigger | CRIT | release-gated (waits for SAVE_FORMAT_VERSION bump) |
| 11 | TD-003 | open | CRIT | release-gated; partial fix (audit + comments) possible without bump |

Quick wins were front-loaded in the original order to "demonstrate
workflow." The workflow is now demonstrated (TD-010 closed via
ADDENDUM-corrected recipe, TD-011 disputed). Remaining ranking
prioritizes byte recovery (TD-001 pressure) over readability /
structural / release-gated work.

---

## TD-001 — Bank exhaustion

**Severity:** CRITICAL. **Order:** 11 (re-evaluate after byte-recovery
items).

### Approach

This is **not a single fix**. It's a strategic constraint. Address by:

1. **Recover bytes first** via TD-005 (macro extraction), TD-007 (label
   pruning in tight banks).
2. **Move co-located code out of bank 0x0e** if the boss AI / late-gen
   items / type passives still don't fit. Candidates for relocation:
   - `engine/battle/type_passive_damage_mods.asm` → ROMX 0x0a or 0x0d
     (currently 6 bytes free, but pruning may open it).
   - `engine/battle/late_gen_held_items.asm` → similar.
3. **Lock pic banks**. Banks 0x12, 0x15, 0x17, 0x1b, 0x1c, 0x1e, 0x1f are
   pic data — they grow when a Pokémon's sprite size changes. Add a
   pre-commit guard to flag pic-byte-count growth in tight banks. (New
   audit script: `tools/audit/check_pic_bank_pressure.py`.)

### Files to touch

- `layout.link` (if relocating sections)
- `main.asm` (section declarations)
- New: `tools/audit/check_pic_bank_pressure.py`

### Verification

```bash
python3 scripts/generate_dev_index.py --rom pokegold
# Re-read docs/generated/dev_index.md Memory Summary; tight banks must
# show > 16 bytes free across the board, ideally > 64.
make compare   # ROM SHA1 must match roms.sha1
```

### Risk

**HIGH for relocation.** Section moves change ROM layout, which can
silently break code that depends on `BANK(label)` returning a specific
value. Audit `farcall` chains carefully if a bank reassignment moves a
hot-path function. Run the full audit suite, not just the smoke test.

### Estimated effort

- Re-evaluation pass after TD-005 + TD-007: 1 session.
- Section relocation (if needed): 2-3 sessions including verification.
- Pic-bank guard script: 1 session.

### Updated 2026-05-03 — bank pressure refresh after TD-005 P1 + TD-007

The 2026-05-02 approach assumed bank 0x0e was the canary at 6 bytes free. Per ADDENDUM 2026-05-03, that's no longer true: 0x0e is now at 568 free (drifted before report time + 41 from TD-005 P1). The new canary is ROMX 0x0d (Effect Commands, 6 free). See ADDENDUM for the full delta and updated relocation targets.

**Revised approach:**

1. **Continue byte recovery via remaining levers.** TD-005 Pattern 2 (multiply/divide thunk) and Pattern 3 (`hBattleTurn` side-branch) are the largest open levers. Pattern 2 is gated on user WIP in `engine/pokemon/experience.asm`; Pattern 3 needs site enumeration (234 candidates → filter to actual side-branch shape, write to `tech_debt/EVIDENCE/td_005_pattern3_sites.md`). TD-009a (HRAM dead-write removal, 2 bytes) is the smallest live lever and is gated on user OK.
2. **Skip bank-0x0e relocations.** Original Approach #2 (move `late_gen_held_items.asm` / `type_passive_damage_mods.asm` to ROMX 0x0a or 0x0d) is no longer needed. 0x0e has 568 bytes free; 0x0d is the new canary so relocating *into* 0x0d is the wrong direction.
3. **Pic-bank guard still applies.** Approach #3 unchanged. Pic banks (0x12, 0x15, 0x17, 0x1b, 0x1c, 0x1e, 0x1f) all at 0-1 free; growth in any single Pokemon sprite size silently breaks link. Add `tools/audit/check_pic_bank_pressure.py`.
4. **Watch new tight regions.** WRAM0 at 49 free, ROMX 0x16 at 48 free. Both newly entered the tight-banks list. Not action items today, but flag if future findings touch global WRAM or that bank.

**Re-evaluation closure:** TD-001 stays `partial` as a strategic monitoring item until the open byte-recovery levers (TD-005 P2/P3, TD-009a) close and the pic-bank guard lands. After those, the bank-pressure picture stabilizes and TD-001 can move to `accepted` (intentionally monitored — not actively fixable beyond byte recovery).

---

## TD-002 — Legacy save format v1→v2 cleanup

**Severity:** CRITICAL. **Order:** 12 (release-gated).

### Approach

This finding is **dormant until** `SAVE_FORMAT_VERSION` bumps. The fix is
trivial mechanically (delete the `$FF` accept paths), but the **trigger**
is the version bump itself, which is a save-format change shipping to
public release — an escalation item.

When triggered:

1. Bump `SAVE_FORMAT_VERSION` in `constants/misc_constants.asm`.
2. Remove `$FF` accept logic from `engine/menus/save.asm:640` and
   `engine/menus/save.asm:668`. Those paths should now reject (not
   silently accept) unmarked saves.
3. Update the comment at `constants/misc_constants.asm:34-37` to drop
   the v1-only language.
4. Update `ram/sram.asm:105, 175` comments accordingly.
5. Run `tools/audit/check_save_format_version.py`.

### Files to touch

- `constants/misc_constants.asm`
- `engine/menus/save.asm` (two locations)
- `ram/sram.asm` (comment-only updates)

### Verification

```bash
python3 tools/audit/check_save_format_version.py
python3 tools/audit/check_release_smoke.py
make compare
```

Plus playtest: load a save from current version, confirm normal load.
Load a v0/legacy save, confirm proper rejection (not silent accept).

### Risk

**MEDIUM-HIGH.** Save-format changes ship to the public — escalation
item. Wait for human approval to bump the version. Once bumped, the
deletion itself is mechanical.

### Estimated effort

15 minutes after trigger event.

### Until triggered

Do **not** mark TD-002 done. Leave open with a `pending-trigger:` log
entry. The role of this finding in the report is to ensure the cleanup
isn't forgotten when the trigger fires.

---

## TD-003 — Hard-coded `org` addresses in `layout.link`

**Severity:** CRITICAL. **Order:** 13 (release-gated / managed).

### Approach

Most of these `org` pins exist because the Stadium 2 checksum tool and the
graphics pipeline expect specific addresses. Cleanup options, in order
of feasibility:

1. **Add a build-time invariant audit.** A new `tools/audit/check_layout_orgs.py`
   that asserts each pinned section is followed by enough `ds` padding
   to absorb expected growth. Cheap. Doesn't fix the pin but makes
   silent breakage loud.
2. **Document the contracts.** Add comments next to each `org` in
   `layout.link` explaining why it's there and what breaks if moved.
3. **Move the Stadium 2 checksum to a dedicated bank** (most fragile case).
   The pin at `0x7f:$7df8` is there because Stadium 2 reads checksums at
   fixed ROM offset `0x1ffdf8`. Verify whether Stadium 2 actually requires
   that exact offset, or whether it reads via the bank-mapped address.
   If the latter, the section can move freely.

Option 1 is safe and high-value — do it first.
Options 2-3 require understanding upstream Stadium 2 behavior.

### Files to touch

- New: `tools/audit/check_layout_orgs.py`
- `layout.link` (comment additions)
- Possibly `Makefile` lines 138-145 (stadium checksum step)

### Verification

```bash
python3 tools/audit/check_layout_orgs.py
make compare
# If Stadium 2 support matters: physically test on hardware/emulator
# with Stadium 2 transfer.
```

### Risk

**HIGH for option 3 (relocation).** Silent breakage of Stadium 2 transfer
is the worst-case failure — you wouldn't know until a player tried it.
**LOW for option 1-2** (audit + comments).

### Estimated effort

- Option 1 (audit + comments): 1 session.
- Option 3 (relocation + verification): multi-session, requires hardware
  testing.

### Updated 2026-05-03 by claude-trusting-kare-692dd4

Option 1 and Option 2 shipped this session. TD-003 moves from `open` to
`partial`.

- **Option 1 (audit) — done.** `tools/audit/check_layout_orgs.py` parses
  `layout.link`, extracts all (bank, address, following-section) tuples,
  and compares against `EXPECTED_PINS` — currently 5 entries
  (`$12:$4000 → Pic Pointers`, `$1f:$4000 → Unown Pic Pointers`,
  `$2e:$6300 → bank2E`, `$31:$7a40 → bank31`,
  `$7f:$7df8 → Stadium 2 Checksums`). FAIL with side-by-side diff if
  the layout drifts. PASS verified plus drift simulation (moved Stadium
  pin → correctly detected).
- **Option 2 (documentation) — done.** `docs/layout_pins.md` covers
  each pin's source declaration, what it backs, why it's pinned, and
  what breaks downstream if removed. Cross-references TD-003 in
  `tech_debt/`.

**Option 3 still release-gated.** Stadium 2 relocation — confirming
whether Stadium 2 reads checksums via fixed ROM offset or bank-mapped
address — requires hardware/emulator testing on a Stadium 2 transfer.
Not closeable without that environment.

The audit's verification floor for any future intentional pin change:
update `EXPECTED_PINS` in the audit AND `docs/layout_pins.md` in the
same change. The audit's fail-mode message instructs the reviewer
explicitly.

#### Done criteria for full close

When Option 3 is dispositioned (either Stadium 2 verifies it doesn't
need the fixed offset and the pin gets removed, OR Stadium 2 testing
confirms the pin must stay and TD-003 moves to `accepted`), the finding
fully closes. Until then, `partial` is the steady state — Option 1
catches accidental drift; Option 2 documents the intentional contract.

---

## TD-004 — Split `boss.asm`

**Severity:** HIGH. **Order:** 8 (after byte recovery).

### Approach

Split `engine/battle/ai/boss.asm` (7,006 lines) along concern boundaries.
Proposed split:

| New file | Contents |
|----------|----------|
| `engine/battle/ai/boss_state.asm` | WRAMX bank 1 init/clear, seen-species tracking, revealed-moves bitmap |
| `engine/battle/ai/boss_typing.asm` | Plausible/likely type-mask inference, type-contribution helpers |
| `engine/battle/ai/boss_scoring.asm` | Score computation, weight tables, tier weight rows |
| `engine/battle/ai/boss_setup.asm` | Setup-boost evaluation (`SetupBoostHasFurtherValue`, speed cap, etc.) |
| `engine/battle/ai/boss_moves.asm` | Move-selection, saved enemy move struct |
| `engine/battle/ai/boss.asm` | Top-level dispatch, public entry points |

### Critical caveats

- **Local labels (`.foo`) are scoped to the assembler unit, not the file.**
  Moving a routine that contains local labels to a new file works as long
  as no other routine in the original file references those labels.
  Verify with `grep` before moving.
- **`::` exports must be preserved.** Any routine called from outside the
  AI subsystem (or from another AI file post-split) must keep `::`.
- **Bank co-location.** All split files must end up in the same bank
  (currently 0x0e — see TD-001) unless explicitly moved. Verify
  `BANK(label)` invariants don't change post-split.
- **`farcall` chains.** Re-run `tools/audit/check_farcall_hl_clobber.py`
  after splitting — moving a routine across files can change which
  `farcall` paths are exercised.

### Procedure

1. Identify routines belonging to each new file by reading top-level
   labels (152 of them) and grouping by purpose. Use `grep '^\w.*::'
   engine/battle/ai/boss.asm` for the list.
2. For each group, before moving: `grep '^\.\w' boss.asm` for local
   labels in that routine; verify no out-of-routine references via
   manual inspection of nearby code.
3. Cut+paste routines into new files. Add `INCLUDE` directives in
   `main.asm` (or wherever boss.asm is currently included).
4. Build. If link fails on missing `::`, add the export. If link fails on
   bank overflow, the split won't work without TD-005 first.
5. Run the full audit suite.

### Files to touch

- `engine/battle/ai/boss.asm` (shrinks)
- New: `engine/battle/ai/boss_state.asm`, `boss_typing.asm`,
  `boss_scoring.asm`, `boss_setup.asm`, `boss_moves.asm`
- `main.asm` or `engine/battle/ai/ai.asm` (INCLUDEs)
- `docs/agent_navigation/source_output_ownership.md` (update map)

### Verification

```bash
make pokegold.gbc                    # must link
make compare                          # SHA1 must match
python3 scripts/generate_dev_index.py --rom pokegold
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_boss_ai_no_cheat.py
python3 tools/audit/check_boss_ai_trace_invariants.py
python3 tools/audit/check_boss_ai_memory_budget.py
python3 tools/audit/check_farcall_hl_clobber.py
```

ROM SHA1 must be **identical** post-split (refactor only, no behavior
change). If it isn't, the split silently changed something.

### Risk

**HIGH.** Largest single refactor in this list. Local-label scoping
mistakes are subtle and produce link failures or worse, runtime bugs
that pass linking. Do this only after TD-005 has freed bank space, so
you have headroom for any bank-realignment side effects.

### Estimated effort

3-5 sessions (split, audit fixes, verification, doc updates).

---

## TD-005 — Extract macros for duplicated boilerplate

**Severity:** HIGH. **Order:** 4 (primary byte-recovery lever).

### Approach

Three macros to add. Each replaces a recurring pattern.

#### Macro 1: `check_held_item ITEM`

For pattern 1 (item-check-and-return), 12 instances in
`late_gen_held_items.asm`.

Proposed location: `macros/scripts/battle.asm` (or new
`macros/scripts/held_items.asm`).

```asm
; Returns to caller's caller if user item != ITEM. Preserves hl, bc.
check_held_item: MACRO
    push hl
    push bc
    callfar GetUserItem
    ld a, b
    pop bc
    pop hl
    cp \1
    ret nz
ENDM
```

(And `check_opponent_item` for the `GetOpponentItem` variant.)

Replace:
```asm
push hl
push bc
callfar GetUserItem
ld a, b
pop bc
pop hl
cp HELD_CHOICE_BAND
ret nz
```
with:
```asm
check_held_item HELD_CHOICE_BAND
```

12 instances × 7 instructions saved = ~84 bytes recovered.

#### Macro 2: `multiply_then_divide`

For pattern 2 (multiply/divide setup), 18 instances across 3 files.

Tricky — the operands vary. Cleanest form: a helper **subroutine** in
ROM0, not a macro. Existing helpers already exist (`Multiply`, `Divide`)
but the setup boilerplate (zero hMultiplicand, copy product to dividend)
is what duplicates. A small `MultiplyThenDivide` thunk in ROM0 that
takes pre-loaded operands in registers/HRAM and chains the two ops would
be ~12 bytes itself, save ~30 bytes per use × 18 = ~540 bytes.

Caveat: this is ROM0 — verify space before adding. ROM0 fullness shown
in `docs/generated/dev_index.md`.

Alternative if ROM0 is full: place in a non-tight ROMX bank with a
homecall thunk.

#### Macro 3: `get_sided_addr`

For pattern 3 (`hBattleTurn` side-branch), 100+ instances. Most-used
pattern.

```asm
; HL = (player turn) ? \1 : \2
get_sided_addr: MACRO
    ldh a, [hBattleTurn]
    and a
    ld hl, \1
    jr z, .got\@
    ld hl, \2
.got\@
ENDM
```

Saves ~5 instructions per use × 100 = ~500 bytes if all replaced. Many
sites have local labels (`.player`, `.got`) collision risk — use `\@`
(macro counter) for unique label generation as shown.

### Files to touch

- New macros: `macros/scripts/held_items.asm` and/or
  `macros/scripts/battle.asm`
- `engine/battle/late_gen_held_items.asm` (12 replacements)
- `engine/battle/type_passive_damage_mods.asm` (multiple replacements)
- `engine/pokemon/experience.asm` (multiply/divide replacements)
- `engine/battle/core.asm` (potentially many `get_sided_addr` sites)
- `home/farcall.asm` (if adding ROM0 thunk for multiply/divide)

### Verification

```bash
make pokegold.gbc
make compare    # SHA1 MUST MATCH — macro replacement is refactor-only
python3 scripts/generate_dev_index.py --rom pokegold
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_battle_math_safety.py
```

If SHA1 doesn't match: **stop**. The macro changed behavior somewhere.
Bisect by reverting macro replacements file-by-file until SHA1 matches,
then debug the differing site.

### Risk

**MEDIUM.** Macros are correct as designed but every replacement site is
an opportunity to introduce a typo. Replace one site at a time, building
between, until you trust the macro. Then bulk-replace.

### Estimated effort

2-3 sessions:
1. Define macros, replace one site of each, verify SHA1.
2. Bulk-replace all sites of macros 1 and 3.
3. Macro 2 (multiply/divide thunk) — careful work.

### Bytes recovered (target)

500-700 bytes total. Banks 0x0d and 0x0e benefit most. Re-check tight
bank table after this finding closes.

### Updated 2026-05-02 by claude-adoring-curie-e2563e

The original "500-700 bytes recovered" headline doesn't survive
arithmetic — see `META_AUDIT.md` TD-A05. Three correctable mistakes:

1. **Macros don't shrink ROM, subroutines do.** A `MACRO` expansion
   emits the same bytes per call site as inline code. Pattern 1
   (item-check) as written is a macro; recovery is **~0 bytes**, not
   ~96. To get real recovery, the pattern needs to become a `call`
   to a shared subroutine (which adds ~3 bytes per site for the call,
   minus the boilerplate length per site).
2. **Pattern 2 (multiply/divide) thunk math is optimistic.** The
   per-site savings of "~30 bytes" assumed the thunk replaces all
   operand-loading boilerplate. In practice the operands vary per
   site, so the thunk only replaces the chained
   `Multiply`+`Divide`+result-copy steps. Realistic per-site recovery:
   ~10-20 bytes.
3. **Pattern 3 (`hBattleTurn` side-branch) is unenumerated.** The
   "100+ instances project-wide" claim has no file:line list (see
   `META_AUDIT.md` TD-A06). Recovery is real if converted to a shared
   subroutine, speculative until measured.

#### Corrected scope and approach

- **Pattern 1:** convert to a shared **subroutine** in the same bank
  as `late_gen_held_items.asm` (currently bank 0x0e — tight; verify
  free space first). Define `_CheckHeldItem` taking the item constant
  in `b`, returning `z` if matched. Each site becomes ~5 bytes
  (`ld b, HELD_X` + `call _CheckHeldItem` + `ret nz`). Per-site
  savings: ~8-10 bytes. 12 sites × 9 = ~108 bytes.
- **Pattern 2:** `MultiplyThenDivide` thunk in ROM0 (verify ROM0
  fullness first per `dev_index.md`). Per-site savings: ~10-20 bytes.
  18 sites × ~15 = ~180-360 bytes.
- **Pattern 3:** before doing any work, **enumerate the actual sites**
  via `grep -rn 'ldh a, \[hBattleTurn\]' --include='*.asm' | wc -l`.
  Record the list to `tech_debt/EVIDENCE/td_005_pattern3_sites.md` (new
  file). Then convert to a shared subroutine `_GetSidedAddr` taking
  player addr in `de`, enemy addr in `bc`, returning the right one in
  `hl`. Per-site savings: ~5 bytes if enumeration confirms the rough
  count.

#### Realistic byte-recovery target

**150-450 bytes total**, with the actual number measured at first
conversion. Drop the headline "500-700 bytes" — that was wishful.

#### Mandatory measurement step (new)

After converting the **first** site of any pattern:
1. Build before and after (`pokegold.gbc.before`, `pokegold.gbc.after`).
2. Diff the `.map` file's bank-size summary — the actual ROM byte
   delta is the only ground truth.
3. Multiply by remaining-site count for a projection. Stop and
   re-evaluate if projection is < 100 bytes — the refactor cost
   probably outweighs the savings.

#### Verification floor (unchanged)

`make compare` SHA1 match is **not** required for TD-005 (this finding
deliberately changes ROM contents to recover bytes). Replace SHA1
match with: build succeeds, audit suite green, and `dev_index.md`
shows tight banks gained free space.

If SHA1 was the floor: subroutine extraction would be impossible
(call-site bytes shift). The original "SHA1 MUST MATCH" line in the
Verification section above is **wrong for this finding** and should
be ignored. Use map-file bank-size diffing as the verification
mechanism instead.

#### Done criteria

After all three patterns converted:
1. Update `STATUS.md` TD-005 row to `done`, with measured byte total
   in `Notes`.
2. `AGENT_LOG.md` `done:` entry includes the byte measurement table
   (per-pattern, per-site).
3. `tech_debt/EVIDENCE/td_005_pattern3_sites.md` exists if pattern 3
   was attempted.

---

## TD-006 — Name the magic numbers

**Severity:** HIGH. **Order:** 7.

### Approach

Three independent sub-fixes. Each is small.

#### TD-006a: paralysis failure constants

`engine/battle/type_passive_damage_mods.asm:950-955`. Add to
`constants/battle_constants.asm`:

```asm
BASELINE_PARALYSIS_FAIL_PCT       EQU 25
ELECTRIC_PARALYSIS_FAIL_PCT       EQU 21    ; or whatever the design value is
ELECTRIC_PARALYSIS_FAIL_PCT_FULL  EQU 41    ; (etc — match the existing values)
```

Replace literals with the constants. Verify with the user that the
**values** are the design intent — these are balance values; he owns the
taste call. (Authority note: this is the kind of thing to escalate
gameplay-side.)

#### TD-006b: nibble masks in experience.asm

`engine/pokemon/experience.asm:56-58, 92-94`. Lower-priority cosmetic
fix. Add to a local constants block in the file:

```asm
EXP_GROWTH_HIGH_NIBBLE_MASK EQU $f0
EXP_GROWTH_LOW_BITS_MASK    EQU $7f
```

#### TD-006c: gym cap table labels

`engine/pokemon/experience.asm:198-206`. Convert `db 14, 17, 21, 26, 34,
34, 34, 39` to:

```asm
.NextJohtoGymCaps:
    db 14 ; FALKNER
    db 17 ; BUGSY
    db 21 ; WHITNEY
    db 26 ; MORTY
    db 34 ; CHUCK
    db 34 ; JASMINE
    db 34 ; PRYCE
    db 39 ; CLAIR
```

Verify gym order against existing trainer order constants
(`constants/trainer_constants.asm`).

### Files to touch

- `constants/battle_constants.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `engine/pokemon/experience.asm`

### Verification

```bash
make pokegold.gbc
make compare    # SHA1 MUST MATCH — naming-only refactor
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_battle_math_safety.py
```

### Risk

**LOW.** Naming-only changes. SHA1 should match exactly.

**Escalation:** if you discover the existing values look like balance
errors (e.g. inconsistent rounding), do **not** fix them — that's a
gameplay taste decision. Log to `AGENT_LOG.md` and surface to the user.

### Estimated effort

1 session.

---

## TD-007 — Selective label pruning

**Severity:** MEDIUM. **Order:** 6.

### Approach

**Do not** delete unreferenced labels broadly — they are harmless in
loose banks and removing them is churn. The high-value targets are
**unreferenced labels in tight banks** (TD-001).

Procedure:

1. From `docs/generated/dev_index.md` Memory Summary, identify which
   bank each tight bank's contents come from. Bank 0x0e covers Boss AI
   + Late Gen + Type Passives — well-tended, few unused labels there.
   Banks 0x0d (battle engine), pic banks (0x12-0x1f) are different.
2. For each tight bank, list its source files (cross-reference
   `main.asm` SECTIONs against bank assignments).
3. Within those files, find labels marked `; unreferenced`. Confirm via
   `grep -rn 'LabelName'` they truly have zero refs (the `;
   unreferenced` comment is a hint, not proof).
4. Delete the label and its body. Run audits.

**Pic-bank labels (0x12, 0x15, 0x17, 0x1b, 0x1c, 0x1e, 0x1f, 0x1a):**
these are pic data, not code. Pruning unused beta-pic data is
high-value. The 48 `Beta*_Blocks` entries in `data/maps/blocks.asm`
should be the first target.

**Stale reward text:** already guarded by `check_release_smoke.py`. Do
**not** re-prune; the guard catches new ones.

### Files to touch

Varies by bank. High-priority targets:
- `data/maps/blocks.asm` (Beta\*_Blocks — large)
- `engine/battle/core.asm` (10+ unused utilities — but verify bank
  before deleting)
- `home/map_objects.asm`, `home/menu.asm`, `home/text.asm` — but these
  are in HOME (ROM0), check ROM0 fullness before deleting

### Verification

```bash
make pokegold.gbc
# SHA1 will NOT match — code is being deleted. That's expected for this
# finding only. Update roms.sha1 only after verification.
python3 scripts/generate_dev_index.py --rom pokegold
# Confirm tight bank free-byte count went UP, not down.
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_workspace_hygiene.py
```

This is the **one finding where SHA1 changes are expected**. Record the
new SHA1 in `roms.sha1` only after a build verifies and at least one
manual playtest confirms gameplay parity. Escalate the SHA1 update to
the human.

### Risk

**MEDIUM.** Deleting "unreferenced" code is straightforward, but the
`; unreferenced` annotation is sometimes wrong — a label may be
referenced via a pointer table or computed jump. Always grep for the
label name (and any adjacent labels) before deletion.

### Estimated effort

1-2 sessions per major bank cleaned.

---

## TD-008 — Upgrade RGBDS

**Severity:** MEDIUM. **Order:** 10.

### Approach

1. Pick target version. As of 2026, RGBDS v1.7+ likely. Read the RGBDS
   changelog (https://rgbds.gbdev.io/) to understand syntax/behavior
   changes between v1.0.1 and target.
2. Test build with target RGBDS in a worktree:
   ```bash
   wsl -e bash -lc 'cd ".../pokemon gold hack" && make -j4 PYTHON=python3 \
       RGBASM=rgbds-X.Y.Z/rgbasm.exe \
       RGBLINK=rgbds-X.Y.Z/rgblink.exe \
       RGBFIX=rgbds-X.Y.Z/rgbfix.exe \
       RGBGFX=rgbds-X.Y.Z/rgbgfx.exe pokegold.gbc'
   ```
3. Resolve assembler errors (deprecated syntax, changed warning
   behavior).
4. Verify SHA1 still matches `roms.sha1`. If RGBDS changes how it
   encodes optimal rst forms or similar, ROM bytes can shift — that's
   a real concern requiring careful diff.
5. Update CI:
   - `.github/workflows/main.yml:9, 22, 78`
   - `CLAUDE.md` build command
   - Any audit/journal references to `rgbds-1.0.1/`

### Files to touch

- `.github/workflows/main.yml`
- `CLAUDE.md`
- `tech_debt/PROJECT_CONTEXT.md` (this folder)
- `rgbdscheck.asm` (update minimum version)

### Verification

```bash
make pokegold.gbc
make compare
# Run the FULL audit suite — RGBDS upgrade is project-wide.
for f in tools/audit/check_*.py; do python "$f"; done
```

If SHA1 doesn't match after RGBDS upgrade and you've ruled out behavior
changes: this may be a known RGBDS version behavior. Document in
`AGENT_LOG.md` with a `roms.sha1` update justified by the upgrade.

### Risk

**MEDIUM-HIGH.** RGBDS version bumps have shipped behavior changes in
the past. Allocate a full session to validation. Be prepared to roll
back and stay on v1.0.1 if any diff can't be explained.

### Estimated effort

2-3 sessions. Could be more if syntax changes touch many files.

---

## TD-009 — Remove unused RAM fields

**Severity:** MEDIUM. **Order:** 3 (quick win, real bytes recovered).

### Approach

For each field in `FINDINGS_DETAIL.md` TD-009 confirmed-unused list:

1. **Triple-check no references.** `grep -rn 'wUnusedFieldName'` must
   return only the definition itself. Some `Unused`-prefixed fields
   ARE used despite the name (the detail file lists known false
   positives — `wUnusedSlotReelIconDelay`, etc.).
2. Delete the `ds N` line in `ram/wram.asm` or `ram/hram.asm`.
3. **Critical:** save format. WRAM ordering is part of the save layout
   for the SRAM-backed structures. Most of these unused fields are
   **outside** the SRAM-backed region (check `ram/sram.asm`), so
   deletion is safe — but verify each field is not within an SRAM
   structure before removing.
4. If a field IS within an SRAM structure: replace with `ds N` of the
   same size (placeholder) rather than deleting, to preserve save
   layout.
5. Run `tools/audit/check_save_format_version.py` after each batch.

### Files to touch

- `ram/wram.asm`
- `ram/hram.asm`

### Verification

```bash
make pokegold.gbc
make compare    # SHA1 may shift slightly if WRAM layout changes affect
                # any code that uses absolute WRAM addresses — most code
                # uses labels, so usually no shift.
python3 tools/audit/check_save_format_version.py    # MUST PASS
python3 tools/audit/check_release_smoke.py
```

Plus playtest: load an existing save, save again, confirm no corruption.
This is the highest-risk part. **Test on a copy of a real save**, not a
fresh game.

### Risk

**MEDIUM.** Save-format breakage is the worst-case. Mitigate by being
strict about the SRAM-region check. The 24-byte `wUnusedMapBuffer` is
the largest single recovery and is safely outside SRAM.

### Estimated effort

1 session (verify each field, delete, build, audit, playtest one save).

### Updated 2026-05-02 by claude-adoring-curie-e2563e

The original verification floor ("playtest one save") underplays
save-format risk. See `META_AUDIT.md` TD-A03 and
`TECH_DEBT_REPORT_ADDENDUM.md` TD-009 risk reframe. Per `CLAUDE.md`:
"Save-format changes shipping to public release are an escalation
item." The corrections below split the work and tighten verification.

#### Why the original recipe is risky

Removing `ds N` from a WRAM field shifts every subsequent field's
offset by N bytes. Even if the deleted field is not SRAM-mirrored,
**any downstream SRAM-mirrored field gets misaligned** — silent
corruption of existing saves with no migration code in the project.

The original recipe's "check ram/sram.asm — most fields are outside
the SRAM region, so deletion is safe" is true only for the deleted
field itself. It does not address downstream shift.

#### Corrected scope: split into TD-009a (safe) and TD-009b (gated)

**TD-009a — HRAM-only deletions, safe:**
- `hUnusedByte` (`ram/hram.asm:31`)
- `hUnusedBackup` (`ram/hram.asm:157`)

HRAM is not save-mirrored. These two are safe to delete with the
original verification floor (build + audit + smoke playtest). 2 bytes
recovered. Quick win.

**TD-009b — WRAM deletions, escalation-gated:**

All `wUnused*` fields in `ram/wram.asm`. For each, before deletion:

1. Locate the field's line in `ram/wram.asm`.
2. Check whether **any subsequent line** is SRAM-mirrored. The
   SRAM-mirrored regions are defined by `ram/sram.asm` mirror
   structures (`MEMORY_BACKUP_*` and similar) — read that file end
   to end before judging.
3. If **any** SRAM-mirrored field appears below the deletion target:
   **escalate to user**. Do not delete. The 24-byte `wUnusedMapBuffer`
   at line 272-273 is upstream of significant WRAM content and almost
   certainly upstream of SRAM mirrors — assume it needs escalation.
4. If no SRAM-mirrored field appears below: deletion is layout-safe,
   but proceed only after running the audit suite and confirming a
   layout-equivalence check (see verification below).

#### Corrected verification (replaces original "playtest one save")

```bash
# Layout-equivalence: WRAM addresses of SRAM-mirrored fields must
# not change. If sram.asm uses absolute address pinning (ds at fixed
# org), this is automatic; otherwise compute via .map file.
make pokegold.gbc
make compare    # SHA1 may shift if any code uses absolute WRAM
                # addresses; that's a red flag, not "expected"
python3 tools/audit/check_save_format_version.py    # MUST PASS
python3 tools/audit/check_release_smoke.py
python3 tools/audit/check_workspace_hygiene.py

# Diff before/after .map files for SRAM-mirrored field addresses:
diff <(grep -E 'wOptions|wPlayer|wPokedexCaught|wPokedexSeen' \
        pokegold.before.map) \
     <(grep -E 'wOptions|wPlayer|wPokedexCaught|wPokedexSeen' \
        pokegold.after.map)
# Empty diff required.
```

Plus playtest on a copy of a real save: load existing, play 5 minutes,
save, reload, confirm party/items/badges/options unchanged.

#### Done criteria

- TD-009a (HRAM) can be marked `done` with the corrected verification.
- TD-009b (WRAM) requires user-escalation per field. Most likely
  marked `accepted` for the larger fields (24-byte `wUnusedMapBuffer`)
  unless a future save-format-version bump (see TD-002) absorbs the
  layout change.

Drop TD-009 from rank #3. New ordering suggestion: TD-009a stays at
rank #3 (quick win, 2 bytes); TD-009b moves to release-gated alongside
TD-002 (next save-format bump opportunity).

---

## TD-010 — Clean `.gitignore`

**Severity:** MEDIUM. **Order:** 1 (quick win).

> **STATUS: blocked → recipe corrected.** See "Updated 2026-05-02"
> subsection below. The original recipe is unsafe; do not execute it.
> Cross-references: `AGENT_LOG.md` 2026-05-03 01:55 UTC blocked entry,
> `TECH_DEBT_REPORT_ADDENDUM.md` TD-010 supersession, `META_AUDIT.md`
> TD-A01.

### Approach

Edit `.gitignore`:
1. Remove non-existent path entries: `rgbds-1.0.1/` (line 23),
   `rgbds-win64.zip`, `rgbds-win64*.zip`, `rgbds-*/` (lines 24-26),
   `.local/` (line 42), `.claude_handoffs/` (line 44),
   `.rebalance_chain/` (line 45). **Verify each is gone via `ls`
   before removing.**
2. Remove duplicate lines 54-56 (already covered by 51-53).
3. Decide on `dist/*.gb` (line 47):
   - If we plan to ever produce ROM binaries in `dist/`, keep it.
   - If `dist/` will only ever hold patches + checksums, remove.
   Likely keep — defensive is fine.

### Files to touch

- `.gitignore`

### Verification

```bash
git status   # confirm nothing previously-ignored is now tracked
```

For each entry removed, verify the path doesn't exist:
```bash
ls -la rgbds-1.0.1/ .local/ .claude_handoffs/ .rebalance_chain/
```

### Risk

**LOW.** If a removed path comes back, the file gets tracked — fixable
on next commit. No silent failure.

### Estimated effort

10 minutes.

### Updated 2026-05-02 by claude-adoring-curie-e2563e

The original recipe is **wrong and unsafe**. The "non-existent paths"
listed in step 1 all exist as real ignored content in the **main repo**;
the original audit was conducted from a worktree (which carries no
untracked content). Executing step 1 as written would push ~1.2 MB of
vendored RGBDS binaries into untracked status — the toolchain
`CLAUDE.md`'s build command depends on. The duplicate-pattern analysis
in step 2 is also inverted. Full evidence: `AGENT_LOG.md` blocked entry
2026-05-03 01:55 UTC; `TECH_DEBT_REPORT_ADDENDUM.md` TD-010
supersession.

#### Corrected recipe (use this, not the original)

Edit `.gitignore`:

1. **Delete line 54** (`*.sav`) — true duplicate of line 34 in the
   emulator block.
2. **Delete line 55** (`*.rtc`) — true duplicate of line 35 in the
   emulator block.
3. **Move line 56** (`*.state`) into the emulator block (between
   current lines 32 and 38) so global state-file coverage stays intact.
   Don't just delete it — it has no global duplicate.
4. **Optionally** delete lines 50-52 (`dist/*.sav`, `dist/*.rtc`,
   `dist/*.state`) since the globals cover them. Defensive is fine —
   recommend leaving the dist scope.

**Do not** delete entries for `rgbds-1.0.1/`, `rgbds-win64.zip`,
`rgbds-win64*.zip`, `rgbds-*/`, `.local/`, `.claude_handoffs/`, or
`.rebalance_chain/`. Those are correct and back real ignored content.

#### Corrected verification

From the **main repo root** (not a worktree):

```bash
git status --ignored 2>&1 | grep -E "rgbds-1\.0\.1|rgbds-win64|\.local|\.claude_handoffs|\.rebalance_chain"
# All five paths must still appear under "Ignored files" — confirms
# the dangerous step 1 of the original recipe was NOT executed.

git status
# After the corrected steps 1-3: no previously-ignored files now
# tracked, no previously-tracked files now ignored.

git diff .gitignore
# Should show 2 deletions (lines 54-55) and 1 move (line 56 → emulator
# block). No other changes.
```

#### Corrected risk

**LOW**, same as original. The corrected scope is small and the
verification above catches the failure mode (accidentally executing
the original step 1).

#### Corrected estimated effort

5 minutes (smaller scope than original 10 minutes).

#### Done criteria

After executing the corrected recipe:
1. Update `STATUS.md` TD-010 row from `blocked` to `done`.
2. Append `done:` entry to `AGENT_LOG.md` with the corrected scope's
   diff.
3. Append a new dated entry in `TECH_DEBT_REPORT_ADDENDUM.md` linking
   the close-out.

**Alternative path:** if the corrected scope feels too small to bother
with, mark TD-010 `accepted` (intentional debt — the entries are
correct as-is, "cruft" was the wrong frame). User approval needed for
`accepted`.

---

## TD-011 — Delete unused script

**Severity:** LOW. **Order:** 2 (quick win).

> **STATUS: disputed.** The script `scripts/export_changes_by_category.py`
> is **not** unused — it generates `docs/CHANGES_BY_CATEGORY.txt` per
> `docs/manifest.md` line 6. See `TECH_DEBT_REPORT_ADDENDUM.md` 2026-05-02
> entry. Do **not** execute the original recipe.

### Approach

1. Final confirmation no references:
   ```bash
   grep -rn 'export_changes_by_category' --include='*' .
   ```
2. If clean: `git rm scripts/export_changes_by_category.py`.
3. If you find it WAS referenced somewhere (rare): log a `disputed:`
   entry and don't delete.

### Files to touch

- `scripts/export_changes_by_category.py` (deleted)

### Verification

```bash
git status
make pokegold.gbc    # build still works (it shouldn't have depended
                     # on this script)
python3 tools/audit/check_workspace_hygiene.py
```

### Risk

**LOW.** Trivially reversible via `git revert`.

### Estimated effort

5 minutes.

---

## TD-012 — Makefile shell hacks

**Severity:** LOW. **Order:** 9.

### Approach

Three options per hack:

#### `cp -f` for back sprite duplication (lines 248-249)

The simplest fix is a Python helper:
```python
# tools/copy_file.py
import sys, shutil
shutil.copyfile(sys.argv[1], sys.argv[2])
```
Then in Makefile: `python tools/copy_file.py $^ $@`. Cross-platform,
explicit. Saves nothing functionally; gains clarity.

Alternative: leave as-is. The `cp -f` works fine on WSL/Linux/Mac
which is the build environment.

#### `cat $^ > $@` binary concat (lines 279-281)

Same pattern — Python helper or leave as-is. Lower priority since the
`cat` form is explicit about what it's doing.

#### `tr < $< -d '\000'` (lines 353-354)

Strips null bytes from SGB tilemap binary. A Python tool would be
clearer:
```python
# tools/strip_nulls.py
import sys
with open(sys.argv[1], 'rb') as f: data = f.read()
with open(sys.argv[2], 'wb') as f: f.write(data.replace(b'\x00', b''))
```

### Files to touch

- `Makefile`
- New: `tools/copy_file.py`, `tools/strip_nulls.py` (if going Python)

### Verification

```bash
make clean && make pokegold.gbc
make compare    # SHA1 must match — these are build-pipeline tools, not
                # source — no behavior change expected
```

### Risk

**LOW.** Any deviation in the new tools shows up immediately as a
build/SHA1 failure.

### Estimated effort

1 session.

### Note

This is genuinely low priority. The hacks work, the build is stable.
Only do this if there's nothing higher-value queued.

---

## TD-013 — `experience.asm` cleanup

**Severity:** LOW. **Order:** 5 (small file, contained).

### Approach

`CalcExpAtLevel` (lines 82-160) has 10+ push/pop pairs managing cubic +
quadratic intermediate terms. Two refactor options:

#### Option A: minimal — extract a `DoSquare` helper

Lines 172-180 already define `.LevelSquared` which squares a value via
`Multiply`. Generalize this to a public `DoSquare` (input: `d`; output:
`hProduct`). Use it in the cubic-term computation to reduce one stack
round-trip.

#### Option B: deeper — restructure to avoid stack arithmetic

Use `hMultiplicand`/`hDividend`/`hProduct` HRAM as intermediate
storage instead of the stack. This is closer to how the rest of the
math engine works. Larger change; more risk; more clarity.

Recommendation: do Option A only. Option B is cleanup-for-cleanup-sake
and risks regression in a working formula.

### Files to touch

- `engine/pokemon/experience.asm`
- Possibly `home/math.asm` or wherever `DoSquare` would live (HOME
  is preferred for math helpers)

### Verification

```bash
make pokegold.gbc
make compare    # SHA1 may shift if instruction count changes — that's
                # expected, but verify EXP curves haven't changed by
                # spot-checking a few level-up XP values.
python3 tools/audit/check_battle_math_safety.py
python3 tools/audit/check_release_smoke.py
```

Plus: in-emulator spot check — start a fresh game, confirm the level-up
EXP requirement at L5, L10, L20 matches expected (Medium-Slow growth
formula values).

### Risk

**MEDIUM.** EXP formula is balance-critical — any rounding shift is a
gameplay change. Do not mark `done:` until both audit AND the in-emulator
spot check pass. Escalate to user if anything looks off.

### Estimated effort

1 session.

### Updated 2026-05-02 by claude-adoring-curie-e2563e

The original verification floor — "SHA1 may shift, spot-check L5, L10,
L20" — is too weak for a balance-critical formula. See `META_AUDIT.md`
TD-A04 and `TECH_DEBT_REPORT_ADDENDUM.md` TD-013 severity revision.

#### Severity revision

`TECH_DEBT_REPORT.md` classifies TD-013 as LOW (low maintenance
burden). Under a two-axis read (burden × correctness risk), TD-013 is
low-burden + high-risk = effective MEDIUM. Treat the verification
floor as MEDIUM even though the immutable report says LOW.

#### Corrected verification floor: SHA1 match required

A "cleanup" of `CalcExpAtLevel` that changes ROM bytes has, by
definition, changed the EXP formula. Spot-checks at L5/L10/L20 will
miss:
- Discontinuities in the cubic term at high levels (L60+)
- Rounding boundaries (e.g. L37, L88) that shift due to operation
  reordering
- Edge cases at level transitions

The only deterministic check is **SHA1 match** between the original
ROM and the refactored ROM. If `make compare` fails, the cleanup
changed behavior. Stop and surface.

This means: Option A (extract `DoSquare` helper) is only viable if
the helper can be inlined or expanded such that the resulting bytes
match the original. Often this isn't possible. If it isn't, **don't
do the refactor** — leave the stack-arithmetic code as-is. Cleanup
is not worth the risk to a balance-critical formula.

Option B (restructure to use HRAM intermediates) almost certainly
shifts ROM bytes and should not be attempted under this corrected
floor.

#### Done criteria

After Option A attempt:
1. `make compare` SHA1 match — REQUIRED.
2. If SHA1 doesn't match: revert the changes, mark TD-013 `accepted`
   with note "deferred — cannot refactor without ROM diff; not worth
   risk to EXP formula." User approval needed for `accepted`.
3. If SHA1 matches: full audit suite passes; mark `done`.

Drop the in-emulator spot-check requirement — SHA1 match makes it
redundant. Save it for cases where SHA1 can't be the floor (e.g.
TD-005, TD-007 which deliberately change ROM bytes).

---

## Cross-cutting verification reminders

For **every** finding marked `done:`:

1. Build: `make pokegold.gbc` succeeds.
2. SHA1: `make compare` matches OR you've justified the SHA1 update in
   the log.
3. Dev index regenerated: `python scripts/generate_dev_index.py --rom
   pokegold`.
4. Relevant audits in `tools/audit/` pass.
5. Reading the diff: re-read the files you edited. "I edited it" is not
   verification.

If any of these fail, the finding is not done — log as `blocked:` or
`partial:` and surface to the human.

---

## When this file is updated

Future agents may refine these proposals as they learn. The format:

```markdown
### TD-XXX — original heading

**Original proposal (2026-05-02):**
... existing content ...

**Updated 2026-MM-DD by <session-id>:**
What changed in the proposal, why, and what evidence prompted the change.
Link to the AGENT_LOG.md entry.
```

Don't overwrite the original recipe — keep history.
