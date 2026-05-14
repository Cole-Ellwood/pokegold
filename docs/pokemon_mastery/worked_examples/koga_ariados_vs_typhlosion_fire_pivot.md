# Worked Example: Koga Ariados vs Typhlosion

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_koga_ariados_vs_typhlosion_fire_spikes_001`

Mechanics profile: `romhack_gym_leader_lab`

Purpose: practice preservation pivoting when the active Pokemon's long-game
tools cannot convert before a public lethal punish.

## Public State

Koga:

- Active: Ariados level 40, 100%, no status, Leftovers.
- Moves: Spikes, Toxic, Leech Life.
- Role: hazard and poison lead with future route value if preserved.
- Bench: Tentacruel, Muk, Nidoking, Umbreon, Crobat.

Player:

- Active: Typhlosion level 45, 100%, no status.
- Revealed move: Flamethrower.
- Public prior: Earthquake plausible.
- Role: faster Fire-pressure attacker.

Damage evidence:

- Typhlosion Flamethrower into Ariados: 149-176%, guaranteed KO.
- Ariados Leech Life into Typhlosion: 14-17%, never decisive.

## Live Advice

Recommendation:

- Switch to Tentacruel.

Plan:

- Preserve Ariados's future hazard/status utility instead of spending it into a
  faster guaranteed KO, then re-score Typhlosion's Fire and Earthquake branches
  from the pivot.

Why this move:

- Spikes and Toxic are normally Koga's long-game tools, but here they do not
  convert before Flamethrower removes Ariados. Tentacruel is the cleanest public
  pivot into the revealed Fire route; Umbreon is the lower-fit fallback.

Opponent's best route:

- Click the revealed lethal Fire move and remove Ariados before Koga starts
  hazard or poison pressure.

Worst plausible branch:

- Typhlosion predicts Tentacruel and uses a plausible Earthquake. That must be
  re-scored after the switch, but it does not make staying in and donating
  Ariados to confirmed Flamethrower correct.

Key piece:

- Ariados is not the whole game, but it is still an unspent utility piece.
  Tentacruel is the current best visible preservation pivot.

What changes the answer:

- If Tentacruel is unavailable or too low, Umbreon may become the preserving
  pivot.
- If Flamethrower is out of PP, unavailable, or no longer lethal by exact
  damage, Spikes or Toxic can be re-scored.
- If Typhlosion is in guaranteed KO range before moving, attack can rise.
- If Ariados is no longer needed and sacrificing it opens a forced route, staying
  in can be reconsidered.

Next turn if it works:

- Re-score from Tentacruel. If Typhlosion stays on Fire pressure, punish or
  stabilize. If Earthquake is revealed, update the pivot map and do not pretend
  the first switch solved the matchup.

## Oracle Check

The hidden oracle labels Tentacruel as best and Umbreon as acceptable. Spikes,
Toxic, and Leech Life are catastrophic because they leave Ariados in against a
faster guaranteed KO before the long-game tool can convert.

This example supports the preservation-pivot recipe: switching is strong when
it preserves a useful role from an immediate punish and creates a cleaner next
state. It is weak when it only delays a problem without protecting a route.
