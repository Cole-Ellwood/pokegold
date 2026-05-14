# Worked Example: Accuracy Disruption Endpoint

Purpose: practice treating accuracy drops as public reliability changes
without mistaking them for a finished route. The mistake is either ignoring the
drop entirely or overvaluing it after the opponent has a better endpoint.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-891112.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-891112.log
- Expert basis: Smogon, Introduction to Status in GSC,
  https://www.smogon.com/resources/competitive/gs/status

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses before turn 215 of `smogtours-gen2ou-891112`.

```text
Fear:
  Forretress is active at 62% after Leftovers.
  Revealed moves: Hidden Power / Rapid Spin / Spikes / Toxic.
  Skarmory is available with Drill Peck / Protect / Toxic / Whirlwind.
  Skarmory was hit by Sand Attack on turn 213, then Fear switched it out.

melancholy0:
  Snorlax is active at 94% after Leftovers.
  Revealed moves: Curse / Rest / Return.
  Snorlax entered through Spikes on turn 214 and is not poisoned yet.
  Skarmory is still alive and has revealed Sand Attack.

Field and boundary:
  Spikes are on melancholy0's side.
  There is no Team Preview. The move knowledge above is from public reveals in
  the replay log, not preview.
```

Route status:

- Sand Attack has proved that melancholy0 can tax hit reliability.
- Fear's active Forretress has a 100-accuracy Toxic into Snorlax.
- Fear's Skarmory has a resistance, Protect, and Whirlwind for the poisoned
  Snorlax route.
- A switched-out Pokemon no longer carries the accuracy drop when it returns.

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Toxic with Forretress, then preserve Skarmory for Protect / Whirlwind.
2. Switch straight to Skarmory and start attacking.
3. Keep Skarmory away forever because Sand Attack was revealed.
4. Ignore poison and try to trade direct damage immediately.
5. Treat Sand Attack as the endpoint and assume Snorlax cannot convert.

## Answer

Recommendation: Toxic Snorlax with Forretress, then use Skarmory to protect
the poison clock with resistance, Protect, and Whirlwind.

In the replay, Forretress uses Toxic on turn 215 while Snorlax Curses. Fear
then switches Skarmory into Return on turn 216, Protects on turn 217, and
Whirlwinds Snorlax out on turn 218. Snorlax later re-enters through Spikes and
is finished by Tyranitar's Rock Slide plus poison on turn 221.

Why Toxic is the endpoint move:

- Snorlax's Curse / Return / Rest route needs turns. Toxic turns those turns
  into a finite clock.
- Skarmory's job is not to win with repeated Drill Peck through accuracy
  pressure. Its job is to spend Snorlax action turns with resistance, Protect,
  and Whirlwind.
- Sand Attack changed the reliability map, but it did not remove Fear's
  poison, Spikes, Protect, or Whirlwind endpoint.
- Switching Skarmory out after turn 213 means the earlier accuracy drop no
  longer forces Fear to keep using a debuffed active.

Why the alternatives are weaker:

- Switching directly to Skarmory before poison gives Snorlax more Curse or
  Rest freedom.
- Attacking with Skarmory turns the game back into an accuracy-taxed damage
  route when a stronger clock route exists.
- Treating Sand Attack as decisive overstates it. It is support; it still
  needs misses to buy a concrete payoff.

## Second Public State

After turn 219:

```text
melancholy0's Skarmory has used Sand Attack into Fear's Skarmory again.
Fear's Skarmory is no longer the damage endpoint.
Snorlax is poisoned and will re-enter through Spikes if brought back.
Fear has Tyranitar available for direct damage.
```

Expected policy: do not chase repeated low-reliability Skarmory attacks just
because Skarmory is active. Preserve the poison and hazard endpoint, then use
the direct damage piece when Snorlax returns in range.

## Boss Transfer

Use this for Falkner Pidgeotto and other local accuracy positions:

```text
1. Record the current accuracy stage and which Pokemon carries it.
2. Re-score the old attack route under current accuracy.
3. Ask whether switching clears the stage without losing the main route.
4. Name the endpoint: KO range, poison clock, PP route, setup receiver, or
   safe pivot.
5. Do not repeat Sand Attack or a low-accuracy attack unless the next miss or
   hit changes a threshold.
```

Local evidence requirements:

- Local Sand Attack data comes from `data/moves/moves.asm`; it uses
  `EFFECT_ACCURACY_DOWN` and 100 accuracy.
- Local accuracy stages come from `data/battle/accuracy_multipliers.asm`; one
  accuracy drop is a 75% multiplier to the affected move's accuracy.
- Exact boss advice must check local move tables, AI memory, stat-stage reset
  behavior, phazing/Haze timing, switch legality, items, and damage.
- Boss AI may use only public accuracy drops and revealed moves. It may not
  use hidden player bench, hidden moves, or hidden items to decide whether the
  endpoint is safe.

## Lesson

Accuracy disruption is real, but it is not a route by itself. After the drop,
re-score reliability and ask which endpoint is still live. If poison, hazards,
Protect, phazing, switching, or direct damage gives a clearer endpoint, use
that instead of autopiloting either the old attack or the debuff.
