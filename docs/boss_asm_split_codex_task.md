# Boss AI File Split — Codex Task Spec

> Split `engine/battle/ai/boss.asm` (currently ~7508 lines after MercyRefusal
> removal at `commit 8089199f`) into the 5 files specified in
> [`docs/boss_ai_organization_plan.md`](boss_ai_organization_plan.md) §3
> Option C. All 5 files stay in the same `Enemy Trainers` SECTION (bank `0e`).
> Bank layout, intra-bank `call` reachability, ROM bytes — unchanged.
> `make compare` MUST be byte-identical. This is purely a structural change.

## Execution shape

This task runs as 4 ordered steps (A → B → C → D). Codex executes all four
in one pass without stopping between them.

### STEP A — Worktree setup (BEFORE any file edit)

Run these commands first, exactly as written:

```bash
git fetch origin
git worktree add .claude/worktrees/codex-boss-asm-split origin/codex/cleanup-gsc-rebalance-split
cd .claude/worktrees/codex-boss-asm-split
cp -r ../../../rgbds-1.0.1 .
git rev-parse HEAD
git rev-parse origin/codex/cleanup-gsc-rebalance-split
```

The two `git rev-parse` outputs MUST match. If they do not, the worktree is
on a stale base and Codex must rerun.

THEN, before any file edit, print this **four-check report** so the user can
spot a misplacement before any commit:

```bash
pwd
git branch --show-current
git rev-parse HEAD
ls docs/boss_ai_organization_plan.md
```

Required state before edits begin:
- `pwd` ends in `.claude/worktrees/codex-boss-asm-split`
- branch is the auto-named codex worktree branch (NOT
  `codex/cleanup-gsc-rebalance-split` directly, NOT any pre-existing codex
  branch)
- `git rev-parse HEAD` matches `git rev-parse origin/codex/cleanup-gsc-rebalance-split`
- `docs/boss_ai_organization_plan.md` lists

ALL subsequent work happens inside this worktree.

### STEP B — Reading

Before doing anything else, read these files end-to-end:

- [`docs/codex_playbook.md`](codex_playbook.md) §1 (bug-check methodology),
  §2 (workflow rituals), §2.3 (commit-tree merge to dev tip pattern).
- [`docs/boss_ai_organization_plan.md`](boss_ai_organization_plan.md) §1.1
  (platform/policy seam), §3 Option C, §4 (simplification — IGNORE for this
  task, no behavior changes here), §5–§7 (skip — out of scope).
- [`docs/agent_navigation/subsystems/boss_ai_logic.md`](agent_navigation/subsystems/boss_ai_logic.md)
  end-to-end.

### STEP C — Execution

Run the 7 sub-steps in [Steps](#steps) below in order. Do not stop between
them.

### STEP D — Ship

Merge to dev tip via the playbook §2.3 commit-tree pattern. The final merge
commit body must contain the bug-check Findings report (§1.1 format)
covering every category in [Acceptance Criteria](#acceptance-criteria).

---

## Background

[`docs/boss_ai_organization_plan.md`](boss_ai_organization_plan.md) §3
specifies three options. Option A (banner comments per region) shipped.
**Option B (section reorder within one file) is being skipped** in favor of
Option C: the file split itself naturally separates platform/policy code,
making Option B redundant.

The `Enemy Trainers` SECTION lives at `main.asm:168-172`. Currently it
includes 3 files: `engine/battle/ai/items.asm`,
`engine/battle/ai/boss.asm`, `engine/battle/read_trainer_attributes.asm`.
After this task it includes 7 files (5 new + 2 unchanged neighbors).

Per the org plan §1.1, the line-count split is approximately:
- ~26% platform (state tracking, no-cheat plumbing, caches, type-matchup,
  cross-bank thunks)
- ~71% policy (scoring, decisions, lookahead, switch refinement)
- ~3% data (static tables)

**Critical constraint:** every function stays reachable from every caller
without a single byte of ROM moving. If `make compare` shows ANY byte diff,
the split has corrupted something — most likely a `::` was downgraded to
`:` (cross-file refs fail to link) or a thunk got placed outside its
required SECTION.

---

## Files to investigate

- `engine/battle/ai/boss.asm` — the file being split.
- `main.asm` — INCLUDE list to update (currently one
  `INCLUDE "engine/battle/ai/boss.asm"`, becomes 5 lines or 4 if
  `boss_data.asm` is folded).
- `tools/audit/check_boss_ai_no_cheat.py` — `SCAN_FILES` constant; needs to
  expand to all new files.
- `tools/audit/check_boss_ai_index_lines.py` — currently scans
  `engine/battle/ai/boss.asm`; needs to scan all new files. Per the org
  plan §2.3, this is the right moment to land
  `scripts/generate_boss_ai_index.py` so the index doc is auto-emitted from
  source.
- `tools/audit/check_boss_ai_trace_invariants.py` — uses
  `boss = read("engine/battle/ai/boss.asm")` with `top_block(boss, ...)` /
  `local_block(...)` helpers. Needs to read each new file and resolve
  labels regardless of which file they live in. Cleanest pattern: read all
  new files and concatenate (preserving order) into one logical buffer for
  the helpers, OR read per-file with a label-resolver.
- `tools/audit/check_boss_ai_gating.py`,
  `tools/audit/check_boss_ai_memory_budget.py`,
  `tools/audit/check_boss_ai_live_capture_ledger.py`,
  `tools/audit/check_boss_ai_policy_contract.py` — each may reference
  `boss.asm`. Audit-update each as needed.
- `docs/agent_navigation/subsystems/boss_ai_logic.md` — line citations
  move from `boss.asm:N` to `<new_file>.asm:N`. ~175 citations. The audit
  `check_boss_ai_index_lines.py` enforces these. Build the generator
  script (in scope per org plan §2.3) so future edits don't require manual
  refresh.
- `docs/boss_ai_organization_plan.md` — update status banner: Option C
  shipped. Preserve the planning history but mark §3 RESOLVED.
- `docs/boss_ai_post_patch_notes.md`, `docs/boss_ai_spec.md` — line
  citations to `boss.asm` need updating.

---

## Steps

### Step 0 — Pre-split audit (do FIRST)

1. Confirm Option A (banner comments) is in current source — grep for
   `; Region:` headers in `engine/battle/ai/boss.asm`.
2. Verify pre-split build SHA matches `roms.sha1` for all 4 ROMs.
3. Capture the pre-split linker map for byte-diff debugging if Step 6
   fails: `cp pokegold.map pokegold.map.pre_split`.
4. List every label in `boss.asm` (top-level `::` and local `.foo`) with
   its line. This list is the spec for per-file label assignment in
   Step 1.

### Step 1 — File partition assignment

Map every region to its target file. Use the org plan §1.1
platform/policy table applied to current source line ranges (NOT the §3
Option B reordered ranges — Option B did not ship).

| Target file | Regions to extract |
| --- | --- |
| `boss_platform.asm` | State tracking; Public-info plumbing; Per-tick cache reset; Caches (passive — `Test*Bit`, uncached `HasAnyKOMove(Uncached)`); Held-item helpers; Type-matchup (no item) machinery; Move-category callfar wrappers; Seen-species index; Mask machinery (structural parts only — `Test*MaskBit`, `Set*MaskBit`); Score I/O (`LoadScorePointer`, `SetScoreHL`, `Encourage/DiscourageScoreHL`); Scouted bitmap I/O; Static no-cheat tables (`BossAI_PlausibleThreatTypes`, `BossAIHiddenPowerThreatTypes`). |
| `boss_policy_move.asm` | Adaptive lead (`MaybePickAdaptiveEnemyLead`); Move-scoring overlay (`BossAI_ApplyMoveModel` and ALL its `.ApplyXxxBias` locals); Move pick (`BossAI_SelectMove` and helpers); Plan selection (`BossAI_SelectPlanIfNeeded`); Party-by-role; Plan/scout/repeat biases; Setup/status/denial classifiers; Mask construction policy (`Add*MovesToMask`, `ComputePlayerPlausibleTypeMask` — the policy parts of the mask machinery, NOT the structural test/set helpers); Pressure scoring; Move-category + accuracy risk policy; Public-faster (`BossAI_PublicEnemyFaster`); Threat caches (active); Predict + revealed-SE; Bench threat score; Lookahead orchestration + body + multi-turn projection + signed-delta clamp; Primary threat type; Threat severity; Tier-roll thresholds; Scout decision; Mark scout pivot; Per-leader effect tables (`BossAIChuckRoleEffects` etc); Bias support tables (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`, `BossAITierWeights`). |
| `boss_policy_switch.asm` | Switch dispatch (`BossAI_SwitchOrTryItem` + base candidate scan); Switch threshold + loop penalty; Switch reason predicates; Switch-in classifiers; Ace timing + switch confidence; Switch-candidate risk refinement; Switch-confidence finalization. |
| `boss_data.asm` | Static data tables that aren't co-located with the function that owns them. **Most data tables are tightly coupled to one function** (per-leader effect tables go with the role-bias function), so this file may end up empty. **If empty, fold it into `boss_policy_move.asm` and skip the file** — surface this decision in Findings. |
| `boss_thunks.asm` | The 7 `*_HL` thunks at the tail of current `boss.asm` (cross-bank `_HL` farcall wrappers to `AI Scoring` bank). MUST stay in bank `0e`. Keep the explanatory block comment about why thunks exist. |

Decision points to flag in Findings:
- Whether `boss_data.asm` ended up needed (default: fold if empty).
- Whether any region had genuinely interleaved platform/policy code that
  resists clean assignment — surface for user judgment, but make a
  defensible default in the diff.

### Step 2 — Physical move

Cut each region from `boss.asm` and paste verbatim into the target file.
Preserve every byte: indentation, comments, blank lines, label `::` vs
`:`. For each new file, prepend:

```
; ============================================================
; engine/battle/ai/<filename> — <one-line concern>
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================
```

After all moves, `boss.asm` itself becomes either:
- (a) empty + deleted, OR
- (b) a thin shim if a few module-glue items resist clean extraction.

Prefer (a). If (b) is unavoidable, justify in Findings.

### Step 3 — Update INCLUDE list

`main.asm` line 171 (the `INCLUDE "engine/battle/ai/boss.asm"`) becomes
INCLUDE lines for the new files in this order: `boss_platform.asm`,
`boss_policy_move.asm`, `boss_policy_switch.asm`, `boss_data.asm` (or skip
if folded), `boss_thunks.asm`. **Order matters** for linker placement.
Match the org plan §3 Option C order.

### Step 4 — Update boss-AI audits

- `check_boss_ai_no_cheat.py`: expand `SCAN_FILES`.
- `check_boss_ai_index_lines.py`: per-file scanning. **Build
  `scripts/generate_boss_ai_index.py`** at this point — reads all new
  files, emits the existing `boss_ai_logic.md` micro-index format with
  line numbers extracted from current source. The audit becomes a
  build-time check that the generator's output matches what's committed.
  Per org plan §2.3, this is essentially mandatory once the file is
  split.
- `check_boss_ai_trace_invariants.py`: read all new files, concatenate
  into one logical buffer with line-tracking, pass to existing
  `top_block` / `local_block` helpers. Each helper finds its label
  regardless of which file it lives in.
- `check_boss_ai_gating.py`, `check_boss_ai_memory_budget.py`,
  `check_boss_ai_live_capture_ledger.py`,
  `check_boss_ai_policy_contract.py`: each gets the same multi-file scan
  treatment if needed; many may not need updating at all.

### Step 5 — Regenerate index + docs

- Run `scripts/generate_boss_ai_index.py` → write
  `docs/agent_navigation/subsystems/boss_ai_logic.md` (replaces
  hand-maintained line numbers).
- Update `docs/boss_ai_organization_plan.md` status banner: Option C
  shipped. Preserve Options A/B/C narrative as historical for §3 archive.
- Update line citations in `docs/boss_ai_post_patch_notes.md`,
  `docs/boss_ai_spec.md` to point at the new files (search-and-replace on
  `boss.asm:N` patterns; verify each).
- Regenerate `docs/generated/dev_index.md`.

### Step 6 — Verify byte-identity (load-bearing)

This is the single most load-bearing check.

- `make compare` MUST be byte-identical to the pre-split state. If it
  isn't, surface the diff and **STOP** — the split has reordered
  something that affects ROM bytes. Most likely cause: a thunk got moved
  outside bank `0e`, or a SECTION boundary changed, or `::` got
  downgraded to `:`. Do not commit a non-byte-identical split unless
  Codex can defensibly explain the diff.
- `roms.sha1` should be byte-identical to dev tip (no changes needed,
  since ROM bytes didn't move). Verify.
- Bank `0e` totals (free space, used) per
  `docs/generated/dev_index.md` should be unchanged or trivially shifted.

### Step 7 — Full audit floor

- 4-ROM build clean.
- ALL of these PASS: `check_release_smoke`, `check_boss_ai_no_cheat`,
  `check_boss_ai_trace_invariants`, `check_boss_ai_gating`,
  `check_boss_ai_index_lines`, `check_boss_ai_memory_budget`,
  `check_boss_ai_policy_contract`, `check_navigation_floor`.
- `clobber_smoke` 24/24 PASS — register ABI must not have shifted (purely
  a file move; if it did, something moved the wrong direction).
- `check_no_stale_shipped_claims.py` if any new doc lines have date
  claims.
- `roms.sha1` byte-identical to dev tip.

---

## Acceptance criteria

- [ ] 5 new files exist (or 4 if `boss_data.asm` was folded), each
      ≤ ~2500 lines.
- [ ] `boss.asm` either deleted or reduced to a tiny shim with explicit
      rationale in Findings.
- [ ] `main.asm` INCLUDE list updated.
- [ ] `make compare` byte-identical (`pokegold.gbc` SHA matches dev
      tip's SHA in `roms.sha1`).
- [ ] `roms.sha1` unchanged from dev tip.
- [ ] All boss-AI audits PASS.
- [ ] `clobber_smoke` 24/24 PASS.
- [ ] `scripts/generate_boss_ai_index.py` exists, generates the index
      doc, and the audit `check_boss_ai_index_lines.py` runs the
      generator at audit time (or compares committed output).
- [ ] `docs/agent_navigation/subsystems/boss_ai_logic.md` line citations
      updated to point at the new files.
- [ ] `docs/boss_ai_organization_plan.md` status banner updated.
- [ ] Final merge commit body has the §1.1 Findings report covering:
      byte-identity verification / file LOC distribution / audit updates
      list / index generator scope / live-capture impact (should be zero
      — purely structural).

---

## Scope boundaries / Do NOT

- Do NOT change ANY function's behavior. Not one byte of code logic.
  Comments, whitespace, banner formatting may differ; instructions and
  labels must be byte-for-byte preserved.
- Do NOT do any of org plan §4's simplification proposals. Those are
  deferred to a separate task. (Twin function fold, macro extraction,
  etc — out of scope.)
- Do NOT change SECTION assignment for any function. All new files stay
  in `Enemy Trainers` SECTION.
- Do NOT move thunks out of bank `0e` — they MUST be in the same bank as
  their callers.
- Do NOT downgrade any `::` to `:`. Cross-file references in the same
  SECTION still work, but only if `::` is preserved. Verify by build —
  RGBLINK will catch this.
- Do NOT touch `engine/battle/ai/boss_trace_topmoves.asm` (already in
  its own SECTION).
- Do NOT touch `engine/battle/ai/scoring.asm`,
  `engine/battle/ai/items.asm`, `engine/battle/ai/move.asm`,
  `engine/battle/ai/switch.asm`, `engine/battle/ai/redundant.asm` —
  separate concerns.
- Do NOT modify CLAUDE.md, the codex playbook, or any handoff docs.
- If `make compare` shows ANY byte diff, **STOP** and report — do not
  commit a non-byte-identical split. The whole point is structural;
  behavior stays.
- If a region resists clean platform/policy assignment, surface it in
  Findings rather than guess. The user can decide.
