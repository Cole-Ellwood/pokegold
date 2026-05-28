# Boss AI Lookahead — making it ~2x smarter at ≤+10% turn time, zero RAM-bank-1 growth

**Status:** research-only, read-only deliverable. No code changed. Date 2026-05-25.
**Origin:** Cole asked for "how to make the look ahead for boss AI 2x as smart without
running up on ram issues or slowing down the turn more than 10%. use web search.
maybe look into chess."
**Companion docs (canonical, read before acting on this):**
[boss_ai_spec.md](boss_ai_spec.md),
[boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md),
[engine/battle/ai/POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md),
[audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md).

---

## TL;DR — the 4-move stack

In ROI order. Each item is justified below; budget accounting in §6.

1. **Use the reserved `BOSS_AI_LOOKAHEAD_M = 3` reply buckets.** The current
   evaluator considers exactly one implicit player reply (the threat-type
   scoring in `BossAI_EvaluateActionLookahead` at
   [boss_policy_move.asm:5564-5579](../engine/battle/ai/boss_policy_move.asm)).
   `M` is reserved in [constants/battle_constants.asm:74](../constants/battle_constants.asm)
   and explicitly noted as unused in
   [boss_ai_spec.md:355-358](boss_ai_spec.md). Adding a 3-bucket expectiminimax
   collapse (`attack / preserve / setup`) over the same predicate battery is
   the single biggest decision-quality unlock. **(chance nodes — §4.3)**
2. **Alpha-beta-style candidate cutoff on the N=4 beam.** This is "S4" from
   [audit/boss_ai_perf/hotspots.md:111](../audit/boss_ai_perf/hotspots.md);
   skip `BossAI_EvaluateActionLookahead` for any candidate whose base score is
   more than `BOSS_AI_LOOKAHEAD_BONUS_CAP` below the current best. It is
   semantically equivalent to alpha-beta with score-bound ordering. Frees
   roughly the cycle budget the M=3 expansion costs. **(§4.1)**
3. **Quiescence extension only on candidates that have a live KO threat.** The
   horizon-effect bug is the #1 Pokémon-AI failure mode — AI sets up one turn
   short of the KO it never sees. Today, every candidate gets the same flat
   `HORIZON_MID / HORIZON_LATE` projection cap; instead, give "loud"
   candidates (KO available / setup mid-sweep / sacrifice on the table) one
   extra synthetic ply. **(§4.4)**
4. **Killer-bucket prior from the previous turn's revealed action.** Free
   move-ordering bonus: whichever of the 3 reply buckets the player picked
   last turn becomes the default heaviest weight for this turn's expectation.
   Two bytes of WRAM scratch (already-budgeted reserve), no new persistent
   state. **(§4.2)**

What I'd **skip**: transposition tables, null-move pruning, MCTS, and any
horizon-extension that touches `HORIZON_LATE`. Reasons in §7.

---

## 1. What "lookahead" actually is today

A precise reading of the source, because the word "lookahead" is misleading
in this codebase. See [boss_policy_move.asm:5363-5419](../engine/battle/ai/boss_policy_move.asm)
for the driver, and `:5455-5702` for the body.

**Today's structure:**

```text
BossAI_ApplyLookaheadToTopMoveCandidates       (driver)
  for each of the top N=4 candidates by base score, while
      candidate_score >= best - BOSS_AI_LOOKAHEAD_BONUS_CAP:
    BossAI_EvaluateActionLookahead             (per-candidate scorer)
      computes upside `b` and downside `c` via:
        - BossAI_CurrentEnemyMovePressureScore (KO-band heuristic)
        - AICheckPlayer{Quarter,Half}HP_HL     (HP band gates)
        - BossAI_IsCurrentEnemySetupMove
        - BossAI_HasAnyKOMove                  (turn-cached)
        - BossAI_SetupBoostHasFurtherValue
        - BossAI_SetupTurnIsAffordable
        - BossAI_ShouldScout                   (turn-cached prereqs)
        - BossAI_GetPrimaryThreatType          (turn-cached)
        - BossAI_GetTypeThreatSeverityVsEnemyMon
        - BossAI_ApplyMultiTurnProjection
            (rolling depth-based delta — see below)
      delta = clamp(c - b, -CAP..+CAP)
      score[i] += delta
```

`BossAI_ApplyMultiTurnProjection` ([:5605-5702](../engine/battle/ai/boss_policy_move.asm))
is *not* a multi-ply state simulator. It is a flat scoring helper that adds an
upside or downside delta proportional to `.GetProjectionDepth` — which returns
0 (early), 3 (mid), or 4 (late) — gated on the same predicate set that
`EvaluateActionLookahead` already evaluated. The "horizon" parameter is a
*magnitude knob* on the projection bonus, not a ply depth. This is why
[audit/boss_ai_perf/hotspots.md:52-57](../audit/boss_ai_perf/hotspots.md) calls
out the redundant-predicate problem — the two helpers re-call five of the
same predicates.

**What is genuinely absent today:**

- **Reply modeling.** `BOSS_AI_LOOKAHEAD_M = 3` reply buckets are reserved
  ([constants/battle_constants.asm:74](../constants/battle_constants.asm))
  but never consulted. The closest thing is `BossAI_PredictPlayerSwitch`
  ([boss_policy_move.asm:3531](../engine/battle/ai/boss_policy_move.asm) per
  [hotspots.md:127](../audit/boss_ai_perf/hotspots.md)), which returns a
  single scalar 0-80 switch chance — collapsed into a single boolean reply
  prior at `:5677-5683`.
- **State simulation.** The "projection" adds a bonus per depth unit but
  never re-evaluates state under a hypothetical move + reply combination.
- **Chance nodes.** Damage rolls (Gen 2 multiplier 217-255/255 per
  `mechanics_changes_from_base.md` and the engine), accuracy, status proc
  rates, crit chance — all collapsed to point estimates.

So "make lookahead 2x smarter" against this baseline does not require *more*
search; it requires *any* real reply modeling at all, plus pruning so the
budget pays for itself. That is the chess-engine playbook in miniature.

**Current baseline cycle cost** ([audit/boss_ai_perf/baseline.json](../audit/boss_ai_perf/baseline.json),
after the 2026-05-25 turn-cache patch landed):

| Scenario | Total cycles | ms @ 1.05 MHz |
| --- | --- | --- |
| mid_lead | 2,668,510 | ~2.5 |
| late_lead | 3,183,488 | ~3.0 |
| late_lookahead_heavy | 3,230,304 | ~3.1 |

+10% headroom = ~320k cycles on the heavy late scenario.

---

## 2. What "2x smarter" should operationally mean

"Smarter" is fuzzy. The honest decompositions:

- **Reply-distribution coverage.** Today: 1 implicit reply considered. Target:
  3 (`attack / preserve / setup`). This is literally 3x more reply
  information; the smart-budget question is "how to spend ≤2x cycles to
  consume it." With alpha-beta candidate pruning the math closes — see §6.
- **Horizon-effect resolution rate.** Today: AI loops Agility past +6, sets up
  one turn before a KO it never sees. Quiescence extension at KO-threat-live
  nodes directly addresses this. Measurable via fixture replays in
  [tools/boss_ai_debugger/](../tools/boss_ai_debugger/) labeled `[bad]` or
  `[cheap]` per [POLICY_DESIGN.md §"Preference Corpus"](../engine/battle/ai/POLICY_DESIGN.md).
- **Public-info correctness floor.** Same as today. The "smart" gain must
  stay strictly inside the no-hidden-info rule
  ([boss_ai_spec.md §"Explicit No-Cheating Invariants"](boss_ai_spec.md)).

A defensible quantitative target: **fixture pairwise-preference accuracy goes
from current X% to ~2× the gap-to-100%.** If today the AI agrees with the
human label on 70% of `[best]` vs `[bad]` pairs, target ~85%. That's
operationally "twice as close to perfect."

---

## 3. The chess analog — what translates

Numbered references are URLs in §10.

| Chess technique | Pokémon mapping | Fits? | Why |
| --- | --- | --- | --- |
| Alpha-beta pruning | Skip candidate evaluator when base score gap > CAP | **Yes** | Free; perf doc S4. Cuts ~25% candidate work. |
| Iterative deepening | Score everything cheaply (already), deep-eval only top-K | **Yes (already partial)** | The current "rank, then evaluate top N" is shallow ID. Add anytime-cutoff. |
| Transposition table | Position-hash → eval cache | **No** | Pokémon turns rarely transpose; cost > value on this hardware. Skip. |
| PV move ordering | Best move from last iter goes first | **Yes (via ID)** | Free with ID. |
| Killer-move heuristic | Player's last-turn reply class becomes prior for this turn's reply distribution | **Yes** | Cheap, real-world Pokémon dynamic — players double-down. |
| History heuristic | Per-trainer-class running counter on which reply bucket the player picked | **Maybe (v2)** | Needs persistent WRAM, marginal lift, defer. |
| MVV-LVA | Order candidates by (expected damage × accuracy × KO_value) / risk | **Yes (already partial)** | The base move score already approximates this. |
| Quiescence search | Extend horizon ONLY when KO threat live, setup mid-sweep, or sacrifice on the table | **Yes** | Single biggest fix for the horizon-effect failure mode. |
| Null-move pruning | "What if the boss passes?" | **No** | Pokémon zugzwang is real (Outrage lock, Encore, last-mon). Risk > reward. |
| Late Move Reductions | Top 1-2 candidates at full depth, rest at reduced | **Maybe (v2)** | Pairs well with alpha-beta cutoff but adds a 2nd depth knob. Defer. |
| Aspiration windows | Center search bound on previous turn's chosen-move score | **No** | Boss AI is single-turn-rooted, no carry-over score to anchor on. |
| Expectiminimax + STAR1 | Chance node = 3 reply buckets; bound the contribution before expanding | **Yes — load-bearing** | This is the `LOOKAHEAD_M = 3` home. |
| MCTS | Random rollouts | **No** | Needs a fast simulator + thousands of rollouts. Not on 4M cycles. |

Citations: see §10. The single most directly relevant source for Pokémon at
small budget is **PokéChamp** ([arXiv 2503.04094](https://arxiv.org/abs/2503.04094)),
which converged on "depth-1 or depth-2 minimax + 3 sampled opponent actions
+ strong evaluator" — exactly the shape of `N=4 × M=3` this codebase already
reserves.

---

## 4. The four recommended phases (concrete)

### 4.1 Alpha-beta candidate cutoff (P-A)

**What:** add the classic alpha-beta lower-bound skip to the candidate
beam. Before calling `BossAI_EvaluateActionLookahead` on candidate `i`,
check `score[i] + BOSS_AI_LOOKAHEAD_BONUS_CAP >= running_best`. If not,
skip — candidate `i` cannot catch the running best even with the maximum
possible upside delta. Plus update `running_best` after each evaluator
call so candidate 0's delta tightens the cutoff for candidates 1-3.

**Side observation worth a separate look:** the existing `.best_loop` at
[boss_policy_move.asm:5341-5356](../engine/battle/ai/boss_policy_move.asm)
initializes `b = 79` and only updates `b = a` when `a < b` (`cp b; jr
nc, .best_next`). That makes `b` end as the **minimum** non-saturated
score, not the maximum. The cutoff at `:5375-5376` then skips candidates
whose score is more than `CAP` above that minimum — i.e. evaluates only
candidates **clustered near the worst**. This looks inverted vs. the
function name "ApplyLookaheadToTop..." and the chess analog. I did **not**
verify this is a bug — the audits are green and the AI ships, so either
(a) the inversion is intentional and I'm missing the reason, (b) other
scoring layers dominate so the inversion never materially decides, or (c)
this is a latent issue. **Recommend a separate dedicated read of
`:5341-5419` in isolation, with a fixture trace showing what scores
actually get evaluated, before P-A is implemented.** If it is a bug,
P-A becomes simpler: fix the `.best_loop` direction and tighten the bound
after each eval — and the AI gets meaningfully smarter for free, before
any of P-B/C/D ships.

**Cost:** in-line patch; one byte of register state (running best) held
across `.eval_loop`. Zero new WRAM. ~25-50 cycles per saved evaluator
call.

**Cycle ROI:** with the inversion resolved, expect 0.5-1.5 evaluator
skips per turn × ~150k cycles each = ~75-225k cycles saved per turn on
heavy scenarios.

**Behavior delta:** none in well-separated cases. Different choice in
near-tie cases where the second-best candidate's *post-lookahead* score
would have exceeded the first. This is exactly S4 in
[hotspots.md:65,113](../audit/boss_ai_perf/hotspots.md) and needs the
same taste sign-off.

### 4.2 Killer-bucket prior (P-B)

**What:** on `BossAI_RecordRevealedPlayerMove` (existing hook,
[boss_platform.asm](../engine/battle/ai/boss_platform.asm)), classify the
revealed move into one of the three reply buckets:

- `BUCKET_ATTACK`  — damaging move
- `BUCKET_PRESERVE` — recovery / Protect / status-cure
- `BUCKET_SETUP`   — stat-boost / hazard / scout / nothing

Store the bucket id in 1 byte: `wBossAILastPlayerBucket`. Initialize to
`BUCKET_ATTACK`. Cleared by `ClearBossAIState`.

**How it's used:** when the reply-bucket expectimax in §4.3 weights its 3
chance children, give the killer bucket +1 weight unit out of the prior
distribution. Tiny ELO bump but free — and it captures the well-known
human-player dynamic of "lock in on a plan once it's working."

**RAM cost:** 1 byte. There are 9 bytes free in the boss-AI reserve under
the trace build (per [boss_ai_spec.md:794-808](boss_ai_spec.md)), and an
unconditional 36 bytes without trace. Comfortably inside budget.

### 4.3 Three-bucket reply expectiminimax (P-C) — the structural change

This is the load-bearing change. Replaces today's implicit single-reply
threat-type scoring at
[boss_policy_move.asm:5564-5579](../engine/battle/ai/boss_policy_move.asm)
with a true expectation across 3 reply buckets.

**Bucket definition (public-info only):**

- `BUCKET_ATTACK`: the player's best **revealed** damaging move into the
  current boss active, OR if no damaging moves revealed, the highest-EV
  guess from `wBossAIPlausibleTypeMaskCache` (already computed).
- `BUCKET_PRESERVE`: switching to the highest-confidence defensive seen
  species (uses `BossAI_PredictPlayerSwitch` output that is already
  computed today), or the player's revealed recovery / Protect move if
  any.
- `BUCKET_SETUP`: the player's revealed setup move if any
  (Curse / Calm Mind / etc), else "stay and click a fast attack" as a
  degenerate setup.

**Weights** (3 bytes, sum to 8 for cheap shift math):

| Tier | ATTACK | PRESERVE | SETUP | Notes |
| --- | --- | --- | --- | --- |
| EARLY | 6 | 2 | 0 | Tier already disabled from heavy lookahead — only used if MID-gate lowered. |
| MID | 5 | 2 | 1 | Slight lean to attack; killer bucket adds +1. |
| LATE | 4 | 3 | 1 | Flatter, more genuine expectation. |

`BossAI_PredictPlayerSwitch` output (current scalar 0-80) is **the single
input** that should shift weights from ATTACK→PRESERVE — if the prediction
says >50, swap one weight unit from ATTACK to PRESERVE. This preserves the
existing prediction surface without adding a new one.

**Evaluation:**

```text
expected_score(candidate) =
   w_attack   * V(candidate, player_picks_ATTACK)
 + w_preserve * V(candidate, player_picks_PRESERVE)
 + w_setup    * V(candidate, player_picks_SETUP)
```

where `V(candidate, reply)` is the existing
`BossAI_EvaluateActionLookahead` body extended to read a reply hypothesis
from a single byte argument. The body is already 95% reply-implicit; the
extension is gating the upside `.late_reply` branch
([:5581-5593](../engine/battle/ai/boss_policy_move.asm)) on the reply
bucket and gating `ApplyMultiTurnProjection`'s `.check_switch`
([:5675-5695](../engine/battle/ai/boss_policy_move.asm)) on whether
`BUCKET_PRESERVE` was the assumed reply.

**STAR1 pruning** (chance-node alpha-beta,
[Ballard 1983 / Winands ChanceProbCut](https://dke.maastrichtuniversity.nl/m.winands/documents/CIG2009.pdf)):
between buckets, maintain a running upper bound. Once
`(remaining_weight * MAX_POSSIBLE_V) + accumulated < beta`, skip remaining
buckets. The existing `BOSS_AI_LOOKAHEAD_BONUS_CAP = 18` is the
`MAX_POSSIBLE_V` — known at compile time. ~1 in 3 candidate-bucket pairs
will skip on typical inputs, recovering most of the 3x evaluator cost.

**Cycle cost without pruning:** 3x the candidate evaluator. With STAR1:
~1.5-2x. With §4.1 candidate-cutoff: net ≈ 1.0-1.2x baseline. Detailed in
§6.

**RAM cost:** 3 bytes for weights (could be ROMX constants — see below);
1 byte for `wBossAILastPlayerBucket`. Net WRAM growth in bank 1: **0-1
bytes** depending on whether weights are constants or runtime-mutable.
Put the weight table in one of the 14 free ROM banks — see §6.

### 4.4 Quiescence-only horizon extension (P-D)

**What:** after the 3-bucket expectimax for candidate `i` lands, if any of
the following "loud-node" conditions is true, run **one extra synthetic
ply** with the bucket weights collapsed to the killer bucket only:

- `BossAI_HasAnyKOMove` returns true (KO line live this turn)
- `BossAI_SetupBoostHasFurtherValue` returned true AND a previous setup is
  already on the active (multi-turn sweep in progress — needs 1 new bit
  on `wBossAIBattleVolatileBitmap`)
- `BossAI_PlayerHasRevealedPriorityThreat` returned true AND boss HP band
  ≤ half (priority revenge sacrifice on the table)

For non-loud nodes, the search stops at the current expectimax depth.
This is the chess "quiescence search" pattern
([Chessprogramming wiki](https://www.chessprogramming.org/Quiescence_Search))
— don't extend through the calm parts of a search; do extend through the
moments where a single move flips the position.

**Direct effect:** resolves the horizon-effect bug — AI no longer sets up
one turn before a KO it never sees, no longer Agility-spams into a freshly
revealed priority threat.

**Cycle cost:** quiescence only fires on a fraction of candidates (~20-40%
in typical mid-game scenarios per the existing fixture replay data).
Per-fire cost ≈ 0.5x the bucket-expectimax cost (single bucket, not
weighted). Expected average overhead: 10-25% of baseline. With §4.1
recovering ~25%, net stays in the ≤+10% target.

**RAM cost:** 1 bit (sweep-in-progress flag in an existing bitmap byte).
Acceptable inside the trace-build 9-byte free count.

---

## 5. ROM-side data — fits the 14-bank budget

The reply-bucket weights, the STAR1 cap constants, and the bucket-classifier
table all want to live in ROMX. These naturally route to the existing P2/P3
in [boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md)
— specifically:

- The KO-band oracle work in P2 supplies a much more accurate `V(candidate,
  reply)` than today's heuristic, *especially* for the chance-node
  framework. The lookahead-2x stack proposed here is the *consumer* of P2;
  if P2 ships first, P-C above gets ~30% sharper evaluations free.
- The revealed-effect interaction matrix in P3 already plans to absorb the
  scattered bespoke effect handlers — those handlers are what populate the
  reply buckets. A unified P3 table is the natural home for "what bucket
  does revealed move X go in."

**Recommendation:** sequence P-A → P-B → P-C **after** P2 has shipped the
KO oracle, but ahead of P3/P5/P6/P7. P-D (quiescence) ships independently
of all of them. None of P-A through P-D blocks the dropped P1/P4 work.

ROM cost estimate:

- P-A: 0 bytes (in-line patch to existing driver)
- P-B: ~30 bytes (bucket-classifier table + 4-byte hook into
  `RecordRevealedPlayerMove`)
- P-C: ~500-1000 bytes (3-bucket evaluator + weight table + STAR1 bound
  helper)
- P-D: ~150 bytes (loud-node detector + single-ply re-evaluator)

Total well under 1 ROM bank. Lives comfortably inside the existing P2 bank
allocation, or a new bank if P2 lands first.

---

## 6. Budget accounting

**Cycle budget on heavy late scenario** (per
[audit/boss_ai_perf/baseline.json](../audit/boss_ai_perf/baseline.json)):

| Phase | Δ cycles (estimate) | Cumulative % vs current heavy-late (3,230,304) |
| --- | --- | --- |
| P-A: alpha-beta candidate cutoff (tightened bound) | **−100,000 to −200,000** | −3% to −6% |
| P-B: killer-bucket prior | **+1,000 to +3,000** | negligible |
| P-C: 3-bucket expectimax with STAR1 pruning | **+400,000 to +700,000** | +12% to +22% |
| P-D: quiescence extension (fires ~30% of turns) | **+50,000 to +150,000** | +2% to +5% |
| **Net** | **+350,000 to +650,000** | **+10% to +20%** |

The headline +10% bound is only achievable with all four pieces shipped.
P-C alone exceeds the budget; P-A + P-C together likely lands inside.
P-D pushes near the edge of the +10% bound and is the natural lever to
gate on tier — apply P-D only at LATE tier.

**RAM bank-1 budget** (per
[boss_ai_spec.md §"Runtime State Budget"](boss_ai_spec.md), 9 free bytes
under trace, 36 free without):

| Field | Bytes | Purpose |
| --- | --- | --- |
| `wBossAILastPlayerBucket` | 1 | Killer-bucket prior |
| `wBossAIBucketEvalScratch` | 3 | Per-bucket V accumulator (could be reg-only with care) |
| `wBossAISweepInProgress` | (1 bit) | Quiescence loud-node detector |
| Reply-bucket weights | 0 | ROMX (table) |
| Bucket classifier table | 0 | ROMX |

**Total new bank-1 WRAM: 4 bytes + 1 bit.** Comfortably fits the 9-byte
trace-build free count, leaves margin for unrelated growth.

If the bucket-eval accumulator is kept in registers (tight but achievable
on SM83 — `b`, `c`, `d` already used for upside/downside; can repurpose
`e` and `h` during the bucket loop), that drops to 1 byte + 1 bit.

**Verification against memory `feedback_ag_nn_clobber_class`:** this is a
hot-path battle-code change; any implementation must run
`python -m tools.damage_debugger.clobber_smoke` before declaring done.
The bucket evaluator dispatches `BossAI_EvaluateActionLookahead` 3x with
different hypothesized state — `EvaluateActionLookahead`'s register-clobber
contract must be respected on all 3 calls. This is exactly the kind of
ABI-changing fix that has bitten the codebase twice.

---

## 7. What I'd skip (and why)

- **Transposition table.** Chess gets ~3-5x speedup from TT because the
  same position is reached through many move orders. Pokémon turns rarely
  transpose at game-tree level — different move + reply combinations
  produce *different* state (different HP, status, stages, turn counter).
  The few transpositions that do exist (e.g. switch-out-switch-in with no
  damage taken) are statistically rare. Cost: ~16-32 bytes of WRAM bank-1
  reserve + a hash function. Not worth it.
- **Null-move pruning.** "Pass the turn" is unsafe in Pokémon for the same
  reason it's unsafe in chess endgames: zugzwang. Outrage-lock, Encore,
  last-mon, choice items all create positions where the AI literally
  cannot do better than its forced move. The carve-out logic to gate
  null-move safely would exceed its expected savings.
- **MCTS.** Needs a fast simulator (we don't have one in-ROM) and
  thousands of rollouts (we have 4M cycles). Wang 2024 MIT thesis hit
  1756 Glicko on Gen 4 with MCTS + PPO running on a server, not on a Game
  Boy. Skip. ([thesis](https://dspace.mit.edu/bitstream/handle/1721.1/153888/wang-jett-meng-eecs-2024-thesis.pdf))
- **Aspiration windows.** Boss AI is single-turn-rooted with no inherited
  score from the previous turn. The technique presupposes iterative
  deepening with a stable score signal across iterations; we don't have
  one.
- **Late Move Reductions.** Composes well with alpha-beta and quiescence,
  but adds a second depth knob and a re-search path. Defer to v2 until
  the P-A/B/C/D stack has shipped and been measured.
- **Raising HORIZON_LATE.** Spec is explicit
  ([boss_ai_spec.md:351-354](boss_ai_spec.md)): "Do not expand this into
  broad literal game-tree search. For example, 8 immediate actions times 4
  player replies over 5 turns is already more than 33 million terminal
  branches." Quiescence extension at loud nodes is the correct *targeted*
  depth knob.
- **TT keyed on (move_id, hp_band, status, stages).** Marginal — the
  existing turn-cache already memoizes the per-tick predicates. Adding
  cross-turn caching for boss AI is the wrong primitive: a different turn
  IS a different position in this domain.

---

## 8. Verification plan (when someone implements this)

Each phase is independently shippable and audit-checkable. No
implementation here — this section is what to wire up *if/when* Cole greenlights.

**Per-phase verification:**

| Phase | Mechanical audit | Behavioral check |
| --- | --- | --- |
| P-A | `audit/boss_ai_perf` re-bench: heavy-late must drop ≥3% | Trace parity on all 19 boss_ai_trace fixtures except 1-3 near-tie cases (re-baseline if needed). |
| P-B | `tools/audit/check_boss_ai_no_cheat.py` re-runs green (killer bucket is public info — revealed player move only) | Manually verify `wBossAILastPlayerBucket` is cleared on `ClearBossAIState`. |
| P-C | New audit `tools/audit/check_lookahead_expectimax_buckets.py` — verifies the 3 bucket reads only touch the allowed public-info caches. | `tools/damage_debugger.clobber_smoke` (load-bearing per §6); `tools/boss_ai_debugger` replay of ≥10 `[bad]`-labeled fixtures showing AI now picks the `[best]` move on each. |
| P-D | New audit `tools/audit/check_lookahead_quiescence_loud_only.py` — verifies the quiescence path can ONLY fire from one of the 3 loud-node conditions. | Specific horizon-effect fixtures: Agility-into-priority-revenge, setup-one-turn-before-KO, Outrage-into-resist — AI must now correctly decline the loud-node trap. |

**Cross-phase floor** (per CLAUDE.md):

- `make pokegold.gbc` — green build.
- `python tools/audit/check_release_smoke.py` — green.
- `python tools/audit/check_farcall_hl_clobber.py` + `check_farcall_a_clobber.py` — green.
- `python tools/audit/check_boss_ai_no_cheat.py` + `check_boss_ai_gating.py` + `check_boss_ai_trace_invariants.py` — green.
- `python tools/audit/check_save_format_version.py` — green (zero save-format change).
- `python scripts/generate_dev_index.py --rom pokegold` — regenerate dev index.
- `python -m tools.damage_debugger.clobber_smoke` — pre-shipping per `feedback_ag_nn_clobber_class`.

**"2x smarter" measurement:**

The BOSSAI-004 preference labels in
[engine/battle/ai/POLICY_DESIGN.md §"Preference Corpus"](../engine/battle/ai/POLICY_DESIGN.md)
are the taste source. Before P-A: measure the current AI's agreement
with `[best]` labels across the fixture set. After P-D: re-measure.
Target: ≥50% reduction in the gap to 100% (the "2× as close to perfect"
interpretation in §2).

If the gap reduction is below ~30%, the implementation is shy of the
target and either P-C or P-D needs revisiting. If above 60%, the
implementation outperformed the brief and the perf-budget envelope should
be re-examined to find out which phase is doing the heavy lift.

---

## 9. Open taste calls for Cole

These are the genuine taste-escalation items per CLAUDE.md:

1. **P-A behavior delta in near-tie cases is acceptable.** S4 in
   [hotspots.md:65](../audit/boss_ai_perf/hotspots.md) is gated on user
   sign-off. The tightened-bound version proposed here has the same
   theoretical behavior shift but lands cleaner because it's a fix to
   already-broken cutoff logic, not a new behavior change. Confirm
   acceptable.
2. **Killer-bucket strength.** The +1 weight unit out of 8 is a deliberately
   small lean. If Cole's intuition says Pokémon players double-down harder
   than that, bump to +2. If the lean should be opposite (players
   *diversify* against an AI that learns), drop to 0 and use the bucket
   only for prediction-display purposes.
3. **Quiescence loud-node set.** I picked 3 conditions: KO-line-live,
   sweep-in-progress, priority-revenge-pending. Cole's playtest taste
   should validate whether these are the right "must not miss" moments.
   Strong candidates I excluded: paralysis-just-landed, sleep-just-landed,
   trap-mid-execution. Easy to add post-baseline if early playtests show
   the AI still loops in those positions.
4. **Sequencing vs ROM-expansion roadmap.** P-A/B/C/D fits between
   [P2 (KO-band oracle)](boss_ai_rom_expansion_2026-05-23_codex_task.md)
   and P3 (revealed-effect matrix) cleanly. Confirm slotting in there is
   the right order, or whether this should be its own track.

---

## 10. References

Chess engine techniques:
- [Alpha-Beta — Chessprogramming wiki](https://www.chessprogramming.org/Alpha-Beta)
- [Quiescence Search — Chessprogramming wiki](https://www.chessprogramming.org/Quiescence_Search)
- [Quiescence search — Wikipedia](https://en.wikipedia.org/wiki/Quiescence_search)
- [Move Ordering — Chessprogramming wiki](https://www.chessprogramming.org/Move_Ordering)
- [Killer Heuristic — Chessprogramming wiki](https://www.chessprogramming.org/Killer_Heuristic)
- [Transposition Table — Chessprogramming wiki](https://www.chessprogramming.org/Transposition_Table)
- [Null Move Pruning — Chessprogramming wiki](https://www.chessprogramming.org/Null_Move_Pruning)
- [Aspiration Windows — Chessprogramming wiki](https://www.chessprogramming.org/Aspiration_Windows)
- [Late Move Reductions — Chessprogramming wiki](https://www.chessprogramming.org/Late_Move_Reductions)

Chance-node search:
- [Expectiminimax — Wikipedia](https://en.wikipedia.org/wiki/Expectiminimax)
- [Winands 2009 — ChanceProbCut: forward pruning in chance nodes (PDF)](https://dke.maastrichtuniversity.nl/m.winands/documents/CIG2009.pdf)
- [Rediscovering \*-Minimax Search (Ballard 1983 revisited)](https://www.researchgate.net/publication/220962560_Rediscovering_-Minimax_Search)

Pokémon-specific:
- [PokéChamp — arXiv 2503.04094](https://arxiv.org/abs/2503.04094) — depth-1/2 minimax + top-K sampled opponent actions + strong evaluator. Most directly relevant prior art.
- [Wang 2024 MIT thesis — RL + MCTS for Gen 4 Random Battle (PDF)](https://dspace.mit.edu/bitstream/handle/1721.1/153888/wang-jett-meng-eecs-2024-thesis.pdf)
- [foul-play (pmariglia) — expectiminimax Showdown bot](https://github.com/pmariglia/foul-play)
- [Stanford CS221 — Optimal Battle Strategy in Pokémon (PDF)](https://web.stanford.edu/class/aa228/reports/2018/final151.pdf)
- [Game Developer — Programming AI for Pokémon Showdown bot battle royale](https://www.gamedeveloper.com/programming/programming-ai-for-pokemon-showdown-bot-battle-royale-)

In-repo:
- [boss_ai_spec.md](boss_ai_spec.md) — canonical spec; especially "Decision Breadth And Play Budget" at lines 314-358.
- [boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md) — ROM-expansion plan; P-A/B/C/D fits between P2 and P3.
- [audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md) — recent perf work and S4 "candidate early-out" item.
- [audit/boss_ai_perf/baseline.json](../audit/boss_ai_perf/baseline.json) — cycle baseline.
- [engine/battle/ai/POLICY_DESIGN.md](../engine/battle/ai/POLICY_DESIGN.md) — BOSSAI-003 architecture decision (use unified scorer, not CFR rewrite).
- [engine/battle/ai/boss_policy_move.asm:5350-5750](../engine/battle/ai/boss_policy_move.asm) — current lookahead body.
- [constants/battle_constants.asm:72-88](../constants/battle_constants.asm) — lookahead constants including reserved `M = 3`.
