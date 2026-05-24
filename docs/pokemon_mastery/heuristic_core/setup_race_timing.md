# Heuristic: Setup Race Timing

Status: live tiny card.

Use when: Curse, Growth, Drum, Defense Curl, Acid Armor, or repeated setup
competes with attacking, Rest, phazing, or switching.

Rule: do not promote attack, switch, Rest, or more setup until the next-turn
threshold is named.

Write the setup ledger:

- Must-cover setup lane: if the active setup move is legal, the user survives
  to move, and the boost changes a damage, Rest, parity, or phaze threshold,
  include that setup move in top three before deciding whether Rest, damage, or
  switch outranks it.
- Boosts on both sides.
- HP after Leftovers on both sides.
- Last observed damage at the current boost/defense stage.
- Rest/wake turn and Sleep Talk risk.
- Whether phaze is confirmed, strong-prior, or only hoped for.
- What changes after this move: KO range, forced Rest, parity, phaze entry,
  paralysis risk, or a lost setup turn.

Promotion rules:

- Keep using active damage while the target is asleep or reset-locked if the
  next hit changes a Rest, KO, or forced-switch threshold before it wakes.
- Handoff to the setup owner when the next opponent action is the wake/setup
  turn and active damage no longer changes the threshold in time.
- In mirrors, continue setup when behind or tied and damage does not force Rest
  before they can match boosts.
- Attack only when ahead enough that the hit forces Rest, KO, or a defensive
  handoff before the opponent reaches parity.
- Rest only when the next revealed hit or paralysis risk threatens the route;
  do not Rest just because HP is imperfect.
- Switch to the wall/phazer only when the phaze/stability is confirmed enough
  and the mirror is losing, or when staying lets the opponent create an
  irreversible setup lead.

Do not:

- Switch to the setup owner one turn before active damage still matters.
- Stay with damage one turn after the wake/setup turn makes setup ownership
  mandatory.
- Leave a Curse mirror just because a wall exists if the wall's phaze/stability
  is unconfirmed or the mirror can still stay at parity.
- Start attacking from a setup lead unless damage creates a forced threshold.
