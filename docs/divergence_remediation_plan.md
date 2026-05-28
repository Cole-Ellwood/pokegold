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

## Preservation log (2026-05-27)

Spot-checking remembered work (the shiny-Gyarados→Magikarp conversion) found it
was never committed — it had accumulated as uncommitted changes across worktrees
and was at risk. All at-risk uncommitted work is now snapshotted into git
(faithful as-is; rewrite + marker pre-commit guards bypassed for preservation
only; master's committed tip `4e34e777` untouched):

- `wip/master-worktree-snapshot-2026-05-27` @ `d74c3f24` — 92 files, +8,843/−3,216:
  the Gyarados→Magikarp pass (maps/dialogue/NPCs/items/sprites/wild) plus boss-AI,
  debugger, headless-battle, lookahead-research, and RAM-relief work. Excludes the
  regenerable `docs/boss_ai_architecture.pdf`.
- `claude/upbeat-williamson-ed7924` @ `768ba16a` — 12 files: boss-AI preference
  fixtures/labels/reports, `boss_policy_move.asm`, trace-invariants audit.
- `claude/upbeat-khorana-77400d` @ `533987d7` — 5 files: `tools/debugger` work.

These are preservation snapshots, not finished work — triage and land deliberately.

## Tier A — Prevention (stop the bleeding)

- **A2 — branch-currency guardrail.** `tools/audit/check_branch_currency.py`
  (DONE, tested: warns + lists missing gameplay commits on a stale branch,
  `--strict` exits 1, silent-PASS when current).
  - [x] Wired (commits `bcee4f16` + `85800645`): (1) SessionStart hook in
    `.claude/settings.json` via `--hook` (JSON envelope, only when stale).
    (2) release-smoke floor — `check_branch_currency()` `_run_subaudit` call
    with `--strict`. (3) Makefile pre-build banner via `$(shell ... --warn)`
    after `tools_bootstrap`. `--warn`/`--hook` emit modes added to the script.
    Note: under WSL, a Windows-created linked worktree's `.git` points to a
    Windows path Linux git cannot resolve, so the Makefile banner degrades to
    a silent no-op there; the SessionStart + release-smoke layers run natively
    and are unaffected. [Agent 3]
- [x] **A1 — canonical-branch policy (CLAUDE.md)** (DONE; governance resolved
  below). Added a "Branches & releases" subsection naming `master` the
  canonical integration branch, redefining "release" as distributing to players
  (roms.sha1 refresh = delegated prep), and stating sync-before-work/playtest
  (rebase short session branches) + merge-back-or-abandon. Made merging
  finished/green work to master delegated in Authority, replaced the
  self-contradictory "Merging to master = release event" escalation bullet with
  "shipping a public release to players," and retargeted "Recent work" to
  `git log master`.
- [x] **A3 — autonomous-loop sync hygiene** (DONE `92d7f655`; biggest divergence
  *generator*). New `tools/pokemon_mastery/sync.py` adds two ops surfaced as
  `loop_runner.py` subcommands: `sync-preflight` (clean check → best-effort
  fetch → rebase onto canonical master → integrity gate; refuses cleanly on a
  dirty tree, a conflicting rebase, or a red gate) and `land` (FF-only advance
  of the shared integration line, default **master**, via `update-ref` CAS;
  worktree-safe — refuses rather than desync a branch checked out elsewhere or
  rewrite history). The land/preflight gate is the per-iteration SAFETY subset
  (pytest + `verify_loop_state` + `verify_regression_battery` +
  `check_branch_currency --strict`), deliberately NOT the full `verify.txt`,
  whose aspirational progress/breadth gates stay red until the loop finishes.
  Wired: `constraints.txt` (replaced "NEVER commit to master" with
  preflight-before / land-after-green), `verify.txt` (added the currency check
  as a pure criterion), `pgoal_spec/README.md`, and the out-of-repo
  `codex-supervisor/supervisor.ps1` (journals commits-behind-master, toasts on
  the rising edge of staleness, downgrades a DONE verdict on a stale branch).
  14 new hermetic tests; full pokemon_mastery suite green. [Agent 7]
- [x] **A4 — uncommitted-work tripwire** (DONE `85800645`; the gap this
  incident exposed). Branch-currency (A2) checks commits-*behind*, not *dirty*
  worktrees — yet the near-loss on 2026-05-27 was ~2,900 lines sitting
  uncommitted in the master worktree, plus two other dirty worktrees.
  `tools/audit/check_uncommitted_work.py` measures tracked+untracked changes
  (significant = >=25 lines or >=4 files); `--hook` warns at SessionStart,
  `--strict` exits 1 for autonomous loops, `--snapshot` (wired to SessionEnd)
  preserves the worktree to `refs/wip-snapshots/<branch>-<ts>` without touching
  the working tree, index, or branch HEAD. Still pairs with A3 (loops should
  also `land` each iteration).

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

## Governance decision — RESOLVED 2026-05-28

**Question (was):** CLAUDE.md listed "Merging to master" as an escalation/release
event, yet master is demonstrably the active integration branch (full of merge
commits; fixes land directly on it).

**Decision (user, 2026-05-28):** merging finished, audit-passing work to master
is **ordinary delegated execution**. The escalation is **shipping a public
release to players** (roms.sha1 refresh + distribution), not a commit reaching
master. Save-format changes shipping to players remain a user-approval item.
Encoded in CLAUDE.md (A1). Master landings (B4, B5) no longer wait for a blanket
OK — though per-item gameplay-taste calls in B5 still do.

## Where work lands

Everything targets **local `master`**. Build the systemic fixes (Tier A, C) on
`claude/divergence-fix`; do the ram-relief reconciliation on its own
cherry-pick branch. Nothing merges to master without the governance decision +
explicit OK.
