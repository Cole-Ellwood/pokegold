# Worked Example: Pryce Slowking Ampharos Preservation

Purpose: practice defensive-answer preservation from public state. Slowking has
useful moves, but the current Ampharos route pressures it immediately. The
question is whether Pryce should spend Slowking's HP on status or move through
the available Piloswine pivot first.

Local evidence:

- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
  (`romhack_defensive_answer_preservation_pryce_001`).
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`.
- Boundary mutation:
  `romhack_defensive_answer_unavailable_holdout_001`.
- Fixture source:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
  (`pryce_slowking_vs_ampharos_ground_pivot`).
- Romhack type and passive evidence:
  `data/types/type_matchups.asm`,
  `engine/battle/type_passive_damage_mods.asm`,
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`, and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert transfer: Smogon checks/counters and pivot concepts are useful only
  after they are reduced to current-entry durability, not species slogans.

## Public State

```text
Pryce Slowking Lv33 at 68%, Leftovers
  Surf / Psychic / Thunder Wave revealed
  current role: bulky support

Pryce bench:
  Dewgong at 41%
  Sneasel at 100%
  Piloswine at 63%

Player Ampharos Lv34 at 80%
  ThunderPunch / Thunder Wave revealed
  likely Dragon coverage

Field:
  no weather
  no screens
```

Public speed evidence from the damage-debugger profile:

- Slowking speed: 30.
- Piloswine speed: 44.
- Ampharos speed: 68.

Switching must therefore be valued as a state transition, not as "Piloswine
outspeeds next turn." The switch matters because Piloswine survives the public
hit much better and changes Ampharos's next risk.

## Candidate Labels

- Best: switch to Piloswine.
- Acceptable: Thunder Wave, only if Slowking survives and slowing Ampharos is
  more valuable than preserving Slowking.
- Catastrophic: Rest.

## Why Switching Is Best

Slowking does not have time to behave like a generic bulky utility Pokemon in
this exact state:

- Ampharos ThunderPunch into Slowking at 68%: 75-89 damage, 101-120% of current
  HP. This is a guaranteed KO from the public state.
- Slowking Surf into Ampharos at 80%: 11-14 damage, 9-12% of current HP. It does
  not change the active route.

Piloswine is not a magic answer from memory; it is the public piece whose final
damage profile and threat back make the transition work:

- Ampharos ThunderPunch into Piloswine at 63%: 22-26 damage, 24-29% of current
  HP.
- Piloswine Earthquake with Soft Sand into Ampharos at 80%: 88-104 damage,
  76-90% of current HP.

The switch preserves Slowking for later defensive work and puts Ampharos in a
position where staying in is costly. That is stronger than asking Slowking to
use status into a hit it cannot survive.

## Why Thunder Wave Is Only A Fallback

Thunder Wave is useful only if it happens before Slowking loses its role, or if
the team has no better pivot. In the seed card, Piloswine is available and
healthy enough to take the public hit. Status is therefore a downgrade from a
clean preservation transition.

In the holdout mutation, Piloswine is gone. The answer flips:

```text
No Piloswine on the public bench -> Thunder Wave becomes the best live
mitigation move, Surf is acceptable chip, and choosing switch:Piloswine is a
state-tracking failure.
```

This is the important arbitration lesson: "preserve the answer" is not a legal
move if the answer is unavailable.

## Why Rest Fails

Rest is not preservation when the opponent keeps the route and moves first. If
Slowking Rests or clicks weak chip while Ampharos continues attacking, Pryce
loses the Slowking role and still has not changed Ampharos's pressure.

Route answer:

```text
Switch to Piloswine. It preserves Slowking, absorbs the public hit far better,
and creates a next-turn Earthquake threat. Re-score after Ampharos's response;
do not assume Piloswine is a permanent answer if new coverage or chip changes
the damage profile.
```

## Answer-Changing Information

The answer can flip if:

- Piloswine is unavailable, too low, statused, or needed for a more important
  route.
- Ampharos reveals coverage that removes Piloswine on entry.
- Slowking has a guaranteed KO or a confirmed status line before Ampharos can
  remove it.
- Ampharos is already statused or otherwise unable to continue immediate
  pressure.
- Local type/passive/damage evidence contradicts the public card.

## Reusable Recipe

Before using a bulky Pokemon's utility move under pressure, ask:

1. Does the active hit remove or cripple the bulky Pokemon before utility
   matters?
2. Is there a bench piece whose current damage profile handles the public hit
   better?
3. Does that pivot also threaten progress, or does it merely delay?
4. Is the pivot actually available in public state?
5. If the pivot is gone, what live mitigation move remains?
6. After the pivot, what new information would make the answer invalid?

Failure signs:

- Clicking Rest because "bulky Pokemon heal" without checking turn order and
  damage.
- Clicking status because it is useful in general while losing the piece that
  needed to be preserved.
- Choosing a switch target that is not actually on the public bench.
- Treating a type identity as proof instead of checking final damage and the
  next route.
