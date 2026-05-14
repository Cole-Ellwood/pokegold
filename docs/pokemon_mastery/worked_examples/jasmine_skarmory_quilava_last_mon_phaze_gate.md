# Worked Example: Jasmine Skarmory vs Quilava Last-Mon Phaze Gate

Purpose: convert the phazing target-pool rule into exact player-side advice.
The lesson is that Whirlwind text stops mattering when the player has no
living bench target; the live question becomes damage, contact recoil, status,
and next-turn conversion.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- Jasmine roster: `data/trainers/parties.asm`, `JASMINE`.
- Local move data: `data/moves/moves.asm`.
- Contact flags: `data/moves/contact_flags.asm`.
- Rocky Helmet behavior: `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Force-switch behavior: `engine/battle/effect_commands.asm`,
  `engine/battle/ai/switch.asm`.
- Policy source: `worked_examples/smogtours_904815_last_mon_phazing_fail.md`.

## Public State

```text
Boss active:
  Skarmory Lv33 at 100%, Rocky Helmet
  Moves: Spikes / Steel Wing / Toxic / Whirlwind
  Jasmine remaining material: Skarmory only

Player active:
  Quilava Lv34 at 73% HP, no status
  Revealed moves: Flame Wheel / ThunderPunch / Quick Attack / Smokescreen
  Possible move if actually learned: Fire Blast
  Player remaining material: Quilava only

Field:
  No weather or screens
  Spikes may be up, but there is no player bench target to drag
```

## Local Evidence

Damage-debugger commands:

```powershell
python -m tools.damage_debugger.matchup QUILAVA:34:player SKARMORY:33:trainer FLAME_WHEEL --attacker-hp 73 --defender-hp 100 --json
python -m tools.damage_debugger.matchup QUILAVA:34:player SKARMORY:33:trainer FIRE_BLAST --attacker-hp 73 --defender-hp 100 --json
python -m tools.damage_debugger.matchup QUILAVA:34:player SKARMORY:33:trainer THUNDERPUNCH --attacker-hp 73 --defender-hp 100 --json
python -m tools.damage_debugger.matchup QUILAVA:34:player SKARMORY:33:trainer QUICK_ATTACK --attacker-hp 73 --defender-hp 100 --json
python -m tools.damage_debugger.matchup SKARMORY:33:trainer QUILAVA:34:player STEEL_WING --attacker-hp 100 --defender-hp 73 --json
```

Damage anchors:

```text
Quilava Fire Blast -> Skarmory:
  180-212 damage, guaranteed KO from full.

Quilava Flame Wheel -> Skarmory:
  78-92 damage, 80-95% of Skarmory's max HP.

Quilava ThunderPunch -> Skarmory:
  64-76 damage, 66-78% of Skarmory's max HP.

Quilava Quick Attack -> Skarmory:
  4-5 damage.

Skarmory Steel Wing -> Quilava at 73%:
  12-15 damage, 14-18% of Quilava's current HP.
```

Local item / contact notes:

```text
Skarmory holds Rocky Helmet.
Flame Wheel is contact.
Fire Blast is non-contact.
Rocky Helmet recoil is attacker max HP / 6, so Quilava takes 19 HP after a
contact hit into Skarmory unless the hit ends the battle first.
```

Local phazing note:

```text
Whirlwind has no legal target here. The player has no living non-active
Pokemon, so the force-switch command routes to failure instead of dragging
anything through Spikes.
```

## Live-Turn Advice

Recommendation: if Quilava actually has Fire Blast, use Fire Blast. If not,
use Flame Wheel. Confidence: high for the move class; Fire Blast accuracy and
move availability are the main caps.

Plan: stop treating Skarmory as a hazard/phaze engine after the target pool is
gone. Convert the last Pokemon with Fire damage before Toxic, Steel Wing, or
Rocky Helmet recoil creates unnecessary risk.

State read: Skarmory is the last boss Pokemon and Quilava is the last player
Pokemon. Whirlwind cannot force a switch. Spikes cannot create new entry damage
without a switch. The remaining threats are Toxic, Steel Wing chip, Rocky
Helmet recoil on contact, and Fire Blast miss variance.

Win condition: remove Skarmory immediately with Fire Blast if available, or
two-turn it with Flame Wheel while tracking contact recoil and status.

Candidate ranking:

1. Fire Blast, if available: best. It KOs from full and avoids Rocky Helmet
   contact recoil, but can miss.
2. Flame Wheel: best revealed fallback. It is a reliable two-hit route from
   full, but it triggers Rocky Helmet contact recoil.
3. ThunderPunch: weaker than Flame Wheel and does not change the route faster.
4. Quick Attack: negligible damage from this state.
5. Smokescreen or other delay: bad unless damage math changes; it gives
   Skarmory more Toxic / Steel Wing turns without creating a conversion.

Opponent's best route: use Toxic or Steel Wing to make the Flame Wheel route
cost more HP, or benefit from a Fire Blast miss. Whirlwind is not a route
because there is no target to drag.

Worst plausible branch: the advisor over-respects Whirlwind and recommends
setup, Smokescreen, or preservation that does not exist in a last-Pokemon
state. Skarmory then lands Toxic or Steel Wing while Quilava still needs to
deal the same damage later.

Key piece: Quilava is the whole remaining route. Do not spend turns on
low-effect moves after the phazing target pool is gone.

What changes the answer:

- Quilava does not know Fire Blast.
- Quilava is low enough that Rocky Helmet plus Steel Wing or Toxic changes the
  two-turn Flame Wheel route.
- Skarmory is already in Flame Wheel or ThunderPunch KO range.
- The player still has a living bench target; then Whirlwind can be live again
  and Spikes / target-map questions return.
- Weather, screens, item, status, or exact damage evidence differs.

Next turn if it works:

- If Fire Blast KOs, the fight is over.
- If Fire Blast misses, re-score whether Quilava still survives Steel Wing /
  Toxic / contact recoil and use Fire Blast or Flame Wheel by remaining HP.
- If Flame Wheel lands and Skarmory survives, finish with Flame Wheel unless
  Skarmory is now in safer non-contact or priority range.

## Lesson Extracted

Phazing text is not a permanent reason to preserve or stall. When the target
pool is gone, the route handoff is immediate: damage, status timing, PP,
recovery, or trade. In this state, Fire damage is the route.
