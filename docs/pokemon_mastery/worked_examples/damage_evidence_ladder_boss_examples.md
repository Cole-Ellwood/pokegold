# Worked Example: Damage Evidence Ladder

Purpose: keep damage advice from collapsing into type slogans. Each example
separates chart evidence, romhack passive evidence, final damage, and strategic
move labels.

## Example 1: Koga Crobat vs Alakazam

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_koga_crobat_vs_alakazam_immediate_ko_001`

Mechanics profile: `romhack_gym_leader_lab`

Public state:

- Koga Crobat is active at 57%, holding Sharp Beak.
- Player Alakazam is active at 51%, with Psychic and Recover revealed.
- Public fixture range: Crobat Wing Attack into Alakazam deals 54-64%.
- Public fixture range: Alakazam Psychic into Crobat deals 53-62%.

Evidence ladder:

```text
type_chart_label:
  Not needed for the recommendation. Do not say "super effective" unless the
  romhack chart evidence is attached.

passive_adjusted_result:
  Not claimed. No passive-specific type conclusion is needed.

final_damage_range:
  Public fixture says Wing Attack is a guaranteed KO from 51%.

strategic_label:
  Wing Attack is best because it removes Alakazam before Recover or Psychic can
  change the route. Toxic and Confuse Ray are catastrophic because they leave
  the recover/retaliate branch alive.
```

Live advice:

- Use Wing Attack.

Answer-changing information:

- If the public range is stale or wrong, this becomes a preservation question:
  Crobat may die to Psychic, and Umbreon or another Alakazam answer must be
  re-scored.
- If Crobat is slower, the KO threshold is not enough by itself because
  Alakazam may move first.
- If Alakazam cannot Recover or cannot hit Crobat meaningfully, slow pressure
  may regain value.

Reusable lesson:

- A public damage range can justify immediate conversion without a type word.
  The route fact is "guaranteed KO before recovery," not "Flying is good into
  Psychic."

## Example 2: Steel/Ghost/Dark Claims In The Romhack

Mechanics profile: `romhack_gym_leader_lab`

Local evidence anchors:

- Type chart: `data/types/type_matchups.asm`
- Mechanics overview: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Type passives: `engine/battle/type_passive_damage_mods.asm`

Known local chart facts:

- Dark into Steel is neutral in this romhack.
- Ghost into Steel has no effect in this romhack.
- These are romhack facts, not vanilla GSC facts.

Evidence ladder:

```text
type_chart_label:
  Allowed only after binding to romhack_gym_leader_lab and checking the local
  chart or the mechanics overview.

passive_adjusted_result:
  Still separate. A chart result does not prove what a passive, item, status,
  or field modifier does to final damage.

final_damage_range:
  Not known from the chart. Use a local calc, source-derived range, fixture, or
  debugger/emulator observation before making KO or survival claims.

strategic_label:
  Do not call a Dark move best into Steel merely because it is neutral. Best
  requires a route fact: KO, forced heal, setup denial, safe entry, or removal
  of an irreplaceable blocker.
```

Failure pattern:

- "Ghost is resisted by Steel" is not safe romhack advice. In this hack the
  relevant chart fact is no effect, and the strategic implication still depends
  on the exact move, target, passives, and battle state.

## Example 3: Hazard Chip As Damage Evidence

Mechanics profile: depends on the position.

Evidence ladder:

```text
type_chart_label:
  Not an attack chart claim.

passive_adjusted_result:
  Check groundedness, Flying status, and any passive that changes hazard
  interaction.

final_damage_range:
  Vanilla GSC and the romhack differ. Use the mechanics profile before saying
  how much a switch costs.

strategic_label:
  Hazard damage matters when it changes a route: turns a 3HKO into a 2HKO,
  forces Rest, makes phazing progress real, denies repeated pivots, or puts a
  boss ace into revenge range.
```

Reusable lesson:

- Hazard chip is not "free progress" by itself. It becomes evidence only when
  tied to a concrete threshold or clock.
