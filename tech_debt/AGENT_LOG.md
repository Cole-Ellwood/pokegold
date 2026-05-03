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

## 2026-05-02 — TD-011 — disputed

- **Agent / branch:** Opus 4.7 (1M context) / claude-unruffled-khayyam-35aa2d @ pending
- **Files touched:** tech_debt/TECH_DEBT_REPORT_ADDENDUM.md, tech_debt/FIX_PROPOSALS.md, tech_debt/STATUS.md (no source code changes)
- **Summary:** TD-011's "no references in docs/" claim is wrong. `docs/manifest.md:6` cites `scripts/export_changes_by_category.py` as the generator for `docs/CHANGES_BY_CATEGORY.txt`, which exists. The script is in active use — deleting it would silently break the next changelog regeneration. Logged disputed; ADDENDUM and FIX_PROPOSALS updated.
- **Verification:** `grep -n export_changes_by_category docs/manifest.md` → returns line 6 with the generator citation; `ls docs/CHANGES_BY_CATEGORY.txt` → file exists.
- **Verifier check:** `grep -rn 'export_changes_by_category' --include='*.md'` should return ≥1 hit in `docs/manifest.md`; if it doesn't, the docs-side reference has been removed and the dispute may need re-evaluation.

## 2026-05-02 — TD-009a — escalation needed (not blocked, scope expanded)

- **Agent / branch:** Opus 4.7 (1M context) / claude-unruffled-khayyam-35aa2d @ pending
- **Files touched:** tech_debt/TECH_DEBT_REPORT_ADDENDUM.md, tech_debt/STATUS.md (no source code changes)
- **Summary:** TD-009a's recipe assumes `hUnusedByte` and `hUnusedBackup` truly have no references. They have **dead writes**: `engine/overworld/events.asm:804`, `home/vblank.asm:147-148`, `engine/menus/intro_menu.asm:39-40`, `engine/menus/intro_menu.asm:45-46`. Field deletion alone won't compile. Recovery requires also removing those four write sites — touches vblank.asm (every-frame hot path), intro_menu.asm, events.asm. Technically safe, but escalating to user before executing because the scope crossed beyond `ram/hram.asm`.
- **Verification:** `grep -rn 'hUnusedByte\|hUnusedBackup' --include='*.asm'` → returned 5 hits (2 declarations + 4 writes) instead of the expected 2 declarations only.
- **Verifier check:** `grep -rn 'ldh \[hUnused' --include='*.asm'` should still return 4 matches until the writes are removed; if the count drops to 0, TD-009a has been completed and STATUS should be flipped to `done`.

## 2026-05-03 — TD-005 — claimed

- **Agent / session:** Opus 4.7 (1M context) / claude-compassionate-hugle-c80944
- **State:** claimed
- **Branch / commit:** claude/compassionate-hugle-c80944 @ ac99b056
- **Files touched:** (none yet)
- **Summary:** Starting TD-005 Pattern 1 (item-check subroutine extraction). First-conversion measurement plan: snapshot pokegold.gbc/.map as `.before`, add `_CheckUserItemEquals` helper at the end of `engine/battle/late_gen_held_items.asm` (bank 0e, 527 free bytes), convert ChoiceBand site (lines 21-32) only, rebuild, diff `.map` for "Late Gen Held Items" section size delta. Build was unblockable until this session's `ac99b056` fixed a pre-existing `FailText_CheckOpponentProtect_Far` link error.
- **Verification run:** N/A (claim only)
- **Bytes recovered (if applicable):** TBD via measurement
- **Bank impact (if applicable):** Bank 0e (Late Gen Held Items section)
- **Issues / followups:** Helper signature differs from FIX_PROPOSALS recipe ("input via `b`"). `b` doesn't survive `GetUserItem` (which writes the actual item there), so input is via `a` instead. Documented design notes in this entry's commit message and in the partial/done entry.
- **Verifier check:** Look for the matching `partial:` / `done:` / `blocked:` entry below.

## 2026-05-03 — TD-005 — partial (Pattern 1 closed; Patterns 2 and 3 open)

- **Agent / session:** Opus 4.7 (1M context) / claude-compassionate-hugle-c80944
- **State:** partial
- **Branch / commit:** claude/compassionate-hugle-c80944 @ pending
- **Files touched:** engine/battle/late_gen_held_items.asm, tools/audit/check_battle_math_safety.py, docs/generated/dev_index.md, tech_debt/AGENT_LOG.md, tech_debt/STATUS.md
- **Summary:** Pattern 1 (item-check boilerplate) converted via two shared subroutines `_CheckUserItemEquals` / `_CheckOpponentItemEquals` (sharing a tail `_CheckItemEquals_finish`) at the bottom of `late_gen_held_items.asm`. 9 callsites converted: ChoiceBand, ChoiceSpecs (User push/pop); AssaultVest, Eviolite_Def, Eviolite_SpD (Opponent push/pop, dual-exit sites collapsed onto `ret nz`/`ret z` which let `.no_boost_def` and `.no_boost_spd` labels be deleted); AirBalloon, RockyHelmet (Opponent no-pop); ShellBell, LifeOrb (User no-pop). Skipped 3 callfar sites that don't fit the pattern: `ApplyLateGenDamageMultipliers_Far` (multi-way dispatch on actual item value, not a single-item check) and 2 `[hl]`-style outliers (METAL_POWDER comparison via `ld a, [hl]`, GetItemHeldEffect). Also updated `tools/audit/check_battle_math_safety.py` to accept either the original push/pop pattern OR the helper pattern at ChoiceBand/ChoiceSpecs callsites, and to verify `_CheckUserItemEquals` itself preserves hl/bc — added `require_one_of` helper for that.
- **Verification run:**
  - `make pokegold.gbc` → PASS (links green)
  - `make compare` → SKIPPED (deliberate ROM-byte change; not the floor for TD-005 per FIX_PROPOSALS Updated 2026-05-02)
  - `python3 tools/audit/check_release_smoke.py` → PASS
  - `python3 tools/audit/check_battle_math_safety.py` → PASS (after audit update for new pattern)
  - `python3 tools/audit/check_save_format_version.py` → PASS
  - `python3 scripts/generate_dev_index.py --rom pokegold` → PASS, regenerated
  - `python3 tools/audit/check_navigation_floor.py` → 2 PRE-EXISTING FAILS (`tools/stadium.exe` path in `docs/review_playbook.md`; whitespace diff check exits 128 due to WSL/git path translation). Both unrelated to this change.
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS
  - `.map` bank-size diff: `Late Gen Held Items` section $704f-$7df0 (3490 bytes) → $704f-$7dc7 (3449 bytes). **Net: -41 bytes.**
- **Bytes recovered:** 41 bytes
- **Bank impact:** Bank 0e — `Late Gen Held Items` section: 3490 → 3449 bytes. Bank 0e free space (per regenerated `dev_index.md`): was 527 bytes, now 568 bytes (+41).
- **Issues / followups:**
  1. **Pattern 1 measured at 41 bytes**, below the FIX_PROPOSALS "Updated 2026-05-02" `<100 byte stop-and-re-evaluate` trigger. After re-evaluation, decided to proceed: 41 bytes in tight bank 0e is real and useful, refactor cost (8 mechanical edits + 23-byte helper block) is small. Decision noted here so future agents understand the threshold was crossed deliberately, not ignored.
  2. **Helper signature deviates from FIX_PROPOSALS recipe.** Recipe said input via `b`; that conflicts with `GetUserItem` itself writing `b`. Input is via `a` instead, with internal push/pop preserving hl, bc, and the target value (push af before callfar). Documented in inline comments at the helper definition.
  3. **Pattern 2 (multiply/divide thunk)** not attempted this session: would touch `engine/pokemon/experience.asm`, which is on the user's no-touch WIP list per the handoff. Defer until WIP lands or user un-blocks.
  4. **Pattern 3 (`hBattleTurn` side-branch)** not attempted: enumeration step not done. Initial grep found 234 `ldh a, [hBattleTurn]` candidates across 49 files — needs filtering down to the actual side-branch pattern before per-site work.
  5. **Pre-session build break** at `engine/battle/effect_commands.asm:2280` (`FailText_CheckOpponentProtect_Far` undefined) was fixed in this session's commit `ac99b056` so any TD work needing a build floor would be possible. That fix is unrelated to TD-005 and lives in its own commit.
- **Verifier check:** From this branch tip, `grep -c '^_CheckUserItemEquals:\|^_CheckOpponentItemEquals:\|^_CheckItemEquals_finish:' engine/battle/late_gen_held_items.asm` should return 3. `grep -c 'callfar GetUserItem\|callfar GetOpponentItem' engine/battle/late_gen_held_items.asm` should return 4 (the helper pair counts as 2; `ApplyLateGenDamageMultipliers_Far` and the 2 `[hl]`-style outliers account for the remaining hits — 2 not 3 because METAL_POWDER's site is `callfar GetOpponentItem` followed by `ld a, [hl]`, and `.GetItemHeldEffect` uses `callfar GetUserItem` followed by `ld a, [hl]`). The Late Gen Held Items section in `pokegold.map` should be `<= $0d79` bytes if rebuilt without further changes.

## 2026-05-03 — TD-007 — claimed

- **Agent / session:** Opus 4.7 (1M context) / claude-compassionate-hugle-c80944
- **State:** claimed
- **Branch / commit:** claude/compassionate-hugle-c80944 @ 23d96d65
- **Files touched:** (none yet)
- **Summary:** Starting TD-007 selective label pruning. Scope: 47 unique `Beta*_Blocks` labels in `data/maps/blocks.asm`, all marked `; unreferenced`, all verified to have exactly 1 ref (the definition itself). Each has its own INCBIN to `maps/unused/Beta*.blk`; total INCBIN bytes: 5,854. The data lives in `Map Blocks 1` (bank 0x2a, currently 85 free), `Map Blocks 2` (bank 0x2b, 166 free), and bank 0x37 — the first two are tight per the dev_index. Plan: delete only the source-side label + INCBIN lines (47 blocks), leave the `.blk` files in `maps/unused/` for reversibility. Will measure section size deltas via `.map` diff before/after.
- **Verification run:** N/A (claim only)
- **Bytes recovered (if applicable):** TBD via measurement — projected ~5,854 bytes
- **Bank impact (if applicable):** Banks 0x2a, 0x2b, 0x37 (mostly the first two)
- **Issues / followups:** Not deleting the `.blk` files themselves — that's a related but separate cleanup. SHA1 will shift by design (per FIX_PROPOSALS, TD-007 is the one finding where SHA1 update is expected). Per recipe, escalate the SHA1 update to the user before touching `roms.sha1`.
- **Verifier check:** Look for the matching `done:` / `partial:` / `blocked:` entry below.

## 2026-05-03 — TD-007 — done (Beta\*_Blocks pruning; SHA1 update deferred to user)

- **Agent / session:** Opus 4.7 (1M context) / claude-compassionate-hugle-c80944
- **State:** done
- **Branch / commit:** claude/compassionate-hugle-c80944 @ pending
- **Files touched:** data/maps/blocks.asm, docs/generated/dev_index.md, tech_debt/AGENT_LOG.md, tech_debt/STATUS.md
- **Summary:** Removed 47 unique `Beta*_Blocks` label + INCBIN pairs from `data/maps/blocks.asm` (all marked `; unreferenced`, all verified to have exactly 1 ref = the definition itself). Used a Python filter that recognizes the 3-line block pattern (label + INCBIN + blank separator) and deletes them atomically; collapsed any 3+ blank-line runs back to 2. Left the `.blk` files in `maps/unused/` for reversibility — deleting source data files is a separate cleanup outside TD-007 scope. **5,854 bytes recovered** across three Map Blocks sections, exact match to the pre-build projection (sum of all `.blk` file sizes).
- **Verification run:**
  - `make pokegold.gbc` → PASS (links green)
  - `make compare` → SKIPPED (deliberate ROM-byte change; per FIX_PROPOSALS this is the one finding where SHA1 update is expected)
  - `python3 tools/audit/check_release_smoke.py` → PASS
  - `python3 tools/audit/check_battle_math_safety.py` → PASS
  - `python3 tools/audit/check_save_format_version.py` → PASS
  - `python3 tools/audit/check_workspace_hygiene.py` → PASS (from Windows Git Bash; the WSL run fails on git path translation, environmental not a regression)
  - `python3 scripts/generate_dev_index.py --rom pokegold` → regenerated, tight-banks list updated (banks 0x2a and 0x2b dropped out entirely)
  - `python3 tools/audit/check_navigation_floor.py` → 2 pre-existing FAILS (stadium.exe path in `docs/review_playbook.md`; whitespace diff env error from WSL/git). Unrelated.
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS
  - `.map` section size diffs (before → after):
    - `Map Blocks 1` (bank 0x2a): $3fab → $31ff = **-3,500 bytes**
    - `Map Blocks 2` (bank 0x2b): $3f5a → $3687 = **-2,259 bytes**
    - `Map Blocks 3` (bank 0x37): $1773 → $1714 = **-95 bytes**
    - Sum: 5,854 bytes (matches projection exactly)
- **Bytes recovered:** 5,854 bytes
- **Bank impact:**
  - Bank 0x2a free: 85 → 3,585 bytes (was tightest in tight-banks list)
  - Bank 0x2b free: 166 → 2,425 bytes (was second-tightest map bank)
  - Bank 0x37 free: was already spacious (~10,000 free), gained 95 bytes
  - Both 0x2a and 0x2b dropped out of the dev_index tight-banks list entirely
- **Issues / followups:**
  1. **`roms.sha1` and `dist/checksums.txt` stale.** Per FIX_PROPOSALS TD-007 recipe: "Record the new SHA1 in `roms.sha1` only after a build verifies and at least one manual playtest confirms gameplay parity. Escalate the SHA1 update to the human." Skipped — needs user playtest + approval. Both files predate this commit's intentional ROM byte change (and several earlier intentional changes — `roms.sha1` is the upstream pret/pokegold baseline; `dist/checksums.txt` was last refreshed before commits like 1f5fd6af and 65c5296f). A combined SHA1/checksums refresh after user playtest will close this gap.
  2. **`.blk` source files in `maps/unused/` left intact.** 47 files, ~5,854 bytes on disk. Reversible: re-adding the label + INCBIN line restores the data. If repo cleanup wants to also drop the `.blk` files, that's a separate small commit. Recommend leaving until/unless a release pass.
  3. **Strategic implication for TD-001 / TD-004.** Banks 0x2a and 0x2b are no longer tight, meaning sections currently in bank 0x0e (e.g. `engine/battle/type_passive_damage_mods.asm`, `engine/battle/late_gen_held_items.asm`) could potentially be relocated there to relieve bank 0x0e for the boss.asm split (TD-004). The 41 bytes Pattern 1 freed in bank 0x0e is not enough headroom on its own. Re-evaluation of TD-001's bank-pressure table and TD-004's bank assumptions is now warranted.
  4. **Pic banks (0x12, 0x15, 0x17, 0x1b, 0x1c, 0x1e, 0x1f) remain at 0-1 byte free.** TD-007 didn't touch those — they're pic data, not source labels. The `data/maps/blocks.asm` cleanup doesn't affect them. Future TD-007 work, if any, should target pic data via a different mechanism (already noted in the original FIX_PROPOSALS).
- **Verifier check:** From this branch tip, `grep -c '^Beta' data/maps/blocks.asm` should return 0. `wc -l data/maps/blocks.asm` should be ~857 (was 998). After a full rebuild, `pokegold.map` Section sizes for `Map Blocks 1`/`2`/`3` should be `$31ff`/`$3687`/`$1714` (or smaller if other size-affecting changes have landed). The `maps/unused/Beta*.blk` files should still exist on disk (47 files).

## 2026-05-03 06:22 UTC — TD-001 — partial (re-evaluation: snapshot refresh)

- **Agent / session:** Opus 4.7 (1M context) / claude-nice-lamarr-f8a7e2
- **State:** partial
- **Branch / commit:** claude/nice-lamarr-f8a7e2 @ pending
- **Files touched:** tech_debt/TECH_DEBT_REPORT_ADDENDUM.md, tech_debt/FIX_PROPOSALS.md, tech_debt/STATUS.md, tech_debt/AGENT_LOG.md (this entry)
- **Summary:** TD-001 re-evaluation per FIX_PROPOSALS Original-order rank #11 ("re-evaluate after byte-recovery items"). Doc-only output; no source code changes. The bank-pressure snapshot in TECH_DEBT_REPORT.md (2026-05-02) is substantially stale — META_AUDIT TD-A07 already flagged it as point-in-time data in an immutable doc. Bank 0x0e went from a reported "6 free" → current 568 free (drifted before report time + 41 from TD-005 P1 this session). The original framing — "0x0e is the canary, boss AI edits risk link failure" — is no longer true. The new canary is ROMX 0x0d (Effect Commands) at 6 free. TD-004 (boss split) is no longer bank-pressure-gated. Section relocations off 0x0e are no longer required. Pic banks (12/15/17/1b/1c/1e/1f) unchanged at 0-1 free; original pic-bank-guard recommendation still applies. Two new tight regions surfaced: WRAM0 (49 free) and ROMX 0x16 (48 free). Updated guidance committed in ADDENDUM 2026-05-03 + FIX_PROPOSALS "Updated 2026-05-03" subsection. Finding stays `partial` as a strategic monitoring item until TD-005 P2/P3, TD-009a, and pic-bank guard close.
- **Verification run:**
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS (5 ADDENDUM entries cross-linked, 13 TD-### IDs consistent across REPORT/STATUS, file refs OK)
  - dev_index.md regeneration: not run — already fresh from this session's prior TD-005/TD-007 work (Generated: 2026-05-03).
- **Bytes recovered:** N/A (doc-only; addendum captures cumulative bank deltas from prior sessions for context)
- **Bank impact:** N/A (doc-only)
- **Issues / followups:**
  1. The original TD-001 table in TECH_DEBT_REPORT.md remains immutable per project rule. Future agents must read ADDENDUM 2026-05-03 alongside the report to get the current picture. Same supersession pattern as TD-010 / TD-013 / TD-009 / TD-011 / TD-009a.
  2. **ROMX 0x0d at 6 free is the new "watch this bank" item.** If future work touches `engine/battle/effect_commands.asm` or `engine/battle/used_move_text.asm`, a pre-edit bank-free check is required. Pre-edit recipe: `grep -A1 'ROMX | 0d' docs/generated/dev_index.md` to confirm free-byte count, then estimate edit byte impact.
  3. **Close-out path for TD-001:** when TD-005 P2/P3 complete (or are accepted as debt) AND TD-009a executes (or accepted) AND the pic-bank guard ships, TD-001 can move to `accepted` — intentionally monitored via dev_index regeneration on every build, no longer an actionable backlog item.
  4. **TD-004 sequencing implication.** Original FIX_PROPOSALS recommended-order put TD-004 after TD-005 because boss.asm split was assumed to need bank headroom. With 0x0e at 568 free, that dependency is gone. TD-004 can be planned independently. Recommend leaving its rank in FIX_PROPOSALS unchanged for now (it's still HIGH effort, multi-session) but note the unblock.
- **Verifier check:** From this branch tip, the dev_index "Tight Banks And Regions" table should match (or be lighter than) the snapshot in ADDENDUM 2026-05-03. Quick checks: `grep -c '^| ROMX | 0d ' docs/generated/dev_index.md` → 1 (0x0d still tight). `grep -c '^| ROMX | 0e ' docs/generated/dev_index.md` → 0 (0x0e dropped out of tight-banks list; if it returns 1, regression — re-read this addendum). `grep -c '^| ROMX | 16 ' docs/generated/dev_index.md` → 1 (newly tight). `grep -c '^| WRAM0 | 00 ' docs/generated/dev_index.md` → 1 (newly tight).

## 2026-05-03 — TD-001 — partial (pic-bank pressure guard shipped)

- **Agent / session:** Opus 4.7 (1M context) / claude-trusting-kare-692dd4
- **State:** partial
- **Branch / commit:** claude/trusting-kare-692dd4 @ pending
- **Files touched:** tools/audit/check_pic_bank_pressure.py (new), tools/audit/data/pic_bank_baseline.json (new)
- **Summary:** Shipped one of TD-001's three remaining concrete deliverables: the pic-bank pressure guard called for in `FIX_PROPOSALS.md` TD-001 Approach #3 (and re-confirmed in the "Updated 2026-05-03" subsection). Reads the "Tight Banks And Regions" table from `docs/generated/dev_index.md`, compares the 8 known pic banks (12, 15, 17, 1a, 1b, 1c, 1e, 1f) against a JSON baseline, FAILs if any drops below baseline. `--update` refreshes the baseline. Initial baseline recorded matches the 2026-05-03 dev_index snapshot ($12=0, $15=0, $17=0, $1a=4, $1b=0, $1c=1, $1e=0, $1f=1). The audit is a *cushion* check (catches encroachment); the link itself catches actual overflow.
- **Verification run:**
  - First run with no baseline → FAIL with instructive `--update` message (expected).
  - `--update` → wrote baseline JSON.
  - Re-run → PASS with summary of bank free counts.
  - Tampered baseline (set 1c=5 manually, then re-ran) → FAIL with `$1c: 5 free baseline -> 1 free now (-4)` + instructive message. Restored baseline via `--update`.
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS.
- **Bytes recovered:** N/A (tooling addition; protects future bytes).
- **Bank impact:** N/A (no source code change).
- **Issues / followups:**
  1. **Audit floor placement.** Not added to `check_release_smoke.py` yet — per `FIX_PROPOSALS.md` and CLAUDE.md, the explicit promotion to release-smoke floor is a separate decision (similar to how `check_cross_bank_call.py` is currently diagnostic-only with 39 known hits). Recommend running it before any sprite-size change as a pre-commit check.
  2. **TD-001 remaining items after this session:** TD-005 Pattern 2 (gated on user WIP in `experience.asm`) and TD-005 Pattern 3 (enumeration shipped this session — see next AGENT_LOG entry; conversion still open), and TD-009a (gated on user OK for vblank/intro_menu/events dead-write removal). Pic-bank guard is now off the list.
  3. **Bank 0x1a inclusion.** ADDENDUM 2026-05-03 lists 0x1a at 4 free as a pic-adjacent bank; original FIX_PROPOSALS list (12/15/17/1b/1c/1e/1f) didn't include 1a. Audit guards all 8 conservatively; if 0x1a isn't truly pic data, the extra coverage is harmless (the `--update` workflow handles deliberate slack changes).
- **Verifier check:** From this branch tip, `ls tools/audit/check_pic_bank_pressure.py tools/audit/data/pic_bank_baseline.json` should show both files. `python3 tools/audit/check_pic_bank_pressure.py` should print `Pic-bank pressure OK: ...` and exit 0. `cat tools/audit/data/pic_bank_baseline.json` should match the 2026-05-03 snapshot ($12=0, $15=0, $17=0, $1a=4, $1b=0, $1c=1, $1e=0, $1f=1). If a future sprite change drops any bank's free count, the audit FAILs and points the agent at `--update`.

## 2026-05-03 — TD-005 — partial (Pattern 3 enumeration shipped; conversion still open)

- **Agent / session:** Opus 4.7 (1M context) / claude-trusting-kare-692dd4
- **State:** partial
- **Branch / commit:** claude/trusting-kare-692dd4 @ pending
- **Files touched:** tech_debt/EVIDENCE/td_005_pattern3_sites.md (new)
- **Summary:** Closed the precursor step for TD-005 Pattern 3 called for in `FIX_PROPOSALS.md` "Updated 2026-05-02" (and `META_AUDIT.md` TD-A06). Wrote a Python classifier (kept in `.local/`, not committed) that walks all `.asm`, finds every `ldh a, [hBattleTurn]`, and classifies each site by shape using a 12-line context window. Output: 234 total reads → **66 Class A** (side-branch eligible), 138 Class B (control-flow only), 30 Class C (turn-flag-as-data). Class A is below the report's "100+" claim but well above the "speculative until measured" bar. Per-file Class A breakdown: 27 in `effect_commands.asm` (canary bank 0x0d, 6 free), 10 in `type_passive_damage_mods.asm`, 6 in `core.asm`, balance scattered. The 27 in 0x0d are the highest-leverage cluster — converting that group alone could relieve the canary bank by ~140 bytes if per-site savings hit the recipe's ~5-byte target. Spot-checked 4 classifier outputs against actual source: 100% match on the spot sample.
- **Verification run:**
  - `python3 .local/classify_pattern3.py | head -5` → reports 234/66/138/30 split (matches recipe expectations).
  - Spot checks on `engine/battle/core.asm:381` (Class A, hl), `core.asm:1087` (Class A, de), `home/battle.asm:39` (Class B, control flow), `core.asm:1326` (Class C, `xor 1` toggle) → all classifications correct.
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS.
- **Bytes recovered:** N/A (enumeration only; conversion is the byte-recovery step and is not in this session's scope).
- **Bank impact:** N/A.
- **Issues / followups:**
  1. **Conversion still open.** Pattern 3 itself is not closed by this entry — the `_GetSidedAddr` helper still needs to be written and call sites converted. The evidence file documents the implementer caveats (helper bank placement, three target registers not one, site-shape variance, recommended starting site).
  2. **Helper-bank-placement caveat is real.** ROM0 has 236 free; the helper is ~8-12 bytes; logical home is `home/battle.asm`. Putting it in a ROMX bank forces `callfar` per site (5 bytes per site = ate the savings). This decision needs to be made explicit before converting.
  3. **Three target registers (hl/de/bc) not one.** Recipe assumes return-in-hl. 38/66 sites use hl; 23 use de; 5 use bc. Either three helpers or a register-move tail per non-hl site. Evidence file analyzes both options.
  4. **Classifier is one-shot.** Lives in `.local/classify_pattern3.py`, not committed. Reproduce instructions are in the evidence file. If a future agent needs to refresh the count, the classifier is 60 lines of Python.
  5. **TD-005 stays partial.** Pattern 1 closed in prior session (-41 bytes); Pattern 2 still gated on user WIP in `experience.asm`; Pattern 3 enumeration done but conversion open. STATUS row updated with the new sub-state.
- **Verifier check:** From this branch tip, `ls tech_debt/EVIDENCE/td_005_pattern3_sites.md` should exist. `wc -l tech_debt/EVIDENCE/td_005_pattern3_sites.md` should be ~150-180 lines. The Class A list inside should have exactly 66 file:line entries. `grep -c "	A	"` of the classifier output (regenerated locally) should still report 66 (or close — small drift is normal as battle code evolves).

## 2026-05-03 — TD-A14 — done (navigation_floor build-artifact carveout)

(TD-A### — codebase finding tracked in `TECH_DEBT_REPORT_ADDENDUM.md`,
no STATUS row by design. This log entry is for chronological trail
only; the canonical state lives in the ADDENDUM entry's "State"
section.)

- **Agent / session:** Opus 4.7 (1M context) / claude-trusting-kare-692dd4
- **State:** done
- **Branch / commit:** claude/trusting-kare-692dd4 @ pending
- **Files touched:** tools/audit/check_docs_navigation.py, docs/generated/balance_audit.md (regen)
- **Summary:** Patched `check_docs_navigation.py` to downgrade build-artifact (`pokegold.map`/`pokegold.sym`/`tools/stadium.exe`) and vendored-toolchain (`rgbds-1.0.1/*`) absences from FAIL to WARN. Added `BUILD_ARTIFACT_PATHS` set, `VENDORED_TOOLCHAIN_PREFIXES` tuple, `is_build_artifact_or_toolchain_ref()` helper. Both `check_required_paths()` and `check_backtick_references()` use the new helper. `check_generated_index()` skips the dev_index regen comparison when `pokegold.map` is absent. Also regenerated `docs/generated/balance_audit.md` to clear an unrelated staleness FAIL surfacing alongside.
- **Verification run:**
  - `python3 tools/audit/check_docs_navigation.py` → ALL DOC NAVIGATION CHECKS PASSED (4 WARNs for missing build-artifacts, none promoted to errors).
  - `python3 tools/audit/check_navigation_floor.py` → "Navigation floor passed."
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS.
- **Bytes recovered:** N/A (audit-only).
- **Bank impact:** N/A.
- **Issues / followups:**
  1. **From main repo with a build,** the audit will still validate dev_index freshness and verify build artifacts exist. Behavior change is scoped to the worktree-without-build path.
  2. **balance_audit.md regen** captured drift that pre-existed this session (DUNSPARCE/TOGETIC/VENOMOTH/QUAGSIRE rows); not a behavior change introduced by my edits.
- **Verifier check:** From a worktree without `pokegold.map`/`pokegold.sym`, `python3 tools/audit/check_navigation_floor.py` should exit 0 with "Navigation floor passed." From main repo after a build, it should still pass and validate dev_index freshness (the WARN-only path triggers solely on missing artifacts).

## 2026-05-03 — TD-A15 — done (47 orphan Beta*.blk files removed)

(TD-A### — codebase finding tracked in `TECH_DEBT_REPORT_ADDENDUM.md`,
no STATUS row by design. This log entry is for chronological trail
only; the canonical state lives in the ADDENDUM entry's "State"
section.)

- **Agent / session:** Opus 4.7 (1M context) / claude-trusting-kare-692dd4
- **State:** done
- **Branch / commit:** claude/trusting-kare-692dd4 @ pending
- **Files touched:** maps/unused/Beta*.blk (47 deletions), maps/unused/ (now empty, removed from filesystem).
- **Summary:** `git rm maps/unused/Beta*.blk` removed all 47 orphan binary files left behind by TD-007's source-side label cleanup. Reference safety verified pre-deletion via `grep -rn '<filename>' --include='*.asm'` for each of the 47 — zero hits. The `.blk` files were the entire content of `maps/unused/`; the directory itself is now gone. 5,854 bytes of file content removed from the working tree (~47 KB in disk-block padding).
- **Verification run:**
  - `git status --short | grep -c '^D '` → 47 (matches expected count).
  - `ls maps/unused/Beta*.blk 2>&1` → "No such file or directory" (gone).
  - `grep -rn 'maps/unused' --include='*.asm' --include='*.md' --include='*.py' --include='*.link'` → only AGENT_LOG / ADDENDUM self-references remain (this entry, the TD-007 done entry's followup #2, the TD-A15 ADDENDUM entry).
  - `python3 tools/audit/check_tech_debt_freshness.py` → PASS.
- **Bytes recovered:** N/A from ROM perspective (TD-007 already recovered the 5,854 ROM bytes by deleting the source-side INCBIN lines). Disk-only cleanup of orphan binaries.
- **Bank impact:** N/A.
- **Issues / followups:**
  1. **TD-007 followup #2 closed.** That followup said "47 files, ~5,854 bytes on disk. Reversible: re-adding the label + INCBIN line restores the data. If repo cleanup wants to also drop the `.blk` files, that's a separate small commit. Recommend leaving until/unless a release pass." This entry is that small commit. Reversibility now via `git show <pre-deletion-commit>:maps/unused/<filename>.blk` if anyone ever wants the data back.
- **Verifier check:** `ls maps/unused/ 2>&1` → "No such file or directory" (or empty if a future agent recreated the dir for other reasons). `git log --diff-filter=D --name-only` should show the 47 deletions in this branch's commit history once committed.

