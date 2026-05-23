# Codex Task — Boss AI ROM Expansion: 14 Empty Banks → Smarter Bosses

**Status:** v0 spec, Cole-approved 2026-05-23 via /codex-pgoal Step 0 AskUserQuestion intake.
**Pairing:** Claude (prompter, ~30%) + Codex (implementer, ~70%) under mutual approval, with the structural defenses below promoted to acceptance criteria (not advisory).
**Artifact:** `claude/boss-ai-rom-expansion` branch off `codex/cleanup-gsc-rebalance-split`.
**Roadmap home:** this file — canonical contract, both LLMs read it, update it before drift.
**Handoff log:** `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl`.

## Goal

Use the ~14 empty ROM banks Cole has on hand to make the boss AI **structurally smarter** — better play under the existing no-hidden-info rule, not modernization or new mechanics. Both LLMs web-search and brainstorm together to identify the highest-value uses of that ROM budget; co-author an implementation phasing section in this roadmap; then ship as many phases as fit before the pgoal budget runs out.

Cole's exact ask (2026-05-23):
> *"both you and codex use web search and brain storm ideas together. come up with how to use all our extra rom to make the boss ai even smarter and then build a roadmap and then implement"*

The "smarter" axis is **open** — Cole did not pin it to one dimension. The brainstorm is responsible for surfacing axes (multi-turn planning, switch heuristics, prep-phase modeling, route-budget reasoning, etc.) and ranking them by ROM-cost vs play-impact.

## North Star constraint (load-bearing — non-negotiable)

From [CLAUDE.md](../CLAUDE.md):
> *"Bosses win without cheating. No hidden-info reads (unrevealed party, unrevealed moves, private stats, current-turn input, RNG manipulation). Public info only: seen species, revealed moves, public TM/level-up learnability. Haki = explicitly authored once-per-battle exceptions only."*

Every brainstorm idea must pass this filter. If an idea NEEDS hidden info, either redesign around public info or drop it. Authored Haki is the only carve-out and is per-boss / per-battle.

## Locked decisions (from AskUserQuestion intake)

| Question | Answer | Implication |
|---|---|---|
| Direction of "smarter" | Open brainstorm | Both LLMs propose freely across axes; no axis pre-locked. Brainstorm phase ranks them. |
| Save-format / RAM policy | ROM-only + unused WRAMX banks 2–7 (Claude's recommendation) | No SRAM edits, no existing-WRAM-layout edits. New state goes in WRAMX banks 2–7 (per `reference_wram_relief_roadmap` those banks are empty). No `SAVE_FORMAT_VERSION` bump. |
| Branch | New off main | `claude/boss-ai-rom-expansion` off `codex/cleanup-gsc-rebalance-split`. |
| Codex chat | New chat (not "Pair with Claude" which is on the debugger work) | TBD by chat policy in Step 3 — Claude opens a fresh chat for this pgoal. |

## Phase A — Brainstorm and co-author implementation phasing

**Phase A is itself an implementation phase**: it produces the locked plan that Phases B, C, … will implement.

### A.1 — Research split (Codex + Claude, parallel)

Both LLMs do web search **plus** repo reading and append findings as `slice_update` rows with `confidence` labels. Topic split is symmetric so neither LLM does all the framing:

**Claude lane (analysis-leaning):**
- Existing boss AI architecture: `engine/battle/ai/boss.asm`, `engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_policy_switch.asm`, `data/trainers/ai_tiers.asm`. Where are the current limits? What does the AI fail at right now? What known-stupid behaviors does it have?
- ROM bank inventory: `docs/generated/dev_index.md` "Tight Banks" → what is the actual free space and where? Are the 14 free banks contiguous or scattered? What size tables can each hold?
- WRAMX bank 2–7 availability: verify per `reference_wram_relief_roadmap` and current `ram/wram.asm` source that those banks are actually free. How many bytes per bank? What state size can we realistically afford?
- Public-info corpus: enumerate the categories of public info boss AI is allowed to read (seen species, revealed moves, TM learnability, public stat tiers). Anything else? Map to existing helpers in `engine/battle/ai/`.

**Codex lane (synthesis-leaning):**
- Gen 2 / Gen 1 AI research: what specifically did vanilla Crystal/Gold/Silver AI do badly? What has the speedrun / TAS / glitch community documented about AI exploits we should patch?
- Modern Pokemon AI literature: showdown bot heuristics, MCTS for Pokemon, opponent-modeling techniques. Which translate to public-info-only? Which assume the bot can read the opponent's hand?
- Heuristic AI design patterns in ROM-constrained systems: utility functions, switch trees, decision tables, hand-authored decision graphs. Per-bank cost estimates for each.
- Prior boss-AI work in this repo: `git log --grep=boss` and `audit/` for what's been tried before, what stuck, what got reverted.

### A.2 — Brainstorm convergence

Both LLMs post 5–10 candidate "smartness levers" each as handoff-log slice_updates. Each candidate states:
- **What the boss currently does** (cite a function or behavior).
- **What "smarter" looks like** (concrete behavior change, not a vague theme).
- **Public-info-only check** (cite the inputs it uses).
- **ROM cost estimate** (banks / kilobytes, rough).
- **WRAMX cost estimate** (bytes of new state, if any).
- **Play-impact estimate** (which fights does this change — gym leader N, all bosses, only late-game).

Then both LLMs review and rank. Adversarial review: assume the candidate is bad, prove it isn't.

### A.3 — Lock the phasing

The output of Phase A is a new section in this file: **"## Implementation phases (locked)"** with phases ordered by impact-per-ROM-byte, each phase containing:
- Goal sentence.
- Public-info filter check.
- Files to touch (write set).
- Acceptance criterion (one mechanical test or audit).
- ROM/WRAMX cost estimate.

Both LLMs `slice_review` the locked phasing before Phase B starts.

## In scope (v1)

1. This file (`docs/boss_ai_rom_expansion_2026-05-23_codex_task.md`) committed with Phase A outputs filled in.
2. `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` populated with the full brainstorm + implementation slice history.
3. Ship as many of the locked phases as fit in the pgoal budget (240 min, 50 iter, 500 tool calls; can request more from Cole on hit).
4. ROM remains buildable (`make pokegold.gbc` exits 0) and release-smoke remains green throughout.
5. No save-format change: `SAVE_FORMAT_VERSION` unchanged; no SRAM or existing-WRAM-layout edits.

## Out of scope (deferred)

- Anything that requires hidden info to work (drops or redesigns at A.2 review).
- Save-format-breaking changes (requires explicit escalation per CLAUDE.md).
- WRAMX bank 0–1 edits (existing reserves; out of scope for this work).
- Per-Pokemon balance tweaks (separate workstream — `docs/balance_intent.md`).
- Trainer roster redesigns (separate workstream — `docs/buff_backlog.md`).
- Modernization features that change feel (per the First-Playthrough Promise).
- New Pokemon mechanics (Abilities, per-move phys/special split, etc — see `docs/agent_navigation/gen2_vs_modern_mechanics.md`).

## Acceptance criteria

Mirrored into `pgoal acceptance init` JSON. All must pass for `pgoal verify --run --record`:

1. **`phase_a_locked`** — this roadmap file contains a "## Implementation phases (locked)" section signed by both LLMs (handoff log has `mutual_done` rows for `P0_brainstorm` and `P0_phasing_locked`).
2. **`structural_defense_v7_strict`** — `python tools/audit/check_two_llm_handoff_log.py --strict --store audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` exits 0. Strict mode means timestamp-order drift is also an error; any phase without mutual sign-off fails.
3. **`no_solo_commits`** — every commit on `claude/boss-ai-rom-expansion` after this roadmap-commit has a paired `slice_review` row from the *other* LLM in the handoff log (validated by `tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py` — to be written in Phase A.1 by Claude as part of structural-defense tooling).
4. **`build_green`** — `make pokegold.gbc` exits 0 from a clean state.
5. **`release_smoke_green`** — `python tools/audit/check_release_smoke.py` exits 0.
6. **`farcall_audits_green`** — both `check_farcall_hl_clobber.py` and `check_farcall_a_clobber.py` exit 0.
7. **`save_format_unchanged`** — `python tools/audit/check_save_format_version.py` exits 0 AND no diff against main on `ram/sram.asm`, `ram/wram.asm` bank 0/1 sections, or any `constants/SAVE_FORMAT_VERSION` define.
8. **`debugger_audit_green`** — `python -m tools.debugger audit` exits 0 (boss-AI inference banks must be inspectable by the unified debugger).

## Structural defenses (acceptance, not advisory)

Per `feedback_codex_pgoal_structural_defenses.md`. Cole flagged on 2026-05-23 the recurring failure mode where /codex-pgoal Stop-hook reminders pull Claude into solo-implementation mode and Codex drifts from hard gate → advisory → absent.

1. **v7 strict in acceptance** (above as `structural_defense_v7_strict`). Any phase missing Codex slice_review = goal failure.
2. **No solo implementation commits** (above as `no_solo_commits`). Verified by the to-be-written `check_no_solo_commits_*.py` audit, which greps the handoff log for `slice_review` rows matching each commit on this branch.
3. **Screenshot Codex first on every pgoal continuation.** Idle-waiting-on-me → review/send work. Observably-coding → poll/note only, never start parallel solo lanes. (Behavioral, not test-enforced; documented as a Stop condition.)
4. **Brainstorm split up front** (Phase A.1 above). Codex posts findings as handoff rows BEFORE Claude drafts further roadmap sections.
5. **Co-authored roadmap** (this very file). Phase A produces sections that Codex commits, not just Claude.

## Approach preference

Use today's debrief operational protocol verbatim (per `docs/llm_pairing_rules.md`):

- **Files-first split.** Declare write-set, safe-set, collision-risk in every `ack_start`.
- **Confidence labels.** `repo-proven` (with at least one `path:line` citation), `memory-derived`, or `judgment`. Stated explicitly on every load-bearing claim.
- **Adversarial review.** Default review stance: assume the draft has a bug or a hidden-info leak, prove it doesn't.
- **2-commits-or-1-hour cadence.** Surface direction at that cadence regardless of momentum.
- **Mutual approval before mutual_done.** Both LLMs must sign off.

## Edge cases

- **Idea uses hidden info.** Drop or redesign at A.2. Don't ship it as Haki to dodge the rule.
- **Idea balloons ROM cost past the budget.** Reduce scope, defer to v2, or pick a smaller idea.
- **WRAMX bank 2–7 turns out to be partially used.** Reverify before assuming free; back off to ROM-only for affected ideas.
- **Idea breaks `clobber_smoke` / damage debugger.** Damage-side regressions are the most dangerous failure class in this repo (per `feedback_ag_nn_clobber_class.md`); the verification floor includes the debugger audit for that reason.
- **Idea changes boss AI behavior in non-deterministic ways.** Document the RNG sources and keep behavior reproducible from save state seeds (per `reference_damage_debugger`).
- **Phase A produces too few ideas.** Re-run web search with different framings. Stop condition triggers only after 2 brainstorm passes both yield <5 candidates each.

## Verification floor

Before declaring any phase done:

1. Build (`make pokegold.gbc`) green.
2. Relevant audits green (release-smoke always; farcall_hl, farcall_a if asm touched; damage_debugger clobber_smoke if battle code touched; save_format_version always).
3. `docs/generated/dev_index.md` regenerated (`python scripts/generate_dev_index.py --rom pokegold`).
4. If balance tables touched: regenerate `docs/generated/balance_audit.md`.
5. Both LLMs `slice_review` with status=slice_accepted.
6. Append `mutual_done` row (or rely on slice_accepted from non-primary, per the two-LLM audit semantics).

Before declaring the **whole pgoal** done:

1. All 8 acceptance criteria pass via `pgoal verify --run --record`.
2. `python tools/audit/check_two_llm_handoff_log.py --strict --store audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` green.
3. Manual playtest sign-off from Cole on at least one shipped phase (taste escalation).

## Branching / commits

- Work on `claude/boss-ai-rom-expansion` (already created off `codex/cleanup-gsc-rebalance-split`).
- **No commit without a paired slice_review row** — per defense #2. Codex's revisions-only commits may follow the commit-then-review rule (`feedback_codex_commit_then_review_rule`).
- Push to `claude/boss-ai-rom-expansion` is allowed. Pushing to `codex/cleanup-gsc-rebalance-split` (main) is **not** without Cole's explicit ask. Force-push to main is forbidden.
- PR creation: not without Cole's explicit ask. Merging to master is a release event (escalation per CLAUDE.md).

## Stop conditions

Pause and surface (or escalate to Cole), do not push through, if:

- `pgoal verify --run` fails 3 times in a row with the same root cause.
- Two consecutive Claude-authored commits land with no Codex `slice_review` row.
- The spec needs a load-bearing change Cole hasn't approved (especially any save-format change, Hidden-info-rule carve-out beyond Haki, or trainer roster change).
- ROM expansion forces a bank-budget overflow that can't be resolved without an idea downgrade.
- Both LLMs can't reach mutual approval after two adversarial-review passes on the same slice.
- Build red and the fix isn't obvious within one slice.
- `clobber_smoke` regressions: any damage-debugger FAIL.

## Disagreement resolution

**Primary rule (Cole 2026-05-23):** Claude + Codex agreement IS Cole's decision. Do not pause for his feedback when the pair can decide. See `feedback_claude_codex_agreement_is_cole_decision.md`.

- **Tiebreak:** Claude + Codex deliberate. Settle the question with adversarial-review passes (default: 2 passes minimum before declaring deadlock).
- **Codex-defaults-win:** code style inside Codex's write set, idiomatic asm patterns, RGBDS quirk handling.
- **Claude-defaults-win:** spec interpretation, when to surface to Cole, when to mark a phase done, structural-defense enforcement.

**Escalate to Cole** only on:
1. **Mutual deadlock** after ≥2 adversarial-review passes — the pair genuinely can't converge.
2. **CLAUDE.md escalation-list items:** gameplay taste, playtest, save-format change, master merge, destructive irreversible.
3. **Directive conflicts** where two Cole-stated operating directives conflict.

**Escalation channel:**
- Cole reachable via chat (in-session): default to chat.
- Cole away: ntfy topic `The-CCC-Boys` per `reference_ntfy_async_cole_channel.md`. Bar matches the 3 escalate-to-Cole conditions above.

**Anti-patterns** (do NOT do these):
- "Want me to X first?" → just do it.
- "Sound right? anything to add?" → strip; ship and surface result.
- Asking Cole to choose between two approaches the pair could agree on.
- Pausing pgoal iterations for "confirmation" of pair-verified work.

## Time / scope budget

- Standard pgoal duration (240 min, 50 iter, 500 tool calls).
- Phase A budget cap: ~30 minutes / 5 iterations. If Phase A is still open at iter 10, the brainstorm is degenerate — surface to Cole.
- Per-implementation-phase budget: aim for ≤3 iterations per shipped phase.
- If at iter 25 we've shipped 0 implementation phases, surface the slowdown to Cole rather than burn the remaining budget.

## Async channel

- Cole reachable via chat: assume yes, but he's at work. Interrupt only on the 3 escalate-to-Cole conditions in Disagreement resolution. The pair owns all other in-scope decisions.
- Cole reachable via ntfy (`The-CCC-Boys`): yes — same 3-condition bar.

## Pgoal arming plan

```bash
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" set \
  --objective "Use the ~14 empty ROM banks to make the boss AI structurally smarter under the no-hidden-info rule. Brainstorm with Codex via the Phase A lanes in docs/boss_ai_rom_expansion_2026-05-23_codex_task.md; co-author the Implementation phases section; ship as many phases as fit in budget." \
  --phase brainstorm_then_implement \
  --criteria "<derived from Acceptance criteria above>" \
  --constraints "<see Structural defenses and Stop conditions above>" \
  --verify "<see Verification floor above>" \
  --max-iterations 50 \
  --max-wall-minutes 240 \
  --max-tool-calls 500 \
  --max-no-progress 3 \
  --max-compactions 3 \
  --no-auto-discover \
  --assume-defaults --replace --clarified
```

## Provenance policy

- `docs/boss_ai_rom_expansion_2026-05-23_codex_task.md` (this file): **committed**.
- `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl`: **committed** at completion (and periodic snapshots during the run).
- `tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py`: **committed** as part of structural-defense tooling.
- Implementation phase deliverables (asm, data, tooling): **committed** under the paired slice rule.
- Brainstorm research notes from Codex/Claude: **committed** inline in this file (under the "## Research findings" subsections of Phase A).
- Scratch experiments: `.local/`, **not committed**.

## Background memory to read before pairing

Both LLMs must read before the first slice (Codex `git pull` + read directly):

- [docs/llm_pairing_rules.md](llm_pairing_rules.md) — committed pairing rules.
- [CLAUDE.md](../CLAUDE.md) — project config, North Star, no-hidden-info rule, ASM gotchas.
- [docs/asm_authoring_guide.md](asm_authoring_guide.md) §0 (load-bearing rules), §3 (common mistakes), §6 (verification floor).
- [docs/agent_navigation/gen2_vs_modern_mechanics.md](agent_navigation/gen2_vs_modern_mechanics.md) — the Gen 2 vs modern mechanics filter.
- [docs/project_context.md](project_context.md) — First-Playthrough Promise full statement.
- `docs/generated/dev_index.md` — ROM bank inventory, free space, boss AI anchors.
- Memory: `feedback_codex_pgoal_structural_defenses.md`, `feedback_autonomous_loop_drops_codex_pairing.md`, `reference_llm_pairing_rules.md`.

## Codex task block

```
---CODEX-TASK---
**Goal:** Use the ~14 empty ROM banks to make the boss AI structurally smarter under the no-hidden-info rule. Brainstorm together (both web-search), co-author the implementation phasing, then ship.

**Roadmap (canonical contract — read first, work from it):**
`@docs/boss_ai_rom_expansion_2026-05-23_codex_task.md`

The roadmap covers Phase A (brainstorm split, convergence, locked phasing), scope, acceptance criteria, structural defenses (5 promoted to acceptance — including v7 strict and no-solo-commits), edge cases, verification floor, branch/commit policy, stop conditions, disagreement resolution, and the pgoal arming plan.

**Branch:** `claude/boss-ai-rom-expansion` (off `codex/cleanup-gsc-rebalance-split`). Already checked out.
**Handoff log:** `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl`.

**Pairing protocol:** today's debrief rules verbatim. Files-first split. Confidence labels (`repo-proven` with path:line citation / `memory-derived` / `judgment`). Mutual approval before any commit. Silence=unknown not approval. Hard-stop reflex on collision risk. 2-commits-or-1-hour cadence. **No solo implementation commits** — defense #2 is enforced by the to-be-written `check_no_solo_commits_*.py` audit.

**Phase A research lanes:**
- You (Codex): synthesis-leaning — Gen 1/2 AI literature, modern Pokemon AI heuristics, ROM-constrained AI design patterns, prior boss-AI work in this repo (`git log --grep=boss`).
- Me (Claude): analysis-leaning — current boss AI architecture and limits, ROM bank inventory (`docs/generated/dev_index.md`), WRAMX bank 2–7 availability verification, public-info corpus enumeration.

**First-slice proposal:** Codex `ack_start P0_brainstorm_codex_research_lane` and post 5–10 candidate smartness levers as a single `slice_update` row. I'll do the same on the Claude lane in parallel. After both lanes' findings are in, we converge in Phase A.2.

Ready when you are. Please confirm the read of the roadmap and post your first `ack_start` row when you're set up.
---END-TASK---
```

## Implementation phases (locked)

**STATUS:** locked 2026-05-23 by mutual Claude+Codex slice_accepted rows 5+6 in `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl`. P0.5 split into a/b/c per Codex convergence note (P0.5b is paired-review work, not setup-allowlist). P4 softmax temperature is kernel-driven per the convergence note (load-bearing in phase definition).

**Phase ordering rationale**: Phase A.0.5 first (unblocks v7 strict + WRAMX-2 dependents); P1 next (per-leader kernels become the scoring substrate every later phase reads); P2 supplies the KO-band data layer; P3 cleans up scattered effect logic; P4 layers reply-buckets on top of P1's kernels; P5 introduces observation memory; P6 adds role classification; P7 puts it all into named plan templates.

**Lever-to-phase mapping reference** (for cross-checking with handoff log rows 2 and 4):

| Phase | Codex levers | Claude levers | Primary author |
| --- | --- | --- | --- |
| P0.5a | — | (drift restore work) | Claude |
| P0.5b | — | (WRAMX plumbing) | Both (paired) |
| P0.5c | — | Claude #2 (revised) | Claude |
| P1 | Codex #7 | Claude #1 | Both (paired) |
| P2 | Codex #1 | Claude #3 | Both (paired) |
| P3 | Codex #5 | — | Codex |
| P4 | Codex #6 | (reads P1 kernels) | Codex |
| P5 | Codex #3, #8 | Claude #4 | Both (paired cluster) |
| P6 | Codex #4 | — | Codex |
| P7 | Codex #2 | — | Codex |
| v2 | — | Claude #5, #6 | (deferred) |

---

### P0.5a — Drift restore (setup-allowlist)

- **Goal**: cherry-pick `docs/llm_pairing_rules.md` from commit `0d3fbf8c` and `tools/audit/check_two_llm_handoff_log.py` from commit `da2f6644` onto this branch. Add both to the no_solo_commits `SETUP_ALLOWLIST` so subsequent edits to those files remain Claude-solo-sanctioned. v7 strict acceptance criterion becomes runnable.
- **Public-info-only**: not gameplay; tooling-only.
- **Files to touch (write set)**: `docs/llm_pairing_rules.md` (new), `tools/audit/check_two_llm_handoff_log.py` (new), `tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py` (allowlist update).
- **Acceptance criterion**: `python tools/audit/check_two_llm_handoff_log.py --strict --store audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` exits 0; `python tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py` exits 0.
- **ROM cost**: 0.
- **WRAMX cost**: 0.
- **Play-impact**: none. Pure setup.
- **Author**: Claude. Setup-allowlist commit acceptable; Codex slice_review post-commit acknowledged via paired row.

### P0.5b — WRAMX bank-2 plumbing (paired)

- **Goal**: declare the first WRAMX bank-2 `SECTION` in `ram/wram.asm` with explicit `BANK[02]` pin; extend the boss-AI bank-switch idiom (`hROMBank` shadow save/restore) to handle bank-2 access; verify zero regression against existing bank-1 reserve (BOSS_AI_TRACE 9-byte floor stays intact); add a `tools/audit/check_wramx_bank2_declaration.py` audit that confirms the SECTION exists and is sized within budget.
- **Public-info-only**: not gameplay; infrastructure for future levers.
- **Files to touch (write set)**: `ram/wram.asm` (new SECTION), boss bank-switch helper if needed, `tools/audit/check_wramx_bank2_declaration.py` (new audit).
- **Acceptance criterion**: build green; `make compare` may diverge (new SECTION is fine, no parity claim); `dev_index.md` regenerated showing WRAMX bank 02 used bytes > 0; existing Boss AI WRAM Reserve table still shows ≥9 trace bytes free in bank 1.
- **ROM cost**: <100 bytes (helper).
- **WRAMX cost**: ≥1 byte placeholder in bank 2 (to make the SECTION non-empty); future levers grow this.
- **Play-impact**: none directly; unblocks P5 + parts of P1/P7.
- **Author**: paired. **Not setup-allowlist work** per Codex convergence note row 6 — this is real boss-AI infrastructure. Requires Codex slice_review before commit OR commit-then-rereview per `feedback_codex_commit_then_review_rule` (Codex's choice).

### P0.5c — Haki-audit tool stub (tools-only)

- **Goal**: extend `tools/boss_ai_debugger/` with a `haki-coverage` subcommand that surfaces per-leader Oracle entries (which leaders have Haki, ace species, iconic move on ace, ParsePlayerAction read source line). No data structure changes; tool reads existing trainer party data + `docs/boss_ai_spec.md` roster table + asm citations.
- **Public-info-only**: not gameplay; dev tool only.
- **Files to touch (write set)**: `tools/boss_ai_debugger/haki_coverage.py` (new), `tools/boss_ai_debugger/__main__.py` (subcommand wiring), `tools/audit/check_haki_coverage_audit.py` (new audit that runs `haki-coverage --self-test` and verifies known leaders are listed).
- **Acceptance criterion**: `python -m tools.boss_ai_debugger haki-coverage --self-test` exits 0 and reports all 10 Haki leaders (Morty, Chuck, Jasmine, Pryce, Clair, Will, Koga, Bruno, Karen, Lance — per `docs/boss_ai_spec.md:66-74`; Red TBD).
- **ROM cost**: 0.
- **WRAMX cost**: 0.
- **Play-impact**: none directly; developer iteration velocity on later levers.
- **Author**: Claude. tools/ change, not setup-allowlist; paired Codex slice_review before commit OR commit-then-rereview.

### P1 — Per-leader personality kernels (paired)

- **Goal**: externalize scoring-weight vectors + plan-template biases + softmax-temperature into ROMX kernel data, keyed by trainer ID, with tier-default fallback. At battle start, load the kernel into existing `wBossAI*` scratch (or new WRAMX-2 if richer). Per-leader curated personalities — Falkner risk-aversive flying-pivot, Whitney stubborn-Miltank, Jasmine Steelix-protective, Lance chain-Dragonite-pressure, Karen mixed-Dark, Red elite-balanced. Adds role-aware boss party preservation table (Codex #7) keyed by same trainer ID — same data file. Includes per-leader softmax temperature byte (consumed by P4) so each leader has curated sharpness.
- **Public-info-only**: kernels are compile-time constants per leader, weighting only public-info inputs. Boss own party introspection is legal. No hidden-info reads.
- **Files to touch (write set)**: new `data/boss_ai/personality_kernels.asm` + per-leader includes; `engine/battle/ai/boss_platform.asm` (kernel load at battle start); existing `wBossAI*` scratch or new WRAMX-2 SECTION.
- **Acceptance criterion**: ROM builds; `tools/boss_ai_debugger` shows different kernel selected per major-leader trainer ID; existing release-smoke + farcall audits stay green; new audit `tools/audit/check_personality_kernel_coverage.py` confirms every major-leader trainer has a kernel entry (tier-default fallback for minor trainers).
- **ROM cost**: 1-2 banks (one of the 14 empty banks; data-driven so fits comfortably).
- **WRAMX cost**: 0-32 bytes (scratch in bank 1 if kernel state fits; otherwise small WRAMX-2 segment).
- **Play-impact**: very high. Serves First-Playthrough Promise directly — every major fight feels like its trainer thought through that match.
- **Author**: paired. Codex primary on per-trainer kernel data; Claude primary on kernel-load + scoring-weight plumbing.

### P2 — KO-band oracle + matchup precompute (paired)

- **Goal**: build ROMX tables and routines estimating public damage bands, 2HKO/3HKO windows, survival bands, deny-KO odds from visible inputs (Codex #1). Pair with compile-time per-boss-roster type-matchup tables (Claude #3): defensive matchup vector per slot vs 17 types, offensive coverage vector per slot. Replace per-turn type-chart loops with table lookups.
- **Public-info-only**: inputs are visible species/level/typing/HP/status/stages, boss-known own moves/items, revealed player moves, observed damage calibration. Player-side stat uncertainty becomes coarse banding only; never reads private stats.
- **Files to touch (write set)**: new `engine/battle/ai/ko_band_oracle.asm` + `data/boss_ai/matchup_tables.asm`; per-leader matchup precompute generated at build time (script in `tools/build_boss_matchup_tables.py`); call sites in `engine/battle/ai/boss_policy_move.asm` `BossAI_CurrentEnemyMoveHasKOPressure` and `BossAI_CurrentEnemyMovePressureScore`.
- **Acceptance criterion**: ROM builds; new `tools/audit/check_ko_band_oracle_self_test.py` runs an oracle self-test against known scenarios and matches expected bands; release-smoke + farcall audits stay green.
- **ROM cost**: 2-3 banks total (1-2 for oracle + 0.5-1 for matchup tables; plus type-passive and held-item public modifiers if tableized).
- **WRAMX cost**: 0 if recomputed per candidate; 8-16 bytes scratch in P0.5b-declared WRAMX-2 if caching.
- **Play-impact**: very high. Improves KO, deny-KO, recovery, setup-affordability, sacrifice-cash-out, switch-confidence across every boss without omniscience.
- **Author**: paired. Codex primary on oracle helpers + KO-band math; Claude primary on per-trainer matchup table build script + integration.

### P3 — Revealed-effect interaction matrix (Codex)

- **Goal**: move the growing bespoke revealed-effect interactions (Protect/Recovery/Encore/Selfdestruct/SleepPreempt/Destiny-Bond/Counter-Mirror-Coat/Disable/Mean-Look/Perish/charging-rampage/phaze-hazard) into ROMX data keyed by revealed player effect, boss candidate effect/category, tier, public speed/HP gates, board flags.
- **Public-info-only**: only exact active revealed moves in `wPlayerUsedMoves` / per-species public memory, public last move, visible HP/status/boosts, public speed predicate, boss candidate move data. No plausible hidden move becomes an exact revealed-effect trigger.
- **Files to touch (write set)**: new `data/boss_ai/revealed_effect_matrix.asm`; refactor of bespoke helpers around `engine/battle/ai/boss_policy_move.asm:1392-1605` into table-driven dispatch.
- **Acceptance criterion**: ROM builds; existing boss-AI fixture tests in `tools/boss_ai_debugger/` continue to pass; release-smoke + farcall audits green; new audit `tools/audit/check_revealed_effect_matrix_coverage.py` confirms key effects represented.
- **ROM cost**: 1 bank (one of the 14 empty banks; replaces growth pressure on tight bank 0e).
- **WRAMX cost**: 0.
- **Play-impact**: high and structurally safe. Expands tactical coverage while reducing scattered bespoke ASM drift and making audits easier.
- **Author**: Codex primary; Claude reviews + may pair on the refactor sites.

### P4 — Top-K reply-bucket payoff with kernel-driven temperature (Codex)

- **Goal**: for late bosses only (tier 2-3), evaluate top 3-4 legal boss actions against three public reply buckets (stay/attack, preserve/switch, greed/setup). Use public payoff tables and **a controlled softmax whose temperature is per-leader, supplied by the P1 personality kernel** (Falkner sharper temp → more deterministic; Karen smoother temp → more mixed). Avoid pure determinism (memorization-exploitable) and pure randomness (no skill expression).
- **Public-info-only**: reply buckets read public HP/status/boosts, revealed/plausible masks, observed tendencies, seen species, prior turns. Never the current selected button, never private party/moves/items.
- **Files to touch (write set)**: new `engine/battle/ai/reply_bucket_payoff.asm`; references P1 kernel for temperature byte; new `data/boss_ai/reply_bucket_payoff_tables.asm`.
- **Acceptance criterion**: ROM builds; `tools/boss_ai_debugger` shows non-deterministic action distribution on near-tie scenarios matching the per-leader temperature; release-smoke + farcall audits green.
- **ROM cost**: 1-2 banks if payoff tables include plan/personality/tier variants; 0.5 bank minimal matrix over existing scores.
- **WRAMX cost**: 0-12 bytes scratch for 4×3 scores; no persistent state.
- **Play-impact**: high for champion/endgame and near-tie cases, medium early. ROM-friendly adaptation of modern MCTS/minimax lessons under hardware constraints.
- **Author**: Codex primary; Claude reviews softmax-distribution choice + integration with P1 kernels.

### P5 — Observation log + tendency counters + speed/damage calibration (paired cluster)

- **Goal**: cluster slice — single WRAMX-2 buffer (16-32 bytes) holding last ~6 turns of structured public observations (turn_no, actor, action_class, observed_damage_band, observed_speed_relation). Codex #3 (tendency counters: switches under threat, attacks into bad public matchup, protects/recovers repeatedly, greedy setup under pressure, status fishing, low-HP sack acceptance) reads from this buffer for counter updates. Codex #8 (calibration) reads from this buffer for KO-band refinement against P2's oracle.
- **Public-info-only**: all entries are public post-resolution facts. No current-turn input. No hidden stat reads. Updates happen at the same next-turn boundary as pending-switch observations.
- **Files to touch (write set)**: new `engine/battle/ai/observation_log.asm` (buffer append + consult helpers); new `data/boss_ai/tendency_counter_weights.asm`; refactor of `BossAI_PredictPlayerSwitch` (engine/battle/ai/boss_policy_move.asm:3531) to consult counters; new WRAMX-2 buffer declaration in P0.5b-prepared section.
- **Acceptance criterion**: ROM builds; new `tools/audit/check_observation_log_invariants.py` confirms append-only, public-info-only, bounded buffer; tendency counter updates traceable via `tools/boss_ai_debugger`; release-smoke + farcall audits green.
- **ROM cost**: ~1.5 banks total (0.5 buffer + 0.5 tendency + 0.5 calibration).
- **WRAMX cost**: 16-32 bytes in P0.5b-declared bank 2 (depends on counter width).
- **Play-impact**: high after turn 3. Makes rematches, Elite Four, Champion, Red feel adaptive without deterministic counterpicking.
- **Author**: paired cluster. Claude primary on observation log buffer + invariants; Codex primary on tendency counter math + calibration consumer.

### P6 — Role/package classifier (Codex)

- **Goal**: classify each seen player species into coarse public packages (spinner, phazer, setup-sweeper, recovery-wall, priority-revenge, sleep/status-pressure, trap/perish-line, physical/special wallbreaker). Use package bits for preservation switches, plan templates, and route valuation.
- **Public-info-only**: inputs are visible species, public learnability, revealed moves, observed behavior, evidence. Output remains probabilistic/package-level — cannot imply exact hidden moves or four-slot sets.
- **Files to touch (write set)**: new `data/boss_ai/role_package_classifier.asm`; consumer hooks in switch-confidence path (`engine/battle/ai/boss_policy_switch.asm`).
- **Acceptance criterion**: ROM builds; `tools/boss_ai_debugger` correctly tags representative species; release-smoke + farcall audits green.
- **ROM cost**: 1-2 banks for species/effect package tables + classifier (less if table only covers boss-relevant species).
- **WRAMX cost**: 0 if recomputed for active/seen candidates; 6-12 bytes cache after observation-log lands.
- **Play-impact**: high for veteran counterplay. Bosses stop treating every public type threat identically and start respecting roles (spinner, setup, revenge, wall) without cheating.
- **Author**: Codex primary; Claude reviews.

### P7 — Coach-plan template engine, minimal-first (Codex)

- **Goal**: compact ROMX table of public-gated plan templates. Minimal-first scope of 4 templates: `attack_now`, `setup_once_then_attack`, `pressure_recover_then_lock`, `cashout_sacrifice`. Plan identity supplies action-sequence bias and stop conditions rather than a literal tree. Later slices expand if measurement supports it (full set: `sleep_then_setup`, `scout_probe_then_commit`, `switch_preserve_then_rescore`, `hazard_phaze_route`).
- **Public-info-only**: templates inspect legal boss actions, boss roster, visible field/HP/status/boosts, seen species, revealed moves, public plausible masks, observed switch history. Must keep fixture-style separation of revealed/plausible/impossible/unknown.
- **Files to touch (write set)**: new `data/boss_ai/coach_plan_templates.asm`; small dispatcher in `engine/battle/ai/boss_policy_move.asm` augmenting existing `BossAI_ApplyPlanMoveBias` at :4702 + `BossAI_SelectPlanIfNeeded`.
- **Acceptance criterion**: ROM builds; `tools/boss_ai_debugger` shows correct template-id selection on representative scenarios; release-smoke + farcall audits green; boss-AI fixture replay tests continue to pass.
- **ROM cost**: 1 bank minimal, 2-3 if full template set later.
- **WRAMX cost**: 8-24 bytes in P0.5b-declared bank 2 for active template id/phase/target/confidence/stop flags; 0-4 bytes for one-turn stateless scoring variant.
- **Play-impact**: very high for named fights. Directly imports existing human-labeled multi-turn lessons (Whitney, Lance, Bugsy, Clair, Koga, Jasmine, Red) into ROM behavior.
- **Author**: Codex primary; Claude reviews.

### v2 deferred

- **Claude #5** — Decoupled Haki action slot with signal text. Conflicts with `docs/boss_ai_spec.md:31-33` (player-invisible Haki). Requires Cole-taste-call / contract amendment before reconsideration.
- **Claude #6** — Public RNG transparency surface for boss_ai_debugger. Pure dev tool, low gameplay impact. v2 unless promoted by iteration-velocity need.

### Phase order summary

```
P0.5a → P0.5b → P0.5c → P1 → P2 → P3 → P4 → P5 → P6 → P7
  ↓       ↓       ↓     ↓    ↓    ↓    ↓    ↓    ↓    ↓
drift  wramx   haki   per   ko   eff  rep  obs  role plan
restore plumb  audit  ldr   band mtx  buck log  cls  tmpl
```

Phase budget per slice: aim for ≤3 iterations to ship each phase. Total expected iterations: ~25-30 to ship the v1 set, leaving headroom in the 50-iter budget.

---

## Research findings — Claude lane

**STATUS: empty. Populated during Phase A.1.**

## Research findings — Codex lane

**STATUS: empty. Populated by Codex during Phase A.1.**

---

**End of roadmap.** Both Claude and Codex work from this file. If something changes during the build, update this file first, then act.
