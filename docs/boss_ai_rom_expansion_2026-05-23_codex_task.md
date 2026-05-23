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

**STATUS: empty. Filled in at end of Phase A.3 by both LLMs.**

Each phase will be appended here with:
- **Phase ID** (e.g. P1, P2, …).
- **Goal sentence** (one line, public-info-only check inline).
- **Files to touch** (write set with collision-risk noted).
- **Acceptance criterion** (mechanical test or audit).
- **ROM cost estimate** (KB or banks).
- **WRAMX cost estimate** (bytes, if any).
- **Play-impact note** (which fights this changes).

---

## Research findings — Claude lane

**STATUS: empty. Populated during Phase A.1.**

## Research findings — Codex lane

**STATUS: empty. Populated by Codex during Phase A.1.**

---

**End of roadmap.** Both Claude and Codex work from this file. If something changes during the build, update this file first, then act.
