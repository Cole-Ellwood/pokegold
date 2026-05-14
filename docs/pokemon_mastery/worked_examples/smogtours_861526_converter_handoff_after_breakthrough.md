# Worked Example: Converter Handoff After Breakthrough

Purpose: practice the turn after a route converter dies. The common mistake is
to call the plan failed because the sweeper fainted. The stronger habit is to
rebuild the blocker map and ask which remaining resource now hands the opened
board to the final converter.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-861526.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-861526.log
- Expert basis: Smogon GSC Spikes article,
  https://www.smogon.com/gs/articles/gsc_spikes

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses after turn 33 of `smogtours-gen2ou-861526`.

```text
underlying:
  Vaporeon has just fainted.
  Golem enters at 94% after Spikes damage and Leftovers.
  Forretress is low but still alive.
  Exeggutor and Snorlax are still available.
  Raikou is statused/asleep from earlier play.
  Spikes are on underlying's side.
  Spikes are also on melancholy0's side.

melancholy0:
  Cloyster fainted.
  Zapdos fainted.
  Snorlax is active at 46% after recoil and Leftovers.
  Skarmory is at 51%.
  Quagsire is at 88%.
  Tyranitar is at 100%.
```

Vaporeon's route status:

- Removed Cloyster, so the opposing Spiker is gone.
- Removed Zapdos, so the Electric answer to Vaporeon and pressure into
  Exeggutor / Golem is gone.
- Forced Snorlax through Rest / Sleep Talk sequences, but did not remove it.
- Died before directly sweeping.

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Rapid Spin with Golem.
2. Immediate Explosion with Golem.
3. Direct damage into Snorlax.
4. Roar immediately.
5. Switch to Snorlax and try to convert now.
6. Preserve everything and wait.

## Answer

Recommendation: Rapid Spin with Golem.

Plan: turn the Vaporeon breakthrough into a final-material route. Vaporeon
removed Cloyster and Zapdos, so the remaining job is to protect the pieces that
can remove Skarmory / Quagsire / Tyranitar and then let Snorlax convert.

Why Rapid Spin is best here:

- Underlying still needs multiple entries or actions from Golem, Forretress,
  Exeggutor, and Snorlax.
- Spikes on underlying's side tax every one of those entries.
- Golem is healthy enough to use the spin turn before the one-time trade
  sequence begins.
- melancholy0's Snorlax is low enough that Rest is a live response, so the
  turn is not automatically won by immediate damage.

Why immediate Explosion is worse:

- Explosion into Snorlax or a switch may remove material before the final
  blocker map is clear.
- The next blockers are not just the active Snorlax. Skarmory, Quagsire, and
  Tyranitar all still affect whether underlying's Snorlax can finish.
- In the replay, Golem's later Explosion is stronger after Rapid Spin and Roar
  have clarified the target map.

Why "Vaporeon died, route failed" is wrong:

- The route changed class. It is no longer a Vaporeon sweep; it is a
  Snorlax-endgame handoff with Golem and Forretress as cleanup resources.
- The correct next action preserves the handoff, not the dead converter.

## Branch Discipline

If Snorlax Rests:

- The spin turn has removed the player's hazard liability while Snorlax spends
  the turn resetting HP.
- Re-score whether Roar, Explosion, Exeggutor pressure, or Snorlax entry best
  converts the sleeping target.

If Skarmory enters:

- Check whether Roar improves the target map or whether Explosion removes the
  Skarmory blocker for Snorlax.

If Quagsire enters:

- Keep Forretress Explosion and Exeggutor pressure in the final-material map.
  Do not spend Golem as though Quagsire were irrelevant.

If Tyranitar enters:

- Decide whether Snorlax's Lovely Kiss / Earthquake route is live, or whether
  another piece must absorb Sandstorm / Earthquake pressure first.

## Boss Transfer

Use this pattern when a boss or player route has already broken the first
layer of defense but the original converter is gone:

```text
1. List what the converter removed.
2. List the remaining blockers to the new closer.
3. Preserve the entries and HP the closer still needs.
4. Spend one-time trades only on blockers the closer cannot beat.
5. Re-score after every Rest, phaze, spin, faint, or switch.
```

Information boundary:

- Player-side coaching can use the visible team state from the recorded
  attempt.
- Boss AI cannot infer hidden player bench answers while deciding whether the
  handoff is winning.

## Lesson

A dead converter can still leave a winning route behind. The next move should
protect and deliver the new closer, not keep playing as if the old converter
must be revived.
