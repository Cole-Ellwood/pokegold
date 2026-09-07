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
