# Exact selector implementation status

Updated 2026-09-07. Paused at the user's request after the reviewed pair/fallback
checkpoint. The complete native selector is **not implemented or integrated**.
The two-second whole-decision target remains unverified. The private prototype
now evaluates replacement decisions natively and routes ordinary decisions through
a complete slow compatibility restart. It is included only in `BOSS_AI_REFERENCE`
builds; no gameplay caller exists.

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

## Validation and timing

Current reference ROM SHA256:
`65e403fb5e8b4e64b8f05d38820f7cf87ba239f9545986afa24a58413989ee75`.
The replacement measurements below used
`1c6ecae2e9940f0532a67d5c3b86a2038a27850be8c9b0a10eceafb73c21e787`.
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
python -m tools.boss_ai_fixtures --rom pokegold_ai_reference --suite all
```

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

## Remaining implementation

Shared incoming accumulation/grouping, defense-change invalidation, native
ordinary/switch/wait orchestration and unary fallback remain. The currently
excluded owned families
also need their required native coverage. The assembled selector must pass
full-record comparisons against the frozen
reference, traversal and hidden-information checks, native phase measurements,
and the complete timing gate before production ABI/interrupt ownership work.

Resume with selector orchestration: compile up to four owned plans once, initialize
each total with `1024*D + (M<<8)*mu_own`, stream a reply once per defender, accumulate
the signed incoming moment sum, and consume correction-only native or fallback
results for each plan. Add `512*B` before changing defender scope. Actor order facts
and candidate adapters still need implementation. Unary switch/wait handling needs
an explicit post-entry standalone baseline and plan lifetime; do not reuse the
current move-only fallback formula with a pre-entry reply moment. No orchestration
or unary implementation was started before this pause.

The [implementation contract](../selector_implementation_contract.md) remains
the authority for those semantics, memory lifetimes and acceptance gates.
