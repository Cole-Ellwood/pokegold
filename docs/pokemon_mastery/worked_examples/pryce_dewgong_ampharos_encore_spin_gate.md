# Worked Example: Pryce Dewgong vs Ampharos Encore Spin Gate

Purpose: convert Pryce's Dewgong route from a generic "watch for Encore and
Rapid Spin" warning into exact player-side advice. The player can know Pryce's
boss roster from documentation, but Pryce's AI cannot know unrevealed player
team information. This drill therefore uses only public battle state, revealed
player moves, source-known boss data, and local damage evidence.

Information model: there is no Gen 2 or Gym Leader Lab Team Preview. A
player-side route sheet may use the documented Pryce roster because the boss is
known from source/research, but Pryce's AI must make decisions from revealed
player-side battle state.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- Pryce route map: `../boss_route_maps/pryce_turn1_route_sheet.md`
- Pryce roster source: `data/trainers/parties.asm`
- Encore source: `engine/battle/move_effects/encore.asm`
- Rapid Spin source: `engine/battle/move_effects/rapid_spin.asm`
- Move data source: `data/moves/moves.asm`
- Ampharos and Dewgong local types/stats:
  `data/pokemon/base_stats/ampharos.asm` and
  `data/pokemon/base_stats/dewgong.asm`
- Damage evidence checked with `python -m tools.damage_debugger.matchup`.

Local mechanic notes:

- Dewgong's known move set is Rapid Spin / Surf / Ice Beam / Encore.
- Encore can fail if the last opposing move is invalid, missing from the
  target's move list, has no PP, missed, or the target is already Encored.
- A successful Encore sets a 3-6 turn lock.
- Rapid Spin is not decorative support in this hack; it clears all Spikes
  layers.

## Public State

```text
Pryce active:
  Dewgong Lv31 at 41%, NeverMeltIce
  Known moves: Rapid Spin / Surf / Ice Beam / Encore

Pryce bench:
  Sneasel at 100%
  Piloswine at 63%
  Slowking at 68%

Player active:
  Ampharos Lv34 at 80%
  Revealed moves: ThunderPunch / Thunder Wave
  Tackle known from prior route notes if still retained

Field:
  No weather
  No screens
  Player hazards may matter only if Dewgong gets to spin

Public prior:
  Ampharos used or threatened a support/status line earlier in the sequence.
  Dewgong is now low enough that an immediate attack can remove it.
```

Damage anchors:

```text
Ampharos ThunderPunch -> Dewgong at 41%:
  84-99 damage, guaranteed KO from current HP.

Ampharos Tackle -> Dewgong at 41%:
  13-16 damage, 28-35% of Dewgong's current HP.

Dewgong Ice Beam -> Ampharos at 80%:
  52-62 damage, 45-53% of Ampharos's current HP.

Dewgong Surf -> Ampharos at 80%:
  8-10 damage, 7-9% of Ampharos's current HP.
```

These debugger ranges do not price NeverMeltIce unless the tool output shows
the held item. The conclusion here does not depend on the item boost:
ThunderPunch removes Dewgong before Dewgong's Ice Beam, Surf, Encore, or Rapid
Spin branch matters, assuming Ampharos acts first and is not stopped by status.

## Live-Turn Advice

Recommendation: ThunderPunch. Confidence: high if Ampharos is able to act
before Dewgong, ThunderPunch has PP, and the player does not have a confirmed
better Piloswine-punish switch.

Plan: remove Dewgong now so it cannot convert the turn into Rapid Spin or
Encore tempo. Re-score only after seeing whether Pryce lets Dewgong faint or
pivots to Piloswine.

State read: Dewgong is not just a Water/Ice target. It is Pryce's spin and
Encore piece. If Ampharos chooses another support move, weak chip, hazard
reset, or passive scouting line, Dewgong can turn the visible last move into a
3-6 turn lock or clear the hazard route before the player has converted it.

Candidate ranking:

1. ThunderPunch: best. It KOs Dewgong from the public HP and denies both Rapid
   Spin and Encore.
2. Switch or double-switch to a Piloswine answer: acceptable only if Piloswine
   is strongly expected and the user's answer is verified from public state.
3. Thunder Wave: usually bad here. It does not remove the active spin/Encore
   route and can become the exact low-value move Dewgong wants to lock.
4. Tackle or weak chip: bad. It leaves Dewgong alive with all route tools.
5. Hazard, setup, recovery, or passive scouting: bad unless the player has
   already named why Encore on that exact move and a full Rapid Spin clear do
   not matter.

Opponent's best route: if Pryce stays, Dewgong wants the player to spend the
turn on Thunder Wave, hazards, or another low-value move so Encore or Rapid
Spin changes the board. If Pryce switches, Piloswine is the likely punishment
for ThunderPunch and asks the next-turn Earthquake question.

Worst plausible branch: the player sees Dewgong as passive, clicks Thunder
Wave or another setup/support action, and gives Pryce a free route: Encore the
support move, spin hazards away, or Ice Beam before Ampharos has converted the
KO.

Key piece: Ampharos is the immediate Dewgong remover, not automatically the
Piloswine answer. Its job can end after ThunderPunch if Pryce pivots correctly.

What changes the answer:

- Ampharos is paralyzed, slower, confused, asleep, out of ThunderPunch PP, or
  otherwise unable to act before Dewgong.
- Dewgong is above ThunderPunch KO range.
- Pryce's Piloswine pivot is so obvious and so punishable that a verified
  double-switch gains more than taking the active KO.
- The player has no answer to Piloswine after ThunderPunch and must preserve
  Ampharos differently.
- The last player move cannot legally be Encored, or repeating it remains
  route-positive while locked.
- Hazards are irrelevant to the user's route, reducing Rapid Spin's value.

Next turn if it works:

- If Dewgong faints, choose the next move from Pryce's replacement route.
  Piloswine asks for Earthquake/Roar survival and a pivot plan. Sneasel asks
  for fast cleanup prevention. Slowking asks whether ThunderPunch still forces
  Rest or KO.
- If Piloswine enters on ThunderPunch, do not keep Ampharos in by inertia.
  Check exact coverage, speed, and Earthquake survival before acting.

## Scorecard

```text
mechanics and public-state accuracy: 4/4
route and win-condition clarity: 4/4
candidate ranking with resource gain and cost: 4/4
worst plausible branch identified: 3/3
preservation or expendability reasoning: 2/2
answer-changing information: 2/2
concise recommendation grounded in the state: 1/1
total: 20/20 for the abstract drill
```

Caps that would apply in a real battle:

- Pryce's AI does not know the player's full team, so boss-side policy must not
  assume a hidden Piloswine answer unless the relevant player-side information
  has been revealed.
- Human coaching can use the user's full team only when the user has provided
  it or the recorded attempt makes it visible.
- The boss AI must not use unrevealed player moves, items, or bench Pokemon to
  decide whether Encore, Rapid Spin, or Piloswine is best.
- If a recorded attempt shows different HP, speed modifiers, status, hazard
  state, or move PP, rerun the damage and route check.

## Lesson Extracted

Encore and Rapid Spin are route moves only when the current state lets them
change the route. In this state, the cleanest answer is not to "play around"
Encore with more support. It is to remove Dewgong with the guaranteed KO, then
respect Pryce's next revealed route.
