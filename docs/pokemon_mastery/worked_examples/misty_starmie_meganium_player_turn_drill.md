# Worked Example: Misty Starmie vs Meganium Player-Turn Drill

Purpose: convert `misty_starmie_meganium_recover_tempo.md` from a recovery
theory note into a concrete user-facing move recommendation.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- `misty_starmie_meganium_recover_tempo.md`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_misty_starmie_vs_meganium_recover_tempo_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_misty_starmie_vs_meganium_recover_tempo_001`
- Damage check: `python -m tools.damage_debugger.matchup --self-test`

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

Damage anchors from the source note:

```text
Meganium Razor Leaf -> Starmie at 46%:
  guaranteed KO from shown current HP.

Starmie Psychic -> Meganium at 68%:
  leaves Meganium alive but can push it toward Lapras cleanup range.

Starmie Recover -> about 96%:
  Meganium Razor Leaf still does heavy damage, but Starmie survives.
```

## Live-Turn Advice

Recommendation: Razor Leaf. Confidence: high for this exact public state,
assuming Meganium's Razor Leaf PP and accuracy are normal and Meganium remains
able to act after Starmie's attack.

Plan: remove Starmie before Recover can turn the position into a reset loop,
then re-score Meganium's remaining job against Lapras, Quagsire, and Lanturn.

State read: Starmie is low enough that Razor Leaf is route-ending damage, while
Recover is only good for Misty if Meganium gives it a recovery window. Psychic
chip matters for Misty's next piece, but Meganium survives the public Psychic
range.

Win condition: keep Misty from preserving Starmie as a fast recovery bridge.
The user wins this exchange by making Starmie's final turn either fainting or
at most one chip action before fainting.

Candidate ranking:

1. Razor Leaf: best. It KOs the active Starmie from the shown HP and prevents a
   free Recover loop.
2. Switch to a dedicated Lapras/Lanturn answer: acceptable only if Meganium is
   uniquely required later and the switch-in survives rain-boosted Water and
   coverage pressure.
3. Reflect, Synthesis, or weak chip: bad in this state because they give
   Starmie a chance to Recover, attack again, or hand the route to Lapras with
   less cost.

Opponent's best route: Psychic chip into Lapras or another cleanup piece if
Starmie cannot safely Recover.

Worst plausible branch: Starmie uses Psychic, Meganium KOs it, and Misty brings
in Lapras while Meganium is now near the Ice Beam cleanup band. This is still
better than donating a Recover window, but it requires immediate re-scoring.

Key piece: Meganium may still be a Quagsire or Water-route answer after Starmie
falls. Do not assume it is expendable just because it won this turn.

What changes the answer:

- Meganium is actually lower than the public HP.
- Razor Leaf PP, accuracy, or disable state is not available.
- Starmie has revealed Ice Beam or another move that changes survival.
- Lapras already cleans Meganium from current HP even without Psychic chip.
- Another player piece handles Lapras/Quagsire better, making a switch safer.

Next turn if it works:

- If Starmie faints and Lapras enters, check rain turns and Ice Beam range
  before deciding whether Meganium attacks, switches, or is preserved.
- If Starmie somehow survives or switches, rebuild around the new active rather
  than following the KO script.

## Scorecard

```text
mechanics and public-state accuracy: 4/4
route and win-condition clarity: 4/4
candidate ranking with resource gain and cost: 4/4
worst plausible branch identified: 3/3
preservation or expendability reasoning: 2/2
answer-changing information: 2/2
concise recommendation grounded in the state: 1/1
total: 20/20 for the abstract drill
```

Caps that would apply in a real battle:

- If Meganium's actual HP, moves, PP, item, or stats differ from the public
  card, the score is provisional.
- If the local damage self-test is stale or does not match the current ROM, the
  damage-dependent recommendation must be rechecked.
- If the user has a better Lapras/Quagsire map than this public state shows,
  the move remains likely correct but the next-turn preservation plan changes.

## Lesson Extracted

When the opponent's recovery user lacks a real recovery window, take the
route-ending hit. The reason is not "Grass hits Water"; the reason is that the
hit denies Recover, removes the fast bridge, and leaves the next route visible
enough to re-score.
