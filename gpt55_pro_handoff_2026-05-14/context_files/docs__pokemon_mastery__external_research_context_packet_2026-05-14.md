# External Research Context Packet - 2026-05-14

Status: upload this alongside
`external_research_prompts_2026-05-14.md` when using GPT-5.5 Pro or Deep
Research.

Purpose: give the external model enough project context to avoid generic
Pokemon advice, later-generation Team Preview assumptions, or unfair boss-AI
proposals.

## Project

We are improving practical battle advice and boss AI for a Pokemon Gold romhack
called Gym Leader Lab. The game is Gen 2 based, but it has local mechanics
changes. Treat vanilla GSC as source material, not as guaranteed romhack truth.

The long-term advisor goal is:

```text
Become a strategically competent high-level Pokemon singles advisor, roughly
equivalent to a solid 1500-ELO player, able to help win long-form battles by
planning from turn 1, updating plans as the board changes, and choosing moves
that preserve or improve realistic win routes.
```

The boss AI goal is:

```text
Absurdly strong but non-cheating boss trainers. They should win by legal
inference, public board reading, risk management, route pressure, and good
resource trades, not hidden player-team reads.
```

## Information Model

There is no public Team Preview in vanilla GSC or this romhack.

Use different knowledge rules depending on who is being advised:

- Player-side boss advice may use source-visible boss roster data, fixed or
  source-supported boss opener policy, and local mechanics docs before turn 1.
- Boss AI must not use the player's unrevealed team, hidden moves, held items,
  hidden PP, hidden reserve HP, private stats, or current-turn input.
- Boss AI may use public battle state, public active species/level, visible
  HP/status/boosts, revealed player moves, observed switches, seen player
  species, public faint/send-out events, and legal public learnset priors.
- Vanilla GSC replay review starts from the actual public lead state and revealed
  information over time, not from future knowledge or Team Preview.
- Later-generation Team Preview sources are analogy material only. Transfer the
  habit of route triage from known information; do not transfer the mechanic.

## Haki Exception

The ROM has a designed unfair exception called Haki/oracle. It is quarantined
and should not be generalized.

Haki rules:

- One activation per battle.
- Only named late/major bosses.
- Only on the ace's first active turn.
- Reads the already-locked player action in a post-input window.
- Must be traceable.
- Must not leak into ordinary boss policy.

Any external boss AI proposal that reads current-turn input outside this
quarantined Haki shape should be rejected.

## Existing Boss AI Capabilities

Assume the current boss AI already has these broad capabilities:

- Move scoring with KO pressure, deny-KO pressure, tempo, setup windows, status
  value, role bias, and risk.
- Public plausible-threat masks from active species, level, STAB, revealed
  damaging move types, legal learnability, and Hidden Power risk.
- A distinction between higher-confidence likely threats and possible-only
  threats.
- Seen player species tracking and visible faint/send-out tracking.
- Revealed player move tracking by active species.
- Public switch prediction from observed switching and active matchup pressure.
- Switch-loop controls.
- Public Perish Song escape.
- Public revealed-move policies for Protect/Detect, recovery, Encore, Destiny
  Bond, Counter/Mirror Coat, Haze/phazing, Explosion/Selfdestruct, and obvious
  utility fail gates.
- Layer-aware Spikes policy for the romhack's three-layer Spikes.
- A documented exact-speed exception for setup-speed headroom only. Do not
  generalize exact private stat helpers.

Useful proposal shape:

- score bias;
- small public gate;
- small counter;
- existing bitmask reuse;
- trace-only audit;
- compact table;
- low-memory state machine.

Bad proposal shape:

- broad game-tree search;
- hidden team read;
- exact hidden move/item/PP/stat read;
- current-turn input read;
- modern Team Preview import;
- untraceable "smartness";
- large memory use.

## Romhack Mechanics Known To Matter

These are supplied local facts. They still need runtime verification when a
simulation claim depends on exact timing or text.

Spikes and Rapid Spin:

- Spikes has three layers.
- Layer damage on grounded switch-in is 1/8, 1/6, then 1/4 max HP.
- A fourth Spikes click at three layers fails.
- Rapid Spin clears all Spikes layers.
- Flying-type Pokemon ignore Spikes.
- There is no Levitate-style ability check.
- Hazard advice must price Rapid Spin and spinblocking. A three-layer stack is
  not automatically secure if the opponent has a live spinner and the current
  side cannot block or punish it.

Vanilla GSC baseline:

- Vanilla GSC has one Spikes layer at 1/8 max HP.
- Rapid Spin is the main removal method.
- Ghost-types can block Rapid Spin because Rapid Spin is Normal-type and fails
  to affect them.
- Common GSC spinblockers are Gengar and Misdreavus; lower-power contexts can
  include Haunter/Gastly.

Local mechanics firewall:

- Type/passive changes exist. Type-effectiveness, immunity, resistance, and
  passive claims must be verified locally before being treated as romhack fact.
- Damage, speed, status, Rest/Sleep Talk, phazing, Encore, Disable, Destiny
  Bond, Counter/Mirror Coat, Explosion, item behavior, and PP/timing can flip
  move advice.
- External answers should label each mechanics claim as vanilla GSC,
  locally supplied, runtime verified, contradicted, or unknown.

## Current Measurement State

The project has a measurement mini-goal, but it does not yet prove mastery.

Current baseline:

- State-transition benchmark proxy: 43 / 43 evaluated positions passed.
- Pairwise holdout proxy: 83.3%.
- Trajectory holdout proxy: 100.0%.
- Preference final readiness: not ready for ROM scoring review.
- No filled real boss-attempt review yet.
- No countable non-self 50-battle run yet.
- Boss-sim readiness audit says aggregate win rate is not countable yet.

The later validation gate is:

```text
Win at least 40 of 50 recorded boss battles against the romhack AI or another
non-self opponent model, using one declared player team and ruleset, with
pre-battle route plans, turn logs, loss review, and no known mechanics mismatch
in the route that decided the result.
```

This gate is not ready. Missing blockers include:

- declared player team and ruleset;
- non-self boss run;
- fuller Spikes/Rapid Spin runtime fixtures;
- more type/passive fixture coverage;
- boss opening policy runtime traces;
- first filled manual boss-attempt review.

External work should help produce better turn judgment, better measurement
materials, or cheap public-info AI proposals. It should not claim the 50-battle
gate is already meaningful.

## What Good Output Looks Like

Good strategy output:

- Gives public-state turn decisions, not broad advice.
- Names the route, irreplaceable piece, worst plausible branch, and next-turn
  implication.
- Separates vanilla GSC mechanics from romhack assumptions.
- Converts source lessons into policies:

```text
When [trigger], prefer [policy], unless [exception].
```

Good boss AI output:

- Uses only public or observed information.
- Says exactly what state is read.
- Estimates memory/code cost.
- Has a trace or audit hook.
- States the failure mode.
- Includes a reason to reject the proposal if local source inspection does not
  support it.

## Common Mistakes To Avoid

- Assuming Team Preview.
- Assuming the boss AI knows the player's full team.
- Treating absence of a revealed move as proof the move does not exist without
  pricing whether there has been a good reveal/use opportunity.
- Treating Spikes as automatic progress when Rapid Spin can erase the stack.
- Using vanilla one-layer Spikes math for the romhack.
- Importing Defog, Stealth Rock, abilities, modern items, modern Hidden Power
  assumptions, or Terastallization logic.
- Explaining that hazards/sleep/status/Explosion are "good" without a route
  trigger and exception.
- Proposing exact damage or exact speed helpers for boss decisions unless the
  exact value is public or already explicitly approved.
- Producing a sealed exam and then exposing the answer key before testing.

## Preferred External Source Areas

Use high-quality sources where possible:

- GSC OU tournament replays and Smogtours logs.
- Smogon G/S resources and GSC-specific articles.
- GSC analyses by role, not just by species.
- High-level old-gen forum posts where the reasoning is explicit.
- Pokemon Showdown source only for simulator mechanics or replay format, not as
  proof of this romhack's custom mechanics.

Good strategic topics:

- no-preview lead value;
- hidden coverage and Bayesian priors;
- Spikes, Rapid Spin, spinblocking, and hazard retention;
- sleep/status target discipline;
- Rest and Sleep Talk cycles;
- Explosion and sacrifice route trades;
- phazing and setup denial;
- PP and endgame conversion;
- preserving or spending irreplaceable defensive answers;
- plan revision after miss, crit, wake, reveal, switch, or unexpected damage.

## Deliverables Should Avoid Contamination

Do not ask the external model to solve current local benchmark IDs or answer
known Gym Leader Lab holdout cards.

For training material, it is okay to include public prompt plus sealed hidden
state if the public prompt is usable separately and hidden facts are clearly
segregated.

For evaluation material, public prompts and answer keys should be returned in
separate sections or separate files so the studying assistant can answer before
seeing the key.
