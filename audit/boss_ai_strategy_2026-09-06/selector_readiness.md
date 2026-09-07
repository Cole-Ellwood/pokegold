# Selector preimplementation readiness

Prepared 2026-09-06. Scope: get the design, baseline, contracts, evidence, and
validation sequence ready before writing the new selector. No implementation
assembly, production policy, or fixture source was changed in this preparation.
Existing source was rebuilt and tested; supplied arithmetic code was copied
unchanged and run. This is readiness for a restricted offline prototype, not
approval to integrate a two-second selector into gameplay.

Pro's [final review](selector_preflight/pro_final_review.md) found no architectural
blocker and required two narrow clarifications before bridge coding. Both are now
in the contract: A/HL input and A-result marshaling across banks, and restoration
of the complete read set/epoch required by the next legacy helper after fallback.
No new oracle freeze, broad preparation pass, or pre-prototype timing proof is
required. The additions below are implementation tests, not claims of new tests run.

## Read this package in order

1. [Updated roadmap](two_second_roadmap.md): stages, scope, and acceptance gates.
2. [Implementation contract](selector_implementation_contract.md): exact ABI,
   memory, algebra, fallback, uncertainty, and phase allocations.
3. [Evidence manifest](selector_preflight/manifest.json): source/build identities,
   results, reproducible commands and limits.
4. [Pro second review](selector_preflight/pro_second_review.md): preserved design
   rationale; local contract takes precedence where it resolves assumptions.
5. [Independent review](selector_preflight/review.md): final disposition.

Claude's earlier analysis and the broader strategic roadmap remain historical
context. Full power rows, ordinary-only factoring, older scratch allocations,
and older timing forecasts are superseded by this package.

## Decisions ready for implementation

| Decision | Disposition and reason |
| --- | --- |
| Hybrid factoring | Adopt identity-inactive transition factoring, scalar ordinary corrections, compact deterministic active-active executor, explicit Selfdestruct special handling |
| First slice | Include recovery and Life Orb/drain immediately, alongside identity, ordinary/fixed/level damage, conservative incoming KO, switch/replacement/wait |
| Oracle | Freeze current tested offline reference; retain direct unprepared pair evaluator and earlier artifacts for comparison |
| Records | Four 64-byte plans, one 48-byte reply, two 24-byte continuations, twelve 10-byte full results, phase-separated 324-byte producer workspace |
| Probability arithmetic | Combine tie corrections first; signed 24-bit standalone moments, signed 32-bit shared moment, 24-bit group masses, 40-bit grouped products/totals |
| HP backend | Direct/rank8/threshold modes with explicit domain checks; actual lookup present in the structural prototype |
| Damage backend | Grouped bases with five-power recurrence where catalog-proven; direct base fallback; no mandatory 512-byte power row |
| Pair fallback | Direct 89-byte prefix, original positive-mass branches, complete pair replacement, separate cost/flags; no old full selector inside live scratch |
| Return ABI | Indexed WRAM output is authoritative; no A-result promise through existing FarCall; future public wrapper reloads index |
| SRAM | Closed entry, explicit bank 0, closed exit; no untracked prior-bank restore promise; legacy HP table entry forbidden |
| Prototype environment | Stable public state, IE masked by harness, no callbacks/graphics/RTC, exclusive animation/decompression scratch |
| Production | Separate later entry/ownership/interrupt/latency/ABI gate; no long interrupt masking adopted as gameplay solution |

Zero standalone utility is not an identity certificate. Every transition's
continuation dependencies, rather than its initial result, determine reuse.
Original accuracy masses and reachable uncertainty remain separate from scoring
normalization. No new combat semantics, hidden information, pruning shortcuts,
or deeper search are included.

## Frozen baseline and checks

Fresh forced build: Gold BOSS_AI_REFERENCE, using the documented WSL make path
and repository RGBDS 1.0.1 Windows tools. ROM SHA256:

    b6ccc77d19649750a722a0029578d413063e28273ad68233e2cb2f7d4fefe2d6

Local immutable comparison copy:
`.local/ai-two-second/preflight-2026-09-06-pro2/oracle.{gbc,sym,map}`.
The same directory contains `review_source.zip` and `source_manifest.json` for
433 relevant source/test files. This is a focused source snapshot, not a complete
standalone checkout with every build asset. The manifest also identifies the
working-tree revision; a Git commit alone is insufficient because work is mixed
and uncommitted. Do not rebuild over the immutable oracle.

| Check | Result | Evidence |
| --- | --- | --- |
| Existing full decision-path fixtures | 839 passed | [fixture log](selector_preflight/fixtures.log) |
| Complete prepared/direct actor contexts | 49,152 passed | [actor log](selector_preflight/actor.log) |
| Accuracy cache/raw-byte/stage/item/type comparisons | 18,432 passed | [accuracy log](selector_preflight/accuracy.log) |
| Cached/direct first-action successors | 41,984 across 113 exchange fixtures passed | [first-state log](selector_preflight/first_states.log) |
| Existing joint vectors | 26 cases, 585 Mean-entry total/mass captures | [vectors](selector_preflight/oracle_vectors.json) |
| Pro arithmetic checks | 4,200,496 HP; 100,000 transition; 520,000 base comparisons passed | [log](selector_preflight/arithmetic.log) |
| Broad table-enabled profile | 132,302,024 cycles; no errors | [profile](selector_preflight/broad_profile.json) |
| Catalog/layout extraction | Simple counts reproduced | [catalog and fixture inventory](selector_preflight/catalog_and_fixtures.json) |
| Fresh linked scratch/bank map | 472-byte WRAM window; mail begins at $a600 | [memory evidence](selector_preflight/memory.json) |
| Static public-information and far-call audits | Passed | [no-cheat](selector_preflight/no_cheat.log), [far-call](selector_preflight/farcall.log) |

The 26-case captured totals were read by a host hook before Mean normalization;
the existing suite independently checks final scores against exhaustive exchange
aggregation, but does not itself expose/assert every complete numerator. Add that
comparison seam when implementing the new fixture adapter. No captured total is
a substitute for direct-pair differential testing.

The first-state script still names the root reference ROM. Its run used the
same hash as the frozen oracle; no build ran concurrently. The older local HP
wrapper script has a stale 252-byte snapshot constant and was not reused as proof
of the new layout. The new layout deliberately prohibits its legacy HP tables.
An additional chart audit passed 189,056 comparisons against the default production
ROM, which was not rebuilt in this pass. It is supplementary evidence only;
the manifest distinguishes that ROM from the frozen reference.

The broad profile is about 31.54 seconds on DMG and includes return-trap padding.
Inclusive routine totals overlap; they cannot be summed into a native budget.
Current reference timing is a baseline, not evidence that the redesign meets its
8.10M-cycle allocation. Reference fixtures execute with interrupts masked.

## Domain and catalog evidence

The initial native acceptance domain is well-formed public snapshots with legal
candidate modes and move IDs, ordinary stage values 1..13, levels 1..100, valid
party indices/counts, and 0<=HP<=maxHP<=999 with nonzero maxima. Ordinary active
decisions begin with a living actor; replacement evaluates living bench entries.
The model does not revive an initially fainted actor. Intermediate zero followed
by same-action drain is part of the native domain.

This is a conservative declared prototype domain, not yet a certification that
every gameplay producer fits it. MAX_LEVEL 100/MAX_STAT_VALUE 999 and CalcMonStatC's
cap support it; the later integration pass must check all import/transformation
and stat/HP writers. Preserve reference behavior for wider/malformed snapshots
through explicit exact fallback, with timing outside the native claim. Do not
quietly classify a difficult reachable state as malformed to meet timing.

For <=999 maxHP, both actor rank-block reservations fit; small M<W uses direct
bytes. General 16-bit valuation uses threshold mode where needed. Large-HP regime
tests must preserve the reference's finite-width doubling/tripling behavior,
which is distinct from proving the HP fraction formula on unbounded integers.

Local source extraction reproduces 254 moves, 157 damaging, 134 potentially
supported damaging, 129 formula moves, 11 multihit, 7 recovery and 5 defensive-boost
moves, 242 base-priority replies, and 85 zero-power replies with no modeled state
transition. Runtime gates/items can still change support. Category power groups
are 21 physical, 19 special, 2 Selfdestruct; all formula powers are multiples of 5.
Outrage's runtime category change uses power 100 already present in both groups.

Simple catalog counts are sufficient to choose the prototype design. They must
become generated assertions when descriptors are implemented. Pro's 1,228 finishing
configuration and 3,010 multihit-step envelopes are not locally certified; neither
is a performance acceptance bound until dependency and compatible-maxima checks
reproduce it. Full score-vector output precludes skipping remaining losing actions.

## Validation matrix for the first coding batch

Use the current fixture infrastructure. The inventory JSON lists existing
exchange/joint fixture IDs and pinned behavior. Add narrow seams rather than a
new general-purpose execution logging system.

| Seam | Required observations | Existing anchor / extension |
| --- | --- | --- |
| Record | Accuracy, priority, denial/check flags, amount/support/range, HP successors and moment | Actor/accuracy checks plus new compact-record adapter |
| Primitive | HP after each ordered operation and after completed action | exchange_life_orb_zero_then_drain; exchange_helmet_zero_then_drain; recovery and recoil fixtures |
| Pair | Complete numerator, order mass, reached flags, fallback replacement | Existing direct exchange aggregation; add totals before division |
| Selector | Twelve full records, mask, winner, repeatability and caller state |26 joint cases and captured preflight vectors |
| Banking/lifetime | Actual far-call wrapper return, closed exit, scratch boundaries, no callbacks or forbidden SRAM helpers | New entry's required implementation assertions/canaries |

Pro final-review additions to the first batch:

- Compare actual macro/shim calls with direct calls for ordinary/replacement
  enumeration and FromContext fallback with nonzero reply/branch. Verify DE/SP,
  BC/carry as declared, and returned ROM bank. Direct harness invocation alone
  does not establish the bridge ABI. Test early rejection after SRAM is opened.
- Poison dead AV prefix fields between fallback and the next producer. Include
  copied-speed uncertainty with equal numeric speeds and different active moves;
  compare to a clean reconstruction. Canary checks do not detect stale in-bounds reads.
- Test accumulator factors independently with maximum masses, both signs,
  256*256, M crossing 255/256, (M<<8)*mu, and 512*B before selector-level tests.
- Verify uncapped recovery quota construction at full HP, then healing after
  damage, including a nontrivial time/weather denominator. Toggle Substitute
  on supported single-hit Life Orb/drain without inventing a new drain gate.
- Force fallback on an early-KO/interrupted pair and verify tentative native
  flags cannot leak into the committed fallback flags.
- Reverse defenders with differing max HP and win-condition weights; shared
  sums must be consumed before actor views/common storage are reused.

Before grouping, test deterministic recovery at original hit masses 0/intermediate/
256 with Zg=sum(w*z), and preserve continuation mass units 0..256 separately from
24-bit grouped masses. Before native amount replacement, add the post-Reflect
defense 1024 low-byte case: raw stat caps do not cap post-modifier operands.
The later restart adapter must collect complete totals before the old selector
reuses them; it cannot reconstruct T from the final score vector.

Required adversaries, with explicit construction rules:

- Broad 254 replies + five bench entries; four active base-priority moves tied
  against the public estimated player speed. Use both normal and reduced accuracy
  stages, not just the original slower Snorlax fixture.
- Four drain moves, Life Orb, low starting HP, both actors uncertain, genuine
  speed ties; also a mixed damage/recovery/recoil set. Preserve duplicate-slot
  identity and all 16 traversal variants.
- Original accuracy bytes 0/254/255; decoded masses 0/256; zero-probability paths
  contribute no reached flags. Reuse joint_accuracy_impossible_hits and early-KO.
- Equal integer scores with unequal numerators; original-index tie rule under
  reversed traversal; joint_speed_tie_round_once distinguishes early rounding.
- Full-HP Rest versus Rest after damage; zero standalone delta must not suppress
  a later useful transition. Both time/LinkMode/weather recovery branches.
- Life Orb or helmet reaches zero then drain restores HP; no premature action
  termination. Dual-Steel recoil rounds to zero; mono-Steel cancels it.
- Exact KO, raw overkill variation, strict half/third boundaries with odd maxima,
  joint stat truncation 255/256, and low-byte extraction boundaries.
- Selfdestruct miss/interruption, unsupported incoming after denial/special
  dispatch, owned unsupported multihit/items, multihit Ice crossing and differing
  raw endpoint stopping points. Pair fallback initially covers unimplemented ones.
- Defensive boosts, execution-time HP regime changes, switch/Pursuit, entry KO,
  replacement's absent reply/mass 2, forced sentinel-to-wait and recharge wait.
- Quick Claw/copied-speed uncertainty versus genuine two-order ties. Hidden player
  item/move/PP/input invariance; fresh decisions and changed scratch fill.
- Grouped versus ungrouped outputs, split equivalent weighted groups, and changes
  to irrelevant flags/HP regimes. Grouping is optional until the base path works.

The two extra broad equal-speed snapshots and their baseline vectors are saved in
[adversarial_vectors.json](selector_preflight/adversarial_vectors.json). They use
the same existing runner without edits to fixture source. Their timings are for
the no-table reference entry, unlike the table-enabled broad profile above.
Both passed all 16 traversal variants and had 968 tied action/reply pairs.
Measured maximum reference calls were 458,703,168 cycles for the mixed set and
458,000,936 for four drain moves. These are adversarial baseline measurements,
not predictions of native executor cost.

## Entry prerequisites versus later gates

Before writing prototype code: frozen/tested oracle; chosen ABI/layout/algebra;
restricted scratch ownership; bounded first slice and exact fallback design;
fixture coverage/specification; independent review of the assembled package.
These are the preparation deliverables of this pass.

During the first coding batch: assembler constants/assertions for proposed
offsets, producer/fallback canaries, result adapter and exact-numerator tests,
real compact HP lookup, host phase counters, and new-entry differential tests.
These cannot be reported as passed before code exists.

Before native timing acceptance: full in-domain native families; generated
descriptor/variant/count assertions; compatible adversarial workload bound;
measured phase costs; no unbudgeted in-domain reference fallback.

Before production promotion: actual call site/public wrapper, animation ownership,
interrupt/VBlank/DMA/callback transitive audit, bank restoration tests, reachable
domain certification, measured integration overhead, production build variants
and full-turn tests. Masking interrupts in the harness closes none of these.

## Exact first implementation sequence

1. Add the private reference-only ABI, named offsets, indexed results, and layout
   assertions. Keep all gameplay calls and old entry points intact.
2. Add minimal producer bridges with explicit A/HL marshaling, FromContext pair
   fallback, complete next-helper read-set/epoch restoration and output copying;
   prevent legacy HP-table calls/flags under the new allocation.
3. Implement direct/rank HP lookup and exact wide accumulation/normalization.
4. Add ordinary scalar corrections and the compact recovery/Life Orb/drain slice;
   route remaining pairs through exact 89-byte direct fallback replacement.
5. Extend existing tests at the record/pair/selector seams; compare all exported
   fields and run the lifetime checks before measuring speed.
6. Measure disjoint native/non-producer work with the actual records and HP lookup.
   Revise expensive families if targets fail; then implement grouped-base and
   finishing arithmetic as separately verified backends.

No micro-optimization campaign, broad cleanup, new test framework, or speculative
production wiring precedes this sequence. Remaining uncertainty is explicitly
assigned to the stage that can resolve it; no two-second result is claimed here.
