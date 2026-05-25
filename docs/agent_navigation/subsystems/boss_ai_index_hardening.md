# Boss AI Index Hardening — Plan

Scope: improvements to `docs/agent_navigation/subsystems/boss_ai_logic.md` so it
stays accurate as the split Boss AI source under `engine/battle/ai/` evolves and so future sessions
hit fewer foot-guns when editing boss AI.

This is a planning doc, not the index itself. Don't ship gameplay changes from
here. Tick items off as they land; prune sections that turn out wrong.

## Status

- [x] **A. Commit working-tree refinement** to the index — landed in `a5e55c75`.
- [x] **B. Add a pitfalls block at the top of the index** — landed in `cbc40041`.
- [x] **C. Add an effect-table / data-ownership clarification table** — landed in `cbc40041`.
- [x] **D. Write `tools/audit/check_boss_ai_index_lines.py`** to catch line-number drift — landed in `eb529985`.
- [ ] **E. Add a scoped `ApplyMoveModel` inner-label section** (now unblocked by D).

## A. Commit working-tree refinement

Already in `git diff docs/agent_navigation/subsystems/boss_ai_logic.md`. Three
edits, all worth landing as one commit:

1. `data/battle/ai/*.asm` row in the source-files table now says those lists
   feed **vanilla** scoring (consumers in `scoring.asm`), and points at the
   inline boss-AI effect tables in the split Boss AI source. Closes a real
   misread risk: the prior phrasing implied editing those data files would
   change boss behavior directly.
2. Per-boss role-bias rows were removed after the source role-bias
   dispatcher/tables were deleted; boss identity now comes from roster,
   moves/items, tier, plans, and public battle state.
3. `BossAITierRampMap` row now names the actual file/line:
   `data/trainers/ai_tiers.asm:51`. The old index only pointed at a
   monolith-local comment.

Effort: trivial. Risk: none — docs only.

## B. Pitfalls block at top of index

Goal: the things a session needs to know *before* it touches boss AI source,
even if it never opens the spec or post-patch notes. Today these only surface
as audit-script names or as an entry in CLAUDE.md.

Sketch (insert above "Source Files At A Glance"):

```
## Pitfalls (read before editing boss AI source)

- `callfar` / `farcall` destroys caller's `hl` before the target runs. If a
  Boss AI helper takes `hl` as input, it must be called via a ROM0 homecall
  thunk (see precedent: `SpeciesItemBoost_Far`,
  `ApplyLateGenDamageStatsItemMods_Far` in `home/battle.asm`).
- Boss AI is gated by `wBossAITier != 0`. When tier is 0, the overlay must
  do nothing — vanilla AI behavior must remain bit-identical. Anything that
  fires unconditionally is a bug.
- No private-info reads outside the spent Haki branch. The AI may only read
  what the player has revealed: sent out, used a move, KO'd, or what the
  public type chart implies. `tools/audit/check_boss_ai_no_cheat.py` is the
  verification floor.
- WRAM reserve is **140 bytes hard** (`ram/wram.asm:2582`). Adding fields
  requires checking `Boss AI WRAM Reserve` in `docs/generated/dev_index.md`
  AND running `tools/audit/check_boss_ai_memory_budget.py`.
- Score saturation: scores ≥79 are treated as "blocked" by `SelectMove`
  (saturated by `DiscourageScoreHL`). Adding a further "discourage" pass
  expecting it to push a move below other already-discouraged moves will be
  a no-op. See `542ef2e2` for the saturation patch.
- Line numbers in this index are hand-maintained. After a non-trivial
  Boss AI source edit, re-grep the labels you're using before trusting them
  (or run the index audit, once it exists — item D below).
```

Effort: ~15 lines. Risk: low. Worth keeping the block tight; if it grows
past ~10 bullets, split into a "Pitfalls" section and a "Conventions" section.

## C. Effect-table / data-ownership clarification

Goal: kill the recurring confusion about which data files do what. The
working-tree edit (item A) fixes the `data/battle/ai/*.asm` row, but a
single ownership table would answer the same question more durably.

Sketch (insert near top of the "Behavior → Source Map" section, or as its
own subsection just above it):

```
### Data Ownership At A Glance

| Concern | Lives in |
| --- | --- |
| Vanilla AI effect lists (`useful_moves`, `risky_effects`, `stall_moves`, etc.) | `data/battle/ai/*.asm` (consumed by `engine/battle/ai/scoring.asm`) |
| Boss AI effect tables (`BossAIDenyKOEffects`, `BossAIStatusEffects`, `BossAIRiskyEffects`) | `engine/battle/ai/boss_policy_move.asm` |
| Per-class role/switch-threshold bias | Removed from `engine/battle/ai/boss_policy_move.asm` and `engine/battle/ai/boss_policy_switch.asm` |
| Per-trainer tier (class+id → EARLY/MID/LATE) | `BossAITierMap:1` in `data/trainers/ai_tiers.asm`; consumed by `LoadBossAITier:69` in `engine/battle/read_trainer_attributes.asm` |
| Per-class tier-weight-row override | `BossAITierRampMap:51` in `data/trainers/ai_tiers.asm` (default = `tier - 1`, set at `LoadBossAITier:97-98`) |
| Tier weight table (rows indexed by tier-weight-row) | `BossAITierWeights:5026` in `engine/battle/ai/boss_policy_move.asm` |
| Plausible-threat type table | `BossAI_PlausibleThreatTypes:1194` in `engine/battle/ai/boss_platform.asm` |
| Trainer attributes (base reward, AI flags) — separate concern, do not confuse with tier | `data/trainers/attributes.asm` (consumed at `engine/battle/read_trainer_attributes.asm:67`) |
```

Effort: ~10 lines. Risk: low. Will need a one-line follow-up if the boss-AI
inline tables ever move again.

## D. Index line-number drift audit

The biggest structural weakness today: every line number in the index is
hand-typed, and Boss AI source shifts on most edits. The pending working-tree
diff already chases drift. We will keep doing this forever unless we mechanize.

**Two options considered:**

- **Generator.** `scripts/generate_boss_ai_index.py` reads a manifest of
  (label, group, "Need" prose) and a source pattern, then renders the index.
  Rejected: the index's value is the human-curated grouping and prose. A
  manifest large enough to drive the rendering is just the index in YAML —
  same maintenance burden, harder to read.
- **Audit.** Parse every `Label:NNNN` and `\.local:NNNN` reference in the
  index, then verify each one resolves to that exact line in
  the split Boss AI source under `engine/battle/ai/` (and other named files). On drift, fail with
  a diff hint: "Index says `BossAI_GetSwitchThreshold:3486`, source says
  `:3492`. Update line." **Recommend this.**

Sketch: `tools/audit/check_boss_ai_index_lines.py`, ~80 lines.

- Walk every backtick-wrapped reference in `boss_ai_logic.md` matching
  `` `(?:\.)?[A-Za-z_][\w]*:(\d+)` `` — i.e. **single-line, label-anchored**.
  Split on a leading file path (`engine/battle/ai/...:NNN` vs bare `:NNN`
  which defaults to the split Boss AI source).
- For each, open the source file, read the line, confirm the line starts
  with the label.
- Local labels (`.foo:NNNN`) must appear within their declared parent
  routine — the parent is the nearest preceding `^[A-Z][\w]*:` label.
- **Skip range refs (`:NNN-MMM`) and comma-list refs (`:N,M,P`).** Those
  name spans or scattered instructions inside a routine, not label-anchored
  lines (e.g. `read_trainer_attributes.asm:70-138`,
  `core.asm:3954,3967`). They aren't mechanically verifiable without
  more structure. The audit should surface them as an "unaudited" count so
  a later pass can decide whether to harden range/list verification.
- Exit non-zero on any mismatch. Print a unified diff of expected vs actual
  per row.

**Where it runs.** Add to the local "run before claiming Boss AI source
work is done" set, alongside the other `tools/audit/check_boss_ai_*.py`
scripts. CI today (`.github/workflows/main.yml`) runs `make` +
`checkdiff.sh` only — no audit lane exists yet. Adding boss-AI audits to
CI is a separate workstream and out of scope for this item.

Effort: ~1 hour to write + 1 commit. Risk: low. The audit only reads files;
no source/ROM impact.

After D lands, the index can also list inner-label-heavy sections more
aggressively (item E) without compounding the maintenance debt.

## E. Scoped ApplyMoveModel inner-label section

`BossAI_ApplyMoveModel` is ~1830 lines of local labels. The index today
lists a handful of public-failure gates and hands you `rg` for the rest.

Two takes:

- **Full coverage.** List every `^\.[A-Za-z]` inside `ApplyMoveModel` with
  one-phrase summary. ~50+ entries. Heavy maintenance burden — every gate
  rename or add/remove drifts a row. Don't do this unless D lands first.
- **Scoped coverage.** List only gates that are (i) referenced by the spec
  / post-patch-notes / Haki contract, (ii) edited in the last 90 days, or
  (iii) public-failure / "would fail publicly" gates. ~15-20 entries.
  Better signal-to-noise.

**Recommend scoped, after D.** Heuristic for "should this gate be in the
index": *would a future session searching for this behavior by intent need
this label?* If yes, list it. If it's an internal helper inside one gate,
don't.

Effort: ~1 hour (mostly reading post-patch-notes for cross-references).
Risk: low after D. Without D, this risks bit-rotting silently.

## What NOT to do

- **Don't mirror `boss_ai_post_patch_notes.md` into the index.** The
  post-patch notes are the catalog of *what each gate does, with rationale*.
  The index's job is to point at where the gate lives. Duplicating content
  creates a stale-spec hazard: someone updates the post-patch notes and
  forgets the index, or vice versa, and the two start disagreeing about
  what a gate even does. The cross-reference at the bottom of the index is
  the right call.
- **Don't add a "recent changes" section** to the index. That's what
  `git log -- engine/battle/ai/` is for. A doc-side recent-changes
  list will rot inside a week.
- **Don't auto-generate the index from source comments.** Tried in spirit
  by the "generator" option above; same reason it doesn't work — the
  natural-language grouping is the value, and source comments don't
  encode it cleanly without a manifest that's just-the-index-again.

## Order of work

1. **A** (commit pending refinement). Clears the working tree.
2. **B** (pitfalls block). Standalone, low-risk.
3. **C** (data-ownership table). Standalone, low-risk.
4. **D** (audit script). Pays for itself the next time Boss AI source shifts.
5. **E** (scoped `ApplyMoveModel` labels). Only after D.

A–C can be one commit if the diffs stay small. D is its own commit. E is
its own commit.

## Verification

- For A–C, E: docs only. No build/audit needed beyond `make compare` if
  paranoid.
- For D: run the new audit against the current index, confirm it passes
  with no drift; then deliberately corrupt one line number and confirm the
  audit fails with the expected diff hint. Add it to the local audit set
  alongside the other `check_boss_ai_*.py` scripts (no CI lane today).
