# Worked Example: Baton Pass Phaze Endpoint

Purpose: practice anti-support-chain advice. The common shortcut is "use Roar"
or "phazing beats Baton Pass." The stronger answer names the passer, the
receiver map, the control user's HP/PP, and the endpoint where resetting turns
into damage.

Source:

- Replay review: `../reviews/2026-05-13_smogtours-gen2ou-861549.md`
- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-861549.log
- Expert basis: Smogon Baton Pass Chain article,
  https://www.smogon.com/rs/articles/baton_pass

Format: vanilla GSC OU strategic review. Transfer to Gym Leader Lab only after
local mechanics validation.

## Public State

This prompt pauses before turn 108 of `smogtours-gen2ou-861549`.

```text
melancholy0:
  Tyranitar is active at 74% after Leftovers.
  Revealed moves: Roar / Curse / Rock Slide.
  Tyranitar has repeatedly Roared Espeon pass attempts.
  Skarmory is still alive as a bulky fallback.

underlying:
  Espeon is active at 77% after Leftovers.
  Revealed moves: Growth / Baton Pass.
  Zapdos is sleeping at 80%.
  Golem and Snorlax are also still possible receivers.

Field:
  No active Spikes pressure on melancholy0's side.
  The pass route has been reset several times, but Espeon can still restart it.
```

Route status:

- Espeon is the support source.
- Zapdos is the dangerous special receiver.
- Golem and Snorlax are alternate receivers or pivots.
- Tyranitar is the anti-pass control piece and also the potential damage
  endpoint.

## Live-Turn Question

What should the advisor prioritize now?

Candidate classes:

1. Roar again.
2. Rock Slide the likely receiver.
3. Curse again.
4. Switch to Raikou or Skarmory.
5. Preserve Tyranitar and wait.

## Answer

Recommendation: Rock Slide if the receiver branch is likely and Tyranitar
survives the return hit; otherwise Roar remains the reset move.

In the replay, Espeon Baton Passes to Zapdos on turn 108 and Tyranitar Rock
Slide takes Zapdos from 80% to 17%. Zapdos wakes and Thunders on turn 109, but
Tyranitar survives and KOs with Rock Slide.

Why attacking rises here:

- Roar has already proved it can reset the pass route, but Espeon can keep
  restarting while it remains alive and while receivers remain available.
- Zapdos is in a damage band where Rock Slide creates an endpoint.
- Tyranitar has enough HP to survive the immediate Zapdos branch in the replay.
- Another Roar could reset the board without removing the receiver, extending
  the same problem.

Why Roar was correct earlier:

- Before the receiver was in range, direct damage risked letting a boosted
  receiver act.
- Repeated Roar preserved the game state while Tyranitar recovered and the
  receiver map became clearer.
- The control move was a bridge to the endpoint, not the endpoint itself.

## Branch Discipline

If Espeon passes to Zapdos:

- Attack if damage plus survival wins the receiver exchange.
- Roar if Zapdos is not in range or Tyranitar cannot survive the return hit.

If Espeon passes to Golem:

- Re-check Earthquake damage and whether Skarmory can absorb the branch.
- Roar may be stronger if Golem cannot be removed quickly.

If Espeon stays and Growths:

- Decide whether another Growth makes the next pass unmanageable. Damage into
  Espeon, Roar, or pivoting can all be correct depending on HP and turn order.

If Tyranitar is low:

- Preserve it only if another answer can cover the current receiver. A dead
  phazer cannot be the endpoint.

## Boss Transfer

Use this for Bugsy Ledian and Sabrina Espeon positions:

```text
1. Name the support source.
2. Name the receivers and the one that actually wins.
3. Check whether phazing, Haze, Encore, status, or attack resolves locally.
4. Preserve the control piece's HP/PP until the endpoint exists.
5. Switch from reset to damage when the receiver is in range.
```

Local evidence requirements:

- Bugsy Ledian has Reflect / Quiver Dance / Leech Life / Baton Pass.
- Sabrina Espeon has Hidden Power / Psychic / Morning Sun / Baton Pass.
- Local Baton Pass behavior comes from
  `engine/battle/move_effects/baton_pass.asm`.
- Local Quiver Dance and screen timing must be checked before exact advice.
- Boss AI must not use unrevealed player-team knowledge to infer hidden Haze,
  phazing, Encore, or receiver answers.

## Lesson

Anti-pass advice is not "click Roar until the game ends." It is reset, preserve
the resetter, identify the receiver that matters, then attack when the receiver
is finally in range.
