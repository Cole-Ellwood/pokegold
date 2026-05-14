# Worked Example: Morty Misdreavus vs Typhlosion

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_morty_misdreavus_vs_typhlosion_perish_route_001`

Mechanics profile: `romhack_gym_leader_lab`

Purpose: practice forced-clock control against a boosted attacker.

## Public State

Morty:

- Active: Misdreavus level 24, 63%, no status, Spell Tag.
- Moves: Confuse Ray, Psywave, Perish Song.
- Role: control piece that can force a boosted target off the board.
- Bench: Gengar.

Player:

- Active: Typhlosion level 28, 84%, no status.
- Revealed moves: Flame Wheel, Swift.
- Plausible hidden moves: Sunny Day, Fire Punch or stronger Fire coverage.
- Boosts: +1 Attack.
- Role: boosted Fire-pressure attacker.

Damage evidence:

- Flame Wheel into Misdreavus: 46-55%, never KOs from 63%.
- Swift into Misdreavus: no useful damage in the public fixture evidence.
- Psywave into Typhlosion: variable and not a KO route from 84%.

## Live Advice

Recommendation:

- Use Perish Song.

Plan:

- Force the boosted Typhlosion to leave or lose to the countdown, then re-score
  the new board instead of trying to win the turn with variance.

Why this move:

- Confuse Ray is swingy and Psywave is low-certainty chip. Perish Song changes
  the opponent's route: Typhlosion cannot simply stay boosted and keep attacking
  without accepting a hard timer.

Opponent's best route:

- Keep Typhlosion active at +1 and pressure Misdreavus before Morty starts a
  forced clock.

Worst plausible branch:

- Hidden stronger Fire coverage means Misdreavus no longer survives the control
  turn. If that becomes public, switch or find another route instead of clicking
  Perish Song.

Key piece:

- Misdreavus is the current control piece. Gengar is the fallback Ghost route if
  Misdreavus cannot safely start the clock.

What changes the answer:

- If Misdreavus no longer survives Flame Wheel or revealed Fire coverage,
  preserve through Gengar.
- If Typhlosion is no longer boosted, Perish Song may be too slow.
- If Typhlosion is already in direct KO range, attack can replace the clock.
- If Gengar is unavailable, the cost of losing Misdreavus rises.

Next turn if it works:

- Re-score after the countdown starts. If Typhlosion switches, identify the new
  active route. If it stays, preserve the Ghost route while the timer does its
  job.

## Oracle Check

The hidden oracle labels Perish Song as best and switching Gengar as acceptable.
Confuse Ray and Psywave are catastrophic because they do not force the boosted
attacker off the board or remove the route.

This example supports the forced-control recipe: control moves are strongest
when they change the opponent's future choices, not when they merely make the
current turn messy.
