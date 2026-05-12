# Boss AI Gym Dossier Future Note

> Status: future design note only. This is not implemented in the ROM, not
> part of the current Boss AI contract, and not permission to add source or
> memory fields without a new explicit task.

## What The Idea Is

A gym dossier would be a limited memory of what leaders have learned about the
player's Pokemon across important fights. The useful version is not "the boss
knows your moveset." It is closer to "the boss has an old note that this species
once showed this kind of threat, and treats that note with caution."

The most valuable fact is per-Pokemon or per-species move memory: which visible
player Pokemon had which revealed or scouted move. Generic global memory is not
very useful because the boss needs to know whether the threat belongs to the
active Pokemon in front of it.

## Why It Is Dangerous

The dossier can make the AI worse if old notes become hard truth. The player can
change movesets between leaders, bring a different member of the same species,
or intentionally bait a leader who always switches away from a remembered
super-effective threat.

The exploit to avoid is:

1. The dossier says Quilava may have Bite.
2. Morty always switches because Bite threatens his Ghost.
3. The player knows this and uses the free turn to set up.

If that happens, the dossier has made the boss predictable and weaker.

## Safe Design Rules

- Dossier facts are hints, not commands.
- Current-battle confirmed revealed moves must matter more than old dossier
  notes.
- A dossier-only threat must never be enough to force a switch by itself.
- The AI must never infer that the player's only moves are the moves already
  seen.
- Old or scouted facts need confidence, freshness, or doubt. If the player has
  clear chances to use the remembered move and repeatedly does not, trust in
  that note should fall.
- Switching away from a dossier threat must be dampened when the player has an
  obvious setup or free-turn punish.
- Repeat fear-switches need loop protection. The player should not be able to
  trigger the same automatic switch over and over.
- The dossier may only use public or authored-scout information. No hidden move
  slots, hidden party reads, held items, private stats, current-turn input, or
  RNG futures.

## Practical Shape If Revisited

The first version should be smaller than the full fantasy:

- Remember broad threat facts, such as damaging move type or special effect
  category, rather than exact complete movesets.
- Attach each remembered threat to a visible species or seen party slot, not to
  a global player profile.
- Feed dossier risk into existing scoring as a small bounded weight.
- Cap its switch-confidence effect so normal public board state still dominates.
- Add anti-bait checks before any switch: current pressure, possible setup,
  sack risk, and recent switch-loop history.
- Add doubt/decay when a remembered move would be useful but is not shown after
  multiple good opportunities.

## Tests Before Any Implementation

Any future implementation should prove these before shipping:

- Dossier-only super-effective memory cannot force a switch.
- Confirmed current-battle revealed moves still influence decisions strongly.
- A stale remembered move loses confidence when repeatedly not used.
- A player setup opportunity reduces dossier-driven switch desire.
- The same remembered threat cannot cause an endless switch loop.
- Normal Boss AI behavior is unchanged when the dossier has no facts.
- Memory budget and no-cheat audits still pass.

## Current Decision

Do not implement this now. The idea is promising, but the wrong version would
make leaders brittle, stale, and exploitable. Revisit only when there is a clear
scenario set and enough memory/ASM budget to represent uncertainty rather than
turning old notes into deterministic decisions.
