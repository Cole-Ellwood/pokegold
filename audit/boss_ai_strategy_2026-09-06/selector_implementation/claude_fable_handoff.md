# Claude Fable continuation — 2026-09-07

## Objective and authorization

The user wants the exact joint boss-AI selector finished correctly, with a complete
decision within two seconds on DMG. They authorized implementation after the three
Pro reviews. They then requested a safe pause and now explicitly ask Claude Fable
to take over temporarily, with full access to this same folder/repository. Codex
has stopped editing and has no outstanding build/test job for this task. Continue
implementation rather than repeating the preimplementation design exercise.

This remains a private `BOSS_AI_REFERENCE` prototype until correctness, performance,
and integration gates pass. Do not claim ordinary selection or the timing target is
finished: ordinary decisions currently use the slow complete restart. Replacement
decisions are native. Preserve the existing public-information model and gameplay.

## Verified checkout and ownership

- Worktree: `C:/Users/lolno/Downloads/pokemon gold hack`
- Branch: `master`
- HEAD: `34d8f9b449eb6201676c66e515d689347ec2c844`
- One worktree was listed at handoff. Compare actual HEAD/status before editing;
  do not automatically pull, reset, stash, clean, or switch branches.
- There is substantial intentional uncommitted work. Most new AI/reference/fast
  sources, fixtures, and the audit directory are untracked. They are real work,
  not disposable output. No checkpoint commit was made.
- The latest implementation lane owns `engine/battle/ai/fast_*.asm`, the matching
  `tools/boss_ai_fixtures/fast_*.py`, reference-only includes in `main.asm`, and
  `selector_implementation/` documentation. Earlier task work also introduced
  reference build support and full-numerator fixture capture.
- Other existing changes include public damage/action/joint models, chart fixes,
  production AI/scouting/pruning changes, mechanics/docs/audits, and SRAM aliases.
  Do not attribute the entire diff to the latest implementation or overwrite it.
  Inspect surrounding changes before touching those files.

## Read these before continuing

Paths below are relative to the worktree above.

1. `CLAUDE.md`, `docs/README.md`, `docs/build.md`, and
   `docs/agent_navigation/gen2_vs_modern_mechanics.md` for repository conventions.
2. `audit/boss_ai_strategy_2026-09-06/selector_implementation/status.md` for the
   current implementation inventory, reviewed hashes, validation and remaining work.
3. `audit/boss_ai_strategy_2026-09-06/selector_implementation_contract.md` for the
   exact ABI, memory, algebra, reachability, fallback and acceptance requirements.
4. `audit/boss_ai_strategy_2026-09-06/two_second_roadmap.md` and
   `selector_readiness.md` for the approved roadmap and gate sequence.
5. `selector_preflight/pro_second_review.md` and `pro_final_review.md` in that
   audit directory if design rationale is needed. Older full-power-row designs,
   scratch layouts and timing forecasts are superseded by the current contract.

The contract's historical wording says implementation is not present; use
`selector_implementation/status.md` to distinguish implemented components from
the still-authoritative design requirements. Do not freeze a new oracle simply
because you are starting a new session.

## Frozen oracle and checkpoint evidence

- Frozen oracle prefix: `.local/ai-two-second/preflight-2026-09-06-pro2/oracle`
  (`.gbc`, `.sym`, `.map`). ROM SHA256:
  `b6ccc77d19649750a722a0029578d413063e28273ad68233e2cb2f7d4fefe2d6`.
- Current `pokegold_ai_reference.gbc` SHA256:
  `65e403fb5e8b4e64b8f05d38820f7cf87ba239f9545986afa24a58413989ee75`.
- Current status document SHA256 at handoff:
  `f8148d23b7848184743715eb182752d5808eacd7157eb0733a0af1ff801cbc53`.
- Build and `git diff --check` pass; diff check reports only line-ending warnings.
- All 839 existing fixtures pass on this ROM. Log:
  `.local/ai-two-second/pair-checkpoint-fixtures.log`.
- Focused checks: 6,048 owned action/reference comparisons; 19,200 incoming
  action/reference comparisons, 1,200 complete incoming plans and 13 edge cases;
  2,160 owned and 3,000 incoming standalone records/moments; 1,728 normalized pair
  full/correction comparisons; 1,248 fallback full/correction comparisons. These
  also check relevant rejects, flags-only behavior, DE/SP, poisoned producer data
  and exact write footprints. Earlier foundation checks are listed in status.md.
- The independent Astra-low reviewer approved the final assembled checkpoint and
  every stated retention decision after the 839-fixture pass. There are no open
  required checkpoint findings. This approval does not extend to future changes
  or unimplemented orchestration/timing. Preserve the requested independent review
  process for new work; if that reviewer configuration is unavailable, disclose
  the gap instead of presenting self-review as equivalent approval.

## What is implemented

The `fast_*` sources provide compact HP representations, exact wide arithmetic,
canonical results and finalization, scalar HP/item transitions, producer bridges,
four owned plans, one incoming plan, actors, standalone moments, normalized move
pairs, complete direct move-pair fallback, native replacement, and full restart.

Incoming opcodes are 0 fallback, 1 damage, 2 recovery, 3 switch-Pursuit transition,
4 absent. Owned plans currently represent single-hit damage and recovery. Defense
boosts, Selfdestruct, multihit, False Swipe and Super Fang still fall back. Fixed
and level damage use the existing amount producer when represented.

`BossAI_FastNormalizedPair` returns full unweighted numerator and flags;
`.CorrectionOnly` returns only `z_own*z_reply*K`. `BossAI_FastFallbackPair` returns
full direct-reference N; its `.CorrectionOnly` subtracts the exact standalone
baseline. The latter currently accepts ordinary move kind only. Its order argument
must describe actual public order: the direct evaluator resolves single order
itself; the argument does not force arbitrary order. A genuine tie expands twice.

Both executors have `.FlagsOnly` entries sharing executable gates. They change
only continuation flags and scratch. Pair scoring evaluates one active/active
numeric terminal per order, while flags visit positive original-event paths using
standalone first-event HP. Do not replace this with four expensive numeric branches.

## Critical invariants

- The owned WRAM window is 472 bytes at `$c900`. Producer prefix 0..323 may be
  rebuilt. Candidates 324..331, reply set 332..398, current reply 399..446, and
  control 447..471 must survive producer/fallback calls. See contract field maps.
- SRAM0 reservation is `$a000..$a5ff`, disjoint from party mail at `$a600`.
  Keep the existing complete layout. Never enable legacy `PrepareHPValues` or
  its prepared-table bit: its two 704-byte aliases overlap live native records.
- `$a54b` is the sequential `FSE_MODE` / standalone-delta-low alias. Every normal
  action resets the mode; Delta runs afterward. Pair control occupies
  `$a54c..$a55f`, and pair total occupies `$a578..$a57c`. The 64 spare bytes at
  `$a5c0..$a5ff` remain uncommitted. Update live-range documentation before use.
- Across FarCall, A and HL are not safe input carriers. Marshal selectors through
  memory or documented registers. DE may be returned as a damage maximum by a
  range producer: save the context pointer. Do not trust A as the public result
  across FarCall; use the exported result block for selected index.
- Direct fallback rebuilds the old prefix and invalidates prepared assumptions.
  Restore the next helper's full read set/epoch, not just move/slot/kind/reply.
  Never call the old full JC selector inside a live native allocation. A complete
  restart is allowed only after closing/discarding native state.
- Preserve exact integer totals and signed moments; decode accuracy255 as256.
  Recovery is deterministic for scoring (`z=256`) even with original accuracy0.
  Original event probabilities still govern flags. Initial full-HP recovery or
  zero standalone delta is not a global identity certificate.
- Flags remain local until native or fallback ownership is decided. Rest flags
  require positive gained HP at the actual continuation. Can-act denial can still
  retain earlier uncertainty. Use exact wrapped 16-bit HP predicates.
- Use raw damage for item/drain/recoil. Helmet triggers after holder KO and before
  drain; same-action zero followed by drain is allowed. Do not add a Substitute
  gate to Life Orb/drain; Helmet has its own explicit Substitute gate. Unsupported
  nonzero-power incoming damage KOs only after its gates, then returns without
  normal after-effects. Unknown player held items are not inferred.
- All twelve indexed records are required, including canonical invalid records.
  Select by final integer score then original index, not numerator or rounded HP.

## Next concrete work — not yet implemented

Start the ordinary selector orchestration, using the reviewed correction APIs:

1. Prepare candidates/reply sets; compile up to four owned plans once and import
   actor/order facts. Initialize each result with `1024*D + (M<<8)*mu_own`.
2. Stream one compiled reply per defender, accumulate signed `B=sum(w*mu_reply)`,
   and consume native correction-only or full fallback-minus-baseline for each
   owned plan. Add `512*B` before changing defender scope.
3. Add switch/wait orchestration with an explicit post-entry baseline and unary
   fallback. Entry KO skips reply execution, not reply mass. Wait's own can-act
   checks occur before Reply even when a later HP gate denies execution.
4. Complete required native family coverage, defense invalidation/variants and
   grouped incoming arithmetic. Then compare full records against the frozen ROM,
   test traversal/hidden-information invariants, profile actual phases, and satisfy
   the complete timing/integration gates. Helper timing is not whole-decision timing.

Implementation leads discussed before pausing, **not reviewed requirements**:

- Candidate adaptation can reuse the existing forced-action predicate, whose
  candidate offset is the same 324, but cannot call the original `.Candidate`
  unchanged: its JC control offsets overlap the compact reply/control lifetime.
- Actor speed words belong at actor14..15, setup flags35 and speed mode36.
  Resolve priorities first; absent reply is own-first. At equal priority, unknown
  speed or Quick Claw follows the reference's conservative order, not a random
  tie. Only the genuine known same-speed model gets the two-order descriptor.
- For unary work, keep original start HP/Phi and post-entry HP/Phi distinct.
  A post-entry reply standalone variant could initialize from actor entry HP and
  subtract entry Phi. Any unary carrier plan needs an explicit opcode/lifetime;
  do not silently repurpose the current move-only fallback contract. Its fallback
  baseline must include entry delta and post-entry reply moment exactly once.
- The unused part of the 24-byte common area could hold the signed shared incoming
  sum. This still needs concrete lifetime review; no new allocation was made.

## Build and checks

Use PowerShell in the worktree. Python and the ROM fixture harness work directly.
Build with WSL and the repository-local Windows RGBDS executables:

```powershell
bash -lc 'make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold_ai_reference.gbc'
python -m tools.boss_ai_fixtures.fast_pair
python -m tools.boss_ai_fixtures.fast_pair_fallback
python -m tools.boss_ai_fixtures.fast_plan_executor
python -m tools.boss_ai_fixtures.fast_reply
python -m tools.boss_ai_fixtures.fast_standalone
python -m tools.boss_ai_fixtures.fast_reply_standalone
python -m tools.boss_ai_fixtures --rom pokegold_ai_reference --suite all
git diff --check
```

Run checks appropriate to new changes, not repeated unchanged sweeps. The existing
`fast_reference.py --prototype` assertions currently expect ordinary backend2 and
replacement-only SRAM writes; update those assertions deliberately when ordinary
native integration changes the contract they test. Keep frozen-record comparison.

Do not rerun `.local/ai-two-second/make_reply*.py`: these were one-time construction
aids and are stale relative to reviewed source edits. The assembly/tests are the
source of truth. No new failure is awaiting repair at this checkpoint.

When returning control to the user/Codex, update the status and this handoff (or
append a clearly dated continuation) with exact changes, tests, hashes, remaining
work and any review gaps. Keep communication concise and progress-oriented.

---

# Continuation 2026-09-07 (Claude Fable): ordinary orchestration landed

## What changed

Ordinary decisions are now evaluated natively by
`BossAI_ComparePublicActionsFastPrototype`; the "restart immediately" path is
gone. `audit/boss_ai_strategy_2026-09-06/selector_implementation/status.md`
has the full description ("Ordinary orchestration (2026-09-07)"), the
validation evidence and the phase profile. Files touched:

| File | Change |
| --- | --- |
| `engine/battle/ai/fast_selector.asm` | Rewritten: ordinary orchestration (active defender, bench switches, wait, reply sweep, shared incoming sum, record accumulation, 40-bit helpers); replacement logic kept, restructured around shared bench-cursor helpers. |
| `engine/battle/ai/fast_pair_fallback.asm` | Appended: common-sum allocation `FSC_*` ($a57d..$a58e) and `BossAI_FastUnaryFallback` (wait/switch unary fallback with exact baseline subtraction). |
| `engine/battle/ai/fast_producers.asm` | Appended: `FSB_QUICK_CLAW` ($a48f), bridges `BossAI_FastPrepareOwnedCandidate`, `BossAI_FastPrepareActiveFacts`, `BossAI_FastPrepareReply`. |
| `engine/battle/ai/fast_reference.asm` | Appended: `BossAI_FastForcedAction` (index-10 forced/wait classification, farcall-safe). |
| `tools/boss_ai_fixtures/fast_reference.py` | `--prototype` accepts native status 0/1 for ordinary kinds, exempts the private SRAM reservation from the footprint check for native ordinary runs, adds a hidden-information rerun, reports which fixtures used fallback. |
| `tools/boss_ai_fixtures/fast_unary_fallback.py` | New unit fixture (88 cases + 4 rejections). |
| `tools/boss_ai_fixtures/fast_ordinary_profile.py` | New: whole-decision and disjoint-phase timing of the 24 ordinary joint fixtures, oracle vs native, writes `fast_ordinary_profile.json`. |
| `tools/audit/check_boss_ai_decision_paths.py` | Release-smoke wrapper now runs `suite="production"` and reports `FixtureError` as FAIL. It had been failing since the runner gained suites: `run_all()` defaulted to the reference suite on the game ROM. Pre-existing, not caused by this work. |
| `audit/.../selector_implementation/status.md`, `cleanup_notes.md`, `fast_ordinary_profile.json`, `fast_replacement_profile.json` | Status rewrite, code-quality notes requested by the user, profiles. |
| `audit/.../selector_implementation_contract.md` | "Implemented allocation" note for the control bytes, common sums, actor-view bytes and bridge byte now in use. |
| `docs/generated/dev_index.md` | Regenerated after rebuilding `pokegold.gbc` (unchanged production behaviour; the rebuild only checked the game ROM was current with source). |

## Evidence (ROM `83070fc20a59f278f82d9f7052510285aba956aab563a53cef4493b383048d01` unless noted)

- `fast_reference.py --prototype`: PASS, 76 vectors (26 fixtures x 2 scans +
  24 hidden-information reruns), 5 invalid entries. 19 native-only, 7 with
  fallback. Log `.local/ai-two-second/ordinary-prototype-run3.log`.
- `fast_reference.py --replacement-boundaries`: PASS, 116 vectors (ROM
  `e8628a6c...`, before the header guard; the guard is on the ordinary path).
- `fast_reference.py`: PASS, 52 vectors.
- `fast_unary_fallback.py`: PASS 88 + 4 rejections. `fast_pair.py` 1,728 and
  `fast_pair_fallback.py` 1,248: PASS.
- `python -m tools.boss_ai_fixtures --rom pokegold_ai_reference --suite all`:
  PASS all 839 (`orchestration-fixtures.log` on `e8628a6c...`,
  `orchestration-fixtures-final.log` on the current ROM).
- `tools/audit/check_boss_ai_decision_paths.py` (production suite on the
  rebuilt `pokegold.gbc`, SHA1 `85a2fe838a28f23b198845e63876a637580e91a9`):
  PASS 473. `check_cross_bank_call.py`, `check_farcall_hl_clobber.py`,
  `check_farcall_a_clobber.py`: PASS.
- Timing: NOT met. Broad benchmark 180,985,824 native cycles vs 132,211,028
  oracle (WithTables) vs 8,388,608 budget. Reply preparation with the existing
  four-regime producers is 104M of it. See status.md "Ordinary timing".

## Review gap

The independent Astra-low reviewer configuration was not available here. The
orchestration code and the audit-wrapper fix are self-reviewed plus
fixture-validated only. Please route `fast_selector.asm`, the appended
routines, `fast_reference.py` and `fast_unary_fallback.py` through that
reviewer before treating them as approved. Everything previously approved is
unchanged (hashes in status.md).

## Next steps (from the profile, in order)

1. Lazy reply regimes via `FSR_VALID` (cheap, 2-4x on the dominant phase).
2. Milestone 4 native amount arithmetic (mandatory for the target).
3. Native fallback families + reply grouping; adversarial fixtures; timing
   gates; production ABI/interrupt ownership.

Design lead, not a reviewed requirement: the selector already computes each
plan's hit-successor HP before the reply sweep, so the needed-regime mask for
a reply is the initial-state regime plus the regime at each live plan's hit
successor, and can be handed to the compiler through a control byte; the
executor should reject an unmarked regime (carry clear) and the selector then
falls back for that pair. Do not fill regimes lazily inside the executor: the
producer prefix is dead by then.

## Git

Two checkpoint commits were made on `master` (not pushed): the first captures
the Codex checkpoint exactly as handed over (all previously uncommitted work,
original versions of the four appended/rewritten sources), the second is this
session's orchestration work. `git show --stat HEAD` lists the second.

---

# Continuation 2026-09-07 (Claude Fable, later): performance work and native families

## What changed since the orchestration commit

Six commits on `master` (not pushed), each validated by the frozen-oracle
comparison (76 vectors exact) before it was made:

| Commit | Change | Broad benchmark |
| --- | --- | ---: |
| `9b822b7f` | Lazy reply regimes (`FS_REPLY_REGIMES`, `FSR_VALID`, `FSC_FAULT` latch and restart), `BossAI_FastScalarPair` | 181.0M -> 122M |
| `a04741df` | `BossAI_FastScalarReplyStandalone`, cached scalar pair gates | 122M -> 106M |
| `0ed1b6c3` | `fast_reply_native.asm`: native reply compiler with in-bank data mirrors and include guards in `data/` | 106M -> 82M |
| `a03213eb` | Effect-class table, short divisions, empty-byte reply scan, identity pairs | 82M -> 75M |
| this checkpoint | Native multihit / Super Fang / False Swipe / Selfdestruct on both sides, `BossAI_FastFallbackPair.Native` | 75M -> 59.1M |

`status.md` sections "Performance work and native families (2026-09-07)",
"Native families validation" and "After the 2026-09-07 performance work" have
the details, fixture counts and the phase split. The target (8,388,608) is not
met; what remains is listed in "Remaining implementation" there.

## Files touched by the native-families checkpoint

| File | Change |
| --- | --- |
| `engine/battle/ai/fast_plans.asm` | Family opcodes 3..6, `FSB_PLAN_OPCODE/PATCH/DELTAS` ($a491..$a493), producer-input patch for the sweep and `.RestorePatch`. |
| `engine/battle/ai/fast_reply_plans.asm` | Family opcodes 5..8, `FSR_MIN_DELTA0..3` (bytes 7, 8, 23, 26), forced full mask for multihit, wide-delta exit to opcode 0 / carry clear. |
| `engine/battle/ai/fast_reply_native.asm` | Same family classification and deltas as the producer path; Selfdestruct halved defense (uncached); Super Fang template amount; `.store_opcode` returns carry clear for opcode 0. |
| `engine/battle/ai/fast_plan_executor.asm`, `fast_reply_executor.asm` | `FSE_OPCODE` ($a53f), family scratch `FSX_*` aliasing the damage-script inputs ($a530..$a53c), `.multi`/`.MultiPath`, `.fang`, `.false_swipe`, `.CapWord`, Selfdestruct self-faint, `.Script` entry for the shared single-hit tail; reply side adds `.MinDeltaFor`. |
| `engine/battle/ai/fast_standalone.asm`, `fast_reply_standalone.asm` | Accept opcodes through the new range. |
| `engine/battle/ai/fast_pair.asm` | Factored pair accepts the families but rejects Selfdestruct on either side; reply mass zero only for Pursuit/absent. |
| `engine/battle/ai/fast_pair_fallback.asm` | `BossAI_FastFallbackPair.Native` mode (executor terminals, order start fixed for single orders, tie flag), `.OwnAction`/`.ReplyAction`. |
| `engine/battle/ai/fast_selector.asm` | `.PlanPair` routes identity replies first, then Selfdestruct on either side to the native whole pair, else scalar/factored. |
| `tools/boss_ai_fixtures/fast_reply.py`, `fast_plans.py`, `fast_plan_executor.py`, `fast_pair.py`, `fast_reply_standalone.py`, `fast_reply_native.py` | Family moves, patched-context expectations, delta bytes, wide-range case, native whole-pair checks, rejection opcodes moved. |
| `audit/.../status.md`, `cleanup_notes.md`, `fast_ordinary_profile.json`, `selector_implementation_contract.md` | Documentation and profile refresh; allocation note extended. |
| `.local/ai-two-second/debug_joint_pairs.py` | Scratch: per-pair native-versus-forced-fallback diff for one joint case. |

## Evidence (ROM `40a209cf3a1e4298897bb97ac213cc842ceb1336c7c48efd80fac600a8e65e58`)

- `fast_reference.py --prototype` PASS 76 vectors, 23 native-only, 3 with
  fallback (defense boosts only); `--replacement-boundaries` PASS 116;
  restart adapter PASS 52.
- `fast_reply_native.py` 5,588; `fast_reply.py` 26,880 / 1,680 plans;
  `fast_plans.py` 240; `fast_plan_executor.py` 8,208; `fast_standalone.py`
  2,160; `fast_reply_standalone.py` 3,000; `fast_pair.py` 3,744 + 15
  rejections; `fast_pair_fallback.py` 1,248; `fast_unary_fallback.py` 88.
- `check_boss_ai_decision_paths.py` on the rebuilt game ROM (SHA1 unchanged
  `85a2fe838a28f23b198845e63876a637580e91a9`): PASS 473.
- 839-fixture reference suite: PASS (`.local/ai-two-second/families-fixtures.log`).
  `tools/audit/check_release_smoke.py`: ALL RELEASE SMOKE CHECKS PASSED on the
  final build.
- Timing: broad benchmark 59,106,740 cycles versus 8,388,608 budget. Not met.

## Review gap

Unchanged from the previous continuation: no independent Astra-low review was
available. Everything since `6dd6c0e6` is self-reviewed plus fixture-validated.
The pair fixture caught two real defects in the native whole pair before the
whole-selector run (missing tie flag; wrong first order), which is the kind of
thing the reviewer should look for in the rest.

## Next steps

1. Defense-boost replies native (last fallback family; the only remaining
   producer calls).
2. Grouped base arithmetic for the reply compile (20.9M of 59.1M).
3. Cheaper scalar standalone/pair and orchestration arithmetic.
4. Bank space: 67 bytes left in the fast-prototype section. Deduplicate the
   two executor tails or open a second reference-only section before adding
   code.

---

# Continuation 2026-09-07 (Claude Fable, evening): performance pass

Seven more commits on `master` (`8c35e94c` .. `7e2db61a`), each validated by
the frozen-oracle comparison (76 vectors), the compiler differential (5,588)
and the pair/standalone fixtures before it was made. Broad benchmark 59.1M
-> 40.5M cycles; target 8,388,608, not met. `status.md` "Evening pass" has
the per-commit table, the current phase split and the plan for the
remaining factor of five (bank space, per-reply facts cache in WRAMX bank 2,
lighter bench standalone, defense boosts native, record grouping).

Facts a successor needs:

- The fast-prototype bank has 77 bytes free. Nothing more fits until the
  cold fallback evaluators (`BossAI_FastFallbackPair`, `BossAI_FastUnaryFallback`,
  about 750 bytes) move to their own section behind far entry points, or the
  two executors share one body.
- Scratch added today: `$a494..$a4a6` chart table (19 entries, compact type
  index), `$a4a7` Dragon majesty, `$a4a8..$a4b1` keyed incoming-regime cache,
  `$a4b2..$a4b3` packed passive contributions; control byte 451 holds the
  equal-priority tie order; `FS_UNARY_FLAGS` accumulates reached reply flags
  during the sweep and reaches the unary record in `.CommitIncoming`.
- Fixture footprints that changed: `fast_pair.py` and
  `fast_reply_standalone.py` allow `$a4a8..$a4b1`, `$a56d..$a56f`,
  `$a5c0..$a5d7`.
- Profiling: `.local/ai-two-second/phase_profile.py <case> <label,list>`
  (entry-order attribution) is the tool that guided every step; a label
  list of about 90 symbols runs in five to ten minutes. `flat_profile.py`
  (every symbol) does not finish in reasonable time.
- Game ROM bytes unchanged throughout (SHA1 `85a2fe838a28f23b198845e63876a637580e91a9`).

---

# Continuation 2026-09-07 (Claude Fable, late): boosts native, cold bank

Commits `984a531b` (fallback evaluators in their own bank) and the native
defense-boost family (see `status.md` "Native defense-boost replies and the
cold-bank move"). Every gate exact; 25 of 26 decisions native-only; broad
benchmark 36.9M cycles (target 8,388,608, not met).

New scratch: `$a4f8..$a50f` defensive variants (eight 3-byte slots, two per
plan), `$a4b4..$a4b7` amount override (flag exactly 1 while live), the
`BossAI_FastProjectPlayerDefense` bridge in `fast_producers.asm` uses
`$a491..$a493` as temporaries. `FSR_BOOST`=9 with stages/axis at record
bytes 43/44. The physical base cache no longer caches powers of 120 and
above.

Own boost plans (the boss's Harden etc.) are the one remaining fallback
family: they need the reply amounts at the raised own defense, i.e. the
native reply compiler run with an overridden defense fact for the affected
category, which is a small extension of the same variant idea.

---

# Continuation 2026-09-07 (Claude Fable, night): own boosts native, two cold sections

One code commit and one docs commit on `master` (not pushed). See
`status.md` "Native own defense-boost plans and two more cold sections" for
the mechanism, the fixture counts and the timing; `cleanup_notes.md` for the
code-quality follow-ups it left.

Facts a successor needs:

- Bank space: the fast-prototype section is at $3d25 of $4000 (731 bytes
  free). Results/finalizer code lives in "Boss AI Fast Results", HP table
  construction plus its event mask table in the page-aligned "Boss AI Fast HP
  Tables"; both behind far entries (`BossAI_FastPreparePublicInputsFar` takes
  C=kind; the HP builders return the mode through C). Moving a routine out of
  the hot bank means every `call` it makes into the hot bank becomes a
  farcall: the finalizer's divide was missed the first time and hung every
  decision.
- `check_cross_bank_call.py` reads `pokegold_ai_reference.sym` too now. The
  other static audits (`check_farcall_hl_clobber.py`,
  `check_farcall_a_clobber.py`) may still see only the game sym; check before
  relying on them for reference-only code.
- `ValuePublicExchange.DefenseInputs` derives the axis from the live AD's
  `AD_MOVE` halfway through. Any bridge that reuses it must stage a boost move
  with the wanted axis/stages in the AD (`BossAI_FastProjectOwnDefense` does).
- New scratch: own actor view bytes 16..23 (`FSA_OWN_VARIANTS`,
  `FSA_OWN_VARIANT_MASK`, `FSA_START_REGIME`); plain damage reply record bytes
  7..8, 26..27 and 23 (`FSR_VARIANT_A/B/FLAGS`); `FSM_VARIANT` = `FSM_TEMP+4`
  during an amount. `FSV_OVERRIDE` is now honoured by both executors.
- Assault Vest makes status moves illegal for the boss, so it cannot be used
  to test own boosts with an item; Eviolite can (`joint_own_boosts_eviolite_slow`).
- The scratch tools that found the two defects: `.local/ai-two-second/
  debug_joint_pairs.py <case>` (per-pair native versus forced fallback) and
  `debug_own_boost.py <case> <own move> <reply>` (variant table, record bytes,
  and the reference's recorded own defense and boosted damage side by side);
  `trace_entry.py <case> <labels> [frames]` reports where a hung entry
  stopped. Background runs did finish this session when given no timeout and
  a log file; the harness reopens the ROM per case, so never rebuild while a
  run is in flight.

## Speed pass (2026-09-07 night to 2026-09-08)

Work happened in the worktree `.claude/worktrees/ecstatic-lewin-9d3386`
(branch `claude/ecstatic-lewin-9d3386`, with copies of `rgbds-1.0.1/` and
`.local/ai-two-second/` since both are untracked), fast-forwarded into
`master` after each green commit: `b5e52223`, `35c36038`, `4133fdbe`,
`0b91d7d8`. The numbers per commit are in status.md ("Speed pass"). Broad
benchmark 36,186,008 -> 27,696,268 at `0b91d7d8`; average 2,906,745 ->
2,388,164; target 8,388,608 not met (two fixtures over: the broad case and
`joint_speed_tie_transformed` at 8.77M).

- Fast pairs (`fast_selector.asm`, after `.SignExtend24`): `.PreparePlanPairs`
  (once per active defender, after `.ReplyRegimes`), `.PlainStandalone` (plain
  damage replies, active and bench), `.FastPair`/`.FastK1`/`.FastK2`/
  `.FastFlags`/`.FastAccumulate`, `.CommitPairs` (after `.CommitIncoming`).
  State in "Boss AI Fast Sweep State" (WRAMX bank 1, reference build only,
  declared in fast_selector.asm): `wFastPlanPairs` (4 x FPP_SIZE),
  `wFastReplyPair`, `wFastStartOutRegime`, `wFastStartGated`, plus the
  page-aligned `wFastReplyWeights`. `.ReplyRegimes` sets the start facts for
  every defender; `.ReplyStandalone` clears `wFastReplyPair+FRP_STATE` first
  so only `.PlainStandalone` marks a reply eligible.
- The identities the fast pairs rely on: for a plain damage own plan the own
  HP after the own hit is the start HP, so K1 is zero unless the reply's
  regime after the own hit differs from the start regime (or the hit fainted
  someone); for a plain damage reply likewise for K2 with the outgoing
  regime. Recovery plans compute from the healed HP (`.OwnHPAfterOwnHit`,
  `.OwnPhiAfterOwnHit` = start Phi + own delta) and heal from the HP the
  reply left (zero when it is the start HP). Recovery replies (7 moves) stay
  on `BossAI_FastScalarPair`.
- The per-pair differential `.local/ai-two-second/wt_debug_fastpair.py
  <case>` snapshots SRAM, the context and the sweep state at every `.FastPair`
  call and replays each through the old scalar pair and the fast pair,
  comparing K and the flags. Run it before the oracle after any pair change.
- Cold sections added: "Boss AI Fast Reply Facts" (facts preparation, chart
  mirror and index, `BossAI_FastTruncateStatsFar`), "Boss AI Fast Actors"
  (`BossAI_FastImportActorHP`, reaching the potential through
  `BossAI_FastOwnPotentialFar`/`BossAI_FastPlayerPotentialFar`, BC in and
  out), "Boss AI Fast Recovery Quota". Hot bank after `0b91d7d8`: $3f23 of
  $4000 (221 bytes free); with the level-term/plan-header commit $3f6a
  (150 free). Space for anything larger comes from moving
  `BossAI_FastBuildOwnedStandalone` or the executors cold with thunks.
- Trap: a routine moved cold can still read data tables in the hot bank; the
  cross-bank audit checks `call`/`jp` only. The chart mirror had to move with
  `.BuildChart`.
- Trap: the compile's regime loop uses `FSM_TEMP+3` as its mask counter, so
  the priority is not there after the amounts (read it from the record).
- Level-term/plan-header commit (`.local/ai-two-second/wt_patch_f.py`:
  `wFastLevelTerm` = floor(2L/5)+2 once per defender in
  `BossAI_FastPrepareReplyFacts`, `.Passives` gated by the packed
  contribution bytes, FPP_SIZE 32 with the plan header read through
  `.PlanPairByte` by `.PlanPair`, `.OrderDescriptor` and `.FastFlags`):
  built and exact (oracle 88, per-pair differential 0 of 636) but measured slower, broad 27,696,268 -> 27,992,100 and `joint_speed_tie_transformed` 8.77M -> 9.21M, because `.PlanPairByte` (push/pop plus the facts address) costs more than the arithmetic `.PlanAddress` it replaced; reverted, not on master. Worth retrying with only the level term and the passive gating (the first two edits of the patch), which should save about 0.4M.
- Profiling: `python -m tools.boss_ai_fixtures.fast_ordinary_profile` (whole
  decisions; PHASES include the fast-pair labels) and `PYTHONPATH=. python
  .local/ai-two-second/phase_profile.py <case> <labels>` (entry-order
  attribution). Launch long runs one per background command; two profiles
  started from one shell with `&` shared a log file and ran concurrently for
  fifteen minutes.
