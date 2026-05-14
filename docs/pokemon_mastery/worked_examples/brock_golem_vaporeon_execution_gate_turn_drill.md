# Brock Golem / Vaporeon Execution-Gate Turn Drill

Purpose: convert the Brock Golem Explosion prompt into exact turn advice using
local damage and turn-order evidence. This is a player-side boss advice drill,
with a boss-policy note where the existing fixture oracle conflicts with the
mechanics gate.

Mechanics profile: `romhack_gym_leader_lab`

Local sources:

- Boss roster: `data/trainers/parties.asm`, `BrockGroup`
- Fixture: `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `brock_golem_vs_vaporeon_explosion_question`
- Quarantine note: `brock_golem_explosion_turn_order_quarantine.md`
- Move data: `data/moves/moves.asm`, `EXPLOSION`, `SURF`, `EARTHQUAKE`
- Priority data: `data/moves/effects_priorities.asm`
- Mechanics reference: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Damage command: `python -m tools.damage_debugger.matchup`

## Position

```text
Brock active:
  Golem Lv60 @ Rocky Helmet
  HP: 42%
  Known/source moves: Curse / Earthquake / Rock Slide / Explosion

Player active:
  Vaporeon Lv61
  HP: 76%
  Revealed moves: Surf / Bite
  Public priors: Ice Beam plausible, Rest plausible

Field:
  No weather
  No screens
  Brock bench: Omastar / Corsola / Kabutops / Onix / Aerodactyl
  Player seen party in fixture: Vaporeon / Machamp
```

Information model:

- Player-side advisor may use Brock's source-known roster and current public
  battle state.
- Boss AI may not know unrevealed player moves such as Protect unless they have
  already been shown or are allowed by a public prior policy.

## Local Damage

Vaporeon Surf into Golem:

```text
python -m tools.damage_debugger.matchup VAPOREON:61:player GOLEM:60:trainer SURF --attacker-hp 76 --defender-hp 42 --json
```

- Damage: 339-399.
- Golem current HP: 83.
- Result: guaranteed KO from current HP and max HP.

Golem Explosion into Vaporeon:

```text
python -m tools.damage_debugger.matchup GOLEM:60:trainer VAPOREON:61:player EXPLOSION --attacker-hp 42 --defender-hp 76 --json
```

- Damage: 262-308.
- Vaporeon current HP: 209.
- Result: guaranteed KO from current HP if Explosion executes.

Golem Earthquake into Vaporeon:

```text
python -m tools.damage_debugger.matchup GOLEM:60:trainer VAPOREON:61:player EARTHQUAKE --attacker-hp 42 --defender-hp 76 --json
```

- Damage: 79-94.
- Result: not a KO and does not stop Surf.

Vaporeon Surf into Omastar:

```text
python -m tools.damage_debugger.matchup VAPOREON:61:player OMASTAR:57:trainer SURF --attacker-hp 76 --defender-hp 100 --json
```

- Damage: 124-146.
- Omastar max HP: 167.
- Result: Omastar survives but takes 74-87%.

## Advice

Recommendation: use Surf with Vaporeon if the fixture's speed statement is
correct and no higher-priority branch is active. Confidence: high on damage,
medium on the whole turn because exact Speed and player move choice still gate
Explosion.

Move ranking from the player side:

1. Surf: removes Golem before Explosion if Vaporeon is faster. This prevents
   both Curse and the one-time trade.
2. Switch or absorb: only if Vaporeon is the sole answer to a more important
   Brock route and another piece can take Explosion or Earthquake.
3. Protect or scout: only if Explosion can execute before Surf, or if Surf's
   KO is somehow unconfirmed. If Surf already prevents Explosion, Protect gives
   Brock a chance to Curse, switch, or reset the position.
4. Bite / weak chip / setup / Rest: bad from this state because they let Golem
   use Explosion or Curse without removing it.

Boss-policy ranking from the same public state:

1. If Vaporeon is faster and Surf is the dominant public branch, Explosion is
   not mechanics-safe. It does nothing if Surf KOs first.
2. Switch to Omastar is a real preservation line, but Surf still chunks it for
   74-87%, so it must be chosen only if Golem's role matters later or
   Explosion cannot execute.
3. Explosion rises only if public evidence changes the branch: Vaporeon is
   slower, full-paralyzed, expected to switch, expected to Protect/Rest/setup,
   Surf is out of PP, Surf is not revealed, or another local turn-order fact
   lets Golem act.
4. Earthquake and Rock Slide are bad under the Surf branch because they neither
   remove Vaporeon nor preserve Golem.

## Route Ledger

If Surf KOs:

- Golem's Curse/Explosion route is gone.
- Re-score Brock's likely next route: Omastar hazards/Protect, Corsola
  Recover/Spin/Toxic, Kabutops Swords Dance, Onix Spikes/Roar, or Aerodactyl
  cleanup.
- Vaporeon remains a major Rock-team pressure piece but must still be checked
  for Aerodactyl speed and Kabutops damage.

If Explosion executes:

- Vaporeon is removed from current HP.
- Brock gets a clean entry but loses Golem's physical-wall and Explosion jobs.
- The player must immediately name who now answers Kabutops, Onix, and
  Aerodactyl.

If Brock switches to Omastar:

- Omastar survives one default Surf but is heavily damaged.
- Brock preserves Golem but may have handed the player enough damage to deny
  Omastar's Spikes/Protect route.

## Answer Flips

Surf stops being automatic when:

- Vaporeon is slower in the exact state.
- Vaporeon is paralyzed and full paralysis is a material branch.
- Golem has a Quick Claw-like move-order effect.
- Surf PP is gone or Surf is disabled/locked out.
- A local item/passive/status branch changes damage or execution.
- Vaporeon is the only answer to a later, more dangerous Brock route and can be
  preserved without letting Golem trade.

Explosion becomes correct for Brock when:

- Golem can actually move before Vaporeon removes it.
- Vaporeon is expected to switch, heal, set up, use weak chip, or scout.
- Removing Vaporeon opens a named route through Omastar, Kabutops, Onix, or
  Aerodactyl.
- Golem's remaining wall role is no longer needed.

## Common Bad Advice

- "Explosion KOs Vaporeon, so use Protect." Not if Surf KOs first.
- "Golem is low, so Brock will Explode." Low HP does not bypass turn order.
- "Earthquake for chip." It loses Golem and keeps Vaporeon.
- "Switch to preserve Vaporeon" without naming the later route that Vaporeon
  alone answers.

## Notebook Lesson

When a one-time trade is lethal but slower than the opponent's KO, the trade is
not a threat until the move-order branch changes. In live boss advice, separate
damage truth from execution truth: "Explosion KOs if it moves" and "Explosion
gets to move" are different claims.

## Unverified Before Exact Live Advice

- Exact Speed and stat stages in the user's battle state.
- Whether Vaporeon is paralyzed, confused, flinched, disabled, locked, or out
  of Surf PP.
- Whether Vaporeon has revealed Protect or another scout move.
- Whether Golem has already revealed Explosion in the battle.
- Whether preserving Vaporeon matters more than removing Golem because of the
  remaining Brock roster and the user's full team.
