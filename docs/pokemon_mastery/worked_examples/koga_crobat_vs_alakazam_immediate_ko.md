# Worked Example: Koga Crobat vs Alakazam

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_koga_crobat_vs_alakazam_immediate_ko_001`

Mechanics profile: `romhack_gym_leader_lab`

Purpose: practice when immediate damage conversion beats slow pressure.

## Public State

Koga:

- Active: Crobat level 44, 57%, no status, Sharp Beak.
- Moves: Wing Attack, Toxic, Confuse Ray.
- Role: fast ace that can cash out a direct KO.
- Bench: Tentacruel, Muk, Nidoking, Umbreon.

Player:

- Active: Alakazam level 44, 51%, no status.
- Revealed moves: Psychic, Recover.
- Plausible hidden move: ThunderPunch.
- Role: fast recovery attacker that punishes slow clocks.

Damage evidence:

- Crobat Wing Attack into Alakazam: 54-64%, guaranteed KO from 51%.
- Alakazam Psychic into Crobat: 53-62%, possible KO from 57%.
- Recover can erase slow chip if Alakazam survives.

## Live Advice

Recommendation:

- Use Wing Attack.

Plan:

- Remove Alakazam immediately before Psychic or Recover can punish slower
  pressure, then re-score the next player switch with Crobat still available if
  the damage outcome permits.

Why this move:

- Toxic and Confuse Ray both leave Alakazam alive. If Alakazam lives, it can
  either threaten Crobat with Psychic or erase chip with Recover. Public damage
  says Wing Attack removes that branch now.

Opponent's best route:

- Survive the turn, then use Psychic to remove Crobat or Recover to reset the
  damage race.

Worst plausible branch:

- The public KO threshold is wrong: if Wing Attack does not KO, Crobat may be
  exposed to Psychic. If the threshold disappears, Umbreon becomes the
  preservation route.

Key piece:

- Crobat is the fast converter right now. Umbreon is the fallback public answer
  if Crobat cannot remove Alakazam immediately.

What changes the answer:

- If Wing Attack no longer KOs, pivot Umbreon or re-score around preservation.
- If Crobat is slower, the direct-KO line must be checked against Psychic first.
- If Alakazam is already statused or cannot Recover, Toxic may regain value in
  some non-KO states.
- If Umbreon is unavailable or threatened by a revealed move, the fallback
  changes.

Next turn if it works:

- After Alakazam faints, identify the next switch's best route before choosing
  whether Crobat should stay, pivot, or be preserved.

## Oracle Check

The hidden oracle labels Wing Attack as best and Umbreon as acceptable only if
the KO threshold is absent. Toxic and Confuse Ray are catastrophic in the public
state because they spend a guaranteed removal turn on slow or swingy pressure.

This example supports the damage-threshold recipe: direct damage is not shallow
when it removes the route that would otherwise recover, retaliate, or set up.
