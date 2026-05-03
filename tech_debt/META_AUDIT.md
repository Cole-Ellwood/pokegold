# Meta-audit of `tech_debt/`

**Compiled:** 2026-05-02
**Author:** Opus 4.7 (1M context) / claude-adoring-curie-e2563e
**Scope:** Audit of the `tech_debt/` workstream folder itself — every file,
every finding, every proposal, every workflow rule. Does the design hold
up? Are the findings correct? Is the recipe ship-quality?

This file is **mutable** and lives outside the immutability rule that
binds `TECH_DEBT_REPORT.md` and `FINDINGS_DETAIL.md`. It can be edited,
appended, or superseded by a future meta-audit.

---

## Verdict

**Not perfect to ship — good bones, six concrete defects to fix first.**

The design is mature: an immutable ground-truth report + mutable proposals
+ append-only agent log is the right shape for cross-session work, and
the TD-010 case study (caught wrong proposal, stopped, documented in
`AGENT_LOG.md`) proves the system works under stress.

But the folder has issues that will compound across future sessions:
1. **TD-010 is wrong and the readers can't tell.** Immutability rule
   means the bad finding stays in `TECH_DEBT_REPORT.md` forever; new
   agents will pick it as a "quick win" and re-do TD-010's blocked work.
2. **No status board.** Open vs. blocked vs. done is buried in
   `AGENT_LOG.md` chronological history, not surfaced anywhere a fresh
   agent will see in step 1.
3. **TD-009 underplays save-format risk.** The proposal calls for "test
   one save"; per `CLAUDE.md`, save-format changes are an escalation
   item.
4. **TD-013 mis-ranks.** EXP curve is balance-critical; "LOW" + "spot
   check a few values" is the wrong floor.
5. **TD-005 byte-recovery numbers are sloppy.** Instructions ≠ bytes;
   the multiply/divide thunk math is optimistic.
6. **Snapshot data baked into immutable doc.** The TD-001 bank table
   captures one moment of `dev_index.md` and pretends it's stable
   forever.

Fix these six and the folder is ship-ready.

---

## Audit method

What I did:
- Read all six files in full (`README.md`, `PROJECT_CONTEXT.md`,
  `TECH_DEBT_REPORT.md`, `FINDINGS_DETAIL.md`, `FIX_PROPOSALS.md`,
  `AGENT_LOG.md`).
- Spot-checked the report's quantitative claims against current source:
  - `boss.asm` line count (claimed 7,006 → confirmed 7,006).
  - `experience.asm` line count (claimed 298 → confirmed 298).
  - `late_gen_held_items.asm` `callfar GetUserItem`/`GetOpponentItem`
    instances (claimed 12 → confirmed 12).
  - `; unreferenced` comment count project-wide (claimed ~419 →
    confirmed 424 across 159 files; "approximate" disclaimer was
    honest).
- Verified TD-010's `.gitignore` claim from the **main repo**, not a
  worktree: `rgbds-1.0.1/`, `rgbds-win64.zip`, `.local/`,
  `.claude_handoffs/`, `.rebalance_chain/` all exist and are correctly
  ignored. The blocked agent was right.

What I did **not** do:
- Did not re-read `TECH_DEBT_REPORT.md` against `docs/generated/dev_index.md`
  to confirm the bank-pressure table is still current as of today
  (2026-05-02 same date — should be).
- Did not validate every file:line citation in `FINDINGS_DETAIL.md`
  individually. Spot-checked only.
- Did not exercise the build/audit floor end-to-end.

---

## Strengths (what to keep)

These are real wins and shouldn't be lost in a refactor.

1. **Immutability rule for the report.** Without it, agents would
   silently rewrite findings to "fix" them, destroying the audit trail
   that lets a later session check past work. The rule worked even
   under pressure — the TD-010 agent did not edit the report despite
   knowing it was wrong.
2. **Five-state lifecycle (`claimed`/`done`/`partial`/`blocked`/
   `accepted`/`disputed`/`pending-trigger`).** Granular enough to
   reflect reality; not so granular it's ceremony. `pending-trigger`
   for TD-002 is a particularly nice fit.
3. **Per-finding verification commands.** The "Verification commands by
   finding" table at the end of `FINDINGS_DETAIL.md` is high-value — a
   future agent can re-check any claim with one shell line.
4. **"What is NOT tech debt" section.** Recording a clean signal is
   underrated; without it, a future audit pass will re-investigate the
   same areas.
5. **Authority and escalation explicitly listed in `README.md`.**
   Mirrors `CLAUDE.md` correctly. Reduces "should I ask?" friction.
6. **Recipe shape (Approach / Files / Verification / Risk / Effort /
   Bytes).** Concrete enough to act on, structured enough to
   compare across findings. The risk calls (LOW/MEDIUM/HIGH) match
   reality in 11/13 cases (TD-009 and TD-013 are the misses — see
   below).
7. **README's "do not chain into the next finding" rule.** Mature.
   Prevents the well-known scope-creep failure mode where one fix
   triggers six more "while I'm here" edits.
8. **The TD-010 blocked entry itself.** That's a model AGENT_LOG entry:
   numbered findings, evidence commands, distinguishes "what's actually
   actionable in the spirit of the finding" from "what the recipe
   literally said." If every blocked entry looked like that, this folder
   could run autonomously for months.

---

## Defects (what to fix before shipping)

Numbered TD-A01..TD-A12. "TD-A" = tech-debt-of-tech-debt, to avoid
collision with the report's TD-### IDs. Severity uses the same scale as
`TECH_DEBT_REPORT.md`.

### TD-A01 — TD-010 is wrong and there's no in-band correction path — CRITICAL

[`AGENT_LOG.md`](AGENT_LOG.md) entry "2026-05-03 01:55 UTC — TD-010 — blocked"
documents that `TECH_DEBT_REPORT.md` TD-010 and `FINDINGS_DETAIL.md`
TD-010 contain three errors:

- The "non-existent paths" list is wrong: `rgbds-1.0.1/`,
  `rgbds-win64.zip`, `.local/`, `.claude_handoffs/`, `.rebalance_chain/`
  all exist in the main repo (verified).
- The duplicate-pattern analysis is inverted: lines 50-52 are
  dist-scoped subsets of the global patterns at lines 54-56, not the
  other way around.
- The recipe step "Remove non-existent path entries" would push
  ~1.2 MB of vendored RGBDS binaries into untracked status if executed.

The immutability rule means none of this can be corrected inline. A
fresh agent reading the report sees TD-010 ranked #1 ("trivial, no risk,
demonstrates workflow") and will pick it. They have to read the **entire**
`AGENT_LOG.md` to find the blocked entry — and only step 4 of the
workflow says "confirm no other agent has claimed or completed this
finding." A blocked entry isn't claimed and isn't done; the workflow
literally doesn't tell them to look for it.

This is the highest-priority defect. It causes wasted work on every
fresh session.

**Fix:**
- Create `tech_debt/TECH_DEBT_REPORT_ADDENDUM.md` (the README already
  reserves this file name) with a TD-010 correction:
  - Mark the original finding "superseded by TD-010-corrected".
  - State the actual safely-actionable scope from the blocked entry's
    issue #4 (delete lines 54-55 `*.sav`/`*.rtc` as true duplicates of
    lines 34-35; reposition `*.state` into the emulator block).
- Update [`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) TD-010 with an
  "Updated 2026-05-03" subsection that scopes the recipe to the
  corrected lines only and removes the dangerous "remove rgbds-1.0.1/,
  .local/, .claude_handoffs/, .rebalance_chain/" steps.
- Add a `STATUS.md` board (see TD-A02) so this kind of correction is
  visible in the read order.

### TD-A02 — No open-finding tracker; readers can't see "what's open" — CRITICAL

The workflow is: read `TECH_DEBT_REPORT.md` (immutable), read
`FIX_PROPOSALS.md` (ranked), then `AGENT_LOG.md` (chronological). The
state of any given finding is computed by the reader from the log
history.

This was fine when the log was empty. With one entry, it's already
non-trivial: the reader has to grep for `TD-010` and read every entry
to determine whether it's claimed-by-someone-else, blocked, or done.
With 13 findings × multiple entries each, the cognitive load grows
fast.

**Fix:** Add `tech_debt/STATUS.md`. One row per TD-###, columns: ID,
severity, current state, terminal log entry timestamp, blockers if
any. Append-only by convention — the log remains the audit trail; this
file is the projection. Update happens at the same moment the agent
appends a `done`/`blocked`/`accepted` entry.

Initial state today:

| ID | Sev | State | Last entry | Notes |
|----|-----|-------|------------|-------|
| TD-001 | CRIT | open | — | strategic; depends on TD-005, TD-007 |
| TD-002 | CRIT | pending-trigger | — | waits on SAVE_FORMAT_VERSION bump |
| TD-003 | CRIT | open | — | release-gated |
| TD-004 | HIGH | open | — | do after TD-005 |
| TD-005 | HIGH | open | — | byte-recovery lever |
| TD-006 | HIGH | open | — | escalation on values |
| TD-007 | MED | open | — | selective only |
| TD-008 | MED | open | — | needs version research |
| TD-009 | MED | open | — | save-format risk (see TD-A03) |
| TD-010 | MED | **blocked** | 2026-05-03 01:55 | finding wrong; see addendum |
| TD-011 | LOW | open | — | quick win |
| TD-012 | LOW | open | — | optional |
| TD-013 | LOW | open | — | EXP curve risk (see TD-A04) |

Add a step 0 to the README workflow: "Read `STATUS.md` first."

### TD-A03 — TD-009 underplays save-format risk — HIGH

Per [`CLAUDE.md`](../CLAUDE.md) and [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md):
"Save-format changes shipping to public release are an escalation item."

[`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) TD-009 says:
> Most of these unused fields are outside the SRAM-backed region (check
> ram/sram.asm), so deletion is safe — but verify each field is not
> within an SRAM structure before removing.
>
> Plus playtest: load an existing save, save again, confirm no
> corruption. ... Test on a copy of a real save, not a fresh game.

This understates two risks:
1. **WRAM ordering** is referenced by absolute address in some places
   (the `ds N` placeholders in `ram/wram.asm` chain offsets). Removing
   a field shifts every subsequent field. Even if the deleted field is
   not SRAM-backed, a downstream SRAM-backed field's offset shifts —
   silent save corruption.
2. **No migration code** (`PROJECT_CONTEXT.md` confirms this). Even
   "safe" deletions need the `SAVE_FORMAT_VERSION` bump treatment if
   they touch anything within or upstream of an SRAM mirror.

The proposal's "playtest one save" is not the verification floor for
this class of change. The floor should be: layout audit + SRAM
structure-equivalence check + escalation to the user if any field is
upstream of SRAM data.

**Fix:** Edit `FIX_PROPOSALS.md` TD-009 (preserve original per the file's
own rules, add an "Updated 2026-05-03" subsection) to:
- Require running `tools/audit/check_save_format_version.py` AND a new
  layout-equivalence check (or existing one if it covers this).
- Require escalation to the user before deletion of any WRAM field
  upstream of an SRAM-backed structure (most of the listed fields,
  judging by their lines — the 24-byte `wUnusedMapBuffer` at line
  272-273 specifically needs escalation).
- Move TD-009 from rank #3 to release-gated (after TD-002), or split
  into TD-009a (HRAM-only deletions, safe) and TD-009b (WRAM
  deletions, escalation-gated).

### TD-A04 — TD-013 mis-ranks EXP curve risk as LOW — HIGH

[`TECH_DEBT_REPORT.md`](TECH_DEBT_REPORT.md) classifies TD-013
(`experience.asm` cleanup) as LOW. [`FIX_PROPOSALS.md`](FIX_PROPOSALS.md)
ranks it #5 with verification:

> SHA1 may shift if instruction count changes — that's expected, but
> verify EXP curves haven't changed by spot-checking a few level-up
> XP values.

Two problems:
1. **EXP curve is balance-critical** — the proposal acknowledges this
   in the "Risk" line ("any rounding shift is a gameplay change") but
   the severity is still LOW.
2. **"SHA1 may shift" is not a verification floor.** SHA1 mismatch is
   the only deterministic way to catch a math regression in cleanup
   work. "Spot-check L5, L10, L20" misses L67-L100 ranges and any
   discontinuity in the cubic term.

**Fix:** Edit `FIX_PROPOSALS.md` TD-013 to require **SHA1 match** as
the floor. If SHA1 doesn't match, the cleanup changed behavior — stop
and surface. Bump severity to MEDIUM. The Option A (extract `DoSquare`
helper) recommendation is still right; the verification just has to be
stricter.

This is also evidence the severity scale conflates "code maintenance
burden" with "correctness risk." A scale like "{maintenance burden} ×
{risk if wrong}" with both dimensions visible would prevent this class
of mis-rank. Out of scope for an immediate fix.

### TD-A05 — TD-005 byte-recovery numbers are sloppy — HIGH

[`TECH_DEBT_REPORT.md`](TECH_DEBT_REPORT.md) and
[`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) cite "500-700 bytes recoverable"
as the headline byte-recovery number. The arithmetic doesn't survive
inspection:

- **Pattern 1 (item check):** "8 instructions × 12 = ~96 bytes." On
  GBZ80, instructions are 1-3 bytes; `callfar` expands to multiple
  ops. The 8-instruction pattern is closer to 13-15 bytes per site,
  and the macro replacement still emits the underlying expansion —
  it shrinks **source**, not ROM. Macro savings come only from any
  inlined boilerplate that the macro inlines once vs N times. As
  written, 12 macro call sites still emit the same 13-15 bytes each.
  **Real recovery: ~0 bytes** unless the macro becomes a `call` to
  a shared subroutine.
- **Pattern 2 (multiply/divide thunk):** "~30 bytes per use × 18 =
  ~540 bytes." Possible if the thunk replaces 30 bytes with one call
  (3 bytes for `call`). But the proposal's macro shape still loads
  operands per-site — that loading IS the boilerplate. Realistic
  recovery: ~10-20 bytes per site if the thunk handles operand
  loading via fixed HRAM addresses, so ~180-360 bytes.
- **Pattern 3 (`hBattleTurn` side-branch):** "100+ instances" with no
  enumeration. Unverifiable. Even at 100 sites × 5 bytes each = 500
  bytes, this counts only if a `call get_sided_addr` shared subroutine
  replaces the inline pattern; a macro alone changes nothing in ROM
  size.

Realistic total: **150-400 bytes** if all three are converted to
shared subroutines (not macros). Maybe more, maybe less. The headline
"500-700" is a stretch.

**Fix:** Edit `FIX_PROPOSALS.md` TD-005 to:
- Distinguish "macro" (source clarity, no ROM savings) from
  "subroutine extraction" (ROM savings, slight per-call overhead).
- Restate the recovery range as "approximately 150-400 bytes if
  patterns 2 and 3 are converted to shared subroutines, with byte
  count to be measured at first conversion." Drop the headline
  number until measured.
- Require the first site converted to be measured (build before/after,
  diff `pokegold.map` for the affected bank) before bulk replacement.

### TD-A06 — TD-005 pattern 3 lacks enumeration — MEDIUM

`FINDINGS_DETAIL.md` TD-005 cites "100+ instances project-wide" of the
`hBattleTurn` side-branch pattern with three concrete examples
(`type_passive_damage_mods.asm:48-52, 505-509, 600-605`). A future
agent has no way to find the other 97. They'd have to re-do the grep
pass.

**Fix:** Either run the grep once and append the full list to
`FINDINGS_DETAIL.md` (it's append-only when adding new content per the
addendum rule, but the rule is fuzzy on enumeration completion of an
existing finding), or add the enumeration to a new
`tech_debt/EVIDENCE/td_005_pattern3_sites.md`. The second is cleaner —
the report stays immutable and the grep output is reproducible
evidence.

### TD-A07 — TD-001 bank table is point-in-time data in an immutable doc — MEDIUM

[`TECH_DEBT_REPORT.md`](TECH_DEBT_REPORT.md) TD-001 includes a 12-row
table of bank free-byte counts. This is read from
`docs/generated/dev_index.md` at audit time (2026-05-02). The
underlying file is regenerated on every successful build. Six months
from now, the cited free-byte counts will be wrong, but the
immutability rule says they can't be updated.

The verification command (`python scripts/generate_dev_index.py`) is
correct, but a fresh agent reading "ROMX 0e: 6 free bytes" in an
immutable doc may treat that as ground truth.

**Fix:** Either:
- Add a header note to TD-001 (via the addendum mechanism) clarifying
  "snapshot — re-verify with `dev_index.md`."
- Define a class of "snapshot data" in the README and require those
  to live in `FINDINGS_DETAIL.md` rather than `TECH_DEBT_REPORT.md`,
  with a stable narrative claim ("multiple banks have 0-6 bytes free")
  in the report and the table only in the detail.

Lower priority than TD-A01–A05 because the verification path is
documented; just easy for a fresh reader to miss.

### TD-A08 — TD-008 RGBDS upgrade target version not researched — MEDIUM

[`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) TD-008 says "As of 2026, RGBDS
v1.7+ likely." That's a guess. The latest stable RGBDS as of this
audit isn't specified anywhere in the folder, and the proposal doesn't
include a "research the changelog" step before "test build with target
RGBDS in a worktree."

This is fine if the agent picking up TD-008 does the research. It's
not fine if they copy the version from the proposal.

**Fix:** Add a step 0 to the TD-008 recipe: "Run `curl -s
https://api.github.com/repos/gbdev/rgbds/releases/latest | jq .tag_name`
to identify current stable version. Read the v1.0.1 → current changelog
on https://rgbds.gbdev.io/ before estimating effort."

### TD-A09 — TD-006 paralysis-constant naming is a taste decision — MEDIUM

[`FIX_PROPOSALS.md`](FIX_PROPOSALS.md) TD-006a names constants like
`BASELINE_PARALYSIS_FAIL_PCT` and `ELECTRIC_PARALYSIS_FAIL_PCT_FULL`.
Naming carries semantics. The user is the gameplay-design lead and
owns the "what does this constant mean" call.

The proposal does say "Verify with the user that the **values** are
the design intent" — but the names also encode intent. Are these
"electric" or "paralysis-resistance"? Are the values "failure rates"
or "success rates"?

**Fix:** Edit TD-006a to require user input on both values **and**
names before introducing the constants. Frame the ask as a taste call.

### TD-A10 — `PROJECT_CONTEXT.md` duplicates `CLAUDE.md` content — MEDIUM

Sections "Critical gotchas" (farcall hl-clobber, farcall doesn't
preserve a, Label vs Label::, plain call, ROM bank size, asserts, stat
math, save format, bank switching) are near-verbatim from
`CLAUDE.md`. The duplication is intentional ("portable summary"), but:

- `CLAUDE.md` is auto-loaded; agents don't usually need the duplicate.
- As `CLAUDE.md` evolves (it does; recent commit `b56f9954` was a
  refresh), this file will lag and the two will disagree.
- There's no detection mechanism for the drift.

**Fix:** Either:
- Replace the duplicated sections with one-line summaries plus
  `CLAUDE.md` section anchors. (Loses portability for agents running
  outside Claude Code, but those are rare.)
- Add `tools/audit/check_tech_debt_context_freshness.py` that diffs
  the duplicated sections against `CLAUDE.md` and flags drift.

The first is simpler. The portability use case (agent in a non-Claude-
Code environment reading `tech_debt/`) is hypothetical.

### TD-A11 — Verification commands inconsistent (`python` vs `python3`) — MEDIUM

`PROJECT_CONTEXT.md` says the build command needs `PYTHON=python3` (no
`python` symlink in WSL Ubuntu). The audit and dev-index commands
elsewhere in the same file and in `FIX_PROPOSALS.md` use `python` not
`python3`:

```bash
python scripts/generate_dev_index.py --rom pokegold
python tools/audit/check_release_smoke.py
```

A fresh WSL agent will hit "command not found" on the first audit
command they try.

**Fix:** Change every standalone `python ...` invocation in
`PROJECT_CONTEXT.md` and `FIX_PROPOSALS.md` to `python3 ...`. Or add
a one-liner in `PROJECT_CONTEXT.md`: "If `python: command not found`,
use `python3` — WSL Ubuntu has no `python` symlink."

### TD-A12 — Workflow doesn't address `blocked` items — MEDIUM

`README.md` workflow step 4: "If 'claimed' but stale (>24h with no
progress), you may take it." The `blocked` state isn't addressed.

After TD-010 was blocked, what does a fresh agent do? Pick a different
finding, or attempt TD-010 with a refined approach? If the latter, do
they need user approval first? `README.md` doesn't say.

**Fix:** Add to README workflow:
- "If a finding is `blocked`, do **not** re-attempt it without first
  reading the blocked entry and either (a) the user has explicitly
  un-blocked it, or (b) the proposal in `FIX_PROPOSALS.md` has been
  updated with an "Updated YYYY-MM-DD" section addressing the block."

---

## Per-file review

### `README.md` — 95 lines

**Strengths.** Workflow steps are concrete and numbered. "Authority"
and "What you can / cannot do" sections mirror `CLAUDE.md` correctly.
File map table is clear.

**Issues.**
- Step 1 says "Read `PROJECT_CONTEXT.md` if you don't already have
  project context loaded." Better as "If running outside Claude Code
  or otherwise without `CLAUDE.md` auto-loaded."
- Workflow doesn't mention `STATUS.md` (which doesn't yet exist —
  TD-A02). Add as step 0.
- Workflow doesn't address `blocked` items (TD-A12).
- "10 commandments rule" is catchy but the section title doesn't
  signal "this is the most important rule in the file." Consider
  promoting to top.

### `PROJECT_CONTEXT.md` — 200 lines

**Strengths.** Subsystem table is clear. Build command is correct.
Critical-gotchas section is the right list of land mines.

**Issues.**
- Duplicates `CLAUDE.md` (TD-A10).
- `python` vs `python3` inconsistency (TD-A11).
- "Stat math" section duplicates `CLAUDE.md` but omits the boss-AI
  Speed cap table that's in `CLAUDE.md`. Good or bad depending on
  scope.

### `TECH_DEBT_REPORT.md` — 200 lines

**Strengths.** Severity scale is clear. Per-finding format is
consistent. The "What is NOT tech debt" section is a unique and
valuable feature. Index table at the end is the right summary.

**Issues.**
- TD-010 is wrong (TD-A01).
- TD-001 includes snapshot data (TD-A07).
- TD-009 severity is right (MEDIUM) but the proposal's risk handling
  is wrong (TD-A03).
- TD-013 severity is wrong (LOW → should be MEDIUM, TD-A04).
- TD-005 byte estimates are wishful (TD-A05).
- "419 unreferenced labels" (TD-007) is approximate. Spot-check
  returned 424. Acceptable per the explicit disclaimer, but consider
  rounding to "~420" or using a verifiable boundary like "more than
  400."

### `FINDINGS_DETAIL.md` — 280 lines

**Strengths.** File:line citations enable independent verification.
"Verification commands by finding" table is excellent. Per-finding
evidence depth is appropriate.

**Issues.**
- TD-010 evidence is wrong (caught and documented; TD-A01).
- TD-005 pattern 3 lacks enumeration (TD-A06).
- WRAMX bank 1 reserve table cites specific line numbers
  (`ram/wram.asm:2534-2591`) — these will drift if anyone touches
  `ram/wram.asm`. Fine for an immutable doc as long as readers know
  it's a snapshot.

### `FIX_PROPOSALS.md` — 580 lines

**Strengths.** Recipe shape is consistent. Verification commands are
specific. Risk calls are mostly accurate. Recommended-order table at
top is a nice index.

**Issues.**
- TD-005 numbers are sloppy (TD-A05).
- TD-009 verification floor is wrong (TD-A03).
- TD-013 verification floor is wrong (TD-A04).
- TD-008 target version not researched (TD-A08).
- TD-006 naming is a taste decision (TD-A09).
- TD-007 mentions HOME (ROM0) targets without checking ROM0 fullness
  first. Add a precondition: "Confirm ROM0 has free space for any
  deletion that shifts HOME content; HOME is a fixed bank and tight."
- TD-010 needs the "Updated 2026-05-03" correction (TD-A01).

### `AGENT_LOG.md` — 100 lines (incl. example + one real entry)

**Strengths.** Template is comprehensive. State definitions are clear.
The TD-010 blocked entry is a model of what good logging looks like.

**Issues.**
- Template has 12 fields per entry. For a quick-win finding (TD-010,
  TD-011), filling all 12 is friction. Consider a "minimal" variant
  for findings that touch one file with no audit fallout: ID / state
  / branch+commit / files / one-sentence summary / one verification
  line. Reserve the full 12-field template for HIGH+ findings.
- Real entries in the log won't render the example block consistently
  unless someone deletes the example as instructed. Easy to forget.
  Consider moving the example to README.md and removing from
  AGENT_LOG.md.

---

## Defects in workflow / process (not in any single file)

- **The folder lives only on branch `claude/unruffled-khayyam-35aa2d`.**
  Not on `master`, not on `codex/cleanup-gsc-rebalance-split`, not on
  origin. The README's premise — "a fresh agent session can pick up the
  work" — assumes the folder is reachable from any starting branch.
  Today it isn't; an agent in a fresh worktree won't see it. **Fix:**
  Merge or cherry-pick the three tech_debt commits onto
  `codex/cleanup-gsc-rebalance-split` (the de facto trunk based on
  recent commit history). User approval needed for the merge per
  `CLAUDE.md` escalation list.
- **No freshness audit script.** The report's file:line citations and
  bank-pressure table will drift. A
  `tools/audit/check_tech_debt_freshness.py` could grep each cited
  file:line for the expected label/text and flag drift. Low effort,
  high value once the folder is in regular use.
- **No `tech_debt/` reference in `MEMORY.md` from before this session.**
  Now fixed (a memory was added in this session pointing to the branch),
  but the only way that worked was a person noticing it didn't show up
  in the worktree. The folder needs to live on a discoverable branch
  (see above).

---

## Concrete fix list (in order)

If you want this folder shippable, here's the minimal punch list. Each
item is small enough to be one session.

1. **Merge tech_debt/ to a stable branch.** Cherry-pick `723057e4` +
   `02889a87` + `a5004b9b` onto `codex/cleanup-gsc-rebalance-split`
   (or `master`), so a fresh worktree from any branch sees the folder.
   Escalation: needs your approval.
2. **Write `tech_debt/STATUS.md`.** One row per finding, current state,
   last log entry. Mechanical; no risk. (TD-A02.)
3. **Write `tech_debt/TECH_DEBT_REPORT_ADDENDUM.md`** with TD-010
   correction. Keeps the immutability rule intact while neutralizing
   the wrong finding. (TD-A01.)
4. **Update `FIX_PROPOSALS.md` TD-010** with "Updated 2026-05-03"
   subsection scoping the recipe to the actual safely-actionable
   changes. (TD-A01.)
5. **Update `FIX_PROPOSALS.md` TD-009 and TD-013** with stricter
   verification floors. (TD-A03, TD-A04.)
6. **Update `FIX_PROPOSALS.md` TD-005** to drop the headline
   500-700 byte claim, distinguish macros from subroutine extraction,
   and require measurement at first conversion. (TD-A05.)
7. **Add `tools/audit/check_tech_debt_freshness.py`** — grep cited
   file:lines, flag drift. Bonus: include a check that the addendum
   exists if any TD-### has a `disputed:` or `blocked:` log entry.
8. **Fix `python` → `python3` in `PROJECT_CONTEXT.md` and
   `FIX_PROPOSALS.md`.** (TD-A11.) Mechanical.
9. **Update `README.md` workflow** to add step 0 (read `STATUS.md`)
   and address `blocked` items. (TD-A12.)
10. **Slim `AGENT_LOG.md` template** for low-severity findings, move
    example to README. (Per-file review.)

After items 1-6, the folder is ship-quality. Items 7-10 are polish.

---

## Things I'd change if I owned the design

Out of scope for the immediate fix list. Recorded for the next
meta-audit pass.

- **Replace severity scale with two-axis: maintenance burden ×
  correctness risk.** Today's scale conflates them; that's why TD-013
  (low burden, high risk) lands as LOW.
- **Drop `PROJECT_CONTEXT.md`.** `CLAUDE.md` is the real source of
  truth and is auto-loaded. The portability argument is hypothetical.
  Worst case: shrink `PROJECT_CONTEXT.md` to a one-line "if running
  outside Claude Code, read `../CLAUDE.md`."
- **Add `tech_debt/CHANGELOG.md`.** Tracks meta-changes to the folder
  itself: addendums added, proposals updated, status board mutations.
  Independent of `AGENT_LOG.md` (which tracks finding work).
- **Promote `STATUS.md` to be the one file you have to load.**
  Everything else linked from it. Reduces the "where do I start?"
  cognitive load to zero.

---

## Ship recommendation

**Don't ship as-is.** TD-010 alone causes burned sessions on every
fresh-agent attempt. TD-A02 (no status board) compounds it.

**Ship after fix-list items 1-6.** That's an estimated 1-2 sessions of
work. The folder design is sound; the defects are in specific findings
and missing scaffolding, not in the architecture.

After items 1-6 ship, the folder will hold its value through ~10
agent sessions before drift requires another meta-audit pass. Schedule
the next meta-audit at the natural trigger: when 5+ findings are
closed, or when 3+ have `disputed:` or `blocked:` entries, whichever
comes first.

End of meta-audit.
