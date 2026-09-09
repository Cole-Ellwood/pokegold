# Selector code cleanup notes

Started 2026-09-07 by Claude Fable while taking over the exact joint selector.
These are observations about code that works but could be written better.
Nothing here is a correctness defect; each item was left alone deliberately so
the orchestration work stayed reviewable. Revisit after the timing gates.

## fast_*.asm (Codex-authored foundation)

- `fast_pair.asm` `.OwnAddress`/`.ReplyAddress` recompute `64*index` with a
  six-step shift loop on every field read. A cached plan base pointer (like
  `FSE_PLAN` in the executor) would remove ~40 cycles per field access in the
  hottest loop. Same pattern in `fast_standalone.asm` and `fast_pair_fallback.asm`.
- `fast_plan_executor.asm` and `fast_reply_executor.asm` are near-duplicates
  (regime test, range/support masks, item quota, recovery). The only real
  differences are which actor is user/target and the Pursuit/absent opcodes.
  A shared body parameterised by an actor-direction byte would halve the code.
- `fast_actors.asm` `BossAI_FastImportActorHP` rebuilds the player HP table on
  every call. The ordinary selector calls it once per defender (active plus each
  bench entry), so the player table is rebuilt up to six times per decision for
  identical inputs. Split into own/player halves once the phase profile confirms
  the cost matters.
- `fast_plans.asm` and `fast_reply_plans.asm` duplicate the four-regime
  `PublicDamageRange` sweep and the descriptor selection. Only the item tag
  (Life Orb/Shell Bell vs Helmet) differs.
- `fsp_store`/`fsr_store` macros push/pop AF and reload the plan pointer for
  every byte stored; a plan pointer held in HL with `ld [hl+]` sequences would be
  both shorter and faster for the contiguous header bytes.
- `fast_results.asm` finalizer keeps `FS_RESULT_PTR` in SRAM and reloads it per
  record instead of walking HL; harmless but noisy.
- Many routines validate `c < 4` then recompute the same shift; a single
  `.PlanAddress` helper shared across files would be cleaner (each file has its
  own copy today: executor, standalone, pair, fallback, selector).

## Orchestration (Claude-authored, 2026-09-07)

- `fast_selector.asm` uses SRAM temporaries (`FSC_TEMP`) for 40-bit shifts and
  adds because register pressure with DE pinned to the context is severe. If
  the orchestration arithmetic ever shows up in the profile, a dedicated
  five-byte accumulator routine with the record pointer in HL would be faster.
- `BossAI_FastPrepareOwnedCandidate` runs `PreparePublicAction` once per plan
  (four times for four moves) even though only the last epoch's incoming actor
  template is used by the reply sweep. One preparation per defender plus a
  cheaper per-move outgoing build would save three template/actor rebuilds.

## Profile-driven observations (2026-09-07)

- `BossAI_FastCompileReplyPlan` runs `PublicDamageRange` for all four HP
  regimes on every reply (7,059 calls on the broad benchmark). At most two or
  three regimes are ever reachable for a given defender and its live plans.
  `FSR_VALID` exists for exactly this and is currently always 15.
- `BossAI_FastNormalizedPair` averages ~19k cycles per pair. Most of it is the
  `.Flags` pass executing `FlagsOnly` for up to four event combinations plus
  repeated `.OwnAddress`/`.ReplyAddress` recomputation; a per-pair cached plan
  pointer and a flags pass that skips events whose flags are already known
  from the standalone continuations would help.
- `BossAI_FastBuildReplyStandalone` executes both original events even when
  accuracy is 255 (miss mass zero): the miss execution result is unused for
  scoring in that case and only the flags matter.
- The unary fallback and the pair fallback both rebuild the whole producer
  prefix per event through `ValuePublicExchangeFromContext`; on the broad case
  that is 189 direct evaluations (27M cycles).

## Native families (Claude-authored, 2026-09-07)

- The `.multi`/`.MultiPath`/`.fang`/`.false_swipe`/`.CapWord` tails are
  generated from one template into both executors with only the target offset,
  the maximum-HP source, the amount lookup and the endpoint selection
  substituted (see `.local/ai-two-second/patch_families2.py`). Together with
  the pre-existing duplication this makes the executor pair the obvious place
  to recover bank space: one body parameterised by a direction byte would save
  roughly 600 bytes.
- `BossAI_FastFallbackPair` now has three entries (full, correction only,
  native correction only) selected by a mode byte with bit tests inside the
  loop. Clearer would be two routines sharing the event loop through a
  terminal callback, but the SM83 has no cheap indirect call and the mode
  byte costs less than the duplication it replaced.
- The multihit/False Swipe min-delta bytes live in four scattered reply-record
  bytes (7, 8, 23, 26) because the 48-byte record has no room for four more
  words. A record layout pass that drops the unused hit-flags byte and packs
  the item quota would free a contiguous run.
- `FSX_*` family scratch aliases the damage script's `FST_*` inputs; correct
  because every family loads its result into BC before jumping to `.Script`,
  but a reader has to know that. Eight more free bytes anywhere in the
  executor area would remove the aliasing.
- The fixtures for the families patch the producer context the same way the
  compilers do (hits 1/1, effect NORMAL_HIT) to compute expectations; that is
  the right independent check for the compile but it means the fixture
  encodes the same idea twice. The executor comparisons against
  `ValuePublicExchange` are the real independent evidence.

## Evening performance pass (Claude-authored, 2026-09-07)

- `BossAI_FastCompileReplyNative.Scale` now has six entry conditions (A==H,
  H==1, A==H+1, A==H-1, 217/255, general). The general path with
  `.Div24By8` is reached only by the 2/3 Dragon passive and Selfdestruct's
  uncached formula. A table of the eleven (A,H) pairs the compiler actually
  uses would read better than the arithmetic dispatch.
- `.Passives` reads two packed contribution bytes with rotate-and-mask
  sequences. Eight plain bytes would be clearer; the packing exists only
  because the bridge area between the regime cache and `FSB_PREFIX` had two
  bytes left.
- The keyed incoming-regime cache compares eight bytes on every call. It hits
  on every standalone and on pair states that repeat the start state; a
  per-defender "start regime" byte set by the facts preparation would be
  cheaper but was wrong for the unit fixtures, which call the scalar routines
  without the facts pass. Fix the fixtures' setup rather than the cache if
  this ever matters.
- `fast_selector.asm` `.IdentityStandalone` duplicates the executor's gate
  logic for the trivial record (check flags, damage flags when able to act,
  unknown damage on an unsupported hit). If the executor's gates change, this
  must change with them; a shared "flags at a living state" routine would
  remove the duplication.
- The three profile scripts under `.local/ai-two-second/` are scratch; the
  label-list profiler is worth promoting into `tools/boss_ai_fixtures/` as a
  proper tool since every performance step relied on it.

## Own boosts and cold sections (Claude-authored, 2026-09-07, night)

- `BossAI_FastCompileReplyVariants` is called for every compiled reply and
  returns on the own-variant mask; hoisting that test into `.ReplySweep`
  saves about 150k cycles on the broad benchmark (1,524 calls at 104 cycles)
  for a two-line change. Left for the next performance pass so this checkpoint
  stayed a single validated change.
- `.IdentityPair`, `.BoostPair` and `.OwnBoostPair` are three hand-written
  variants of "which action's flags are reached in which order"; a shared
  reached-flags helper taking the two successors and the order would remove
  the duplication and the per-routine reasoning about miss masses.
- `BossAI_FastProjectPlayerDefense` and `BossAI_FastProjectOwnDefense` are
  the two directions of one operation and could share the raise/screen/item
  tail; the own side reuses `.DefenseInputs` and needs the staged `AD_MOVE`,
  the player side re-implements the reads. Pick one shape.
- `FSA_OWN+16..23` was chosen for the own variant table because the actor
  import zeroes the whole 80-byte view (so bench defenders inherit an empty
  mask for free); the contract's allocation table should list the actor-view
  extras in one place instead of the current scatter across notes.
- The static audits other than `check_cross_bank_call.py` still read only
  `pokegold.sym`; the reference-only sections are invisible to them. Worth a
  shared sym loader in `tools/audit/asm_scan.py`.
- `.OwnVariants` and `BossAI_FastCompileReplyVariants` use `FSM_TEMP+3/+4` as
  scratch outside a compile; that is safe today only because no compile is in
  flight at either point. A dedicated byte would make the lifetime explicit.

## Speed pass (Claude-authored, 2026-09-07 night to 2026-09-08)

- `BossAI_FastScalarPair` (1,451 bytes) now serves only recovery replies and
  the unit fixture; its standalone (`BossAI_FastScalarReplyStandalone`) only
  recovery replies too. Once family replies get fast paths, both can become
  a small recovery-reply pair or move cold with thunks for their hot helpers.
- `.IncomingRegimeIndex` duplicates `.ReplyRegimeBit`'s arithmetic and
  `.OutgoingRegimeIndex` duplicates `BossAI_FastScalarPair.OutgoingRegime`;
  one index routine each with the bit table applied by the caller would
  remove both copies.
- `.PlanPairFacts` clobbers A; every caller that holds a value in A must
  save it (the union OR did not, once). A version that preserves A costs a
  push/pop and would remove the trap.
- `.IdentityPair`, `.BoostPair` and `.OwnBoostPair` still read the plan
  record through `.PlanAddress`; the per-plan facts hold the plan header.
- The fast-pair flags pass re-reads the own and reply accuracies per event
  combination; hoisting the two mass tests out of the loop halves its cost.
- `fast_ordinary_profile.py` attributes by entry order; a label that is not
  in PHASES falls into the previous phase, which is why the compile phase
  absorbed `.PlainStandalone` until the labels were added. Add new selector
  labels to PHASES with the code.

## Speed pass, second day (Claude-authored, 2026-09-08)

- Four header bytes of the compile scratch now double as amount facts
  (`FSM_PASSIVE`, `FSM_CHART_ROWS`, `FSM_REGIME_REPEAT`, `FSM_CHART_MAJESTY`).
  Correct because the header is written before any amount compiles, but a
  dedicated eight-byte amount-facts block would make the lifetimes obvious;
  `FSM_TEMP` is full.
- `.MatchupByRows` is `.chart_apply` on EFFECTIVE tabulated by hand (from a
  Python simulation of the routine). The compiler differential covers it for
  every move in eleven scenarios, one of them a Dragon attacker, but a
  generator or an ASSERT-style derivation would remove the duplicated rule.
- `engine/battle/ai/fast_contact_flags.inc` restates the contact table as
  254 `DEF` lines because RGBDS cannot read `db` values back. It is the
  first generated `.inc` under `engine/`; if a second one appears, give the
  generators a shared home and one audit that checks them all.
- The reply executor's miss path still runs `.validate`/`.represented`
  (about 1.2k cycles) to reach two flag ORs; the standalone's start-state
  compare and `.PlainStandalone`'s "miss = start" are the same fact written
  twice. A miss-only entry that returns the flags without touching the
  continuation would remove both.
- `BossAI_FastImportActorHP` takes its keep bit in C bit0 because both
  weights (128, 192) leave the low bits free. It is an ABI convention with
  one caller; if a second caller appears, give it a named constant.
