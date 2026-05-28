# Branch-divergence remediation plan

**Created 2026-05-27.** Synthesis of an 8-agent investigation into why
"previously fixed" boss-AI behavior keeps reappearing in playtests.

## Problem & root cause

The repo is developed by many parallel autonomous Claude/Codex sessions, each
on its own auto-created worktree branch (`.claude/worktrees/<name>`,
`.local/worktrees/<name>`). Those branches drift behind `master`, are often
never merged back, and **nothing makes the staleness visible** — a stale
branch still builds, and every other audit only checks a branch's *internal*
consistency, not its currency vs master. So sessions build and playtest ROMs
hundreds of commits behind master and see already-fixed bugs as phantom
"regressions."

Trigger that surfaced this: `ram-relief-2026-05-26` is 126 commits behind
master and missing the Morty boss-AI fixes (`4969efb1` matchup-aware faint
replacement, `e532da2c` pain-split gates), so playtesting it showed AI bugs
that were already fixed on master.

## Canonical facts (2026-05-27)

- **`master` is canonical.** Local `master` = `4e34e777`. `codex/cleanup-gsc-rebalance-split`
  is fully merged into it (126 behind, 0 ahead); all ~30 other branches are
  100–471 behind. **`origin/master` is 603 commits stale (last fetched Feb)** —
  local `master` is the only truth; compare against it, not origin.
- Stranded unmerged work is **mostly tooling**; real lost *gameplay* work is
  small (see Tier B5).
- The release-smoke floor currently runs **no boss-AI behavioral check** —
  which is why these regressions were invisible.

## Tier A — Prevention (stop the bleeding)

- **A2 — branch-currency guardrail.** `tools/audit/check_branch_currency.py`
  (DONE, tested: warns + lists missing gameplay commits on a stale branch,
  `--strict` exits 1, silent-PASS when current).
  - [ ] Wire it: (1) SessionStart hook in `.claude/settings.json` — emit the
    banner as `hookSpecificOutput.additionalContext` (pattern:
    `scripts/inject_asm_guide.py`), always exit 0. (2) release-smoke floor —
    add a `_run_subaudit` call with `--strict` in `check_release_smoke.py`
    `main()`. (3) Makefile pre-build banner via `$(shell ... --warn)` near the
    `tools_bootstrap` block (~line 147). [Agent 3]
- [ ] **A1 — canonical-branch policy (CLAUDE.md).** Name `master` canonical +
  integration; redefine "release" (roms.sha1 refresh + distribute, NOT "a
  commit reached master"); sync-before-work and before any playtest build
  (rebase for short session branches); merge-back-or-abandon. Fix the
  self-contradictory "Merging to master. Release event" escalation bullet and
  retarget "Recent work" from `codex/cleanup-gsc-rebalance-split` to
  `git log master`. Drop-in text drafted by Agent 4. **GATED on the governance
  decision below.**
- [ ] **A3 — autonomous-loop sync hygiene** (biggest divergence *generator*).
  `tools/pokemon_mastery/loop_runner.py` has zero git awareness and pgoal is
  told "never leave your claude/ branch." Add `sync-preflight` (fetch + rebase
  master + currency check + verify, refuse on non-FF) and `land` (FF-merge to
  one shared integration line) to `loop_runner.py`; wire
  `tools/pokemon_mastery/pgoal_spec/{constraints,verify}.txt` and
  `C:/Users/lolno/Downloads/codex-supervisor/supervisor.ps1`. [Agent 7]

## Tier B — Recover & reconcile (one-time)

- [ ] **B4 — ram-relief → master.** Cherry-pick `06d33eaf` then `cdabdd07`
  onto a branch off master. Clean except `tools/audit/check_boss_ai_memory_budget.py`
  (master moved `fail`/`load` to `_common.py`): keep master's
  `from _common import fail, load`, drop ram-relief's inline defs, keep the
  fingerprint functions. `ram/wram.asm` auto-merges (master added `wBossAI*Cache`
  ~2464; ram-relief deletes `wUnusedMapBuffer`/`wSafariMonAngerCount` — keep
  both). Post: rebuild (fires the save.asm asserts against master's layout),
  regen dev_index, regen the offset-map fingerprint baseline via the audit's
  `--update`, re-run audits. [Agent 6]
- [ ] **B5 — recover real lost work.** `upbeat-williamson-ed7924` (Kanto/E4/rival
  balance — MANUAL reconcile vs master's competing rebalance; gameplay-taste,
  user call). `reverent-kepler-1952df` (ROM-bug audit doc incl. a Sev-3
  save-loader finding — cheap cherry-pick, worth reading). 8-step poison
  cadence hunk (optional, user taste). Abandon the rest. **Do NOT bulk-merge**
  any stranded branch — wholesale merge would *revert* master's newer boss AI.
  [Agent 1]
- [ ] **B6 — prune.** 16 merged branches + 4 redundant worktrees. KEEP
  `codex/cleanup-gsc-rebalance-split`, `wip/*`, and all 19 unmerged branches.
  Per-branch safe checklist: `git rev-list --count master..B` == 0 AND
  `git cherry master B` all `-`, not in the exempt set, then `git worktree
  remove` then `git branch -d` (lowercase). [Agent 2]

## Tier C — Durable net

- [ ] **C7 — behavioral regression net.** Tier-1 (free, source-shape): add
  `check_boss_ai_trace_invariants.py` + `check_boss_ai_preference_regression.py`
  to the release-smoke floor. Tier-2 (trace-gated): new
  `check_boss_ai_behavior_regression.py` over JSONL scenarios via
  `tools/boss_ai_debugger/rom_switch_materialize.py` /
  `rom_score_materialize.py` — scenarios: painsplit-full-HP, faint-replace-avoid-4x,
  Morty-concrete, painsplit-low-HP control, dominance-matchup-aware. [Agent 8]
- [ ] **C8 — build provenance.** `tools/gen_build_info.py` → `pokegold.gbc.build-info`
  sidecar (branch, SHA+dirty, commits-behind-master, BEHIND-ON-GAMEPLAY flag,
  timestamp, rgbds version, ROM sha1) + end-of-build banner; wire after the
  `%.gbc` recipe (~line 197), add `*.build-info` to `.gitignore`. Zero ROM
  bytes → `make compare` safe. No in-ROM stamp on the four sha1-pinned targets.
  [Agent 5]

## Open decision (gates A1 + every master landing)

**Governance:** CLAUDE.md lists "Merging to master" as an escalation/release
event, yet master is demonstrably the active integration branch (full of merge
commits; fixes land directly on it). Decision needed: **make merging finished
work to master ordinary delegated execution, reserving escalation for actual
public releases?** Until decided, all work stays on agent branches and
master-landing waits for explicit user OK.

## Where work lands

Everything targets **local `master`**. Build the systemic fixes (Tier A, C) on
`claude/divergence-fix`; do the ram-relief reconciliation on its own
cherry-pick branch. Nothing merges to master without the governance decision +
explicit OK.
