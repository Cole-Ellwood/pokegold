# Worked Example: Janine Qwilfish Spikes Arbitration

Purpose: practice the romhack hazard fork as a move-choice problem, not as the
slogan "set Spikes." The same Qwilfish position can ask for Spikes, Explosion,
or a live attack depending on public layer count, public Rapid Spin, and whether
the stack has already converted.

Local evidence:

- Public cards:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
  (`romhack_spikes_third_layer_janine_001`,
  `romhack_spikes_public_spinner_holdout_001`,
  `romhack_spikes_fourth_click_janine_001`,
  `romhack_spikes_maxed_explosion_conversion_holdout_001`).
- Hidden oracles:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`.
- Fixture source:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
  (`janine_qwilfish_finish_third_spikes_layer`,
  `janine_qwilfish_spikes_already_maxed`).
- Romhack source: `engine/battle/move_effects/spikes.asm`,
  `engine/battle/move_effects/rapid_spin.asm`,
  `engine/battle/core.asm`, and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Expert transfer: Smogon's GSC Spikes guide treats Spikes as a route tool that
  needs retention, spinner pressure, or conversion support, not as a move to
  click independently of the whole position.

## Local Mechanics Facts

The romhack is not vanilla GSC here:

- Spikes can reach three layers.
- Switch-in damage is max HP / 8, max HP / 6, then max HP / 4.
- Flying-type Pokemon ignore the damage check.
- Rapid Spin clears all layers.
- A fourth Spikes click fails when three layers are already on the target side.

These are mechanics-profile facts, not generic Pokemon memory.

## Boundary 1: Two Layers, No Public Spinner

Public state:

```text
Janine Qwilfish Lv60 at 82%, Leftovers
  Spikes / Sludge Bomb / Surf / Explosion

Player Snorlax Lv60 at 76%
  Body Slam / Rest revealed

Player side:
  two Spikes layers
  six grounded Pokemon seen
  no Rapid Spin user revealed
```

Move label:

- Best in this card: Spikes, if the posterior chance of a live effective
  spinner is low enough.
- Acceptable: Explosion only if it opens a clearer forced route than the third
  layer.
- Catastrophic: switching Qwilfish out without a better reason.

Why:

- The third layer changes all future grounded entries from max HP / 6 to max HP
  / 4.
- The public opponent has no revealed cheap removal route. That is evidence,
  not proof; an unrevealed Rapid Spin set must still be priced.
- Snorlax's public actions do not immediately stop Qwilfish from placing the
  layer.
- Sludge Bomb is meaningful damage but does not change the hazard economy.

Damage grounding:

- Qwilfish Sludge Bomb into Snorlax at 76%: 134-158 damage, 58-68% of current
  HP. It does not guarantee the KO.
- Qwilfish Explosion into full Snorlax: 243-286 damage, 79-93% of max HP. It is
  not a full-HP KO and spends Qwilfish before the third layer is placed.

Route answer:

```text
Use Spikes now when the estimated chance of a live effective spinner is below
the threshold where a completed three-layer stack beats the best direct move.
The open turn completes the hazard stack and makes every future grounded pivot,
Rest loop, and forced switch much harder. Do not cash Qwilfish out while its
unique current job is still live unless the spin posterior or a separate route
trade makes the layer too likely to disappear before conversion.
```

Hidden-spinner posterior:

```text
p = P(live effective spinner | no Rapid Spin revealed yet)

P(spinner | no reveal) =
  P(no reveal | spinner) * P(spinner)
  / (
      P(no reveal | spinner) * P(spinner)
    + P(no reveal | no spinner) * P(no spinner)
    )
```

The important term is `P(no reveal | spinner)`.

- If a legal spinner had several safe, high-value spin turns and did not spin,
  the posterior drops.
- If no clean spin opportunity has existed, no reveal barely changes the
  posterior.
- If the active side has no Ghost, trap, faster KO, status, or Explosion line
  that prevents or punishes Spin, the cost of being wrong is much higher in
  this romhack because Rapid Spin clears all three layers.

EV threshold:

```text
Set the third layer when:

  (1 - p) * value_if_stack_sticks
+ p       * value_if_spinner_exists
> value_of_best_direct_alternative

Equivalent threshold:

  p < (A - C) / (A - B)

A = value if the third layer sticks long enough to convert
B = value if an effective spinner exists and can erase the stack
C = value of the best non-Spikes move now
```

This example still labels Spikes as best because the public card presents a
high-value 2 -> 3 layer turn against a grounded, non-threatening active with no
revealed removal. The lesson is not "ignore hidden Spin." The lesson is "finish
the stack only when the hidden-Spin posterior is low enough or the spin reveal
is punishable enough that the EV stays positive."

Answer-changing information:

- A Rapid Spin user is revealed and can enter cheaply.
- A legal Rapid Spin species has not yet had a meaningful chance to reveal the
  move, so the no-reveal evidence is weak.
- The player team is mostly Flying-type.
- Snorlax has an immediate KO on Qwilfish.
- Explosion removes the only piece blocking Janine's next route.

## Boundary 2: Two Layers, Public Spinner Active

Public state:

```text
Janine Qwilfish Lv60 at 82%
  Spikes / Sludge Bomb / Surf / Explosion

Player Starmie Lv60 at 55%
  Rapid Spin / Recover / Surf revealed

Player side:
  two Spikes layers
  Rapid Spin is public and active
```

Move label:

- Best by oracle: Explosion.
- Acceptable: Sludge Bomb.
- Catastrophic: Spikes.

Why:

- The third layer is likely removed before it converts if Starmie can spin
  cheaply.
- Sludge Bomb pressures Starmie but does not stop Rapid Spin or Recover by
  itself.
- Explosion is not guaranteed to KO this exact Starmie from 55%, but it is the
  only listed move that can immediately contest the public hazard-control route.

Damage grounding:

- Qwilfish Sludge Bomb into Starmie at 55%: 57-67 damage, 49-58% of current HP.
  It is not a guaranteed KO.
- Qwilfish Explosion into Starmie at 55%: 102-120 damage, 88-103% of current HP.
  It is a KO roll, not a guaranteed removal.

Route answer:

```text
Do not finish the stack into a public active spinner unless the spin turn is
punished. The hazard route now depends on removing, forcing, or severely
damaging Starmie more than on placing the third layer.
```

Answer-changing information:

- Rapid Spin was not actually revealed.
- Starmie is already in guaranteed live-attack range.
- Qwilfish is needed later for a more important Explosion target.
- The opponent has another hazard remover, making this trade less final.

## Boundary 3: Three Layers Already Up

Public state:

```text
Janine Qwilfish Lv60 at 74% or 42%
  Spikes / Sludge Bomb / Surf / Explosion

Player Snorlax Lv60 at 58% or 62%
  Body Slam / Rest revealed

Player side:
  three Spikes layers
```

Move label:

- Best in the seed card: Sludge Bomb.
- Best in the holdout when Qwilfish is at 42% and Snorlax is the Rest-cycle
  anchor: Explosion.
- Catastrophic: Spikes.

Why:

- The fourth Spikes click fails in source.
- Once the stack is complete, the question changes from "can we add a layer?"
  to "how do we convert the completed stack?"
- Live damage is fine when Qwilfish still has future work.
- Explosion rises when Qwilfish's future role is lower than removing the
  opponent's hazard absorber or Rest-cycle anchor.

Damage grounding:

- Qwilfish Sludge Bomb into Snorlax at 58%: 134-158 damage, 75-89% of current
  HP. It does not guarantee the KO.
- Qwilfish Explosion into Snorlax at 58%: 243-286 damage, 137-161% of current
  HP. It is a guaranteed KO if the move executes and is not blocked.

Route answer:

```text
At 3/3 layers, stop valuing Qwilfish as a setter. Use a live conversion move:
Sludge Bomb when preserving Qwilfish still matters, Explosion when removing the
Rest-cycle anchor matters more than Qwilfish's remaining role.
```

Answer-changing information:

- The layer count was wrong and only two layers are up.
- The local source changes to allow a fourth layer.
- Explosion is blocked or Qwilfish is removed before acting.
- Qwilfish is still needed as the only answer to a later route.

## Reusable Recipe

When deciding on Spikes in this romhack, ask these in order:

1. What is the public layer count under the romhack mechanics profile?
2. Is the next layer legal and does it change a route?
3. Can a public Rapid Spin user remove the stack before it converts?
4. Is the setter's current role still "add layer," or has it changed to
   "convert," "remove spinner," "preserve," or "trade"?
5. What opponent piece turns the hazard stack into no progress if it stays?

Failure signs:

- Treating 2/3 and 3/3 layers as the same position.
- Completing a stack into a public free Rapid Spin turn.
- Exploding before the setter's live hazard job is finished.
- Continuing to click Spikes after the stack is already complete.
