# Codex implementation playbook

A structured menu of implementation tasks for this hack that Codex can
execute with `/goal`. Each task is self-contained — feed the relevant
section to a fresh Codex session and it has everything needed. The
bug-check methodology in §1 applies to every task and is what makes
Codex's output trustworthy without re-checking line by line.

> **This doc is for Codex execution.** It complements `CLAUDE.md` (which
> describes the senior-dev contract), `docs/asm_authoring_guide.md`
> (which is the canonical asm reference), and the per-system docs under
> `docs/agent_navigation/`. It is **not** a project plan or a
> design-decision doc — taste calls escalate to the user, never live
> here.

## How to use this doc

1. Pick a task from §3 (or compose one in the same shape).
2. Open a fresh Codex session.
3. Paste **the entire task block** (its `/goal` line + its full body).
   Codex sessions are fresh — they need the whole spec, not a reference.
4. When Codex reports done, spot-check its work against §1's
   methodology. If it matches the bug-check format and the audits pass,
   trust it. If not, push back with specifics.
5. When you're done with a task, mark it done in §3 (or remove the row).

The `/goal` line is intentional. Codex's `goal` skill anchors a session
to a single deliverable and reports a structured Findings list at the
end. Without it, Codex tends to drift or stop early.

---

## §1 Bug-check methodology

Every task ends with Codex emitting a Findings report and you (or me)
spot-checking it. The bar is "trust but verify, fast" — not re-doing
Codex's work.

### 1.1 Findings format Codex must emit

For each spot-check category in the task spec, Codex emits:

```
File / Line:  <path>:<line> or <symbol>
Issue:        PASS or FAIL — <one-line summary>
Why:          <what would break if this regressed>
Fix:          <what was changed, or "none" for PASS>
Confidence:   High | Medium-high | Medium | Low
              + one-line reason if not High
```

This is the format the print/photo follow-up Codex run produced
(`8cb0fc2a` merge body) and it reads cleanly. Reject any other format —
it's the difference between "I checked X" (claim) and "X passes
because Y" (verifiable).

### 1.2 Universal checks every task runs before "done"

| Check | When | Command |
| --- | --- | --- |
| 4-ROM build | always | `wsl -e bash -lc 'cd "<worktree>" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc pokegold_debug.gbc pokesilver_debug.gbc'` |
| `roms.sha1` bumped + verified | if ROM bytes changed | `python tools/verify_sha1.py roms.sha1` (all 4 + 2 patches OK) |
| `roms.sha1` byte-identical to dev tip | if change is python/docs only | `git diff origin/codex/cleanup-gsc-rebalance-split -- roms.sha1` (empty) |
| `check_release_smoke.py` | always | `python tools/audit/check_release_smoke.py` |
| `check_cross_bank_call.py` | if asm touched | `python tools/audit/check_cross_bank_call.py` |
| `check_save_format_version.py` | if `ram/` touched | `python tools/audit/check_save_format_version.py` (must PASS, fingerprint byte-identical to pre-change unless `SAVE_FORMAT_VERSION` was bumped — and bumps require user approval) |
| `check_no_stale_shipped_claims.py` | if `.md` files touched with date claims | `python tools/audit/check_no_stale_shipped_claims.py` |
| `check_docs_navigation.py` | if `docs/` touched | `python tools/audit/check_docs_navigation.py` |
| `check_typepassive_c_mirror.py` | if `engine/battle/late_gen_held_items.asm` or `type_passive_damage_mods.asm` touched | `python tools/audit/check_typepassive_c_mirror.py` |
| `clobber_smoke` | if battle-code register ABI touched | `python -m tools.damage_debugger.clobber_smoke` (24/24 PASS) |
| `dev_index` regen | always | `python scripts/generate_dev_index.py --rom pokegold` (no diff after final regen) |
| `balance_audit` regen | if balance tables touched | `python scripts/generate_balance_audit.py` |

If a check is irrelevant to the task scope, Codex should say so
explicitly with one-line reason — never silently skip.

### 1.3 Common Codex misses (lessons from this session)

These were caught during the print/photo cleanup. Codex should
proactively scan for them on every task that fits the pattern.

| Pitfall | Symptom | Mitigation |
| --- | --- | --- |
| **VC patch templates carry stale symbol refs** | Regular ROM build passes, `make pokegold.patch pokesilver.patch` fails | When deleting any symbol that has a `vc_hook` / `vc_patch` reference, also grep `vc/pokegold.patch.template` and `vc/pokesilver.patch.template` for the symbol name and remove the matching `[print forbid X@SymName]` block. Caught in commit `93263564` during print/photo bug-check. |
| **Commit lands on the wrong branch** | `b1afda99` BOSSAI runner committed onto `codex/damage-debugger-roadmap-20260506` instead of a fresh dev-tip worktree | Always start with `git worktree add <path> origin/codex/cleanup-gsc-rebalance-split` per the task spec, then `cp -r ../../../rgbds-1.0.1 .`. Verify `git rev-parse HEAD` matches the expected dev tip before committing. |
| **`commit XYZ` cite format** | `check_no_stale_shipped_claims.py` keeps warning even after you add a hash | The audit's regex is `\bcommit\s+\`?(?P<hash>[0-9a-f]{7,40})\`?`. Plural `commits` doesn't match. Use singular `commit \`abc1234\` + commit \`def5678\`` for multiple cites on one line. |
| **Co-named WRAM aliases vs bytes** | Removing one alias inside a `wMomBankDigitCursorPosition:: \\ wPrinterQueueLength::` style block doesn't change layout | Removing a label is fine. Removing a `db` / `dw` / `ds N` directive is what shifts offsets. Don't touch the directive unless intentionally resizing. |
| **ID-table re-indexing** | Music plays the wrong song; events fire wrong handler; `special X` calls go to wrong destination | When removing an entry mid-list (e.g. `dba Music_Printer`), replace with a placeholder of identical width (`dba Music_Nothing`), don't delete the line. Same rule for `add_special` and event flags. |
| **Cross-bank `call` after refactor** | Symptom: silent jump-to-garbage, often crashes | Audited by `check_cross_bank_call.py`. If you change a `farcall` to `call` (or vice versa), run this audit. The May 2026 type-immunity softlock and rival-1 softlock both came from this. |
| **`farcall` clobbers caller's `hl`** | Caller's `hl` corrupted before target runs | Three valid patterns in `docs/asm_authoring_guide.md` §3.2. Don't pick a fourth. |
| **`farcall` return — `a` = target's `c`, not target's `a`** | Caller reads garbage from `a` after farcall | See `home/farcall.asm:13-28`. Mirror the value to `c` at every `ret` in the target, OR return via HRAM, OR use a HOME thunk. Audited by `check_farcall_a_clobber.py`. |
| **Adding a register write at function exit** | Same-bank in-bank callers whose `bc` is load-bearing post-dispatch break silently | The AG-08 `c`-mirror trap. Run `clobber_smoke` after any battle-code ABI change. |
| **Scope creep** | Task's diff sprawls beyond the stated goal | Codex should call out and refuse. Single-task PRs are easier to review and revert. |

### 1.4 What good Findings look like

Real example from print/photo follow-ups (merge `8cb0fc2a`):

```
File/Line: vc/pokegold.patch.template:528; vc/pokesilver.patch.template:536
Issue: FAIL fixed in this merge — stale [print forbid *@Forbid_printing_*]
       VC patch blocks survived the printer-symbol removal.
Why:   The regular ROM build still passed, but `make pokegold.patch
       pokesilver.patch` failed because make_patch could not resolve
       .VC_Forbid_printing_Unown and the related deleted hook labels.
Fix:   Removed the obsolete print-forbid patch blocks, removed deleted
       printer symbol names from comments/history so the orphan scan is
       clean, regenerated patch SHA1s in roms.sha1 in 93263564.
Confidence: High — VC patches regenerate, verify_sha1 OK for ROMs and
            patches, deleted-symbol rg returns zero matches.
```

Note the structure: precise location, one-line summary, why-it-matters,
what-was-done, and a confidence + reason. That's the bar.

---

## §2 Workflow rituals

These belong in every task block but are factored here.

### 2.1 Worktree setup (first thing in every task)

```bash
git fetch origin
git worktree add .claude/worktrees/codex-<task-slug> \
    origin/codex/cleanup-gsc-rebalance-split
cd .claude/worktrees/codex-<task-slug>
cp -r ../../../rgbds-1.0.1 .   # gitignored, required for build
git rev-parse HEAD              # confirm dev tip
```

### 2.2 Per-piece commit pattern (handoff convention)

Build → audit → verify → commit per piece, not all-at-once. Each commit
should:
- start with a lowercase prefix matching the area: `print:`, `bossai:`,
  `bossai-debugger:`, `tm-system:`, `dragon-narrative:`, `bugfix:`, etc.
- have an em-dash separator: `prefix: action — short rationale`
- include a `Co-Authored-By: ...` trailer

### 2.3 Merge to dev tip (commit-tree push pattern)

`codex/cleanup-gsc-rebalance-split` is normally checked out somewhere
(another worktree, the main repo). Don't try to check it out — use the
commit-tree pattern that pushes a merge commit without checkout:

```bash
# from a worktree whose branch is rebased onto current dev tip:
git fetch origin
MERGE_SHA=$(git commit-tree HEAD^{tree} \
    -p origin/codex/cleanup-gsc-rebalance-split \
    -p HEAD \
    -m "Merge: <task title>

<bug-check report in Findings format>")
git push origin "$MERGE_SHA:refs/heads/codex/cleanup-gsc-rebalance-split"
```

This is non-destructive (every prior commit is reachable from the merge
commit's first parent). If the push is rejected as non-fast-forward,
`git fetch` first and rebase.

### 2.4 Cleanup after merge

```bash
git fetch origin
cd ..  # exit the worktree
git worktree remove .claude/worktrees/codex-<task-slug>
```

Don't leave codex worktrees around — they accumulate audit noise (see
the lucid-bartik-93f5ff lesson; it sat for 3 days as a "phantom
rollback" until I diagnosed it as stale).

### 2.5 If anything goes wrong

- **Build fails:** read the actual error; don't assume. Most often a
  leftover INCLUDE referencing a deleted file, or a typo'd symbol.
- **Audit fails:** read the audit's complaint exactly. Audits in this
  repo print specific file:line + reason.
- **Save-format fingerprint changes:** **do not bump
  `SAVE_FORMAT_VERSION`** without escalating. The user must approve any
  save-format-shipping change. Revert the layout shift instead — most
  often it's a renamed `wOptions`-region label.
- **`make compare` mismatch on a parity-preserving change:** the change
  is not actually parity-preserving. Either accept the SHA bump or
  diagnose what added bytes.

---

## §3 Active task menu

Each task is self-contained. Pick one, paste the whole section into a
fresh Codex session, run.

### Task 3.1 — Mystery Gift removal (cleanup roadmap step 2/3)

```
/goal remove the Mystery Gift subsystem from the hack and reclaim its ROM/RAM/SRAM. STEP A — set up a fresh worktree on dev tip BEFORE any other action: run `git fetch origin && git worktree add .claude/worktrees/codex-mystery-gift-removal origin/codex/cleanup-gsc-rebalance-split && cd .claude/worktrees/codex-mystery-gift-removal && cp -r ../../../rgbds-1.0.1 . && git rev-parse HEAD && git rev-parse origin/codex/cleanup-gsc-rebalance-split` — the two rev-parse outputs MUST match; if they do not, you are on a stale base and must rerun. ALL subsequent work (commits, builds, audits) happens inside this worktree on its auto-named branch — NOT directly on `codex/cleanup-gsc-rebalance-split`, NOT on any pre-existing codex branch. STEP B — read docs/codex_playbook.md §1 (bug-check methodology) and §3.1 (this task) end-to-end. STEP C — execute Step 0 (dependency audit) AND Step 1 (deletion + save-format-stable cleanup) of §3.1 in this one pass — do not stop between them. STEP D — ship one PR's worth of work to dev tip via the commit-tree pattern (§2.3) with the bug-check Findings report (including the dependency audit) in the final merge commit body.
```

**Background.** The Mystery Gift subsystem was originally a Game-Boy-link
event-distribution feature (decorations, items, trainer-house challenge).
It is unused in this hack's design and consumes ~3-5 KB of ROM plus
SRAM-mapped state. Removal is the second of three feature-cleanup
workstreams. Print/Photo (step 1/3) shipped at `2365eab1`/`8cb0fc2a`/
`4f3b058b` and is the working pattern; X items (step 3/3) is queued and
will reuse the same skeleton.

**Step 0 — dependency audit (do this FIRST, then proceed to Step 1).**
Surface the surface area. The print/photo audit at the top of
`.claude_handoffs/2026-05-09-1400-feature-cleanup-roadmap.md` is the
shape: a categorized list of every file / symbol / map script / save
field / audit reference, with one-line annotations. The audit informs
the Step 1 deletion plan and is included in the final Findings report;
do not gate on user review between Step 0 and Step 1.

Files known to exist (audit will find more):
- `engine/link/mystery_gift.asm`, `mystery_gift_2.asm`, `mystery_gift_3.asm`,
  `mystery_gift_gfx.asm`
- `gfx/mystery_gift/`
- `data/decorations/mystery_gift_decos.asm`
- `data/items/mystery_gift_items.asm`
- main menu callers in `engine/menus/main_menu.asm` (search for
  `MysteryGift` symbols)
- maps that gate the trainer-house feature (search `MYSTERY_GIFT` event
  flags)
- SRAM fields in `ram/sram.asm` matching `sMysteryGift*`
- WRAM scratch in `ram/wram.asm`
- audit references: `tools/audit/check_release_smoke.py` may guard
  mystery-gift behavior; remove guards last
- `vc/pokegold.patch.template` / `vc/pokesilver.patch.template` —
  search for any `Forbid_*` or `Mystery_*` patch refs (per §1.3)

**Step 1 — deletion order (informed by the Step 0 audit).** Same shape
as print/photo:
1. Detach all callers (main menu entries, special handlers, map scripts,
   audit references). Stub or remove. Each commit builds clean.
2. Delete engine/audio/gfx/constants files. Remove INCLUDEs from
   `main.asm`, `home.asm`, `audio.asm`, `includes.asm`. Delete VC patch
   template blocks.
3. **Save-format care:** SRAM fields require `RESERVED_UNUSED`
   placeholder pattern (the same pattern used for `TM_VOUCHER` and
   `wTMTutor*` — see `commit 67f0bb28` for the working example). The
   `SAVE_FORMAT_VERSION` does **not** bump if you preserve byte widths.
   `check_save_format_version.py` fingerprint must remain byte-identical
   to pre-change.
4. WRAM/HRAM cleanup with `ds N` placeholders if shifting non-save WRAM
   would be aesthetically bad; otherwise compact.

Per-piece commits. Build + audit between each. Single bundled merge to
dev tip via the commit-tree pattern (§2.3).

**Save-format pitfall.** The SRAM regions saved are listed in
`tools/audit/check_save_format_version.py` `WRAM_PAIRS`: `wOptions`,
`wPlayerData1/2/3`, `wCurMapData`, `wPokemonData`. If `sMysteryGift*`
fields live inside any of those regions (or the SRAM `Save` /
`Backup Save 1/2/3` sections), label-list changes shift the fingerprint
and the audit fails. Mitigation: rename the labels to
`sReservedUnusedMysteryGift*` while keeping byte widths exact, OR keep
the original label names with the bytes intact and just remove the
*readers and writers*. The label-rename approach is cleaner; the
keep-labels approach is zero-risk on fingerprint. **Default to
keep-labels** unless the user explicitly wants the rename.

**Acceptance criteria:**
- [ ] Dependency audit included in the Findings report (final merge
      commit body).
- [ ] Mystery Gift menu entry no longer appears in the main menu.
- [ ] No orphan `MysteryGift*` / `sMysteryGift*` symbols remain in source
      (grep returns zero hits except the deletion commits' contexts).
- [ ] 4-ROM build clean. `roms.sha1` bumped + verified.
- [ ] `check_save_format_version.py` PASS, fingerprint byte-identical to
      pre-change, `SAVE_FORMAT_VERSION=2` unchanged.
- [ ] `check_release_smoke.py`, `check_cross_bank_call.py`,
      `check_navigation_floor.py` PASS.
- [ ] `dev_index` regenerated; expected ROM0 / ROMX free deltas reflect
      the savings.
- [ ] VC patch templates clean.
- [ ] Bug-check Findings report (§1.1 format) in the final merge commit
      body, covering: orphan symbols / save-format / WRAM UNION
      integrity / VC patches / Music+Special ID layout / map-script
      coherence / dev_index regen / cleanup completeness.

**Scope boundaries / Do NOT:**
- Do NOT bump `SAVE_FORMAT_VERSION` without explicit user approval.
- Do NOT touch X items yet (step 3/3); they're a separate task.
- Do NOT delete items that are referenced by `data/items/mystery_gift_items.asm` if those items also exist outside Mystery Gift (audit dependencies first).
- Do NOT remove Trainer House map content unless the user explicitly approves; the room may be repurposed.
- Do NOT modify CLAUDE.md or the existing handoff docs.

---

### Task 3.2 — X items removal (cleanup roadmap step 3/3)

```
/goal remove the 7 battle-only stat-boost items (X Attack, X Defend, X Speed, X Special, X Accuracy, Dire Hit, Guard Spec) from the hack. STEP A — set up a fresh worktree on dev tip BEFORE any other action: run `git fetch origin && git worktree add .claude/worktrees/codex-x-items-removal origin/codex/cleanup-gsc-rebalance-split && cd .claude/worktrees/codex-x-items-removal && cp -r ../../../rgbds-1.0.1 . && git rev-parse HEAD && git rev-parse origin/codex/cleanup-gsc-rebalance-split` — the two rev-parse outputs MUST match; if they do not, you are on a stale base and must rerun. ALL subsequent work (commits, builds, audits) happens inside this worktree on its auto-named branch — NOT directly on `codex/cleanup-gsc-rebalance-split`, NOT on any pre-existing codex branch. STEP B — read docs/codex_playbook.md §1 (bug-check methodology) and §3.2 (this task) end-to-end. The bag is disabled in trainer battles in this hack (gate at engine/battle/core.asm:4813-4825) so these items are genuine orphans. STEP C — execute Step 0 (dependency audit) AND Step 1 (deletion) of §3.2 in this one pass — do not stop between them. STEP D — ship one PR's worth of work to dev tip via the commit-tree pattern (§2.3) with the bug-check Findings report (including the dependency audit) in the final merge commit body.
```

**Background.** The bag is SFX-rejected in trainer battles in this
hack (`engine/battle/core.asm:4813-4825`). Wild battles allow the bag
for catching, but X-item stat boosts only matter in battle. With
trainer battles disabling the bag, X items are unreachable in their
intended use; they're vestigial. Removal frees ~300-500 bytes and
simplifies the items table. Do this **after** Mystery Gift removal
(step 2/3); `data/items/mystery_gift_items.asm` references X items
and removing it first keeps the X-item cleanup smaller.

**Step 0 — dependency audit.** Same pattern as Task 3.1. Categories:
- `data/items/{attributes,names,descriptions,x_stats,marts}.asm`
- `engine/items/item_effects.asm`
- `data/battle_anims/objects.asm` (X-item battle animations)
- TM/Mart placement (any vendor lists)
- Item ID enum in `constants/item_constants.asm`
- `tools/audit/check_release_smoke.py` may verify X-item placement
- Save-format: item IDs are stored in PC item lists and bag — leave as
  `RESERVED_UNUSED` placeholder slots (same trick as `TM_VOUCHER` per
  commit `67f0bb28`).

**Step 1 — deletion order:**
1. Remove X items from all mart inventories (so they can't be bought).
2. Remove from `attributes.asm`, `names.asm`, `descriptions.asm`,
   `x_stats.asm`. Replace each ID slot with `RESERVED_UNUSED` to
   preserve item-ID layout.
3. Remove their effect handlers in `engine/items/item_effects.asm`.
4. Remove battle animations.
5. Audit cleanup (drop any release-smoke checks that referenced X items).

**Save-format pitfall.** Item IDs in PC item slots / bag slots survive
saves. Removing an ID in the middle of the enum without a
`RESERVED_UNUSED` placeholder shifts every later ID and corrupts old
saves. Use the placeholder pattern. After: any save with an X item in
inventory loads as `RESERVED_UNUSED` (an empty slot).

**Acceptance criteria:**
- [ ] Dependency audit included in the Findings report (final merge
      commit body).
- [ ] All 7 X items unreachable in marts / NPCs / overworld pickups.
- [ ] Item-ID layout unchanged: each removed item now `RESERVED_UNUSED`.
- [ ] 4-ROM build clean. `roms.sha1` bumped.
- [ ] `check_save_format_version.py` PASS, fingerprint stable.
- [ ] `check_release_smoke.py`, `check_cross_bank_call.py` PASS.
- [ ] `check_docs_navigation.py` PASS if any docs touched.
- [ ] Bug-check Findings report covering: orphan symbols / item-ID
      layout stability / save format / mart inventory coverage / battle
      animation cleanup / dev_index regen.

**Scope boundaries / Do NOT:**
- Do NOT remove the `RESERVED_UNUSED` constant or change its semantics.
- Do NOT touch held items (X items are bag-only, distinct from held
  items like Choice Band / Eviolite / Assault Vest).
- Do NOT remove items used in held-item builds even if their bag
  presence is incidental (e.g. don't remove Bright Powder if it's a
  held item somewhere).

---

### Task 3.3 — Boss AI Dragon Dance smart-attack scoring fix

```
/goal teach the boss AI scorer in engine/battle/ai/boss.asm that Dragon Dance now boosts SpA when SpA > Atk (the smart-attack mechanic). read docs/codex_playbook.md §1 (bug-check methodology) and §3.3 (this task) end-to-end before starting; the engine change is at engine/battle/effect_commands.asm BattleCommand_BestAttackUp (opcode 0xb0); the AI gap is that special-leaning Dragons (Ampharos, Kingdra) currently classify DD as a generic setup move and undervalue it. ship one PR's worth of work to dev tip with the bug-check Findings report.
```

**Background.** As of merge `418efe24` (commit `4500412a`), the Dragon
Dance move uses a smart-attack mechanism: it boosts whichever attack
stat is higher (Atk for physical Dragons, SpA for special Dragons).
Implementation is `BattleCommand_BestAttackUp` at
`engine/battle/effect_commands.asm:3996` (opcode `0xb0`), mirroring
the Outrage category-swap mechanism in
`TypePassive_GetEffectiveMoveCategory_Far`.

The boss AI in `engine/battle/ai/boss.asm` `.check_speed` /
`.check_atk_or_spd` / `.check_quiver_dance` correctly handles Agility,
Quiver Dance, and Curse. It **does not** know about the Dragon Dance
smart-attack rule. Bosses with special-leaning Dragons (Ampharos
post-Steelix-retype-era movesets, Kingdra) score DD as a generic Atk +
Spe setup and therefore undervalue it relative to setup moves like
Calm Mind that explicitly buff their special attack.

**Implementation strategy.**
1. Read `engine/battle/effect_commands.asm:3996` for
   `BattleCommand_BestAttackUp` to understand the asm-side check.
2. Read `engine/battle/ai/boss.asm` `.check_atk_or_spd` and
   `.check_speed` for the existing combo-move handling.
3. Add a Dragon Dance branch that mirrors the asm logic: if the user's
   computed SpA > computed Atk, score DD as if it were a +1 SpA / +1 Spe
   setup move; otherwise the existing +1 Atk / +1 Spe scoring stays.
4. Use existing helpers if they exist (look for `GetUserSpeed`,
   `GetUserAtk`, `GetUserSpa` in boss.asm and home/battle helpers).
5. The **boss AI Speed-cap rule** in CLAUDE.md still applies: ≥90 base
   Spe → 1 DD, 60-89 → 1 DD, ≤59 → 2 DDs. The smart-attack patch does
   not change that cap.

**Validation via the preference-lab fixture corpus.** The fixtures
`clair_kingdra_vs_dragonair_dragon_dance_mirror` and
`clair_kingdra_vs_lapras_agility_or_attack` deliberately test special-
Dragon DD scoring. After the fix, run
`python -m tools.boss_ai_debugger regress` and confirm those fixtures
either score correctly or surface as labelable disagreements.

**Acceptance criteria:**
- [ ] `engine/battle/ai/boss.asm` Dragon Dance branch reads the user's
      computed SpA vs Atk via the existing helper pattern (no
      duplication of the read).
- [ ] If SpA > Atk: scoring tracks +1 SpA + +1 Spe (mirrors Quiver
      Dance's special-leaning logic).
- [ ] If Atk >= SpA: scoring tracks +1 Atk + +1 Spe (unchanged from
      today).
- [ ] Speed-cap rule preserved (≤59 base = 2 DDs, others = 1).
- [ ] 4-ROM build clean. `roms.sha1` bumped.
- [ ] `check_release_smoke`, `check_boss_ai_no_cheat`,
      `check_boss_ai_gating`, `check_boss_ai_trace_invariants`,
      `check_boss_ai_index_lines`, `check_boss_ai_preference`,
      `check_boss_ai_policy_contract` all PASS.
- [ ] `clobber_smoke` PASS (24/24).
- [ ] `python -m tools.boss_ai_debugger regress` runs without error;
      the two named fixtures score the SpA branch correctly.
- [ ] Bug-check Findings report covering: register-clobber audit (per
      §1.3 the AG-08 trap) / Speed-cap rule / smart-attack branch
      reachability / preference-lab impact / asm-vs-AI consistency.

**Scope boundaries / Do NOT:**
- Do NOT change `BattleCommand_BestAttackUp` itself (the engine side is
  already correct).
- Do NOT touch the Speed-cap rule.
- Do NOT add hidden-info reads (no querying private stats / hidden
  moves; only public-info computed stats like Atk/SpA).
- Do NOT add new AI plan IDs (`PLAN_*` constants in
  `engine/battle/ai/boss.asm`); reuse the existing setup-attack plan.

---

### Task 3.4 — Stale-claims audit hardening (low-priority QoL)

```
/goal sweep tracked .md files for date-anchored claims with no commit cite, fix them up to clear check_no_stale_shipped_claims.py warnings. read docs/codex_playbook.md §1 (bug-check methodology) and §3.4 (this task) before starting; the audit's regex is \bcommit\s+`?[0-9a-f]{7,40}`? — must be singular "commit" not plural; commit-tree merge to dev tip after.
```

**Background.** The `check_no_stale_shipped_claims.py` audit warns
when a `.md` file has a date-anchored claim (`shipped 2026-MM-DD`,
`fixed YYYY-MM-DD`, etc.) without a commit cite on the same line. The
warnings are non-fatal but accumulate. Periodically sweeping them up
keeps the audit signal high.

**Implementation.**
1. Run `python tools/audit/check_no_stale_shipped_claims.py`.
2. For each WARN, decide:
   - If the claim is correct: add `commit \`abc1234\`` cite (singular!
     plural `commits` doesn't match the regex).
   - If the claim is stale (cited commit no longer ancestor of dev
     tip): rephrase or strip the date — the line shouldn't promise
     something that didn't ship.
3. Run the audit again — should be PASS with zero warnings.
4. One commit per file or one bundled commit; user preference.

**Acceptance criteria:**
- [ ] `check_no_stale_shipped_claims.py` exits 0 with zero warnings.
- [ ] Every newly cited commit hash resolves and is an ancestor of
      `origin/codex/cleanup-gsc-rebalance-split`.
- [ ] No content claims changed (only adding cites or stripping dates).
- [ ] `check_docs_navigation.py` PASS.

**Scope boundaries / Do NOT:**
- Do NOT remove or rewrite claims that are accurate just to silence the
  audit. Cite them.
- Do NOT add cites pointing at commits on stale side branches that
  didn't make dev tip.
- Do NOT touch CLAUDE.md (it has its own `Recent work` design — see the
  CLAUDE.md note explaining why the "shipped on YYYY-MM-DD" enumeration
  was removed).

---

## §4 Workstreams that gate on user input (DO NOT codex-task these)

These are real workstreams that need taste decisions. They are
**not** codex-runnable as-is. The user makes the call first; once the
call is made, the implementation may become a codex task. Listed here
so they don't get forgotten.

| Workstream | Why it gates | What's needed |
| --- | --- | --- |
| Lance + Clair roster overhaul | Trainer party design / mon selection is taste | User picks final rosters; agent translates to `data/trainers/parties.asm` |
| Boss AI rebuild (BOSSAI-003 v2) | Architecture choice (Option A/B/C from `docs/boss_ai_design_conversation_2026-05-05.md`) | User picks an architecture and lifts the shelf |
| BALANCE-001 weak-Pokemon queue | Per-species role/stat decisions are taste | User picks one species at a time; agent ships per-species |
| MASTERY-001 S-tier gym mastery | Reward shape + criteria are taste; save-format question | User confirms criteria + reward; agent designs save-format |
| BOSSAI-002 gym scout dossier | New game system; needs prototype + feel test | User commits to building it (currently WAIT) |
| Future fixtures beyond 50 | Corpus expansion is the user's labeling rhythm choice | User asks for more |

---

## §5 Reference

### 5.1 Verification floor (canonical, from CLAUDE.md / asm guide §6)

A green build proves "it links," not "it works." The audits are the
floor. See §1.2 above for the per-touch-area mapping.

### 5.2 The bag-disabled-in-trainer-battles fact (relevant to Task 3.2)

`engine/battle/core.asm:4813-4825` is the gate. Three lines above
`BattleMenu_Pack`. SFX-rejects the bag in trainer battles; allows it in
wild battles for catching. This is what makes X items orphans.

### 5.3 The `RESERVED_UNUSED` placeholder pattern (save-format-stable)

Used for `TM_VOUCHER` and `wTMTutor*` in commit `67f0bb28`. Pattern:
- Item ID slot: keep `RESERVED_UNUSED` in place of the removed item
  name; later items don't shift.
- Effect handler: replace with a stub that returns immediately, OR
  remove the entry from the dispatch table after the placeholder if the
  table is symbol-indexed (not fixed-offset).
- Description / name: empty string or `"@"` terminator placeholder.

Not the same as deleting the item entirely — that breaks saves.

### 5.4 The print/photo cleanup as a worked example

The closest analog to Mystery Gift / X items removal. Three commits
shipped under `2365eab1` (Phase A: detach callers; Phase B: delete
files; Phase C: WRAM/HRAM cleanup), then a follow-up merge `8cb0fc2a`
with the bug-check fix + map dialogue rewrites. Total: ~5,487 ROMX
bytes freed, ROM0 +66 free, bank `10` cleared from Tight Banks. Read
the merge bodies for the working pattern.

### 5.5 The scorer heuristic (relevant to Task 3.3 + future BOSSAI work)

`tools/boss_ai_debugger/scorer.py` is a Python heuristic over fixture
text — **not** the asm scorer. It's the design proxy. Once it
converges with the user's labels, its rules become the spec for any
asm tweaks. Do not invert this — don't tune asm to match the heuristic
without the user's labels confirming the heuristic is right.

The runner `tools/boss_ai_debugger/regression.py` reports agreement
between the heuristic and the user's pairwise labels. Today's baseline
is 40% on N=5; meaningful threshold tuning starts at N≥20.

### 5.6 What this doc isn't

- Not a substitute for `CLAUDE.md` (workflow + escalation rules).
- Not a substitute for `docs/asm_authoring_guide.md` (canonical asm
  reference).
- Not a project plan (see `docs/project_roadmap.md`).
- Not for design / taste decisions (those escalate to the user).
- Not for boss AI rebuild architecture (see
  `docs/boss_ai_design_conversation_2026-05-05.md` and
  `docs/boss_ai_rebuild_plan.md`).

If a task doesn't fit the shape in §3 (Goal / Background / Steps /
Acceptance / Scope), it's probably not codex-runnable. Either redesign
it, or escalate.
