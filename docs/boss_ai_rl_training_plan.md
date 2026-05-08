# Boss AI Preference Training Plan (RLHF-ish Lab)

> **STATUS: VERSION A IMPLEMENTED 2026-05-08.** Version A, the
> preference-labeler MVP, exists under `tools/boss_ai_preference/`. Version B
> simulator/optimizer work remains optional and should wait until labels exist.
> This doc is the canonical roadmap for the RLHF-ish idea and supersedes the
> original v2 RL-ROM-first plan archived below.

**Decision locked — 2026-05-08.** Build **Version A, the preference labeler,**
before any simulator or optimizer. The goal is not to make a black-box boss AI.
The goal is to let the user teach the project what "smart, fair, scary, cheap,
too robotic, or stylish" means in concrete public-info battle states. Those
labels become a durable taste corpus and a regression oracle whether or not a
later optimizer ever ships.

Related reading:
- `docs/project_roadmap.md` — BOSSAI-004 now tracks this side app.
- `docs/boss_ai_design_conversation_2026-05-05.md` — explains why the simpler
  unified-scoring architecture should stay the likely mainline boss-AI rebuild.
- `docs/boss_ai_rebuild_plan.md` — archived full rebuild plan; useful context,
  not a prerequisite for the labeler MVP.
- `tools/damage_debugger/` — infrastructure pattern to reuse when the app needs
  ROM-backed fixtures, hooks, boot cache, or `safe_call.py`.
- `audit/boss_ai_trace/*_live.txt` — eventual source of real boss-decision
  states, after the fixture-backed MVP exists.

## Implementation status

Version A shipped on 2026-05-08:

- `tools/boss_ai_preference/` contains the fixture loader, JSONL label writer,
  Markdown/JSON report generator, source-derived player threat availability
  report, CLI, and local stdlib web UI.
- `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json` contains
  20 public-info fixtures across Johto, Kanto, Koga, Champion Lance, and Blue.
- `tools/audit/check_boss_ai_preference.py` validates fixture count, label
  persistence, duplicate/conflict reporting, threat availability, voucher/tutor
  gating, Old Rod/Surf encounter timing, simple gift/static sources,
  four-revealed-move slot blocking, bad switch-in suppression, and Markdown
  report coverage.
- `audit/boss_ai_preference/latest_report.md` and `.json` are generated report
  artifacts. `threat_availability_report.md` and `.json` are the generated
  player-threat map. They currently show one user pairwise preference if the
  local label file is present.

Run it:

```powershell
python -m tools.boss_ai_preference serve --host 127.0.0.1 --port 8765
python -m tools.boss_ai_preference threat-report
```

## Final product shape

This is a fun side app first and a training system second. It should feel like
playing "AI coach" for the boss brain:

1. The app shows a public-info battle state.
2. It lists legal boss actions with readable explanations.
3. The user ranks or tags the actions.
4. The app saves the label as JSON.
5. A report shows what the labels imply for scoring weights, personality
   choices, and regression disagreements.

The important constraint: every saved judgment must be explainable and portable
back into readable scoring logic or asm tables. If a trained artifact cannot
explain why it prefers an action, it does not land.

## Version A — preference labeler MVP (ship first)

Version A has no optimizer, no self-play league, and no ROM AI rewrite. It is
the narrowest useful version:

- Load curated battle-state fixtures from JSON.
- Show only public information: visible species, HP bands, revealed moves,
  known items/weather/status, turn count, and public learnability priors.
- List legal boss actions: moves, switch candidates, and "try item" only when
  the real boss context allows it.
- Display the current scorer's explanation if one exists; otherwise display the
  raw fixture/action fields without inventing confidence.
- Let the user label actions as `best`, `good`, `bad`, `cheap`, `scary_good`,
  or `needs_context`.
- Save every label with fixture id, action id, user tag, optional note, timestamp,
  and tool version.
- Produce a Markdown/JSON report: label counts, top disagreements, and candidate
  weight changes for human review.

MVP done means the user can label 20-50 states in one sitting and the repo gains
a reviewable corpus. Nothing auto-lands into ROM from Version A.

## Version B — RLHF-ish lab (later)

Version B is the fun experiment layer after labels exist. It can be useful, but
it should grow out of Version A's corpus instead of replacing it.

- Compare two candidate policies on the same labeled fixture set.
- Fit small readable scoring weights against labels.
- Generate fresh scenarios from trace captures or controlled PyBoy state
  factories.
- Run AI-vs-AI tournaments for regression and entertainment.
- Try an optimizer over a fixed, readable policy class.
- Surface disagreements back to the labeler before any result is trusted.

Still out of scope: deep learning, opaque policy blobs, giant auto-generated asm
tables, or "the optimizer says so" as a reason to land behavior.

## Why this is not useless

The scarce resource is taste, not compute. Battle simulators can optimize win
rate; they cannot know when a win feels cheap, when a bluff feels earned, or when
a boss should preserve its ace because that is the personality of the fight.

The preference corpus remains valuable even if Version B never happens:

- It becomes a regression suite for future boss-AI changes.
- It turns vague taste into concrete examples.
- It gives Codex sessions stable evidence instead of asking the user to re-argue
  the same design calls.
- It can guide the simple unified-scoring rebuild just as well as a later
  optimizer.

## Phasing

### Phase 0 — schema and fixture slice

Define the fixture schema and hand-author a tiny set of representative states:
obvious best move, risky switch, hidden coverage threat, "cheap" punish, and
leader-personality choice.

Output: schema doc plus 10-20 fixtures.

### Phase 1 — labeler MVP

Build the local side app or CLI-backed web view. It reads fixtures, shows legal
actions, records labels, and writes the first report.

Output: `tools/boss_ai_preference/`, label JSON, report command.

### Phase 2 — scoring inspector

Connect labels to the current boss AI or the simplified future scorer. The app
should show where the scorer agrees/disagrees with the user's labels and why.

Output: disagreement report; no auto-edits.

### Phase 3 — readable weight fitting

Fit small weights against the labeled corpus and produce proposed diffs or
parameter tables for review. The proposal must name the examples it improves and
the examples it worsens.

Output: candidate weights + tradeoff report.

### Phase 4 — simulator/tournament lab (optional)

Reuse damage-debugger/PyBoy patterns to generate fresh battle states and run
policy comparisons. This is where the old "RL-ROM" infrastructure becomes useful
as a lab, not as the first deliverable.

Output: generated fixtures, tournament report, expanded corpus.

### Phase 5 — optimizer/training (optional)

Run an optimizer only over a fixed, readable policy class. Optimizer output must
round-trip through the labeler and trace regression before landing.

Output: reviewed params, never an opaque trained model.

## Data shape

Suggested label record:

```json
{
  "fixture_id": "whitney_miltank_vs_geodude_turn3",
  "state_version": 1,
  "action_id": "switch_clefable",
  "label": "scary_good",
  "rank": 1,
  "note": "Preserves Miltank and punishes the obvious Rock switch-in.",
  "created_at": "2026-05-08T00:00:00Z",
  "tool_version": "boss-ai-preference-v0"
}
```

The fixture schema should keep state separate from labels so the same state can
be re-labeled, compared across policies, or regenerated from trace tooling.

## Verification floor

For Version A:

1. Fixture schema loads cleanly.
2. Labeler can write and re-read labels without data loss.
3. Report command includes every label and flags duplicate/conflicting labels.
4. Docs navigation check passes.

For later versions:

1. Any policy/weight proposal includes agreement and disagreement examples.
2. No ROM behavior lands without trace/audit checks from the boss-AI rebuild
   lane.
3. Any simulator-generated state records its seed and source so results are
   reviewable.

## Archived original RL-ROM plan

The sections below are retained as historical design material from 2026-05-05.
They are no longer the current ordering. Do not start with the headless
simulator, population, reward, and optimizer unless Version A already exists and
the user explicitly resumes the lab path.

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
