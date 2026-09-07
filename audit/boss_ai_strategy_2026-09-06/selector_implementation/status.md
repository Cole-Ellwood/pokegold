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
  Defense boosts, Selfdestruct, multihit, False Swipe and Super Fang currently
  receive explicit fallback opcodes. Amounts require fixed non-HP context inputs.
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
- Unrepresented replies (opcode 0: defense boosts, Selfdestruct, multihit,
  False Swipe, Super Fang, and anything the compiler rejects) use the new
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

## Validation and timing

Current reference ROM SHA256:
`83070fc20a59f278f82d9f7052510285aba956aab563a53cef4493b383048d01`
(pair/fallback checkpoint before orchestration:
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

## Remaining implementation

Ordinary orchestration, switch/wait handling with an explicit post-entry
baseline and the unary fallback are implemented and match the frozen reference
on every existing joint fixture. Still remaining, in the order the profile
suggests:

1. **Reply regime laziness** (cheap, no new arithmetic): compile only the HP
   regimes a reply can reach for this defender and its live plans, mark them in
   `FSR_VALID`, and have the executor reject an unmarked regime so the
   selector falls back rather than reading a zero amount. Expected to cut the
   dominant reply-preparation phase two-to-four-fold; not sufficient alone.
2. **Milestone 4 native amount arithmetic** streamed by defender, category,
   power group and reply (grouped incoming bases, five-power-step recurrence,
   finishing in original order). This is the only route to the target: the
   producer-backed reply preparation is twelve times the whole budget.
3. **Native coverage of the fallback families** (defense boosts with variant
   staging and invalidation, Selfdestruct, multihit, False Swipe, Super Fang)
   and reply grouping by continuation with three-byte group masses. The broad
   benchmark spends 27M cycles in fallbacks today and 19k cycles per native pair
   against a 1,100-cycle target.
4. Adversarial-domain fixtures (maximum candidates and replies, both sides
   uncertain, Fire/Ice thresholds, complex after-effects), then the isolated
   and integrated timing gates and the production ABI/interrupt ownership work.

The [implementation contract](../selector_implementation_contract.md) remains
the authority for semantics, memory lifetimes and acceptance gates; its
"Implemented allocation" note records the control/common-sum bytes this
orchestration uses.
