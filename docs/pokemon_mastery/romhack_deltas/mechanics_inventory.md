# Romhack Mechanics Inventory For AI Work

Status: active front-door reference.
Last audited: 2026-05-17.

Purpose: keep Pokemon mastery and boss-AI work grounded in this romhack's
actual mechanics instead of vanilla GSC, modern Pokemon, or stale change logs.
Use this before changing AI policy, labeling boss decisions, or importing a GSC
lesson into the romhack.

## Verification Snapshot

Commands run on 2026-05-17:

```powershell
python scripts/generate_hack_mechanics_reference.py --check
python tools/audit/check_mechanics_docs_and_fixtures.py
python scripts/generate_balance_audit.py --stdout
```

Results:

- `hack_mechanics_reference.md` is regenerated from current source.
- Mechanics docs and Boss AI fixture notes passed the stale-phrase/source
  alignment audit.
- `docs/generated/balance_audit.md` matches regenerated balance-audit data
  after normalizing the generated timestamp.

## Source-Of-Truth Order

Use this order when sources disagree:

1. Local assembly/data source.
2. Generated source-derived references:
   - `docs/agent_navigation/hack_mechanics_reference.md`
   - `docs/generated/balance_audit.md`
3. Focused romhack delta docs:
   - `docs/mechanics_changes_from_base.md`
   - `docs/agent_navigation/gen2_vs_modern_mechanics.md`
   - `docs/pokemon_mastery/romhack_deltas/*.md`
4. Historical manifest/change logs:
   - `docs/manifest.md`
   - `docs/CHANGES.txt`
   - `docs/CHANGES_BY_CATEGORY.txt`

The historical manifest and generated `CHANGES*` files are useful history, not
exact current truth. Do not use them as the final authority for current stats,
types, moves, or learnsets.

## What Is New Or Different

### Type Chart And Categories

- The hack still uses the Gen 2 type-based physical/special split.
- Dark remains special; Ghost, Poison, Bug, Rock, Ground, Steel, Flying,
  Fighting, and Normal remain physical.
- Outrage has a Dragon-only exception: Dragon users make Outrage physical when
  current Attack is greater than current Special Attack.
- The local type chart has deliberate edits. Important traps include:
  - Dark hits Steel neutrally.
  - Ghost does no damage to Steel.
  - Poison hits Normal super-effectively.
  - Psychic is neutral into Poison.
  - Grass is neutral into Flying.
  - Ground is neutral into Fire and no-effect into Ghost.
- Exact table: `docs/agent_navigation/hack_mechanics_reference.md`.
- Source: `data/types/type_matchups.asm`,
  `constants/type_constants.asm`, and
  `engine/battle/type_passive_damage_mods.asm`.

### Type Passives

- Type passives change damage, status, recoil, accuracy, speed, and recovery
  assumptions.
- Major route-affecting examples:
  - Dragon's Majesty converts Dragon-attacker immunity results to resistance.
  - Imperial Scales reduces non-super-effective hits into Dragon defenders.
  - Fighting reduces paralysis and burn penalties.
  - Dark can consume a one-time status shield.
  - Psychic can occasionally nullify damage.
  - Poison can retaliate with poison on contact.
  - Steel can reduce or erase recoil.
  - Grass regrowth heals between turns.
- Source: `engine/battle/type_passive_damage_mods.asm`.
- Strategy notes: `romhack_deltas/type_passive_route_impacts.md` and
  `romhack_deltas/type_passive_fixture_priorities.md`.

### Spikes And Rapid Spin

- Spikes has 3 layers, encoded by `SCREENS_SPIKES` and `SCREENS_SPIKES_2`.
- Damage on grounded switch-in:
  - 1 layer: `maxHP/8`
  - 2 layers: `maxHP/6`
  - 3 layers: `maxHP/4`
- Spikes fails only when the target side is already at 3 layers.
- Rapid Spin clears all layers.
- Flying types are unaffected; there is no Levitate-style ability check.
- Boss AI has layer-aware Spikes scoring.
- Source: `engine/battle/move_effects/spikes.asm`,
  `engine/battle/move_effects/rapid_spin.asm`,
  `engine/battle/core.asm`, `engine/battle/ai/redundant.asm`,
  `engine/battle/ai/scoring.asm`, and
  `engine/battle/ai/boss_policy_move.asm`.
- Focused doc: `romhack_deltas/spikes_and_rapid_spin.md`.

### Late-Gen Held Items

The hack adds or activates late-gen style held items that can change AI move
ranking and switch safety:

- Life Orb
- Choice Band
- Choice Specs
- Choice Scarf
- Assault Vest
- Expert Belt
- Muscle Band
- Wise Glasses
- Eviolite / EVOLITE
- Air Balloon
- Shell Bell
- Rocky Helmet
- Metronome item

Exact behavior and constants are in
`docs/agent_navigation/hack_mechanics_reference.md`. Source files:
`constants/item_constants.asm`, `data/items/attributes.asm`, and
`engine/battle/late_gen_held_items.asm`.

### Contact System

- Moves have Gen 6 style contact flags.
- Contact matters for Rocky Helmet, Poison retaliation, and held flinch checks.
- Source: `data/moves/contact_flags.asm` and
  `engine/battle/type_passive_damage_mods.asm`.

### Move Data

- Exact current move power, type, category, accuracy, PP, effect, effect
  chance, and contact status are generated in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Historical tracked move edits include stronger Solarbeam, Giga Drain,
  Fire Blast, Cross Chop, and many base move parameter changes, but do not rely
  on the historical manifest as the final current-value source.
- Source: `data/moves/moves.asm`, `data/moves/effects.asm`,
  `data/moves/effects_priorities.asm`, and `data/moves/contact_flags.asm`.

### Pokemon Stats, Types, TMs, And Learnsets

- Exact current species stats/types/items/TM learnsets are generated in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- `docs/generated/balance_audit.md` compares current source to the baseline ref
  and flags balance-review risks. It is the best existing source-derived
  "what changed" audit for stats/evolutions/learnset coverage.
- `docs/manifest.md` and `docs/CHANGES_BY_CATEGORY.txt` are historical data
  logs and are not enough for current exact AI assumptions.
- Source: `data/pokemon/base_stats/*.asm`,
  `data/pokemon/evos_attacks.asm`, `data/moves/tmhm_moves.asm`, and trainer
  data under `data/trainers/`.

### Other Battle-System Deltas

- Ditto has Imposter-style auto-Transform on switch-in.
- Trainer battle menu and item access rules differ from vanilla.
- Gym TM rewards, Move Reminder behavior, former HM/TM access, and branching
  evolution behavior are documented in `docs/mechanics_changes_from_base.md`.

## AI Assumption Firewall

Before coding or labeling any mechanics-sensitive AI case, write down the local
status for each relevant mechanic:

- Type matchup and category.
- Move data, accuracy, PP, contact, priority, and effect.
- Current species stats, type, item, learnset, and trainer set.
- Hazard layer count and whether Spin can clear it.
- Type passive, held item, or contact interaction.
- Timing-sensitive mechanic such as sleep/wake, Explosion, phazing, Counter,
  Mirror Coat, or Rapid Spin.

If the needed mechanic is not source-verified or runtime-verified, cap the
claim and add or run a fixture before turning it into AI policy.

## Known Remaining Unknowns

Use `romhack_deltas/mechanics_pending_index.md` for the live status table.
As of this audit, several mechanics remain decision-relevant but not fully
runtime-verified in the Pokemon mastery notes, including sleep/wake timing,
Sleep Talk/Rest details, Explosion timing and Ghost interactions, phazing
failure cases, Focus Band/Quick Claw behavior, and Counter/Mirror Coat details.
