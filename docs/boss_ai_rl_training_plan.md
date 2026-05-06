# Boss AI RL Training Plan (v2 — RL-ROM)

> **STATUS: SHELVED 2026-05-05.** Do not start work on the v2 RL training
> simulator until the user explicitly resumes. See
> [boss_ai_design_conversation_2026-05-05.md](boss_ai_design_conversation_2026-05-05.md)
> — the simpler architecture surfaced there (algorithmic moveset priors +
> unified scoring) likely obviates the need for v2 RL training entirely
> (playtest tuning likely sufficient). The simulator infrastructure has
> standalone value for future work (regression testing, AI vs AI tournament
> mode); could resurrect for that purpose independently of priors-tuning.
> Active focus has shifted to fully building out the damage debugger
> (`tools/damage_debugger/`).

**Status — 2026-05-05.** Plan documented. Not yet started — gated on v1 boss AI rebuild (BOSSAI-003) shipping. Decisions locked via interview pass 2026-05-05.

This file is the canonical plan for the v2 RL training simulator. It supersedes the paragraph in `docs/boss_ai_rebuild_plan.md` ("Out-of-scope for v1 — captured for v2"). v1 ships with corpus-only Layer B; once corpus coverage proves insufficient after playtesting, this plan kicks off.

Related reading:
- `docs/boss_ai_rebuild_plan.md` — v1 rebuild (Layer A + corpus-driven Layer B online CFR). Read this first.
- `tools/damage_debugger/` — infrastructure pattern this reuses (PyBoy + boot cache + `safe_call.py`).
- `audit/boss_ai_trace/*_live.txt` — per-leader live captures, the regression suite for trained agents.

---

## Why this exists (and why it's v2, not v1)

v1 ships Layer B with hand-tuned per-leader priors (cold-start bluff frequency 5–18% across leaders, regret step size, max-bluff cap) plus a human-curated corpus of structural rules ("in this state class, the crazy play is move X"). Online CFR adapts the bluff frequency in-battle from observed exploitation; the corpus is the ground-truth "what counts as a bluff."

The v1 corpus will be sparse at ship: ~30-50 entries from playtests across 16 leaders is undercovered. The hand-tuned priors are educated guesses, not optimization-derived values. v1 will play *fine, but not great* against a thinking human.

v2 fixes both gaps via simulation: thousands of self-play battles per leader, a population of opponents that punish predictable play and reward general robustness, a parameter optimizer that finds priors maximizing corpus-weighted reward.

Two failure modes of naive RL the design specifically guards against:

- **Self-play degeneracy.** Pure self-play converges to a Nash equilibrium *within the policy class*; if the class is narrow you get a degenerate equilibrium that loses to anything outside the class. Mitigated by the population (multiple scripted personalities + historical snapshots).
- **Overfit-to-base-AI.** Training only against base game AI teaches the agent to exploit base AI's specific predictabilities, not to play robust Pokemon. Mitigated by base AI being *one voice in the population*, not the only opponent.

## What gets trained, what stays human

This is **not deep learning.** The training problem is tuning ~30-50 numerical parameters per leader in a fixed policy class (Layer A + Layer B). CMA-ES or genetic algorithm finds a near-optimal point in that space in tens of thousands of battles — minutes-to-hours of wall clock, not GPU-weeks.

**Trained per-leader:**
- Cold-start bluff frequency
- Regret update step size
- Max bluff cap
- Counter-switch denial bonus magnitude
- Layer A softmax temperature
- (and the small handful of other per-leader knobs Layer A/B exposes)

**Trained globally (one value, all leaders):**
- `EV_THRESHOLD` — when to mix vs play top in Layer A's near-tie detection.

**Human-defined, never RL-tuned:**
- Corpus structural rules (what counts as a crazy play in a state class). RL only adjusts *priors and frequencies*; structural taste stays gated to user judgment.
- Layer A heuristic logic itself.

**Reward signal:**
- Corpus agreement: 5× weight when state is tagged. Per-decision dense feedback.
- HP differential at battle end: 1× weight.
- Win/loss: 1× weight.
- Soft over-bluff penalty: penalize bluff_freq far from observed-optimal-against-this-opponent (computed post-hoc per training run).
- Smoothed over a 50-battle rolling window.

**No entropy bonus on AI's move distribution.** The AI is allowed to win efficiently if it can. Boring-win patterns surface as corpus disagreements during regression checks; corpus tagging is the place to address them, not the reward signal. This is a deliberate design choice — reward-shaping for "feel" puts feel-knobs in the wrong layer.

## Population (the league)

Eight scripted personalities + historical snapshots:

1. **Base game AI** — the predictable-opponent benchmark.
2. **Layer-A-only** — Layer B disabled. The "no bluffing" baseline.
3. **Greedy EV-max** — always argmax, no mixing. Pure deterministic.
4. **Status-spam bot** — prioritizes Para/Sleep/Toxic; tests AI's status defense.
5. **Setup-merchant** — looks for free turns to boost; tests AI's tempo response.
6. **Switch-happy** — any unfavorable matchup → switch; tests AI's switch denial.
7. **Bluff-bot** — high cold-start bluff freq (40%), never decays; tests AI's read game.
8. **Historical snapshots** of the trained agent itself (every 1k battles, capped at 8 most recent).

Plus **3 hand-written exploiter agents**, scoped after the first training run reveals the trained policy's blind spots. Style: "always pick the move that exploits the assumption that AI never bluffs into resists." Forces robustness against targeted exploits, à la AlphaStar's exploiter agents. Built in Phase 7.

Population is **shared across leaders.** Each leader trains its parameter set independently against the same league. Leader differences come from final converged params, not from training opponents.

Per-battle opponent sampling: uniform from the population, with current trained agent's most-recent self at 1.5× weight (slightly favors recent self-play without dominating).

## Per-battle simulation: how it actually runs

Reuses the damage debugger's PyBoy + boot-cache infrastructure:

1. Generate a random battle context: leader (fixed for the run), leader's team (from `data/trainers/parties.asm`), player team (from a synthetic-team generator constrained to the leader's gym point in the game), starting HP/PP/items.
2. Inject context into RAM via the same `boss_ai_state_factory` pattern used for trace captures.
3. Sample opponent personality from the population.
4. Run battle to termination headless. Trained agent uses current parameter values from the optimizer; opponent uses its scripted policy.
5. Record decision trace (every move chosen, every score, every Layer B state transition) for reward computation.
6. Compute reward; feed back to optimizer.

Single-process throughput: ~500 battles/min with boot cache (proven on damage-debugger side). Parallelized 4-8×: 2-4k battles/min. A 1-hour run is 120-240k battles per leader, plenty for parameter convergence in a ~50-dim space.

## Training run mechanics

**On-demand initially.** CLI: `python -m tools.boss_ai_rl_training run --leader whitney --duration 60m`. Prints structured log to terminal; writes a Markdown final report.

**1-hour cap with checkpoint/resume.** Auto-checkpoints every 10 minutes. `--resume <run_id>` continues from latest checkpoint. Avoids runaway runs; supports "I have an hour, run training, come back to results" flow.

**Final report includes:**
- Win-rate vs each population member (start vs end of run).
- Final parameter values (diff vs previous run).
- Corpus agreement rate (start vs end).
- Top-5 disagreements with corpus (surface for review).
- Convergence indicator (regret-update size below threshold for last N batches).

**Phase 2 (later, after we trust it):** scheduled runs (e.g., nightly retraining as corpus grows). **Phase 3 (maybe never):** background daemon. Neither phase 2 nor phase 3 is committed in v2 scope.

## Validation: shipping a trained agent

Trained agents go through the same trace-pipeline + corpus regression check that v1 uses, applied post-RL:

1. After a training run completes, run trained agent against every per-leader trace capture (`audit/boss_ai_trace/*_live.txt`).
2. Surface every decision that disagrees with the captured one.
3. User judges each disagreement: AI improved → update capture; AI regressed → kill the run, retune params or fix the heuristic.
4. If all disagreements are "improved" or "no change," trained params land via `scripts/land_trained_priors.py` into `engine/battle/ai/policy_priors.asm` (or wherever the final asm representation lives).

**Playtest gate:** trace+corpus is enough for shipping to the dev branch. **Explicit user playtest is required only before tagging a public release.** Keeps cadence high during normal development — a trained agent can land same-day if metrics are clean — and reserves user time for the high-stakes release validation.

## Decisions locked (2026-05-05, interview pass)

- **Strict v1 → v2.** Training infra build starts only after v1 ships. No parallel work.
- **On-demand training, 1-hour cap, terminal log + final report.** Phases 2 and 3 (scheduling, daemon) deferred.
- **8-bot full nominee list + 3 exploiters** (exploiters scoped after first run, Phase 7).
- **Shared population, per-leader training.**
- **Reward: Corpus 5× / HP-diff 1× / win-rate 1× / soft over-bluff penalty.** No entropy bonus.
- **Trained: per-leader regret + cap + softmax + counter-switch bonus, global EV_THRESHOLD.** Corpus structural rules strictly human-defined.
- **Regression: trace + corpus disagreement surfacing.** Playtest only for releases.

## Phasing

### Phase 1 — Headless battle simulator (~1 week)

Adapt damage-debugger boot cache + state-factory injection to drive a complete battle to termination with two scripted/trained policies. Verify against a known reference battle (e.g., a per-leader trace capture) for byte-identical determinism with seeded RNG.

Output: `tools/boss_ai_rl_training/sim.py`, smoke test verifying determinism.

### Phase 2 — Population (~3-4 days)

Implement the 8 scripted bot personalities. Each one is a small Python class implementing the same `choose_move(state) -> move_id` interface. Verify each bot plays sensibly in 100 sample battles.

Output: `tools/boss_ai_rl_training/league/`, smoke tests per bot.

### Phase 3 — Reward + optimizer (~3-4 days)

Reward computation from decision traces (corpus 5×, HP-diff 1×, win-rate 1×, over-bluff penalty). CMA-ES wrapper over the per-leader parameter space. Verify reward function matches expected behavior on hand-crafted decision traces.

Output: `tools/boss_ai_rl_training/reward.py`, `tools/boss_ai_rl_training/optimize.py`.

### Phase 4 — Training run CLI + report (~2-3 days)

Top-level `python -m tools.boss_ai_rl_training run` entry. Checkpoint/resume. Markdown final report.

Output: `tools/boss_ai_rl_training/__main__.py`, report templates, checkpoint format.

### Phase 5 — Validation pipeline (~3-4 days)

Trained-agent vs trace-capture regression. Corpus disagreement surfacing. Param landing into asm.

Output: `tools/boss_ai_rl_training/validate.py`, `scripts/land_trained_priors.py`, new audit `tools/audit/check_trained_priors_in_sync.py`.

### Phase 6 — First training pass (~3-5 days)

Run training for all 16 leaders + Koga + Champion Lance. Land params for those that pass regression; surface disagreements for those that don't. Iterate.

This phase is where the system meets reality — expect to revise reward weights and population mix once we see what the optimizer actually finds.

### Phase 7 — Exploiter agents (~3-5 days)

After first pass, hand-write 3 exploiter agents targeting the trained policy's blind spots (revealed by Phase 6's regression results). Re-run training with exploiters in the league. Re-validate.

**Total estimate: ~3-4 weeks of focused work,** consistent with the original "2-3 weeks" estimate plus the validation/exploiter work the interview surfaced.

## File layout (proposed)

```
tools/boss_ai_rl_training/
├── __main__.py          # CLI entry
├── sim.py               # PyBoy headless battle driver
├── league/
│   ├── base_ai.py
│   ├── layer_a_only.py
│   ├── greedy.py
│   ├── status_spam.py
│   ├── setup_merchant.py
│   ├── switch_happy.py
│   ├── bluff_bot.py
│   └── snapshots.py     # historical snapshots of trained agent
├── exploiters/          # added in Phase 7
├── reward.py            # corpus + HP + win-rate + over-bluff
├── optimize.py          # CMA-ES wrapper
├── validate.py          # post-training trace+corpus check
├── checkpoint.py
└── report.py            # Markdown final report

scripts/
└── land_trained_priors.py   # writes engine/battle/ai/policy_priors.asm

audit/boss_ai_rl_training/
├── README.md
└── runs/                # per-run logs, params diff, reports
```

## Verification floor

A green training run is not enough. Adds to the existing release-smoke floor:

1. `python -m tools.boss_ai_rl_training validate --leader X --params <run_id>` — runs trained agent vs all trace captures + corpus, must surface zero "regressions" (only "improvements" or "no change").
2. After landing params: existing `check_release_smoke.py`, `check_boss_ai_no_cheat.py`, `check_boss_ai_gating.py`, `check_boss_ai_trace_invariants.py` must still pass. Trained params change Layer B *behavior*, not Layer B *invariants* — anti-cheat must still hold.
3. After landing params: trace captures are re-run with the new ROM. Distribution captures (per the v1 plan's "Trace pipeline implications" section) must be within tolerance.
4. New audit: `tools/audit/check_trained_priors_in_sync.py` — verifies `engine/battle/ai/policy_priors.asm` matches the most recent training run's output (catches "I forgot to land the params" drift).

## Risks and open questions

**Stochastic training reproducibility.** A run with seed S should produce identical params from identical inputs. Pin BattleRandom seeds in the simulator; pin numpy/random seeds in the optimizer. Audit captures the seed. Without this, "trained agent X" isn't reviewable.

**Corpus agreement might dominate too hard.** 5× weight on tagged states could mean the trained agent only optimizes the ~30-50 tagged states and plays bizarrely on untagged ones. Mitigation: monitor "corpus agreement vs untagged-state win-rate" separately in reports; rebalance if drift detected.

**Population diversity collapse.** If trained-agent snapshots dominate the population at the expense of scripted bots, training drifts toward self-play degeneracy. Mitigation: cap snapshot weight in population at ~30%; scripted bots always get ≥70% combined weight.

**Open: per-leader training time budget.** Training all 18 boss agents (16 leaders + Koga + Lance) is 18 × 1hr = 18 hours wall clock serial, ~3-4 hours parallelized. Acceptable for now; revisit if it feels slow.

**Open: retraining cadence.** After every corpus update? Monthly? After each playtest session? Decide after first run reveals the cadence sweet spot.

**Open: synthetic team generator quality.** Phase 1's "synthetic player team constrained to the leader's gym point" needs to feel realistic — using legal-but-bizarre teams produces unrealistic training distributions. Reuse `tools/damage_debugger/fuzz.py` patterns where possible; possibly seed from real playtest party snapshots.

## Out-of-scope for v2 — captured for v3

- **Continuous background daemon.** Phase 3 of training-run mechanics. Defer until on-demand mode proves stable.
- **Live-play in-loop training.** Pause real battle mid-turn, judge AI's pick, save to corpus, retrain. Useful but adds GUI complexity.
- **Multi-leader joint training.** Train all leaders' params simultaneously sharing a single objective. More compute, possibly better cross-leader coherence.
- **Cross-leader policy transfer.** Whitney's params seeding Falkner's training. Faster onboarding for under-judged leaders.
- **Live web dashboard.** Phase 4 currently ships terminal-log only; dashboard deferred to v3.

## How v2 changes the doc tree

- New: `docs/boss_ai_rl_training_plan.md` (this file)
- New: `tools/boss_ai_rl_training/`
- New: `scripts/land_trained_priors.py`
- New: `engine/battle/ai/policy_priors.asm` (target of training output, written by `land_trained_priors.py`)
- New: `audit/boss_ai_rl_training/`
- New: `tools/audit/check_trained_priors_in_sync.py`
- Modified: `docs/project_roadmap.md` — new BOSSAI-004 row
- Modified: `tools/audit/check_release_smoke.py` — adds the trained-priors-in-sync check to the floor
