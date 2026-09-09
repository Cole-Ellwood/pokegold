# Exact selector implementation status

Updated 2026-09-07 (Claude Fable continuation). Ordinary selector orchestration
is now **implemented and validated** against the frozen reference on every
existing joint fixture; the complete native selector is still a private
`BOSS_AI_REFERENCE` prototype with no gameplay caller. The two-second
whole-decision target is **not met**: the structural prototype with the
existing amount producers measures 181M DMG T-cycles on the broad benchmark
against an 8.4M budget (see "Ordinary timing" below). Replacement decisions and
ordinary decisions are both evaluated natively; ordinary pairs whose owned or
incoming family is not yet represented use the exact direct fallback.

## Verified foundation

- `engine/battle/ai/fast_math.asm`: signed 40-bit ring multiplication by an
  unsigned 24-bit factor; exact unsigned 24/16 division with zero rejection.
- `engine/battle/ai/fast_hp.asm`: direct small-HP tables, rank8 tables, and
  16-bit threshold tables for wider domains, including exact binary lookup.
  Construction uses only the assigned table reservations and the 32-byte
  arithmetic workspace before accumulated values become live.
- `engine/battle/ai/fast_results.asm`: cross-bank public input preparation,
  canonical invalid records, full numerator/mass normalization, integer-score
  selection with original-index ties, and 128-byte export. Invalid finalization
  discards the entire vector. Finalization closes SRAM on every exit.
- The `FromC` candidate adapter marshals decision kind across the real farcall.
  Input preparation retains an incomplete backend marker until evaluation.
- `tools/boss_ai_fixtures/joint.py` now retains independently aggregated event
  totals and masses as `joint_records`, in addition to existing scores.
- `fast_transitions.asm` implements saturated HP loss, uncapped quota gain,
  recovery quotas, drain and Steel-adjusted recoil. Its caller-certified damage
  script applies target loss, then the user item, then drain/recoil, preserving
  raw damage and permitting same-action drain after Life Orb reaches zero HP.
- `fast_producers.asm` exports separate can-act/check/effect/hit/setup/range
  flags, capped and raw endpoints, and support status through same-bank bridges.
  The 64-byte prefix export also separates recovery recognition from its uncapped
  quota. These are stage metadata; their consumers enforce reachability.
- `fast_plans.asm` compiles owned single-hit/recovery amount plans in the fixed
  64-byte layout. Four raw HP regimes retain support and range masks separately.
  Own defense-boost plans (the boss's own Harden and relatives) receive the
  explicit fallback opcode; multihit, Super Fang, False Swipe, Selfdestruct
  and, on the reply side, defense boosts became native on 2026-09-07 (see
  "Performance work and native families"). Amounts require fixed non-HP
  context inputs.
- `fast_plan_executor.asm` executes one represented owned action, including
  both-living/can-act gates, original hit/miss semantics, conditional uncertainty,
  finite-width HP regimes and the known item/drain/recoil script. It reads compact
  plans and actors with the producer prefix poisoned in differential tests.
- `fast_actors.asm` validates and imports actor HP/max/weight/potential/table-mode
  fields. `fast_standalone.asm` records both original-event HP successors, reached
  flags, signed deltas and the exact signed 24-bit probability moment. These are
  owned-action components; ordinary selector orchestration does not yet use them.
- `fast_reply_plans.asm` compiles the fixed 48-byte incoming record directly at
  context offsets 399..446. It captures four selected raw maximum regimes,
  support/range masks, original power, and the known defender's Helmet quota.
  Absence bypasses producer reads. Switch-Pursuit has an explicit transition
  opcode; unsupported damaging replies retain the reference's reached KO bound.
- `fast_reply_executor.asm` executes incoming damage/recovery, including Helmet
  before drain/recoil and holder-KO behavior. `fast_reply_standalone.asm` records
  original-event successors and exact signed moments. Both preserve owned plans.
- Both action executors expose `FlagsOnly` entries with identical reached flags
  and no HP mutation. Rest uncertainty requires a positive quota and missing HP
  at that continuation. These entries share the executable gates and metadata.
- `fast_pair.asm` computes represented normalized move pairs from standalone
  moments and one active/active terminal per order. It combines modeled tie
  corrections before multiplication. Positive original-event flag paths use
  standalone first-event HP and `FlagsOnly`; they do not repeat damage arithmetic.
  A correction-only entry omits the standalone baseline for future shared sums.
- `fast_pair_fallback.asm` produces complete direct-reference move-pair numerators
  or subtracts the exact previously assigned standalone baseline. It rebuilds the
  producer prefix for each positive original event, never enters the old JC or
  SRAM-table lifetime, and preserves compact plans/results. The order input must
  describe actual public order. This fallback currently accepts move kind only.
- `fast_reference.asm` owns the old JC workspace exclusively and copies full
  five-byte numerators and masses before another candidate clears them. It
  returns complete status 2 records through the common finalizer. It does not
  enable the old fixed SRAM HP tables.
- `fast_selector.asm` exposes `BossAI_ComparePublicActionsFastPrototype`.
  Replacement decisions use public actor/setup/entry facts, compact HP tables,
  native HP transitions and potentials, and exact mass 2 records. Invalid HP
  domains discard partial native state before restarting. Ordinary decisions
  currently restart immediately; this is not a fast ordinary evaluator.

Complete prototype records are compared against independent aggregation using
the frozen preflight ROM. This establishes replacement and compatibility results,
not an unimplemented ordinary native evaluator.

## Ordinary orchestration (2026-09-07)

- `fast_selector.asm` now evaluates ordinary decisions natively. The active
  defender compiles up to four owned plans (choice moves, or the forced move
  at original index 10), classifies the wait candidate (index 10 after the
  reference's forced-wait conversions, or 11 in recharge mode), imports the
  actor once, builds the standalone moments, initializes every record with
  `M<<26 + (M<<8)*mu_own` (wait: `(M<<16)*1024`), then streams one compiled
  reply per possible move ID. Each represented reply adds `w*mu_reply` to the
  signed 32-bit shared sum and one correction per plan: native
  `BossAI_FastNormalizedPair.CorrectionOnly` when both sides are represented,
  otherwise `BossAI_FastFallbackPair.CorrectionOnly`. `512*B` is committed to
  every plan and the unary candidate before the defender changes.
- Bench switches (indices 4..9) reuse `BossAI_FastPrepareReplacementFacts`,
  rebuild the actor/tables, apply entry hazards, record the entry delta, then
  make the post-entry HP/Phi the actor's start state so reply standalone
  moments are post-entry by construction. Records start at
  `(M<<16)*(1024+entry_delta)`; entry KO leaves the reply gated and the mass
  intact.
- Unrepresented replies (opcode 0: multihit or False Swipe replies whose
  roll range is wider than a byte, and anything the compiler rejects) use
  the new
  `BossAI_FastUnaryFallback` for the wait/switch candidate: the direct
  evaluator runs each positive original reply event with own event mass 256
  and a single order, and the routine subtracts the exact baseline
  `2*65536*(1024+entry_delta)` already assigned. Move plans paired with such a
  reply take the whole-pair fallback, whose baseline subtraction uses the
  reply's zero moment consistently with the shared sum that excluded it.
- Order descriptors come from the compact records and imported actor facts:
  priority first, then known speeds; unknown public order or Quick Claw at
  equal speed keeps the reference's conservative reply-first order, and only a
  genuine same-priority, same-known-speed pair without Quick Claw gets the
  two-order descriptor. Unknown-speed uncertainty is a candidate-level flag
  for move plans; Quick Claw's order flag is already a setup flag.
- Bridges in `fast_producers.asm` (`BossAI_FastPrepareOwnedCandidate`,
  `BossAI_FastPrepareActiveFacts`, `BossAI_FastPrepareReply`) keep every
  cross-bank input in BC/DE or the context, and `BossAI_FastForcedAction` in
  `fast_reference.asm` mirrors the reference's index-10 rules (including
  `.ForcedCanExecute`) from the joint-policy bank.
- The traversal flags still produce identical vectors: bit0 reverses the bench
  and plan cursors, bit1 the reply sweep; bits 2..3 are absorbed by the exact
  commutative accumulation.
- Status byte: 0 native-only, 1 when any pair or unary fallback ran. Invalid
  actor HP domains, a reply mass outside 1..282 or a stale reply header
  discard native state and restart through the compatibility adapter.

## Performance work and native families (2026-09-07)

Five commits after the orchestration landed reduce the broad benchmark
(`joint_broad_prior_mass`, one scan) from 180,985,824 to 59,106,740 DMG
T-cycles while every frozen-oracle vector stays exact. None of them changes a
result; each replaces a producer-backed or executor-backed computation with an
equivalent that reads compact records.

- **Lazy reply regimes** (`9b822b7f`). `.ReplyRegimes` in `fast_selector.asm`
  marks the incoming HP regimes a reply can reach for the current defender: the
  start state plus every live plan's original-event successors (bit0 the
  player's attacker-low predicate, bit1 the own defender-high predicate, both
  in the executor's wrapped 16-bit arithmetic). The compile receives the mask in
  C (`BossAI_FastCompileReplyPlan.Masked`, `BossAI_FastCompileReplyNative`) and
  records it in `FSR_VALID`; only masked regimes get amounts/range/support bits.
  If an incoming plan ever executes at an unmarked regime the executor latches
  `FSC_FAULT` ($a58f) and the selector restarts through the reference adapter
  instead of reading a zero amount. The reply bridge also stopped calling the
  prepared-range producer and copying the template.
- **Scalar pair** (`9b822b7f`, `a04741df`). `fast_scalar_pair.asm`:
  `BossAI_FastScalarPair` evaluates a plain damage/recovery pair (effect and
  item tags both zero on both sides) with at most two potential lookups per
  order instead of executing both actions; gate fields are cached once per
  record in `FSK_OWN`/`FSK_REPLY` ($a5c0..$a5d7). The selector tries it first
  and falls back to `BossAI_FastNormalizedPair.CorrectionOnly`.
- **Scalar standalone** (`a04741df`). `BossAI_FastScalarReplyStandalone` builds
  the plain-reply standalone record (bytes 28..42 plus the standalone flags at
  24/25) from the actor start potentials with one lookup per changed HP word
  and a signed 16x8 multiply (`BossAI_FastMulSigned16By8`).
- **Native reply compiler** (`0ed1b6c3`, `a03213eb`). `fast_reply_native.asm`:
  `BossAI_FastPrepareReplyFacts` derives per-defender facts (`FSN`,
  $a5e0..$a5ff: level, types, weather, template flags, guards, stages,
  Bright Powder, Focus Band, Helmet quota, Outrage category, truncated formula
  stats, Steel/Psychic/Poison typing, switch flag) once per epoch, and
  `BossAI_FastCompileReplyNative` compiles the 48-byte reply record from
  in-bank mirrors of the move table, contact flags, effect priorities, accuracy
  multipliers and the type chart (the data files gained `BOSSAI_EMIT_LOCAL_*`
  include guards so the reference build emits second copies; the game ROM's
  bytes are unchanged). It mirrors the producer's Category, EffectSupport,
  copyguards, SurvivalFacts, accuracy modifiers, PlayerCanAct, effect/hit
  uncertainty, RecoveryQuota, descriptor and the single-hit kernel (chart,
  weather, STAB, passives, variation 217/255, postroll). A generated 256-byte
  effect-class table replaces list scans; the formula base is cached per
  category and power (physical $a590..$a5bf and $a4f8..$a50f, special in the
  dead template bytes at context 89..190). `fast_reply_native.py` compares the
  native record with the producer path byte for byte.
- **Identity replies** (`a03213eb`). `.ClassifyIdentity` marks a damage reply
  that can never change HP from any state (unsupported with zero power, or all
  compiled regimes supported with zero amounts and no range bits, or unable to
  act). Pairs with such a reply take `.IdentityPair`: zero correction, flags
  from the standalone records with the reference's reachability rules.
- **Native families** (this checkpoint). Multihit, Super Fang, False Swipe and
  Selfdestruct are represented opcodes on both sides: owned plans
  `FSP_MULTI`=3, `FSP_FANG`=4, `FSP_FALSE_SWIPE`=5, `FSP_SELFDESTRUCT`=6; reply
  records `FSR_MULTI`=5, `FSR_FANG`=6, `FSR_FALSE_SWIPE`=7,
  `FSR_SELFDESTRUCT`=8. Only defense boosts remain fallback replies.
  - Compilers keep the per-regime sweep unchanged and patch the producer input
    for the sweep: multihit compiles per-hit endpoints with `AD_MIN/MAX_HITS`
    forced to 1/1 (all four regimes, since hits cross regimes inside one
    action), False Swipe compiles uncapped endpoints with `AD_EFFECT` set to
    `EFFECT_NORMAL_HIT`; `.RestorePatch` undoes the patch before the epilogue.
    Reply records store only maxima, so these two families also store the
    per-regime maximum-minus-minimum in the otherwise unused bytes 7, 8, 23 and
    26 (`FSR_MIN_DELTA0..3`); a delta wider than a byte makes the compile
    return opcode 0 with carry clear (header written, fallback follows). The
    native compiler halves the truncated defense for Selfdestruct without
    caching that base, and computes Super Fang's template amount as half the
    template HP (minimum one).
  - Executors finish the families at the real continuation state. Multihit
    walks the hits one at a time from the target's current HP, recomputing the
    defender-high predicate per hit, stopping at a KO and saturating the total
    like the kernel (the final hit's overkill stays in the total); the range
    flag compares the minimum-hit/minimum-amount path with the maximum-hit/
    maximum-amount path, and the selected total (own minimum, reply maximum)
    runs through the ordinary single-hit script so items and drain use it as
    raw. Super Fang halves the target's current HP (minimum one; a compiled
    zero is chart immunity). False Swipe caps both endpoints at target HP minus
    one and flags a range only when the capped amounts differ. Selfdestruct
    faints the user after the amount regime is read and before the event and
    accuracy checks, so it faints on a miss too; the damage script then skips
    the dead user's item, as the reference does.
  - Pairs: a Selfdestruct miss is not identity, so the factored
    `BossAI_FastNormalizedPair` rejects it. The selector routes those pairs to
    `BossAI_FastFallbackPair.Native`, a third mode of the whole-pair evaluator
    that takes both terminals from the compact executors in every modeled
    order (own first for order 0, reply first for order 1, both for a tie) and
    subtracts the standalone baseline. Identity replies still take
    `.IdentityPair` even against a Selfdestruct plan (its successor rules
    already handle the self-KO). The standalone builders and the factored pair
    accept the other families unchanged because their executors do the work.

## Validation and timing

Current reference ROM SHA256:
`40a209cf3a1e4298897bb97ac213cc842ceb1336c7c48efd80fac600a8e65e58`
(orchestration checkpoint:
`83070fc20a59f278f82d9f7052510285aba956aab563a53cef4493b383048d01`;
pair/fallback checkpoint before orchestration:
`65e403fb5e8b4e64b8f05d38820f7cf87ba239f9545986afa24a58413989ee75`).
The refreshed replacement profile below was measured on
`e8628a6cfde19b508a6d6b75b9bf32bd3cb7a5a6fff319bb689a7e465feabfb0`, which
differs from the current ROM only by the stale-reply-header guard.
The original foundation tests/profile below were recorded on
`01746b7e6b31fe8325ef19f264c4ca26ed3cb165b996254ac21f1cfe46fbf16d`;
later batch results are listed separately.

Reproduction from the repository root:

```text
python -m tools.boss_ai_fixtures.fast_math
python -m tools.boss_ai_fixtures.fast_hp
python -m tools.boss_ai_fixtures.fast_results
python -m tools.boss_ai_fixtures.fast_hp_profile
python -m tools.boss_ai_fixtures.fast_transitions
python -m tools.boss_ai_fixtures.fast_producers
python -m tools.boss_ai_fixtures.fast_plans
python -m tools.boss_ai_fixtures.fast_plan_executor
python -m tools.boss_ai_fixtures.fast_standalone
python -m tools.boss_ai_fixtures.fast_reply
python -m tools.boss_ai_fixtures.fast_reply_standalone
python -m tools.boss_ai_fixtures.fast_pair
python -m tools.boss_ai_fixtures.fast_pair_fallback
python -m tools.boss_ai_fixtures.fast_reference
python -m tools.boss_ai_fixtures.fast_reference --prototype
python -m tools.boss_ai_fixtures.fast_reference --replacement-boundaries
python -m tools.boss_ai_fixtures.fast_replacement_profile
python -m tools.boss_ai_fixtures.fast_unary_fallback
python -m tools.boss_ai_fixtures.fast_ordinary_profile
python -m tools.boss_ai_fixtures.fast_reply_native
python -m tools.boss_ai_fixtures --rom pokegold_ai_reference --suite all
```

### Ordinary orchestration validation (2026-09-07)

- `fast_reference.py --prototype`: all 26 joint fixtures (24 ordinary, 2
  replacement) match the frozen oracle's complete T/M/score/uncertainty
  vectors, best index, legal mask, BC/carry, DE/SP and bank in forward and
  reverse traversal, plus 24 hidden-information reruns (private player item,
  moves, PP and input poisoned): 76 vectors and 5 invalid entries. Backend
  status: 19 decisions native-only, 7 with fallback (`joint_broad_prior_mass`,
  `joint_speed_tie_transformed`, `joint_accuracy_mixed`,
  `joint_accuracy_own_selfdestruct_miss`,
  `joint_accuracy_reply_selfdestruct_miss`, `joint_accuracy_early_ko`,
  `joint_defense_transitions`). Logs: `.local/ai-two-second/ordinary-prototype-run2.log`
  (ROM `e8628a6c...`) and `ordinary-prototype-run3.log` (current ROM).
- `fast_reference.py --replacement-boundaries`: 116 vectors, 58 native-only,
  including both partial-native restart cases.
- `fast_reference.py` (compatibility adapter): 52 vectors unchanged.
- `fast_unary_fallback.py`: 88 wait/switch unary totals and flags against
  direct reference event sums (eleven reply families including Explosion,
  multihit, False Swipe, Super Fang, Harden, Pursuit; Helmet, Quick Claw,
  Spikes 0..3, confusion, win-condition weight, entry KO bench at 3 HP) with
  baseline subtraction, write footprints and four no-write rejections.
- `fast_pair.py` (1,728) and `fast_pair_fallback.py` (1,248) still pass.
- All 839 decision-path fixtures pass on the orchestration ROM
  (`.local/ai-two-second/orchestration-fixtures.log`, ROM `e8628a6c...`;
  `orchestration-fixtures-final.log` on the current ROM).
- Not yet exercised by any fixture: an ordinary decision whose actor import
  is rejected (max HP 0 / HP above max) and the reply-mass bound; both
  routes are the same `.restart` path the replacement restart cases cover.


### Native families validation (2026-09-07)

Reference ROM SHA256
`40a209cf3a1e4298897bb97ac213cc842ceb1336c7c48efd80fac600a8e65e58`; game ROM
rebuilt, SHA1 unchanged (`85a2fe838a28f23b198845e63876a637580e91a9`).

- `fast_reply.py`: 26,880 incoming action/reference comparisons over 1,680
  compiled plans (adds Fury Swipes, Bonemerang, Twineedle, Super Fang, False
  Swipe, Explosion to the move list, with the expectation patching the context
  the same way the compiler does and checking the delta bytes), plus a
  wide-roll-range case (Pin Missile, level 100, attack 999 into defense 1,
  4x chart) that must compile to opcode 0 and be rejected by the executor.
- `fast_reply_native.py`: 5,588 native compiles identical to the producer path,
  now including a level-5 Grass/Psychic defender against a level-100 Bug
  attacker so both compilers take the wide-delta exit.
- `fast_plans.py`: 240 owned plans (all family moves represented; Super Fang's
  template amount is HP-dependent by design and excluded from the
  HP-independence check). `fast_plan_executor.py`: 8,208 owned action
  comparisons including Fury Swipes, Bonemerang, Super Fang, False Swipe and
  Explosion at eight HP states, both events, three items and three maxima.
- `fast_standalone.py` 2,160 and `fast_reply_standalone.py` 3,000 (1,500
  scalar) unchanged; rejection opcodes moved past the new range.
- `fast_pair.py`: 3,744 pair numerators/flags (390 scalar) over twelve moves
  including Fury Swipes, Super Fang, False Swipe and Explosion; Explosion pairs
  assert that the factored pair rejects and that `BossAI_FastFallbackPair.Native`
  matches the reference event sum minus the baseline; 15 no-write rejections.
  Two defects found and fixed by this fixture before the whole-selector run:
  the native mode lacked the modeled-tie flag, and it started single orders
  from the wrong side (the direct evaluator resolves order itself, the native
  mode must execute the actual one).
- `fast_pair_fallback.py` 1,248 and `fast_unary_fallback.py` 88 unchanged.
- `fast_reference.py --prototype`: 76 vectors exact; backend status 23
  native-only, 3 with fallback (`joint_broad_prior_mass`,
  `joint_defense_transitions`, `joint_speed_tie_transformed`, all because of
  defense-boost replies). `--replacement-boundaries` 116 vectors and the
  restart adapter 52 vectors unchanged.
- `tools/audit/check_boss_ai_decision_paths.py` on the rebuilt game ROM: 473
  production fixtures pass; the 839-fixture reference suite passes
  (`.local/ai-two-second/families-fixtures.log`) and
  `check_release_smoke.py` passes on the final build.

The `.local/ai-two-second/debug_joint_pairs.py` script records every
`.AddPairTotal` contribution of one joint case twice, once natively and once
with every pair forced through the direct fallback, and prints the pairs whose
totals differ. It localized the order-start defect in one run and is the
fastest way to find which reply a future whole-selector mismatch comes from.

### Ordinary timing (structural prototype, not the gate)

[Ordinary profile](fast_ordinary_profile.json) measures the 24 ordinary joint
fixtures in two scans, bank-qualified entry through the final `CloseSRAM`
return, native prototype versus `BossAI_ComparePublicActionsWithTables` on the
frozen oracle. Native cycles are split into disjoint phases by entry hooks.

| Case | Native cycles | Oracle cycles | Status |
| --- | ---: | ---: | --- |
| `joint_broad_prior_mass` (4 moves, 5 bench, 254 replies) | 180,985,824 | 132,211,028 | 1 |
| `joint_speed_tie_transformed` (open prior, unknown order) | 39,238,140 | 48,668,688 | 1 |
| `joint_open_prior` | 6,722,952 | 5,437,608 | 0 |
| `joint_defense_transitions` | 5,247,672 | 3,283,504 | 1 |
| `joint_accuracy_own_selfdestruct_miss` | 2,491,928 | 813,352 | 1 |
| smallest (`joint_recharge_wait`) | 898,704 | 567,536 | 0 |

Broad-benchmark phase split (one scan): reply preparation 104.0M (57.5%,
1,524 `PreparePublicReply`+compile calls, 7,059 `PublicDamageRange` calls
because every compiled reply evaluates all four HP regimes eagerly), reply
standalone 21.3M, native pairs 18.9M, whole-pair fallback 14.3M, unary
fallback 13.1M, orchestration arithmetic 7.5M, owned preparation 1.1M, HP
tables 0.56M, entry/inputs 0.11M, finalize 0.05M. The budget is 8,388,608.

Conclusions the profile supports: (1) the existing amount producers cannot
reach the target; the reply-preparation phase alone is twelve times the whole
budget, so Milestone 4 native base/finishing arithmetic streamed by power
group is mandatory, not optional; (2) an interim two-to-four-fold reduction of
reply preparation is available without new arithmetic by compiling only the
HP regimes a reply can actually reach (initial state plus each plan's hit
successor), which the `FSR_VALID` mask was designed for; (3) the pair
evaluator averages about 19k cycles per native pair against the contract's
1,100-cycle scalar-unit target, so reply grouping and cheaper terminal
execution are required as well; (4) fallback families cost 27M on the broad
case and must become native before any timing claim. Small decisions (one
reply set, one or two plans) already run at 0.9M-1.4M cycles, roughly 1.2-1.8
times the oracle, because the four-regime compile dominates them too.


#### After the 2026-09-07 performance work

Same method, same 24 fixtures, current ROM
(`40a209cf3a1e4298897bb97ac213cc842ceb1336c7c48efd80fac600a8e65e58`).

| Case | Native cycles | Oracle cycles | Status |
| --- | ---: | ---: | --- |
| `joint_broad_prior_mass` | 59,106,740 | 132,211,028 | 1 |
| `joint_speed_tie_transformed` | 19,372,692 | 48,668,688 | 1 |
| `joint_defense_transitions` | 4,815,120 | 3,283,504 | 1 |
| `joint_open_prior` | 3,006,988 | 5,437,608 | 0 |
| `joint_accuracy_reply_selfdestruct_miss` | 1,210,904 | 1,667,800 | 0 |
| `joint_accuracy_own_selfdestruct_miss` | 1,123,828 | 813,352 | 0 |
| smallest (`joint_recharge_wait`) | 475,072 | 567,536 | 0 |

Progression of the broad benchmark: 181.0M (orchestration) -> 122M (lazy
regimes, scalar pair) -> 106M (scalar standalone) -> 82M (native compiler)
-> 75M (effect-class table, identity pairs) -> 59.1M (native families).

Broad-benchmark phase split now (one scan): native reply compile 20.9M
(1,524 compiles, about 13.7k cycles each), scalar standalone 11.2M (1,494
calls), scalar pair 8.1M (636 calls), orchestration arithmetic 7.7M, executor
reply standalone 2.8M (149 calls), whole-pair fallback 2.5M (20 calls, all
defense boosts), factored native pairs 2.1M (88 calls), unary fallback 1.8M
(25 calls), owned preparation 1.1M, HP tables 0.55M. `PublicDamageRange` runs
22 times and `ValuePublicExchange` 45 times, all for defense-boost replies.

What the target still needs (8,388,608 cycles): the per-reply compile has to
come down roughly four-fold (grouped base arithmetic by category and power
group across the reply set, so the formula runs once per group instead of once
per reply, with per-reply finishing), the scalar standalone and pair paths
need per-reply costs in the low thousands of cycles (they are 7.5k and 12.7k
today; both recompute plan addresses and gate reads that a per-defender cache
could hold), and the orchestration arithmetic (7.7M) needs the five-byte
record accumulation moved off SRAM temporaries. Defense-boost replies must
also become native before any timing claim: they are the only remaining
fallback and the only remaining producer calls.

#### Native defense-boost replies and the cold-bank move (2026-09-07, late)

- `984a531b`: `BossAI_FastFallbackPair` and `BossAI_FastUnaryFallback` moved
  to their own "Boss AI Fast Fallback" section behind far entries (order
  descriptor through `FS_ORDER`, executors and the standalone delta through
  three main-bank stubs in `fast_fallback_stubs.asm`); 777 bytes of the
  fast-prototype bank recovered.
- Native boost replies (Harden, Withdraw, Barrier, Acid Armor, Amnesia):
  both compilers emit `FSR_BOOST`=9 with the stages and axis in the hit bytes
  and zero damage flags (the reference's `.Reply` returns after
  `.DefenseBoost`, so only check flags reach the record). The reply executor
  treats the opcode as check flags only; the selector writes the identity
  standalone record for it (zero moment). When an owned plain damage plan is
  prepared, `.PlanVariants` computes its raw minimum at the start regime
  against the player's defense raised by one and two stages (physical) or
  special defense raised by two (special) through
  `BossAI_FastProjectPlayerDefense` (the player's public estimate raised with
  `BossAI_ProjectRaisedDefense`, then the player's screen, as
  `ValuePublicExchange.ProjectedDefense`) and the producer range; the eight
  three-byte slots live at `$a4f8..$a50f` (raw minimum, then range /
  supported / special-axis / valid bits), replacing the rarely used physical
  base-cache high part. A boost pair (`.BoostPair`) keeps the identity pair's
  flag rules and, on the reply-first hit path when the reply can act and the
  boost touches the plan's axis, runs the own hit through the compact
  executor with the variant amount (override at `$a4b4..$a4b7`, live only
  while its flag byte is exactly 1) and takes the correction
  V(terminal)-V(start) minus the own hit delta, doubled for a single order;
  mass 256 for the deterministic boost. Own boost plans stay on the fallback.
- Result: 25 of 26 ordinary decisions native-only (`joint_defense_transitions`
  keeps the fallback for the boss's own boost plan); broad benchmark 40.5M ->
  36.9M cycles; `joint_speed_tie_transformed` 12.6M. Per-pair boost
  corrections equal the direct fallback's on every boost reply of the broad
  case (`debug_joint_pairs.py`). Fixtures: `fast_reply.py` 30,720 (boost
  records and executor flags), differential 5,588, pair 3,744, standalone
  2,160/3,000, own executor 8,208, fallback 1,248/88, replacement 116,
  restart 52. Two defects the whole-selector comparison caught before the
  commit: the boost record's axis byte was clobbered by the store macro's use
  of BC, and the boost pair read the own hit delta with a clobbered plan slot
  and treated an axis mismatch as a match (carry from `cp`).

#### Evening pass (2026-09-07): 59.1M -> 40.5M

Seven further commits, each exact on the frozen oracle (76 vectors) and the
unit fixtures before it was made:

| Commit | Change | Broad benchmark after |
| --- | --- | ---: |
| `8c35e94c` | Move mirror keeps only the four bytes the compiler reads (756 bytes of bank freed) | 59.1M |
| `baa37c8a` | Per-defender chart table (two 2-bit row codes per attacking type, Foresight and Dragon majesty folded in), Scale skips divisors 1 and 2 and computes 217/255 with a shift identity, pair correction total uses 16x8 and 24x8 signed multiplies, 40x24 multiply shortcuts an exact 256 | 51.6M |
| `696dbb6b` | Scalar gate caches and standalone record writes from one base pointer | 47.4M |
| `3d9afcea` | Unrolled record clear, masked-regime loop, direct (H+1)/H and (H-1)/H passive ratios, keyed incoming-regime cache (state plus both maxima), base-pointer eligibility | 45.0M |
| `1bb3bd86` | Reply set bit table, equal-priority order once per defender, inline plan index, unary flags committed once per defender | 44.2M |
| `e47ed142` | Identity replies get a trivial standalone record (start state, zero moment, executor gate flags); aligned mask table first in the bank | 41.5M |
| `7e2db61a` | Packed passive contributions per epoch, power/5 once per compile, neutral accuracy stages skip | 40.5M |

Phase split now (broad benchmark, one scan): native compile 13.4M (1,524
compiles, 8.8k each), orchestration 6.7M, scalar pairs 5.3M (636 pairs,
8.3k each), scalar standalone 4.6M (1,494 replies minus 61 identity
replies per defender), executor standalone 2.4M (149 family replies),
fallback pair 2.4M and unary fallback 1.8M (defense boosts only), factored
native pairs 1.9M, owned preparation 1.1M, HP tables 0.55M.

Where the remaining factor of five has to come from. Every remaining item is
per (defender, reply) work, and 1,494 such evaluations leave about 5,000
cycles each for everything (compile, standalone, the active defender's
pairs and the loop overhead) inside the 8,388,608 budget; today each costs
about 27,000. A census of the compiled records shows 249 replies collapse to
about 140 distinct records per defender (the largest group is the 61
identity replies, already shortcut), so grouping identical records saves
under half of the standalone and pair work, not the five-fold needed. The
five bench defenders (1,245 of the 1,494 evaluations) need only the reply's
standalone moment and flags, and most of what the compile does for them is
defender-independent (effect support, accuracy before evasion and Bright
Powder, can-act, priority, recovery quota, uncertainty flags, hits). The
remaining plan is therefore: (1) free bank space by moving the cold fallback
evaluators behind far entry points (77 bytes remain in the bank); (2) cache
the defender-independent compile facts once per reply in WRAMX bank 2 (about
14 bytes per reply; the observation log leaves most of the bank free) so
bench compiles do only the amount, item and typing-dependent parts; (3) a
lighter bench standalone that produces the moment and flags without the full
record; (4) defense-boost replies native; (5) grouping identical records for
the active defender's pairs. The two-second target is not met and no timing
claim is made.

#### Native own defense-boost plans and two more cold sections (2026-09-07, night)

- Bank space first. `fast_results.asm` (input preparation, result clearing,
  finalization: once per decision) and the HP table construction in
  `fast_hp.asm` (`BossAI_FastBuildHPTable` and its five kernels: once per
  defender) moved into their own sections, "Boss AI Fast Results" and the
  page-aligned "Boss AI Fast HP Tables" (which carries the event mask table
  the rank kernels index), behind far entries: `BossAI_FastPreparePublicInputsFar`
  (C=kind, since farcall clobbers A) and `BossAI_FastBuildOwnHPTableFar` /
  `BossAI_FastBuildPlayerHPTableFar` (the mode mirrored through C). Both the
  finalizer and the builder reach `BossAI_FastDivide24By16` through farcall
  (memory operands; BC and carry survive the far return). The fast-prototype
  section went from $3f76 to $3d25 of $4000 with the boost code included
  (731 bytes free).
- The first build of that move hung on every decision: the finalizer still
  reached the divide with a plain `call`, and `check_cross_bank_call.py` had
  not flagged it because it read only `pokegold.sym`, where the
  reference-only sections do not exist. The audit now checks
  `pokegold_ai_reference.sym` as well, each sym on its own since a label's
  bank can differ between the builds; the reintroduced call fails it.
- Own boost plans compile to `FSP_BOOST`=7 with stages and axis at
  `FSP_DEFENSE_STAGE`/`FSP_DEFENSE_AXIS` and zero damage flags. The owned
  executor and the standalone builder accept the opcode as check flags only
  (the reference's `.OwnMove` returns right after `.DefenseBoost`), so the
  standalone record is the identity with zero moment.
- Reply amounts at the raised own defense. `BossAI_FastProjectOwnDefense`
  (producer bank) reproduces `ValuePublicExchange.DefenseBoost` for the boss
  (`.DefenseInputs`, `BossAI_ProjectRaisedDefense`), then the own screen and
  the known own item exactly as `.ProjectedDefense` applies a recorded own
  boost to a reply. It stages a representative boost move in the live AD for
  the duration because `.DefenseInputs` re-derives the axis from `AD_MOVE`:
  the first version read Special Defense for a Defense boost, so Barrier
  variants came out at 246 instead of 156, which `debug_joint_pairs.py`
  localized to exactly the two physical replies of `joint_defense_transitions`.
  The selector's `.OwnVariants` runs the bridge once per distinct boost of
  the active defender (slots Defense+1, Defense+2, Special Defense+2),
  quarters the result with the player's prepared attack through
  `BossAI_FastPrepareReplyFacts.TruncateStats`, and keeps the operand bytes at
  `FSA_OWN+16..21` with the slot mask at `FSA_OWN+22`; `.ReplyRegimes` stores
  the start regime index at `FSA_OWN+23`. After each native reply compile,
  `BossAI_FastCompileReplyVariants` runs `.Amount` once more per matching slot
  at the start regime with `FSM_VARIANT` selecting the operands (uncached,
  like Selfdestruct's halved defense) and stores the raw maximum plus a valid
  and a range bit per slot in the plain damage record's free bytes (7..8 and
  26..27 for the words, 23 for the bits: `FSR_VARIANT_A/B/FLAGS`).
- `.OwnBoostPair`: mass 256 for the boost, the reply's mass from its
  accuracy. Own first (or the own-first half of a tie) with a plan that can
  act and a valid variant runs the reply from the start state through
  `BossAI_FastExecuteReplyPlan` with `FSV_OVERRIDE` armed (the reply executor
  now honours the override for its raw maximum and range bit) and takes
  V(terminal)-V(start) minus the reply's hit delta, doubled for a single
  order; reply first is the standalone transition. Flags: the reply's
  standalone flags per positive event, the own check flags when an order
  reaches the boss (own first always; reply first when the reply's successor
  leaves both alive), and on the variant path the reply's flags at the
  variant instead of its standalone hit flags. An own boost against a
  multihit, False Swipe or Selfdestruct reply keeps the exact direct fallback
  (`.PlanPair` routes it before the native paths); against a boost or
  identity reply the existing pairs apply unchanged.
- Fixtures: `fast_plans.py` 252 (Barrier added; boosts expect opcode 7 with
  the axis/stage bytes), `fast_plan_executor.py` 9,072 (Harden, Amnesia),
  `fast_standalone.py` 2,430 (Harden). Four joint cases cover both single
  orders, two equivalent boosts on one plan set, both screens, Eviolite and
  the fallback route: `joint_own_harden_first`,
  `joint_own_barrier_screens_first`, `joint_own_boosts_eviolite_slow`,
  `joint_own_harden_multihit` (Assault Vest was tried first; it makes the
  boost itself illegal, so it tested nothing).
- Evidence on the final ROM: frozen oracle `--prototype` 88 vectors exact
  with 29 of 30 ordinary decisions native-only (`joint_own_harden_multihit`
  keeps the fallback by design), `--replacement-boundaries` 116, restart 60;
  per-pair native corrections equal the forced-fallback ones on all six
  boost cases (`debug_joint_pairs.py`); `fast_reply_native` 5,588,
  `fast_reply` 30,720, `fast_pair` 3,744, `fast_standalone` 2,430,
  `fast_reply_standalone` 3,000, `fast_plan_executor` 9,072, `fast_plans`
  252, `fast_pair_fallback` 1,248, `fast_unary_fallback` 88, `fast_results`
  1,011, `fast_hp` 1,614, `fast_math` 2,080/2,072, `fast_transitions` 4,722,
  `fast_producers` 1,000; the 843-fixture suite; `check_release_smoke.py`
  PASS; game ROM SHA1 unchanged `85a2fe838a28f23b198845e63876a637580e91a9`.
- Timing (`fast_ordinary_profile.py`, refreshed): `joint_defense_transitions`
  3.76M -> 1.54M cycles (its 2.33M of direct fallback is gone); the broad
  benchmark 35.76M -> 36.19M (+0.4M: the per-reply variant check, 1,524 calls
  at 104 cycles, plus far-entry overhead on the once-per-defender HP builds);
  `joint_speed_tie_transformed` 12.66M -> 12.83M. Every ordinary decision is
  now native except the designed multihit fallback; no producer runs during
  a native decision. Target 8,388,608, not met.

#### Speed pass (2026-09-07 night, continued 2026-09-08)

Commits, each exact on the frozen oracle (88 vectors, 29 native-only), the
touched unit fixtures and the 843-fixture suite before it was made; the game
ROM's bytes unchanged throughout (SHA1
`85a2fe838a28f23b198845e63876a637580e91a9`). Whole-decision numbers are
`fast_ordinary_profile.py` (24 ordinary fixtures in two scans):

| Commit | Change | Broad benchmark | Average decision |
| --- | --- | ---: | ---: |
| `f99cf46f` (start) | | 36,186,008 | 2,906,745 |
| `b5e52223` | Compile micro-optimisations: priorities in the effect class table (bits 2..3) and its bit 4 gating the effect-support special cases, power/5 as floor(205p/1024), H=2 ratios as shifts, eight-trial 16-bit division for a zero high byte | 34,620,404 | 2,835,019 |
| `35c36038` | `BossAI_FastPrepareReplyFacts`, the type chart mirror and its index in the cold "Boss AI Fast Reply Facts" section behind farcall (`BossAI_FastTruncateStatsFar` takes the pointer in BC; the hot compiler keeps `BossAI_FastTypeContribution`); the per-reply own-variant call skipped without boost plans | 34,511,344 | 2,830,517 |
| `4133fdbe` | Fast pairs: per-plan facts (`.PreparePlanPairs`: the reply's regime after the own hit, gate, own flags per regime and on a miss, z_own) and per-reply facts (`.PlainStandalone`, which also replaces the scalar standalone for plain damage replies) make K1/K2 two compares unless a hit changed the other side's amount regime or fainted an actor; weight*z_reply*K accumulates per plan in WRAMX bank 1 ("Boss AI Fast Sweep State", reference build only) and z_own multiplies once at `.CommitPairs` | 31,074,396 | 2,596,931 |
| `0b91d7d8` | Own recovery plans on the fast pairs (heal from the HP the reply left; Rest transition below the maximum); bench defenders write only the two standalone flag bytes; `.ReplyMass` fills a page-aligned per-move weight table the sweeps read; arithmetic `.PlanAddress`; the actor import and the recovery quota in cold sections | 27,696,268 | 2,388,164 |
| `efcc0382` (2026-09-08) | The compile's regime loop re-stores the first regime's amount for the remaining masked regimes when neither the Fire passive (attacker low) nor the Ice passive (defender high) can apply, the only two places the regime bits reach an amount; decided only after a first amount stored and only when a second masked regime exists. 198 of 979 amounts on the broad case (the 11 multi-hit moves at four regimes per defender) | 27,067,104 | 2,360,134 |
| `6cebb74a` | Per-reply amount facts computed once (the defender's chart rows for the reply's type, whether a no-effect row halves, whether any type passive can apply): the matchup probe is a 32-entry table (`.MatchupByRows`), `.Chart` and `.Passives` read the facts; the contact flag folded into bit 7 of the moves mirror's type byte (the 254-byte contact mirror gone; `fast_contact_N` comes from the generated `engine/battle/ai/fast_contact_flags.inc`, `scripts/generate_fast_contact_flags.py` from the untouched `data/moves/contact_flags.asm`, drift caught by `tools/audit/check_fast_contact_flags.py` in the release-smoke floor); the record clear skips the bytes the header always writes; `.Div24By8` skips the first eight trials when the high byte is below the divisor; `.variation` keeps the pre-roll amount on the stack and skips unit post-roll multipliers; the reply standalone writes delta zero when an event's successor equals the start state; the reply executor computes the regime for the hit event only (`.SelfFaint` shared); bench imports keep the player HP table built by the active import (`wFastPlayerTable`, C bit0) | 26,128,232 | 2,317,392 |

The bench reply cache in WRAMX bank 2 (the brief's step 1) was built,
verified byte-exact through a fill/use fixture, and reverted: after the
compile micro-optimisations the defender-independent facts cost about 1.2k
cycles per compile, so the cache saved 0.27M on the broad case for 650 bytes
of hot bank and an interrupt-atomic bank window. A bench compile pays for its
amounts, not its facts.

Per-pair differential (`.local/ai-two-second/wt_debug_fastpair.py <case>`):
every fast pair of the broad case replayed through `BossAI_FastScalarPair`,
0 of 636 differ. It found the two defects of the fast-pair commit before the
oracle did: `.PlanPairFacts` clobbering A before the union OR (the flags byte
became the WRAM page), and per-reply facts left over from the previous plain
reply on multi-hit, recoil, drain and recovery replies (the eligibility byte
is now cleared for every reply before its standalone).

Attribution of the broad case after `0b91d7d8` (27.64M): native reply compile
11.33M (1,524 compiles, 7.4k each), sequential family standalone 2.41M (146
replies, 16.5k each), factored family pairs 1.81M (88, 20.5k each), plain
standalone 1.50M (784), reply/own preparation `PreparePublicAction` 1.07M
(10 calls), fast pair flags 0.98M (520 pairs, 1.9k each), pair dispatch and
order 0.94M, actor import 0.64M (6, the player table rebuilt each time),
K2 for recovery plans 0.60M, incoming accumulation and flags 0.90M,
identity classification/standalone/pairs 1.30M. Two ordinary fixtures remain
over the 8,388,608 budget: `joint_broad_prior_mass` and
`joint_speed_tie_transformed` (8.77M after `0b91d7d8`); 22 of 24 are under.
**The two-second target is not met.** What the numbers say: after the pairs,
the per-reply floor is the compile's amount pipeline (about 3.9k cycles per
amount) plus the record clear and header (about 1.5k), and 1,524 compiles at
that floor alone exceed the budget; reaching it needs the compile's per-reply
cost cut roughly threefold, which is grouped amounts (Milestone 4) rather
than more trimming.

Continued 2026-09-08 (worktree `.claude/worktrees/nostalgic-wu-e45477`,
branch `claude/nostalgic-wu-e45477`, fast-forwarded into `master`). Two code
commits, `efcc0382` and `6cebb74a`, rows above; every gate exact on each
(oracle 88 vectors, `fast_reply_native` 5,588 compiles byte-exact, per-pair
differential 0 of 636, `fast_reply_standalone` 3,000, `fast_hp` 1,614,
`fast_standalone` 2,430, the 843-fixture suite, `check_cross_bank_call`,
`check_release_smoke`; game ROM SHA1 unchanged). Broad benchmark 27,696,268
-> 26,128,232, average 2,388,164 -> 2,317,392, `joint_speed_tie_transformed`
8,775,728 -> 8,726,488; 22 of 24 fixtures under budget, the same two over.
**The target is still not met.**

Measured before building, and dropped: the per-defender amount memo keyed by
(power/5, type, category, postrolls, regime) that headed the remaining list.
A census of the broad case's amount stream (`.local/ai-two-second/
nw_amount_census.py`, `nw_amount_keys.py`) gives 961 memo-eligible amounts
per decision with 241 possible hits (25%: the same 118 distinct keys on every
defender, post-roll bits constant, regime 2 for 123 of 156), each hit saving
about 3k cycles: a gross ceiling of 0.67M against 0.4-0.5M of miss-path and
key overhead, 372 bytes of SRAM and most of the hot bank's free space. The
best cheap hash (`power/5 + 7*type + 8*regime`, 62 slots) reaches 223 of
those 241. Its one real component, the multi-hit moves' four regimes sharing
one amount, became `efcc0382` instead.

Whole-decision phases of the broad case after `6cebb74a` (26.13M): native
reply compile 11.17M (1,524 compiles, 7.3k each), orchestration 3.50M, scalar
pair 2.49M, native pair 2.47M, scalar standalone 2.29M, family (sequential)
standalone 2.19M, owned preparation 1.24M, HP tables 0.34M (the player table
built once), reply facts 0.22M, entry 0.11M, finalize 0.06M. Inside the
compile, the header and glue that run for every reply (record clear and move
facts 0.84k, Descriptor with the amount facts and the first-regime scan
~1.0k, Accuracy 0.43k, HitUncertainty 0.43k, PlayerCanAct 0.28k,
MultiHitItemState 0.23k, EffectSupport 0.22k, Priority 0.17k, RecoveryQuota
0.15k and the rest) cost about 4.0k per compile, more than the amounts
(Formula 4.1k on the 271 base-cache misses, variation 0.78k, Passives 0.56k,
probe 0.24k, Chart 0.21k per amount). Attribution logs:
`.local/ai-two-second/nw-attr-compile-0.log` (start), `-a3` (after
`efcc0382`), `-b` (after `6cebb74a`; the compiler bytes of that build are the
final ones), `nw-attr-orch-a3.log` (orchestration:
`PreparePublicAction` 0.78M for 10 calls, own and player HP tables 0.26M
each, `PrepareReplyFacts` 36k per defender, `ReplyMass` 0.19M),
`nw-attr-family-a3.log` (the family standalone at 16.5k per reply: executor
validate/represented/Regime/done glue 4.5k per event, `Delta` 2.3k per
event, Moment 1.9k).

An independent read-only review (Opus 5, 2026-09-08, requested by the
project lead; `.local/ai-two-second/cut_candidates_2026-09-08.md`, scratch)
listed 13 things the selector computes whose cost exceeds their plausible
effect on the decision. Nothing from it is implemented; the lead rules on
each item. Its headline changes how the target should be read:
`joint_broad_prior_mass` is a level 50 Smeargle, and `BossAI_BuildPublicReplySet`
(`engine/battle/ai/public_replies.asm`) emits the 254-move set only for
Smeargle, a Transformed mon or an unreadable species byte; every real species'
natural prior at level 50 has 2 to 58 moves (median 36, Nidoqueen the
largest) and four revealed moves close it to five. The sweep is close to
linear in reply count, so the worst realistic decision projects to about
8.1M, inside the budget, while the two fixtures over budget are both
254-move priors. The other large items: a shared record for the 85 zero-power
identity moves (3.9M, exactness-preserving as grouping), bench defenders
against revealed moves only (15.0M, a fairness cost the lead must weigh),
multi-hit exactness (1.9M), pairing every reply against four own plans
(3.1M), drain/recoil bookkeeping (1.0M); Explosion and Pursuit are explicit
keeps.

The [replacement profile](fast_replacement_profile.json) was refreshed on the
restructured bench loop: the largest native sample is 623,988 cycles
(`replacement_hp65535_spikes2`, oracle 925,704); among maxima <=999 the largest
is 507,436. Same limitations as before.

- 2,080 divisions and 2,072 signed ring products passed, including signed and
  carry boundaries, stack/context preservation, and SRAM write footprints.
- 1,614 HP builds, 121,402 table bytes and 46,268 lookups passed. Cases include
  smaller/larger buffer reuse, both owned weights, mode boundaries, all offsets
  in early rank blocks, maximum HP 65,535, and invalid construction inputs.
- 1,011 finalizations/rejections, 66 real cross-bank input preparations, and
  all 26 existing joint fixtures' exhaustive numerator vectors passed.
- All 839 existing boss-AI decision-path fixtures passed.

Later batches passed 46,268 HP-potential comparisons; 4,722 HP transitions;
9,440 drain/recoil comparisons; 2,592 recovery-quota/reference comparisons;
2,108 compound damage scripts and three tag rejections; and 1,000 action/setup/
range exports with three direction rejections. These include the documented
DE/SP, context and SRAM write boundaries. Primitive/bridge tests do not prove
full ordinary-action reachability.

Both the standalone restart and prototype passed all 26 existing joint fixtures
in forward/reverse traversal: 52 complete frozen-ROM numerator/mass/score/flag
vectors each, plus five invalid entries. Another 58 replacement fixtures passed
116 vectors and five invalid entries, covering HP maxima 1..65,535, five bench
slots, all Spikes layers, Flying immunity, item flags and win-condition weights.
Two malformed third-bench cases force restart after partial native results in
both scan orders; the final status 2 vector still matches the frozen reference.
The final expanded replacement run also verifies no RNG consumption.

[The HP profile](fast_hp_profile.json) sweeps every maximum from 1 through 999
for each actor/weight class. The conservative six-owned-plus-player construction
sum is **388,920 DMG T-cycles**, including seven calls, excluding caller argument
loading. Rank lookup is 208 cycles in the body, 232 including its call. These
measurements fit the respective helper assumptions; they are not whole-selector
measurements. Wider-domain lookup/construction is correct but outside that sweep.

Three preliminary 12-legal-record finalizer cases at mass 564 measured 61,060,
61,876 and 62,356 cycles for scores 0, 1024 and 2048. These are examples, not a
proven worst-case bound. They include SRAM closure and exclude caller setup.

[Replacement timing](fast_replacement_profile.json) measures 112 five-bench
decisions against the frozen unprepared selector, from bank-qualified entry
through return. Every sampled native decision is faster. The largest native
sample is 622,476 DMG T-cycles (about 0.15 seconds), versus 925,840 for its matching
reference case. Among sampled HP maxima <=999, the largest native time is 505,924
cycles. These are measured replacement samples, not a whole-domain or ordinary
decision timing guarantee. Caller argument loading and production integration
are excluded.

#### Reply sets: transformed player mon and Smeargle (2026-09-08, `30c3dfc8`)

Approved by the project lead and co-signed by an independent Opus 5 review
before landing (zero blocking findings; its non-blocking ones are folded in).
`public_replies.asm` is compiled into the reference build only, so the reply
set change lives in the reference selector; the game ROM gains only the
recorder hook in the Transform effect as forward wiring (its bytes change for
that alone). `BossAI_BuildPublicReplySet` gave a Transformed player mon and
Smeargle the full 254-move set. Transform copies the moves of the boss's own
Pokémon that is out, which the boss knows exactly: `BossAI_RecordPlayerTransform`
(platform hook called from the Transform effect, so it covers the Transform
move, this hack's Ditto Imposter auto-transform and a Metronome or Sleep Talk
Transform) remembers the own party slot in `wBossAITransformSource` (the
retired `wBossAILookaheadRunningBest` byte, no WRAM offset moved, zeroed by
`ClearBossAIState`), and the reply set while the player stays transformed is
that slot's four moves plus Struggle, flagged as a closed set
(`PR_FOUR_REVEALED_F`: the whole moveset is known). A transform with no record
(unreachable in a boss battle; pinned by fixtures) stays broad. Smeargle's set
is the revealed moves plus the lead's authored expectation
(`.SmeargleExpectedReplies`: Sketch, Spore, Spikes, Baton Pass, Substitute and
the set-up moves) plus Struggle, since
Sketch can copy anything and a veteran expects exactly those. Neither is a
hidden-information read: the boss reads its own party's moves and remembers a
transform it watched happen (`check_boss_ai_no_cheat` passes).

Fixtures: `replies_transformed_known`, `_known_bench_slot`,
`_known_with_observed`, `_recorded_by_effect` (through the recorder with the
player's turn), `_recorded_boss_turn_ignored`, `_recorded_no_boss_ignored`, `_source_out_of_range`,
`not_transformed_ignores_source`, `sketch_prior` (authored), `sketch_prior_with_observed`;
joint `joint_transformed_known` and `joint_broad_nidoqueen` (the widest natural
prior of any species at level 50, 57 moves plus Struggle, tied with Mew: the
realistic worst case now that Smeargle's set is authored);
`joint_broad_prior_mass` is renamed `joint_smeargle_authored_prior` for what it
now measures; `joint_speed_tie_transformed` records the copy as every boss
battle would. The harness zeroes `wBossAITransformSource` per seeded
battle as the game does at battle start. The frozen oracle was rebuilt from
this source (`.local/ai-two-second/preflight-2026-09-08-replies/oracle`, replacing
`preflight-2026-09-06-pro2`) because the reply set is an input to both
selectors; 94 vectors exact. 853 fixtures pass; release smoke passes on the
rebuilt game ROM.

Whole-decision timing after this change (30 ordinary fixtures x 2 scans):
worst `joint_broad_nidoqueen` 8,143,568 (scan 15) and 8,135,984 (scan 0)
against the 8,388,608 budget; `joint_smeargle_authored_prior` about 3.6M;
average 1,486,638; **no ordinary fixture over budget**. The headroom on the
realistic worst case is about 3%, so the approved exactness-preserving cuts
(shared identity record, heal-effect gate, False Swipe as identity, reply-side
minimum roll, Helmet gate) are still worth landing for margin; the cost of an
unrealistic 254-move prior is no longer the gate.

## Independent review

The existing Astra-low reviewer approved each arithmetic, HP, and boundary
batch, then approved the assembled foundation after the 839-fixture pass.
Approval explicitly includes retaining the HP/math helpers, enumeration/reply
semantics, joint/reference model, production code and memory allocation.
The reviewer subsequently approved all HP primitives, potential, compound damage
script, producer bridges, standalone restart, and native replacement batches,
including their stated retentions and the replacement timing methodology. Required
partial-native-state restart coverage was added and passed. No required batch
findings remain. This is not approval of ordinary native selection or production
integration/performance gates.

All 839 existing decision-path fixtures also passed on the earlier assembled
ROM after the native replacement additions.

The subsequent owned-action batches passed 1,000 prefix/flag/range comparisons,
960 recovery-prefix cases and six input rejections; 240 complete amount-plan
records and four input rejections; 6,048 native owned-action/reference comparisons
with producer poisoning; and 2,160 actor imports and full standalone records,
including exact signed moments for accuracy 0, 1, 128, 254 and decoded 255.
Standalone coverage includes both own weights, distinct own/player maxima and
eleven no-write actor/standalone rejection cases. The independent reviewer approved
each of these bounded batches and its retention decisions. All 839 existing
decision-path fixtures also pass on the assembled actor/standalone ROM; its log is
`.local/ai-two-second/ordinary-standalone-foundation-fixtures.log`.

The incoming/pair checkpoint adds 19,200 incoming action comparisons, 1,200
complete incoming-plan comparisons and 13 absent/rejected cases; 3,000 complete
incoming standalone records/moments and three no-write rejections; 1,728 native
pair comparisons (both full numerator and correction-only outputs) and seven
no-write rejections; and 1,248 direct fallback full/correction comparisons with
six no-write rejections. Owned/incoming action tests also verify `FlagsOnly`
against the reference and guard every continuation byte. The 6,048 owned-action
and 2,160 owned-standalone checks remain passing after this extension.
The independent reviewer explicitly approved these final batches and all stated
retentions. No ordinary full-selector timing claim follows from these unit checks.
All 839 existing decision-path fixtures pass on the current checkpoint ROM;
the complete run is saved in `.local/ai-two-second/pair-checkpoint-fixtures.log`.
The current-ROM 2,160/3,000 standalone and 1,728/1,248 pair/fallback checks were
also rerun successfully before pausing. The build and `git diff --check` pass.

Checkpoint memory lifetimes: incoming plan bytes 399..446 are persistent across
producer-prefix rebuilds; its standalone builder writes only bytes 28..42 of that
record. `FSE_MODE` at $a54b aliases the low standalone-delta byte sequentially:
an action/flag pass resets it, and Delta runs afterward. Pair control uses the
previously unused executor tail $a54c..$a55f. Its five-byte output uses common-sum
space $a578..$a57c, leaving $a57d..$a58f for subsequent common-sum work. No part of
the 64 uncommitted bytes at $a5c0..$a5ff has been assigned. Pair flags and totals
must be consumed before reusing their scratch. Source generation helpers under
`.local/ai-two-second/make_reply*.py` were one-time construction aids and are not
the source of truth; later reviewed edits exist only in the checked source files.

Reviewed assembly hashes:

```text
fast_math.asm    9c35bb2b13c8db28d24bef315d14538e0771ac98aa9a12c405680b70357171f3
fast_hp.asm      f96f2c7eb809a17ea5159f501130e6a593d4aa1ec22c8eb40dc2f2f50ad67803
fast_results.asm cd853d6afec817bbee9fcd827144f7e0dbed7d1823fe95566395c9224a5ded93
fast_transitions.asm a6c4999f6aa4dae17df1d0e413c0687ebe03dee190f38a2db8cc9c7a5eb32cf5
fast_producers.asm 18e25836a5f092361632d3d7ec02c186be4c137e0e5ba642066b2d14f6ac5147
fast_plans.asm c1c18799daa56aba372220782a2ca1ba049f4ad418858be42a4048539a187afd
fast_plan_executor.asm e803f23d7166903bda4fb8df042aa1427ddcfe7dc20a721883226f5e4d413080
fast_actors.asm 18255e39e900d82edb5baf7f3f45bb5c75faa7afd2737f260f014adaa1ccccc1
fast_standalone.asm 1b70b2dc079101745916e5b2e35dcaf19d9abd1e58990a544137ec99e5478d91
fast_reply_plans.asm 32bc75ffb044974136000eee1b3a2e01cd92c32a06363183e2f8cbb1db7100f4
fast_reply_executor.asm 0db86161b68452135b9b1bb2f2ec89bb158de27ba725f4be91276ed1a8e2d89e
fast_reply_standalone.asm 914b6063c22332852da509227dedc496ddfdb61a865421cfb3f828828e947478
fast_pair.asm e2f7b65cf7aef21641898fc198bc6013b6f94201dcb7c1009695effc14d2b17d
fast_pair_fallback.asm 215fe368862fa7c4a935a7103073773276d261881d0d9d5e319efe11f6cf36bf
fast_reference.asm a257a1ccc353e604b371e580d08a9171d9f8fb19a792edc210344e377d314f56
fast_selector.asm 24ebc0a9238f4d0233ea04b02fe4346eb8aeac03f3aff14775019aa21659b1e5
```

Files changed by the 2026-09-07 orchestration work (current hashes; these
have **not** received the independent Astra-low review, see below):

```text
fast_selector.asm 0b174edc9a349cc51f1df2ba21a10d942b159fcfdf5bfec57579cc9c2f2d0e5c
fast_pair_fallback.asm 2348bf94cfbacbdb4a978f2a4ef4ba8d0f657bd67cd4633dc66a056dd5800ee1
fast_producers.asm 9528a1c0d9db87d11da4e79f5797f7ff54004c22a9dec51e9738c98b6295e428
fast_reference.asm 7022b6c18801153224fb42c5ab88b09fcb96927123b7cb0739621b6e19b0ef13
```

`fast_pair_fallback.asm`, `fast_producers.asm` and `fast_reference.asm` were
only appended to (common-sum definitions and `BossAI_FastUnaryFallback`;
three bridges; `BossAI_FastForcedAction`). `fast_selector.asm` was rewritten
around the unchanged replacement logic. The review gap: the Astra-low
reviewer configuration was not available in this session, so the orchestration
was validated by the frozen-oracle comparison, the new unit fixture and the
full fixture sweep, and self-reviewed only. It should receive the independent
review before it is treated as approved.

Files changed by the later 2026-09-07 performance and native-family work
(current hashes; same review gap, validated by the fixtures listed above):

```text
fast_plans.asm 672876ee78e43d14f3a40dbf52b17cca35e8108b0293f0965e2c597535e69163
fast_reply_plans.asm bda0f5afaf9c130540d69aeca5ea7bc300429a0a9d7029f7900cc1a5ddc33e87
fast_reply_native.asm 198e56766aa81c15445a42f2a5f645a2aec0ed9130a5538dea3f746a763f3085
fast_scalar_pair.asm (new, see git)
fast_plan_executor.asm 63a299dea21cc72733f26d34b1a38e6b592b223a66bc41dd6667289c2da5513d
fast_reply_executor.asm 73a62a5b980c13b200976346247b08ab9a3667108e9f82d11e5d9ee853749427
fast_standalone.asm 4fb3ed3cd29761eaa72a5956284a7c9fbade0d4b760eb51d6d6e4061795fd898
fast_reply_standalone.asm 1d8cefb427bee2a15a8ad0fe5927b1d3e8d48578286f267f6889137ef502218d
fast_pair.asm 995d0cad6fef7c718587212be1166de8bdf652fcc46c85d19c821979c274b034
fast_pair_fallback.asm 897b6b7e62e34789a1f5e243888f8c1d0aa68e1ae8e7b1122a8933be57e7af39
fast_selector.asm 7631bf01eea887f3e3379b7c58f72d28c6c289cb34fa117bf279a9d195733084
```

Files changed by the 2026-09-07 night work (own boosts native, results and HP
construction in their own sections; same review gap, validated as listed in
that section):

```text
fast_plans.asm fb77a16f9522d1767709dae48d0c9df8cd3137a990a47d8eb7d4ce471d50848a
fast_plan_executor.asm 82b2a5e7887f1a961590aefd40397ce9ee307c1348e399adb9257bc8e0ab0ebd
fast_standalone.asm a0484b2ec88cfa543886d3b884f5adc995cc3133b9130c9bbcd06b2a0cd7a8f2
fast_reply_plans.asm 3177ae0f15f0f7ca6124027621d507b9688f44ce9c75d1b506e52d972f8de35d
fast_reply_executor.asm b4aed9efccb89e9ccec7bbf7b5a34344900868ea197024b744ce9014b20e6329
fast_producers.asm b655f6dae2b1cef632b359bca04bae7fc2f9897b63c39ef3ac2b263bbcc2bdf2
fast_reply_native.asm 194eb86e26c8a2f7a710e9976979a81e96a80df75c5c57a112cf1607a827e35c
fast_selector.asm 0d35b8ffa6f255cd1e8d520eb95f7a7b273bf31fd3441ddad7b220b3e7f6c5b9
fast_results.asm 170e6f24b2c067ca919ebe2868d934a0003529574add7894682b0f434d22a65a
fast_hp.asm 8e65ce76c55834fdd7569d81a670b60a2355546f8a070f73f911eaaca1eb9cf8
fast_hp_masks.asm cc2d1b2040b68c6d05b8c311eed94a7f765a3bb85774ba0173b0016deaac2e41
fast_actors.asm 28630ab2adc96ab95e463c9c6106a6cf505c0d129c806fa09b14b13985633ef5
```

The "Boss AI Fast Prototype" section is at $3d25 of its $4000 bank after this
checkpoint (731 bytes free), with the results/finalizer code in "Boss AI Fast
Results", the HP construction and its mask table in "Boss AI Fast HP Tables"
and the fallback evaluators in "Boss AI Fast Fallback", all behind far
entries. Cross-file `call`s inside the remaining fast files still assume the
one hot bank; `check_cross_bank_call.py` now audits the reference build too.

## Remaining implementation

Ordinary orchestration, switch/wait handling with an explicit post-entry
baseline, the unary fallback, lazy reply regimes, the fast pairs and plain
standalone, the native reply compiler, the native families and both
defense-boost directions are implemented and match the frozen reference on
every joint fixture; the only remaining fallback route is an own boost
against a multihit, False Swipe or Selfdestruct reply. The broad benchmark is
above 8,388,608 (see the speed pass above for the current number). Still
remaining, in the order the attribution suggests:

1. **The lead's ruling on the cut list** (see the speed pass above). Capping
   the unbounded Smeargle/Transformed prior changes an input to both selectors
   and needs a refrozen oracle; a shared record for the 85 identity moves is
   exactness-preserving grouping (the census shows 61 byte-identical records
   per defender) and saves 3.9M on the broad case.
2. **Family replies** (2.19M standalone plus about 1.8M of pairs): a fast
   standalone and fast pairs for drain/recoil and multi-hit replies. The
   sequential executor's cost is mostly glue (validate/represented/Regime/
   done about 4.5k per event, `Delta` 2.3k per event, Moment 1.9k); the
   family arithmetic itself (`.MultiPath`, `BossAI_FastDamageScript`) is small
   and reusable.
3. **Owned preparation** (1.24M): `BossAI_FastPrepareOwnedCandidate` runs
   `PreparePublicAction` once per plan (78k each, 10 calls in all) although
   `BossAI_PrepareIncomingActor` and the speeds repeat for the same actor;
   `PrepareReplyFacts` costs 36k per defender; `ReplyMass` 0.19M.
4. **Per-reply glue** (about 2.5M): `AccumulateIncoming` 0.9M, `PrepareReply`
   0.41M, `ClassifyIdentity` 0.58M, `reply_next` 0.26M, the identity
   standalone/pair trio, `PlanPair` dispatch 0.84M.
5. **The compile's header** (about 4.0k of its 7.3k per reply): most of it
   depends on the move and the player, not the defender, and is recomputed
   for all six defenders; the amounts below it are near their floor without
   grouped base arithmetic (Milestone 4). The memo is measured out (above).
6. Adversarial-domain fixtures (maximum candidates and replies, both sides
   uncertain, Fire/Ice thresholds, complex after-effects), then the isolated
   and integrated timing gates and the production ABI/interrupt ownership work.

The [implementation contract](../selector_implementation_contract.md) remains
the authority for semantics, memory lifetimes and acceptance gates; its
"Implemented allocation" note records the control/common-sum bytes this
orchestration uses.
