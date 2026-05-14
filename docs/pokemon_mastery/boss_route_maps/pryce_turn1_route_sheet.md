# Pryce Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, and items are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Foresight source: Smogon, Borat's GSC guide; apply the "so what?" test to
  every early hazard, damage, pivot, and Explosion line.
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Pryce as adaptive first-three: Cloyster / Dewgong / Sneasel.
- Cloyster, Dewgong, Sneasel, Piloswine, and Slowking local stats/types:
  `data/pokemon/base_stats/*.asm`
- Rapid Spin source: `engine/battle/move_effects/rapid_spin.asm`; clears both
  Spikes bits, so it removes all layers.
- Roar / priority caveat:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; do not import modern
  Roar priority assumptions.
- Recovery source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Rest
  fully heals and creates a sleep-cycle window.
- Slowking / Ampharos preservation example:
  `docs/pokemon_mastery/worked_examples/pryce_slowking_ampharos_preservation.md`
- Dewgong / Ampharos exact player-side example:
  `docs/pokemon_mastery/worked_examples/pryce_dewgong_ampharos_encore_spin_gate.md`

Boss roster:

```text
Lv30 Cloyster @ NEVERMELTICE:
  Spikes / Surf / Ice Beam / Explosion

Lv31 Dewgong @ NEVERMELTICE:
  Rapid Spin / Surf / Ice Beam / Encore

Lv32 Sneasel @ BLACKGLASSES:
  Faint Attack / Ice Punch / Shadow Ball / Quick Attack

Lv34 Piloswine @ SOFT_SAND:
  Earthquake / Blizzard / Rock Slide / Roar

Lv33 Slowking @ LEFTOVERS:
  Surf / Psychic / Thunder Wave / Rest
```

Boss likely openings:

- Pryce is source-listed as adaptive first-three, not fixed Cloyster.
- Plan for Cloyster / Dewgong / Sneasel, with Cloyster favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Pryce's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Cloyster route:

- Goal: set early Spikes, pressure with Water/Ice damage, then threaten
  Explosion once the hazard job or emergency-stop job is worth cashing out.
- What it punishes: letting the first layer land for free, then switching
  repeatedly through grounded hazards without a spin plan.
- Denial idea: if Cloyster can be removed or forced out before Spikes, do it.
  If Spikes lands, immediately decide whether the route is to spin, pressure
  Dewgong, or play through the hazard clock. Do not forget Explosion.

Dewgong route:

- Goal: remove the player's hazards with Rapid Spin and disrupt sequencing with
  Encore.
- What it punishes: hazard plans that have no retention pressure and setup moves
  that can be Encored.
- Denial idea: if our win route depends on hazards, do not treat "I set Spikes"
  as progress until Dewgong's spin turn is answered. If our team is taking
  heavy grounded switch damage, preserving our spinner or forcing Dewgong out
  can matter more than chip.

Dewgong Encore check:

- Before recommending hazards, setup, recovery, or passive scouting into
  Dewgong, name the exact last move Dewgong can Encore and the 3-6 turn route it
  opens.
- If the locked move lets Dewgong spin for free, pivot to Piloswine/Sneasel, or
  hand Slowking a clean Rest/stabilize turn, the support move is suspect even if
  it is normally good.
- If the locked move still forces damage, denies spin, or creates a route while
  repeated, Encore is a cost to price rather than an automatic veto.
- If Dewgong is already in a verified KO range, removing it can be better than
  inventing another anti-Encore line. The Ampharos drill shows this exact
  player-side case.

Sneasel route:

- Goal: convert chip into fast cleanup with Dark/Ice/Ghost coverage and Quick
  Attack.
- What it punishes: over-spending bulky answers earlier in the hazard war, then
  leaving a fast cleaner with priority to finish.
- Denial idea: keep a fast check or bulky answer healthy enough after Spikes.
  Type words here are romhack-sensitive; check the local chart before claiming
  a safe resist or immunity.

Piloswine route:

- Goal: apply Ground/Ice/Rock coverage and Roar opponents through Spikes.
- What it punishes: passive recovery or setup lines that let Roar plus hazards
  erase progress.
- Denial idea: verify whether phazing works in the current speed/timing state,
  then decide whether to attack, pivot, or remove hazards before Piloswine gets
  repeated Roar value.

Slowking route:

- Goal: stabilize with bulk, Thunder Wave, Leftovers, and Rest while hazards and
  prior chip make the player's switches worse.
- What it punishes: rushing damage that fails to force Rest at the right time,
  or letting paralysis make the Sneasel/Piloswine cleanup easier.
- Denial idea: force Rest only when the sleep turns can be punished. If Rest
  merely resets the board while Spikes remain against the player, the damage did
  not cash out.

## Player Plan Template

Primary route:

- Decide the hazard war early: either prevent Cloyster's layer, remove it with
  a preserved spinner, or accept the layer and stop switching as though it were
  free.

Backup route:

- If hazards go up and cannot be removed, shift to shorter routes: direct KO
  thresholds, forced Rest punish, or preserving the exact piece that stops
  Sneasel/Piloswine cleanup.

Best lead profile:

- A lead that pressures Cloyster, does not donate free Rapid Spin/Encore value
  to Dewgong, and does not lose control if Sneasel opens with fast coverage or
  Quick Attack cleanup pressure. It must not be the only Piloswine answer.
- A spinner lead is good only if it can still spin after Cloyster's pressure
  and Dewgong's presence are accounted for.

Avoid as lead:

- A hazard setter whose layers are immediately erased by Dewgong with no punish.
- A passive setup lead that gets Encored, Roared, or forced through Spikes.
- The only Sneasel/Piloswine answer if Cloyster can explode or chip it early.

First-turn question:

```text
Which adaptive opener appeared?

Cloyster: can we deny Spikes or make Explosion a bad trade before the hazard
clock starts?

Dewgong: is Rapid Spin, Encore, Surf, or Ice Beam the live route, and does our
lead punish it instead of donating a reset?

Sneasel: can we prevent fast coverage or Quick Attack cleanup pressure without
spending the Piloswine answer?
```

## Foresight Ladder Checkpoints

Use this before approving a turn-1 move. The move must name the next board and
the route after that.

Damage into Cloyster:

- Next board required: Cloyster is removed, forced low enough that Explosion is
  a bad trade, or denied enough freedom that the first layer cannot become both
  hazard pressure and later boom pressure.
- Route after that: Dewgong, Sneasel, Piloswine, or Slowking is met with the
  correct preserved answer instead of with a team already paying Spikes tax.
- Failure sign: the attack only creates chip while Cloyster still sets Spikes
  and keeps Explosion as a useful trade.

Setting our hazards:

- Next board required: Pryce is forced to pay for Dewgong's Rapid Spin turn, or
  the layer immediately creates a KO, Rest, phaze, or forced-switch threshold.
- Route after that: hazards help punish Pryce's switches or Rest cycles before
  Sneasel / Piloswine cleanup becomes live.
- Failure sign: Dewgong spins all layers for free, so the first turn only
  donated tempo.

Pivoting:

- Next board required: the pivot preserves the lead's later job while entering
  the piece that handles Pryce's most urgent route.
- Route after that: the new active either denies Spikes, punishes spin/Encore,
  pressures Slowking's Rest, or keeps the Sneasel/Piloswine answer intact.
- Failure sign: the pivot is the only Sneasel or Piloswine answer and gets
  chipped before that route appears.

Forcing Slowking Rest later:

- Next board required: Slowking is asleep or forced to heal while the player
  has a concrete punish turn.
- Route after that: use the sleep window for setup, hazards, item pressure,
  phazing, or safe entry, not just more chip that Rest erases.
- Failure sign: Slowking Rests, Pryce still owns the hazard clock, and the
  player has no route that uses the sleep turns.

Spending a one-time resource:

- Next board required: the spent move, Explosion absorber, or sacrifice removes
  a route blocker or creates clean entry for a named converter.
- Route after that: the converter can act before Sneasel, Piloswine, or
  Slowking rebuilds the board.
- Failure sign: the trade wins the visible exchange while losing the only
  answer to Pryce's next route.

If Cloyster sets Spikes:

- Re-score around layer count, grounded team members, Dewgong's spin role, and
  whether Cloyster still has Explosion value.

If Dewgong opens, enters, or spins:

- Do not simply re-set hazards unless the next layer will stay or force
  immediate route progress.
- Before using setup, recovery, or hazards into Dewgong, name the Encore branch
  and whether it lets Pryce spin, pivot, or stabilize for free.

If Sneasel opens or enters:

- Check whether the current lead is still allowed to take Faint Attack, Ice
  Punch, Shadow Ball, or Quick Attack chip. Do not spend the Piloswine or
  Slowking answer just to win the visible Sneasel exchange.

Worst plausible branch:

- The player lets Cloyster set Spikes, fails to remove them, loses the spinner
  or Ground/Ice answer to Explosion or chip, then Piloswine and Slowking turn
  forced switches, Roar, Thunder Wave, and Rest into a long-game loss.

Abandon conditions:

- Our grounded core can no longer switch enough times through current Spikes.
- Dewgong can spin for free and our hazard plan has no punish.
- Cloyster's Explosion would remove an irreplaceable piece.
- Piloswine has a live Roar plus hazard route.
- Slowking can Rest without giving us a punish turn.
- Type-chart, passive, or damage evidence contradicts the assumed matchup.

Snorlax study transfer:

- Pryce is a hazard-control lesson, not a Snorlax lesson. The transferable GSC
  concept is that passive damage must be converted through phazing, forced Rest,
  spin pressure, or route thresholds. In the romhack, three-layer Spikes make
  this more urgent, but Rapid Spin removing all layers means the plan must also
  explain how the layers stay.
