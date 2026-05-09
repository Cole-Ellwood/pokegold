# Boss AI Rebuild Design Conversation — 2026-05-05 (SHELVED)

> **STATUS: SHELVED 2026-05-05.** Do not start work on the boss AI rebuild
> (BOSSAI-003) or RL training simulator (BOSSAI-004) until the user explicitly
> resumes them. Active focus has shifted to fully building out the damage
> debugger (`tools/damage_debugger/`). User wants more time to think about
> whether a full rebuild is the right approach — the design conversation
> below surfaced a much simpler architecture that may be the actual right
> path when work resumes.

## What this doc captures

A 2026-05-05 brainstorming session that started as Layer-B-CFR refinement
and ended with the user shelving the rebuild for further thought. This file
preserves the architectural ideas, the open questions, and the recommended
path so the next session opening this work can pick up cold.

The two existing plan docs — `docs/boss_ai_rebuild_plan.md` (v1 Layer A +
Layer B CFR) and `docs/boss_ai_rl_training_plan.md` (v2 RL training
simulator) — remain on disk as the most-recently-locked plans, but should
be **re-evaluated against the simpler architecture below before committing
to either.** Both carry SHELVED banners pointing here.

## Core insight (the load-bearing one)

The single conceptual shift that makes a strong non-cheating AI possible:
**the AI plays against a probability distribution over the player's hidden
state, not just the revealed state.** That's the foundation. Everything
else (mixing, personality, pattern detection, per-leader feel) is bonus
that bolts onto a probabilistic core.

Without probabilistic reasoning the AI is structurally blind to
unrevealed-but-plausible threats. With it, even simple heuristics produce
intelligent-looking play.

## Diagnostic scenario: Suicune / Ice Beam

The conversation crystallized around this scenario:

- AI's Dragonite is in front. Player's Suicune is in front.
- Suicune's revealed moves do not (yet) include Ice Beam.
- Surface read: Water STAB, Dragon resists, "favorable matchup, stay in."
- Real read: Ice Beam is the standard coverage move on Suicune (~70%
  prior in any reasonable meta), 4× super-effective on Dragonite,
  high kill probability if Suicune carries it. Switch out.

A knowledgeable human trainer makes the second read using public-meta
knowledge. Vanilla AI (and the current `boss.asm` heuristics) cannot,
because they only consult **revealed** moves, not the prior over likely
movesets given species.

This is THE distinguishing test for whether the AI feels intelligent.
Any rebuild plan that doesn't pass this test fails the First-Playthrough
Promise. Any rebuild plan that does pass it is most of the way there.

## Architecture options surfaced

Ranked by simplicity. All three respect the no-cheat invariant (only public
information: seen species, revealed moves, public learnability tables, plus
public meta-knowledge encoded in ROM as priors).

### Option A — Minimal viable (~2 weeks user-felt, ~3-4 weeks real work)

- Single scoring function with risk-weighted threats
- Algorithmic moveset priors per species (see below)
- Per-mon value table + per-leader personality weights
- Near-tie softmax mix (only source of stochasticity)
- **No Layer B, no CFR, no RL training**

Hits ~85-90% of the First-Playthrough-Promise bar. Lowest risk, fastest to
ship, easiest to maintain. Every heuristic in source cites a section of
POLICY_DESIGN.md.

### Option B — Plus pattern detector (~3 weeks user-felt, ~4-5 weeks real work)

All of Option A, plus a **4-8 byte WRAM struct** that tracks
`(player_action, my_active_class)` pairs over a small window. When the
player has done the same thing twice in a row in a recurring matchup, the
AI gets a small bonus on counter-moves the next time the matchup recurs.

Captures roughly 80% of CFR's experiential value at ~10% of its complexity.
The dumb-pattern detector punishes pattern-following players without any of
the regret-update math, exponential smoothing, or convergence theory.

Hits ~92-95% of the bar. **Recommended option as of 2026-05-05.**

### Option C — Full original plan (~6-8 weeks)

The full Layer A + Layer B (CFR) + v2 RL training plan as captured in
`docs/boss_ai_rebuild_plan.md` and `docs/boss_ai_rl_training_plan.md`.

CFR is intellectually elegant (real-time Nash-equilibrium-seeking) but
probably overkill for a campaign playthrough against a single human. RL
training is a big infra investment to derive priors that playtest tuning
could reach in a fraction of the time.

Hits ~100% of the theoretical bar but pays a high complexity tax for the
last 5-10% of feel. **Probably overengineered** relative to the bar.

## The simpler unified architecture (recommended pitch)

If/when work resumes, the architecture I'd recommend is a refinement of
Option B that drops the "Layer A / Layer B" framing in favor of a single
coherent scoring function:

```
score(action) = E[damage_dealt | action]                          ; what I get
              + strategic_value(action)                            ; tempo, status, setup
              − risk_aversion(my_mon) × P(KO_this_turn | action)   ; preserve my ace
              − E[damage_taken | action]                           ; what I lose
              + pattern_punishment_bonus(action)                   ; counter player repetition
              + leader_personality_bias(action)                    ; Whitney ≠ Clair
```

Expectations are computed against probabilistic moveset priors per species,
refined by revealed moves. Pick the top-scoring action unless multiple are
within ~15% of each other; then softmax-sample among the near-ties.

**Eight components total** — three kept from current platform (state
tracking, anti-cheat audit, trace pipeline), five new:

1. Public-info state tracker (KEEP)
2. Probabilistic moveset prior (NEW — see algorithmic generation below)
3. Risk-weighted scoring function (NEW — the formula above)
4. Per-mon value table (NEW — drives risk aversion; Lance's Dragonite is
   high-value, throwaway leads are low)
5. Near-tie softmax mix (NEW — replaces always-argmax)
6. Pattern detector (NEW — 4-8 bytes WRAM; the dumb CFR replacement)
7. Per-leader personality weights (NEW — small per-leader scoring biases)
8. Anti-cheat audit + trace pipeline (KEEP)

No layers, no CFR, no RL. One scoring function, one source of stochasticity.

## Algorithmic moveset priors (the key engineering decision)

User's strong instinct, validated: **hand-curating 251-species moveset
priors is tedious and bias-prone, and most of the work can be automated.**
This was the rebuild's biggest perceived blocker for the user. The
algorithmic approach removes that blocker entirely.

### Filter

```
For each species, candidate set = legal moves (level-up + TM/HM + egg)
that pass:

  IF damaging move:
    effective_power(move) > 55, where effective_power adjusts for:
      - multi-hit: avg_hits × base_power
        (Pin Missile 14×3=42 OUT; Double Kick 30×2=60 IN)
      - variable: Hidden Power → 70 BP avg; Magnitude → 71 BP avg
      - fixed-damage: Night Shade / Seismic Toss → ~level BP
      - priority moves (Quick Attack 40, Fake Out 40, Mach Punch 40):
        KEEP regardless of power — strategic value is in priority

  IF status move, KEEP if functional category is:
    - self-buff (DD, CM, Curse, Belly Drum, Swords Dance)
    - opponent-debuff (Toxic, Will-O-Wisp, Thunder Wave, Spore, Hypnosis)
    - field setup (Spikes, Reflect, Light Screen, Mist)
    - recovery (Recover, Synthesis, Rest, Moonlight, Morning Sun)
    - phazing (Roar, Whirlwind)
  DROP: Splash, Conversion, Foresight, Sand Attack, Smokescreen, etc.
```

### Probability assignment (also algorithmic)

```
1. Classify species by role from base stats:
   - "special attacker" if SpA > Atk + 15
   - "physical attacker" if Atk > SpA + 15
   - "mixed" otherwise
   - "wall" overlay if HP+Def+SpD > 250
   - "fast" overlay if Spe > 100

2. For each move in candidate set, assign probability bucket:
   - STAB damage move matching role: 95%
   - Non-STAB coverage matching role: 70%
   - STAB damage off-role (e.g. Suicune's Bite): 25%
   - Setup move matching role (DD on physical, CM on special): 60%
   - Recovery move on a wall: 50%
   - Phazing on wall: 30%
   - Priority move on fast attacker: 30%
   - Everything else in candidate set: 15%

3. Optional small override file for the ~5-10% of cases where the meta
   is locked-in tight enough to override role-weighting. Estimated 10-20
   override lines across the whole project.
```

### Implementation sketch

```
scripts/generate_moveset_priors.py        # auto-generator (Python)
data/pokemon/moveset_priors.asm           # generated, ~15-25 entries/species
data/pokemon/moveset_prior_overrides.asm  # optional hand overrides
```

Generator reads `data/moves/moves.asm` (BPs, categories), per-species
learnsets, base stats; runs the filter + role-weighting; writes ROM
tables. `make moveset_priors` regenerates after move/learnset/base-stat
changes. Estimated ROM size ~4 KB total.

User overhead when revisiting: **~10-20 override lines across the project
lifetime, not per-species curation.** This is the unblock.

## User workflow estimate (across the rebuild)

Total user time: **~15-25 hours over ~6 weeks**, mostly conversational.
User makes taste calls; agent writes all code.

| Phase | User time | Activity |
| --- | --- | --- |
| Platform split + interview | 2-4 hrs | Philosophy dump (~500 words) + structured interview (~30-50 questions) |
| Auto prior generator | 1-2 hrs | Spot-check role classifier on ~5 species |
| Scoring + per-leader weights | 3-4 hrs | Per-leader personality calls (18 boss-tier trainers) |
| Pattern detector + near-tie mix | ~30 min | Approve trigger conditions |
| Trace regression check | 1-2 hrs | Judge ~30 AI disagreements |
| Playtest + tune | 5-10 hrs | Play ROM, surface "this fight felt wrong" moments |

User does not write code, asm, or Python at any point.

## What's still undecided when revisiting

1. **Final architecture pick.** Recommendation: Option B (unified scoring
   + algorithmic priors + risk-weighted threats + pattern detector). User
   has not committed.
2. **CFR / Layer B scope.** Probably drop — pattern detector captures most
   of its value cheaper. User may want CFR's theoretical rigor for specific
   high-stakes leaders (Lance, Red); decide on revisit.
3. **v2 RL training scope.** Probably drop — playtest tuning is cheaper.
   The simulator infrastructure has standalone value for future work
   (regression testing, AI vs AI tournament mode); could resurrect for
   that purpose independently of priors-tuning.
4. **Per-leader personality structure.** Taste calls deferred to the
   Step 2 interview. User wants to think about each leader's vibe before
   locking specifics.
5. **Whether even Option A is too much.** User wants to think about this
   — there may be a simpler approach we haven't considered yet.

## Per-leader feel sketch (under recommended architecture)

For grounding when revisiting:

- **Falkner** — low risk-aversion, basic scoring. Aggressive newbie.
  Tutorial energy. Commits to attacks; dies if outpaced.
- **Bugsy** — moderate risk-aversion on Scyther; throws chip mons.
- **Whitney** — high risk-aversion on Miltank, strong commitment to
  Rollout chains, pattern detector earns its keep here. Switch to a
  Rock/Steel wall twice → third time she Stomps you instead.
- **Morty** — Hypnosis ~60-70% prior on Gengar; AI plays around it
  preemptively, switching sleep-vulnerable mons before sleep is shown.
- **Chuck** — low-moderate risk-aversion, focus moves, pattern-punishes
  Flying/Psychic counter-switches.
- **Jasmine** — high risk-aversion on Steelix, defensive patience,
  pattern-punishes setup attempts.
- **Pryce** — moderate risk-aversion, hail/setup-aware.
- **Clair** — moderate-high risk-aversion on Kingdra, high setup-value
  (Dragon Dance), willing to take risks for setup payoff.
- **Lance** — the ace test. Maximum risk-aversion on Dragonite, broad
  moveset prior, preemptive play around hidden threats. Plays scared of
  your Suicune even before Ice Beam is revealed. **The Suicune/Ice Beam
  case is Lance's signature behavior.**
- **Koga** — moderate risk-aversion on Crobat (fast ace), high
  status-spamming weight. Toxic-clock-wins-it.
- **Red (post-game)** — maximum everything. Late-game champion plays
  every turn like it matters.

## Why we shelved (2026-05-05)

User explicitly: *"i think there may be an easier solution. we will
instead focus on getting the damage debugger fully built out and revisit
this when i have time to think."*

This is a "let it breathe" shelf, not a kill. The architecture conversation
surfaced real complexity savings (especially algorithmic priors); user
wants room to consider whether even Option A is more than the project
actually needs.

**Adjacent work the user wants now (not part of the rebuild):** make the
existing 7144-line `engine/battle/ai/boss.asm` more navigable — plan how to
index, organize, simplify, optimize the existing code without rebuilding
the policy layer. That's a separate planning session.

## When you revisit the rebuild

1. Re-read this doc end-to-end first.
2. Decide whether Option A, B, C, or some new fourth option is the path.
3. Re-read `docs/boss_ai_rebuild_plan.md` and
   `docs/boss_ai_rl_training_plan.md` only if Option C is in play;
   otherwise treat them as superseded by the simpler architecture above.
4. If Option B is confirmed, the work is:
   - Update `docs/boss_ai_rebuild_plan.md` to reflect the unified scoring
     architecture (drop Layer A/B framing entirely)
   - Mark `docs/boss_ai_rl_training_plan.md` as deferred-indefinitely
     unless v2 RL specifically resumes
   - Roadmap update: BOSSAI-003 urgency → DO NOW, status notes refreshed
5. Then start Phase 1 (platform split + interview).

## Related docs

- [boss_ai_rebuild_plan.md](boss_ai_rebuild_plan.md) — v1 Layer A + Layer B plan (SHELVED, points here)
- [boss_ai_rl_training_plan.md](boss_ai_rl_training_plan.md) — v2 RL plan (SHELVED, points here)
- [boss_ai_spec.md](boss_ai_spec.md) — older 811-line design doc; still relevant for the platform layer (state tracking, anti-cheat boundaries)
- `audit/boss_ai_trace/*_live.txt` — per-leader live captures (the regression suite for any rebuild)
- `engine/battle/ai/boss.asm` — the 7144-line file under future rebuild
