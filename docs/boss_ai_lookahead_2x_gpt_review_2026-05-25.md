# GPT 5.5 Pro adversarial review of `boss_ai_lookahead_2x_research_2026-05-25.md`

**Date:** 2026-05-25.
**Reviewer:** GPT 5.5 Pro (commissioned by Cole as third-LLM cross-review).
**Subject:** [boss_ai_lookahead_2x_research_2026-05-25.md](boss_ai_lookahead_2x_research_2026-05-25.md) (the original v1 proposal).
**Verdict:** "Scope is wrong, see I23: ship instrumentation, P-A, and P2 first; redesign P-C around a branch-safe evaluator contract before shipping the '2x smarter' stack."
**Outcome:** v1 retained on disk for reference; [boss_ai_lookahead_2x_research_2026-05-25_v2.md](boss_ai_lookahead_2x_research_2026-05-25_v2.md) supersedes it incorporating these findings.

The review text below is verbatim from GPT 5.5 Pro. Preserved on disk so future readers can audit v2's response against the original critique.

---

I'm going to be blunt: Claude found one real-looking code smell, but then partly misread the project's score convention. The proposal is directionally interesting, but it is overselling both correctness and budget. The biggest hidden risk is not RAM; it is cache invalidation and score-sign discipline once you introduce hypothetical reply buckets.

## A. Correctness of the code reading

### A1

**Confidence:** high.

**Answer:** The flag trace confirms the narrow claim that `.best_loop` computes the minimum non-saturated score. It does not confirm the proposal's conclusion that this is inverted.

In this AI, lower score is better. The platform helpers prove it: `BossAI_EncourageScoreHL` decrements the score toward 1, while `BossAI_DiscourageScoreHL` increments it toward 79; scores `>=80` are treated as blocked. `BossAI_SelectMove` also initializes best score to `$ff` and accepts a candidate only when `score < best`, so the "best" move is the minimum score, not the maximum.

Line-by-line for `06_source_boss_policy_move.asm:5341–5356`:

`ld b, 79` sets the initial best-score ceiling to the worst legal non-blocked score.

`ld a, [hl]` loads the candidate score.

`cp 80` computes `a - 80`. On SM83, `jr nc` branches when there is no carry, meaning `a >= 80`. So blocked scores skip.

`cp b` computes `a - b`. Carry is set when `a < b`. `jr nc, .best_next` skips when `a >= b`. Therefore `ld b, a` executes only when the current score is smaller than the current best. That is a minimum scan. SM83 only has `z/nz/c/nc` branch conditions, and carry is the unsigned less-than flag for `cp`.

Then `06_source_boss_policy_move.asm:5362–5376` does this: `threshold = best_min + BOSS_AI_LOOKAHEAD_BONUS_CAP`; later `cp [hl]` compares `threshold - candidate_score`; `jr c` skips when `threshold < candidate_score`. In other words, it evaluates candidates whose score is `<= best + cap`. Since lower is better, this is a near-best window, not a near-worst window.

So: not inverted. Not a bug. Not vestigial. It is a static near-best beam cutoff. The proposal's "minimum" observation is correct; its "clustered near the worst" interpretation is wrong.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.1 / Misreads lower-is-better score semantics after correctly noticing the min scan / A future implementer may "fix" the driver in the wrong direction and make lookahead evaluate bad moves / Rewrite §4.1 to say "best = minimum legal score; existing cutoff evaluates candidates within cap of the best; proposed S4 should be a dynamic lower-is-better futility bound" / Confidence high.`

`06_source_boss_policy_move.asm / 5362–5376 / Static one-cap cutoff is not a safe alpha-beta bound once deltas can be signed / A candidate more than +18 worse than the initial best can still overtake if the best is penalized +18 and the candidate is rewarded -18 / For P-A, skip only when candidate_best_possible = base_score - CAP is still >= running_best_after_delta; otherwise use a conservative 2*CAP bound / Confidence medium-high.`

### A2

**Confidence:** high.

**Answer:** The delta sign is not backwards. The user's intuition is right only if "higher score" meant better. Here higher score is worse.

`BossAI_EvaluateActionLookahead` initializes `b` as upside and `c` as downside, then computes `a = c - b` before clamping. If downside exceeds upside, the signed delta is positive. `BossAI_ApplySignedDeltaToScore` sends positive deltas to `.positive`, where it adds the delta to `[hl]`, making the move score worse. Negative deltas go through the two's-complement path and subtract from `[hl]`, making the move score better.

`BossAI_ClampSignedLookaheadDelta` does not flip the sign. It checks bit 7, converts negative to absolute magnitude, clamps, then converts back to negative; positive values are just capped.

So the math is coherent:

`more downside than upside → positive delta → score increases → move less likely`

`more upside than downside → negative delta → score decreases → move more likely`

The actual defect is naming. "Bonus" is misleading in a lower-is-better signed-delta system.

**Defect found?**

`01_proposal_lookahead_2x.md / §1 and §4.3 / Calls the signed adjustment a "bonus" and describes it as score += delta without stating lower-is-better / This invites exactly the sign-inversion bug Cole is worried about when P-C adds weighted V values / Rename the proposal variables to signed_penalty_delta, upside_reward, downside_penalty, and explicitly state "positive delta worsens score" / Confidence high.`

### A3

**Confidence:** high for the first three; medium for the rest until measured.

**Answer:** Yes. The proposal missed several sharper hazards.

The biggest one: P-C's hypothetical reply buckets break the current per-turn caches. `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` caches by `MOVE_TYPE` only because the current player types and substatus are assumed turn-stable. That assumption is false inside a PRESERVE/switch reply hypothesis. If one bucket evaluates "player stays as current active" and another evaluates "player preserves by switching," the same move type can have different effectiveness. A cache keyed only by move type will leak one bucket's matchup into another. `BossAI_ShouldScout` also caches turn-stable prereqs and restores `wTypeMatchup` on hit; that can become stale under hypothetical reply state.

Second: weighted expectimax with weights summing to 8 can overflow signed 8-bit math. Current deltas are clamped to `[-18,+18]`. A weighted sum can reach `8 * 18 = 144`, which does not fit signed 8-bit. If P-C accumulates in `a`, `b`, or `c` naïvely before shifting, it can wrap across bit 7 and invert meaning.

Third: if `BOSS_AI_LOOKAHEAD_N` is ever reduced below 4, the driver does not actually evaluate the top N moves. It scans move-slot order and increments the evaluated count only for moves passing the static threshold. With `NUM_MOVES = 4` and `N = 4`, this is mostly harmless. With `N = 3`, it becomes a quiet ordering bug.

Other misses: trace only stores three lookahead bonus bytes even though `N = 4`; the proposal's verification plan would miss the fourth candidate. The proposal also ignores side effects on `wEnemyMoveStruct`, `wTypeMatchup`, `hBattleTurn`, `wCurSpecies`, and temp bytes across hypothetical bucket evaluations. This codebase has a documented history of register/ABI bugs in battle code, including same-bank caller breakage from tiny "safe" changes.

**Defect found?**

`08_source_boss_platform.asm / BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem / Cache key is MOVE_TYPE only / P-C hypothetical switch buckets make defender typing non-stable, so cached matchup can cross-contaminate reply branches / Either bypass this cache in hypothetical evaluation, include defender-type/substatus in the key, or reset branch-local caches per bucket / Confidence high.`

`01_proposal_lookahead_2x.md / §4.3 / Weighted expectimax has no accumulator-width plan / Sum-of-8 weights times ±18 exceeds signed 8-bit range / Use 16-bit signed accumulation or shift/divide after each bucket with explicit saturation tests / Confidence high.`

`06_source_boss_policy_move.asm / 5391–5396 / Trace records only first three evaluated lookahead deltas while N is four / P-C/P-A verification can silently miss the fourth candidate / Expand trace storage or explicitly document "trace top 3 only" and add a separate full audit trace for lookahead work / Confidence high.`

## B. Soundness of the proposal

### B4

**Confidence:** medium; I'd need to measure `BossAI_EvaluateActionLookahead` inclusive cost directly.

**Answer:** The headline is not believable as written. The proposal's own budget table estimates net `+350k` to `+650k` cycles, which it labels `+10%` to `+20%` against the current heavy-late `3,230,304` cycle scenario. That already contradicts "≤+10%." The post-opt perf file gives heavy late at `3,230,304`, so +10% is only about `323k` cycles.

There is also a unit bug in the proposal's "ms @ 1.05 MHz" framing. `3,230,304 / 1,050,000 ≈ 3.08 seconds`, not `3.1 ms`. If the benchmark's "cycles" are Game Boy CPU T-cycles at about 4.19 MHz, then `3.23M` is about `771 ms`, which matches the perf notes' "~750ms compute window" story. But the proposal's table is still off by three orders of magnitude if read literally.

My back-of-envelope for P-C:

Current heavy late is about `3.23M` total. The current profile after caching still shows expensive primitives: `BossAI_CurrentEnemyMovePressureScore` around `28.8k` per call, `BossAI_GetTypeThreatSeverityVsEnemyMon` around `20.2k`, `BossAI_ApplyDamageDominanceBias` around `19.4k`, and scout-related paths can still be very expensive depending on cache state.

A three-bucket model adds two extra reply evaluations per candidate. With four candidates, that is up to eight extra branch evaluations. If a branch costs `50k`, P-C costs `400k`. If a branch costs `100k–150k`, P-C costs `800k–1.2M`. STAR1 can help, but with only three buckets and small bounded scores, expecting it to reliably erase one third of the work is optimistic.

So Claude's `400k–700k` estimate is calibrated as a lower-to-middle estimate, not a safe budget. It becomes believable only if P-C uses branch-local caches correctly, orders buckets well, and skips candidates aggressively. It does not support a ≤10% claim yet.

Smallest experiment: hook `BossAI_EvaluateActionLookahead` entry/exit directly at `5455–5602`, because the existing profile's `BossAI_ApplyLookaheadToTopMoveCandidates = 24 cycles` is obviously not inclusive enough to budget P-C. Then add a no-op "call evaluator 3x per candidate" branch behind a compile flag and measure heavy-late with and without cache resets.

**Defect found?**

`01_proposal_lookahead_2x.md / §1 and §6 / Cycle-to-ms conversion is wrong or unit-ambiguous by ~1000x / Bad units produce false confidence about turn lag / State whether perf counts T-cycles, M-cycles, or emulator cycles; convert with the correct clock; remove "3.1 ms @ 1.05 MHz" / Confidence high.`

`01_proposal_lookahead_2x.md / §6 / Headline says ≤+10% while own net estimate is +10–20% / The proposal does not meet its stated constraint on paper / Reframe as "research target; must measure; P-D is gated off unless P-A savings are real" / Confidence high.`

### B5

**Confidence:** medium-high.

**Answer:** Three buckets are the right budget shape, and they match the spec's intended `stay/attack`, `preserve/switch`, and `greed/setup` reply buckets. The spec explicitly says `BOSS_AI_LOOKAHEAD_M = 3` should be used for three player reply buckets, not more AI candidate plays.

But I would rename and tighten them:

`PRESSURE`: damaging attacks, priority, immediate status pressure, Counter/Mirror Coat threat.

`PRESERVE`: switch, Protect, recovery, Rest, defensive stall.

`ADVANCE`: setup, hazards, phazing, trapping, greed.

I would not split ATTACK into damage vs priority as a fourth always-on bucket. Priority is a tactical flag inside PRESSURE. It matters only when revealed and when boss HP/speed makes it relevant. A two-bucket model is too blunt because it merges "switch/recover" with "Dragon Dance/Spikes," which are strategically opposite.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3 / SETUP fallback says "stay and click a fast attack" / That collapses ATTACK into SETUP and muddies the bucket semantics / Make SETUP/ADVANCE only cover board-advancing non-immediate lines; fast attack belongs in ATTACK/PRESSURE / Confidence medium-high.`

### B6

**Confidence:** medium; this should be tuned from fixtures.

**Answer:** The proposed weights are acceptable as cold-start gut constants, but not as a final policy.

`6/2/0` early is too certain. Even early players can set up, heal, or switch. If early lookahead is enabled at all, `6/1/1` is safer. For mid, `5/2/1` is fine. For late, I would start with `4/2/2`, not `4/3/1`, unless `BossAI_PredictPlayerSwitch` is high. Late-game good players do not only attack or preserve; they greed when the board is safe.

The better architecture is compile-time default weights plus current-fight observation priors from P5's observation log/tendency counters. The roadmap already plans a public observation log and tendency counters in WRAMX-2, using post-resolution public facts rather than hidden input. That is the right home for adaptive weights.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3 / Treats bucket weights as fixed constants / Fixed priors cannot capture Cole's actual playstyle or per-fight observed behavior / Use compile-time defaults only as fallback; let P5 current-fight public tendency counters shift weights with caps / Confidence medium.`

### B7

**Confidence:** medium.

**Answer:** Closest answer: **(d) useless as written**, but salvageable.

The chess "killer move" analogy is weak here. Pokémon player actions are highly board-contingent. A player who Protected last turn may attack this turn. A player who switched last turn often cannot or should not switch again. A player who set up last turn may now cash out. So "last bucket +1" is mostly noise unless conditioned on repeated opportunity.

If you keep it, +1 out of 8 is the maximum I would allow. I would require either "same bucket used two comparable turns in a row" or "same bucket used under the same pressure class." Then +1 is fine. +2 or +3 is too much. Subtracting the last bucket is also too clever; many real players double down, but good players diversify when punished.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.2 / Unconditional last-bucket bonus / Pokémon actions are state-contingent, so last turn's bucket is not strong evidence this turn / Gate the bonus on repeated comparable board states or move it into P5 tendency counters / Confidence medium.`

## C. Missing techniques

### C8

**Confidence:** medium-high.

**Answer:** The proposal covered the obvious chess terms, but it did not sort them by actual fit cleanly enough.

PVS and null-window search are mostly not worth implementing literally. Principal variation search depends on strong move ordering and uses narrow/null windows for non-principal moves; on a four-move root, the practical translation is simply "evaluate the current best first, then ask whether later candidates can beat it." That is P-A/futility, not full PVS. The chess definition of PVS as null-window searches after the first move supports the analogy, but the full machinery is overkill here.

Futility pruning is the best chess analog for P-A. If a candidate's best possible improvement cannot beat the incumbent, skip it. That maps directly to lower-is-better score bounds. Chess futility pruning is specifically about skipping moves near the horizon that cannot raise alpha; here it becomes "candidate_base - max_upside cannot beat running_best."

Late move pruning is distinct from late move reduction. LMP skips late, quiet, badly ordered moves entirely. This can fit only after the driver actually sorts candidates by score. LMR, by contrast, evaluates late moves at reduced depth and may re-search; I would not add that yet.

Check/threat extensions map well: KO threat, revealed priority, recharge, Encore/Disable lock, Perish/trap, rampage, and semi-invulnerable states are Pokémon's "checks." This is exactly where quiescence should fire.

History heuristic is better than killer bucket. Track public current-fight tendencies: switch under pressure, protect/recover loops, greedy setup, status fishing, low-HP sack acceptance. That is P5 and is more Pokémon-native than chess killer moves.

Internal iterative deepening is already partly present: score all moves cheaply, then look ahead near-top candidates. A tiny version could order buckets by cheap static prior before expensive V, but do not add a second iterative layer until P-C works.

Razoring is useful: near-leaf candidates that are both far behind and non-loud should skip P-D entirely. It is safer than broad LMR.

**Defect found?**

`01_proposal_lookahead_2x.md / §3 / Treats "alpha-beta" as the main pruning analogy / The exact fit is futility pruning with lower-is-better signed bounds / Rename P-A to root futility cutoff and specify the bound algebra / Confidence high.`

### C9

**Confidence:** high.

**Answer:** Yes, rejecting broad transposition tables and broad null-move pruning is the right call.

Pokémon rarely transposes in the chess sense. Different move/reply orders usually change HP, status, lock state, boosts, counters, and switch history. A cross-turn TT would spend scarce RAM on stale equivalence. The useful thing is not a TT; it is branch-local memoization of pure helpers and ROM lookup tables.

Null-move pruning is also unsafe. The proposal's zugzwang examples are real: Outrage/rampage, Encore, Choice lock, last-mon, recharge, Bide, Perish/trap, and setup windows can all make "passing" radically misleading. Chess null-move pruning itself carries known zugzwang risk because it assumes passing and still being above beta implies the position is strong.

Carve-outs worth reconsidering: model the player failing to act as a chance event for sleep, freeze, paralysis, confusion, infatuation, recharge, or charge-turn states. That is not null-move pruning; it is an action-denial probability inside V. A tiny within-turn memo keyed by `(candidate move, reply bucket, active type/HP/status band)` is also fine. Do not call that a TT.

**Defect found?** No, except terminology: do not conflate "memoize duplicate helper results" with "transposition table."

### C10

**Confidence:** medium; current literature moves fast, and I checked recent sources.

**Answer:** PokéChamp is a reasonable reference for the family of ideas, but the proposal overstates it as direct proof for "depth-1/2 minimax + top-K sampled opponent actions = N=4 × M=3."

The PokéChamp paper describes a minimax-style agent using LLM modules for candidate action sampling, opponent modeling, and value estimation. It explicitly says full Pokémon search is infeasible under time constraints and uses candidate action sampling to prune action spaces; it also simplifies stochastic transitions by expected value. That supports the proposal's general direction: small candidate sets, opponent action modeling, strong evaluator, shallow search.

But I would cite PokéChamp as "sampled-action minimax under constraints," not as validation of exactly three buckets or STAR1. Better companion references are Metamon for offline sequence-model policy learning from Pokémon Showdown logs, and ChanceProbCut/STAR for chance-node pruning. Metamon is directly about Pokémon as a stochastic imperfect-information game and argues that strong agents usually rely on heuristic search or custom simulators, while its own approach learns from human logs without explicit search.

**Defect found?**

`01_proposal_lookahead_2x.md / §3 / Uses PokéChamp as if it directly validates "3 sampled opponent actions" for this ROM design / The paper supports candidate sampling and shallow minimax generally, not this exact bucket design / Reword citation claim and add Metamon + ChanceProbCut as separate supporting references / Confidence medium-high.`

## D. Pokémon-specific gotchas

### D11

**Confidence:** high on categories; medium on exact implementation until move-effect source is audited.

**Answer:** The proposal under-handles commitment state. M=3 buckets are fine only if forced-action and lock-state rules override the bucket prior.

Needs explicit handling in M=3:

Outrage/rampage, Rollout/Fury Cutter-style lock/ramp states, Hyper Beam recharge, Bide, Fly/Dig, SolarBeam charge, Encore, Disable, Choice lock, Mean Look/trapping, Perish, and recharge/charge substatus. These change legal actions or hit validity. They cannot be "expected value" decorations after bucket selection. They must collapse or mask buckets.

For example: if the player is Encored, ATTACK/PRESERVE/SETUP weights are not free priors; the legal repeated move dominates. If the player is recharging or asleep with known counter, the AI should treat "player acts" probability differently. If the boss is facing Fly/Dig, ordinary ATTACK V is wrong unless the candidate can hit semi-invulnerable targets. If the player is trapped, PRESERVE-as-switch is illegal or heavily reduced.

Can collapse into expectation per branch:

Damage variance, ordinary crit chance, accuracy, secondary status proc, paralysis full-para, confusion self-hit, infatuation, and most status procs can be single expected values in the default case. But they must become explicit near thresholds: KO range, survival range, "one miss loses," "one crit wins," or action denial changes setup affordability.

Mechanics document reminders: damage has a Gen 2 random factor around `0.85..1.00`, crit is a 2× multiplier, and this hack has type passives layered into damage. The proposal's point-estimate V is too crude at KO boundaries.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3–§4.4 / Treats reply buckets as if player action classes are always freely selectable / Lock, recharge, charge, trap, Encore, Disable, and semi-invulnerable states change legal replies and hit validity / Add a "forced/committed action override" before bucket weighting; buckets are priors only after legality masks / Confidence high.`

### D12

**Confidence:** high.

**Answer:** Yes, point-estimate V leaves performance on the table, but low/mid/high damage roll buckets everywhere are too expensive.

The right fix is not `V(candidate, reply, low/mid/high)` for every branch. That triples the expensive branch count before you even include crit/accuracy/status. With `N=4`, `M=3`, and three roll buckets, you are at 36 evaluations before quiescence. That is dead on this budget.

The right fix is a KO-band oracle: compute min/mean/max or coarse `P(KO)` from public bands and use that inside V. The mechanics doc says damage variation is roughly `0.85..1.00`, with the common Gen 2 `217..255/255` framing. P2 already plans a KO-band oracle and matchup precompute that improves KO, deny-KO, recovery, setup affordability, sacrifice, and switch confidence without reading private stats. That should ship before P-C.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3 / V is underspecified as a point estimate / Around KO thresholds, a point estimate picks visibly dumb lines / Consume P2 KO-band min/mean/max or P(KO) instead of adding explicit damage roll buckets to P-C / Confidence high.`

### D13

**Confidence:** high.

**Answer:** Root-level composition is okay; branch-level composition is not.

Using `BossAI_PredictPlayerSwitch` once to shift some ATTACK weight to PRESERVE is a reasonable root prior. The switch predictor is already public-info based: observed switches, visible HP bands, public pressure, and revealed super-effective moves.

But V should be candidate-conditioned. The player's switch chance is different if the boss candidate is a likely KO move, a setup move, Spikes, a resisted move, or a recharge/lock commitment. Calling the current scalar once and shifting weights globally ignores the boss candidate hypothesis. Worse, if V itself calls `BossAI_PredictPlayerSwitch`, you can double-count switch pressure.

The clean version: compute a public root switch prior, then apply small candidate-local modifiers. Do not re-run the entire switch predictor under fake state unless you have a branch-local context object and cache isolation.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3 / Uses one scalar switch chance to shift ATTACK→PRESERVE for all candidates / Switch probability is candidate-dependent; a KO threat and a setup move do not induce the same player response / Use root prior + candidate-conditioned public modifiers; avoid double-counting inside V / Confidence high.`

## E. Verification

### E14

**Confidence:** medium-high.

**Answer:** The metric is defensible but incomplete.

"Reduce the gap to 100% by 50%" is a good executive metric. If pairwise best-vs-bad agreement moves from 70% to 85%, that is meaningful. It also fits BOSSAI-004's role as the taste source: `best` and rank-1 are positive, `bad` and `cheap` are warnings, `scary_good` is allowed but monitored, and `needs_context` should not drive source changes alone.

But a single agreement score can hide regressions. I would require:

Pairwise rank accuracy: `best > bad`, `best > cheap`, and `scary_good` not automatically penalized.

Probability mass on best under fixed RNG seeds, because final selection is weighted best-vs-second, not deterministic.

Scenario strata: KO threshold, setup, switch/preserve, status, lock/recharge, and revealed-priority scenarios.

Non-regression budget: no increase in `cheap` picks, no early-tier "too smart" leaks, no no-cheat violations.

**Defect found?**

`01_proposal_lookahead_2x.md / §2 and §8 / Single aggregate "2x smarter" metric can hide scenario regressions / Averages may improve while setup or switch scenarios get worse / Report stratified pairwise ranking, stochastic choice probability, and cheap/bad regression counts / Confidence high.`

### E15

**Confidence:** medium-high.

**Answer:** STAR1 fits best for a first implementation, but expectations should be modest.

Chance nodes are weighted sums of child outcomes. STAR1 and STAR2 are exact pruning methods for expectimax-style chance nodes; ChanceProbCut is a probabilistic pruning method using shallow-search/deep-search correlation and confidence intervals. The ChanceProbCut paper notes STAR1 is exact but often not impressive because bounds can be pessimistic; STAR2 uses probing to improve bounds; ChanceProbCut needs regression/calibration.

On SM83 with only three buckets, STAR2's extra probes can cost more than they save. ChanceProbCut is premature until you have a dataset of shallow/deep bucket evaluations and know the error distribution. STAR1 is simple, exact, and auditable, but I would not count on it to save one third of bucket evaluations.

Implementation tradeoff:

STAR1: simple cap math, exact, easiest to audit, weak pruning.

STAR2: more code and extra probes, maybe useful only after P-C is measured.

ChanceProbCut: powerful in theory, not acceptable without calibration; better as offline tooling later.

**Defect found?**

`01_proposal_lookahead_2x.md / §4.3 and §6 / Assumes STAR1 recovers most of 3x evaluator cost / With only three buckets and loose bounds, STAR1 may prune little / Treat STAR1 savings as upside, not budget-critical; measure bucket-prune rate explicitly / Confidence medium-high.`

### E16

**Confidence:** high.

**Answer:** Add these before shipping P-C:

A cache-isolation audit: assert hypothetical bucket evaluation cannot read stale `wBossAILastMatchupType`, `wBossAIShouldScoutPrereqCache`, `wTypeMatchup`, `wEnemyMoveStruct`, `wCurSpecies`, or `hBattleTurn` from another branch.

A top-N audit: if `N < 4` ever ships, verify the evaluated candidates are actually the top N by score, not the first N in move-slot order.

A signed-score property test: upside-only must never worsen a score; downside-only must never improve it; clamp must preserve sign; blocked scores must stay blocked.

A weighted-accumulator test: feed max weights and max deltas and prove no signed 8-bit overflow.

A RNG-consumption trace: P-B/P-C must not accidentally change `Random` consumption except where behavior is intentionally changed. The current `ShouldScout` cache was careful to preserve Random consumption; P-C needs the same discipline.

A p95 perf gate with more than three samples. Current perf samples are too small for a shipping claim.

A full branch trace: candidate index, base score, bucket weights, per-bucket V, final signed delta, and final selected move.

A save-state replay suite across real fights, not just synthetic fixtures.

**Defect found?**

`01_proposal_lookahead_2x.md / §8 / Verification plan lacks branch-cache and signed-overflow audits / These are the most likely P-C failure modes / Add explicit audits for cache isolation, top-N ordering, signed accumulation, and RNG parity / Confidence high.`

## F. Sequencing

### F17

**Confidence:** medium-high.

**Answer:** The proposed sequence is close, but I would change it.

Do before P2:

First, fix the proposal and add instrumentation. The code semantics and budget must be clear before any new search layer.

Second, implement P-A as a measured lower-is-better futility cutoff, not "alpha-beta," because it is local and can create budget.

Third, add trace expansion for all four candidates.

I would not ship P-B before P2 unless it is only logging. The killer bucket is not valuable enough to spend design complexity before the evaluator improves.

P2 should precede P-C. The roadmap's P2 KO-band oracle is exactly the foundation P-C needs: public damage bands, survival windows, deny-KO odds, and matchup precompute. Multiplying a weak V across three buckets just gives you three times the wrong answer.

P-D can ship before full P-C only as a tiny KO-only quiescence guard. The broader P-D should wait until P-C and P2 are stable.

**Defect found?**

`01_proposal_lookahead_2x.md / §5 / Sequences P-B before the evaluator is strong enough to use it / Last-bucket priors are low-value compared with P2 KO-band V and branch-safe P-A / Ship instrumentation + P-A before P2; P2 before P-C; P-B after P5 or as logging only / Confidence medium-high.`

### F18

**Confidence:** medium.

**Answer:** LATE-only is right for the first ship. Mid-tier should get a reduced version only after measurement. Early should not get it.

The project's tier philosophy is clear: early bosses are simpler, mid bosses respect obvious threats, late bosses preserve and adapt. Full P-D in MID risks making midgame feel like E4 AI and risks budget creep. A reduced MID quiescence is reasonable later: only fire for immediate KO/no-KO threshold, revealed priority revenge, recharge/lock, or Perish/Encore hard states. No multi-turn setup-chain extension in MID until fixtures prove it is needed.

**Defect found?** No. The proposal's LATE gate is conservative and sane.

## G. Bigger picture

### G19

**Confidence:** medium-high.

**Answer:** Yes. The proposal is too search-centric. A better same-budget path is probably "better evaluator first, more search second."

A learned evaluator is very plausible if trained offline and baked into ROM as a small interpretable weighted sum or lookup table. The policy file forbids black-box training output landing directly in ASM, but it allows public-info heuristics with documented policy rationale. So the right shape is not a neural net in ROM; it is an offline-trained scoring table converted into transparent weights: KO band, speed relation, HP band, revealed threat class, lock state, setup state, switch tendency.

A supervised policy network distilled to a decision tree is even better. Train from BOSSAI-004 labels, self-play logs, and curated Cole labels; distill into decision lists or small tables. That gives ROM-cheap behavior, no RAM growth, and auditability.

Coevolution/self-play is useful for tuning constants, not for runtime policy. Let an offline simulator pit candidate weights against scenario corpora, then bake stable weights. Guard against overfitting to "competitive" behavior that violates the project's first-playthrough feel.

Recent Pokémon AI work points this way. PokéChamp supports shallow sampled search with opponent modeling and value estimation under constraints. Metamon is even more relevant for offline learning: it frames Pokémon as stochastic imperfect information and trains from human battle logs without explicit search at inference time. For this ROM, the lesson is not "run ML on Game Boy." The lesson is "use ML offline to discover small public-info rules, then compile them into transparent tables."

**Defect found?**

`01_proposal_lookahead_2x.md / Entire proposal / Over-focuses on adding reply search before upgrading V / Search amplifies evaluator errors; a weak V across three buckets can be worse than one good evaluation / Prioritize P2 KO-band oracle, public observation/tendency counters, and offline-distilled evaluator weights before full P-C / Confidence medium-high.`

### G20

**Confidence:** medium-high.

**Answer:** Yes. Poker is a better analog than chess for P-C/P5. Chess is good for pruning vocabulary, but it is perfect-information deterministic search. Pokémon boss AI is public-information inference under variance and hidden information.

Best analog domains:

Poker: opponent modeling, mixed strategies, exploitability, public betting history, and avoiding overreaction to a single observation. This maps directly to reply buckets and tendency counters.

Fighting game AI / RTS micro: tiny real-time budgets, threat windows, frame advantage, utility scoring, and behavior trees. This maps to SM83 constraints better than chess engine architecture.

Magic: strong conceptual analog for hidden hand/deck knowledge, public reveals, and archetype inference. But it is too combinatorial to import directly.

Chess: useful for futility pruning and quiescence only. Dangerous if it makes the proposal chase alpha-beta/PVS terminology instead of Pokémon-native state.

Go/MCTS: mostly wrong here. No fast simulator, no rollout budget.

Hanabi: not relevant; cooperative information conventions do not map to boss adversarial play.

**Defect found?**

`01_proposal_lookahead_2x.md / §3 / Chess is over-weighted as the inspiration domain / It pushes the plan toward search jargon instead of opponent modeling and public-information priors / Add poker and fighting-game/RTS micro as primary analogs; keep chess only for pruning/quiescence terminology / Confidence medium-high.`

## H. Open taste calls

### H21

**Confidence:** high.

**Answer:** The most consequential taste call is S4 / P-A cutoff semantics, not killer-bucket strength.

Reason: S4 decides which moves get deeper reasoning at all. If it is wrong, P-C never sees the line that matters. It also determines whether the ≤10% budget is real. Killer-bucket strength is tiny by comparison. Quiescence loud-node set is second because it defines when the AI is allowed to "think harder" and will strongly affect perceived fairness. Sequencing is third. Killer-bucket strength is fourth.

**Defect found?**

`01_proposal_lookahead_2x.md / §9 / Treats killer-bucket strength as a comparable taste call to S4/quiescence / Killer strength is low leverage; S4 correctness is load-bearing for both quality and perf / Reorder open calls by consequence: S4 bound, quiescence loud set, sequencing, killer strength / Confidence high.`

## I. Honest assessment

### I22

**Confidence:** high.

**Answer:** It does not yet deliver "2x smarter." It proposes a plausible path to a real improvement, but the headline is oversold.

Load-bearing parts:

P2-quality KO/survival evaluator.

Branch-safe P-C with cache isolation.

Correct lower-is-better futility cutoff.

Quiescence only on real loud nodes.

A real measurement harness using BOSSAI-004 labels.

Decorative or weak parts:

The "chess" framing.

The killer-bucket prior.

STAR1 as a budget savior.

Exact hand-written weights.

The "2x" phrase itself.

The proposal says the current lookahead lacks true reply modeling and state simulation, which is correct. But adding three coarse reply buckets is not automatically "2x smarter." It can be "3x more opinionated about the same flawed heuristic." The own budget table also does not satisfy the ≤10% claim.

**Defect found?**

`01_proposal_lookahead_2x.md / Title and TL;DR / Oversells "~2x smarter at ≤+10%" / The proposal has not proven either the quality gain or the perf bound, and its own estimates exceed the bound / Retitle to "candidate plan for reply-bucket lookahead; requires P2 evaluator and perf proof" / Confidence high.`

### I23

**Confidence:** medium-high.

**Answer:** Yes, partly. The proposal is load-bearing in the wrong place if it ships P-C before improving V.

Inside the same +10% budget, I would expect more player-visible improvement from:

P2 KO-band oracle and damage/survival ranges.

Observation/tendency counters from P5.

Revealed-effect matrix cleanup from P3.

Correct root futility cutoff and full lookahead trace.

Those improve the evaluator and the public-information model. P-C should consume that. It should not be the first major intelligence upgrade.

The roadmap already positions P2 as very high impact because it improves KO, deny-KO, recovery, setup affordability, sacrifice, and switch confidence across every boss. That is more foundational than a bucket wrapper.

**Defect found?**

`01_proposal_lookahead_2x.md / §5–§6 / Treats P-C as the structural change while P2 is just a helpful precursor / The evaluator is the actual load-bearing component; bucket search only multiplies it / Make P2/P5 evaluator quality the dependency gate for P-C / Confidence medium-high.`

### I24

**Confidence:** high.

**Answer:** The single most important thing to do differently: **rewrite P-C around an explicit branch-context contract before writing any ASM.**

That contract must say what a hypothetical reply can mutate, what it cannot read, which caches are branch-local, how signed scores accumulate, how defender typing is represented, and how V uses KO-band ranges. Without that, the implementation will almost certainly leak stale cache state or invert signed math.

Put another way: do not start by adding M=3. Start by defining `EvaluateCandidateAgainstReply(candidate, reply_context)` as a safe, measurable, public-info function. Then P-C is just a loop around it.

**Defect found?**

`01_proposal_lookahead_2x.md / Missing design contract / No branch-local context model for hypothetical replies / This is the core implementation risk for correctness, no-cheat safety, and cache validity / Add a new section "P-C branch context contract" before phases; no implementation until it has tests / Confidence high.`

## Top 3 specific changes I would make to `01_proposal_lookahead_2x.md`

1. **§4.1 P-A:** Replace the `.best_loop` critique. Say: "Existing code correctly finds the minimum legal score because lower is better. Existing cutoff is a static near-best beam. P-A should be a dynamic lower-is-better futility cutoff using signed-delta bounds." Remove the "clustered near worst" claim.

2. **§4.3 P-C:** Add a branch-context contract. It must cover defender type/HP/status for hypothetical PRESERVE, cache isolation for `wTypeMatchup`, `wEnemyMoveStruct`, `wCurSpecies`, `hBattleTurn`, `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem`, `BossAI_ShouldScout`, signed 16-bit weighted accumulation, and no hidden-info reads.

3. **§6 Budget accounting:** Fix units and downgrade the headline. State that current estimates are `+10–20%`, not ≤10%; require direct inclusive measurement of `BossAI_EvaluateActionLookahead`; gate P-D off until P-A/P-C are measured.

## Top 3 risks the proposal underrates

1. **Cache contamination across hypothetical reply buckets.** Current caches assume the active player state is turn-stable. P-C makes it branch-variable.

2. **Evaluator quality.** Three buckets with a weak point-estimate V will amplify wrong evaluations, especially around KO ranges, locks, recharge, and switch states.

3. **Signed arithmetic overflow/inversion.** Current signed deltas fit in 8-bit. Weighted bucket sums do not necessarily fit.

## Overall verdict

**Scope is wrong, see I23:** ship instrumentation, P-A, and P2 first; redesign P-C around a branch-safe evaluator contract before shipping the "2x smarter" stack.

[1]: https://www.chessprogramming.org/Principal_Variation_Search "Principal Variation Search"
[2]: https://www.chessprogramming.org/Futility_Pruning "Futility Pruning"
[3]: https://en.wikipedia.org/wiki/Null-move_heuristic "Null-move heuristic"
[4]: https://arxiv.org/html/2503.04094v1 "PokéChamp: an Expert-level Minimax Language Agent"
[5]: https://arxiv.org/html/2504.04395v1 "Human-Level Competitive Pokémon via Scalable Offline Reinforcement Learning with Transformers"
