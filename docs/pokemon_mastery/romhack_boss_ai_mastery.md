# Romhack Boss AI Mastery Bridge

Status: active implementation-prep reference.
Last audited: 2026-05-17.

Purpose: translate the Pokemon mastery work into rules that are safe to use
when recoding Gym Leader, Rival, Elite Four, Champion, Red, Rocket Executive, or
other explicitly selected boss AI in this romhack. This file is not a
replacement for source checks. It is the bridge that says which learned battle
principles transfer, which mechanics must be looked up locally, and what a
strong no-cheat boss should value.

## Source Stack

Use this order whenever memory, GSC notes, modern Pokemon knowledge, or old
project notes disagree:

1. Local assembly/data source.
2. Generated source-derived references:
   - `docs/agent_navigation/hack_mechanics_reference.md`
   - `docs/generated/balance_audit.md`
3. Mechanics overview and delta docs:
   - `docs/pokemon_mastery/romhack_deltas/mechanics_inventory.md`
   - `docs/mechanics_changes_from_base.md`
   - `docs/agent_navigation/gen2_vs_modern_mechanics.md`
   - focused `docs/pokemon_mastery/romhack_deltas/*.md`
4. Focused tools:
   - `tools.damage_debugger.matchup` for exact damage ranges.
   - `tools.debugger` for triage, provenance, slices, setup plans, and
     runtime watch/trace proof when a mechanic is uncertain.
5. Strategy lessons from GSC/expert play.

Do not teach the boss AI from vanilla GSC memory until the local mechanic has
passed this stack.

## What Transfers From GSC Training

These are strategy concepts, not mechanics claims:

- Name the current route and the opponent's route before scoring moves.
- Prefer moves that convert a route, deny the opponent's route, punish a
  high-incentive branch, or preserve the correct irreplaceable piece.
- Treat hazards, status, recovery, phazing, setup, Explosion, and switching as
  multi-turn resource trades.
- Track role identity: the same Pokemon may be a wall, route converter,
  spinner, phazer, cash-out piece, status absorber, or clean-entry sacrifice.
- Compare the likely player line with the worst plausible public branch.
- Use positive selection: a move should buy something concrete, not merely be
  defensible.

These are still valuable for the romhack, but their inputs must come from local
mechanics and local rosters.

## What Does Not Transfer Directly

Do not import these assumptions:

- Vanilla one-layer Spikes. This hack has three layers.
- Modern per-move physical/special categories. This hack uses the Gen 2
  type-based split, with the local Outrage exception.
- Modern type-chart intuition. This hack has deliberate matchup edits.
- Modern ability assumptions. There are no ordinary Pokemon abilities; the
  closest local system is type passives.
- Generic Smogon item intuition without checking local item code.
- Generic species roles without checking local stats, types, movesets,
  learnsets, trainer rosters, and held items.
- Full-information play. Ordinary boss AI must not read hidden player team
  slots, hidden moves, hidden items, hidden PP, or current-turn player input.

## Boss AI Legality Model

Upgraded AI is opt-in. General trainers should keep the base-game AI unless
they are explicitly selected as bosses. Current boss scope is Gym Leaders,
Silver/Rival fights, Elite Four, Champion/Lance, Red, and Rocket Executives.

This opt-in rule controls strategic strength, not mechanics correctness. Base
trainers may keep the legacy planning level, but shared AI scoring must still
respect this romhack's mechanics. Do not allow ordinary trainers to make basic
mistakes from vanilla assumptions about the type chart, move category,
three-layer Spikes, Rapid Spin, type passives, or visible held-item legality.

Strong boss AI should look prepared because it uses public information well:

- visible active species, HP, status, boosts, screens, weather, hazards, and
  turn history;
- revealed player moves and observed damage/status/switch patterns;
- public learnability priors allowed by the current policy;
- boss roster, boss held items, boss plan, and trainer tier/personality;
- local source-derived type chart, move data, item behavior, and type passives.

Ordinary boss AI should not use hidden party slots, hidden moves, hidden items,
hidden PP, direct current-turn player input, private menu state, or Haki/oracle
behavior. If a special boss script intentionally uses extra information, keep
it quarantined, named, and fixture-tested.

## Pre-Scoring Mechanics Gate

Before assigning move or switch score, resolve these local facts for the
candidate and target:

1. Type matchup from `data/types/type_matchups.asm` or the generated reference.
2. Offensive category from type, not move animation or modern memory.
3. Move power, accuracy, PP, priority, effect, contact flag, and effect chance.
4. Current species stats/types/items/learnset/trainer moves from local data.
5. Hazard layer count and whether a Rapid Spin line can erase all layers.
6. Type passive and held item effects that alter damage, status, speed,
   recoil, contact, recovery, or move legality.
7. Public-information status: revealed, strong public prior, possible-only, or
   hidden/illegal for the boss.
8. Runtime status for timing-sensitive mechanics. If the pending index says
   unknown, do not convert that mechanic into a hard scoring rule yet.

## Local Mechanics That Must Shape Scoring

### Type Chart And Category

Use `docs/agent_navigation/hack_mechanics_reference.md` for exact tables.
High-risk traps:

- Dark remains special and hits Steel neutrally.
- Ghost is physical and does no damage to Steel.
- Poison is physical and hits Normal super-effectively.
- Psychic is neutral into Poison.
- Grass is neutral into Flying.
- Ground is neutral into Fire and no-effect into Ghost.
- Fire, Water, Grass, Electric, Psychic, Ice, Dragon, and Dark are special.
- Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, and Steel are
  physical.
- Outrage is Dragon-type but Dragon users make it physical only when current
  Attack is greater than current Special Attack.

Boss implication: never score coverage from move names or vanilla memory.
Score from local type, local category, local matchup, local stats, and local
passives.

### Type Passives

Type passives can make a correct chart read strategically wrong:

- Dragon's Majesty converts Dragon-attacker immunities into resistances for
  damaging non-fixed-damage moves.
- Imperial Scales reduces non-super-effective hits into Dragon defenders.
- Dark can block the first eligible status attempt.
- Poison can poison on contact.
- Psychic can rarely set incoming damage to zero.
- Grass regrowth changes chip and status clocks.
- Fire below one-third HP becomes more dangerous.
- Fighting changes paralysis/burn penalties and full-paralysis odds.
- Electric speed, Flying accuracy, Steel recoil, and smaller defensive
  reductions matter at thresholds.

Boss implication: a hard AI rule that says "status this target", "this is a
safe immune pivot", or "this damage KOs" must pass the passive layer.

### Three-Layer Spikes And Rapid Spin

Spikes is a route multiplier, not a checkbox:

- 0 to 1 layer creates a switch tax.
- 1 to 2 layers is useful only if repeated grounded switches, phazing, Rest
  pressure, or a route to the third layer makes it convert.
- 2 to 3 layers is major pressure because grounded switch-ins take maxHP/4.
- 3 to 3 is no progress and should be discouraged.
- Flying types ignore Spikes. There is no Levitate-style ability check.
- Successful Rapid Spin clears all layers.

Boss implication: layer-aware scoring must ask whether the next layer changes
switch costs, KO ranges, Rest timing, phazing value, sacrifice math, or the
opponent's recovery route. It must also price active public Rapid Spin before
greedy second or third layers.

### Late-Gen Held Items

Use `engine/battle/late_gen_held_items.asm` and generated item tables before
scoring held-item cases:

- Life Orb boosts damage and costs recoil.
- Choice Band, Choice Specs, and Choice Scarf lock the holder into the first
  selected move while boosting physical attack, special attack, or speed.
- Assault Vest boosts incoming special defense and blocks most non-damaging
  move use.
- Expert Belt boosts super-effective damage.
- Muscle Band and Wise Glasses boost physical or special damage.
- Eviolite / EVOLITE boosts Def and SpDef for species that can evolve.
- Air Balloon makes Ground attacks no-effect until popped by direct hit damage.
- Shell Bell heals after damage.
- Rocky Helmet punishes contact.
- Metronome item rewards repeated use of the same damaging move.

Boss implication: item-aware scoring must adjust both move value and candidate
legality. A Choice-locked boss should not score illegal alternatives; an
unlocked Choice boss should price first-lock regret; an Assault Vest holder
should not be taught to prefer a blocked support move; contact moves into
Rocky Helmet or Poison defenders need a cost branch.

### Move Data, Stats, And Rosters

Exact current move data, species stats/types, TM compatibility, and trainer
rosters are local data, not memory:

- Move data lives in `data/moves/moves.asm`, effect scripts, priority data, and
  contact flags.
- Species stats/types/TM learnsets live in `data/pokemon/base_stats/*.asm`.
- Level-up moves and evolutions live in `data/pokemon/evos_attacks.asm`.
- Trainer rosters live under `data/trainers/`.
- `docs/generated/balance_audit.md` is useful for changed stats and balance
  review, but generated tables are hints for design, not a damage calculator.

Boss implication: species identity must be rebuilt from local stats, typing,
item, and moves. Do not assume standard Smogon roles when the local Pokemon may
have changed stats, type, item, or move access.

## Boss Scoring Skeleton

Use the existing public-info scorer shape, but make the scoring terms
mechanics-aware:

```text
 immediate KO or forced survival
+ route conversion
+ opponent route denial
+ branch punish from public incentives
+ hazard/status/recovery/phaze/setup progress that changes a future state
+ item/passive-aware damage or legality value
+ preservation of a named irreplaceable boss route piece
- illegal or mechanically failed move
- hidden-information dependency
- route-losing exposure to public threat
- repetition, loop, or first-lock regret
- fake progress from capped Spikes, blocked status, bad contact, or reset loops
```

The boss should not merely choose the highest immediate damage. It should pick
the move or switch that improves the best public route while covering the
player's strongest public counter-route.

## Candidate Generation Contract

For every serious boss turn, generate candidates from roles before ranking:

- active KO or damage converter;
- status or setup converter;
- hazard placement, removal, or retention;
- phaze, Encore, disable, trap, or anti-setup denial;
- recovery, Rest, Protect, or survival route;
- switch to direct absorber, immunity pivot, revenge owner, or preserved ace;
- sacrifice or cash-out move when it buys a cleaner route;
- item-specific line such as Choice lock, Air Balloon pivot, Assault Vest
  attack-only pressure, or Metronome-repeat commitment.

Missing a live role is a candidate-generation bug. Promoting the wrong live role is a route-budget bug.
Keep those failure classes separate when testing.

## Route-Budget Tiebreak For Boss AI

When two legal candidates are close, prefer the one that:

1. KOs or denies an immediate loss.
2. Converts a named route within the next one or two turns.
3. Denies the player's named route.
4. Punishes the highest-incentive public branch.
5. Preserves the boss piece whose future job is unique.
6. Spends the piece whose job is already complete.
7. Keeps next-board clarity instead of opening a reset loop.

Safe/default moves are correct only when they preserve a winning route or deny
the player's route. A safe move that lets the player Spin, Rest, set up, heal,
switch freely, or waste the boss's item lock is not actually safe.

## Implementation Prep Checklist

Before changing boss AI source:

1. State the public-info reason the behavior is legal.
2. State the local mechanics facts it depends on.
3. Name the current source hook or the new hook needed.
4. Add or update a fixture/preference row for the behavior.
5. Run the mechanics audit if the rule touches type chart, move category,
   items, Spikes/Rapid Spin, type passives, or fixture prose.
6. Use `python -m tools.debugger triage --changed-file <path>` or a symptom
   query when the touched behavior crosses damage, item timing, hazards, or
   Boss AI scoring.
7. Run the boss-AI audit floor for the touched module.
8. Add a trace label if the score change should be inspectable.

If the rule cannot be expressed as public-info behavior plus a local mechanics
fact, quarantine it instead of teaching it to ordinary bosses.

## Current Debugger Finding

2026-05-17 battle-only debugger pass found and fixed a Boss AI thunk register
bug: `AICheckPlayerQuarterHP_HL` and `AICheckPlayerHalfHP_HL` now preserve
`bc/de`, because the banked HP macros use `b/c` as scratch while boss
lookahead uses `b/c` as upside/downside accumulators.

This fixed real ROM score corruption, but it did not make Boss AI policy clean.
The remaining materialized failures are decision-quality or mirror-alignment
work: broad lookahead penalties and over-selection of Toxic/status in generated
prediction states. See
`docs/pokemon_mastery/runs/2026-05-17_battle_debugger_bug_hunt.md` before
editing lookahead, status, or role bias.

## Current Open Risks

These mechanics still need runtime or fixture caution before hard scoring:

- sleep duration, wake timing, Sleep Talk, and Rest edge cases;
- Explosion timing, damage, and Ghost interactions;
- phazing timing and failure cases;
- Focus Band and Quick Claw;
- Counter and Mirror Coat;
- Air Balloon display text ordering if UI behavior becomes relevant; Ground
  immunity and after-hit active/party item clear are damage-debugger covered;
- exact same-turn Spikes/Rapid Spin text, PP, and timing branches.

Until verified, these can inform cautious branches, but they should not become
unqualified scoring rules.

## Correct Mental Model

The desired boss is not a vanilla GSC player, a modern Showdown bot, or a
cheating oracle. It is a public-info planner in this romhack's ruleset:

```text
local mechanics -> legal candidates -> route value -> branch risk -> score
```

GSC study teaches the route language. This file and the local source define the
rules of the actual game the boss is playing.
