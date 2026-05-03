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
