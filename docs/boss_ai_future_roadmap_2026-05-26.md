# Boss AI Future Roadmap — 2026-05-26

**Status:** active forward-looking plan for the boss-AI workstream.
Supersedes [boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md) —
the Codex-pairing scaffolding (mutual-sign-off acceptance criteria,
handoff-log requirements, paired-LLM protocol) is dead because Cole no
longer pairs with Codex. Cross-LLM review is now one-shot ChatGPT 5.5 Pro
consultations on hard design questions; Claude is the sole executor per
the CLAUDE.md senior-dev contract.

**Approver:** Cole (sole). **Executor:** Claude.

**North Star (unchanged):** the no-hidden-info rule. Every phase below
reads only public information — seen species, revealed moves, public
TM/level-up learnability, public stat tiers, observed behavior. Haki is
the only exception and is now the uniform Oracle path documented at
[boss_ai_spec.md](boss_ai_spec.md) §"Haki Exception Contract".

---

## 1. Recently shipped

### P-A — dynamic futility cutoff on the lookahead beam

Spec: [boss_ai_lookahead_p_a_2026-05-26_v2.1.md](boss_ai_lookahead_p_a_2026-05-26_v2.1.md).

Replaces the static `initial_best + CAP` cutoff in
`BossAI_ApplyLookaheadToTopMoveCandidates` with a running
`running_best - CAP` cutoff that tightens as candidates are evaluated.
The new bound is strictly tighter than the existing static gate (no
behavior regression in well-separated cases; near-tie cases differ —
S4 sign-off received). Cost: 1 byte in the boss-AI reserve
(`wBossAILookaheadRunningBest`) + 1 byte trace expansion (3 → 4 to
cover all `BOSS_AI_LOOKAHEAD_N = 4` candidates). Cycle bench shows
−70k T-cycles on `late_lookahead_heavy`.

Round-1 and round-2 GPT 5.5 Pro reviews of the underlying v1/v2
research are at
[boss_ai_lookahead_2x_gpt_review_2026-05-25.md](boss_ai_lookahead_2x_gpt_review_2026-05-25.md)
and
[boss_ai_lookahead_2x_v2_gpt_round2_review_2026-05-26.md](boss_ai_lookahead_2x_v2_gpt_round2_review_2026-05-26.md).
v2.1 incorporates the K6 (register-aliasing), K7 (weight saturation),
and J3 (signed-product width) fixes from round 2.

**Status:** implementation, audits, cycle bench, dev_index regen all
complete and green. **Uncommitted in the main worktree.** Cole commits
on his own cadence; do not commit on his behalf.

Files modified: `engine/battle/ai/boss_policy_move.asm`, `ram/wram.asm`,
`docs/generated/dev_index.md`. New tooling:
`tools/audit/check_lookahead_futility_bound.py`,
`tools/audit/check_lookahead_trace_width.py`,
`tools/audit/check_lookahead_running_best_lifecycle.py`. New perf
JSONs: `audit/boss_ai_perf/head_baseline_10samples.json` and
`audit/boss_ai_perf/p_a_v2.1.json`. New docs: v1 / v2 / v2.1 spec +
round-1 + round-2 reviews.

### P1H — Uniform Haki Oracle (already in HEAD)

Shipped in commits `e532da2c` (oracle rework + primary-threat register
fix + curse/pain-split gates) and `3f32a2f5` (taunt text relocated into
`BANK(BattleText)`). Replaced the bespoke Morty-only path with a
generic `BossAI_OracleHakiRead` plus
`BossAI_OracleHakiAfterPlayerAction` for player-first sequencing.
Extended from 1 leader to the 16 eligible classes via the `wBossAITier
!= AI_TIER_EARLY` AND `wTrainerClass NOT IN BossAIHakiExcludedClasses`
gate. Per-leader taunt rows print before the enemy action animation.
Audit `tools/audit/check_haki_oracle_uniform.py` exists and is green.
Full design contract at [boss_ai_spec.md](boss_ai_spec.md)
§"Haki Exception Contract" through §"Hook Site".

---

## 2. Technical phases ordered by dependency

The phases below are the active forward stack. P0.5a (drift restore for
pairing-rules / handoff-log tooling) is retired with the Codex pairing
workflow. P0.5b (WRAMX bank-2 SECTION declaration) and P0.5c
(haki-coverage debugger tool) are listed where their consumers need
them; treat P0.5b as a prerequisite for any phase that needs WRAMX-2
storage (P5, P7).

### Independent / now-shippable

| Phase | Goal | ROM | WRAMX-2 | File-touch sketch |
|---|---|---|---|---|
| **P2 — KO-band oracle + matchup precompute** | Build ROMX tables and routines estimating public damage bands, 2HKO/3HKO windows, survival bands, deny-KO odds from visible inputs. Plus compile-time per-boss-roster type-matchup tables (defensive matchup vector per slot vs 17 types, offensive coverage vector per slot). Replace per-turn type-chart loops with table lookups. | 2–3 banks | 0 (recompute per candidate) or 8–16 bytes scratch if caching | New `engine/battle/ai/ko_band_oracle.asm` + `data/boss_ai/matchup_tables.asm`; per-leader matchup precompute via `tools/build_boss_matchup_tables.py`; call sites in `engine/battle/ai/boss_policy_move.asm` at `BossAI_CurrentEnemyMoveHasKOPressure` and `BossAI_CurrentEnemyMovePressureScore`. |
| **P3 — Revealed-effect interaction matrix** | Move the growing bespoke revealed-effect interactions (Protect / Recovery / Encore / Selfdestruct / SleepPreempt / Destiny-Bond / Counter-Mirror-Coat / Disable / Mean-Look / Perish / charging-rampage / phaze-hazard) into ROMX data keyed by revealed player effect, boss candidate category, tier, public speed/HP gates, board flags. | 1 bank | 0 | New `data/boss_ai/revealed_effect_matrix.asm`; refactor of bespoke helpers around `engine/battle/ai/boss_policy_move.asm:1392-1605` into table-driven dispatch. New `tools/audit/check_revealed_effect_matrix_coverage.py`. |

**Public-info filter:** P2 inputs are visible species/level/typing/HP/
status/stages; boss-known own moves/items; revealed player moves;
observed damage calibration. Player-side stat uncertainty becomes
coarse banding only; never reads private stats. P3 reads only exact
revealed moves in `wPlayerUsedMoves` / per-species public memory,
public last move, visible HP/status/boosts, public speed predicate.
No plausible-mask entry becomes an exact revealed-effect trigger.

**P2 is the highest-leverage next phase** because the deferred stack
(P-C / P-D) is gated on it. P3 is fully independent of P2 and can
ship in parallel.

### Sequentially gated

| Phase | Goal | Gated on |
|---|---|---|
| **P5 — Observation log + tendency counters + speed/damage calibration** | Single WRAMX-2 buffer (16–32 bytes) holding the last ~6 turns of public observations (turn, actor, action_class, observed damage band, speed relation). Tendency counters: switches under threat, attacks into bad public matchup, repeated protect/recover, greedy setup under pressure, status fishing, low-HP sack acceptance. Calibration feedback into P2's oracle. | P2 (calibration reads oracle's KO bands). Also needs P0.5b WRAMX bank-2 SECTION declaration. |
| **P6 — Role/package classifier** | Classify each seen player species into coarse public packages (spinner, phazer, setup-sweeper, recovery-wall, priority-revenge, sleep/status-pressure, trap/perish-line, physical/special wallbreaker). Package bits feed preservation switches, plan templates, route valuation. | None — independent of P2/P5. Can ship between them. |
| **P7 — Coach-plan template engine, minimal-first** | Compact ROMX table of public-gated plan templates. Minimal-first set: `attack_now`, `setup_once_then_attack`, `pressure_recover_then_lock`, `cashout_sacrifice`. Plan identity supplies action-sequence bias and stop conditions rather than literal tree search. | P5 (templates consult observation log + tendency counters). Also P0.5b. |

### Deferred until branch-context ABI v3

P-C / P-D / P-B from the lookahead-2x research stack are
**not implementation-safe yet**. Round-2 review
([boss_ai_lookahead_2x_v2_gpt_round2_review_2026-05-26.md](boss_ai_lookahead_2x_v2_gpt_round2_review_2026-05-26.md))
found six load-bearing gaps that any v3 must close before any ASM
lands. The durable list lives in that file; cite it from the v3
research doc rather than re-deriving:

- **J2 — Full cache inventory.** Branch-sensitive caches
  (`wBossAIHasKOMoveCache`, `wBossAIPublicThreatCache`,
  `wBossAIRevealedPriorityCache`, `wBossAILookaheadDepthCache`,
  `wBossAIShouldScoutMatchupValue`, plausible-mask species/level keys)
  need an explicit per-bucket reset/keying policy.
- **J3 — Signed-product width.** `weight × delta` (up to `8 × ±18 = ±144`)
  must form as signed 16-bit before accumulation; SM83 has no sign
  flag, so signed compare/shift helpers must be specified.
- **J4 — Legality mask completeness.** Choice lock, Endure (priority 3),
  Substitute as PRESERVE, Pursuit-on-switch, Beat Up, Triple Kick,
  Magnitude variance, Attract, Perish count = 2 — each needs an
  explicit row in legality mask, bucket classifier, or V/P2 move-effect
  coverage.
- **K7 — Weight normalization.** Modifier order, legality re-mask after
  candidate adjustments, saturate each weight to `0..8`, renormalize to
  sum exactly 8.
- **K8 — STAR1 vs best-vs-second selector.** Existing `BossAI_SelectMove`
  is stochastic (60/75/90% best-pick by gap); pure best-only pruning
  can distort the second-best distribution.
- **K10 — Pressure-class schema.** Bit-packed public schema with
  explicit fields (`player_hp_band`, `boss_hp_band`,
  `public_threat_severity`, `boss_has_ko_band`, `player_has_ko_band`,
  `speed_relation`, `revealed_priority_flag`, `trap/perish_flag`,
  `hazard_pressure_flag`) — or fold entirely into P5 tendency counters.

| Deferred phase | Gated on |
|---|---|
| **P-C** — 3-bucket expectimax with branch-local V | P2 AND the ABI v3 covering J2 / J3 / J4 / K7 / K8 above. |
| **P-D** — Loud-node quiescence | P-C ships and V measures cheap enough; KO-only first per round-2 K9. |
| **P-B** — State-conditional bucket prior | P5 lands; P-B folds into P5 state (pressure class per K10). |

---

## 3. Verification floor

Per-phase (must pass before declaring shipped):

- `make pokegold.gbc` clean build green.
- `python tools/audit/check_release_smoke.py`.
- `python tools/audit/check_farcall_hl_clobber.py` + `python tools/audit/check_farcall_a_clobber.py`.
- `python tools/audit/check_boss_ai_no_cheat.py` + `python tools/audit/check_boss_ai_gating.py` + `python tools/audit/check_boss_ai_trace_invariants.py`.
- `python tools/audit/check_save_format_version.py` (no save-format change in scope for any phase here; if a phase needs one, escalate).
- `python -m tools.damage_debugger.clobber_smoke` — battle-code ABI safety floor; non-negotiable for any phase touching damage-chain register discipline (per `feedback_ag_nn_clobber_class` memory).
- The three P-A lookahead audits stay green:
  - `tools/audit/check_lookahead_futility_bound.py`
  - `tools/audit/check_lookahead_trace_width.py`
  - `tools/audit/check_lookahead_running_best_lifecycle.py`
- `python scripts/generate_dev_index.py --rom pokegold` after any
  successful build.
- If balance tables touched: regenerate
  `docs/generated/balance_audit.md`.

For any phase that adds WRAMX bank-2 bytes:

- `Boss AI WRAM Reserve` table in `docs/generated/dev_index.md` still
  shows bank-1 trace floor intact.
- New bytes reset through `BossAI_ResetTurnCaches` or explicit
  per-turn init.

For any phase touching score / dispatch:

- Trace parity on the 19 fixture scenarios under `audit/boss_ai_trace/`.
- Any near-tie selection diff documented in the commit message and
  taste-signed by Cole.

---

## 4. Open taste calls and escalation items

**Resolved for P-A:**

- **S4 / P-A behavior delta in near-tie cases — approved by Cole** (sole
  approver per CLAUDE.md; same sign-off as the broader S4 line in
  [audit/boss_ai_perf/hotspots.md](../audit/boss_ai_perf/hotspots.md)).
- **WRAM placement of `wBossAILookaheadRunningBest`** adjacent to
  `wBossAILookaheadDepthCache` — **approved**.

**Defaulted (holds unless overridden):**

- **Three new `check_lookahead_*` audits stay as three separate
  scripts** per [boss_ai_lookahead_p_a_2026-05-26_v2.1.md](boss_ai_lookahead_p_a_2026-05-26_v2.1.md) §8.
  Diagnostic > file-count.

**Open / not yet decided:**

- **P-A commit timing.** All work is uncommitted in the main worktree;
  bench is green; Cole commits when ready.
- **P2 next vs P3 next.** Both are independently shippable. P2 unblocks
  the deferred stack; P3 is the bigger immediate quality win for
  revealed-effect coverage and removes growth pressure on tight banks.
  Cole's call which to ship first.
- **P-C v3 spec ownership.** When P2 lands, the ABI v3 (J2 / J3 / J4 /
  K7 / K8 / K10) needs a fresh research doc, same shape as the v2 →
  v2.1 → P-A iteration, gated by another GPT 5.5 Pro round of review
  before any ASM.

**Escalation triggers (per CLAUDE.md):**

- Save-format change in any phase → escalate. (Every phase in scope is
  designed to avoid it.)
- Trainer roster / balance taste-call changes that overlap a phase's
  scope → escalate; balance and rosters stay separate workstreams
  (`docs/balance_intent.md`, `docs/buff_backlog.md`).
- Merging to master is a release event.

---

## 5. What this doc replaces

[boss_ai_rom_expansion_2026-05-23_codex_task.md](boss_ai_rom_expansion_2026-05-23_codex_task.md)
is superseded as of 2026-05-26. The technical phases (P2 / P3 / P5 /
P6 / P7) survive; the structural scaffolding (mutual-sign-off
acceptance, paired-LLM handoff log, Codex task block, Provenance /
Async-channel / Disagreement-resolution sections) does not — Cole no
longer pairs with Codex. Consult the old doc only for historical
context on dropped phases (P1, P4) or the original Phase-A research-
lane split that produced the lever inventory.

---

**End of roadmap.** Update this file when scope changes; do not start a
parallel roadmap doc.
