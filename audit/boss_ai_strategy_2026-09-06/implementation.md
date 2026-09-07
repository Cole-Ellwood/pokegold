# Battle AI strategic consistency implementation — 2026-09-06

This is the implementation follow-up authorized after the findings-only audit in
`report.md`. The original report, probes, source manifest and `review.md` preserve
the earlier audit basis; they do not describe the post-change ROM. This record
covers the actual changes against implementation baseline
`34d8f9b449eb6201676c66e515d689347ec2c844`.

**Result:** a bounded strategic consistency pass, not a claim of perfect play.
The boss now compares feasible alternatives more consistently, considers every
selectable move and living bench slot, and avoids several demonstrably wrong
premises. It still uses heuristic tactical estimates and separate move/switch/
faint-replacement policy scales. No win-rate improvement is claimed.

## Implemented decisions and evidence

| Unit | Change and strategic purpose | Verification |
|---|---|---|
| Owned move availability | One PP/Disable/Choice/Assault Vest predicate is shared by KO, dominance and strong-matchup scans. An attack that cannot be chosen cannot suppress a trade or utility action. | PP, PP-Up-only, Disable, current/stale Choice locks, Vest attack/status twins; KO and dominance/strong-alternative ROM twins. |
| Hard blocks | Public status failure returns immediately. Both encouragement paths respect score 80. Signed lookahead floors preference scores at 1. | Toxic against Steel remains blocked under plan/model/selection; existing immunity cases; independent signed-delta reference. |
| Move evaluation | Preserve the upside/downside accumulator across pressure and HP helpers. Remove mixed raw/evaluated-score pruning and evaluate all selectable slots, including unattractive late hedge candidates. | Independent per-move ROM evaluation matches the production driver on uniform, highly unequal and blocked arrays. The legacy futility-audit CLI now runs this behavioral contract. |
| Damage ranking | Quarter resistance is distinct from half resistance in damage dominance. | Actual ROM scaling at immunity, quarter, half, neutral and double effectiveness; availability/dominance twins. |
| Voluntary switches | Preserve likely/speculative tier weights across mask tests; cap accumulation before byte overflow. Filter HP and strict threat improvement before ranking every living bench member. Preserve plan target scratch. | Tier 1/2/3 likely/possible/absent risk matrix, overflow tests, fifth bench winner, bench permutation, rejected dying candidate with viable runner-up, no-improvement refusal. |
| Perish escape | At count 1, select a living escape and bypass ordinary confidence/KO/sack gates. Count 2 retains preparation pressure and another action. The outer entry still enforces traps/locks. | Count 0/1/2/3 twins, neutral and dying escape, no living bench, Mean Look and Wrap entry gates. |
| Public Speed | Compare own effective Speed and known Scarf with a public species/level/stage/status/type estimate using DV8. Match engine table, passive constants, integer rounding and stage cap. Place the implementation in a floating ROM section with a cursor-preserving caller wrapper. | Level, stage, paralysis, Scarf, 16-bit, Electric/Fighting fractions, level-1 quotient and 999 stage cap cases; normal/trace ROM execution and banking audits. |
| Setup | Plan and projection rewards share headroom, available-KO and current-board safety checks. Remove the rule that a useful setup opportunity expires solely after two turns on the field. | Early/late safe opportunity twins and low-HP/public-threat refusals; source/call-graph review of shared reward gates. |
| Public memory and coaching | Four stable reveals narrow masks and fallback STAB threats; tainted reveals preserve uncertainty. Choice regret ignores publicly fainted species. Coach resistance uses the active defender instead of unrelated loaded base data. | Full/unknown/tainted reveal twins for both mask and predicate; living/dead Ghost lock-risk twins; coach tests with deliberately conflicting visible and stale base types. |
| Scouting | Cache the final decision, including its single probability roll, for the tick. Preserve matchup side effects on positive cache hits. | Actual ROM Random hook counts one call across four consumers; cached yes/no and next-tick reset tests. |
| Destiny Bond | Recognize revealed neutral nonimmune retaliation in the low-HP, faster, no-available-KO trade window. Exclude Counter/Mirror Coat and Hidden Power's placeholder type from this evidence. | Original full-HP/dying selection twins still pass; attack/status/counter/immune helper twins. Reviewer independently checked the original trade through the damage pipeline. |
| Baseline fallback | Correct HP-times-four arithmetic and include exact quarter HP in the ordinary-trainer fallback helper. | 24/25/26 of 100 and low-byte bit-6 boundary cases. |
| Test and maintenance surface | Seed neutral stages and the engine's doubled-DV stat formula; support register/pointer inputs, exact memory outcomes, RNG observation and independent lookahead comparison in the existing harness. Refresh policy/API notes, semantic static invariants and generated indices. | Full normal and trace suites, policy/ABI/audit floor, generated-index check. No parallel test framework or new battle state layout. |

The coach issue left unresolved in the historical audit is now resolved by the
active-type correction and its two conflicting-context ROM tests.

## Retention decisions

These approve retaining the named architecture or policy with its limitations;
they do not certify every untouched move effect or every reachable battle state.

- **R1 — Public-information boundary and isolated Haki:** preserve the existing
  once-per-battle, tier/ace/turn gates and the explicit input-reading exception.
  Haki remains a designed exception; ordinary reasoning gains no hidden reads.
- **R2 — Compact public bitsets, generated tables and per-tick caches:** suitable
  for the platform. Corrected weights, reveal semantics and scout reuse retain
  this representation. Species-keyed memory still cannot reliably distinguish
  duplicate individuals; outcome calibration still describes public type
  severity rather than actual observed HP loss.
- **R3 — Bounded computation:** exhaustively checking four moves and five bench
  candidates is small and removes invalid exclusions. Retain capped heuristic
  projection, without representing it as a successor-state search. Accept the
  measured additional late-tier work below; do not restore the invalid cutoff.
- **R4 — Authored plans, tiers, tables and opener variety:** retain difficulty and
  personality choices, subject to the corrected feasibility/setup gates. No
  claim that existing weights or all templates maximize win probability.
- **R5 — Banking, thunks and isolated trace state:** retain these boundaries and
  use a small floating Speed section to fit both builds. Preserve the retired
  pruning byte and cache symbol names to avoid incidental WRAM layout changes.
- **R6 — No trainer bag items and separate ordinary-trainer policy:** intentional
  gameplay choices. Only the shared quarter-HP fallback correction touches the
  ordinary switch policy; do not add item search or late-boss reasoning to it.
- **R7 — Coarse damage and separate action-family valuation for this pass:** the
  current corrections have local behavioral evidence. A common damage/survival
  evaluator, joint move/switch/faint scoring, true successor search and contextual
  learning require a separate measured design. Adding them now without a trusted
  continuation corpus would expand assumptions and storage, not establish a
  strategic improvement. This limitation remains explicit, not endorsed as
  optimal behavior.
- **R8 — Conservative Perish and uncertain retaliation/speed:** no terminal-win
  exception based on hidden party count or a coarse KO bucket. No invented exact
  player DV/item/badge knowledge. Destiny Bond's retaliation test is a danger
  estimate, not a guaranteed KO prediction, and the player can decline to attack.

The audit's coverage inventory in `report.md` continues to define the full
architecture review surface. This implementation changes the listed units and
retains the other units under R1–R8. Exhaustive per-effect gameplay correctness
and global optimality are outside the demonstrated evidence.

## Validation and cost

- Fresh **Gold, Silver, Gold debug and Gold trace builds** succeed with RGBDS
  1.0.1 through the documented WSL build commands.
- **114/114 normal-ROM and 114/114 trace-ROM fixtures** pass. Exact per-case
  outcomes and ROM hashes are in `pokegold_fixtures.json` and
  `pokegold_trace_fixtures.json`.
- All **12 recorded checks** pass in `implementation_checks.json`, including
  the required no-cheat, gating, trace invariants, memory budget and index floor;
  policy contract; cross-bank and farcall ABI audits; the independent lookahead
  contract; and Python preference regression. The preference regression is
  **45/45 strict pairs**, with nine non-strict cases skipped; it is not ROM
  playing-strength evidence.
- Enemy Trainers ends at **0e:7f5c normally** (163 bytes free) and
  **0e:7ff9 in trace** (6 bytes free). The new floating Speed section is 317 bytes.
  Trace headroom is tight and must be rechecked on subsequent edits.
- Boss AI WRAM remains **112/140 normal**, **140/140 trace**. The save-format-3
  offset audit verifies all **1,450 saved fields** unchanged.

The unchanged legacy synthetic benchmark uses three samples per scenario:

| Synthetic workload | Before mean cycles | After mean cycles | Change |
|---|---:|---:|---:|
| mid_lead | 2,574,878 | 2,574,877 | unchanged within measurement granularity |
| late_lead | 3,370,750 | 4,260,256 | +26.4% |
| late_lookahead_heavy | 3,651,649 | 4,213,440 | +15.4% |

Raw results are in `cost_before.json` and `cost_after.json`. These counts include
frame-rounded return-trap waiting. Scenario names/comments and hardcoded IDs are
legacy synthetic workloads, not faithful complete trainer battles. Use them only
as a coarse before/after cost check. This is a strategic correctness tradeoff,
not a performance optimization claim or a hardware latency guarantee.

Natural battle continuations, a matched-seed win-rate comparison, full heuristic
ablations and every possible move/party permutation were not run. Archived live
captures from the historical audit have a different ROM basis and are not used
as proof of this build. No source change outside the reviewed implementation
scope, save migration, commit, push or publication is part of this delivery.

## Final review

The independent Astra reviewer must approve this assembled implementation,
its tests and documentation, and every retention decision R1–R8. The final
state is identified by `implementation_manifest.json`; the approval is recorded
in `implementation_review.md` after it is received. Earlier findings-only
approval in `review.md` does not approve the implementation.
