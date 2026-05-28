# GPT 5.5 Pro round-2 review of `boss_ai_lookahead_2x_research_2026-05-25_v2.md`

**Date:** 2026-05-26.
**Reviewer:** GPT 5.5 Pro (commissioned by Cole as third-LLM cross-review).
**Subject:** [boss_ai_lookahead_2x_research_2026-05-25_v2.md](boss_ai_lookahead_2x_research_2026-05-25_v2.md) (v2 of the proposal, which incorporated round-1 findings at [boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md)).
**Verdict:** "Redesign before shipping. v2 is a much better memo than v1, but P-C is still not branch-safe or budget-honest enough to become ASM; ship P-A only after fixing the sketch and measuring it."
**Outcome:** P-A shipped (see [boss_ai_lookahead_p_a_2026-05-26_v2.1.md](boss_ai_lookahead_p_a_2026-05-26_v2.1.md) for the impl spec actually shipped, which incorporated the K6/K7/J3 fixes from this review). P-C / P-D / P-B deferred to a future v3 that must address the load-bearing findings J2 (cache inventory), J3 (signed-product width), J4 (legality mask completeness), K8 (STAR1 vs best-vs-second selector), K7 (weight normalization), and K10 (pressure-class schema).

Verbatim transcript below. Round-2 review captures the durable constraints for any future P-C / P-D / P-B work; if a future session is about to draft v3 of the lookahead stack, read this in full first.

---

**Confidence: high** on score-sign/code-reading, cache inventory, and v2 follow-through. **Medium** on perf ranges because P-C cost still depends on real branch-local V implementation and P2 oracle shape. **Medium-high** on mechanics gaps; the uploaded mechanics doc does not enumerate Beat Up / Triple Kick in detail, so I am treating those as known Gen 2 move-effect hazards that v2 must explicitly audit, not as fully source-proven from the provided docs.

My bottom line: **v2 is a real improvement over v1 as a research memo, but it is not yet a safe implementation spec.** It fixed the headline framing and many conceptual errors. It did **not** fully close I24. The branch context contract is still too partial: it misses branch-sensitive caches, does not define weight normalization/saturation, does not cover product-width before accumulation, and lets STAR1 prune with a score bound that may be unsafe for the existing best-vs-second stochastic selector.

---

## J — Round-1 follow-through

### J1. §12 changelog row-by-row

v2's §12 table is at `01_proposal_v2.md:713-743`. The table is useful, but several rows overclaim. The most important overclaims are A3 cache contamination, D11 legality mask, D13 switch/weight modifiers, E15 STAR1, E16 audit coverage, and I24 branch context.

| GPT ID                          |                                        v2 landing | Verdict                                                                                                                                                                                                                                                                                                                           |
| ------------------------------- | ------------------------------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1                              |              `01_proposal_v2.md:68-85`, `272-298` | **Substantively fixed conceptually.** v2 now correctly says lower is better and that the old cutoff is a near-best beam. However, the §5.1 implementation sketch introduces new register/trace defects; see K6.                                                                                                                   |
| A2                              |                         `01_proposal_v2.md:78-85` | **Mostly fixed.** Positive delta worsens and negative delta improves are explicit. Incomplete only in naming discipline: v2 still uses "bonus" in `BOSS_AI_LOOKAHEAD_BONUS_CAP` and trace naming, but the sign semantics are now clear enough.                                                                                    |
| A3 cache contamination          |                       `01_proposal_v2.md:174-187` | **Incomplete.** §4.1 lists some caches but misses `wBossAIHasKOMoveCache`, `wBossAIPublicThreatCache`, `wBossAIRevealedPriorityCache`, `wBossAILookaheadDepthCache` classification, `wBossAIShouldScoutMatchupValue`, and the plausible-mask species/level keys. This is not cosmetic; these are real branch-contamination risks. |
| A3 signed overflow              |                       `01_proposal_v2.md:213-226` | **Incomplete.** It covers 16-bit accumulation and final clamp, but not the multiplication/product step. `weight × delta` can overflow before it ever reaches the 16-bit accumulator. See J3.                                                                                                                                      |
| A3 trace 3-of-4                 |                       `01_proposal_v2.md:622-624` | **Fixed as a verification requirement.** It says to extend trace from 3 bytes to 4. That is adequate at doc level.                                                                                                                                                                                                                |
| A3 N<4 ordering                 |                           `01_proposal_v2.md:601` | **Incomplete.** A "top-N audit" is listed, but v2 does not specify the implementation invariant: sort/select by score, not slot order, if `N < 4`. This is only a test wish, not a design fix.                                                                                                                                    |
| B4 units                        |                        `01_proposal_v2.md:87-103` | **Fixed.** v2 correctly identifies T-cycles and gives ~770 ms for heavy late.                                                                                                                                                                                                                                                     |
| B4 budget contradiction         |              `01_proposal_v2.md:48-52`, `537-565` | **Mostly fixed.** The ≤+10% claim is no longer asserted. But the +12–37% P-C range is still too optimistic on the upper bound; see L11.                                                                                                                                                                                           |
| B5 bucket names                 |                       `01_proposal_v2.md:347-359` | **Fixed.** PRESSURE / PRESERVE / ADVANCE is better, and ADVANCE no longer falls back to fast attack.                                                                                                                                                                                                                              |
| B6 weights                      |                       `01_proposal_v2.md:361-375` | **Partly fixed, new bug introduced.** The root rows are better than v1, but P5 ±2 and candidate modifiers lack saturation/renormalization. Weights can go negative or sum above 8. See K7.                                                                                                                                        |
| B7 killer bucket                |                       `01_proposal_v2.md:493-520` | **Incomplete.** Deferring P-B is right, and state gating is right, but "pressure class = HP band + threat class" is underdefined and unauditable. See K10.                                                                                                                                                                        |
| C8 pruning vocabulary           | `01_proposal_v2.md:130-142`, `272-298`, `481-483` | **Fixed conceptually.** Chess is demoted, P-A is futility, razoring exists. Implementation still needs signed-score care.                                                                                                                                                                                                         |
| C10 PokéChamp citation          |                       `01_proposal_v2.md:676-685` | **Fixed.** v2 now cites it for direction, not proof of exact N=4×M=3.                                                                                                                                                                                                                                                             |
| D11 legality mask               |                       `01_proposal_v2.md:232-254` | **Incomplete.** It covers many lock states, but misses Choice lock, Endure, Substitute as PRESERVE, Pursuit-on-switch, Beat Up, Triple Kick, Magnitude variance, and some action-denial/threshold states. See J4.                                                                                                                 |
| D12 point-estimate V            |            `01_proposal_v2.md:391-406`, `583-585` | **Partly fixed.** P-C is gated on P2 KO-band oracle and avoids roll-bucket explosion. But v2 does not specify what P2 must expose for multi-hit, variable-power, Pursuit/switch, Endure, or Substitute.                                                                                                                           |
| D13 switch prediction           |                       `01_proposal_v2.md:371-389` | **Incomplete / new defect.** Root prior + candidate modifier is the right shape, but modifier order, legality-mask reapplication, saturation, and sum-to-8 normalization are undefined.                                                                                                                                           |
| E14 metric                      |            `01_proposal_v2.md:109-124`, `626-630` | **Substantively improved.** Pairwise rank, probability mass, strata, and per-stratum budget are all good. It still needs cheap/no-cheat zero-tolerance and confidence intervals for small strata.                                                                                                                                 |
| E15 STAR1 expectations          |                       `01_proposal_v2.md:408-433` | **Framing fixed; algorithm suspect.** v2 says STAR1 savings are upside, not budget-critical. But the actual pruning condition and "break then use partial acc" need redesign. See K8.                                                                                                                                             |
| E16 verification gaps           |            `01_proposal_v2.md:256-266`, `597-624` | **Partly fixed.** Good floor additions, but the three P-C audits are too coarse and miss product-width, weight normalization, branch key invalidation, second-best pruning safety, and concrete cache inventory. See J5.                                                                                                          |
| F17 sequencing                  |   `01_proposal_v2.md:30-41`, `344-345`, `493-520` | **Acceptable with caveat.** P-A can run parallel with P2 because it is evaluator-independent. But it must not ship from the shown sketch.                                                                                                                                                                                         |
| F18 P-D scope                   |                       `01_proposal_v2.md:456-489` | **Partly fixed.** LATE-only and KO-only first is right. Loud-node set is undercomplete and "sweep-in-progress" is too vague. See K9.                                                                                                                                                                                              |
| G19 evaluator first             |   `01_proposal_v2.md:19-22`, `344-345`, `391-406` | **Mostly fixed.** P2 is now a hard P-C precondition. Good.                                                                                                                                                                                                                                                                        |
| G20 chess overweighted          |                       `01_proposal_v2.md:130-142` | **Fixed.** Poker/RTS micro are now primary analogs.                                                                                                                                                                                                                                                                               |
| H21 taste call ordering         |                       `01_proposal_v2.md:634-657` | **Fixed.** S4/P-A and P-C ship/defer are correctly ahead of P-B.                                                                                                                                                                                                                                                                  |
| I22 oversell                    |                    `01_proposal_v2.md:1`, `48-52` | **Fixed as framing.** Title says candidate plan; TL;DR says math does not support ≤+10%.                                                                                                                                                                                                                                          |
| I23 load-bearing in wrong place |     `01_proposal_v2.md:19-22`, `30-41`, `344-345` | **Mostly fixed at roadmap level.** P-A/P2 first is now the plan. P-C still needs redesign before it is implementation-safe.                                                                                                                                                                                                       |
| I24 branch context              |            `01_proposal_v2.md:148-230`, `232-266` | **Not closed.** This was the most important addition, and v2 made a good start, but §4 is not complete enough to protect an ASM implementation. See J2–J5.                                                                                                                                                                        |

---

### J2. §4.1 cache coverage against actual `wBossAI*Cache`

The source says `BossAI_ResetTurnCaches` clears these caches: `wBossAIHasKOMoveCache`, `wBossAIPublicThreatCache`, `wBossAIRevealedPriorityCache`, `wBossAIPrimaryThreatCache`, `wBossAIPublicEnemyFasterCache`, `wBossAILookaheadDepthCache`, `wBossAILastMatchupType`, `wBossAIShouldScoutPrereqCache`, plus `wBossAIShouldScoutMatchupValue`. That reset comment explicitly says these helpers rely on inputs being stable within one AI tick. P-C breaks that assumption. `10_source_boss_platform.asm:540-565`.

| Cache/state                                                         |                                                                                                                                               Source evidence | §4.1 coverage                       | Verdict                                                                                                                                                                                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------: | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `wBossAIHasKOMoveCache`                                             |                                         `10_source_boss_platform.asm:550`, `899-912`; uncached path scans enemy moves and calls pressure scoring at `916-956` | **Missing**                         | **Defect.** Branch defender HP/type/status changes can change KO pressure. Must invalidate or key per branch.                                                                                                                       |
| `wBossAIPublicThreatCache`                                          |                                        `08_source_boss_policy_move.asm:2994-3007`; uncached path reads revealed moves and active public typing at `3011-3066` | **Missing**                         | **Defect.** PRESERVE can change active species/moves/types, so public threat can change.                                                                                                                                            |
| `wBossAIRevealedPriorityCache`                                      |                                                                  `08_source_boss_policy_move.asm:3069-3082`; uncached path reads active used moves at `3086+` | **Missing**                         | **Defect.** PRESERVE can change active species' revealed moves. Priority-revenge logic becomes stale.                                                                                                                               |
| `wBossAIPrimaryThreatCache`                                         |                                                                                                                    `08_source_boss_policy_move.asm:5802-5821` | Included at `01_proposal_v2.md:183` | Good, but invalidating only on PRESERVE is too narrow if ADVANCE changes threat severity through stages/status later.                                                                                                               |
| `wBossAIPublicEnemyFasterCache`                                     |                                                                                                                    `08_source_boss_policy_move.asm:3650-3667` | Included at `01_proposal_v2.md:182` | Good for PRESERVE. Needs explicit branch-speed context if ADVANCE can model speed boosts/paralysis.                                                                                                                                 |
| `wBossAILookaheadDepthCache`                                        |                                                                                                                    `08_source_boss_policy_move.asm:5704-5726` | **Missing from §4.1**               | Safe as branch-invariant because it depends only on tier, but §4.1 was supposed to walk every cache. It should be listed under branch-invariant caches.                                                                             |
| `wBossAILastMatchupType` + `wBossAILastMatchupResult`               |                                           `10_source_boss_platform.asm:609-631`; key is move type only and assumes player types/substatus stable at `614-615` | Included at `01_proposal_v2.md:179` | Conceptually included, but action is underpowered: "invalidate on PRESERVE entry" is not the same as "top of each V call." Given how cheap correctness is relative to P-C risk, reset per bucket or key by defender type/substatus. |
| `wBossAIShouldScoutPrereqCache`                                     |                                                           `08_source_boss_policy_move.asm:6224-6237`, `6267-6285`; reset at `10_source_boss_platform.asm:557` | Partly included                     | Incomplete.                                                                                                                                                                                                                         |
| `wBossAIShouldScoutThresholdCache`                                  |                                                                                                         `08_source_boss_policy_move.asm:6241`, `6259`, `6268` | Included                            | Needs saturation/branch invalidation with prereq cache.                                                                                                                                                                             |
| `wBossAIShouldScoutMatchupValue`                                    |                                                            `08_source_boss_policy_move.asm:6239`, `6264-6265`; reset at `10_source_boss_platform.asm:558-564` | **Missing**                         | **Defect.** This is the cached side-effect value restored into `wTypeMatchup`. If not branch-local, cache hits literally restore the wrong branch's matchup.                                                                        |
| `wBossAIPlausibleTypeMaskCache`                                     | `08_source_boss_policy_move.asm:4792`, `4847`; `10_source_boss_platform.asm:1090`, `1123`, `1182`; spec defines it at `04_spec_boss_ai.md:567-574`, `598-605` | Included at `01_proposal_v2.md:181` | Partly fixed.                                                                                                                                                                                                                       |
| `wBossAILikelyTypeMaskCache`                                        |                    `08_source_boss_policy_move.asm:4858`; `10_source_boss_platform.asm:1096`, `1151`, `1214`; spec at `04_spec_boss_ai.md:572-574`, `598-605` | Included at `01_proposal_v2.md:181` | Partly fixed.                                                                                                                                                                                                                       |
| `wBossAIPlausibleTypeMaskSpecies` / `wBossAIPlausibleTypeMaskLevel` |                                                            `08_source_boss_policy_move.asm:4769-4780`; spec invalidation rule at `04_spec_boss_ai.md:609-614` | **Missing**                         | **Defect.** These are cache keys. Clearing only mask bytes is not enough if the species/level key still says "valid."                                                                                                               |

**J2 defect**

`01_proposal_v2.md / 177-187 / §4.1 cache table is incomplete / It omits live branch-sensitive caches and cache keys cleared by BossAI_ResetTurnCaches or used by plausible-mask recompute / Add a complete cache inventory with branch action for each: HasAnyKOMove, PublicThreat, RevealedPriority, PrimaryThreat, PublicEnemyFaster, LookaheadDepth, LastMatchup pair, ShouldScout prereq-threshold-matchup, Plausible/Likely masks plus species/level keys / Confidence high.`

---

### J3. §4.4 accumulator-width contract

The contract correctly notices that `8 × 18 = 144` does not fit signed 8-bit, and it requires a 16-bit accumulator at `01_proposal_v2.md:213-226`. But it does **not** cover the multiplication/product step.

Worst case:

`CAP = 18` from `11_constants_battle.asm:88`.

For max negative delta: `delta = -18`.

For max legal weight: `weight = 8`.

Correct product: `8 × -18 = -144`, i.e. 16-bit `$FF70`.

If an SM83 implementation does repeated 8-bit addition before widening:

`-18` as 8-bit is `$EE`.

`$EE × 8 mod 256 = $70`, which is `+112`, already sign-inverted before shift.

Then `$70 >> 3 = +14`, while the correct `-144 / 8 = -18`.

So §4.4 must require **signed 16-bit product formation**, not just a 16-bit final accumulator. The audit must check the actual multiply loop, not merely the accumulator register pair. This matters more because SM83 has no sign flag and only `z/nz/c/nc` branch conditions, so signed comparisons and signed shifts must be explicitly implemented. `18_asm_authoring_guide.md:52-57`.

**J3 defect**

`01_proposal_v2.md / 223-226 / Accumulator-width contract omits product-width contract / A naïve 8-bit weight×delta multiply can wrap before entering the 16-bit accumulator / Require sign-extend delta to 16-bit, multiply via 16-bit repeated add/sub, then arithmetic divide-by-8 and clamp; add product-level test cases for 8×-18 and 8×+18 / Confidence high.`

---

### J4. §4.5 legality mask completeness

v2's table at `01_proposal_v2.md:239-251` is a useful start, but it is not complete enough against Gen 2 commitment/lock states and the hack's mechanics.

What it covers well: rampage lock, Rollout/Fury Cutter, recharge, charge/release, Bide, semi-invuln, Encore, Disable, trapping, Perish count 1, and action-denial probabilities.

What is missing or under-specified:

1. **Choice lock.** Round 1 explicitly named Choice lock. v2 omits it. The hack has Choice items and move-lock state; legality must collapse to the locked move when the lock is public/action-enforced. If the item itself is hidden, the contract must say what public signal makes the lock usable.

2. **Endure.** The mechanics doc says Protect and Endure are priority 3, above ordinary priority moves. `17_mechanics_gen2.md:668-675`. Endure is a PRESERVE/survival reply, not an attack/progress reply. It must be a bucket classifier and a survival-band modifier.

3. **Substitute as PRESERVE.** v2's PRESERVE bucket includes switch, recovery, and Protect at `01_proposal_v2.md:356-357`, but not Substitute. The current lookahead already treats Substitute alongside Protect in scout logic at `08_source_boss_policy_move.asm:5555-5558` and projection at `5642-5645`; mechanics say Substitute blocks status, secondary status, crits, stat drops, and Toxic counter advancement at `17_mechanics_gen2.md:337-356`. It belongs in PRESERVE, not ADVANCE by default.

4. **Pursuit-on-switch.** Mechanics explicitly say Pursuit doubles BP on a switching target and checks switching flags at `17_mechanics_gen2.md:523-525`. In a PRESERVE bucket that hypothesizes a switch, a boss Pursuit candidate must get branch-local payoff. This is not a root legality mask; it is a candidate × bucket interaction that v2 does not specify.

5. **Magnitude variance.** Mechanics call out Magnitude as a real public damage threat and note Earthquake/Magnitude/Fissure hit Dig users at `17_mechanics_gen2.md:124-127`, `534-540`. Magnitude needs KO-band variance handling in P2/V, especially around Dig. It is not just a static PRESSURE move.

6. **Beat Up multi-hit.** Needs explicit no-cheat handling. Beat Up's damage/hit count involves party composition in Gen 2. The AI must not read hidden player party to model player Beat Up; it needs a public lower/upper band from seen species only, or treat unrevealed contributors as unknown.

7. **Triple Kick.** Needs multi-hit / per-hit accuracy / increasing-power handling in KO-band. Not a legality mask, but it is a V coverage issue around thresholds.

8. **Infatuation/action denial.** Constants include `SUBSTATUS_IN_LOVE` at `11_constants_battle.asm:285`; v2 includes sleep/freeze/full-para/confusion but not attraction. If Attract exists in the hack's move data, this belongs in action-denial probability.

9. **Perish count = 2.** v2 only hardcodes count 1. Count 2 is often already a loud/urgent planning boundary, especially with trap/forced switch windows.

**J4 defect**

`01_proposal_v2.md / 239-251 / Legality mask is not complete against commitment and branch-sensitive move effects / Missing Choice lock, Endure, Substitute-as-PRESERVE, Pursuit-on-switch, multi-hit/variable-power KO-band obligations, and some action-denial states / Split §4.5 into "legal action masks," "bucket classifiers," and "V/P2 move-effect coverage," then add explicit rows for each named mechanic / Confidence high.`

---

### J5. §4.6 audit granularity

The three audits at `01_proposal_v2.md:256-266` are the right **categories**, but they are too coarse to catch the likely bugs.

I would decompose them like this:

`check_bucket_cache_inventory.py`: enumerate every cache cleared by `BossAI_ResetTurnCaches` and every cache-like key, then require an explicit branch policy row.

`check_bucket_cache_isolation_paths.py`: static reachability from V to every cached helper, asserting reset/keying before use.

`check_bucket_context_restore.py`: verifies `wTypeMatchup`, `wEnemyMoveStruct`, `wCurSpecies`, `wCurPartySpecies`, `hBattleTurn`, and temp bytes restore on all exits.

`check_bucket_weight_normalization.py`: all bucket weights after root, legality, P5, and candidate modifiers are `0..8`, legal buckets only, sum exactly 8 unless explicitly using a different denominator.

`check_bucket_product_width.py`: specifically tests signed product formation before accumulation.

`check_bucket_signed_shift_clamp.py`: tests divide-by-8 behavior for negative values and final clamp.

`check_legality_mask_coverage.py`: every legal mask row represented.

`check_bucket_classifier_coverage.py`: revealed Protect/Substitute/Endure/recovery/setup/hazard/phaze/trap/Pursuit/etc. map to expected buckets.

`check_star1_second_best_safety.py`: proves pruning cannot change best-vs-second stochastic selection unless the behavioral delta is explicitly accepted.

---

## K — New defects introduced by v2

### K6. §5.1 P-A implementation sketch

The P-A algebra is mostly right; the sketch is not shippable.

The underflow branch at `01_proposal_v2.md:313-315` says "score < CAP, can always reach 0." That comment is wrong. `BossAI_ApplySignedDeltaToScore` saturates negative deltas at score **1**, not 0: see `08_source_boss_policy_move.asm:5428-5432`. The correct comment is "can reach the minimum score 1." This matters when `running_best == 1`: the candidate may only tie, not beat, and ties affect the weighted best-vs-second selector.

Register `b` is worse. Current lookahead uses `b` as evaluated-candidate count and trace index: `08_source_boss_policy_move.asm:5389-5407`. v2 repurposes `b` as `running_best` at `01_proposal_v2.md:303-322` but leaves "existing counter + trace" omitted at `324`. That cannot work. The current trace block checks `b < 3` and stores into `wBossAITraceLookaheadBonusTop[b]`; with `b = running_best`, it indexes trace by score. The current N-limit increments `b` and compares to `BOSS_AI_LOOKAHEAD_N`; with `b = running_best`, it corrupts the best score and terminates nonsensically.

Called-helper lifetime: `BossAI_EvaluateActionLookahead` itself pushes/pops `bc` at `08_source_boss_policy_move.asm:5465-5467` and `5599-5601`, so it preserves `b`. `BossAI_ApplySignedDeltaToScore` clobbers `c`, and current code already wraps it in `push bc` / `pop bc` at `5386-5388`. The real problem is not helper clobber; it is that v2 needs **two live values**: `running_best` and `eval_count/trace_index`.

**K6 defect**

`01_proposal_v2.md / 302-324 / P-A sketch reuses b for running_best while existing trace/N-limit uses b as evaluated-count / Trace indexes by score and N-limit corrupts running_best / Use separate storage: e.g. b=count and wBossAITemp=running_best, or c=count with a saved move-slot counter, then rewrite trace and N-limit explicitly / Confidence high.`

`01_proposal_v2.md / 313-315 / Underflow comment says candidate can reach 0 / ApplySignedDeltaToScore saturates at 1, so tie semantics differ when running_best is already 1 / Change bound/comment to minimum score 1 and decide whether tie-producing candidates may be skipped / Confidence high.`

---

### K7. §5.2 per-candidate weight adjustment

This is a new v2 defect.

Root LATE weights are `4/2/2` at `01_proposal_v2.md:361-369`. Switch prediction ≥50 shifts `+1` from PRESSURE to PRESERVE at `373`, producing `3/3/2`. A KO candidate then adds `+1 PRESERVE` at `381-382`, producing `3/4/2`, sum **9**, not 8. Yet the math still shifts right by 3 as if the denominator is 8 at `419-424`.

Now add legality mask order. If a trap mask fires at `249` and zeroes PRESERVE-as-switch, then the KO candidate can re-add `+1 PRESERVE` after the mask unless the mask is reapplied. That resurrects an illegal bucket.

Post-P5 is worse: `bounded ±2 per weight` at `375` can drive a 1-weight bucket negative, especially EARLY/MID ADVANCE or any masked-to-zero bucket. v2 defines no saturation behavior.

**K7 defect**

`01_proposal_v2.md / 371-389 / Bucket modifiers do not define saturation, re-mask order, or sum-to-8 renormalization / Weights can go negative, exceed sum 8, or re-add illegal buckets after legality mask / Define exact order: root weights → legality mask → candidate/P5 modifiers only on legal buckets → saturate each weight 0..8 → renormalize/remainder distribute to sum exactly 8; audit it / Confidence high.`

---

### K8. §5.2 STAR1 pruning sign under lower-is-better

The sign direction is **basically correct** if interpreted as signed math:

Candidate can still matter if:

`score[i] + best_possible_delta <= running_best`

So it is futile when:

`best_possible_delta > running_best - score[i]`

That matches v2's comparison at `01_proposal_v2.md:421`.

But three serious defects remain.

First, it requires signed comparison. SM83 has no sign flag and only `z/nz/c/nc` branches, so v2 must specify a signed 16-bit compare routine. `18_asm_authoring_guide.md:52-57`.

Second, the division of negative values must be specified. An arithmetic shift-right of negative values is not the same as truncation toward zero. For pruning, the bound should be **optimistic** for lower-is-better, or the prune can become unsafe.

Third, and most important: v2 says `break` and then computes `delta` from the partial accumulator at `421-424`. That can be acceptable for "cannot become best," but BossAI does not only choose deterministic best. It chooses best vs second-best using score-gap probabilities: 90%, 75%, or 60% best depending on gap at `08_source_boss_policy_move.asm:2889-2912`. A candidate that cannot beat the best can still become second-best or create a near-tie distribution. If STAR1 stops early and applies a partial delta, it may distort the second-best score and therefore the final RNG distribution.

**K8 defect**

`01_proposal_v2.md / 419-424 / STAR1 prune is best-only, but BossAI selection is best-vs-second stochastic / Pruning remaining buckets can still alter second-best gap and selection probabilities; using partial acc after break is not an exact value / Either compute exact values for all candidates that can affect second-best, return a conservative bound that cannot make the candidate look too good, or explicitly accept and test the stochastic-selection behavior delta / Confidence high.`

---

### K9. §5.3 P-D loud-node set

Current loud set at `01_proposal_v2.md:472-479`:

* KO threat live.
* Sweep-in-progress.
* Priority-revenge-pending.

That is a decent first cut, but not enough.

Add or clarify:

1. **Hazard about-to-fire.** If Spikes are set and PRESERVE predicts a switch into lethal or near-lethal chip, that is a loud node. The source already treats Spikes as a strategic pressure object in move scoring, and v2 itself says hypothetical field state can include hazard ticks at `01_proposal_v2.md:172`.

2. **Status counter boundary.** Sleep counter at one denied action remaining, Perish count 2→1, Toxic/Leech/Sand chip crossing KO band, and paralysis just applied can all flip "setup is safe" vs "cash out now."

3. **Trap + Perish / trap-mid-execution.** v2 says trap-mid-execution can be added later at `01_proposal_v2.md:648-651`, but that is exactly the kind of one-turn horizon edge quiescence exists for.

4. **Sweep-in-progress is too broad.** "Boss has a setup move active and un-cashed" at `473-475` should become "boost changes KO/speed/survival band or player has a public revenge answer." Otherwise P-D fires on calm boosts and burns budget.

I would not add every status as loud. Add only status/counter states that cross an action-denial, speed-order, or KO/survival threshold.

---

### K10. §5.4 pressure class

Not auditable as written.

v2 says same coarse pressure class means "HP band + threat class" at `01_proposal_v2.md:502-504`. That is not enough to implement or audit. It does not say whether the class includes boss HP, player HP, speed relation, public KO band either direction, revealed priority, trap/perish, screens, hazards, weather, or active species.

Minimum auditable class should be a byte or two with explicit fields, for example:

`player_hp_band`, `boss_hp_band`, `public_threat_severity`, `boss_has_ko_band`, `player_has_ko_band`, `speed_relation`, `revealed_priority_flag`, `trap/perish flag`, `hazard_pressure flag`.

**K10 defect**

`01_proposal_v2.md / 499-512 / "Pressure class" is underdefined / P-B audit cannot verify "same class" if the class has no field contract / Define a bit-packed public pressure-class schema and update/clear rules, or fold entirely into P5 tendency counters / Confidence high.`

---

## L — Budget honesty

### L11. Is +12% to +37% still optimistic?

Yes. The lower bound is plausible only if V is cheap, branch-local invalidation is minimal, P-A skips reliably, and STAR1 prunes usefully. The upper bound is too low.

Post-opt heavy late is `3,230,304` T-cycles in `13_perf_post_opt.json:82-88`. Current profile still shows expensive helpers: `BossAI_ApplyScoutMoveBias` at 164,645 cycles/call, `BossAI_CurrentEnemyMoveHasKOPressure` at 30,120, pressure score at 28,840, threat severity at 20,246, and damage dominance at 19,404 in `14_perf_profile.json:9-49`.

My current ±2σ estimate for **P-C net after P-A savings but before P-D**:

* **Low:** +650k T-cycles, about **+20%**.
* **Center:** +1.1M T-cycles, about **+34%**.
* **High:** +1.75M T-cycles, about **+54%**.

If P-D is added, add another +50k to +200k depending on loud-node frequency.

Why higher than v2? Because branch isolation removes many current cache-hit assumptions. A branch-local V cannot freely reuse `HasAnyKOMove`, public threat, priority, matchup, and scout prereq caches across hypothetical defenders. v2's +37% upper bound is basically "8 extra V calls × 150k" with little allowance for branch setup, cache rewarming, signed math, trace, and second-best-safe pruning.

### L12. Measurement plan sufficiency

v2's plan at `01_proposal_v2.md:551-565` is a good minimum experiment, not a ship gate.

It must add:

* p95/p99 full-turn timing for `AIChooseMove`, not only evaluator entry/exit.
* A no-op branch that uses the real branch-context ABI: save/restore, invalidation, weight math, and trace paths.
* Separate release and trace builds; trace expansion can perturb cycles.
* Measured STAR1 prune rate by stratum.
* P2 oracle integrated timing, not a stub.
* Cache-hit/miss counters per branch-sensitive cache.
* Second-best distribution check: probability mass on best/second before/after pruning.
* At least 10 samples per scenario, as v2 already says at `01_proposal_v2.md:618-619`; I would use 30+ for p95.

### L13. If P-C measures at +25% net

Pick **(d) Redesign V to be ~30% cheaper before P-C.**

Do not collapse M=3→M=2 first. Merging PRESERVE and ADVANCE destroys the whole reason to use reply buckets: "switch/recover" and "setup/hazard" are strategically opposite. Do not renegotiate +10% yet; Cole's original constraint was load-bearing. Do not defer P-C entirely if the failure is a costed V problem; P-A-only is fine as an interim ship, but the correct path for the smarter stack is cheaper V.

My call: ship P-A separately if it measures cleanly, then redesign V/P2 until P-C lands under budget.

---

## M — Stratified metric

### M14. Is §2 defensible?

Yes, it is defensible. Pairwise rank + probability mass + per-stratum non-regression is much better than v1's single aggregate. It correctly accounts for `BossAI_SelectMove` being stochastic best-vs-second rather than deterministic argmin. The weighted final selector is visible in `08_source_boss_policy_move.asm:2889-2912`.

Still add these axes:

* Cheap-pick count: **zero tolerance** for new `cheap` increases, not merely 5%.
* No-cheat and early-tier leak: zero tolerance.
* Legality/forced-state stratum: lock/recharge/Encore/Disable/trap/Endure/Substitute/Pursuit.
* Selection entropy / near-tie distribution: ensure "smarter" does not become deterministic.
* KO-band calibration: around 0%, 25%, 50%, 75%, 100% KO probability.
* Regression severity: losing one rank among equal "good" moves is not same as choosing `[bad]`.

### M15. Is 5% right?

For **rank/probability metrics**, 5% is reasonable as a first budget if each stratum has enough fixtures/seeds.

For **realized RNG pick rates**, 5% is too tight on small strata unless you use confidence intervals. The selector's 60/75/90% best-pick thresholds mean random-seed variance can look like a regression if sample sizes are thin.

For **cheap/no-cheat/early-tier-too-smart**, 5% is too loose. Those should be zero or "must be manually approved."

I would use:

* No-cheat: 0.
* New `cheap` picks: 0 unless explicitly approved.
* Per-stratum pairwise rank: ≤5% with minimum sample size.
* Probability mass on best: ≤5 percentage-point drop with confidence interval.
* Rare strata: absolute-count threshold, not percent.

---

## N — Sequencing

### N16. P-A parallel with P2?

Acceptable, with conditions.

v2's "P-A can ship in parallel with P2" at `01_proposal_v2.md:30-35`, `272-340` is a fair pushback on my stricter round-1 framing. P-A is evaluator-independent and can create budget. But the implementation sketch must be rewritten first, and instrumentation/trace expansion should land with it.

Order I would approve:

1. Trace expansion to 4 candidates.
2. Inclusive lookahead measurement.
3. Correct P-A implementation with separate `running_best` and `eval_count`.
4. P2 KO-band oracle.
5. P-C only after §4 is a real ABI.

### N17. P-B deferred to post-P5?

Right call.

P-B should not ship earlier as behavior. It can ship earlier as **logging only**: record last bucket and candidate pressure-class fields into trace or P5 observation state. But no +1 weight until P5 defines the pressure class and tendency counters.

---

## O — Final verdict

### O18. Did v2 close the round-1 verdict?

Partly, but not enough.

Round 1 said: "scope is wrong, see I23: ship instrumentation, P-A, and P2 first; redesign P-C around a branch-safe evaluator contract."

v2 fixes the **scope framing**: it now calls itself a candidate plan, admits ≤+10% is not proven, makes P2 a hard precondition for P-C, and adds §4. That is real progress.

But v2 does not close the **branch-safe evaluator contract**. §4 is still missing cache inventory, cache keys, product-width math, weight normalization, legality-mask completeness, branch-class schema, and second-best-safe pruning.

So: **verdict softened, not closed.** P-A/P2 sequencing is acceptable. P-C remains redesign-before-ASM.

### O19. New ship / redesign / defer verdict on v2

**Ship P-A only after fixing K6 and measuring it.**

**Defer P-C. Redesign §4 and §5.2 before any implementation.**

**Defer P-D until P-C/V is measured, except possibly a tiny KO-only guard if fixtures prove a specific horizon bug.**

**Defer P-B to P5/logging.**

### O20. Single most important thing v2 still needs to do differently

Turn §4 from a narrative contract into an **executable branch-context ABI**:

`ReplyContext` fields, complete cache inventory, legal read set, branch-local save/restore, weight normalization, signed product math, and exact pruning/selection semantics.

No P-C ASM until that exists.

---

## Defect list in requested format

| File                |    Line | Issue                                     | Why                                                                                       | Fix                                                                                      | Confidence  |
| ------------------- | ------: | ----------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ----------- |
| `01_proposal_v2.md` | 177-187 | Incomplete branch cache table             | Missing branch-sensitive caches and plausible-mask keys                                   | Add full cache inventory from `BossAI_ResetTurnCaches` plus plausible key bytes          | High        |
| `01_proposal_v2.md` | 179-183 | "Invalidate on PRESERVE entry" too narrow | Contract says top of each V call, but table only invalidates on PRESERVE                  | Specify per-bucket reset/keying, or prove branch-invariant per cache                     | High        |
| `01_proposal_v2.md` |     180 | Missing `wBossAIShouldScoutMatchupValue`  | Cache hit restores this into `wTypeMatchup`; stale value crosses buckets                  | Include with ShouldScout prereq/threshold cache                                          | High        |
| `01_proposal_v2.md` | 213-226 | Product-width not specified               | `8 × -18` can overflow 8-bit before accumulation                                          | Require signed 16-bit product formation and test it                                      | High        |
| `01_proposal_v2.md` | 239-251 | Legality mask incomplete                  | Misses Choice lock, Endure, Substitute, Pursuit-on-switch, multi-hit/variance obligations | Split into legal masks, bucket classifiers, and V/P2 move-effect coverage                | High        |
| `01_proposal_v2.md` | 258-266 | Audits too coarse                         | Would miss product overflow, weight normalization, second-best STAR1 bug                  | Decompose audits as in J5                                                                | High        |
| `01_proposal_v2.md` | 302-324 | P-A sketch reuses `b` incorrectly         | Existing trace/N-limit uses `b` as eval count                                             | Use separate count and running_best storage; rewrite trace explicitly                    | High        |
| `01_proposal_v2.md` | 313-315 | Underflow comment says reaches 0          | Score helper saturates at 1                                                               | Update bound/comment and decide tie behavior                                             | High        |
| `01_proposal_v2.md` | 371-389 | Weight modifiers lack saturation/order    | Weights can go negative, sum >8, or re-add illegal bucket                                 | Define modifier order, legal-bucket mask, saturate 0..8, renormalize sum=8               | High        |
| `01_proposal_v2.md` | 419-424 | STAR1 only proves cannot be best          | Existing selector also cares second-best probability                                      | Exact-evaluate second-best candidates or return conservative bound and test distribution | High        |
| `01_proposal_v2.md` |     421 | Signed compare unspecified                | SM83 lacks signed branch conditions                                                       | Add signed 16-bit compare helper contract                                                | High        |
| `01_proposal_v2.md` | 472-479 | Loud-node set incomplete                  | Hazards/status-boundaries/trap-perish can be horizon-flip nodes                           | Add threshold-based loud states; narrow sweep-in-progress                                | Medium-high |
| `01_proposal_v2.md` | 502-504 | Pressure class undefined                  | P-B cannot be audited                                                                     | Define bit-packed public pressure-class schema or fold into P5                           | High        |
| `01_proposal_v2.md` | 537-549 | P-C upper budget optimistic               | Branch-local invalidation likely raises V cost above 150k                                 | Revise estimate to ~+20–54% net until measured                                           | Medium-high |

---

## Top 3 NEW changes I'd make to v2

1. Replace §4.1 with a complete table of every cache/key touched by `BossAI_ResetTurnCaches`, plausible-mask recompute, and V-reachable helpers. Each row must say: branch-invariant, reset-per-bucket, key-extended, or forbidden.

2. Rewrite §5.2 weight math: explicit modifier order, legal-bucket mask reapplication, saturate each weight to `0..8`, renormalize to sum exactly 8, and audit `weight × delta` as signed 16-bit before accumulation.

3. Rewrite STAR1 around the actual selector. Either evaluate exact scores for anything that can affect second-best, or make the prune return a conservative bound that cannot improve a candidate's final selection probability.

## Top 3 risks v2 STILL underrates

1. **Cache contamination is broader than matchup/scout.** KO, public-threat, priority, plausible-mask keys, and restored `wTypeMatchup` are all branch-sensitive.

2. **Second-best stochastic selection makes pruning harder.** "Cannot beat best" is not enough when final move choice depends on best-vs-second score gap.

3. **Budget blowout from branch-safe correctness.** The exact work needed to make P-C correct—cache invalidation, context restore, signed math, P2 oracle calls—pushes the likely upper bound well past +37%.

## One-sentence overall verdict

**Redesign before shipping.** v2 is a much better memo than v1, but P-C is still not branch-safe or budget-honest enough to become ASM; ship P-A only after fixing the sketch and measuring it.
