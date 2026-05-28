# Boss AI Split Repartition — Codex Task Spec

> The file split shipped at `commit fc43378a` (Merge: boss AI source
> split) — but the partition is incorrect. `BossAI_ApplyMoveModel` and
> all `.ApplyXxxBias` bodies (~1800 lines of POLICY code) live in
> `boss_platform.asm`. `boss_data.asm` bloated to 1810 lines vs the
> ~140 lines the org plan §1.1 specified. The platform/policy seam —
> the entire reason for the split — is currently broken at the
> conceptual level. Build clean, audits pass, ROM byte-identical, but
> the layer separation isn't there.
>
> This task re-partitions the 5 files to match the canonical platform/
> policy table in
> [`docs/boss_ai_organization_plan.md`](boss_ai_organization_plan.md)
> §1.1, with NO behavior change and byte-identical ROM output. Same
> byte-identity discipline as the original split task at
> [`docs/boss_asm_split_codex_task.md`](boss_asm_split_codex_task.md).

## Execution shape

This task runs as 4 ordered steps (A → B → C → D). Codex executes all
four in one pass without stopping between them.

### STEP A — Worktree setup (BEFORE any file edit)

Run these commands first, exactly as written:

```bash
git fetch origin
git worktree add .claude/worktrees/codex-boss-asm-repartition origin/codex/cleanup-gsc-rebalance-split
cd .claude/worktrees/codex-boss-asm-repartition
cp -r ../../../rgbds-1.0.1 .
git rev-parse HEAD
git rev-parse origin/codex/cleanup-gsc-rebalance-split
```

The two `git rev-parse` outputs MUST match. If they do not, the
worktree is on a stale base and Codex must rerun.

THEN, before any file edit, print this **four-check report** so the
user can spot a misplacement before any commit:

```bash
pwd
git branch --show-current
git rev-parse HEAD
ls docs/boss_asm_split_codex_task.md
```

Required state:
- `pwd` ends in `.claude/worktrees/codex-boss-asm-repartition`
- branch is the auto-named codex worktree branch (NOT
  `codex/cleanup-gsc-rebalance-split` directly, NOT any pre-existing
  codex branch)
- `git rev-parse HEAD` matches
  `git rev-parse origin/codex/cleanup-gsc-rebalance-split`
- `docs/boss_asm_split_codex_task.md` lists

ALL subsequent work happens inside this worktree.

### STEP B — Reading

Before doing anything else, read:

- [`docs/codex_playbook.md`](codex_playbook.md) §1, §2, §2.3.
- [`docs/boss_ai_organization_plan.md`](boss_ai_organization_plan.md)
  §1.1 (platform/policy seam — the canonical layer table) and §3
  Option C (the architectural decision).
- [`docs/boss_asm_split_codex_task.md`](boss_asm_split_codex_task.md)
  Step 1 (the file partition table the original split was supposed to
  follow but didn't).
- The 5 current split files at `engine/battle/ai/boss_*.asm` to see
  the actual current distribution.

### STEP C — Execution

Run the 5 sub-steps in [Steps](#steps) below, in order.

### STEP D — Ship

Merge to dev tip via the playbook §2.3 commit-tree pattern. Final
merge commit body has the bug-check Findings report (§1.1 format),
including before/after LOC distribution tables and explicit
byte-identity confirmation.

---

## Background

Current state (verify by `wc -l engine/battle/ai/boss_*.asm` at
worktree HEAD):

| File | Current LOC | Spec target LOC | Delta |
| --- | ---: | ---: | ---: |
| `boss_platform.asm` | ~2317 | ~1850 | **+467 (over)** |
| `boss_policy_move.asm` | ~1376 | ~2300 | **−924 (under)** |
| `boss_policy_switch.asm` | ~1962 | ~2100 | −138 (close) |
| `boss_data.asm` | ~1810 | ~140 | **+1670 (way over)** |
| `boss_thunks.asm` | ~78 | ~60 | +18 (close) |

Confirmed misplacements (verify with `grep -lE
"^BossAI_ApplyMoveModel" engine/battle/ai/boss_*.asm`):

- `BossAI_ApplyMoveModel` is in `boss_platform.asm`. It IS policy code
  (it's the move-scoring overlay that produces numeric scores per
  policy). It should be in `boss_policy_move.asm`.
- All `.ApplyXxxBias` local labels (currently 25 of them after the
  bias deletions in `commit 8089199f` and `commit 0351b8f7`) are
  inside `BossAI_ApplyMoveModel`, so they move with it.
- `boss_data.asm` at 1810 lines vs ~140 spec'd: contains many static
  tables that are tightly coupled to one function and should live with
  that function (e.g., per-leader effect tables go with the role-bias
  function in `boss_policy_move.asm`).

The org plan §1.1 platform/policy split specifies ~26% platform / ~71%
policy / ~3% data. The current LOC distribution gives:
~30% platform / ~18% policy_move / ~26% policy_switch / ~24% data /
~1% thunks. The bloated platform + bloated data + thin policy_move
all reflect the same misclassification.

**Critical constraint:** ROM bytes MUST stay byte-identical (same as
the original split task). `make compare` is the verification. If it
fails, surface the diff and STOP.

---

## Files to investigate

All in `engine/battle/ai/`:

- `boss_platform.asm` — needs ~1800 lines of policy code extracted to
  `boss_policy_move.asm`
- `boss_policy_move.asm` — receives the move-scoring overlay
- `boss_policy_switch.asm` — likely close to correct, verify against
  spec
- `boss_data.asm` — needs many tables relocated to their owner files;
  may end up empty (fold into `boss_policy_move.asm` per the original
  spec's "if empty, fold" guidance)
- `boss_thunks.asm` — likely correct, verify

Other:

- `main.asm` — INCLUDE order may need adjustment if `boss_data.asm`
  gets folded
- `tools/audit/check_boss_ai_no_cheat.py` — `SCAN_FILES` set; may need
  trimming if `boss_platform.asm` becomes the canonical no-cheat file
- `tools/audit/check_boss_ai_*` — verify all still pass
- `scripts/generate_boss_ai_index.py` — already exists (shipped in the
  original split). Re-run to refresh the index doc.
- `docs/agent_navigation/subsystems/boss_ai_logic.md` — auto-regen via
  the generator script
- `docs/boss_ai_organization_plan.md` — update status banner if the
  partition is now actually correct

---

## Steps

### Step 0 — Pre-repartition audit

Run from the worktree root:

```bash
wc -l engine/battle/ai/boss_*.asm
```

Capture the current LOC distribution. Compare to the spec table in
[`docs/boss_asm_split_codex_task.md`](boss_asm_split_codex_task.md)
Step 1. Identify every region (set of contiguous labels with shared
concern) that's in the wrong file per the org plan §1.1 platform/
policy table.

For each label currently in `boss_platform.asm` and `boss_data.asm`,
classify as PLATFORM, POLICY, or DATA per the org plan §1.1 line
ranges (applied to current source). Any DATA table that's tightly
coupled to one function moves with that function (e.g., per-leader
effect tables go with role bias).

Capture the pre-move map: `cp pokegold.map pokegold.map.pre_repartition`
for byte-diff debugging if Step 4 fails.

### Step 1 — Apply correct partition per org plan §1.1

Use the partition table at
[`docs/boss_asm_split_codex_task.md`](boss_asm_split_codex_task.md)
Step 1 verbatim. The expected target distribution:

| File | Contains |
| --- | --- |
| `boss_platform.asm` | State tracking; Public-info plumbing; Per-tick cache reset; Caches (passive — `Test*Bit`, uncached `HasAnyKOMove(Uncached)`); Held-item helpers; Type-matchup (no item) machinery; Move-category callfar wrappers; Seen-species index; Mask machinery (structural — `Test*MaskBit`, `Set*MaskBit`); Score I/O; Scouted bitmap I/O; Static no-cheat tables (`BossAI_PlausibleThreatTypes`, `BossAIHiddenPowerThreatTypes`) |
| `boss_policy_move.asm` | Adaptive lead; Move-scoring overlay (`BossAI_ApplyMoveModel` + ALL `.ApplyXxxBias` locals); Move pick (`BossAI_SelectMove`); Plan selection; Party-by-role; Plan/scout/repeat biases; Setup/status/denial classifiers; Mask construction policy (`Add*MovesToMask`, `ComputePlayerPlausibleTypeMask`); Pressure scoring; Move-category + accuracy risk policy; Public-faster (`BossAI_PublicEnemyFaster`); Threat caches (active); Predict + revealed-SE; Bench threat score; Lookahead orchestration + body + multi-turn projection + signed-delta clamp; Primary threat type; Threat severity; Tier-roll thresholds; Scout decision; Mark scout pivot; Per-leader effect tables (`BossAIChuckRoleEffects` etc); Bias support tables (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`, `BossAITierWeights`) |
| `boss_policy_switch.asm` | Switch dispatch (`BossAI_TrySwitch`); Switch threshold + loop penalty; Switch reason predicates; Switch-in classifiers; Ace timing + switch confidence; Switch-candidate risk refinement; Switch-confidence finalization |
| `boss_data.asm` | Static tables not tightly coupled to one function. **If empty after this repartition, fold into `boss_policy_move.asm` and remove the file from main.asm.** Surface the fold/keep decision in Findings. |
| `boss_thunks.asm` | The `*_HL` thunks at the tail (cross-bank `_HL` farcall wrappers). Stays in bank `0e`. |

Decision points to flag in Findings:
- Whether `boss_data.asm` ended up empty (fold) or still has content
  (keep). If folding, update `main.asm` to remove that INCLUDE.
- Any region with genuinely interleaved platform/policy code that
  resists clean assignment — surface for user judgment, make a
  defensible default in the diff.

### Step 2 — Physical move

For each region in the wrong file: cut from current file, paste
verbatim into target file. Preserve every byte: indentation, comments,
blank lines, label `::` vs `:`. Do NOT change ANY function's behavior.
Comments, file-header banners, blank lines may differ; instructions
and labels must be byte-for-byte preserved.

If `boss_data.asm` is folded, remove its INCLUDE from `main.asm` and
delete the file.

### Step 3 — Regenerate index

Run `python scripts/generate_boss_ai_index.py` (already exists from
the original split). It scans all 5 (or 4 if folded) files and writes
`docs/agent_navigation/subsystems/boss_ai_logic.md`. The audit
`check_boss_ai_index_lines.py` will validate.

Regenerate `docs/generated/dev_index.md` per CLAUDE.md verification
floor.

### Step 4 — Verify byte-identity

This is the load-bearing check.

- `make compare` MUST be byte-identical to dev tip. If it isn't,
  surface the diff and **STOP** — the repartition has reordered
  something that affects ROM bytes. Most likely: a `::` got
  downgraded to `:`, a thunk got moved out of bank `0e`, or a SECTION
  boundary changed.
- `roms.sha1` should be byte-identical to dev tip. Verify with
  `git diff origin/codex/cleanup-gsc-rebalance-split -- roms.sha1`
  (must be empty).
- Bank `0e` totals (free space, used) per `docs/generated/dev_index.md`
  should be unchanged or trivially shifted.

### Step 5 — Full audit floor

- 4-ROM build clean.
- ALL of these PASS: `check_release_smoke`, `check_boss_ai_no_cheat`,
  `check_boss_ai_trace_invariants`, `check_boss_ai_gating`,
  `check_boss_ai_index_lines`, `check_boss_ai_memory_budget`,
  `check_boss_ai_policy_contract`, `check_navigation_floor`.
- `clobber_smoke` 24/24 PASS — register ABI must not have shifted.
- `check_no_stale_shipped_claims.py` if any new doc lines have date
  claims.

---

## Acceptance criteria

- [ ] Final LOC distribution: `boss_platform.asm` ~1850, `boss_policy_move.asm` ~2200, `boss_policy_switch.asm` ~2100, `boss_data.asm` empty/folded or ~140, `boss_thunks.asm` ~60. Distribution matches org plan §1.1 ±10%.
- [ ] `BossAI_ApplyMoveModel` lives in `boss_policy_move.asm` (verify with `grep -l ^BossAI_ApplyMoveModel engine/battle/ai/boss_*.asm`).
- [ ] All `.ApplyXxxBias` locals live with `BossAI_ApplyMoveModel`.
- [ ] `make compare` byte-identical to dev tip (`pokegold.gbc` SHA matches `roms.sha1`).
- [ ] `roms.sha1` unchanged from dev tip (no row diff).
- [ ] All boss-AI audits PASS.
- [ ] `clobber_smoke` 24/24 PASS.
- [ ] `boss_ai_logic.md` regenerated via generator; audit confirms.
- [ ] `docs/generated/dev_index.md` regenerated.
- [ ] `docs/boss_ai_organization_plan.md` status banner updated to reflect Option C SHIPPED + REPARTITIONED if previously claimed shipped.
- [ ] Final merge commit body has §1.1 Findings report covering: before/after LOC distribution table / byte-identity verification / `boss_data.asm` fold-or-keep decision / audit results / scope adherence.

---

## Scope boundaries / Do NOT

- Do NOT change ANY function's behavior. This is a structural fix, not
  a refactor. ROM bytes preserved.
- Do NOT do any of org plan §4's simplification proposals (twin
  function fold, macro extraction, etc — out of scope).
- Do NOT change SECTION assignment for any function. All files stay in
  `Enemy Trainers` SECTION.
- Do NOT move thunks out of bank `0e`.
- Do NOT downgrade any `::` to `:`. Cross-file references in the same
  SECTION work only if `::` is preserved. Build will catch this.
- Do NOT touch `engine/battle/ai/boss_trace_topmoves.asm` (already in
  its own SECTION).
- Do NOT touch `engine/battle/ai/scoring.asm`,
  `engine/battle/ai/items.asm`, `engine/battle/ai/move.asm`,
  `engine/battle/ai/switch.asm`, `engine/battle/ai/redundant.asm`.
- Do NOT modify CLAUDE.md, the codex playbook, or any handoff docs.
- If `make compare` shows ANY byte diff, **STOP** and report.
- If a region resists clean platform/policy assignment, surface in
  Findings rather than guess.
