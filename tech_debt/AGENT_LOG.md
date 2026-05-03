# Agent Log — append-only

Every agent that touches a TD-### finding logs here. **Do not edit existing
entries.** Append at the bottom in chronological order.

The log lets future agents (and the human) verify whether a claimed fix
actually addresses what `TECH_DEBT_REPORT.md` and `FINDINGS_DETAIL.md`
identified.

---

## Entry formats

Two templates. Pick by finding severity / fix scope.

### Minimal — for LOW or quick-win MEDIUM findings

Use when: single-file edit, no audit fallout, no bytes/bank impact,
no follow-ups. Most TD-010, TD-011 -class fixes.

```markdown
## YYYY-MM-DD HH:MM — TD-### — <state>

- **Agent / branch:** <model + branch @ short SHA>
- **Files touched:** <list, or "(none yet)" for `claimed`>
- **Summary:** <1-2 sentences>
- **Verification:** `<cmd>` → PASS/FAIL; `<cmd>` → PASS/FAIL
- **Verifier check:** <one line — how to independently re-confirm>
```

### Full — for HIGH+ findings, or any fix with bytes/bank/follow-ups

Use when: byte-recovery work (TD-005), structural refactor (TD-004),
boss AI changes, save-format work (TD-009b), or anything blocked.

```markdown
## YYYY-MM-DD HH:MM — TD-### — <state>

- **Agent / session:** <model + session marker>
- **State:** claimed | done | partial | blocked | accepted | disputed | pending-trigger
- **Branch / commit:** <branch @ short SHA, or "uncommitted">
- **Files touched:** <list>
- **Summary:** <1-3 sentences>
- **Verification run:**
  - `<command>` → PASS / FAIL / N/A <(notable output)>
  - `<command>` → PASS / FAIL / N/A
- **Bytes recovered (if applicable):** <number, or N/A>
- **Bank impact (if applicable):** <which bank changed, before/after>
- **Issues / followups:** <anything deferred or surfaced for human>
- **Verifier check:** <how a future agent can independently confirm>
```

### State definitions

- **claimed** — agent is starting work; appended at session start to claim the finding so two agents don't collide.
- **done** — fix implemented, full verification floor passed, finding closed.
- **partial** — fix partially implemented; next agent can continue. Include where to pick up.
- **blocked** — agent stopped; cannot proceed without input. Surface to human.
- **accepted** — finding intentionally left as debt. Requires human approval.
- **disputed** — agent believes the finding is wrong; provide evidence.
- **pending-trigger** — finding gated on an external event. Log once.

### Update STATUS.md in the same commit

Whenever you append a terminal entry (`done` / `blocked` / `accepted` /
`disputed` / `partial` / `pending-trigger`), edit `STATUS.md` in the
**same commit** — set the `State` cell, set the `Last entry` cell to
this entry's timestamp, and add a one-line note if context is needed.
Don't update STATUS for `claimed` entries (too churny).

For a worked example, see the TD-010 blocked entry below.

---

## Real entries below (append here)

## 2026-05-03 01:52 UTC — TD-010 — claimed

- **Agent / session:** Opus 4.7 (1M context) / claude-unruffled-khayyam-35aa2d
- **State:** claimed
- **Branch / commit:** claude/unruffled-khayyam-35aa2d @ 02889a87
- **Files touched:** (none yet)
- **Summary:** Starting TD-010 `.gitignore` cleanup per FIX_PROPOSALS.md rank #1.
- **Verification run:** N/A (claim only)
- **Bytes recovered (if applicable):** N/A
- **Bank impact (if applicable):** N/A
- **Issues / followups:** N/A
- **Verifier check:** Look for the matching `done:` / `partial:` / `blocked:` entry below.

## 2026-05-03 01:55 UTC — TD-010 — blocked

- **Agent / session:** Opus 4.7 (1M context) / claude-unruffled-khayyam-35aa2d
- **State:** blocked
- **Branch / commit:** claude/unruffled-khayyam-35aa2d @ 02889a87 (no source edits made; only this AGENT_LOG entry)
- **Files touched:** tech_debt/AGENT_LOG.md (this entry)
- **Summary:** TD-010's premise is largely wrong. The "non-existent paths" the
  finding asks us to remove from `.gitignore` actually exist in the **main
  repo** — they only appear absent from a worktree (which carries only tracked
  files). Removing them would flip real, intentionally-ignored content
  (including the vendored RGBDS toolchain) into the untracked set. The
  duplicate-pattern analysis is also miswritten. Stopping per project rule
  "if the proposal turns out wrong, log blocked and surface to human; don't
  silently expand scope."
- **Verification run:**
  - `ls -la rgbds-1.0.1/ rgbds-win64.zip .local/ .claude_handoffs/ .rebalance_chain/` (from worktree) → all five "No such file or directory" — matches what the proposal author saw, but is misleading because worktrees don't carry untracked files.
  - `ls -la ../../../` (main repo) → shows `.claude_handoffs/`, `.local/`, `.rebalance_chain/`, `rgbds-1.0.1/`, `rgbds-win64.zip` all present as real directories/files.
  - `cd ../../../ && git status --ignored` → all five appear under "Ignored files" — correctly ignored today; would flip to untracked if their `.gitignore` entries were deleted.
  - `ls ../../../rgbds-1.0.1/` → confirms it contains `rgbasm.exe`, `rgblink.exe`, `rgbfix.exe`, `rgbgfx.exe`, `libpng16.dll`, `zlib1.dll` — i.e. the vendored RGBDS 1.0.1 toolchain CLAUDE.md's build command depends on. Removing this `.gitignore` entry would put ~1.2 MB of binaries into `git status` and risk an accidental commit.
- **Bytes recovered:** N/A
- **Bank impact:** N/A
- **Issues / followups for the human to reconcile:**
  1. **FINDINGS_DETAIL.md TD-010 list of "non-existent paths" is incorrect.**
     Lines 23 (`rgbds-1.0.1/`), 24 (`rgbds-win64.zip`), 25 (`rgbds-win64*.zip`),
     26 (`rgbds-*/`), 42 (`.local/`), 44 (`.claude_handoffs/`), 45
     (`.rebalance_chain/`) are all backing real ignored content in the main
     repo. The proposal's `ls` verification only worked from a worktree.
  2. **Duplicate-pattern analysis is miswritten.** FINDINGS_DETAIL says
     "Lines 54-56 duplicate lines 51-53 (`.sav`, `.rtc`, `.state`)." Looking
     at the actual file: lines 50-52 are `dist/*.sav`, `dist/*.rtc`,
     `dist/*.state` (dist-scoped) and lines 54-56 are `*.sav`, `*.rtc`,
     `*.state` (global). The relationship is the inverse of what the
     finding claims — the dist-scoped lines are subsets of the globals.
     The actual true duplicates are: line 54 `*.sav` duplicates line 34
     `*.sav` (in the emulator block); line 55 `*.rtc` duplicates line 35
     `*.rtc`. Line 56 `*.state` is unique — removing it would NARROW
     coverage. Lines 50, 51 are subsets of globals 34, 35. Line 52
     (`dist/*.state`) is a subset of line 56.
  3. **Recipe step 1 is unsafe as written.** "Remove non-existent path
     entries" with the listed lines would cause real ignored content to
     become untracked. Do not execute that step.
  4. **What's safely actionable in the spirit of TD-010:**
     - Delete lines 54-55 (`*.sav`, `*.rtc`) — true duplicates of 34-35.
     - Move `*.state` (line 56) into the emulator block at lines 32-38
       (where it logically belongs) so it stays covered globally.
     - Optionally delete lines 50-52 (`dist/*.sav`, `dist/*.rtc`,
       `dist/*.state`) since globals cover them — but the proposal's
       "defensive is fine" guidance suggests leaving the dist scope.
     None of the rgbds-/.local-/.claude_handoffs-/.rebalance_chain-
     deletions are safe.
  5. **Recommended human action:** mark TD-010 `accepted:` (kept as
     intentional debt — the entries are correct as-is) OR rewrite the
     recipe in FIX_PROPOSALS.md to scope it to lines 54-55 only, then
     re-open. Either way, `TECH_DEBT_REPORT.md` itself remains immutable
     per project rule; only `FIX_PROPOSALS.md` should be updated.
- **Verifier check:** From the **main repo root** (not a worktree): `git status --ignored 2>&1 | grep -E "rgbds-1\.0\.1|rgbds-win64|\.local|\.claude_handoffs|\.rebalance_chain"` should list all five paths under "Ignored files". `ls ../../../rgbds-1.0.1/` from this worktree should show the RGBDS binaries. If both are still true at the time of re-verification, the blocked: state holds.

## 2026-05-02 — TD-010 — done (corrected scope)

- **Agent / branch:** Opus 4.7 (1M context) / claude-unruffled-khayyam-35aa2d @ pending
- **Files touched:** .gitignore
- **Summary:** Executed `FIX_PROPOSALS.md` TD-010 "Updated 2026-05-02" corrected recipe. Deleted lines 54-55 (`*.sav`, `*.rtc` — true duplicates of lines 34-35 in the emulator block). Moved `*.state` from line 56 into the emulator block as a new line 39. Did **not** touch the `rgbds-1.0.1/`, `rgbds-win64*`, `.local/`, `.claude_handoffs/`, `.rebalance_chain/` entries (the original recipe wanted those deleted; ADDENDUM TD-010 supersession explains why that's wrong).
- **Verification:** `git diff .gitignore` → PASS (clean +1/-3 diff matching corrected scope); `ls ../../../{rgbds-1.0.1,.local,.claude_handoffs,.rebalance_chain}` (main repo) → PASS (all still present and gitignored).
- **Verifier check:** `grep -c '^\*\.sav$\|^\*\.rtc$' .gitignore` should return 1 each (only the emulator-block entry survives); `grep -c '^\*\.state$' .gitignore` should return 1 (moved into emulator block); `git ls-files --others --ignored --exclude-standard | head` from main repo should still list the rgbds binaries and scratch dirs as ignored.
