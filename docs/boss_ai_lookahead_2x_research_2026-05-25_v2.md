# Boss AI Lookahead — candidate plan for reply-bucket lookahead (v2)

**Status:** research-only, read-only deliverable. No code changed. v2 dated 2026-05-26.
**Origin:** Cole asked for "how to make the look ahead for boss AI 2x as smart without
running up on ram issues or slowing down the turn more than 10%. use web search.
maybe look into chess."
**v1:** [boss_ai_lookahead_2x_research_2026-05-25.md](boss_ai_lookahead_2x_research_2026-05-25.md) — superseded; retained for audit trail.
**Cross-review:** GPT 5.5 Pro reviewed v1 (verbatim findings at
[boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md));
v2 incorporates the load-bearing fixes. §12 maps every v1 defect to its v2
resolution.
**Companion docs:**
[boss_ai_spec.md](boss_ai_spec.md),
[boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md),
[POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md),
[audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md),
[engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm) (score convention).

This is a **candidate plan**, not a shipping spec. It requires direct
measurement (§7) and the P2 KO-band oracle (from the
[ROM expansion roadmap](boss_ai_rom_expansion_2026-05-23_codex_task.md))
before P-C can ship.

---

## TL;DR

In ROI / dependency order:

1. **P-A — dynamic lower-is-better futility cutoff** on the N=4 beam.
   Replaces the static `initial_best + CAP` gate at
   [boss_policy_move.asm:5358-5419](../engine/battle/ai/boss_policy_move.asm)
   with a tight per-candidate cutoff against running best. **Evaluator-
   independent — can ship in parallel with P2.** Estimated saves
   ~75-225k T-cycles per turn. (§5.1)
2. **P2 — KO-band oracle** (already in the ROM expansion roadmap, not
   in this doc). Required precondition for P-C.
3. **P-C — three-bucket expectiminimax** with the §4 branch context
   contract. Implements the reserved `BOSS_AI_LOOKAHEAD_M = 3` as
   `PRESSURE / PRESERVE / ADVANCE` buckets. **Gated on P2 shipping
   first** and on the contract being honored. (§5.2)
4. **P-D — KO-only quiescence** at LATE tier. Resolves the
   horizon-effect failure class (setup one turn short of KO). (§5.3)
5. **P-B — state-conditional bucket prior**. Was "killer bucket" in v1;
   reframed to require board-state gating. Deferred to post-P5 or
   folded into P5 tendency counters. (§5.4)

**Honest delta vs the user's "≤+10% turn time" target:** P-A alone
saves cycles. P-C as currently sketched costs +12% to +35% on paper.
The headline "2x smarter at ≤+10%" is **not yet supported by the math**
and depends on direct measurement plus either a cheaper V (from P2) or
collapsing M=3→M=2. v2 framing: candidate plan + measurement gate.

---

## 1. What "lookahead" is today (factual)

Same architectural description as v1 — driver
([boss_policy_move.asm:5324](../engine/battle/ai/boss_policy_move.asm))
calls `BossAI_EvaluateActionLookahead` (:5455) for up to N=4 candidates,
which calls 10+ predicates plus `BossAI_ApplyMultiTurnProjection` (:5605).
`BOSS_AI_LOOKAHEAD_M = 3` reply buckets are reserved
([constants/battle_constants.asm:74](../constants/battle_constants.asm))
but never consulted today. v1 §1 captures the body structure correctly.

### Two facts v1 mishandled

**Score convention — LOAD-BEARING:**
[engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm) literally says
"Score each move of wEnemyMonMoves in wEnemyAIMoveScores. **Lower is
better.**" Helpers confirm:

- `BossAI_EncourageScoreHL` **decrements** toward 1 (encourage = lower).
- `BossAI_DiscourageScoreHL` **increments** toward 79 (discourage = higher).
- `BossAI_SelectMove` picks the **minimum**.
- Scores ≥ 80 are **blocked** (sentinel).

`BossAI_ClampSignedLookaheadDelta` + `BossAI_ApplySignedDeltaToScore`
([:5422-5443](../engine/battle/ai/boss_policy_move.asm)) follow the
convention: **positive delta worsens** score (move less likely);
**negative delta improves** score (move more likely). v1's "inversion"
footnote was a false alarm — the existing `.best_loop` correctly finds
the minimum, the `.eval_loop` cutoff correctly evaluates candidates
**within `CAP` of the best** (near-best beam), and the delta sign is
consistent. v1 misread the convention and called all of this inverted.

**Cycle units — fixed from v1:** The perf bench in
[audit/boss_ai_perf/](../audit/boss_ai_perf/) measures **T-cycles**
(the underlying 4.19 MHz Game Boy clock, not the 1.05 MHz M-cycle
clock).

| Scenario | Total T-cycles | ms @ 4.19 MHz |
| --- | --- | --- |
| mid_lead | 2,668,510 | ~636 ms |
| late_lead | 3,183,488 | ~759 ms |
| late_lookahead_heavy | 3,230,304 | ~770 ms |

Matches [hotspots.md](../audit/boss_ai_perf/hotspots.md)'s "~750ms
compute window." +10% of heavy late = +77 ms ≈ +323k T-cycles.

v1's "ms @ 1.05 MHz" framing was off by 4x (or read literally, by 1000x)
because 1.05 MHz is the M-cycle clock, not the T-cycle clock the bench
uses.

---

## 2. What "2x smarter" should operationally mean

Per GPT E14, a single aggregate "agreement with [best]" can hide
regressions. v2 requires stratified measurement:

- **Pairwise rank accuracy** on the
  [BOSSAI-004 preference corpus](../engine/battle/ai/POLICY_DESIGN.md):
  `best > bad`, `best > cheap`, `scary_good` not auto-penalized.
- **Probability-mass-on-best under fixed RNG seeds** (since
  `BossAI_SelectMove` is weighted-best-vs-second, not deterministic).
- **Scenario strata**: KO threshold, setup, switch/preserve, status,
  lock/recharge, revealed-priority.
- **Non-regression budget per stratum**: no individual stratum may
  regress more than 5%; no increase in `cheap` picks; no early-tier
  "too smart" leaks; no no-cheat violations.

Quantitative target: ~50% reduction in the gap to 100% agreement
**measured across all strata**, no individual stratum regressing >5%.

---

## 3. Domain analogs

Per GPT G20: v1 over-weighted chess as the primary inspiration. v2
demotes chess to **pruning vocabulary only** and elevates poker / RTS
micro AI / fighting-game AI as the structural analogs. Boss AI is
opponent modeling under variance with public info — closer to a poker
agent's decision shape than a chess engine's.

| Domain | What translates | Use in v2 |
| --- | --- | --- |
| **Poker** | Opponent modeling under variance; mixed strategies; public history → bucketed priors; avoiding overreaction to single observation. | **Primary analog for P-C bucket weights, P-B state-conditional prior, P5 tendency counters.** |
| **Fighting game / RTS micro** | Hard per-decision budget; legality masks before priors; utility-function-driven decisions. | **Primary analog for §4 contract shape and budget discipline.** |
| **Chess** | Futility pruning, quiescence search, razoring, history heuristic. | **Pruning terminology only** (P-A, P-D). |
| **MCTS / Go** | — | **Skip.** No fast simulator on SM83. |
| **Hanabi** | — | Cooperative info; not applicable. |

Citations in §11.

---

## 4. Branch context contract (REQUIRED before any P-C ASM)

Per GPT I24 — single most important addition. P-C calls
`V(candidate, bucket)` up to 3 times per candidate. Each call evaluates
a HYPOTHETICAL state where the player picks a different reply class
(PRESSURE / PRESERVE / ADVANCE). PRESERVE in particular hypothesizes a
switch — the player active species, typing, HP, status, and stages all
change. Today's per-turn caches assume those are turn-stable; under P-C
they are **branch-variable**.

**Without this contract, P-C will leak stale cache state between
buckets and silently produce wrong (potentially sign-inverted)
evaluations.** This is the AG-NN class of bug
(`feedback_ag_nn_clobber_class`) but harder to detect because the failure
is statistical rather than load-bearing-on-every-frame.

### 4.1 Branch-local state (must NOT leak between buckets)

The hypothetical reply may change:
- Player active species (PRESERVE → hypothetical switch-in).
- Player active typing (derived from species).
- Player active HP band (post-switch full, or post-recovery).
- Player active status (cleared on switch, induced by PRESSURE).
- Player active stat stages (cleared on switch, applied by ADVANCE).
- Field state (hazard ticks on hypothetical switch-in).

Caches keyed on any of these must be **invalidated at the top of each
`V(candidate, bucket)` call**:

| Cache | Source | Branch action |
| --- | --- | --- |
| `wBossAILastMatchupType` + `wBossAILastMatchupResult` | `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` ([boss_platform.asm](../engine/battle/ai/boss_platform.asm)) | Invalidate (set sentinel `$ff`) on PRESERVE entry. |
| `wBossAIShouldScoutPrereqCache` + `wBossAIShouldScoutThresholdCache` | `BossAI_ShouldScout` | Invalidate on PRESERVE entry. |
| `wBossAIPlausibleTypeMaskCache` + `wBossAILikelyTypeMaskCache` | `BossAI_ComputePlayerPlausibleTypeMask` | Invalidate on PRESERVE entry (active species changed). |
| `wBossAIPublicEnemyFasterCache` | `BossAI_PublicEnemyFaster` | Invalidate on PRESERVE entry (defender speed changed). |
| `wBossAIPrimaryThreatCache` | `BossAI_GetPrimaryThreatType` | Invalidate on PRESERVE entry. |
| `wTypeMatchup` (transient) | Various callers | Save/restore around each bucket call. |
| `wEnemyMoveStruct` | `AIGetEnemyMove_HL` | Per-candidate scope; bucket loop nested INSIDE candidate loop so this is invariant within bucket dimension. |
| `wCurSpecies` / `wCurPartySpecies` | Per-candidate | Save/restore if any V touches plausible-mask helpers. |
| `hBattleTurn` | Turn-direction probe | Save/restore around each bucket call. |

Bucket loop order: nested INSIDE candidate loop. Outer-to-inner:
candidate → bucket. This keeps `wEnemyMoveStruct` stable across the
3-bucket inner loop and concentrates the invalidation work on a known
boundary.

### 4.2 Branch-invariant state (safe to read from any bucket)

- Boss roster (party slots, levels, learnsets).
- Boss active species/level/HP/status/stages (the boss doesn't act yet).
- Boss revealed plan + `wBossAITier`.
- Public observation history from prior turns (seen species, revealed
  player moves committed BEFORE this turn).
- ROM-side tables (P2 KO oracle, type chart, base stats).
- `BOSS_AI_LOOKAHEAD_*` constants.
- Turn counter.

### 4.3 Forbidden reads (no-cheat invariant, carries forward)

From [boss_ai_spec.md §"Explicit No-Cheating Invariants"](boss_ai_spec.md):
hidden player party, unrevealed moves, hidden items, private stats,
this-turn player input, future RNG state. Plus v2-specific: the bucket
distribution itself must be derivable from public info, not from any
private knowledge.

### 4.4 Accumulator width contract (per GPT A3)

Signed 8-bit overflows with weighted bucket sums.

- Per-bucket V returns signed delta in `[-CAP, +CAP]`,
  `CAP = BOSS_AI_LOOKAHEAD_BONUS_CAP = 18`.
- Bucket weights sum to 8 (see §5.2).
- Worst case weighted sum: `8 × 18 = 144` — does NOT fit signed 8-bit
  (range -128..+127).

**Required**: accumulate weighted bucket sum in a 16-bit register pair
(`de` or `hl`). After the bucket loop, divide-by-8 (shift right 3) and
saturating-clamp back to signed 8-bit `[-CAP, +CAP]` before calling
`BossAI_ApplySignedDeltaToScore`.

Failure mode if not honored: wrap across bit 7 → sign inversion → AI
prefers worst moves. Same blast radius as AG-08
([CLAUDE.md §"farcall"](../CLAUDE.md)).

### 4.5 Legality mask contract (per GPT D11)

Before applying bucket weights, V checks whether the player is in a
forced-action / restricted-action state. If yes, bucket weights are
**masked** to the legal subset at root (candidate-invariant scope —
applies to all 4 candidates uniformly):

| Player state | Bucket mask (PRESSURE / PRESERVE / ADVANCE) |
| --- | --- |
| Outrage / Petal Dance / Thrash mid-lock | 8 / 0 / 0 (locked attack only) |
| Rollout / Fury Cutter ramp | 8 / 0 / 0 (locked attack, ramped power) |
| Hyper Beam / Sky Attack / Razor Wind / Skull Bash recharge | 0 / 8 / 0 (no action this turn) |
| Solar Beam / Sky Attack charge | 8 / 0 / 0 (locked attack release next) |
| Bide storing | Public counter visible; weight by phase. Storing → 0 / 8 / 0; release → 8 / 0 / 0. |
| Fly / Dig / Bounce semi-invuln | Charge turn 0 / 8 / 0; release turn 8 / 0 / 0. |
| Encore on revealed move | All weight collapses to the Encored move's bucket. 8 / 0 / 0 if PRESSURE; 0 / 8 / 0 if recovery/Protect; 0 / 0 / 8 if setup. |
| Disable on player's primary | Disabled bucket = 0; redistribute weight to remaining buckets proportionally. |
| Mean Look / Spider Web / partial-trap | PRESERVE-as-switch illegal; redistribute to PRESSURE + ADVANCE. |
| Perish Song count = 1 | Escape-urgent; weight 1 / 6 / 1. |
| Asleep / Frozen / Paralyzed-full / Confused-self-hit | Action-denial probability factored into per-bucket V as multiplicative damage=0 weight, NOT bucket mask change. |

The mask is candidate-invariant: computed ONCE at root from public
state, applied to all 4 candidates' bucket evaluation.

### 4.6 Required audits (gate P-C shipping)

1. **`tools/audit/check_bucket_cache_isolation.py`** — static scan:
   enumerate all reads of §4.1 caches from any code path reachable from
   V; assert each is either (a) preceded by an invalidate or save, or
   (b) keyed on bucket-variable state.
2. **`tools/audit/check_bucket_accumulator_width.py`** — symbolic
   check: max weight × max delta path produces values that fit the
   chosen register pair; final saturating clamp present.
3. **`tools/audit/check_legality_mask_coverage.py`** — assert every
   row in §4.5 has a corresponding case in the mask code.

---

## 5. The phases

### 5.1 P-A — Dynamic lower-is-better futility cutoff

**Sequencing**: ships first, parallel-OK with P2. Evaluator-independent.

**Definition**: replace the static cutoff at
[boss_policy_move.asm:5358-5419](../engine/battle/ai/boss_policy_move.asm)
with a dynamic cutoff against running best.

**Algebra (lower-is-better, signed delta in `[-CAP, +CAP]`):**

- `running_best` = minimum over all already-evaluated post-eval scores
  and not-yet-evaluated pre-eval scores. Monotonically non-increasing
  (adding any score to a min can only lower or hold it).
- For candidate `i` about to be evaluated, best-case post-eval score is
  `score[i] - CAP` (maximum upside, most-negative delta).
- **Skip candidate `i` if `score[i] - CAP >= running_best`.** It
  cannot improve to beat current best even with max upside.
- After evaluating candidate `i`, update running_best with its post-eval
  score.

**GPT A1 footnote, preserved here**: the EXISTING static cutoff
`score[i] > initial_best + CAP` is technically too aggressive under
signed deltas — a candidate at `initial_best + CAP + 1` could
theoretically catch up if the initial best worsens by `+CAP` and the
candidate improves by `-CAP`. The correct safe static bound would be
`initial_best + 2*CAP`. The DYNAMIC bound proposed here is strictly
tighter than either static version and is the recommended replacement.

**Implementation sketch:**

```text
; b = running_best (init 79)
; eval loop walks candidates by slot order; skips by futility bound
ld b, 79
.eval_loop_v2
  ld a, [de]                    ; move id
  and a
  jr z, .eval_done
  ld a, [hl]                    ; candidate score
  cp 80
  jr nc, .eval_next             ; blocked
  sub BOSS_AI_LOOKAHEAD_BONUS_CAP
  jr c, .can_win                ; underflow → score < CAP, can always reach 0
  cp b
  jr nc, .eval_next             ; score - CAP >= running_best → futile, skip
.can_win
  ; existing evaluator + ApplySignedDeltaToScore ...
  ld a, [hl]                    ; reload post-eval score
  cp b
  jr nc, .skip_update            ; new score >= running_best, no update
  ld b, a                        ; tighten running_best
.skip_update
  ; existing counter + trace ...
```

**Cost**: +1 register live across loop (`b`); ~10 extra T-cycles per
candidate; -1 push/pop pair eliminated. Net: roughly cycle-neutral on
no-skip path, big save on skip path.

**ROI**: estimated 0.5-1.5 evaluator skips per turn × ~150k T-cycles
each = ~75-225k saved per turn on heavy scenarios. **Requires
measurement** to confirm.

**Behavior delta**: identical for well-separated cases. Different
choice in near-tie cases where dynamic bound is tighter. Same S4
sign-off needed per
[hotspots.md:65,113](../audit/boss_ai_perf/hotspots.md).

**RAM cost**: 0.

### 5.2 P-C — Three-bucket expectiminimax (REQUIRES P2)

**Sequencing**: ships AFTER P2 KO-band oracle, AFTER §4 contract is
honored, AFTER §4.6 audits exist.

**Bucket naming** (per GPT B5): `PRESSURE / PRESERVE / ADVANCE` (not
v1's `ATTACK / PRESERVE / SETUP` — "stay and click fast attack" belongs
in PRESSURE, not collapsed into SETUP).

**Bucket definitions (public-info only):**

- `PRESSURE`: player's best **revealed** damaging move (incl. priority)
  into the current boss active; if none revealed, highest-EV guess from
  `wBossAILikelyTypeMaskCache`.
- `PRESERVE`: hypothetical switch to highest-confidence defensive seen
  species, OR player's revealed recovery / Protect move.
- `ADVANCE`: player's revealed setup / hazard / phazing / trap move.
  **No fallback to attack** — if no revealed advancement, weight is 0.

**Root weights** (per GPT B6 calibration):

| Tier | PRESSURE | PRESERVE | ADVANCE |
| --- | --- | --- | --- |
| EARLY | 6 | 1 | 1 |
| MID | 5 | 2 | 1 |
| LATE | 4 | 2 | 2 |

Sum = 8 for clean shift-by-3 math.

**Root prior adjustments** (candidate-invariant, computed once):

- If `BossAI_PredictPlayerSwitch >= 50`: shift +1 from PRESSURE to PRESERVE.
- §4.5 legality mask fires: weights replaced per mask table.
- Post-P5: P5 tendency counter modifier (bounded ±2 per weight).

**Per-candidate adjustments** (per GPT D13):

After the root prior, V applies small candidate-conditioned modifiers:

- Boss candidate is a likely KO move → +1 PRESERVE (player likely to
  switch to escape).
- Boss candidate is a setup move → +1 ADVANCE (player likely to set up
  in response or punish).
- Boss candidate is a self-locking commitment (Outrage, Hyper Beam) →
  +1 PRESERVE (player likely to switch to absorb).

Modifier cap: total ±2 weight per candidate (prevents pathological
per-candidate weight blowup).

**V(candidate, bucket) — consumes P2 KO-band oracle:**

```text
V(candidate, bucket) returns signed delta in [-CAP, +CAP] from:
  - P2.KO_band(candidate, defender_state[bucket])          ; from P2
  - P2.survival_band(defender_reply[bucket], boss_active)   ; from P2
  - existing predicate battery (HasAnyKOMove, ShouldScout,
    GetPrimaryThreatType, GetTypeThreatSeverityVsEnemyMon,
    SetupBoostHasFurtherValue, SetupTurnIsAffordable) BUT against
    branch-local defender state per §4
  - ApplyMultiTurnProjection rolled into V (no longer a separate call)
```

V signature carries a `bucket_id` argument so the predicates that
depend on defender state (`GetTypeThreatSeverityVsEnemyMon`, etc.)
read from the branch-local copy, not the live `wBattleMon*` slots.

**STAR1 pruning between buckets** (per GPT E15, treat savings as
upside not budget-critical):

```text
acc_16 = 0                                ; signed 16-bit
remaining_weight = sum(weights)
for bucket in [PRESSURE, PRESERVE, ADVANCE]:
    if weight[bucket] == 0: continue       ; masked out
    v = V(candidate, bucket)               ; in [-CAP, +CAP]
    acc_16 += weight[bucket] * v
    remaining_weight -= weight[bucket]
    ; STAR1 upper-bound: best-case remaining = remaining * (-CAP)
    best_remaining = remaining_weight * (-CAP)
    if (acc_16 + best_remaining) / 8 > (running_best - score[i]):
        break                              ; futile, skip remaining buckets
delta = saturating_clamp(acc_16 / 8, -CAP, +CAP)
ApplySignedDeltaToScore(delta)             ; existing helper
```

**Cycle cost (honest estimate, per GPT B4):**

- V cost ≈ 50-150k T-cycles per call (depends on KO-oracle path + cache
  invalidation overhead).
- 4 candidates × 3 buckets worst case = 12 calls.
- P-A skips ~1 candidate average; STAR1 prunes 0-1 buckets average
  (unknown without measurement).
- Estimated net: 400k-1.2M T-cycles added.
- Versus heavy-late baseline (3.23M): **+12% to +37%**.

**The headline ≤+10% is NOT supported on paper.** P-C ships only if
direct measurement (§7) confirms <+10%, or after one of:
- Faster V via fully-tableized P2 oracle.
- Aggressive STAR1 prune rate confirmed by measurement.
- Collapse M=3 → M=2 (merge PRESERVE+ADVANCE — degrades quality).
- Perf budget renegotiated.

**RAM cost**: 4 bytes in WRAMX bank-1 reserve (within the 9-byte free
count under trace; see [boss_ai_spec.md:794-808](boss_ai_spec.md)):

- `wBossAILastPlayerBucket` (1 byte, see §5.4)
- Bucket accumulator scratch (3 bytes signed-16 + flags; could be
  register-only with tight discipline).

Plus 1 bit for sweep-in-progress flag (§5.3) in existing bitmap byte.

**ROM cost**: 600-1000 bytes total (V dispatcher + bucket scoring +
STAR1 + cache invalidation calls). Lives in the P2 bank.

### 5.3 P-D — KO-only quiescence at LATE tier

**Sequencing**: ships AFTER P-C is measured and stable (per GPT F18,
KO-only first; broader P-D waits).

**Definition**: when V(candidate, killer_bucket) reports a KO is on the
table THIS TURN for either side, extend search by one synthetic ply
using the killer bucket only:

```text
if BossAI_HasAnyKOMove(candidate, defender_state[bucket]) or
   defender_has_KO_back_at(candidate, defender_state[bucket]):
    extension_V = V(candidate_followup, killer_bucket)
    final_V = blend(V_root, extension_V, weight=0.5)
```

Loud-node set (gates the extension):
- KO threat live (either direction).
- Sweep-in-progress flag set (boss has a setup move active and
  un-cashed).
- Priority-revenge-pending (revealed priority move + boss HP band).

Excluded from quiescence (these are legality-mask territory, not
quiescence): Outrage / Encore / recharge / charge / semi-invuln.

**Razoring complement** (per GPT C8): candidates that are both far
behind running_best AND non-loud explicitly skip P-D entirely.
Cheap safety net.

**Tier gate**: LATE only in v2 ship. MID expansion requires fixture
evidence per GPT F18.

**Cycle cost**: fires ~20-40% of turns; each fire ≈ 0.5× P-C cost.
Average overhead: ~50-150k T-cycles.

**RAM cost**: 1 bit in existing bitmap.

### 5.4 P-B — State-conditional bucket prior

**Sequencing**: ships AFTER P5 (observation log + tendency counters),
or folded into P5 entirely. Per GPT B7, isolated last-bucket bonus is
noise.

**Definition** (revised from v1's "killer bucket"): apply +1 weight to
the bucket the player picked last turn ONLY when:

- Same bucket was picked under the same coarse **pressure class** (HP
  band + threat class) the previous turn, AND
- Current board state is in the same pressure class.

**Implementation** (if not folded into P5):

- `wBossAILastPlayerBucket` (1 byte) — bucket id of last revealed
  player action.
- `wBossAILastBucketPressureClass` (1 byte) — coarse class id at the
  time the bucket was recorded.
- Update on `BossAI_RecordRevealedPlayerMove`. Cleared by
  `ClearBossAIState`.

**Cycle cost**: ~1-3k T-cycles.

**RAM cost**: 2 bytes (or 0 if folded into P5 state).

**Alternative**: if P5 ships first, P-B becomes a consumer of P5
tendency counter state instead of its own slice.

---

## 6. ROM-side data

P-A: 0 bytes (in-line refactor of existing driver).
P-C: 600-1000 bytes (V dispatcher + bucket scoring + STAR1) — lives in
the P2 bank alongside the KO oracle.
P-D: ~150 bytes (loud-node detector + extension call).
P-B: ~30 bytes (or 0 if folded into P5).

Total: under 1.5 KB. Comfortably inside the P2 bank allocation; well
under any of the 14 free ROM banks.

---

## 7. Budget accounting (honest)

| Phase | Δ T-cycles | % vs heavy late (3.23M) | Confidence |
| --- | --- | --- | --- |
| P-A | **−75k to −225k** | **−2% to −7%** | medium (depends on real evaluator skip rate) |
| P2 (precondition) | tracked separately in P2 spec | — | — |
| P-C | **+400k to +1.2M** | **+12% to +37%** | low (requires direct V measurement + STAR1 prune-rate measurement) |
| P-D | **+50k to +150k** | **+2% to +5%** | medium |
| P-B | **+1k to +3k** | negligible | high |
| **Net (P-A+P-C+P-D+P-B)** | **+375k to +1.125M** | **+12% to +35%** | **low until measured** |

**P-A alone meets the budget (in fact saves cycles).** P-C as designed
breaches +10% by 2x-25x its own estimate range.

**Measurement plan (smallest experiment per GPT B4):**

1. Hook PyBoy entry/exit on
   `BossAI_EvaluateActionLookahead` at
   [:5455-5602](../engine/battle/ai/boss_policy_move.asm); measure
   inclusive cycle distribution across 100+ fixture scenarios.
2. Add a compile-flag-gated no-op "call evaluator 3x per candidate
   with cache invalidation" branch; measure heavy-late cycles with the
   full §4 contract overhead included.
3. Tune STAR1 prune rate against measured V distribution.
4. Gate decision: ship P-C if measured cost ≤ +10%; else collapse
   M=3 → M=2 or defer.

**P-D and P-C ship only after direct measurement.** P-A ships
independently if S4 sign-off lands.

---

## 8. What to skip (and why)

- **Transposition tables** — Pokémon turns rarely transpose; cache
  overhead > value. Branch-local memoization per §4 is fine; cross-turn
  TT is not.
- **Null-move pruning** — zugzwang real (Outrage, Encore, last-mon,
  recharge, Bide, Perish, setup windows). Carve-out engineering not
  worth it.
- **MCTS / Monte-Carlo rollouts** — no fast simulator on SM83.
- **Aspiration windows** — no inherited turn-to-turn score signal.
- **LMR (Late Move Reductions)** — second depth knob; defer until
  P-A/P-C measured.
- **Raising HORIZON_LATE** — spec forbids broad game-tree search;
  quiescence is the targeted depth knob.
- **Per-bucket damage roll buckets (low/mid/high V)** — multiplies
  branches by 3 again (4×3×3 = 36 evals). P2's KO-band oracle supplies
  this info cheaper.
- **Unconditional last-bucket bonus** — per GPT B7, noise without state
  gating. P-B requires the §5.4 gating.
- **Broad P-D (mid or early tier)** — per GPT F18, LATE-only first.
- **Black-box learned policy in ROM** — POLICY_DESIGN.md forbids it.
  Offline-distilled transparent weights (per GPT G19) are a v3 question,
  not a v2 phase.

---

## 9. Verification

**Per-phase audits:**

| Phase | Mechanical audit | Behavioral check |
| --- | --- | --- |
| P-A | Cycle bench: heavy-late ≥3% drop. Top-N audit: actually-evaluated candidates = lowest-N. Trace parity except near-tie cases. | Existing fixture replay set; manual sweep of `[best]` labels. |
| P-C | §4.6 audits (cache isolation, accumulator width, legality mask coverage). Cache-isolation property test (synthetic bucket transitions). RNG-consumption parity test (per GPT E16; same discipline as the `ShouldScout` cache shipped 2026-05-25). | Stratified preference test per §2; save-state replay across real fights. |
| P-D | New audit `check_quiescence_loud_only.py`: extension fires only from the §5.3 loud-node set. | Horizon-effect fixtures: Agility-into-priority-revenge, setup-one-turn-before-KO; AI must now decline the trap. |
| P-B (post-P5) | `check_bucket_prior_state_gated.py`: bonus only applies under same-pressure-class repetition. | State-transition fixtures showing the bonus fires only when gated. |

**Cross-phase floor:**

- `make pokegold.gbc` — green.
- `check_release_smoke.py`, `check_farcall_hl_clobber.py`,
  `check_farcall_a_clobber.py`, `check_boss_ai_no_cheat.py`,
  `check_boss_ai_gating.py`, `check_boss_ai_trace_invariants.py`,
  `check_save_format_version.py` — all green.
- `python -m tools.damage_debugger.clobber_smoke` — pre-shipping per
  `feedback_ag_nn_clobber_class`. P-C changes V dispatch, which is an
  ABI surface change — this is non-negotiable.
- `python scripts/generate_dev_index.py --rom pokegold` — regenerate
  dev index.
- **p95 cycle bench with ≥10 samples per scenario** (per GPT E16; v1's
  3-sample bench is too thin for shipping claims).
- **Save-state replay suite** across real fights, not just synthetic
  fixtures.
- **Trace expansion**: extend `wBossAITraceLookaheadBonusTop` from 3
  bytes to 4 so all N=4 candidates appear in trace
  (per GPT A3 — v1 verification plan would miss the 4th candidate).

**"2x smarter" measurement** (stratified per §2):
- Pairwise rank accuracy across all strata.
- Probability-mass-on-best under fixed RNG seeds.
- Per-stratum non-regression budget (no individual stratum regressing
  >5%).

---

## 10. Open taste calls for Cole (ordered by consequence)

Per GPT H21 — reordered from v1's arbitrary ordering. Cole's input
matters most at the top.

1. **P-A futility cutoff sign-off** (= S4 in
   [hotspots.md:65](../audit/boss_ai_perf/hotspots.md)). The dynamic
   bound is strictly tighter than the existing static one; changes
   behavior in near-tie cases. **Highest consequence**: gates whether
   P-C ever sees the right candidate to evaluate.
2. **P-C ship/defer/collapse decision** after measurement. If P-C
   measures at +12-35% on real hardware, do we (a) collapse M=3→M=2,
   (b) renegotiate the +10% budget, or (c) defer P-C entirely until P2
   produces a much cheaper V?
3. **Quiescence loud-node set** (§5.3). KO-live, sweep-in-progress,
   priority-revenge-pending — are these the right "must not miss"
   moments? Easy to add paralysis-just-landed / sleep-just-landed /
   trap-mid-execution later if fixtures reveal AI still loops.
4. **Sequencing slot in the
   [ROM expansion roadmap](boss_ai_rom_expansion_2026-05-23_codex_task.md)** —
   does P-A/P-C/P-D fit between P2 and P3, or as its own track?
   Codex-pairing protocol implications.
5. **P-B state-gating strictness** — same-pressure-class repetition
   threshold. Low consequence relative to 1-4.

---

## 11. References

Chess engine pruning (terminology only):
- [Futility Pruning — Chessprogramming wiki](https://www.chessprogramming.org/Futility_Pruning)
- [Quiescence Search — Chessprogramming wiki](https://www.chessprogramming.org/Quiescence_Search)
- [Razoring — Chessprogramming wiki](https://www.chessprogramming.org/Razoring)
- [History Heuristic — Chessprogramming wiki](https://www.chessprogramming.org/History_Heuristic)
- [Principal Variation Search — Chessprogramming wiki](https://www.chessprogramming.org/Principal_Variation_Search)
- [Killer Heuristic — Chessprogramming wiki](https://www.chessprogramming.org/Killer_Heuristic)

Chance-node search:
- [Expectiminimax — Wikipedia](https://en.wikipedia.org/wiki/Expectiminimax)
- [Winands 2009 — ChanceProbCut: forward pruning in chance nodes (PDF)](https://dke.maastrichtuniversity.nl/m.winands/documents/CIG2009.pdf)
- [Rediscovering *-Minimax Search (Ballard 1983 revisited)](https://www.researchgate.net/publication/220962560_Rediscovering_-Minimax_Search)

Pokémon AI prior art:
- [PokéChamp — arXiv 2503.04094](https://arxiv.org/abs/2503.04094) —
  sampled-action minimax under constraints. Cited for direction
  (small action sets, opponent action sampling, shallow search with
  strong evaluator), NOT as validation of the exact N=4×M=3 design.
- [Metamon — arXiv 2504.04395](https://arxiv.org/abs/2504.04395) —
  offline RL on Pokémon Showdown logs. Frames Pokémon as stochastic
  imperfect-info game. Supports the offline-distilled evaluator
  approach (relevant for a future v3 considering G19's "learned
  evaluator, transparent weights" path).
- [Wang 2024 MIT thesis — RL+MCTS Gen 4 Random Battle (PDF)](https://dspace.mit.edu/bitstream/handle/1721.1/153888/wang-jett-meng-eecs-2024-thesis.pdf)
- [foul-play (pmariglia) — expectiminimax Showdown bot](https://github.com/pmariglia/foul-play)
- [Stanford CS221 — Optimal Battle Strategy in Pokémon (PDF)](https://web.stanford.edu/class/aa228/reports/2018/final151.pdf)

Opponent modeling (the primary v2 analog per GPT G20):
- [Pluribus — Brown & Sandholm 2019](https://www.science.org/doi/10.1126/science.aay2400) —
  multiplayer no-limit poker; public action history → bucketed opponent
  priors. The pattern P-C borrows.
- Cognitive hierarchy / level-k thinking literature (various; for the
  "don't overreact to single observation" intuition behind P-B's
  state-conditional gating).

In-repo:
- v1 reference: [boss_ai_lookahead_2x_research_2026-05-25.md](boss_ai_lookahead_2x_research_2026-05-25.md)
- GPT 5.5 Pro review of v1: [boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md)
- [boss_ai_spec.md](boss_ai_spec.md)
- [boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md)
- [POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md)
- [audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md)
- [audit/boss_ai_perf/baseline.json](../audit/boss_ai_perf/baseline.json)
- [boss_policy_move.asm:5320-5750](../engine/battle/ai/boss_policy_move.asm)
- [boss_platform.asm](../engine/battle/ai/boss_platform.asm)
- [constants/battle_constants.asm:72-88](../constants/battle_constants.asm)
- [engine/battle/ai/move.asm:2](../engine/battle/ai/move.asm) — score convention SoT

---

## 12. Changelog vs v1 (every GPT finding mapped to its v2 fix)

| GPT ID | v1 defect | v2 fix location |
| --- | --- | --- |
| A1 | Misread `.best_loop` as inverted (false alarm — lower is better) | §1 (explicit "Lower is better" note + helpers); §5.1 (no inversion claim; dynamic futility cutoff replaces static) |
| A2 | Misread delta sign as backwards (false alarm — same root cause) | §1 (correct semantics: positive delta worsens score) |
| A3 (cache contamination) | No analysis of per-turn caches under hypothetical buckets | §4.1 (full cache invalidation table) |
| A3 (signed overflow) | No accumulator width plan for weighted bucket sums | §4.4 (signed-16 accumulator + saturating clamp) |
| A3 (trace 3-of-4) | Trace only records 3 of 4 candidates; v1 verification plan would miss the 4th | §9 (trace expansion to 4 bytes) |
| A3 (N<4 ordering) | If N ever drops below 4, evaluator scans slot-order not score-order | §9 (top-N audit) |
| B4 (units) | "ms @ 1.05 MHz" off by 4x/1000x | §1 (corrected to T-cycles at 4.19 MHz; ~771 ms heavy late) |
| B4 (budget contradiction) | Headline ≤+10% contradicts own +10-20% row totals | §7 (honest +12-35%; framed as candidate plan; measurement gate) |
| B5 (bucket names) | ATTACK fallback bleeds into SETUP | §5.2 (PRESSURE / PRESERVE / ADVANCE; ADVANCE has no fallback) |
| B6 (weight calibration) | 6/2/0 too certain for early; 4/3/1 too thin on ADVANCE for late | §5.2 (6/1/1, 5/2/1, 4/2/2; modifier path from P5) |
| B7 (killer bucket) | Unconditional last-bucket bonus is noise | §5.4 (state-conditional gating: same pressure class for two consecutive turns) |
| C8 (PVS/futility/etc) | "Alpha-beta" overloaded; missed futility pruning, razoring, history heuristic | §3 (chess demoted to pruning vocab); §5.1 (P-A renamed "futility cutoff"); §5.3 (razoring complement) |
| C10 (PokéChamp cite) | PokéChamp cited as direct validation of N=4×M=3 | §11 (PokéChamp cited for direction; Metamon + ChanceProbCut added) |
| D11 (legality mask) | M=3 buckets treated as free-action; ignores Outrage/recharge/Encore/Disable/trap/semi-invuln | §4.5 (full legality mask table; mask applied before bucket weighting) |
| D12 (V is point estimate) | V at KO threshold is too coarse | §5.2 (V consumes P2 KO-band oracle; P-C gated on P2 first) |
| D13 (switch prediction) | One root scalar shifts all candidate weights | §5.2 (root prior + per-candidate modifier with cap ±2) |
| E14 (single metric) | Single aggregate "2x smarter" hides regressions | §2 (stratified pairwise rank + probability-mass + per-stratum budget) |
| E15 (STAR1 expectations) | STAR1 treated as 1/3 budget savior | §5.2 (STAR1 savings treated as upside; bucket-prune rate must be measured) |
| E16 (verification gaps) | Missing branch-cache audit, signed-overflow test, p95 perf, save-state replay, RNG parity | §4.6 (3 new audits); §9 (p95 ≥10 samples; save-state replay; RNG parity) |
| F17 (sequencing) | P-B sequenced before evaluator improvements | §5 (P-A → P2 → P-C → P-D → P-B; P-A can ship parallel to P2 — light pushback on strict serialization, P-A is evaluator-independent) |
| F18 (P-D scope) | P-D scope undefined; v1 said "LATE tier" without justification | §5.3 (LATE-only KO-only first; MID expansion gated on fixture evidence) |
| G19 (evaluator first) | Search-centric; under-weights evaluator quality | §5 sequencing makes P2 a hard precondition for P-C; §8 notes offline-distilled evaluator as a v3 question |
| G20 (chess overweighted) | Chess primary analog; missed poker/RTS micro | §3 (chess demoted; poker + RTS micro primary) |
| H21 (taste call ordering) | Calls ordered by Claude's narrative, not consequence | §10 (S4/P-A first; P-B last) |
| I22 ("2x" oversells) | Title and TL;DR claim ≤+10% / 2x without proof | Title ("candidate plan"); TL;DR explicit "not yet supported by math" + measurement gate |
| I23 (load-bearing in wrong place) | P-C as structural change; P2 as helpful precursor | §5 (P2 is hard precondition; P-C is consumer of P2's evaluator) |
| I24 (branch context contract) | No branch-local state model | §4 (full contract: state ownership, caches, accumulator width, legality mask, audits) |

---

**End of v2.** This document supersedes
[v1](boss_ai_lookahead_2x_research_2026-05-25.md). The GPT 5.5 Pro
critique anchored to v1 is at
[boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md).
Cole should ack §10 open taste calls before any phase implementation.
Phase implementation slices to be drafted as Codex task specs (per
`feedback_codex_task_specs_in_committed_doc`) once Cole green-lights.
