# Tech Debt Report — Addendum

**Created:** 2026-05-02
**Purpose:** Corrections, supersessions, and additions to
`TECH_DEBT_REPORT.md`. The report itself is **immutable** per project
rule; this file exists to handle the cases where a finding turns out to
be wrong or new findings are identified after the original audit pass.

**Format:** append-only. Each entry has its own dated section. When a
finding is corrected by a later entry, link forward in the heading.

**Reading order:** read this file **before** acting on any TD-###
finding. If a finding has an entry here, the entry's guidance
supersedes the original report and `FIX_PROPOSALS.md` (unless
`FIX_PROPOSALS.md` itself has a later "Updated YYYY-MM-DD" subsection
acknowledging the addendum).

---

## 2026-05-02 — TD-010 superseded (was: ".gitignore cruft")

**Source:** `AGENT_LOG.md` blocked entry "2026-05-03 01:55 UTC — TD-010
— blocked"; meta-audit `META_AUDIT.md` TD-A01.

**Corrects:** `TECH_DEBT_REPORT.md` TD-010, `FINDINGS_DETAIL.md` TD-010.

### What was wrong with the original finding

The original TD-010 listed six paths in `.gitignore` as "non-existent"
and recommended deletion:
- `rgbds-1.0.1/`
- `rgbds-win64.zip`, `rgbds-win64*.zip`, `rgbds-*/`
- `.local/`
- `.claude_handoffs/`
- `.rebalance_chain/`

All six exist as real ignored content in the **main repo** (verified
2026-05-02). The original audit was conducted from a worktree, which
does not carry untracked content — that's why the paths appeared
absent. The recipe was unsafe as written: executing it would push
~1.2 MB of vendored RGBDS binaries (the toolchain `CLAUDE.md`'s build
command depends on) into untracked status and risk an accidental
commit.

The duplicate-pattern analysis was also inverted. The original claimed
"Lines 54-56 duplicate the `.sav`/`.rtc`/`.state` patterns already on
lines 51-53." Actual layout in `.gitignore`:
- Lines 50-52: `dist/*.sav`, `dist/*.rtc`, `dist/*.state` (dist-scoped)
- Lines 54-56: `*.sav`, `*.rtc`, `*.state` (global)

The dist-scoped lines are subsets of the globals, not the other way
around. The actual true duplicates are line 54 `*.sav` ↔ line 34 `*.sav`
(in the emulator block) and line 55 `*.rtc` ↔ line 35 `*.rtc`. Line 56
`*.state` is unique — removing it would narrow coverage.

### Corrected scope

The only safely-actionable cleanup in the spirit of TD-010:

1. **Delete line 54** (`*.sav`) — true duplicate of line 34.
2. **Delete line 55** (`*.rtc`) — true duplicate of line 35.
3. **Move line 56** (`*.state`) into the emulator block at lines 32-38
   so global state-file coverage stays intact (emulator block is the
   logical home).
4. **Optionally** delete lines 50-52 (`dist/*.sav`, `dist/*.rtc`,
   `dist/*.state`) since the globals cover them — but the original
   "defensive is fine" guidance suggests leaving the dist scope.

**Do not** delete entries for `rgbds-1.0.1/`, `rgbds-win64.zip`,
`rgbds-win64*.zip`, `rgbds-*/`, `.local/`, `.claude_handoffs/`, or
`.rebalance_chain/`. Those are correct as written and back real
ignored content.

The corrected recipe is in [`FIX_PROPOSALS.md`](FIX_PROPOSALS.md)
TD-010 "Updated 2026-05-02" subsection. `STATUS.md` shows TD-010 as
`blocked` until either the corrected recipe is executed or the user
explicitly accepts TD-010 as intentional debt (the entries are correct
as-is; "cruft" was the wrong frame).

### Verification of this correction

Anyone re-checking this addendum should run, **from the main repo
root** (not a worktree):

```bash
git status --ignored 2>&1 | grep -E "rgbds-1\.0\.1|rgbds-win64|\.local|\.claude_handoffs|\.rebalance_chain"
```

All five paths should appear under "Ignored files." If they don't, the
.gitignore has been changed since 2026-05-02 and this addendum needs
re-validation.

---

## 2026-05-02 — TD-013 severity revision (effective MEDIUM, not LOW)

**Source:** meta-audit `META_AUDIT.md` TD-A04.

**Corrects:** `TECH_DEBT_REPORT.md` TD-013 severity column (was LOW).

The `experience.asm` cleanup is technically a small refactor (low
maintenance burden), which is what the LOW classification reflected.
But the EXP curve is balance-critical: any rounding shift in
`CalcExpAtLevel` is a gameplay change.

The severity scale conflates "code maintenance burden" with
"correctness risk." Under a two-axis read, TD-013 is low-burden +
high-risk = effective MEDIUM. Treat it as such for verification floor:
SHA1 match is required, not "spot-check a few values."

The corrected verification floor is in
[`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) TD-013 "Updated 2026-05-02"
subsection.

---

## 2026-05-02 — TD-009 risk reframe (save-format escalation required)

**Source:** meta-audit `META_AUDIT.md` TD-A03.

**Corrects:** `TECH_DEBT_REPORT.md` TD-009 verification posture
(implicitly via FIX_PROPOSALS).

TD-009 lists ~30 bytes of "unused" RAM fields for deletion. The
original proposal's verification floor was "playtest one save." That
underplays the risk:

1. Per `CLAUDE.md` and `PROJECT_CONTEXT.md`: "Save-format changes
   shipping to public release are an escalation item."
2. WRAM ordering matters even for non-SRAM fields: removing `ds N`
   from one field shifts every subsequent field's offset, and any
   downstream SRAM-mirrored field gets misaligned.
3. There is **no migration code** in the project. Existing saves
   silently corrupt if the layout shifts.

The corrected proposal in [`FIX_PROPOSALS.md`](FIX_PROPOSALS.md)
TD-009 "Updated 2026-05-02" subsection requires:
- Distinguishing HRAM-only deletions (safe, low risk) from WRAM
  deletions (escalation-gated for any field upstream of an SRAM
  mirror).
- Running save-format-equivalence audit, not a single playtest.
- User escalation before deleting `wUnusedMapBuffer` (the largest,
  24 bytes) or any other WRAM field upstream of SRAM data.

---

## 2026-05-02 — TD-011 disputed (script is in active use)

**Source:** discovery while preparing to execute TD-011 per the
new STATUS workflow; meta-audit follow-up.

**Disputes:** `TECH_DEBT_REPORT.md` TD-011 ("Likely-unused script
`scripts/export_changes_by_category.py`"); `FINDINGS_DETAIL.md` TD-011.

### Why the finding is wrong

The original audit checked references in:
- `tools/audit/`
- `scripts/`
- `Makefile`
- `.github/workflows/`
- `docs/`

and concluded "no references in docs/." But `docs/manifest.md` line 6
says verbatim:

> `docs/CHANGES_BY_CATEGORY.txt` is generated from this file by
> `scripts/export_changes_by_category.py`.

And `docs/CHANGES_BY_CATEGORY.txt` exists. The script is part of the
changelog generation pipeline. Deleting it would silently break the
next changelog regeneration.

The original audit's `grep -rn 'export_changes_by_category' --include='*.md'`
must have either skipped `docs/manifest.md` or the manifest reference
post-dates the audit. Either way, the finding's recommendation is
unsafe.

### Recommended state

Mark TD-011 `disputed` in STATUS. The script is **not** unused.

If a future work item wants to consolidate the two changelog scripts
(`export_changes_from_manifest.py` and `export_changes_by_category.py`)
into one tool, that's a different finding and belongs in a new
TD-A### entry — not in TD-011.

---

## 2026-05-02 — TD-009a dead-writes scope correction

**Source:** discovery while preparing to execute TD-009a per
`FIX_PROPOSALS.md` TD-009 "Updated 2026-05-02"; meta-audit follow-up.

**Corrects:** `FINDINGS_DETAIL.md` TD-009 line 412-413 ("`hUnusedByte`
... No refs" / "`hUnusedBackup` ... No refs").

### Why the "No refs" claim is wrong

`hUnusedByte` and `hUnusedBackup` both have **writes** in the live
engine code, even though the original audit marked them "No refs":

- `hUnusedByte`: 1 write at `engine/overworld/events.asm:804`
  (`ldh [hUnusedByte], a` — zeros the byte after a menu return).
- `hUnusedBackup`: 3 writes:
  - `home/vblank.asm:148` (saves `hSeconds` to it during vblank)
  - `engine/menus/intro_menu.asm:40` (saves `rLY` during player-ID RNG)
  - `engine/menus/intro_menu.asm:46` (same, second pass)

The `wUnusedMusicF9Flag` finding in TD-009 explicitly noted "writes
only ... write-only flag, also dead" — the same write-only-no-reads
audit lens **wasn't** applied to these two HRAM fields. The "No refs"
marker reflects a read-search only, missing the writes.

### Implication for the deletion recipe

Removing the field declarations alone (`hUnusedByte:: db` at line 31,
`hUnusedBackup:: db` at line 157) would break compilation: the
`ldh [n8], a` writes still resolve symbol names at link time. To
actually recover the 2 HRAM bytes, the writes must also be removed:

| File | Line | Code to remove |
|------|------|----------------|
| `engine/overworld/events.asm` | 804 | `ldh [hUnusedByte], a` |
| `home/vblank.asm` | 147-148 | `ldh a, [hSeconds]` + `ldh [hUnusedBackup], a` (2 lines; the read is dead too) |
| `engine/menus/intro_menu.asm` | 39-40 | `ldh a, [rLY]` + `ldh [hUnusedBackup], a` |
| `engine/menus/intro_menu.asm` | 45-46 | `ldh a, [rLY]` + `ldh [hUnusedBackup], a` |

All four sites are dead writes (and their associated reads target
side-effect-free registers/HRAM). Removal is technically safe but the
work crosses into:

- **vblank.asm** — every-frame hot path, even dead-store removal
  warrants careful review.
- **intro_menu.asm** — startup/RNG init code.
- **events.asm** — menu handling.

### Recommended posture

- HRAM is at **0 bytes free** per TD-001. Recovering 2 bytes is
  genuinely valuable.
- The fix is technically safe but touches three engine files for a
  micro-recovery. Risk/reward is dominated by review cost.
- **Escalate to user** before executing. Frame as: "TD-009a is real
  but bigger than the original recipe — touches vblank.asm. 2 HRAM
  bytes + ~10 ROM bytes recoverable. Do you want it done?"

Until escalated, leave TD-009a `open` with this addendum entry as
the standing context.

---

## 2026-05-03 — TD-001 snapshot refresh after TD-005 P1 + TD-007

**Source:** `AGENT_LOG.md` partial entry "2026-05-03 — TD-005 — partial" and done entry "2026-05-03 — TD-007 — done"; meta-audit `META_AUDIT.md` TD-A07 (snapshot data in immutable doc).

**Refreshes:** `TECH_DEBT_REPORT.md` TD-001 bank table + strategic framing.

### Why a refresh

Per META_AUDIT TD-A07, the TD-001 bank table is point-in-time data in an immutable doc — by design it goes stale, and the addendum mechanism is the only way to update guidance without violating the immutability rule. As of 2026-05-03 the snapshot has drifted enough that the original strategic framing is misleading.

### Snapshot delta

Bank-pressure picture per `docs/generated/dev_index.md` (Generated: 2026-05-03):

| Bank/Region | Original report (2026-05-02) | Current (2026-05-03) | Note |
|---|---:|---:|---|
| HRAM 00 | 0 | 0 | unchanged |
| ROMX 0d (Effect Commands) | 6 | 6 | unchanged — **new canary** |
| ROMX 0e (Enemy Trainers + Late Gen Held Items) | 6\* | 568 | drifted before report time + 41 from TD-005 P1; **dropped out of tight-banks list** |
| ROMX 12 / 15 / 17 / 1b / 1e (pic data) | 0 | 0 | unchanged |
| ROMX 1c (pic data) | 1 | 1 | unchanged |
| ROMX 1f (Unown pic pointers) | 1 | 1 | unchanged |
| ROMX 1a (pic data) | 4 | 4 | unchanged |
| WRAMX 01 (boss AI reserve) | 0 | 0 | unchanged |
| ROMX 16 | (not listed) | 48 | **newly tight** |
| WRAM0 00 | (not listed) | 49 | **newly tight** |
| ROMX 2a (Map Blocks 1) | 85 | 3,585 | +3,500 from TD-007; dropped out |
| ROMX 2b (Map Blocks 2) | 166 | 2,425 | +2,259 from TD-007; dropped out |

\*The original "6 free" for ROMX 0e was already inaccurate at report time per META_AUDIT TD-A07 (the dev_index data the report compiled from predated 2026-05-02). The actual figure pre-TD-005 P1 was 527 free per AGENT_LOG.

### What this changes

1. **Bank 0x0e is no longer the canary.** The original report's framing — "any non-trivial boss AI edit risks link failure" — was wrong at report time and is now substantially wrong. 568 bytes free in 0x0e is comfortable headroom for normal growth.

2. **ROMX 0x0d (Effect Commands) is the new tight battle bank** at 6 free. Any growth in `engine/battle/effect_commands.asm` or `engine/battle/used_move_text.asm` has nowhere to go. Treat 0x0d as the old 0x0e was treated.

3. **TD-004 (boss.asm split) is no longer bank-pressure-gated.** With 568 free in 0x0e, a structural split that adds modest interfile overhead (helper labels, section seams) is feasible without prerequisite section relocation. The split is still warranted on readability/maintenance grounds, but the sequencing dependency on TD-005 closing first is now relaxed.

4. **Section relocation off bank 0x0e is no longer required.** Original Approach #2 in `FIX_PROPOSALS.md` TD-001 (move `late_gen_held_items.asm` / `type_passive_damage_mods.asm` out of 0x0e to ROMX 0x0a or 0x0d) is unnecessary while 0x0e has room. Skip unless 0x0e re-tightens.

5. **Pic banks unchanged** — 0x12 / 0x15 / 0x17 / 0x1b / 0x1c / 0x1e / 0x1f all still at 0-1 free. Original Approach #3 (pre-commit guard via `tools/audit/check_pic_bank_pressure.py`) still applies and is the only remaining concrete fix in TD-001's recipe that hasn't been addressed by other findings.

6. **Two new tight regions** to be aware of:
   - **WRAM0 (49 free)** — global wram is finite. Any new always-resident state has 49 bytes max before pressure.
   - **ROMX 0x16 (48 free)** — battle engine adjacent. Watch for growth.

### Updated relocation candidates (if pressure shifts again)

Original TD-001 recipe pointed to ROMX 0x0a / 0x0d as relocation targets. As of 2026-05-03:
- **ROMX 0x0d at 6 free** — DO NOT relocate into. It is now the canary.
- **ROMX 0x0a not in tight-banks list** — likely roomy, but pic-adjacent; verify before relocating.
- **Best relocation targets** (per dev_index "Largest ROMX Free Ranges"): banks 13, 22, 27, 28, 29, 2c, 2d, 2f, 34, 35, 58, 63, 67, 6f are entirely free (16,384 bytes each). Banks 2c-2f are most natural for code/data adjacency to existing battle-region banks.

### Verification

```bash
python3 scripts/generate_dev_index.py --rom pokegold
# Re-read docs/generated/dev_index.md "Tight Banks And Regions" — banks listed there are the canon.
```

The dev_index is regenerated on every build that changes linker outputs; it is the authoritative current state, not this addendum. This addendum captures the strategic interpretation as of 2026-05-03 — the data underneath will continue to drift.

The corrected approach is in `FIX_PROPOSALS.md` TD-001 "Updated 2026-05-03" subsection. STATUS notes for TD-001 reference this addendum.

---

## How this file is structured

- **Append-only.** Never edit a prior entry. Add a new dated entry if
  guidance changes again.
- **Each entry has a dated heading.** Format:
  `## YYYY-MM-DD — TD-### <action>` where action is `superseded`,
  `severity revision`, `risk reframe`, `clarification`, or
  `new finding` (use TD-A### for additions discovered after the
  original audit; TD-### IDs are reserved for the original report).
- **Forward-link** when later entries supersede earlier ones in this
  file.
- **Always cite source** (an `AGENT_LOG.md` entry or `META_AUDIT.md`
  finding) for traceability.
