# Boss AI Rebuild Plan

> **STATUS: COMPLETED VIA SIMPLER CURRENT-SOURCE PATH 2026-05-08.** The
> archived Layer A + Layer B rewrite below was not implemented. Source review
> found that current `boss.asm` already contains the accepted unified
> public-info scorer components, so BOSSAI-003 completed by documenting the
> platform/policy seam, formalizing policy design, adding a fixture-backed
> decision debugger, and adding a policy-contract audit.

**Status — 2026-05-08.** BOSSAI-003 complete. Current artifacts:
`engine/battle/ai/PLATFORM_API.md`, `engine/battle/ai/POLICY_DESIGN.md`,
`tools/boss_ai_debugger/`, and `tools/audit/check_boss_ai_policy_contract.py`.
Future behavior work should be evidence-driven through BOSSAI-004 labels and
the debugger, not a speculative wholesale rewrite.

This file is the canonical plan for the boss AI rebuild project. It supersedes incremental improvements to `engine/battle/ai/boss.asm` for the policy layer; the platform layer is untouched by the rebuild and continues to evolve under existing workstreams (BOSSAI-001 trace proof, AG-NN audit pass, etc.).

Related reading:
- `docs/boss_ai_spec.md` — existing 811-line design doc; the rebuild's interview phase treats this as input ("here's what we said before, do we still believe it?"), not as constraint.
- `docs/boss_ai_post_patch_notes.md` — history of previous patches.
- `docs/boss_ai_trace_capture.md` — trace pipeline used as the rebuild's regression suite.
- `audit/boss_ai_trace/*_live.txt` — captured first-decision behavior for every gym leader + Koga + Champion Lance. **These become the regression suite.**
- `engine/battle/ai/boss.asm` — the file under rebuild. 7144 lines, 160 top-level functions, 482 internal labels.
- `tools/boss_ai_debugger/` — fixture-backed Phase-1 scoring inspector and judgment recorder.
- `tools/boss_ai_preference/` — BOSSAI-004 labeler and preference corpus.

## 2026-05-08 completion note

The source did not match the stale premise that no central architecture existed.
It already had the core pieces of the simpler design:

- public plausible threat masks from visible species, revealed moves, and public
  learnability
- plan id/confidence selection
- top-candidate lookahead
- stochastic best-vs-second move choice
- switch prediction, scouting, repeat penalties, and switch-loop penalties
- plausible-risk switch candidate refinement

That makes the minimal appropriate fix a contract/debugger completion, not a
large asm replacement. The Layer A/Layer B material below is retained as
historical design context.

---

## Why we're rebuilding

Boss AI currently lives in `engine/battle/ai/boss.asm`: 7144 lines of overlay code on top of the base scoring in `engine/battle/ai/scoring.asm`. It accumulated organically across many Codex sessions with no central design intent. The user's assessment is that it is "huge and stupid": large in surface area, but produces decisions worse than the base AI's heuristics in many situations.

The fix is not incremental tweaking. The mess is structural — heuristics interact in unintended ways because no single design philosophy anchors them. The fix is to replace the heuristic policy layer wholesale, anchored to a stated design philosophy, while keeping the (hard-won) platform code that surrounds it.

## Scope: keep the platform, replace the policy

`boss.asm` contains two distinct layers stacked together. Step 1 of the rebuild is to formally split them; this plan's prior is the split below. **Step 1 may revise this prior** if the platform layer turns out to be more rotted than function-name inspection suggests.

### Platform layer — KEEP

These functions and infrastructure are the *hard* part of "boss AI that doesn't cheat." They are audited, tested via the trace pipeline, and shaped by real fixes against real bugs (e.g., the May-2026 cross-bank-call softlock, the `f2e18554` thunk fix). The rebuild does not touch them.

- **State tracking**: `BossAI_RecordPlayerSwitch`, `BossAI_RecordPlayerSpecies`, `BossAI_RecordPlayerFaint`, `BossAI_SetSeenPlayerAliveBit`, `BossAI_ClearSeenPlayerAliveBit`, `BossAI_RecordRevealedPlayerMove`, `BossAI_AddRevealedMoveToSpeciesMask`, `BossAI_SetRevealedSpeciesMaskBit`, `BossAI_IncrementTurnsElapsed`.
- **Public-info-only data plumbing**: `BossAI_GetActiveSpeciesRevealedMaskPointer`, `BossAI_LoadPlayerUsedMovesForActiveSpecies`, `BossAI_MirrorPlayerUsedMovesToSpeciesSlot`, `BossAI_GetActiveSpeciesUsedMovesPointer`, `BossAI_GetMoveAttr`, `BossAI_GetMoveByte`. The revealed-moves bitmask system is the technical mechanism that makes the no-hidden-info promise inspectable.
- **Cross-bank-call thunks**: the 7 hl-preserving wrappers (`AIxxx_HL` style) that route bank-0x0b scoring helpers via `farcall` correctly. Built in commit `f2e18554` after the original 39-cross-bank-`call` problem was diagnosed. Rewriting these from scratch is error-prone and adds nothing.
- **WRAMX bank-1 budget management**: tracked by `tools/audit/check_boss_ai_memory_budget.py`. The budget is finite; rebuild's policy layer must fit within it, but the budget machinery itself is not the rebuild's concern.
- **Anti-cheat audit infrastructure**: `tools/audit/check_boss_ai_no_cheat.py`, `check_boss_ai_gating.py`, `check_boss_ai_trace_invariants.py`, `check_boss_ai_live_capture_ledger.py`, `check_boss_ai_index_lines.py`. These guard the no-cheat invariants and the trace pipeline. They do not need rewriting.
- **Trace pipeline**: `tools/trace/boss_ai_state_factory.py`, `tools/trace/boss_ai_trace_batch.py`, `audit/boss_ai_trace/*_live.txt`. The per-leader live captures are gold — they are the regression suite for the rebuild.

Estimated split: ~30% of `boss.asm` is platform code (~2000-2500 lines).

### Policy layer — REPLACE

These functions implement decisions and scoring. They are the part the user describes as stupid. Replacing them does not affect the platform's invariants because every policy function calls *into* the platform API (`BossAI_GetMoveAttr`, `BossAI_PlayerHasRevealedPriorityThreat`, etc.) and produces a numeric score or a discrete choice.

- **Move evaluation**: `BossAI_ApplyMoveModel`, `BossAI_CurrentEnemyMoveHasKOPressure`, `BossAI_CurrentEnemyMovePressureScore`, `BossAI_CurrentEnemyMoveScoredPower`, `BossAI_ScaleMovePowerByBaseStatRatio`, `BossAI_ApplyEnemyKnownPressureModifiers`.
- **Threat assessment**: `BossAI_PlayerHasPublicThreatVsEnemy`, `BossAI_PlayerHasPublicThreatVsEnemyUncached`, `BossAI_PlayerHasRevealedPriorityThreat`, `BossAI_PlayerHasRevealedPriorityThreatUncached`.
- **Type matchup heuristics**: `BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem`, `BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem`, `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`, `BossAI_CheckTypeMatchupNoItem`, `BossAI_ApplyDragonsMajestyNoItem`.
- **Switch logic**: `BossAI_TrySwitch`, `BossAI_OnSwitchExecuted`, `BossAI_DecaySwitchCooldown`, `BossAI_CheckAbleToSwitchSafe`, `BossAI_FindFirstAliveSwitchCandidate`, plus the switch confidence / cooldown machinery.
- **Top-level decision loop**: `BossAI_SelectMove`, `BossAI_ResetTurnCaches`, `BossAI_EnemyIsGhostType` (ghost-type special-casing).

Estimated split: ~70% of `boss.asm` is policy code (~4500-5000 lines).

## Foundational design pillar: mixed strategy, not pure-optimal

Pokemon is a hidden-information game — closer to poker than chess. A boss AI that always picks the argmax of its scoring function is **structurally exploitable**: the player models the AI as deterministic and counter-plays for free. This is the dominant reason vanilla Gen 2 AI feels easy. The rebuild must fix this at the structural level, not as one heuristic among many.

The decision-making is two layers, distinct mechanisms:

### Layer A — EV-based scoring with near-tie mix

Scores all candidate moves with the heuristic system. Picks via:
- If gap from top score to second exceeds `EV_THRESHOLD` (~20% of top), play top.
- If multiple moves are within `EV_THRESHOLD`, sample from a softmax weighted by score, with a counter-switch denial bonus added to moves that punish the player's likely safe switch-in.

Handles ~90% of decisions. Pure-Gameboy-implementable: ~30 lines in `BossAI_SelectMove` plus the bonus computation. The mixing prevents trivial-determinism exploits ("Pidgeot always switches in safely against my Earthquake user") because the mix tilts toward Stone Edge when Pidgeot is revealed.

### Layer B — Online regret-minimization (the "safe vs crazy" tracker)

Layer A handles "near-EV-tie" mixing but cannot capture **dominant-move spots where the deception equity exceeds the EV cost** — the Thunderbolt-into-Ground class. The bluff this turn is worth its zero-EV cost only because of how the player's mental model has been shaped over previous turns.

Layer B is a per-battle adaptive bluff-frequency system based on **counterfactual regret minimization** (the algorithmic foundation behind modern poker AI), specialized to Pokemon. Per turn:

1. AI picks per Layer A (the "safe play"). Identifies a "crazy play candidate" — the structurally-relevant alternative for this state class (e.g., "switch into the Electric-type predicting Flying-switch" vs "EQ the Typhlosion in front of you").
2. Player commits their response.
3. AI evaluates: *if I had picked the crazy play, what would the outcome have been against the response the player just made?* — using the existing scoring system, no new infrastructure.
4. Compute regret = `counterfactual_outcome - actual_outcome`. Positive regret means the crazy play would have been better; the player exploited AI's predictability.
5. Update accumulated regret with exponential smoothing (avoids wild swings on a single noisy turn).
6. Adjust per-battle bluff frequency: high regret → bluff frequency rises; negative regret → bluff frequency drops.
7. On AI's next decision: roll `BattleRandom`; if below current bluff frequency, override Layer A with the crazy play candidate.

**Convergence story** — this matches the player's intuition exactly: *"player constantly acts like you'll never bluff which increases odds to bluff."* The algorithm is Nash-equilibrium-seeking in real time. If player exploits → regret accumulates → AI bluffs more → some bluffs land → player can't safely exploit → adjusts → regret stops accumulating → bluff frequency stabilizes at whatever rate keeps the player honest.

**Per-battle state** (4 bytes WRAMX): `regret_count: i16`, `bluff_freq: u8`, `last_alt_pick: u8`.

**Per-turn cost**: ~200-300 bytes of asm. The hard-looking step (counterfactual evaluation) is free — it's a second invocation of the existing scoring code on the alternative move against the player's now-revealed response.

**Per-leader personality** lives in the priors: cold-start `bluff_freq` (Falkner 5%, Whitney 8%, Clair 15%), regret-update step size, max-bluff-frequency cap (e.g., 30%). Tunable; defines the leader's flavor.

### Where the corpus comes back in

Layer B's regret-minimization handles *frequency* (how often to bluff). It does not by itself answer *what is the crazy play candidate for this state?* That structural question — defining the safe/crazy pair per state class — is where user-tagged corpus entries from playtests still earn their keep:

- Corpus tags scenarios as `(state class, defines crazy-play pair)`. E.g., "when AI's mon has a coverage move that's strictly worse than its STAB but threatens a specific switch-in, the crazy play is the coverage move."
- During play, Layer B's "what's the crazy play candidate?" lookup uses the corpus rules.
- Frequency stays online and adaptive; structural identification stays user-shaped.

This is the right division of labor: humans define *what counts as a bluff* (structural taste), the algorithm decides *how often to bluff* (online optimization).

### Why this stays north-star-compatible

- **No hidden-info reads.** Regret signals only use AI's own past moves and the player's observable responses — both public. No peeking at unrevealed party members or PP counters.
- **Heuristics still readable.** Layer A heuristics are plain scoring rules anchored to POLICY_DESIGN.md. Layer B's regret state is a 4-byte struct any auditor can dump: "AI's accumulated regret is +28, bluff frequency is 14%, last roll was 87 (no bluff)." Auditable.
- **Each leader has personality.** Falkner is risk-averse (low cold-start bluff frequency, small max cap). Whitney is conservative + punishing (high counter-switch bonus in Layer A, slow regret response). Clair is aggressive (high cold-start bluff frequency, fast regret adaptation). Personality is per-leader parameters anchored to flavor.
- **Player can learn the patterns.** "Clair bluffs sooner when ahead on HP because her cold-start bluff frequency is higher" is a learnable read. The system isn't random noise — bluff frequency is a deterministic function of accumulated regret. Mastery comes from reading the leader's *style*.

### Implementation reality

On SM83:
- Layer A: ~30-line addition to `BossAI_SelectMove`. Counter-switch bonus is a few hundred bytes per leader.
- Layer B: per-battle 4-byte WRAMX state (`regret_count`, `bluff_freq`, `last_alt_pick`, padding). ~200-300 bytes of asm: regret-update routine (called after player's response resolves), bluff-decision routine (called inside `BossAI_SelectMove`). The crazy-play-candidate lookup table (corpus-derived structural rules) lives in ROM, regenerated as part of the build.

Memory budget concern is small (WRAMX bank 1 is tight per `check_boss_ai_memory_budget.py`, but 4 bytes per active battle is well within slack). The corpus-derived structural-rule table lives in ROM where the budget is bank-by-bank rather than reserved.

### Trace pipeline implications

Once AI is stochastic, deterministic single-frame "AI picked move X" captures stop being a complete description. Two adaptations needed:

- **Seeded-RNG repro**: each `audit/boss_ai_trace/*_live.txt` capture pins a `BattleRandom` seed so the trace is reproducible.
- **Distribution capture**: each capture also records the score distribution + tie set + Layer B activation (if any) + sampled move. Audits verify "AI was sampling from the right set with the right Layer B state" rather than "AI picked the right move."

Lean toward distribution capture — it's the right abstraction for stochastic AI. Existing per-leader live captures need to be re-run after the rebuild lands; this is part of Step 4's regression check anyway.

## Methodology: interview-driven design

The current heuristics are bad because no single design philosophy anchors them. The rebuild fixes this by inverting the order: **philosophy first, heuristics second.**

### The interview

Two phases:

1. **Philosophy dump** (~30 min, free-form): the user writes a stream-of-consciousness description of how boss AI should think — what it values, what it should never do, what kinds of decisions it should be willing to "spend a turn" on. Plain English, ~500 words. This becomes the seed.
2. **Structured questionnaire** (~1-2 hours, 1-2 sessions): I produce ~30-50 specific questions covering the major decision categories — move selection, switching, setup, status, recovery, prediction, type-matchup weighting, prioritization conflicts. User answers in plain English with examples. Where ambiguous, I ask follow-ups.

The interview output is a design document: `engine/battle/ai/POLICY_DESIGN.md`. Every heuristic in the rebuilt policy layer cites a section of this document as its source. **No heuristic without an explicit design rationale.**

### Why this beats organic growth

- Heuristics that are stated principles can be argued with directly — "you said X, but this scenario suggests Y; do we revise?" — instead of being archeologically reconstructed.
- Conflict between heuristics becomes a *design* discussion, not a debugging session.
- 30-40 well-anchored heuristics reliably outperform 200 organically-grown ones.
- A new contributor (Codex, a future Claude session, the user themselves) can read POLICY_DESIGN.md and understand why the AI does what it does.

## Phasing

### Step 1 — Platform/policy audit (1 session, ~3-5 hours)

Read `boss.asm` end-to-end. Split functions into PLATFORM and POLICY using the prior above; verify by reading 5-10 implementations from each set. Write `engine/battle/ai/PLATFORM_API.md` documenting:
- The functions the policy layer is allowed to call.
- The invariants the platform guarantees (e.g., "this function only reads revealed moves, never reads `wEnemyParty[N].Moves`").
- The seam: where one layer ends and the other begins.

Output: `PLATFORM_API.md` + an updated split (which functions are actually platform vs policy after a real read).

If Step 1 finds the platform is also rotted (e.g., subtle hidden-info leaks, structural rot), full scrap goes back on the table. Don't pre-commit to keep until Step 1 confirms it.

### Step 2 — Philosophy dump + structured interview (1-2 sessions)

Phase 2.1: user writes ~500 words of stream-of-consciousness boss AI philosophy.
Phase 2.2: I produce ~30-50 structured questions; user answers across 1-2 sessions.

Output: `engine/battle/ai/POLICY_DESIGN.md` — the design document anchoring every future heuristic. Treat this as a living doc; revise as scenarios surface conflicts the interview missed.

### Step 3 — Initial heuristic synthesis (~1 week of focused work)

I write the new policy layer in asm, plugged into `PLATFORM_API.md`. ~30-40 heuristics, each citing a POLICY_DESIGN section. Default weights chosen from the interview where stated; otherwise reasonable middle values.

Output: new policy code in `engine/battle/ai/boss.asm` (replacing ~5000 lines of old code), `POLICY_DESIGN.md` annotations, `boss.asm` with platform layer untouched.

### Step 4 — Trace-capture regression check (~3 days)

Run new AI against every existing per-leader live capture (`audit/boss_ai_trace/*_live.txt`). For each:
- Same decision: pass.
- Different decision: surface to user; user judges. If new decision is correct, update the capture. If wrong, refine heuristic.

This is where the existing trace pipeline becomes the rebuild's regression suite. Captures are not sacred — they're a reference point. The user is the ultimate judge of correctness.

Output: refreshed `audit/boss_ai_trace/*_live.txt`, possibly with annotations distinguishing "AI changed, user approved" from "AI was always right."

### Step 5 — Iterative refinement via Boss AI Decision Debugger (ongoing)

Once the rebuild has a workable initial policy, the iteration loop is driven by the supporting tool described below. New scenarios → user judges → optimizer/co-pilot proposes weight or asm changes → user approves → AI improves.

## Supporting tool: Boss AI Decision Debugger

This is its own project, tightly coupled to the rebuild. It reuses the damage-debugger infrastructure (PyBoy boot cache, `safe_call.py`, hook-based instrumentation, symbol table) but retargeted at AI decisions instead of damage values.

### Phase 1 — Scoring inspector + judgment recorder (CLI, ~1 week)

Load a battle state, run boss AI, dump structured scoring breakdown for every legal move: every heuristic that scored it, its contribution, its file:line. Output: structured JSON + human-readable table. Interactive judgment mode: "AI picked X. Right? [y/n/correct-pick]." Saves to a corpus file.

Files: `tools/boss_ai_debugger/inspect.py`, `tools/boss_ai_debugger/judge.py`, `tools/boss_ai_debugger/corpus/`.

### Phase 2 — Weight optimizer (~1 week)

Given the corpus, find weight assignments that satisfy as many entries as possible (constrained linear/quadratic programming over the heuristic-weight space). Suggest weight diffs, show which entries each diff fixes/breaks, user approves. **Every update is fully readable: a diff of weights with a one-line explanation per change.**

File: `tools/boss_ai_debugger/optimize.py`.

### Phase 3 — GUI (~1-2 weeks)

Local Flask + simple HTML. Three panes: battle state visualization (showing only what AI sees — revealed-info filter), AI's reasoning (ranked moves with expandable per-heuristic breakdown), user verdict (pick the right move, optionally rank others, save to corpus). Plus a "Train" button: runs the optimizer on accumulated unfixed judgments, shows proposed weight diff, user approves.

**This is the button that makes it feel like training.**

Files: `tools/boss_ai_debugger/gui/`.

### Phase 4 — LLM heuristic co-pilot (~1 week)

When the optimizer can't satisfy a judgment by reweighting (the heuristic's *logic* is wrong, not its weight), surface to me. I propose an asm edit. User reviews in the GUI, accepts/rejects/iterates.

This is where the rebuild stays alive past the initial Step 3 — when interview-stated principles meet reality and need revision, the co-pilot proposes the asm change and POLICY_DESIGN.md update together.

File: `tools/boss_ai_debugger/copilot.py`.

### Phase 5 — Synthetic scenario generator (~3-5 days)

Random battle states constrained to be realistic — uses gym leader teams from `data/trainers/parties.asm`, valid level ranges for that point in the game, real movesets. Tuned to surface *interesting* states: boundary cases of interview answers, scenarios where two principles conflict, mirror matches at unusual HP ratios.

Hypothesis-strategy style, reusing the damage-debugger fuzzing infrastructure (`tools/damage_debugger/fuzz.py` patterns).

Files: `tools/boss_ai_debugger/scenarios.py`.

## North star compliance

The rebuild and supporting tool both protect the First-Playthrough Promise:

- **No hidden-info reads**: enforced by the platform layer + `check_boss_ai_no_cheat.py`. The rebuild keeps both.
- **Haki = explicitly authored exceptions only**: kept as a separate workstream (BOSSAI-001's "design contract but no source implementation"). The rebuild does not implement Haki implicitly through accident; if Haki ships, it ships as named exceptions in POLICY_DESIGN.md.
- **Heuristics readable**: one principle in POLICY_DESIGN.md ↔ one named heuristic in source. Future readers can trace any decision to a stated principle.
- **No black-box training**: every change in the iteration loop is either a weight diff (Updater A) or an asm diff (Updater B). Both are reviewable. The corpus is a transparent, growing set of (state, your-judgment) pairs — not a model checkpoint.

## Verification

The rebuild is verified the same way the existing boss AI is verified, plus the new tool:

- All existing static audits pass: `check_boss_ai_no_cheat`, `check_boss_ai_gating`, `check_boss_ai_memory_budget`, `check_boss_ai_trace_invariants`, `check_boss_ai_live_capture_ledger`, `check_boss_ai_index_lines`.
- Every per-leader live capture in `audit/boss_ai_trace/` either matches (sanity) or has been re-judged by the user during Step 4.
- Damage debugger continues passing — the rebuild doesn't touch the damage chain.
- Boss AI Decision Debugger corpus grows: every (state, user-judgment) pair becomes a permanent test that the AI must keep satisfying as it evolves.
- POLICY_DESIGN.md and boss.asm stay in sync; mismatches caught by spot-checking heuristic citations.

The rebuild does not bump `SAVE_FORMAT_VERSION` (it touches `engine/battle/ai/`, not `ram/`). No save-format escalation needed.

## Decisions locked in (2026-05-05)

- **Time budget**: 4-week focused sprint. Damage debugger continues in parallel only for the cheap items (H1 multi-process fuzz, H3 weather/badges); deeper damage-debugger work pauses until rebuild v1 ships.
- **Start**: next session kicks off Step 1 (platform/policy audit).
- **Layer architecture**: Layer A (EV-based scoring + near-tie mix) + Layer B (corpus-driven strategic-deception override). See "Foundational design pillar" above.
- **Haki scope**: deferred past initial rebuild. Build strict-public-info policy first; Haki rides on top later as authored once-per-battle exceptions.

## Open questions still to answer during Step 1 / Step 2

1. **Existing heuristics worth saving.** Are there specific decisions the current AI gets right that should be preserved through the rebuild? Surface during Step 1 audit; capture in Step 4 trace-regression check as anchor scenarios.
2. **Tool ordering.** Tool Phase 1 (CLI scoring inspector) is needed *during* Step 4 (trace regression check). My recommendation: build Tool Phase 1 *before* Step 3 (heuristic synthesis) so it's ready when Step 4 starts. Confirm during Step 1 audit when we know the platform API surface.

## Out-of-scope for v1 — captured for v2

These are good ideas but explicitly defer past v1 to protect the 4-week budget. Track here so they don't drop off the floor.

- **Preference-training side app (BOSSAI-004).** The old RL-ROM simulator-first idea is superseded by `docs/boss_ai_rl_training_plan.md`: build a preference labeler first, then consider simulator/tournament/optimizer work only after labels exist. This remains out of scope for the v1 source rebuild, but it can be resumed independently as side-app tooling because Version A collects corpus/taste data rather than rewriting the ROM policy.
- **Cross-leader policy transfer.** If Whitney's Layer B corpus has 50 entries and Falkner's has 5, can Falkner's pattern-matcher borrow from Whitney's where features overlap? Risk: leader personalities blur; gain: faster onboarding for under-judged leaders. Defer until v1 reveals whether this matters.
- **Live-play in-the-loop training.** GUI lets you pause a real battle mid-turn, judge AI's pick, save to corpus. Higher engagement than replay-based judging but also more cumbersome. Tool Phase 4-ish addition; evaluate after Phase 3 GUI lands.

## What changes in the doc tree as this lands

- New: `engine/battle/ai/POLICY_DESIGN.md` (Step 2)
- New: `engine/battle/ai/PLATFORM_API.md` (Step 1)
- New: `tools/boss_ai_debugger/` (Tool Phase 1 onward)
- Modified: `engine/battle/ai/boss.asm` (policy layer replaced; platform layer unchanged)
- Modified: `audit/boss_ai_trace/*_live.txt` (Step 4 may update some captures)
- Modified: `docs/boss_ai_spec.md` may be partially superseded; review at end of Step 2
- Modified: `docs/project_roadmap.md` — BOSSAI-003 row tracking this project
- Per-step verification entries appended to `tools/boss_ai_debugger/BUG_CHECK.md` (new, mirrors the damage debugger's pattern)
