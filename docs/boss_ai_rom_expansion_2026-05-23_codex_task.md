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

**STATUS:** locked 2026-05-23 by mutual Claude+Codex slice_accepted rows in `audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` (see P0_phasing_locked phase). P0.5 split into a/b/c per Codex convergence note (P0.5b is paired-review work, not setup-allowlist). **2026-05-23 pivot:** P1 (per-leader personality kernels) and P4 (kernel-driven reply-bucket softmax) were DROPPED per Cole directive — "personality is the team itself, not how the boss plays"; meta-level per-leader scoring risked making AI play *worse* without heavy curated playtest tuning. Replaced with **P1H (Uniform Haki Oracle refactor + extension + per-leader taunts)**, which lifts the existing bespoke Morty Haki into a uniform Oracle pattern across the 16-class eligible roster and adds the pre-fire taunt as the per-leader feel signal. P1a functional code (`wBossAIKernel`, kernel constants, kernel data, kernel load helper) was reverted on this branch; the save-format audit precision-fix from that slice was kept (independently good — guards against wEventFlags spillover without false-positives on padded reserve internals). See `P1a_kernel_load_mechanism` phase rows in the handoff log for the full retraction provenance. Roadmap pivot paired-contract amendment landed via handoff rows; both LLMs `slice_review` the new shape before P1H ack_start.

**Phase ordering rationale**: Phase A.0.5 first (unblocks v7 strict + WRAMX-2 dependents); **P1H next** (Uniform Haki Oracle lands the gate rule + per-leader taunts + extends Haki to all 16 eligible classes — needed before later phases assume the Oracle shape and to absorb the existing bespoke Morty path); P2 supplies the KO-band data layer; P3 cleans up scattered effect logic; P5 introduces observation memory; P6 adds role classification; P7 puts it all into named plan templates.

**Lever-to-phase mapping reference** (for cross-checking with handoff log rows 2 and 4; updated 2026-05-23):

| Phase | Codex levers | Claude levers | Primary author |
| --- | --- | --- | --- |
| P0.5a | — | (drift restore work) | Claude |
| P0.5b | — | (WRAMX plumbing) | Both (paired) |
| P0.5c | — | Claude #2 (revised) | Claude |
| ~~P1~~ | ~~Codex #7~~ | ~~Claude #1~~ | DROPPED 2026-05-23 (Cole pivot) |
| P1H | (Haki Oracle asm refactor + taunt plumbing) | (spec amendment landed Item 2; new uniform-Oracle audit) | Both (paired) |
| P2 | Codex #1 | Claude #3 | Both (paired) |
| P3 | Codex #5 | — | Codex |
| ~~P4~~ | ~~Codex #6~~ | ~~(reads P1 kernels)~~ | DROPPED 2026-05-23 (depended on P1) |
| P5 | Codex #3, #8 | Claude #4 | Both (paired cluster) |
| P6 | Codex #4 | — | Codex |
| P7 | Codex #2 | — | Codex |
| v2 | — | ~~Claude #5~~ (promoted to P1H taunt text), Claude #6 | (Claude #6 deferred) |

---

### P0.5a — Drift restore (setup-allowlist)

- **Goal**: cherry-pick `docs/llm_pairing_rules.md` and `tools/audit/check_two_llm_handoff_log.py` from the debugger-masterpiece-roadmap branch's pairing-rules / handoff-log work onto this branch (concrete source SHAs preserved in the boss-AI handoff log slice_update row for P0_5a_drift_restore). Plus the `tools/debugger/handoff_log.py` module the audit imports. Add setup-scope handling for these files in the no_solo_commits audit narrowly enough that the P0.5a restore is exempt, but later non-setup edits to those files still require paired review. v7 strict acceptance criterion becomes runnable.
- **Public-info-only**: not gameplay; tooling-only.
- **Files to touch (write set)**: `docs/llm_pairing_rules.md` (new), `tools/audit/check_two_llm_handoff_log.py` (new), `tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py` (allowlist update).
- **Acceptance criterion**: `python tools/audit/check_two_llm_handoff_log.py --strict --store audit/boss_ai_rom_expansion_2026-05-23_handoff_log.jsonl` exits 0; `python tools/audit/check_no_solo_commits_boss_ai_rom_expansion.py` exits 0.
- **ROM cost**: 0.
- **WRAMX cost**: 0.
- **Play-impact**: none. Pure setup.
- **Author**: Claude. Setup-scope restore commit acceptable; Codex slice_review post-commit acknowledged via paired row. Future edits to restored files require paired review unless a later phase explicitly allowlists them.

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
- **Acceptance criterion**: `python -m tools.boss_ai_debugger haki-coverage --self-test` exits 0 and reports all 19 Haki leaders listed in `docs/boss_ai_spec.md:66-84` (Morty, Chuck, Jasmine, Pryce, Clair, Will, Koga, Bruno, Karen, Lance, Brock, Misty, Lt. Surge, Erika, Janine, Sabrina, Blaine, Blue, Red).
- **ROM cost**: 0.
- **WRAMX cost**: 0.
- **Play-impact**: none directly; developer iteration velocity on later levers.
- **Author**: Claude. tools/ change, not setup-allowlist; paired Codex slice_review before commit OR commit-then-rereview.

### P1H — Uniform Haki Oracle refactor + extension + per-leader taunts (paired)

- **Goal**: replace the bespoke Morty-only `BossAI_TryMortyHakiOracle` with a generic `BossAI_OracleHakiRead` that any Haki-eligible leader uses. Implement the gate rule from `docs/boss_ai_spec.md:39-44` literally (`wBossAITier != AI_TIER_EARLY` AND `wTrainerClass NOT IN BossAIHakiExcludedClasses`), extending Haki from 1 leader to the full 16-class roster (Johto post-Whitney + Silver MID+/LATE + Rocket executives + E4 + Champion + Blue + Red). Add per-leader pre-fire taunt text storage and the queue-and-flush plumbing that prints the taunt **before** the enemy action animation. Determinism: known-action re-score using the player's locked move (post-`ParsePlayerAction`) — no second-best RNG. v1 is **enemy-first only**; player-first Haki sequencing is out of scope until v2 (rephrased per Codex chat lane-shape: "enemy-first v1 only, deterministic known-action re-score, class/tier gate, queued taunt before enemy action, no P1/P4 dependencies, and no deletion of prior handoff history").
- **Public-info-only**: Oracle reads the player's just-locked move via `ParsePlayerAction`'s output (legal per the existing Morty Haki precedent — the boss reads the input the player committed *this turn*, not unrevealed party/moves/items). Deterministic re-score; no hidden info. Taunt text is per-leader flavor with no mechanic information leakage — players learn to fear the taunt across the game, building mastery without the mechanic name ever being printed.
- **Files to touch (write set)**:
  - `engine/battle/ai/boss.asm` — rename `BossAI_TryMortyHakiOracle` → `BossAI_OracleHakiRead`; generalize the ace-detection + first-turn-active checks per `docs/boss_ai_spec.md` §"Hook Site".
  - `data/trainers/ai_haki_excluded.asm` (new) — `BossAIHakiExcludedClasses` table holding `BROCK`, `MISTY`, `LT_SURGE`, `ERIKA`, `JANINE`, `SABRINA`, `BLAINE`.
  - `data/boss_ai/haki_taunts.asm` (new) — per-leader (trainer class, trainer id) → text-pointer rows covering the 16 eligible classes.
  - `engine/battle/ai/haki_taunt_queue.asm` (new, small) — queue-and-flush helper: store a pending taunt id at Oracle fire time; flush the print job immediately before the enemy move animation begins.
  - `tools/audit/check_haki_oracle_uniform.py` (new) — audits (a) no bespoke `BossAI_TryMortyHakiOracle`-style entry points remain, (b) every eligible class has a taunt row, (c) every excluded class is present in `BossAIHakiExcludedClasses`, (d) the taunt-queue flush call is sequenced BEFORE the enemy-action dispatcher, not after.
- **Acceptance criterion**: ROM builds; release-smoke + farcall audits green; `python tools/audit/check_haki_oracle_uniform.py` exits 0; `python tools/audit/check_haki_coverage_audit.py` continues to PASS; `python -m tools.boss_ai_debugger haki-coverage --self-test` exits 0; manual smoke or `tools/boss_ai_debugger` fixture shows: (1) Morty fight still fires Haki on ace's first turn (regression test for the refactor), (2) one of the newly-extended classes (e.g. Chuck or Karen) ALSO fires Haki on ace's first turn with the per-leader taunt printed BEFORE the move animation, (3) an excluded Kanto gym (e.g. Brock or Sabrina) does NOT fire Haki.
- **ROM cost**: ~0.5–1 bank total. Taunt text data + generic helper. The generic Oracle is ~30 bytes smaller than the bespoke Morty path once duplicated branches collapse, partially offsetting the new helpers.
- **WRAMX cost**: 1 byte (pending-taunt-id in the P0.5b-declared bank 2) + reuses existing `wHakiSpent` + the ace-first-turn bit already mentioned in the spec. No save-format change.
- **Play-impact**: very high. Extends the "Lance's eyes narrow" / "Karen smiles slowly" pre-Haki moment from 1 leader (Morty, who currently doesn't even print a taunt) to 16 leaders. The taunt becomes a player-trainable signal of "this turn is about to be brutal" without leaking the mechanic name. Resolves the Cole-flagged complaint about the current bespoke Morty Haki shape (single-leader, no taunt, opaque to the player).
- **Author**: paired. **Codex primary** on the asm refactor + new helpers + taunt-queue plumbing (his stated future lane). **Claude primary** on the spec amendment (already landed on this branch via Item 2 — `docs/boss_ai_spec.md` lines 31-38 + 39-44 + 67-100; see handoff log Item 2 row for provenance) + the `check_haki_oracle_uniform.py` audit + the per-leader taunt copy taste-pass. Both LLMs `slice_review` before commit; new-phase work means chat ack BEFORE ack_start per the Codex commit-then-review rule.

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

### ~~P4~~ — Top-K reply-bucket payoff with kernel-driven temperature — **DROPPED 2026-05-23**

P4 depended on P1's per-leader softmax-temperature byte. With P1 dropped (personality = team, not play-style), the kernel-driven temperature input disappears, so P4 has no anchor. Plain top-K softmax without per-leader temperature was considered and rejected as too generic for the ROM cost — bosses would all play with the same distribution shape, which is the opposite of the curated feel the project wants. Re-evaluate as v2 only if a public-info-derived temperature source emerges (e.g. tier-driven sharpness with 3 buckets), but not as a kernel-dependent phase.

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

- **Claude #5** — **PROMOTED 2026-05-23 to P1H.** Originally deferred for conflicting with player-invisible Haki; Cole amended the contract on 2026-05-23 to allow per-leader pre-fire taunt text (no mechanic naming, no other visible effect). The decoupled-Haki-with-signal-text idea now lives inside P1H as the queue-and-flush taunt mechanic.
- **Claude #6** — Public RNG transparency surface for boss_ai_debugger. Pure dev tool, low gameplay impact. v2 unless promoted by iteration-velocity need.
- **(new v2 candidate)** — Player-first Haki sequencing. P1H v1 keeps Haki enemy-first only. If a future fight wants Haki to read the player input AND act before the player's animation resolves (rather than just before the boss's), the engine plumbing for player-first sequencing is a meaningful new surface; defer until P1H v1 ships and the player-first feel is taste-checked.

### Phase order summary

```
P0.5a → P0.5b → P0.5c → P1H → P2 → P3 → P5 → P6 → P7
  ↓       ↓       ↓      ↓     ↓    ↓    ↓    ↓    ↓
drift  wramx   haki   haki   ko   eff  obs  role plan
restore plumb  audit  oracle band mtx  log  cls  tmpl
```

Phase budget per slice: aim for ≤3 iterations to ship each phase. Total expected iterations after 2026-05-23 pivot: ~22-26 to ship the v1 set (P1 and P4 dropped saves ~5-7 iterations of the original ~25-30 estimate), leaving more headroom in the 50-iter budget for the P1H taunt-text taste-pass and possible v2 reach.

---

## Research findings — Claude lane

**STATUS: empty. Populated during Phase A.1.**

## Research findings — Codex lane

**STATUS: empty. Populated by Codex during Phase A.1.**

---

**End of roadmap.** Both Claude and Codex work from this file. If something changes during the build, update this file first, then act.
