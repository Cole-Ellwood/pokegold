# Worked Example: Chuck Poliwrath Focus Punch Free-Turn Denial

Purpose: practice Focus Punch as a condition-dependent move. The lesson is not
"Focus Punch is strong" or "use coverage." The lesson is to ask whether the
board gives the user a no-damage window before the move can matter.

Local evidence:

- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
  (`fixture_chuck_poliwrath_vs_pidgeotto_ice_punch_001`).
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`.
- Fixture source:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
  (`chuck_poliwrath_vs_pidgeotto_ice_punch`).
- Chuck roster source: `data/trainers/parties.asm`.
- Focus Punch source: `data/moves/moves.asm`,
  `data/moves/effects_priorities.asm`, and
  `engine/battle/late_gen_held_items.asm`.
- Speed/stat source: `tools.damage_debugger.matchup` profile plus
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert transfer: Smogon Substitute / SubPunch material frames Focus Punch as
  powerful only when a switch, Substitute, sleep, passive turn, or other board
  condition protects the user from being damaged first.

## Public State

```text
Chuck Poliwrath Lv34 at 76%, Mystic Water
  Surf / Hypnosis revealed
  Ice Punch / Focus Punch available
  current role: bulky closer

Chuck bench:
  Sudowoodo at 58%
  Hitmontop at 89%
  Hitmonlee at 100%
  Umbreon at 72%

Player Pidgeotto Lv33 at 58%
  Wing Attack / Quick Attack revealed

Player seen party:
  Pidgeotto / Kadabra
```

Public speed evidence:

- Damage-debugger profile speed: Poliwrath 58, Pidgeotto 76.
- Pidgeotto also has Quick Attack, so the priority branch can break Focus
  Punch even if another live state changes ordinary speed.

## Candidate Labels

- Best: switch to Sudowoodo.
- Acceptable: Ice Punch.
- Catastrophic: Focus Punch.

## Why Sudowoodo Is Best

Poliwrath is not just the active attacker; it is Chuck's bulky closer. Spending
its HP into a revealed Flying-pressure line makes the later Kadabra and cleanup
branches easier for the player.

Sudowoodo changes the state cleanly:

- Pidgeotto Wing Attack into Poliwrath at 76%: 52-62 damage, 53-63% of current
  HP.
- Pidgeotto Quick Attack into Poliwrath at 76%: 13-16 damage, 13-16% of current
  HP, and still enough to break Focus Punch.
- Pidgeotto Wing Attack into Sudowoodo at 58%: 12-15 damage, 21-27% of current
  HP.
- Pidgeotto Quick Attack into Sudowoodo at 58%: 6-8 damage, 11-14% of current
  HP.

Sudowoodo does not need to instantly win the matchup to be the right move. It
only needs to preserve Poliwrath while making the public attack branch much
less valuable.

## Why Ice Punch Is Only Acceptable

Ice Punch is live damage into Pidgeotto:

- Poliwrath Ice Punch into Pidgeotto at 58%: 34-40 damage, 52-61% of current
  HP.

That is real pressure, but it is not a guaranteed KO. If Pidgeotto attacks
first, Poliwrath pays more than half its current HP before dealing the damage.
Ice Punch can be right if Sudowoodo is unavailable, if Poliwrath no longer
needs to be preserved, or if the damage roll plus follow-up creates a forced
route. In the public card, preservation is cleaner.

## Why Focus Punch Fails The Position

Focus Punch damage looks tempting:

- Poliwrath Focus Punch into Pidgeotto at 58%: 58-69 damage, 88-105% of current
  HP.

But the local source marks Focus Punch as failed if the selected user takes
nonzero damage before acting. Pidgeotto has public attacking moves, it is faster
in the local profile, and Quick Attack gives it a priority damage branch.

Route answer:

```text
Do not click Focus Punch just because the damage range is attractive. The
condition for the move is absent. Preserve Poliwrath through Sudowoodo, then
re-score from the new board.
```

## Answer-Changing Information

The answer can flip if:

- Sudowoodo is unavailable, too low, statused, or needed for a more important
  route.
- Ice Punch becomes a guaranteed KO and Poliwrath survives every public
  response afterward.
- Pidgeotto is locked into a non-damaging move, asleep, fully unable to damage
  before Focus Punch, or forced to switch.
- Kadabra is gone, making Poliwrath's HP much less valuable.
- Live speed, priority, Quick Claw, paralysis, or damage-debugger evidence
  contradicts the public card's turn-order assumption.

## Reusable Recipe

Before choosing Focus Punch, ask:

1. Can the opponent damage the user before Focus Punch executes?
2. Is that damage nonzero under the current mechanics profile?
3. Is the opponent incentivized to attack, switch, recover, status, or setup?
4. If Focus Punch fails, what route did we lose?
5. If Focus Punch lands, what route becomes better beyond raw damage?
6. Is there a pivot that preserves the Focus Punch user and covers the public
   punish?

Failure signs:

- Choosing Focus Punch from damage range alone.
- Calling a move "coverage" without pricing the HP spent to use it.
- Preserving no one for the later route because the current attack looks active.
- Treating Focus Punch as safe after sleep, switch pressure, or Substitute
  without re-scoring the current board.
