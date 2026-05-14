# Worked Example: Misty Starmie vs Meganium Recovery Tempo

Purpose: practice recovery-window arbitration. Recover is powerful only when it
preserves a route better than immediate progress; it is not correct just
because the user is low.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster: `data/trainers/parties.asm`, `MistyGroup`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_misty_starmie_vs_meganium_recover_tempo_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_misty_starmie_vs_meganium_recover_tempo_001`
- Mutation:
  `audit/boss_ai_preference/state_transition_mutations.md`,
  `mut_misty_recovery_window_opens_001`
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`

Expert-source framing:

- Smogon's Rain Offense guide treats rain as a finite offensive window that has
  to be converted, not just maintained:
  <https://www.smogon.com/dp/articles/rain_offense>.
- Smogon's battle-conditions guide frames weather as a field condition that
  changes move value and therefore turn value:
  <https://www.smogon.com/resources/beginner/battle_conditions>.
- Smogon's GSC Spikes article uses Starmie as a useful recovery/removal
  example: Recover can extend Starmie's role, but pressure can still deny the
  role if the opponent keeps it from healing freely:
  <https://www.smogon.com/gs/articles/gsc_spikes>.

## Public State

```text
Boss active:
  Starmie Lv63 at 46%, Wise Glasses
  Known moves: Hydro Pump, Recover, Psychic
  Bench: Politoed / Quagsire / Lapras / Lanturn

Player active:
  Meganium Lv62 at 68%
  Revealed moves: Razor Leaf, Reflect
  Public priors: Synthesis plausible, Body Slam plausible

Field:
  Rain active
  Player Reflect active
```

The public benchmark labels Psychic as best, switch to Lapras as acceptable,
and Recover / Hydro Pump as catastrophic in this exact state.

The mutation `mut_misty_recovery_window_opens_001` flips the answer to Recover
when Meganium cannot immediately punish and Psychic no longer changes cleanup
math. That flip is the real lesson: recovery is conditional on a window.

## Damage Anchors

```text
Starmie Psychic -> Meganium at 68%:
  67-79 damage.
  35-42% of Meganium's current HP.
  24-28% of Meganium's max HP.

Meganium Razor Leaf -> Starmie at 46%:
  119-140 damage.
  142-167% of Starmie's current HP.
  Guaranteed KO from the shown current HP.

Meganium Razor Leaf -> Starmie after Recover to about 96%:
  119-140 damage.
  68-80% of Starmie's post-Recover HP.
  Starmie survives, but remains badly damaged and has not changed Meganium's
  route.

Lapras Ice Beam -> Meganium at 37%:
  88-104 damage.
  85-101% of Meganium's current HP.
  Not guaranteed from this exact default-calc state.

Lapras Ice Beam -> Meganium at 31%:
  88-104 damage.
  102-121% of Meganium's current HP.
  Guaranteed from this exact default-calc state.
```

The harvested public card says Psychic chip changes the Lapras cleanup band.
The default damage debugger output supports the broader idea that chip matters,
but it does not prove a guaranteed Lapras cleanup from every post-Psychic HP
state. Exact current HP, stats, and prior chip still matter.

## Route Interpretation

Why Recover is bad here:

- Starmie is low, but Meganium can immediately punish the recovery turn.
- Recover leaves Starmie alive but still under the same damage pressure.
- Recover does not damage Meganium, does not force a switch, and does not
  improve Lapras's cleanup route.
- If Starmie spends the turn healing, Misty may preserve Starmie briefly while
  losing the route that mattered.

Why Psychic is better:

- Psychic turns Starmie's likely final action into route material.
- Even if Starmie faints to Razor Leaf afterward, the turn can move Meganium
  toward Lapras cleanup.
- The move has a named follow-up: Starmie chips, then Lapras or another Misty
  piece tries to convert. It is not generic damage.

Why switch to Lapras is only acceptable:

- Switching preserves Starmie and goes directly to the cleanup piece.
- It may miss the chip that makes Lapras's next turn reliable.
- It rises if Starmie is needed later, if Meganium cannot punish Lapras, or if
  Lapras already cleans from the current HP.

## Decision Recipe

Use recovery when:

```text
the user still has a live job;
the opponent cannot immediately erase the recovered HP;
the recovery turn preserves a blocker or converter;
the recovered piece has a concrete next action after healing.
```

Attack or pivot instead when:

```text
the opponent can keep damaging through the heal;
the recovery turn does not change the route;
the user's best remaining job is to create chip before fainting;
another piece converts only after that chip.
```

## Player-Side Advice

If advising the user with Meganium active:

1. Keep pressure if Starmie lacks a real recovery window.
2. Do not let Recover reset the exchange for free.
3. Track whether Starmie's last attack puts Meganium into Lapras range.
4. If Meganium is asleep, disabled, too low, or unable to punish Recover, the
   answer changes: expect Starmie to heal and rebuild the route.

If advising Misty:

1. Do not click Recover just because Starmie is low.
2. Ask whether Recover exits the damage cycle or merely delays fainting.
3. If the recovery window is closed, cash Starmie for the chip that improves
   Lapras, Lanturn, Quagsire, or Politoed.
4. If the recovery window opens, preserve Starmie because it remains a fast
   recovery attacker in the remaining route map.

## Transfer Lesson

Recovery is a route-preservation move, not a panic button. A low-HP Pokemon
should heal only when the healed HP changes the next route. If the opponent can
remove or re-create the same damage state immediately, the better move may be
to spend the low-HP Pokemon on chip, status, a forced switch, or safe entry.

## Unverified Before Real Turn Advice

- Exact player Meganium stats, current HP, item, PP, and unrevealed moves.
- Whether Meganium has Synthesis and whether rain changes that route in the
  current state.
- Whether Lapras actually cleans after Starmie chip from the exact resulting
  HP range.
- Whether Starmie is needed for a later route more than the immediate chip is
  needed now.
