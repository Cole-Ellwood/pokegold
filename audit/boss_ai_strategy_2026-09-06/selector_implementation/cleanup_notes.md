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
