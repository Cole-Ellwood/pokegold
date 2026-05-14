# Worked Example: Bugsy Scyther vs Quilava

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_bugsy_scyther_vs_quilava_fire_setup_001`

Mechanics profile: `romhack_gym_leader_lab`

Purpose: practice the live boss-turn advice template on a non-Snorlax setup
position using public state.

## Public State

Bugsy:

- Active: Scyther level 17, 81%, no status, Silverpowder.
- Moves: Quick Attack, Wing Attack, Swords Dance.
- Speed: faster than Quilava.
- Role: ace and setup route.
- Bench: Ariados, Ledian.

Player:

- Active: Quilava level 17, 69%, no status.
- Revealed moves: Ember, Quick Attack.
- Public prior: Fire STAB remains available.

Damage evidence:

- Unboosted Wing Attack into Quilava: 49-58%, never KOs from 69%.
- +2 Wing Attack into Quilava: 95-114%, possible KO.
- Quilava Ember into Scyther: 71-84%, never KOs from 81%.

## Live Advice

Recommendation:

- Use Swords Dance.

Plan:

- Turn Scyther from chip attacker into the win-condition piece by taking the
  survivable Ember branch, then converting with boosted Wing Attack.

Why this move:

- Wing Attack now does not KO, so immediate damage still lets Quilava fire back.
  Swords Dance changes the two-turn route: Scyther survives the public Fire
  punish and threatens to remove Quilava next turn while staying boosted.

Opponent's best route:

- Quilava should use Ember or another Fire attack to stop Scyther before it can
  convert.

Worst plausible branch:

- The setup line fails if the Fire move is stronger than public Ember damage, if
  Scyther is slower than believed, or if the damage roll leaves Quilava outside
  boosted Wing Attack plus follow-up range.

Key piece:

- Scyther is Bugsy's ace and current converter. Preserve it in general, but do
  not switch here because the public setup window is live and Ledian enters the
  same Fire pressure.

What changes the answer:

- If Ember or hidden Fire coverage KOs after Swords Dance, attack immediately.
- If unboosted Wing Attack already KOs, take the KO.
- If Scyther is slower, do not assume the boosted line converts.
- If Quilava has a switch-in that blanks boosted Wing Attack and punishes
  Scyther, re-score.

Next turn if it works:

- Use boosted Wing Attack unless new information shows Quilava survives or a
  better forced line appears.

## Oracle Check

The hidden oracle also labels Swords Dance as best and Wing Attack as
acceptable. Quick Attack and switching to Ledian are catastrophic because they
give up the live setup route without solving the Fire-pressure problem.

This example supports the setup-window recipe: setup is correct only when the
punish is survivable and the boost changes a concrete route.
