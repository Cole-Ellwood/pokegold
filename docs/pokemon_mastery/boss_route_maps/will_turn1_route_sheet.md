# Will Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Will as adaptive first-three: Forretress / Starmie / Slowbro.
- Future Sight source: `data/moves/moves.asm`,
  `engine/battle/move_effects/future_sight.asm`, and
  `engine/battle/core.asm`; local Future Sight is 120 BP, 90 accuracy, special,
  non-contact, delayed, and the delayed-resolution path sets `wTypeModifier` to
  `EFFECTIVE`.
- Pursuit doubles damage on switching targets according to
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Dark is special in this hack according to
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Focus Band, Expert Belt, Leftovers, Charcoal, and TwistedSpoon behavior is
  listed in `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`; Expert Belt requires
  local type-effectiveness evidence before assuming the boost on a specific
  matchup.
- Expert principle sources: Smogon GSC Spikes, Explosion, Houndoom Pursuit, and
  Future Sight / Doom Desire discussions.

Boss roster:

```text
Lv40 Forretress @ Leftovers:
  Spikes / Protect / Toxic / Explosion

Lv40 Starmie @ Expert Belt:
  Rapid Spin / Surf / Psychic / Thunderbolt

Lv41 Slowbro @ Leftovers:
  Amnesia / Surf / Psychic / Rest

Lv42 Alakazam @ TwistedSpoon:
  Psychic / Ice Punch / ThunderPunch / Fire Punch

Lv41 Houndoom @ Charcoal:
  Crunch / Flamethrower / Sunny Day / Pursuit

Lv43 Xatu @ Focus Band:
  Night Shade / Psychic / Future Sight / Drill Peck
```

Boss likely openings:

- Will is source-listed as adaptive first-three, not fixed Forretress.
- Plan for Forretress / Starmie / Slowbro, with Forretress favored by the
  current weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Will's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Forretress route:

- Goal: start the fight by putting Spikes on the player side, poison something
  with Toxic, buy scouting turns with Protect, or trade with Explosion once its
  hazard job is done.
- What it punishes: passive leads, hazard plans that ignore Will's Starmie, and
  letting the only Alakazam/Houndoom/Slowbro answer take early poison or
  Explosion damage.
- Denial idea: pressure Forretress before it owns the clock. If it gets Spikes,
  immediately re-score grounded player Pokemon, Starmie's spin role, and the
  value of preserving the Forretress answer versus forcing the trade now.

Starmie route:

- Goal: remove the player's hazards with Rapid Spin while threatening enough
  Water/Psychic/Electric coverage that spin turns are not free to punish.
- What it punishes: assuming hazards are permanent progress, or pivoting by type
  slogans instead of local type-chart, passive, and damage evidence.
- Denial idea: make Rapid Spin expensive. If the player's win route depends on
  hazards, Starmie must be forced out, damaged into range, trapped, or made to
  spend the spin turn while giving up a larger route.

Slowbro route:

- Goal: use Amnesia, Leftovers, Surf/Psychic pressure, and Rest to become the
  special-side anchor.
- What it punishes: weak chip that lets it boost and Rest on schedule, and
  teams with no phaze, Haze, strong physical pressure, status plan, or Rest-turn
  punish.
- Denial idea: do not let the first Amnesia be a free turn. If Slowbro Rests,
  decide whether the sleep turns create real progress or merely reset the
  damage race while Will's other attackers stay healthy.

Alakazam route:

- Goal: use very high Speed and Special Attack plus Psychic / elemental punch
  coverage to punish over-simple pivots.
- What it punishes: preserving the wrong wall, assuming unrevealed coverage is
  absent, or letting the actual Alakazam answer take poison, Spikes, or
  Explosion damage earlier.
- Denial idea: preserve a verified special answer or revenge route. Every
  intended switch needs local damage evidence because Alakazam's value comes
  from coverage, not from one generic type identity.

Houndoom route:

- Goal: force uncomfortable switch decisions with Crunch, Flamethrower,
  Charcoal, Sunny Day, and Pursuit.
- What it punishes: switching a vulnerable special attacker or weakened Psychic
  answer without pricing Pursuit, and letting Sunny Day create a Fire-damage
  route for free.
- Denial idea: decide before switching whether Houndoom is threatening the stay
  line, the switch line, or both. Smogon GSC Houndoom material is useful here:
  Pursuit is strongest when the target wants to flee from Houndoom's immediate
  attacks.

Xatu route:

- Goal: create delayed Future Sight pressure, fixed Night Shade damage, direct
  Psychic/Flying pressure, and Focus Band variance.
- What it punishes: ignoring the future-hit ledger, relying on a single KO roll
  through Focus Band, or switching into a turn where Future Sight and Xatu's
  current attack stack on the same answer.
- Denial idea: track Future Sight as an active countdown. If it is started,
  plan the landing turn before choosing the next pivot or setup move.

## Player Plan Template

Primary route:

- Stop Will from turning the opening into Forretress hazard/status progress
  plus Starmie spin control plus a Slowbro or Alakazam/Houndoom special endgame.

Backup route:

- If Forretress gets Spikes or trades Explosion early, shorten the game around
  concrete KOs, Rest-turn punishment, or preserving the one answer that still
  covers Alakazam, Houndoom, or Slowbro.

Best lead profile:

- A lead that pressures Forretress, does not donate free Rapid Spin or coverage
  value to Starmie, and does not let Slowbro start Amnesia for free. It must
  not be the only answer to Alakazam, Houndoom, or Slowbro.
- Fire pressure into Forretress may be attractive, but it must be checked
  against local type/passive/damage evidence and the Houndoom route later in
  the fight.

Avoid as lead:

- A passive hazard lead if Starmie can spin without losing a larger resource.
- The only special anchor if Forretress can poison it or trade Explosion into
  it.
- A setup lead that lets Slowbro enter and Amnesia or lets Houndoom Sunny Day.
- A plan that assumes Future Sight behaves like generic Psychic damage without
  checking the local delayed-hit source.

First-turn question:

```text
Which adaptive opener appeared?

Forretress: can we deny Spikes / Toxic / Protect / Explosion from enabling the
later special routes?

Starmie: is Rapid Spin, Surf, Psychic, or Thunderbolt the live route, and does
our lead actually punish it?

Slowbro: can we prevent free Amnesia or force a Rest cycle that converts before
Will's faster special attackers arrive?
```

If Forretress sets Spikes:

- Re-score grounded player Pokemon, Will's Starmie as spinner, and whether the
  next switch exposes the Alakazam/Houndoom/Slowbro answer.

If Forretress uses Toxic:

- Check whether the poisoned Pokemon is the irreplaceable answer to a later
  special route. If yes, pivot or force progress quickly; if no, spend that
  poisoned Pokemon to create a concrete advantage.

If Forretress threatens Explosion:

- Treat Explosion as route conversion, not just damage. Ask what Forretress
  removes for Will and whether that removed piece was the only answer to a
  later special attacker.

If Starmie opens or enters:

- Decide whether Rapid Spin matters to the player's route. If the player is not
  relying on hazards, do not overchase Starmie while the Alakazam, Houndoom,
  Slowbro, or Xatu route remains more dangerous. If hazards do matter, make
  the spin turn expensive before adding more layers.

If Slowbro opens or enters:

- Decide whether immediate pressure, status, phazing/Haze, or sacrifice creates
  the best answer before Amnesia and Rest turn the exchange into a reset loop.

If Houndoom enters:

- Do not switch automatically. Price both stay and switch branches, including
  Pursuit on the switch and Sunny Day / Flamethrower pressure if staying gives
  it a free setup turn.

If Xatu uses Future Sight:

- Start a delayed-damage ledger. Track the counter, likely landing turn,
  expected active Pokemon, and whether the future hit combines with Xatu's next
  attack or a teammate's entry to overload the same answer.

Worst plausible branch:

- The player lets Forretress start Spikes or poison the main special answer,
  fails to punish Starmie spinning, gives Slowbro a free Amnesia/Rest loop, and
  then loses switch freedom to Houndoom Pursuit or Xatu Future Sight while
  Alakazam cleans weakened targets.

Abandon conditions:

- The only Alakazam, Houndoom, or Slowbro answer is poisoned, exploded on, or
  below its required damage threshold.
- Starmie can spin away the player's hazard route without giving up a decisive
  turn.
- Slowbro reaches a boost/rest state that the current team cannot break before
  it resets.
- Houndoom's Pursuit makes the planned pivot route worse than staying in or
  sacrificing a different piece.
- Future Sight is active and the planned switch would stack delayed damage on
  an irreplaceable answer.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Will does not use Snorlax, but Slowbro teaches the same anchor lesson:
  identify when a bulky Rest user is turning weak damage into lost tempo.
  Forretress teaches the Explosion route-trade lesson, Starmie teaches hazard
  denial, Houndoom teaches Pursuit incentive modeling, and Xatu teaches delayed
  damage planning.
