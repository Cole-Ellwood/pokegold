# Exact Boss AI selector: roadmap to two seconds

Updated 2026-09-06 after Pro's second review and repository preflight.
Status: implementation plan; no sub-two-second result has been demonstrated.

Start with [preflight readiness](selector_readiness.md), then use the
[implementation contract](selector_implementation_contract.md). The preserved
[second Pro review](selector_preflight/pro_second_review.md) is design evidence;
the local contract resolves its ABI and integration assumptions.
Pro's [final review](selector_preflight/pro_final_review.md) confirms the
architecture for the restricted prototype. Its two pre-bridge clarifications
(cross-bank argument/result marshaling and complete next-helper state restoration)
are incorporated in the contract; targeted hazards are assigned to first-batch
tests or later grouping/arithmetic/restart gates. No further broad preparation
pass is required before beginning the restricted slice.

## Objective and completion criteria

Implement an exact replacement for the experimental joint selector that finishes
within **8,388,608 DMG T-cycles (two seconds at 4,194,304 Hz)** over its declared
supported input domain. Include entry/exit, preparation, table construction,
selection, bank handling, and measured integration overhead. Reserve 750,000
cycles for integration during development, giving the isolated selector a
working ceiling of 7,638,608 cycles; replace that allowance with actual evidence
before completion. Do not describe a benchmark maximum as a proven domain bound.

Preserve the exhaustive reference's integer numerators, denominator/mass, score
vector, lowest-index integer-score tie break, and uncertainty bytes. Preserve
public-information restrictions and authored candidate/reply semantics. No new
move model, deeper search, learning, or policy retuning belongs in this work.

The broad benchmark is mandatory: four active moves, five switches, 254 replies,
2,286 pairs. It is one workload, not the entire acceptance domain. The domain
must also cover supported maximum candidate counts and adversarial branching.
Current legal candidate modes allow at most nine simultaneous candidates: four
ordinary moves plus five bench entries. Forced/wait modes are alternatives;
twelve original-index result slots remain necessary.
Malformed/out-of-domain snapshots may use an exact reference fallback, but their
runtime must be reported separately. A fallback on an in-domain slow case still
counts against the target.

## Architecture decision

Use **standalone action values plus interaction corrections**, with compact
transition records streamed in defender -> reply -> active-action order.

- Build public facts once at their actual dependency scope. Four active moves
  share the active defender's incoming reply sweep.
- Evaluate switches as entry damage followed by a unary reply transition at
  post-entry HP. Entry KO skips the reply.
- For active moves whose inactive event is identity on every relevant
  continuation, accumulate standalone moments and one active-active correction
  per order. This includes supported recoil/drain/item effects. Recovery and
  recognized boosts use scoring mass 256; retain original masses for flags.
- Use ordinary algebraic zero/KO/regime corrections where valid and a compact
  deterministic sequential executor for complex active-active corrections.
  Selfdestruct requires explicit nonidentity-miss handling. A zero standalone
  value is never sufficient to certify an identity transition.
- Coalesce equivalent continuations and sum latent hit/miss probabilities when
  they have the same transition. Preserve positive-mass uncertainty reachability.
- Keep a small bounded native transition executor for complex families. Do not
  rebuild/copy the full 51-byte damage context in the final hot pair loop.
- Compile descriptors from authoritative move/effect tables. Stream grouped
  bases in runtime category / Selfdestruct / power order. Prefer a five-power-step
  recurrence when the generated catalog proves eligibility; retain direct
  calculation for other inputs. Defer full 512-byte power rows.
- Use direct HP bytes for small domains and compact eight-HP rank blocks when
  eligible, with exact threshold lookup for wider domains. Test the real lookup
  in the structural prototype, rather than subtracting a hypothetical future cost.

Claude's measured routine costs and proposed compact combination experiment are
useful evidence. Pro's factoring adds the ability to omit zero-correction work.
Neither proposal's paper budget establishes timing. Preserve the original
integer rounding order, including raw-damage after-effects and HP valuation.
This roadmap supersedes their implementation sequence, provisional memory
allocations, and timing forecasts as the working plan. Retain
`cycle_budget_redesign.md` as historical analysis and profiling evidence.

## Current evidence and retained work

The saved profiles in this folder establish approximately 157.4M cycles for the
older no-table broad run and 150.0M for its SRAM-table version. The fresh preflight
reference table-enabled run measures 132,302,024 cycles, including return-trap
padding, on ROM `b6ccc77d19649750a722a0029578d413063e28273ad68233e2cb2f7d4fefe2d6`.
These are different revisions, not interchangeable baselines. The manifest and
test limits are linked from the readiness record.

Keep the exhaustive evaluator, fixture suites, arithmetic/combat comparisons,
and profiling tools as the oracle and diagnostic infrastructure. Existing HP
tables and first-action caching remain useful reference optimizations. Current
accuracy caching, actor normalization, and bulk move-attribute loading are retained
in the frozen offline oracle following regression checks and focused review.
The new entry must disable legacy HP-table access because its SRAM layout differs.
Do not continue a separate micro-optimization campaign or port caches merely
because they exist; the new architecture must justify each retained hot-path cost.

Keep gameplay selection unchanged during prototype development. Preserve the
historical reports and the broader strategic roadmap: this effort addresses
practical exact joint valuation, not completion of deeper search or learning.

## Milestone 0 — Freeze the oracle and define the acceptance domain

1. Inventory outstanding source edits and finish the narrow validation/review
   of the latest helper changes, or select an earlier verified snapshot as the
   oracle. Preserve unrelated work. Snapshot the reference ROM, symbols, source
   identity, build flags, fixture definitions, and profiler together.
2. Use immutable ROM/symbol pairs for each run. Concurrent builds must not
   replace a ROM that a test reopens between cases.
3. Record baseline full outputs and exclusive phase timings. Inclusive routine
   totals overlap and cannot be added into a cycle budget.
4. Write down legal HP/stat/candidate limits from actual producers and all
   supported modeled effect families. Separate malformed fixture inputs from
   reachable gameplay states without quietly excluding difficult legal states.
5. Add adversarial snapshots to the existing corpus: four equal-priority,
   equal-speed active moves; both sides uncertain; maximum candidates/replies;
   Fire/Ice thresholds; defensive changes; and complex after-effects.

**Exit:** reproducible oracle and domain, exact expected outputs, current memory
limits, and a workload matrix. No performance claim depends on stale binaries.

## Milestone 1 — Specify records, arithmetic, and scratch ownership

Write a compact field/read-set specification alongside the implementation. For
each record or opcode, identify its inputs, initial facts, execution-time facts,
HP writes, uncertainty gates, and invalidation conditions. Audit transitive
helpers, including recovery's TimeOfDay and LinkMode dependencies.

Use the exact integer potential for legal non-reviving states:

    Phi(W, M, h) = 0 when h == 0; otherwise 2*W + floor(W*h/M)
    V = Phi_own - Phi_player
    U = 1024 + V(final) - V(initial)

Ordinary owned weight is 128 and win-condition weight is 192. Compute the 192
fraction directly. Establish the domain before using this identity; zero max HP,
above-max HP, or revival behavior requires explicit treatment.

For normalized identity-inactive transitions, implement the exact standalone
baseline and active-active correction identity, using the compact executor where
ordinary scalar formulas do not apply. Add both tie-order corrections before
probability multiplication. Use signed corrections with
explicit sign extension into the 40-bit total. Compare final integer scores for
selection, never raw numerators. Keep uncertainty as a separate reachability
calculation; no exhaustive winner-only replay may be appended to recover flags.
Prove signed intermediate widths and preserve the reference's fractional-byte
removal before final division. Standalone moments use signed 24 bits; the shared
incoming weighted moment uses signed 32 bits. Group masses require 24 bits;
grouped correction products and final accumulation require 40 bits.

Proposed scratch allocation, to be proven by actual assembly/link assertions:

| SRAM bank 0 range | Purpose | Bytes |
| --- | --- | ---: |
| $a000–$a17f | Owned HP representation | 384 |
| $a180–$a27f | Player HP representation | 256 |
| $a280–$a2f7 | Twelve full result records | 120 |
| $a2f8–$a3f7 | Four 64-byte active plans | 256 |
| $a3f8–$a447 | Two actor views | 80 |
| $a448–$a477 | Two continuations | 48 |
| $a478–$a4f7 | Producer bridge/staging | 128 |
| $a4f8–$a5ff | Arithmetic/group/variant workspace | 264 |
| Total | | 1,536 |

WRAM offsets 0–323 retain producer scratch; 324–331 candidate state; 332–398
reply state; 399–446 current reply; 447–471 control. Export twelve results and
summary into the first 128 bytes only after the final producer/fallback call.
SRAM reserves all 1,536 bytes, with 64 bytes uncommitted inside working storage.

Audit bank selection, interrupts, callbacks, and all called helpers for scratch
collisions. Closing/reopening SRAM does not protect data from a helper that uses
the same physical memory. Define fallback restart rules and closed-SRAM exit
behavior before implementation. Hot code and tables need verified ROM placement.

The private entry's result record is authoritative. Ordinary FarCall restores
the bank by clobbering A; a later public ROM0 wrapper must reload the selected
index from the exported record. Require closed SRAM entry, bank 0 while live,
closed exit, exclusive animation scratch and masked interrupts in the harness.
Do not promise restoration of an untracked prior SRAM bank.

**Exit:** reviewed dependency/record contract, width proofs, bounded storage,
and a safe wrapper/fallback lifetime design. Memory fit remains provisional
until built and checked against fresh symbols/maps.

## Milestone 2 — Build the structural prototype

Add a separate experimental entry point. Use existing verified amount producers
initially; replace the traversal, repeated exchange interpretation, and weighting.

1. Stream one incoming record per defender/reply and share it across active
   actions. Build owned standalone plans and switch entry states once.
2. Implement identity, ordinary/fixed/level damage, conservative incoming KO,
   recovery, Life Orb followed by drain, and switch/replacement/wait orchestration.
   Include exact weighting, compact HP lookup, and reachable flags from the start.
3. Use the direct unprepared 89-byte exchange prefix through the far-call-safe
   FromContext entry for whole-pair fallback,
   replacing that pair's already assigned baseline exactly. Never call the old
   full joint selector inside live new control storage. Restore bridge inputs
   after fallback; charge preparation and execution separately from native work.
4. Compare full per-action totals/masses, scores, index, and uncertainty against
   the oracle, including all 16 existing traversal variants.

Record disjoint counts and cycles for: preparation; incoming records; shared
standalone values; zero-correction pairs; KO corrections; HP-regime corrections;
additional tie orders; native complex corrections; fallback; and final selection.
Record group counts and classification costs too. Each cycle belongs to one phase.

**Exit:** exact outputs and measured structural costs. A 45–50M-cycle total with
old producers is a hypothesis, not a required outcome. Use the phase allocations
in the implementation contract: roughly 1,100 cycles per scalar order unit and
paired-endpoint finishing configuration at Pro's proposed count envelopes, with
probability and multihit work separate. These envelopes still require certification.
Non-producer work above 7,638,608 cycles fails the development allowance even with
free preparation; above 8,388,608 cannot be rescued by faster damage preparation.

## Milestone 3 — Complete native semantics and reduce equivalent work

Add native families in bounded batches, each differentially checked before the
next. Prioritize measured fallback frequency and cost, while covering the full
declared domain before timing acceptance.

| Family | Required behavior |
| --- | --- |
| Recovery and defensive boosts | Preserve execution before hit/miss checks, actual recovery inputs, projected-stat truncation and screens/items applied once |
| Selfdestruct | Use pre-faint attack facts; self-faint also on miss; finish the same action before deciding whether another actor can act |
| Recoil, drain, Shell Bell, Life Orb, helmet | Preserve raw-damage operands, rounding, caps, and operation order; Life Orb reaching zero must not prematurely skip same-action drain |
| Fire/Ice regimes | Recompute only predicates actually read by that move/passive; select facts at execution HP |
| Multihit | Bounded per-hit progression, threshold crossing, raw accumulation, and KO stopping |
| Super Fang / False Swipe | Native HP-dependent amount operations |
| Unsupported damage | Native reference upper-bound transition only after denial, reachability, miss, and earlier special dispatch |
| Switch/Pursuit and switch hazards | Preserve modeled transition uncertainty and post-entry state, including entry KO |

Group replies by deterministic continuations and reachable flag behavior, with
weighted hit/miss masses. Do not group merely because a move has zero power:
healing and defensive boosts can change the next action. Equal terminal utility
permits terminal merging; equal utility before a continuation does not.

**Exit:** complete native handling of supported domain, explicit exceptional
fallback inventory, and exact differential results. No worst-case timing claim
is allowed while common in-domain families still use unbudgeted fallback.

## Milestone 4 — Replace amount and valuation arithmetic

1. Generate move descriptors/priority/support data from authoritative tables and
   audit agreement. Resolve move-specific accuracy gates before reusing stage
   maps; bench BrightPowder differences remain part of the calculation. Prove
   the number of accuracy classes fits any chosen bounded map, with an explicit
   exact overflow path or larger representation if it does not.
2. Stream grouped bases, preferably with the exact five-power-step recurrence.
   Preserve joint truncation of attack/defense, byte extraction, Selfdestruct's
   defense adjustment, zero guards, and 999 cap. Power zero dispatch stays outside
   the base calculation. Keep up to three small base states for relevant defensive
   variants; avoid repeated setup per pair. The current catalog has 21 physical,
   19 special, and 2 Selfdestruct power groups, all on the five-power lattice.
   Generate eligibility checks; keep outgoing item arithmetic separately proven.
3. Replace finishing arithmetic in its existing order: weather, STAB, chart rows,
   passives, variation, and postroll rules. Preserve minimum-one, zero, overflow,
   and saturation behavior. Test full arithmetic domains and paired ROM behavior.
4. Use the prototype's exact direct/rank-block/threshold HP backend.
   Reuse standalone valuations and bypass searches for known unchanged/full/zero
   states. Rank blocks require maxHP >= weight and must fit their reserved span;
   larger domains retain exact threshold valuation and explicit timing accounting.
5. Replace general probability multiplication and repeated-subtraction Mean with
   exact bounded arithmetic where profiling still justifies it. Keep intermediate
   floors and integer-score tie behavior unchanged.

**Exit:** assembled native backend, same outputs, verified bank/layout assertions,
and fresh end-to-end timings. Python identities support the assembly tests; they
do not substitute for them.

## Milestone 5 — Close the performance and correctness gates

Pro's revised 7.35M native + 0.75M integration allocation totals 8.10M, leaving
288,608 cycles. It supersedes the earlier forecasts as a development target;
none of these forecasts establishes feasibility. Use disjoint measured phases
and certified counts to close the final budget.

The broad benchmark has only 2,835 branches. An adversarial tie case can require
2,032 active correction units instead of Pro's earlier 1,016 allocation; doubling that
work alone can consume its margin. Also account for extra base variants, both relevant HP
predicates, after-effects, maximum candidates, grouping failures, and fallback
preparation. Do not extrapolate those costs from a slow Snorlax case alone.

Required validation combines existing fixtures with targeted adversaries:

- Full outputs and reversed traversal; exact integer-score ties; accuracy bytes
  0/254/255 and decoded probability masses including 0/256; zero-probability
  uncertainty suppression; speed ties and unknown order.
- Exact KO/overkill, half/third-HP boundaries, raw endpoint variation, defense
  truncation, switches/hazards, and all native complex families above.
- Public hidden-state invariance and deterministic repeatability; caller state,
  stack, declared SRAM bank/enable exit contract, scratch boundaries, and callback lifetime.
- Broad and adversarial maximum workloads on immutable builds. Instrumentation
  overhead must be separated or conservatively counted; confirm uninstrumented
  timing with the same fixtures.

**Exit:** no output mismatches; isolated and integrated timing meet their stated
limits; fresh map evidence fits memory/banks; independent review approves changes
and retained behavior. If only the tested corpus meets timing, report that limit
and continue establishing the domain bound instead of declaring a universal win.

## Milestone 6 — Integrate and document the result

Promote the selector only after correctness/performance gates. Specify how the
exact ranking feeds the existing authored tier/variety policy; preserve that
policy unless separately authorized. Run affected production build variants,
public-information audits, normal/trace regressions, and complete-turn fixtures.
Measure real entry-to-return latency under intended interrupt/display conditions.

Publish a compact manifest of source/build identities, domain, output comparisons,
per-workload timing, memory use, fallback counts, integration behavior, and review
status. Update the strategic roadmap to mark only the capabilities actually
delivered. Deeper successors and learning remain later work.

## Immediate next implementation batch

Use the preflight record to close the remaining implementation-entry requirements,
then implement the contract and milestone 2 hybrid prototype in dependency order.
Do not begin another broad micro-optimization pass,
replace all damage arithmetic at once, add unsound pruning, or tune around only
the broad benchmark. Revisit the design when measured gates fail; preserve exact
semantics and expose the cost responsible for the failure.

This roadmap is a planning deliverable. It does not itself resume or complete
the paused implementation goal, validate pending source edits, or authorize a
claim that the two-second target has already been met.
