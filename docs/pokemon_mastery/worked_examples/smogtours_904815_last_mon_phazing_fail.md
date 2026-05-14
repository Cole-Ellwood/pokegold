# Worked Example: Last-Mon Phazing Failure

Source review: `../reviews/2026-05-13_smogtours-gen2ou-904815.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-904815

Local source: `../../engine/battle/effect_commands.asm`,
`../../engine/battle/ai/switch.asm`.

Format: vanilla GSC strategic example plus Gym Leader Lab mechanics transfer.

## Position Pattern

```text
Our side:
A Roar or Whirlwind user is active.
Hazards, sleep turns, or setup denial would normally make phazing attractive.

Opponent side:
The active Pokemon is the opponent's only living Pokemon, or no legal
non-active target is public.
```

In the replay, Zapdos used Whirlwind successfully while RUBYBLOOD still had a
bench. After Exeggutor fainted on turn 45, RUBYBLOOD had only Raikou left.
Whirlwind on turns 69, 70, 73, 74, 79, and 80 no longer dragged anything.

## Local Mechanics Check

`BattleCommand_ForceSwitch` uses separate trainer-battle gates:

- player using Roar / Whirlwind into the enemy calls `FindAliveEnemyMons`;
- enemy using Roar / Whirlwind into the player calls
  `CheckPlayerHasMonToSwitchTo`;
- either no-target result routes to the normal failed-move path;
- `wEnemyGoesFirst` also gates the Gen 2 requirement that Roar / Whirlwind
  act last.

## Candidate Move Classes

Best / acceptable:

- Use Roar / Whirlwind when it works mechanically, the target has a living
  bench, and the forced target map improves through hazards, sleep turns,
  setup denial, recovery timing, or answer preservation.
- In a last-Pokemon state, hand off to damage, status that survives the reset
  map, PP conservation, recovery, setup, or a final trade.

Wrong:

- Clicking Roar / Whirlwind because "they are boosted" or "Spikes are up"
  without checking whether there is anything left to drag.
- Treating a failed last-mon phaze as useful scouting when no answer-changing
  information is gained.

## Rule

Before phazing, fill all fields:

```text
route being denied:
move acts last under local mechanics:
target has living non-active Pokemon:
forced target map improves:
next move after the drag:
```

If the target-pool field is false, Roar / Whirlwind is not route control.

## Boss-Battle Transfer

Use this for Jasmine Skarmory, Brock Onix / Golem-style phazing, Pryce
Piloswine, Chuck Sudowoodo, Bruno phaze loops, and any player-side Roar /
Whirlwind answer.

Boss AI rule:

- Do not score phazing from hidden player-team knowledge. If the public state
  does not prove a legal player bench target, cap confidence or prefer the move
  that improves against the visible active.

Player-side rule:

- Against a source-known boss, track the boss's remaining living Pokemon. Once
  the boss is on its last Pokemon, stop recommending Roar / Whirlwind as a way
  to reset setup or collect hazard damage.
