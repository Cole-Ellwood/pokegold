# Boss Live-Turn Prompt Cards

Status: training material, not sealed benchmarks. These cards bridge local boss
route maps into live move-choice practice. They intentionally omit the user's
team; fill that layer before giving final advice.

Use with `../boss_turn_advice_template.md`.

## Card 001: Misty Adaptive Opening

Source route map: `../boss_route_maps/misty_turn1_route_sheet.md`

Policies tested: `STP-002`, `STP-004`, `STP-009`, `STP-010`, `STP-012`.

Public state:

```text
Boss may open Politoed, Starmie, or Quagsire.

Politoed threatens Rain Dance / Hypnosis / Surf / Ice Beam.
Starmie threatens Recover / Hydro Pump / Psychic / Thunder.
Quagsire threatens Curse / Earthquake / Surf / Rest.

Player has one strong Water answer, one faster cleaner, and one bulky pivot.
Only one of those reliably handles Starmie after rain-accurate Thunder.
```

Required live answer:

```text
Recommendation:
State read:
Win condition:
Candidate ranking:
Worst plausible branch:
What changes the answer:
Next turn if it works:
```

Expected arbitration:

- Do not lead or pivot the only Starmie/Lapras answer into Politoed sleep
  unless sleep occupation itself is the route.
- If Starmie opens, the first question is whether the player can cross a
  threshold before Recover, status it, or force a bad Recover turn.
- If Quagsire opens, deny Curse before treating Misty as a pure special Water
  fight.

Answer flip:

- If the Water answer is duplicated, absorbing Politoed Hypnosis becomes more
  acceptable.
- If the cleaner loses to Lanturn Thunder Wave, preserving its status matters
  more than early damage.
- If the player has Haze, Encore, strong Grass pressure, or verified Electric
  damage, Quagsire or Starmie priority changes.

Failure signs:

- "Lead the Grass/Electric because it hits Water."
- "Sleep fodder the bulky Water" without checking later Starmie/Lapras jobs.
- "Just chip Starmie" when Recover erases the exchange.

## Card 002: Misty Starmie Recover Turn

Source route map: `../boss_route_maps/misty_turn1_route_sheet.md`

Policies tested: `STP-004`, `STP-006`, `STP-009`, `STP-011`.

Public state:

```text
Starmie is active at mid HP and can Recover.
Rain is either active or one turn from expiring.
The player's active can attack for chip, switch to a stronger answer, use
status/control, or preserve the active for Quagsire/Lapras later.
```

Expected arbitration:

- Damage is good only if it forces Recover at a punishable time, crosses a KO
  or revenge threshold, or prevents Starmie from using coverage freely.
- Switching is good only if the entry is real after rain/Thunder/Psychic
  damage and does not spend the later Quagsire or Lapras answer.
- Status/control rises if it turns Recover into an entry or setup window.

Answer flip:

- Rain expiring makes some pivots safer.
- Starmie below a true KO threshold can make attacking better than preserving.
- If Quagsire is still unhandled, spending the only physical-anchor answer on
  Starmie can lose the next route.

## Card 003: Blue Adaptive Opening

Source route map: `../boss_route_maps/blue_turn1_route_sheet.md`

Policies tested: `STP-004`, `STP-009`, `STP-010`, `STP-011`, `STP-012`.

Public state:

```text
Boss may open Pidgeot, Porygon2, or Gyarados.

Pidgeot is Choice Band and may reveal its lock.
Porygon2 can Recover and attack with Tri Attack / Thunderbolt / Ice Beam.
Gyarados can Dragon Dance and threaten Outrage / Surf / Hyper Beam.

Player has one anti-Gyarados route, one fast cleaner, and one bulky physical
answer. The fast cleaner is vulnerable to Quick Attack or ExtremeSpeed range
later.
```

Expected arbitration:

- Lead choice must cover Pidgeot lock, Porygon2 stabilization, and Gyarados
  Dragon Dance without spending the only Gyarados answer.
- If Pidgeot opens, record the lock before pivoting.
- If Porygon2 or Gyarados opens, abandon the Pidgeot-only script immediately.

Answer flip:

- A duplicated Gyarados answer permits more aggressive Pidgeot punishment.
- If the current active can deny Dragon Dance and still handle Arcanine
  priority later, anti-setup rises.
- If Porygon2 cannot be broken before Recover, status, PP, setup denial, or
  route handoff outranks chip.

Failure signs:

- "Punish the lead" without preserving Gyarados/Arcanine answers.
- Treating Choice Band lock as known before Pidgeot reveals the move.
- Letting Porygon2 Recover-loop because the move did visible damage once.

## Card 004: Blue Gyarados After Dragon Dance

Source route map: `../boss_route_maps/blue_turn1_route_sheet.md`

Policies tested: `STP-006`, `STP-008`, `STP-009`, `STP-011`.

Public state:

```text
Gyarados has used Dragon Dance.
Player can attack, phaze/Haze/status if available, sacrifice into a revenge
entry, or pivot to the preserved answer.
Tauros, Rhydon, and Arcanine remain unrevealed or not fully solved.
```

Expected arbitration:

- The immediate question is whether boosted Gyarados becomes irreversible next
  turn. If yes, denial outranks slow value.
- Sacrifice is legal only if it creates a clean answer entry and does not spend
  the piece needed for Tauros/Rhydon/Arcanine.
- Do not assume Hyper Beam recharge is punishable unless the user stays active
  and the next action converts.

Answer flip:

- If phazing/Haze is healthy and legal, control can dominate.
- If the answer dies to +1 damage after hazards or chip, it is no longer a
  hard switch.
- If Gyarados is already in revenge range, attack or priority may outrank a
  risky pivot.

## Card 005: Lance Serial Setup Budget

Source route map: `../boss_route_maps/lance_turn1_route_sheet.md`

Policies tested: `STP-006`, `STP-008`, `STP-009`, `STP-010`, `STP-012`.

Public state:

```text
Lance opens Steelix. Gyarados, Ampharos, Yanma, Kingdra, and Dragonite remain.
Steelix can Dragon Dance, Earthquake, Iron Tail, or Outrage.
The player has two anti-setup tools and one final Dragonite answer.
One anti-setup tool also handles Kingdra; the other can stop Steelix now.
```

Expected arbitration:

- Do not spend the final Dragonite or Kingdra answer on Steelix unless Steelix
  itself becomes irreversible.
- Pressure Steelix while preserving enough anti-setup coverage for later waves.
- If Steelix boosts, re-score local Dragon Dance mechanics and Speed before
  choosing damage, control, status, sacrifice, or pivot.

Answer flip:

- If Steelix is one hit from removal, attacking may preserve anti-setup tools.
- If Steelix's boost makes the next hit remove the only Dragonite answer,
  immediate control or sacrifice rises.
- If the player has redundant Dragonite coverage, spending one answer early is
  less catastrophic.

Failure signs:

- "Use the Dragon answer now because Steelix is Dragon."
- Treating every Dragon Dance user as the same damage profile.
- Reaching Dragonite with no healthy Haze/phaze/status/revenge route.

## Card 006: Lance Yanma Focus Band / Sleep Branch

Source route map: `../boss_route_maps/lance_turn1_route_sheet.md`

Policies tested: `STP-002`, `STP-004`, `STP-008`, `STP-009`.

Public state:

```text
Yanma is active with Sleep Powder, Quiver Dance, Outrage, Giga Drain, and Focus
Band. The player can attempt a KO, switch to a sleep absorber, use status or
control, or sacrifice for clean entry.
```

Expected arbitration:

- A one-hit KO route must price Focus Band survival if Yanma getting one extra
  action can sleep or boost into a route.
- Sleep absorber assignment depends on future jobs, not on who has the most HP.
- If Yanma boosts, re-score Speed and special damage immediately.

Answer flip:

- If Sleep Clause is already occupied, direct damage rises.
- If the intended absorber is also the only Dragonite answer, denial or
  sacrifice may be safer than absorption.
- If the player has multi-hit, phazing, Haze, priority, or status evidence,
  the Focus Band branch may be less severe.

## Card 007: Red Pikachu Answer Reservation

Source route map: `../boss_route_maps/red_turn1_route_sheet.md`

Policies tested: `STP-004`, `STP-009`, `STP-010`, `STP-012`, `STP-032`.

Public state:

```text
Red opens fixed Pikachu.

Pikachu has Light Ball, ExtremeSpeed, Thunderbolt, Razor Leaf, and Surf.
Light Ball boosts Pikachu's Special Attack locally, not ExtremeSpeed.
Razor Leaf is high-crit locally.

Player has one lead that beats most Pikachu branches, but that lead is also one
of the few answers to Snorlax, Espeon, sun, or Blastoise later.
```

Expected arbitration:

- Do not choose the lead or first move by "beat Pikachu" alone. Red's opening
  is an answer-reservation test.
- Price Thunderbolt, Razor Leaf, Surf, and ExtremeSpeed separately because they
  threaten different resources.
- A lead is good only if it handles Pikachu while preserving at least one live
  answer map for Snorlax, Espeon setup, sun conversion, and Blastoise.

Answer flip:

- If the Pikachu answer is duplicated, aggressive damage or status into Pikachu
  rises.
- If the same piece is the only Snorlax answer, preserving its HP/status can
  outrank a cleaner Pikachu KO.
- If the player has a safe pivot that reveals Pikachu's branch without entering
  ExtremeSpeed or crit range, scouting/pivoting rises.
- If Pikachu is already in guaranteed KO range and cannot revenge with
  ExtremeSpeed, attacking rises.

Failure signs:

- "Use Ground/Rock because Pikachu is Electric" without pricing Surf and Razor
  Leaf.
- "ExtremeSpeed is Light Ball boosted" in this local mechanics profile.
- Winning turn 1 while chipping or statusing the only Snorlax or Espeon answer.

## Card 008: Red Blastoise Mirror Coat Arbitration

Source route map: `../boss_route_maps/red_turn1_route_sheet.md`

Policies tested: `STP-004`, `STP-009`, `STP-015`, `STP-020`, `STP-032`.

Public state:

```text
Red Blastoise is active with Mystic Water, Earthquake, Surf, Blizzard, and
Mirror Coat.

Player can use a special attack for heavy damage, a weaker physical attack, a
status/control move, a pivot, or a controlled sack into the real Blastoise
answer.

The special attacker may also be needed for Venusaur, Charizard, or Espeon.
```

Expected arbitration:

- Special damage is correct only if Mirror Coat does not create a decisive
  punish, or if the KO/forced route is worth accepting that branch.
- Physical, status, control, or pivot lines rise when they deny Mirror Coat
  while preserving the special attacker for a later Red route.
- If the special move is still best, the answer must name why the Mirror Coat
  branch is tolerable, blocked, or outweighed.

Answer flip:

- If Blastoise is in guaranteed special KO range and Mirror Coat cannot resolve
  afterward, special attack rises.
- If the special attacker is irreplaceable for Espeon, Venusaur, or Charizard,
  preserving it rises.
- If the physical line fails to change a route and lets Blastoise attack
  freely, special damage or controlled sack may become correct.
- If local AI trace/source evidence makes Mirror Coat unlikely in this exact
  state, it becomes a branch rather than the whole plan.

Failure signs:

- "Use the super effective special move" without Mirror Coat evidence.
- Switching to a physical answer that loses to Surf, Blizzard, or Earthquake
  without creating progress.
- Treating Mirror Coat as guaranteed boss behavior without source, trace, or
  route-incentive evidence.

## Card 009: Pryce Dewgong Encore / Spin Turn

Source route map: `../boss_route_maps/pryce_turn1_route_sheet.md`

Policies tested: `STP-001`, `STP-005`, `STP-016`, `STP-039`, `STP-040`.

Public state:

```text
Pryce's Dewgong is active with Rapid Spin / Surf / Ice Beam / Encore.

The player has hazards available or already set, plus a support/setup/recovery
move that looks useful. Dewgong can remove hazards, attack, or lock the last
executed move with Encore. Cloyster, Sneasel, Piloswine, and Slowking remain
possible later routes.

Player can set another hazard layer, attack Dewgong, pivot to a spin punisher,
use support/setup/recovery, or switch to preserve the current active.
```

Expected arbitration:

- Hazard progress is not real until Dewgong's Rapid Spin turn is punished,
  blocked, or priced.
- Support, setup, or recovery into Dewgong must pass the Encore target test:
  what exact last move is locked, and what 3-6 turn route does Pryce get?
- Attacking or pivoting rises when it denies spin/Encore while preserving the
  Sneasel/Piloswine/Slowking answer map.
- If the repeated move remains productive while locked, Encore is only a cost,
  not an automatic veto.

Answer flip:

- If Dewgong is in KO range, attacking can outrank preserving hazard tempo.
- If the player has a healthy spinblocker or spin punisher, setting or
  preserving hazards rises.
- If the current active is the only Sneasel or Piloswine answer, staying in for
  chip or hazards becomes worse.
- If the last move is invalid for local Encore, out of PP, already locked, or
  still route-positive when repeated, Encore fear drops.

Failure signs:

- "Set hazards because hazards are good" while Dewgong spins for free.
- "Recover/setup because Dewgong is passive" without naming Encore's locked
  move and follow-up.
- Attacking Dewgong for chip while losing the only answer to Sneasel,
  Piloswine, or Slowking.

## Card 010: Blaine Ninetales Weather / Safeguard Posture

Source route map: `../boss_route_maps/blaine_turn1_route_sheet.md`

Policies tested: `STP-004`, `STP-018`, `STP-027`, `STP-039`.

Public state:

```text
Blaine's Ninetales is active with Sunny Day / Fire Blast / Psychic / Safeguard.

The player's current plan relies on Water damage, status, or a single Fire
answer staying above priority range. Magcargo may already have created hazard
pressure. Rapidash, Arcanine, and Magmar remain possible later routes.

Player can attack Ninetales, status it, pivot to the Fire answer, change or
stall weather, preserve the current active, or make a riskier conversion play
before sun/Safeguard take over.
```

Expected arbitration:

- First label the posture: ahead/stable, losing slowly, or forced risk.
- If the clear-weather plan still wins, reduce variance and deny Ninetales's
  weather or Safeguard payoff without spending the only Fire answer.
- If the safe pivot only lets sun/Safeguard plus hazards create a losing clock,
  the correct move may be direct pressure, weather denial, a status attempt
  before Safeguard, or a controlled conversion risk.
- Waiting is acceptable only if the weather/status clock is contained and the
  Fire answer stays outside Rapidash Quick Attack or Arcanine ExtremeSpeed
  cleanup range.

Answer flip:

- If Sunny Day is already active, Water damage and Fire survival math must be
  recalculated before choosing the old plan.
- If Safeguard is active, status routes drop unless they can be delayed until
  the clock expires.
- If the Fire answer is already chipped by Spikes or priority range, pivoting
  can be worse than forcing Ninetales now.
- If direct pressure on Ninetales fails to change the weather route, burning
  turns or preserving the answer can outrank damage.

Failure signs:

- "Use Water/status because Blaine is Fire" without pricing sun and Safeguard.
- Calling a pivot safe while hazards plus sun put the Fire answer into priority
  or coverage range.
- Taking a risky conversion line while already ahead and able to deny the clock
  cleanly.
- Refusing a necessary risk when every conservative line lets the five-turn
  window become Blaine's route.

## Card 011: Janine Explosion Trade Into Breaker Route

Source route map: `../boss_route_maps/janine_turn1_route_sheet.md`

Policies tested: `STP-003`, `STP-007`, `STP-025`, `STP-028`.

Public state:

```text
Janine's Qwilfish or Weezing is active and can use Explosion.

Janine still has at least one major backline converter: Nidoking with broad
coverage or Venomoth with Sleep Powder / Quiver Dance. Tentacruel can also
spin or Haze, and Muk can RestTalk through weak chip.

The player's active can attack for damage, pivot to the sturdy answer, set or
preserve hazards, use status/control, or sacrifice a lower-value piece for
clean entry. One player Pokemon may be the only reliable Nidoking or Venomoth
answer.
```

Expected arbitration:

- Explosion is priced by the route it opens, not by whether the active Pokemon
  looks bulky or low HP.
- Do not give Qwilfish or Weezing the only Nidoking/Venomoth answer unless
  removing the exploder creates an immediate stronger route.
- Attacking rises when it removes the exploder, forces it low enough that the
  trade becomes bad, or prevents Spikes/coverage from making the boom route
  better.
- Sacrifice or pivot rises only when the lost role is accounted for and the
  next entry changes Janine's route map.

Answer flip:

- If the current active has no remaining job against Nidoking, Venomoth, Muk,
  or Tentacruel, absorbing Explosion can be correct.
- If Tentacruel can spin or Haze for free after the trade, preserving hazard or
  setup state may outrank immediate damage.
- If Venomoth has no setup route left or Nidoking is already solved by another
  piece, trading the current answer becomes less catastrophic.
- If the expected Explosion target is immune, resistant, protected, or can
  force a miss/block under local mechanics, the trade calculus changes.

Failure signs:

- "Let the bulky answer take Explosion" without checking its later job.
- "Attack because Qwilfish/Weezing is low" when the attack lets the exact
  irreplaceable answer get traded.
- Treating the first good trade as permission to spend the next sacrifice
  without rebuilding the remaining route map.

## Card 012: Morty Destiny Bond / Temporary Control Turn

Source route map: `../boss_route_maps/morty_turn1_route_sheet.md`

Policies tested: `STP-002`, `STP-024`, `STP-025`, `STP-036`.

Public state:

```text
Morty's Gengar is active and low enough that the player's obvious attack may
KO. Gengar has Shadow Ball / Thunderbolt / Destiny Bond / Psychic.

Earlier Morty pieces may have already created sleep, confusion, Curse, Toxic,
Pain Split, or Focus Band pressure. A second Haunter may remain. The player has
one clean Ghost answer and one damaged backup.

Player can take the KO, use a non-KO move, switch, status/control, sacrifice a
lower-value piece, or stall a temporary state.
```

Expected arbitration:

- Taking the KO is correct only if Destiny Bond is inactive, unlikely enough to
  accept, or the trade still preserves the remaining Morty route map.
- If Destiny Bond is active or heavily incentivized, non-KO control, switching,
  status, setup, or a lower-value sacrifice can outrank the obvious KO.
- Sleep/confusion/Curse/Pain Split pressure must be cashed out before reset; do
  not assume the battle is solved because one Morty piece is low.
- Preserve at least one awake, healthy answer for the second Haunter or any
  remaining Ghost route.

Answer flip:

- If Gengar cannot use Destiny Bond this turn or the state has cleared, the KO
  rises.
- If the attacker is no longer needed after Gengar faints, accepting the trade
  can be correct.
- If the backup Ghost answer is asleep, cursed, poisoned, or below threshold,
  preserving the current answer rises.
- If a non-KO move lets Gengar attack freely and remove the same answer anyway,
  KO or sacrifice may become the least bad route.

Failure signs:

- "Take the KO" without checking Destiny Bond state, speed/order, and the
  remaining Morty route.
- Treating sleep or confusion as a solved state instead of a temporary discount.
- Sacrificing the clean Ghost answer when the second Haunter or a Curse clock
  still needs it.

## Card 013: Koga Poison / Trap Clock Ownership

Source route map: `../boss_route_maps/koga_turn1_route_sheet.md`

Policies tested: `STP-013`, `STP-027`, `STP-028`, `STP-029`.

Public state:

```text
Koga's Ariados or Umbreon has created, or is about to create, a clock with
Spikes, Toxic, Spider Web, Confuse Ray, Pursuit, Moonlight, or recovery.

Tentacruel can Rapid Spin or Haze. Muk can Curse / Toxic / Rest. Nidoking and
Crobat remain as breaker and cleaner routes. The player's current active may
be able to attack, set hazards, use status, pivot, sacrifice, wait, or try to
force Koga's clock onto a less important Pokemon.

One player Pokemon may be the only Nidoking or Crobat answer.
```

Expected arbitration:

- First decide who owns the next three turns if the clock starts or continues.
- Toxic, trapping, hazards, or waiting are good only if they damage the right
  target and create a forced follow-up before Koga spins, Hazes, Rests,
  Moonlights, Pursuits, or enters Crobat.
- Pivoting rises when the current active would become trapped, poisoned, or
  chipped out of an irreplaceable Nidoking/Crobat job.
- Direct pressure rises when slow control lets Tentacruel reset the route or
  lets Muk/Umbreon turn the exchange into their own recovery loop.

Answer flip:

- If the poisoned/trapped piece is expendable, using its remaining turns for
  damage, hazards, or a clean-entry sacrifice can be correct.
- If Tentacruel is low or unable to spin/Haze safely, a hazard/setup clock rises.
- If Muk has already started Curse/Rest, direct denial or Haze/phazing may
  outrank poison progress.
- If Crobat is in range and cannot clean after the current exchange, waiting or
  poison damage becomes safer.

Failure signs:

- "Just Toxic it" without naming whether Koga can Rest, Moonlight, switch,
  spin, Haze, trap, or clean first.
- Waiting while Koga creates a new route instead of losing to the existing
  clock.
- Letting Ariados poison or trap the only Nidoking/Crobat answer because the
  current matchup looked manageable.

## Card 014: Jasmine Set-Retain-Convert Hazard War

Source route map: `../boss_route_maps/jasmine_turn1_route_sheet.md`

Policies tested: `STP-001`, `STP-005`, `STP-015`, `STP-028`, `STP-029`.

Public state:

```text
Jasmine can set hazards with Magneton or Skarmory, remove the player's hazards
with Forretress, and convert hazards with Steelix Roar or Skarmory Whirlwind.
Forretress also has Toxic / Protect / Explosion. Scizor can use Swords Dance
and then clean with Steel Wing / Wing Attack / Quick Attack.

The player can set hazards, attack the setter or spinner, spin or remove
Jasmine's hazards, pivot, use status/control, preserve the Scizor answer, or
trade/sacrifice. One player Pokemon may be the only reliable Scizor or Steelix
answer.
```

Expected arbitration:

- Split the hazard plan into set, retain, and convert before choosing a move.
- Setting hazards is bad if Forretress spins them for free and the turn does
  not create a threshold, entry, or trade.
- Spinning or attacking rises when Jasmine's hazards enable Roar/Whirlwind
  cycles, Scizor cleanup, or contact/recoil chip on the needed answer.
- Forretress Protect is progress for Jasmine only if the protected turn scouts,
  heals, stalls a clock, or improves the spin/Explosion route; otherwise punish
  the low-effect turn.

Answer flip:

- If the player already has a route that converts one layer before Forretress
  can spin, setting hazards rises.
- If the Scizor answer is paralyzed, poisoned, contact-chipped, or in Quick
  Attack range, preserving it outranks slow hazard progress.
- If Steelix or Skarmory can phaze repeatedly while Spikes are up, removal or
  direct pressure rises.
- If Forretress is low enough that Rapid Spin or Protect loses tempo, attacking
  or forcing the trade can outrank spinblocking theory.

Failure signs:

- "Set Spikes because hazards are good" without retaining or converting them.
- "Spin because hazards are bad" without naming what route the removed layer
  was enabling.
- Donating the Scizor answer to Toxic, Explosion, Rocky Helmet, or phaze damage
  while winning a minor hazard exchange.

## Card 015: Bugsy Support Chain Into Scyther

Source route map: `../boss_route_maps/bugsy_turn1_route_sheet.md`

Policies tested: `STP-008`, `STP-010`, `STP-022`, `STP-023`, `STP-029`,
`STP-048`.

Public state:

```text
Bugsy's Ledian is active with Reflect / Quiver Dance / Leech Life / Baton Pass,
or Ariados has already put poison/chip pressure on the player.

Scyther remains in back with Swords Dance / Leech Life / Quick Attack /
Wing Attack. The player can attack Ledian, status or phaze/Haze if available,
set up, pivot, preserve the Scyther answer, or sacrifice for clean entry.

One player Pokemon may be the only piece that survives or removes supported
Scyther.
```

Expected arbitration:

- Judge Ledian and Ariados by what they let Scyther do, not by their immediate
  damage.
- Attacking Ledian rises when it removes Baton Pass or forces Scyther to enter
  without useful support.
- Preserving or pivoting rises when the current active is the only supported
  Scyther answer and the support turn is trying to tax it.
- Phazing, Haze, Encore, or status must name the endpoint: does it stop the
  pass source, reset the receiver before it acts, or create a damage turn into
  Scyther? A reset with no follow-up may only delay the same pass route.
- Hazards, status, or setup lose value if Baton Pass delivers Scyther first and
  the receiver answer is no longer healthy.

Answer flip:

- If a separate Scyther answer remains healthy, spending the active to deny
  Ledian can be correct.
- If phazing/Haze is legal and acts before the pass or receiver conversion, it
  can outrank damage, but only while the follow-up endpoint is still named.
- If Scyther enters unsupported and in confirmed KO or revenge range, direct
  pressure can beat over-preservation.
- If Ariados poisons the Scyther answer, relabel that piece's remaining entries
  before using it to win the current exchange.

Failure signs:

- "Ledian is weak, ignore it" while it is one turn from passing the support
  that makes Scyther safe.
- Spending the only Scyther answer to win the Ledian/Ariados exchange.
- Setting up or using status while Baton Pass reaches Scyther first.

## Card 016: Will Slowbro Rest / Amnesia Anchor

Source route map: `../boss_route_maps/will_turn1_route_sheet.md`

Policies tested: `STP-002`, `STP-017`, `STP-024`, `STP-026`, `STP-029`.

Public state:

```text
Will's Slowbro is active with Amnesia / Surf / Psychic / Rest.

Forretress may have created Spikes, Toxic, Protect scouting, or Explosion
pressure. Starmie can remove hazards with Rapid Spin. Alakazam, Houndoom, and
Xatu remain possible special-pressure routes.

The player can attack Slowbro, force Rest, status it before Rest, use phazing
or Haze if available, pivot to a breaker, set hazards, preserve the special
answer, or sacrifice for clean entry.
```

Expected arbitration:

- Do not treat Rest as either pure passivity or pure reset. Ask whether the
  sleeping turns can be converted before Slowbro wakes.
- Do not import RestTalk assumptions: this Slowbro has Rest but not Sleep Talk
  in the local route sheet.
- Attacking rises when it forces Rest at a punishable time, prevents Amnesia
  from compounding, or creates a safe entry for the actual breaker.
- Pivoting or preserving rises when weak chip only lets Slowbro Rest while
  Alakazam, Houndoom, or Xatu inherit a damaged special answer.

Answer flip:

- If Slowbro is already boosted with Amnesia, physical pressure, phazing, Haze,
  status timing, or sacrifice may outrank more special chip.
- If hazards remain and Starmie cannot spin safely, forcing Rest can become a
  route because repeated entries matter.
- If the player cannot exploit the Rest turns, forcing Rest may only reset the
  damage race.
- If the special answer is poisoned or exploded on by Forretress, preserving it
  for Alakazam/Houndoom/Xatu may outrank trying to break Slowbro immediately.

Failure signs:

- "It Rests, so set up for free" without checking wake timing, Amnesia state,
  and the next Will route.
- "Attack again" when the damage only feeds Rest and leaves the special answer
  worse.
- Treating this Rest-only Slowbro like Red Snorlax's RestTalk set, or treating
  Red Snorlax like this Rest-only Slowbro.

## Card 017: Will Future Sight / Pursuit Resolution Turn

Source route map: `../boss_route_maps/will_turn1_route_sheet.md`

Policies tested: `STP-003`, `STP-024`, `STP-029`, `STP-033`, `STP-034`.

Public state:

```text
Will's Xatu is active with Night Shade / Psychic / Future Sight / Drill Peck
and Focus Band. Future Sight has just been used or is strongly available.

Will's Houndoom remains, or can plausibly enter soon, with Crunch /
Flamethrower / Sunny Day / Pursuit. Alakazam, Slowbro, Starmie, or Forretress
may also still be alive depending on the route.

The player can attack Xatu, pivot, sacrifice, use status/control, set up, heal,
or try to schedule a switch before Future Sight resolves. One player Pokemon
may be the only answer to Houndoom, Alakazam, or Slowbro.
```

Expected arbitration:

- Start with the landing turn, not the current one-on-one. Name the countdown,
  the likely active Pokemon on resolution, and whether Future Sight stacks with
  Xatu's current attack or a teammate's entry.
- Do not assume a normal Psychic-type switch answer solves the delayed hit:
  local Future Sight stores damage and the resolution path sets type modifier
  to effective.
- Houndoom changes the escape math. A switch that dodges Xatu's immediate hit
  may still be the line Will wants if Pursuit punishes the fleeing special
  answer or if Sunny Day / Flamethrower inherits the landing turn.
- Attacking Xatu rises when it prevents Future Sight from starting, removes
  Xatu before it stacks attacks, or forces a cleaner resolution turn. After the
  delayed hit is active, the answer must still schedule who takes it.

Answer flip:

- If Future Sight has not been started and Xatu is in reliable KO or control
  range, immediate pressure rises.
- If Future Sight is already active and the current Pokemon is expendable,
  staying or spending it can be correct to keep the Houndoom/Alakazam answer
  off the landing turn.
- If switching invites Pursuit on the only Houndoom answer, staying, healing,
  status/control, or sacrificing a lower-value piece may outrank the clean
  type-chart pivot.
- If Houndoom is gone or unable to punish the switch, the best line may become
  a scheduled pivot into the Pokemon that can take the stored damage and answer
  the next Will route.

Failure signs:

- "Future Sight is later, so ignore it now" without naming the resolution
  Pokemon.
- "Switch to the Psychic resist" without checking local Future Sight behavior,
  Pursuit, and the next active threat.
- KOing or damaging Xatu while forgetting that an already stored Future Sight
  still needs a landing-turn plan.
- Letting Focus Band variance turn the single planned Xatu KO into a stacked
  Future Sight plus current-attack turn.

## Card 018: Brock Golem Explosion Execution Gate

Source route map: `../boss_route_maps/brock_turn1_route_sheet.md`

Source mechanics: `../worked_examples/brock_golem_explosion_turn_order_quarantine.md`,
`data/trainers/parties.asm`, `data/moves/moves.asm`,
`engine/battle/move_effects/selfdestruct.asm`,
`engine/battle/move_effects/protect.asm`, and
`docs/agent_navigation/gen2_vs_modern_mechanics.md`.

Policies tested: `STP-003`, `STP-015`, `STP-020`, `STP-036`, `STP-042`,
`STP-043`.

Public state:

```text
Brock's Golem is active with Curse / Earthquake / Rock Slide / Explosion and
Rocky Helmet. It is low or mid HP.

The player has a Water or Grass attacker active, commonly Vaporeon-like, with a
revealed or obvious damaging move that may KO Golem. The player may also have
Protect, a switch to Omastar/Corsola coverage, status, setup, or a sacrifice
available.

Brock still may have Kabutops, Onix, Aerodactyl, Corsola, or Omastar routes
depending on the fight state.
```

Expected arbitration:

- Before pricing Explosion as a trade, check whether it can execute. Explosion
  is `EFFECT_SELFDESTRUCT` at base priority in the local move table; it is not
  a priority interrupt.
- If the player's active is faster and its Water/Grass attack KOs before Golem
  moves, direct attack rises because the trade never resolves.
- If Golem can move first or the player is likely to switch, heal, set up, or
  use non-KO chip, Explosion must be priced as a route trade into the remaining
  Brock endgame.
- If Protect is revealed and usable, it can blank Explosion, but Protect is not
  automatic progress. It is strong only when the Explosion branch is
  incentive-compatible or when scouting changes the next route.
- Switching or preserving rises when the active is the only Kabutops,
  Aerodactyl, or Onix answer and Golem's Explosion would remove that job.

Answer flip:

- If the player's damaging move does not KO, or Golem is faster through Speed,
  paralysis, Quick Claw-like effects, or the player chooses a non-damaging
  move, Explosion can become the decisive trade.
- If Protect was just used, local consecutive-use odds make repeating it less
  reliable.
- If Golem is still needed by Brock as the only answer to a later player route,
  the boss may prefer Curse, Earthquake, Rock Slide, or switching over
  Explosion.
- If the player's active has revealed Protect or Detect, boss AI should
  penalize commitment moves from public memory; it must not know unrevealed
  player Protect.

Failure signs:

- "Explosion removes the Water type" without checking Speed, priority, KO
  range, Protect, or whether the move executes.
- "Click Protect because Explosion is scary" when Surf or another attack
  cleanly removes Golem before it can move.
- "Golem is low, so it must explode" without naming what Brock gains after the
  trade and which player answer is lost.
- Letting Golem trade into the only Aerodactyl or Kabutops answer because the
  visible Golem matchup looked favorable.

## Card 019: Phazing Target-Pool Gate

Source route maps: `../boss_route_maps/jasmine_turn1_route_sheet.md`,
`../boss_route_maps/pryce_turn1_route_sheet.md`,
`../boss_route_maps/bruno_turn1_route_sheet.md`, and
`../boss_route_maps/chuck_turn1_route_sheet.md`.

Source mechanics: `engine/battle/effect_commands.asm`,
`engine/battle/ai/switch.asm`, and
`worked_examples/smogtours_904815_last_mon_phazing_fail.md`.

Policies tested: `STP-008`, `STP-012`, `STP-028`, `STP-041`, `STP-046`.

Public state:

```text
A local phazer is active or likely to enter soon:

- Jasmine Steelix has Earthquake / Iron Tail / Rock Slide / Roar.
- Jasmine Skarmory has Spikes / Steel Wing / Toxic / Whirlwind.
- Pryce Piloswine has Earthquake / Blizzard / Rock Slide / Roar.
- Bruno Onix has Spikes / Earthquake / Rock Slide / Roar.
- Chuck Sudowoodo has Spikes / Rock Slide / Focus Punch / Roar.

Hazards may be up, or a player setup/recovery route may make phazing look
attractive. The player may have a revealed bench, an unrevealed bench, or only
one living Pokemon left depending on the fight state.
```

Expected arbitration:

- First count the legal target pool. Roar / Whirlwind is route control only if
  the target has a living non-active Pokemon to drag.
- Then check local timing. In this romhack, the force-switch command preserves
  the Gen 2-style act-last gate; a phazing move that acts too early fails.
- If the player has a public living bench and hazards are up, phazing can be
  high value because it converts Spikes, resets setup, reveals switch-ins, and
  damages preservation plans.
- If the player is publicly on last Pokemon, phazing is not route control.
  Score damage, status that survives Rest/cure timing, recovery, setup,
  Focus Punch denial, PP, or a trade instead.
- If the boss AI only prefers phazing because it secretly knows the player's
  unrevealed bench or lack of bench, reject that label. Use public battle
  state, revealed switches, observed faints, and source-allowed memory.

Answer flip:

- With three layers up and at least one known player bench target, Roar /
  Whirlwind may dominate even over moderate damage.
- With no legal target, the same Roar / Whirlwind turn is a mechanics failure.
- With no hazards and no live setup route, attacking or preserving the phazer
  can beat spending finite phaze PP.
- If the phazer is faster under local order, or Sleep Talk / priority changes
  move order, re-check whether the force-switch move resolves.

Failure signs:

- "Spikes are up, so Roar" without proving a legal target and act-last timing.
- "They boosted, so Whirlwind" when the player is on last Pokemon.
- Boss AI using hidden player-team knowledge to decide whether a phaze has a
  target.
- Player-side advice continuing to preserve a phazer for a forced-switch route
  after the boss is already on its last Pokemon.

## Card 020: Post-Converter Handoff After Breakthrough

Source route maps: `../boss_route_maps/brock_turn1_route_sheet.md`,
`../boss_route_maps/pryce_turn1_route_sheet.md`,
`../boss_route_maps/janine_turn1_route_sheet.md`,
`../boss_route_maps/jasmine_turn1_route_sheet.md`,
`../boss_route_maps/lt_surge_turn1_route_sheet.md`, and
`../boss_route_maps/will_turn1_route_sheet.md`.

Source study: `../reviews/2026-05-13_smogtours-gen2ou-861526.md` and
`smogtours_861526_converter_handoff_after_breakthrough.md`.

Policies tested: `STP-006`, `STP-020`, `STP-027`, `STP-043`, `STP-047`.

Public state:

```text
The player's first converter, breaker, hazard piece, or one-time trade has
just fainted or been forced out after removing at least one important boss
blocker.

Examples:
- a Fire attacker removes Jasmine's Steelix or Forretress but is now too low
  to handle Scizor;
- a Water / Grass route removes Brock's Golem but has lost too much HP for
  Kabutops or Aerodactyl;
- the player removes Janine's Qwilfish / Tentacruel but loses the original
  poison-team breaker;
- Will's Forretress or Starmie is gone, but Alakazam, Houndoom, Slowbro, or
  Xatu still has a live route;
- Surge's Magneton / Electrode support piece is gone, but Raichu or Electabuzz
  is now the real route.

The player still has a possible closer, pivot, spinner, phazer/Haze user,
status move, recovery turn, or one-time trade, but exact player bench data may
or may not be public depending on perspective.
```

Expected arbitration:

- Do not decide from the old converter's survival. First list what it removed,
  which boss routes remain, and which player piece is now the closer.
- Utility can be the best move after a breakthrough: Rapid Spin to preserve
  final entries, phazing/Haze to reset the inherited setup route, status to
  stop the new closer, recovery to keep the final answer alive, or Explosion /
  sacrifice to remove the blocker the new closer cannot beat.
- If the supposed closer lacks HP, PP, speed, status state, entry access, or
  coverage, call the handoff fake and move to backup route or emergency
  denial.
- Boss AI must score the handoff from public state only. It may know its own
  remaining roster and public battle history, but it must not assume hidden
  player bench answers, unrevealed moves, items, or PP.
- Player-side coaching may use the user's full team only when the user or
  recording has provided it. Otherwise cap confidence and phrase the answer as
  route classes.

Answer flip:

- If the first converter removed the spinner, phazer, status spreader, or
  Explosion piece that blocked the route, handoff to the closer rises.
- If the first converter removed only a visible active while the real boss ace
  kept its answer intact, preserving the old plan falls.
- If hazards, poison, weather, or screen turns now make extra pivots too
  expensive, direct damage or a one-time trade can beat another utility turn.
- If the new closer is the only answer to a remaining boss route, recovery or
  preservation may outrank greedy damage.

Failure signs:

- "Our sweeper died, so the plan failed" without listing what it removed.
- "Keep attacking because we are ahead" while hazards, screens, or status make
  the final closer impossible to deliver.
- Using Explosion, phazing, Haze, or Rapid Spin because it is available rather
  than because it serves the new closer.
- Boss AI declaring the handoff won or lost from unrevealed player-team
  knowledge.

## Card 021: Whitney Rollout Reclassification Gate

Source route map: `../boss_route_maps/whitney_turn1_route_sheet.md`.

Source mechanics:
`../romhack_deltas/present_rollout_function_reclassification.md`,
`whitney_miltank_rollout_commitment.md`, and
`whitney_miltank_geodude_player_turn_drill.md`.

Policies tested: `STP-014`, `STP-017`, `STP-045`, `STP-050`.

Public state:

```text
Role: Whitney boss AI, public-turn advice.

Boss active:
  Miltank Lv21 at 92%, Mint Berry.
  Known moves: Milk Drink / Body Slam / Rollout / Attract.

Player active:
  Geodude Lv20 at 78%.
  Revealed moves: Rock Throw / Defense Curl.
  Public prior: Magnitude is plausible, not confirmed.

Field:
  No weather, hazards, screens, or known attraction lock.
  Geodude is not paralyzed.
```

Expected arbitration:

- Do not classify Miltank as "the Rollout Pokemon" on this turn. It is a
  flexible pressure ace until the lock route is actually favorable.
- Body Slam is the default route move: it creates chip and a paralysis branch
  while preserving Milk Drink, Attract, switch, and later Rollout timing.
- Milk Drink is too early at 92% unless current damage or a newly revealed
  punish makes preservation urgent.
- Rollout is bad from this public state because the first hit is tiny, Geodude
  is healthy and unstatused, and the boss gives up flexible move choice before
  reducing the Rock/Ground punish branch.
- Defense Curl from Geodude is public, but it does not by itself prove the
  player has a particular hidden bench answer or hidden move. Boss AI must not
  use unrevealed player-team knowledge to decide Rollout is safe or unsafe.

Answer flip:

- If Body Slam has already paralyzed Geodude, Rollout rises.
- If Miltank is near a real danger threshold, Milk Drink rises.
- If Geodude is low enough that the first or second Rollout hit immediately
  forces the route, Rollout rises.
- If Magnitude is confirmed absent, the lock route becomes safer but still
  needs HP and status checks.
- If the player reveals Haze, Roar, Whirlwind, Encore, Disable, or another
  anti-lock tool from the active battle state, preserve flexibility and
  re-score.

Failure signs:

- Opening Rollout because it is the famous Whitney move.
- Healing at high HP before creating Body Slam pressure.
- Switching away from Miltank without a concrete route reason.
- Boss AI treating hidden player bench, hidden moves, or hidden items as
  public information.
