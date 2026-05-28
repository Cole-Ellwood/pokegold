# Boss AI Lookahead P-A — futility cutoff implementation spec (v2.1)

**Status:** implementation-ready spec for the P-A track only. Other phases
(P-C / P-D / P-B) deferred to v3 pending P2 KO-band oracle landing and a
fuller branch-context contract per round-2 review.
**Author:** Claude. Cole is sole approver; no LLM pairing.
**Date:** 2026-05-26.
**Background:**
[v2 research doc](boss_ai_lookahead_2x_research_2026-05-25_v2.md) +
[GPT 5.5 Pro round-1 review of v1](boss_ai_lookahead_2x_gpt_review_2026-05-25.md).
Round-2 review of v2 lives in this session transcript; the load-bearing
findings (K6, K7, J3) are baked into this spec.
**Companion docs (canonical):**
[boss_ai_spec.md](boss_ai_spec.md) (§"Decision Breadth And Play Budget"),
[POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md),
[audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md),
[engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm) (score convention).

This spec ships P-A alone. The full "2x smarter" stack from v2 (reply
buckets, quiescence, killer prior) is **deferred** — round-2 review showed
it needs the P2 KO-band oracle and an executable branch-context ABI
before any ASM lands. P-A is the one phase that's evaluator-independent
and can ship now.

---

## 1. What P-A does

**Current state** ([boss_policy_move.asm:5324-5419](../engine/battle/ai/boss_policy_move.asm)):

`BossAI_ApplyLookaheadToTopMoveCandidates` walks all 4 move slots and
calls `BossAI_EvaluateActionLookahead` on candidates whose score is
within `BOSS_AI_LOOKAHEAD_BONUS_CAP = 18` of the *initial* minimum score
(lower is better, per
[engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm)). The cutoff
bound is fixed at function entry and never tightens as candidates are
evaluated.

**P-A change:** replace the static cutoff with a **dynamic futility
cutoff** that tightens as the running best improves. For each candidate
about to be evaluated, skip if it cannot possibly beat the current
running best even with maximum upside.

**Algebra** (lower is better, signed delta in `[-CAP, +CAP]`):

- `running_best` = minimum over all already-evaluated post-eval scores
  and not-yet-evaluated pre-eval scores. Monotonically non-increasing.
- For candidate `i` about to be evaluated, best-case post-eval score is
  `max(1, score[i] - CAP)` because
  [`BossAI_ApplySignedDeltaToScore`](../engine/battle/ai/boss_policy_move.asm)
  saturates negative deltas at 1, not 0
  ([:5428-5432](../engine/battle/ai/boss_policy_move.asm)).
- **Skip candidate `i` if `score[i] - CAP >= running_best`.** It cannot
  improve to beat current best even with maximum upside.
- After evaluating candidate `i`, update `running_best` with its
  post-eval score.

**Why this is strictly tighter than the existing cutoff:** the existing
gate compares against `initial_best + CAP` (computed once); P-A
compares against `running_best - CAP` (updated each iteration). As
soon as any candidate produces a lookahead delta that lowers
`running_best` below `initial_best`, P-A excludes additional candidates
the static gate would have evaluated. In the degenerate case where no
candidate improves running_best, P-A's bound equals the static bound.

---

## 2. Behavior delta and S4 sign-off

P-A changes behavior in near-tie cases — same class as S4
([audit/boss_ai_perf/hotspots.md:65,111-113](../audit/boss_ai_perf/hotspots.md)).
**Cole approval required before merge.**

**Identical behavior** in well-separated cases: when the best candidate
is clearly the best (gap > CAP), P-A skips the same losers as the
existing cutoff.

**Different behavior** in near-tie cases: when candidate 0 evaluates and
improves running_best, P-A may skip candidates 1-3 that the existing
cutoff would have evaluated. Skipped candidates retain their base
score (no lookahead delta applied).

**Second-best ordering caveat** (round-2 K8 partial — see §5): the
existing cutoff and P-A both leave skipped candidates at their base
score, which can fail to award them a deserved lookahead improvement
relative to their second-best competitors. This distortion class
already exists in the current code; P-A inherits it but does not amplify
it. The downstream
`BossAI_SelectMove`
([:2889-2912](../engine/battle/ai/boss_policy_move.asm)) uses
60/75/90% best-pick probabilities by score gap — near-tie skips can
shift the second-best distribution. Same S4 sign-off covers this.

---

## 3. Implementation (SM83)

Round-2 K6 fixes baked in:

- **Separate storage** for `running_best` (was `b` in v2's sketch,
  conflicting with the existing eval-count and trace-index use of `b`).
- **Underflow comment corrected**: candidate best-case is `max(1, score - CAP)`,
  not 0.
- **Trace expansion**: extend `wBossAITraceLookaheadBonusTop` from 3
  bytes to 4 (round-2 A3) so all `BOSS_AI_LOOKAHEAD_N = 4` candidates
  appear in trace.

**Register allocation in the loop:**

| Reg | Use |
| --- | --- |
| `hl` | score pointer (unchanged) |
| `de` | move pointer (unchanged) |
| `c` | move-slot counter, decremented per slot (unchanged) |
| `b` | evaluated-candidate counter, incremented per evaluator call (unchanged — drives `cp BOSS_AI_LOOKAHEAD_N` and trace index) |
| WRAM `wBossAILookaheadRunningBest` | dynamic minimum, 1 byte, lives only during the lookahead loop. Sentinel `$ff` = uncomputed (matches existing cache-byte conventions). |

`wBossAILookaheadRunningBest` is new. Add to the boss AI WRAM reserve
adjacent to other lookahead caches (e.g. immediately after
`wBossAILookaheadDepthCache` at
[ram/wram.asm:2465](../ram/wram.asm)). Cost: 1 byte. Boss AI reserve has
9 free bytes under trace
([boss_ai_spec.md:794-808](boss_ai_spec.md)) — comfortably inside.

**Reset:** add to `BossAI_ResetTurnCaches`
([boss_platform.asm](../engine/battle/ai/boss_platform.asm)) so the
sentinel is restored at the top of each AI tick.

**Sketch** (replaces the body at
[:5338-5419](../engine/battle/ai/boss_policy_move.asm) — full replacement,
not patch):

```text
BossAI_ApplyLookaheadToTopMoveCandidates:
	ld a, [wBossAITier]
	cp BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN
	ret c

IF DEF(BOSS_AI_TRACE)
	xor a
	ld [wBossAITraceRiskFlags], a
	ld hl, wBossAITraceLookaheadBonusTop
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a          ; 4 bytes now (was 3) — covers all N candidates
ENDC

; Compute initial running_best = min(scores < 80). Stored in WRAM scratch.
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
	ld b, 79                          ; b = scratch min during this pass
.scan_best
	ld a, [de]
	and a
	jr z, .scan_done
	ld a, [hl]
	cp 80
	jr nc, .scan_next                 ; blocked
	cp b
	jr nc, .scan_next
	ld b, a
.scan_next
	inc hl
	inc de
	dec c
	jr nz, .scan_best
.scan_done
	ld a, b
	ld [wBossAILookaheadRunningBest], a

; Main eval loop: walk slots, futility-cutoff each, eval, update running_best.
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
	ld b, 0                            ; b = evaluated-candidate counter
.eval_loop
	ld a, [de]
	and a
	jr z, .eval_done
	ld a, [hl]
	cp 80
	jr nc, .eval_next                  ; blocked

; Futility test: skip if score - CAP >= running_best.
; Candidate best-case post-eval is max(1, score - CAP); ApplySignedDeltaToScore
; saturates at 1. If score <= CAP, candidate can always reach 1, never skip.
	cp BOSS_AI_LOOKAHEAD_BONUS_CAP + 1
	jr c, .candidate_alive             ; score <= CAP, can saturate to 1; evaluate
	sub BOSS_AI_LOOKAHEAD_BONUS_CAP    ; a = score - CAP
	ld c, a                            ; stash temporarily
	ld a, [wBossAILookaheadRunningBest]
	cp c
	ld a, [hl]                          ; restore a = score (preserves [hl] semantics for evaluator)
	ld c, NUM_MOVES                    ; HOLD: must preserve c (move counter) — see §3.1 below
	; ...
```

**3.1 Register-preservation note.** The sketch above shows the futility
test but I've used `c` as scratch and then "restored" it to `NUM_MOVES`,
which is wrong because `c` is the *running* move counter (decremented
per slot) not the constant. The fix: use a WRAM scratch byte for the
intermediate `score - CAP` value, OR use the stack:

```text
; Replace the c-stash above with:
	push bc                            ; save b (eval count) and c (slot counter)
	ld c, a                            ; c = score - CAP
	ld a, [wBossAILookaheadRunningBest]
	cp c                                ; carry set if running_best < score - CAP
	pop bc
	jr c, .eval_next                   ; futile — skip
	ld a, [hl]                          ; reload candidate score for evaluator
.candidate_alive
	; existing evaluator call sequence (unchanged from current code)
	push hl
	push de
	ld a, [de]
	call BossAI_EvaluateActionLookahead
IF DEF(BOSS_AI_TRACE)
	ld [wTempByteValue], a
ENDC
	pop de
	pop hl
	push bc
	call BossAI_ApplySignedDeltaToScore
	pop bc

; Update running_best with post-eval score.
	ld a, [hl]
	ld c, a                             ; save score
	ld a, [wBossAILookaheadRunningBest]
	cp c
	jr c, .no_update                    ; running_best < score, no update
	ld a, c
	ld [wBossAILookaheadRunningBest], a
.no_update

IF DEF(BOSS_AI_TRACE)
	push bc
	push hl
	ld a, b                             ; b = eval count (= candidate index for trace)
	cp BOSS_AI_LOOKAHEAD_N              ; 4 now, was 3 — trace expanded
	jr nc, .after_trace
	ld c, a
	ld b, 0
	push de
	ld hl, wBossAITraceLookaheadBonusTop
	add hl, bc
	ld a, [wTempByteValue]
	ld [hl], a
	pop de
.after_trace
	pop hl
	pop bc
ENDC
	inc b                               ; eval count++
	ld a, b
	cp BOSS_AI_LOOKAHEAD_N
	jr nc, .eval_done
.eval_next
	inc hl
	inc de
	dec c                               ; c = move slot counter; OK to dec because each path preserved it
	jr nz, .eval_loop
.eval_done
	ret
```

**Confidence on the sketch:** medium. The register-preservation needs
careful proof against the actual evaluator's clobber set. Before merge,
run the helper-clobber audit (see §6) on every path from
`.candidate_alive` through `BossAI_EvaluateActionLookahead` and
`BossAI_ApplySignedDeltaToScore` to confirm `c` (slot counter) survives.
The current code preserves `bc` around both calls; that pattern is
maintained.

**Trace constants:** the existing trace block hardcodes `cp 3` at
[:5393](../engine/battle/ai/boss_policy_move.asm) and writes to a
3-byte buffer. v2.1 expands the buffer to 4 bytes (add 1 byte to the
trace section of WRAM) and replaces the magic `3` with
`BOSS_AI_LOOKAHEAD_N`. The +1 byte stays inside the trace-build WRAM
allowance.

---

## 4. WRAM additions

| Symbol | Bytes | Section | Reset |
| --- | --- | --- | --- |
| `wBossAILookaheadRunningBest` | 1 | Boss AI reserve (bank 1, adjacent to existing lookahead caches) | `BossAI_ResetTurnCaches` sets to `$ff` |
| `wBossAITraceLookaheadBonusTop` extension | +1 (3 → 4) | Boss AI trace block | Zeroed at lookahead entry |

**Total new WRAM in bank 1**: 1 byte in the always-on reserve (well
inside the 9-byte free count under trace per
[boss_ai_spec.md:794-808](boss_ai_spec.md)) + 1 byte in the trace-only
section.

**No save format impact.** The boss AI reserve is volatile state, not
save-formatted (per [boss_ai_spec.md:794](boss_ai_spec.md)).

---

## 5. Cycle cost estimate

Per-loop overhead vs current code:

- 5 extra T-cycles for the futility test on candidates that pass (one
  `cp`, one `sub`, one WRAM load, one `cp`, one `jr`).
- ~50 T-cycles saved per skipped candidate (avoid full
  `BossAI_EvaluateActionLookahead` body).
- 6-10 T-cycles for the running_best update after each evaluator call.

**Estimated net** on heavy late scenario
([baseline.json](../audit/boss_ai_perf/baseline.json), 3.23M T-cycles):

- If 0 candidates are skipped: ~+30 T-cycles (negligible).
- If 1 candidate is skipped on average: ~−80k T-cycles (≈−2.5%).
- If 2 candidates are skipped on average: ~−180k T-cycles (≈−5.5%).

Skip rate is the unknown. Empirical measurement required (§6).

**No degradation expected** vs the current static cutoff — P-A's bound
is strictly tighter, so skip count is always ≥ current skip count.

---

## 6. Verification before merge

**Mechanical floor:**

- `make pokegold.gbc` clean build green.
- `python tools/audit/check_release_smoke.py` green.
- `python tools/audit/check_farcall_hl_clobber.py` + `check_farcall_a_clobber.py` green.
- `python tools/audit/check_boss_ai_no_cheat.py` + `check_boss_ai_gating.py` + `check_boss_ai_trace_invariants.py` green.
- `python tools/audit/check_save_format_version.py` green (no save-format change).
- `python scripts/generate_dev_index.py --rom pokegold` regenerate.

**Battle-code ABI safety floor** (per [feedback_ag_nn_clobber_class](../memory)):

- `python -m tools.damage_debugger.clobber_smoke` green. P-A touches the
  lookahead driver, which is in the battle-code register-discipline
  surface. Non-negotiable.

**P-A specific audits to add** (new tooling, lands with the patch):

- `tools/audit/check_lookahead_futility_bound.py` — proves the new
  cutoff is monotonically at least as aggressive as the existing static
  cutoff (no regressions in skip rate).
- `tools/audit/check_lookahead_trace_width.py` — confirms
  `wBossAITraceLookaheadBonusTop` is 4 bytes and the trace block iterates
  to `BOSS_AI_LOOKAHEAD_N`, not a hardcoded `3`.
- `tools/audit/check_lookahead_running_best_lifecycle.py` — confirms
  `wBossAILookaheadRunningBest` is reset in `BossAI_ResetTurnCaches` and
  not read outside the driver's scope.

**Cycle bench** ([audit/boss_ai_perf](../audit/boss_ai_perf)):

- Run with ≥10 samples per scenario (mid_lead, late_lead,
  late_lookahead_heavy).
- Report mean + p95.
- Confirm heavy-late ≥0% delta (no regression) and report any savings.

**Behavioral verification** (the S4 sign-off material):

- Trace parity on all 19 fixture scenarios in
  [audit/boss_ai_trace/](../audit/boss_ai_trace/).
- Re-baseline any near-tie scenarios where P-A's tighter bound causes a
  different selection. Document each diff in the commit message.

---

## 7. What's deferred (and why)

Per round-2 review, the full v2 stack (P-C / P-D / P-B) is not
implementation-safe yet. Deferred to v3 with the following gates:

| Phase | Deferred until |
| --- | --- |
| P-C (3-bucket expectimax) | P2 KO-band oracle lands AND an executable branch-context ABI is specified covering: full cache inventory, branch-local save/restore protocol, signed-16 product math, weight normalization, legality mask completeness, STAR1 selector-safety. |
| P-D (KO-only quiescence) | P-C ships and measures; broader P-D depends on P-C's V being cheap enough. |
| P-B (state-conditional bucket prior) | P5 (observation log + tendency counters) lands. P-B folds into P5 state. |

P-A is the only phase that ships from the v2 plan on this iteration.

---

## 8. Open taste calls

In order of consequence:

1. **S4 / P-A behavior delta acceptance.** Near-tie cases will differ.
   Same sign-off as the broader S4 line item in
   [hotspots.md:65,111-113](../audit/boss_ai_perf/hotspots.md). Cole's
   call.
2. **WRAM byte placement.** New `wBossAILookaheadRunningBest` adjacent to
   `wBossAILookaheadDepthCache` is the natural slot. Confirm or override.
3. **Audit naming.** The three new `check_lookahead_*.py` audits — fold
   into a single audit script vs three? Three is more diagnostic; one is
   less file churn. Default to three unless Cole prefers consolidation.

---

## 9. References

In-repo:
- [boss_ai_lookahead_2x_research_2026-05-25.md](boss_ai_lookahead_2x_research_2026-05-25.md) — v1 original
- [boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md) — GPT 5.5 Pro round-1 review
- [boss_ai_lookahead_2x_research_2026-05-25_v2.md](boss_ai_lookahead_2x_research_2026-05-25_v2.md) — v2 research
- [boss_ai_spec.md](boss_ai_spec.md) — canonical AI spec
- [POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md) — BOSSAI-003 architecture decision
- [audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md) — recent perf work + S4 item
- [audit/boss_ai_perf/baseline.json](../audit/boss_ai_perf/baseline.json) — cycle baseline
- [audit/boss_ai_perf/post_opt.json](../audit/boss_ai_perf/post_opt.json) — post-opt cycle counts
- [boss_policy_move.asm:5324-5419](../engine/battle/ai/boss_policy_move.asm) — driver to replace
- [boss_policy_move.asm:5455-5602](../engine/battle/ai/boss_policy_move.asm) — `BossAI_EvaluateActionLookahead` (unchanged by P-A)
- [boss_policy_move.asm:5422-5443](../engine/battle/ai/boss_policy_move.asm) — `BossAI_ApplySignedDeltaToScore` (saturation at 1, not 0)
- [engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm) — score convention SoT ("Lower is better")
- [constants/battle_constants.asm:72-88](../constants/battle_constants.asm) — lookahead constants
- [ram/wram.asm:2421-2492](../ram/wram.asm) — boss AI reserve

---

**End of v2.1.** Ready for Cole sign-off on the S4 behavior delta and
WRAM placement, after which implementation can proceed.
