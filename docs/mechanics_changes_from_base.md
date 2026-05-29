# Mechanics Changes From Base Game

Generated: 2026-02-16
Baseline commit: `060d4accd7c0d01b1697ac97e7d7e2da72e3646b`

## Scope

This document describes mechanics-level changes only (battle systems, rules, item behavior, AI behavior, progression systems, and evolution logic).

Intent lens: these mechanics serve the First-Playthrough Promise. They should
make old Pokemon knowledge useful but incomplete, create readable danger, and
support scary boss fights without hidden-information cheating. Do not read this
file as a mandate for modernization by itself.

Excluded on purpose:
- Base stat edits
- Move power/PP/accuracy/type roster balancing details
- Trainer party composition changes
- Wild encounter table changes
- Cosmetic/UI-only edits

## 1) Battle Mechanics

### 1.1 Contact System (Gen 6 style contact mapping)

Files:
- `data/moves/contact_flags.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `engine/battle/effect_commands.asm`

Changes:
- Added a per-move contact table for all moves (`MoveContactFlags`) using Gen 6 contact logic.
- Added `TypePassive_IsCurrentMoveContact_Far` to query contact status from current move anim/move id.
- Contact is now used by:
  - Rocky Helmet recoil trigger.
  - Poison passive retaliation trigger.
  - Held flinch check (King's Rock-like effect now requires contact).

### 1.2 Late-Gen Held Item Framework

Files:
- `constants/item_constants.asm`
- `constants/item_data_constants.asm`
- `data/items/attributes.asm`
- `data/items/names.asm`
- `data/items/descriptions.asm`
- `engine/battle/late_gen_held_items.asm`
- `engine/battle/core.asm`
- `engine/battle/used_move_text.asm`
- `engine/battle/effect_commands.asm`

New/activated held effects:
- `LIFE_ORB`:
  - Damage multiplier: `13/10` (1.3x)
  - Recoil: `maxHP/10` (minimum 1)
- `CHOICE_BAND`:
  - Physical attack stat multiplier: `3/2` (1.5x)
  - Move-locks user into first selected move until reset condition
- `CHOICE_SPECS`:
  - Special attack stat multiplier: `3/2`
  - Move-lock behavior as above
- `CHOICE_SCARF`:
  - Speed multiplier in turn-order calc: `3/2`
  - Move-lock behavior as above
- `ASSAULT_VEST`:
  - Holder's SpDef multiplier for incoming special damage: `3/2`
  - Blocks non-damaging move selection/use (with explicit allowed exceptions in code)
  - If no legal move remains, forced `STRUGGLE`
- `EXPERT_BELT`:
  - Super-effective damage multiplier: `6/5` (1.2x)
- `MUSCLE_BAND`:
  - Physical damage multiplier: `11/10` (1.1x)
- `WISE_GLASSES`:
  - Special damage multiplier: `11/10` (1.1x)
- `EVOLITE`:
  - If species can evolve: Def and SpDef multipliers `3/2`
- `AIR_BALLOON`:
  - Ground-type attacks become no-effect against holder
  - Pops and item is cleared after holder takes direct hit damage
- `SHELL_BELL`:
  - Heal after hit: `floor(damage/8)` (minimum 1)
- `ROCKY_HELMET`:
  - If hit by contact move: attacker takes `maxHP/6` (minimum 1)
- `METRONOME_ITEM`:
  - Repeated use of same damaging move increases damage multiplier by +0.2 per stack
  - Formula: `(10 + 2*count)/10`, capped at `20/10` (2.0x)
  - Tracker resets on move change, non-damaging move, switching, or no longer holding item

Core enforcement behavior:
- Player choice lock and Assault Vest legality are enforced in move selection and "has usable moves" checks.
- Enemy choice/vest restrictions are enforced at action parse time.
- Choice/metronome state is reset on battle start and on switch/new active mon.

### 1.3 Type Passives System (Type Passive V1)

Files:
- `engine/battle/type_passive_damage_mods.asm`
- `engine/battle/effect_commands.asm`
- `engine/battle/core.asm`
- `ram/wram.asm`

Damage multipliers/passives:
- Normal STAB enhancer (when using Normal move with STAB bit set):
  - Half contribution: `31/30` (final STAB ~1.55x)
  - Full contribution: `16/15` (final STAB ~1.60x)
- Fire attacker below one-third HP:
  - Half: `11/10`
  - Full: `6/5`
- Ghost attacker vs statused defender:
  - Half: `21/20`
  - Full: `11/10`
- Dragon's Majesty:
  - Dragon attackers treat type-chart immunities as resistances (`0x` -> `0.5x`).
  - Applies only to damaging, non-fixed-damage moves.
- Imperial Scales:
  - Dragon defenders reduce non-super-effective, non-fixed-damage hits.
  - Half reduction: `2/3`
  - Full reduction: `1/2`
- Dragon-only Outrage category exception:
  - `DRAGONBREATH` stays special because Dragon is a special type.
  - `OUTRAGE` stays Dragon-type, but for Dragon users it uses the physical damage category when current Attack is greater than current Special Attack.
  - Ties and non-Dragon users keep `OUTRAGE` special.
  - The same category decision is used for damage stats, Reflect/Light Screen, critical stat checks, Choice Band/Specs, Muscle Band/Wise Glasses, Bug/Water passive reductions, Counter, and Mirror Coat.
- Ground defender on super-effective hit taken:
  - Half reduction: `19/20`
  - Full reduction: `9/10`
- Rock defender on critical hit taken:
  - Half reduction: `19/20`
  - Full reduction: `9/10`
- Bug defender vs physical-category hit taken:
  - Half reduction: `19/20`
  - Full reduction: `9/10`
- Water defender vs special-category hit taken:
  - Half reduction: `39/40`
  - Full reduction: `19/20`
- Ice defender above half HP:
  - Half reduction: `39/40`
  - Full reduction: `19/20`

Status and accuracy passives:
- Electric speed passive:
  - Half: speed `41/40`
  - Full: speed `21/20`
- Paralysis speed penalty tuning by Fighting typing:
  - Baseline: `1/4`
  - Half Fighting: `3/8`
  - Full Fighting: `1/2`
- Burn attack penalty tuning by Fighting typing:
  - Baseline: `1/2`
  - Half Fighting: `5/8`
  - Full Fighting: `3/4`
- Full paralysis fail chance by Fighting typing:
  - Baseline: 25%
  - Half Fighting: 20%
  - Full Fighting: 15%
- Flying accuracy bonus:
  - Half Flying: `26/25` (1.04x)
  - Full Flying: `27/25` (1.08x)

Reactive/status passives:
- Dark status shield (first eligible status attempt only):
  - Full Dark defender: always negates
  - Half Dark defender: 50% negate chance
  - Consumes one per active mon (`wPlayerDarkShieldConsumed`, `wEnemyDarkShieldConsumed`)
- Psychic mind shield:
  - Half Psychic defender: `6/256` chance to set incoming damage to 0
  - Full Psychic defender: `13/256`
  - Hit still proceeds through hit-flow semantics
- Poison retaliation:
  - On contact damaging hit, defender may poison attacker
  - Half Poison defender: 10%
  - Full Poison defender: 20%
  - Honors target immunity/status/item checks
- Steel recoil mitigation on recoil moves:
  - Half Steel user: recoil halved
  - Full Steel user: recoil becomes 0
- Grass regrowth (between turns):
  - Heals if not statused and not full HP
  - Half Grass: round-half-up `maxHP/64` (implemented as `floor((maxHP + 32) / 64)`, minimum 1)
  - Full Grass: round-half-up `maxHP/32` (implemented as `floor((maxHP + 16) / 32)`, minimum 1)

### 1.4 Spikes and Rapid Spin Rework

Files:
- `constants/battle_constants.asm`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/move_effects/rapid_spin.asm`
- `engine/battle/core.asm`
- `engine/battle/ai/redundant.asm`
- `engine/battle/ai/scoring.asm`
- `data/moves/animations.asm`

Changes:
- Spikes now supports 3 layers via two screen bits (`SCREENS_SPIKES`, `SCREENS_SPIKES_2`).
- Placement fails only when already at 3 layers.
- Damage on switch-in:
  - 1 layer: `maxHP/8`
  - 2 layers: `maxHP/6`
  - 3 layers: `maxHP/4`
- Rapid Spin clears both spikes bits (all layers).
- AI redundancy and AI scoring for Spikes/Rapid Spin updated to be layer-aware.
- Spikes animation now reflects layer count.

### 1.5 Ditto Imposter Auto-Transform

Files:
- `engine/battle/ditto_imposter.asm`
- `engine/battle/core.asm`
- `data/text/battle.asm`

Changes:
- Added `TryActivateDittoImposter` calls on battle-entry flow after both active battlers are loaded, including normal enemy lead startup and switch-in flow after hazard processing.
- If entering mon is Ditto, alive, not already transformed, and opponent is not hidden (Fly/Dig states), Ditto auto-uses Transform.
- Displays explicit activation text.

### 1.6 Trainer Battle Menu and Item Access Rules

Files:
- `engine/battle/menu.asm`
- `engine/battle/core.asm`
- `engine/battle/ai/items.asm`
- `engine/menus/options_menu.asm`
- `data/default_options.asm`

Changes:
- In non-link trainer battles, Pack is removed from the menu (menu is FIGHT / PKMN / RUN).
- Attempting Pack from trainer battle route is blocked.
- Enemy trainer bag item usage is disabled in trainer battles.
- Battle style is forced to Set: the switch prompt after an opposing KO is never
  offered, default options set the Set bit, and the Options menu displays Set
  without toggling back to Shift.

### 1.7 Additional Battle Rule/Bugfix Changes

Files:
- `engine/battle/effect_commands.asm`
- `data/types/type_boost_items.asm`
- `data/items/attributes.asm`

Changes:
- Ground vs Air Balloon immunity integrated in type matchup check.
- Dragon boost item mapping corrected so Dragon Fang now truly boosts Dragon-type damage (Dragon Scale continues to do so).
- Type-boost held effect parameter values changed from 10 to 20 (effectively 1.1x -> 1.2x) for the standard type-boosting items.
- Multi-stage stat-up helper (`effect0x5d`) now explicitly clears miss state to prevent chained stat scripts from inheriting stale miss flags.
- Existing critical-stat-stage logic and Ditto Metal Powder handling were refactored to shared far routines; behavior is now centralized and consistent across sides.

## 2) AI Mechanics

### 2.1 Boss AI Tiering and Activation

Files:
- `constants/trainer_data_constants.asm`
- `data/trainers/ai_tiers.asm`
- `engine/battle/read_trainer_attributes.asm`
- `engine/battle/start_battle.asm`
- `ram/wram.asm`

Changes:
- Added AI tiers: `AI_TIER_BASELINE`, `AI_TIER_EARLY`, `AI_TIER_MID`, `AI_TIER_LATE`.
- Added trainer-specific tier map for Gym Leaders, Rival milestones, Elite Four, and Champion.
- Added full Boss AI state block in WRAM with per-battle reset.

### 2.2 Boss Move Selection Model

Files:
- `engine/battle/ai/boss_policy_move.asm`
- `engine/battle/ai/move.asm`
- `constants/battle_constants.asm`

Changes:
- Added weighted boss move model with layered scoring:
  - KO opportunity
  - deny-KO utility
  - tempo
  - setup safety
  - status value
  - role/plan bias
  - risk penalties
- Added plan system (`BOSS_PLAN_TEMPO_PRESSURE`, `BOSS_PLAN_STATUS_CHOKE`, `BOSS_PLAN_SETUP_SWEEP`, `BOSS_PLAN_WALLBREAK_THEN_CLEAN`, `BOSS_PLAN_ENDGAME_PROTECT`, `BOSS_PLAN_ANTI_SETUP_DENIAL`) with adaptation over turns.
- Added probabilistic best-vs-second-best move pick to avoid deterministic patterns.
- Added mid/late lookahead scoring on top move candidates.
- Setup-move encouragement (`BossAI_SetupBoostHasFurtherValue.check_speed`) caps Speed boosts by the booster's base Speed: base ≥90 caps at +1 stage, base 60–89 caps at +2, base ≤59 caps at +3 (the only band that permits a second Agility). Already-outspeeding the player short-circuits further encouragement regardless of cap.

### 2.3 Boss Switching Logic

Files:
- `engine/battle/ai/boss_policy_switch.asm`
- `engine/battle/ai/items.asm`
- `constants/battle_constants.asm`

Changes:
- Tier-based switch confidence thresholds:
  - Early 80
  - Mid 70
  - Late 60
- Anti-loop switch cooldown and same-mon re-switch penalty.
- Exceptions for imminent KO prevention, immunity pivots, and ace timing hooks.
- Candidate refinement uses plausible risk modeling against seen/revealed/plausible player threat types.
- Class-specific threshold modifiers for some boss trainers.

### 2.4 Boss Knowledge Model (No Hidden Party Reads)

Files:
- `engine/battle/ai/boss_platform.asm`
- `engine/battle/used_move_text.asm`
- `engine/battle/core.asm`

Changes:
- Boss AI tracks seen player species and revealed player moves.
- Builds a possible threat type mask from:
  - currently seen species typing
  - revealed damaging moves
  - public TM/HM learnability possibilities
  - active-species and pre-evolution-chain level-up moves
  - active-species and pre-evolution-chain egg moves
- Builds a likely threat type mask from:
  - currently seen species typing
  - revealed damaging moves
  - current-species level-up moves at or below the active level
- Switch-risk scoring gives likely threats full tier weight and possible-only
  threats reduced speculative weight.
- Includes scout flow (Protect/Substitute preference when scouting trigger is active).

### 2.5 Generic AI Bugfixes and Upgrades

Files:
- `engine/battle/ai/redundant.asm`
- `engine/battle/ai/scoring.asm`

Changes:
- Future Sight redundancy logic fixed (no longer keying off unrelated screen bit).
- Mean Look smart logic fixed to inspect player toxic state, not enemy toxic state.
- Dragon Dance recognized as setup move in scoring.
- Rapid Spin smart scoring now checks hazard layers and scales encouragement.
- Late-tier bosses bypass one conservative "Cautious" discouragement gate.

## 3) Progression / Overworld Mechanics

### 3.1 Gym TM Rewards

Files:
- `maps/VioletGym.asm`
- `maps/AzaleaGym.asm`
- `maps/GoldenrodGym.asm`
- `maps/EcruteakGym.asm`
- `maps/CianwoodGym.asm`
- `maps/OlivineGym.asm`
- `maps/MahoganyGym.asm`
- `maps/BlackthornGym1F.asm`

Mechanic:
- Johto gym rewards follow the direct TM pattern:
  - Falkner: `TM_WING_ATTACK`
  - Bugsy: `TM_LEECH_LIFE`
  - Whitney: `TM_DOUBLE_EDGE`
  - Morty: `TM_SHADOW_BALL`
  - Chuck: `TM_DYNAMICPUNCH` and `TM_FOCUS_PUNCH`
  - Jasmine: `TM_IRON_TAIL`
  - Pryce: `TM_BLIZZARD`
  - Clair: `TM_OUTRAGE`

### 3.2 Move Reminder

Files:
- `engine/events/move_reminder.asm`
- `maps/DayCare.asm`
- `data/events/special_pointers.asm`

Mechanic:
- New Move Reminder service.
- Free relearn flow.
- Move pool is built from current species and pre-evolution chain level-up learnsets up to current level.
- Already-known moves and duplicates are filtered out.
- Paged move list UI (`NEXT` / `CANCEL`) supports larger candidate sets.

### 3.3 HM Field Tools And Former HMs As TMs

Files:
- `constants/item_constants.asm`
- `data/items/attributes.asm`
- `data/items/names.asm`
- `engine/events/overworld.asm`
- `engine/items/item_effects.asm`
- `engine/items/tmhm.asm`
- HM reward map scripts in `maps/`

Mechanic:
- Field use no longer requires a party Pokemon to know the old HM move.
- Seven key items provide field actions while preserving acquisition and badge
  gates: `PRUNERS`, `SKY_PASS`, `SURFBOARD`, `POWER_GLOVE`, `LANTERN`,
  `WHIRL_KIT`, and `CLIMB_GEAR`.
- Former HM discs are displayed and handled as `TM51`-`TM57`.
- Former HM moves can be forgotten and their discs are consumed when taught.
- Original HM reward moments now give the key item plus the corresponding
  converted TM.
- Legacy saves that already set an original HM reward event treat that event as
  ownership for matching field-tool checks and try to backfill the missing key
  item. `SKY_PASS` and `LANTERN` can also be recovered by revisiting their
  reward NPCs, since Fly/Flash do not have an A-button route-blocker check.
- `SKY_PASS` uses a fixed Pidgey-style fly animation icon instead of reading
  stale party-mon state.
- Failed or canceled tool use from the Bag or SELECT registration is marked as
  handled no-effect state, so field-specific failure text is not followed by the
  generic Oak "not the time" message.
- The tools are `CANT_TOSS` key items without `CANT_SELECT`, so they can be
  registered for SELECT use.
- A-button obstacle prompts and tool-use success text name the replacement
  tools instead of asking the player to use the old HM moves.
- Badge speeches and nearby field-move advice NPCs explain badge gates using
  the replacement tools rather than "Pokemon must know the HM" wording.
- The seven tools fit exactly in the existing key-item pocket budget: 25
  key-item attributes for `MAX_KEY_ITEMS = 25`.

## 4) Evolution Mechanics

### 4.1 Branching Level Evolution Choice Menu

Files:
- `engine/pokemon/evolve.asm`

Mechanic:
- If multiple level-based evolution outcomes are valid at level-up, player is prompted to choose target species.
- Up to 5 candidates are shown.
- Canceling the menu cancels that evolution attempt (no forced branch).

## 5) Runtime State and Integration Additions

Files:
- `ram/wram.asm`
- `main.asm`

Added runtime state for new mechanics:
- Dark shield consumed flags.
- Choice lock states.
- Metronome tracking states.
- Reserved bytes that preserve the removed move-tutor layout.
- Full Boss AI state block (+ optional trace block under `BOSS_AI_TRACE`).

Build integration:
- New modules included for boss AI, late-gen held items, type passive logic,
  and move reminder.
- `Makefile` now supports extra assembler defines via `DEFINES`, enabling optional debug trace builds (for example `-D BOSS_AI_TRACE`).

## Appendix A: Mechanics-Relevant Files Touched

- `constants/battle_constants.asm`
- `constants/event_flags.asm`
- `constants/item_constants.asm`
- `constants/item_data_constants.asm`
- `constants/trainer_data_constants.asm`
- `data/events/special_pointers.asm`
- `data/items/attributes.asm`
- `data/items/descriptions.asm`
- `data/items/names.asm`
- `data/moves/contact_flags.asm`
- `data/text/battle.asm`
- `data/trainers/ai_tiers.asm`
- `data/types/type_boost_items.asm`
- `engine/battle/ai/boss_platform.asm`
- `engine/battle/ai/items.asm`
- `engine/battle/ai/move.asm`
- `engine/battle/ai/redundant.asm`
- `engine/battle/ai/scoring.asm`
- `engine/battle/core.asm`
- `engine/battle/effect_commands.asm`
- `engine/battle/late_gen_held_items.asm`
- `engine/battle/menu.asm`
- `engine/battle/move_effects/rapid_spin.asm`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/read_trainer_attributes.asm`
- `engine/battle/start_battle.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `engine/battle/used_move_text.asm`
- `engine/events/move_reminder.asm`
- `engine/pokemon/evolve.asm`
- `main.asm`
- `maps/DayCare.asm`
- `maps/VioletGym.asm`
- `maps/AzaleaGym.asm`
- `maps/BlackthornGym1F.asm`
- `ram/wram.asm`
