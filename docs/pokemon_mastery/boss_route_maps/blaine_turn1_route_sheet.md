# Blaine Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; Blaine's roster
  is Fire-heavy but has hazard/setup, weather, priority, recoil, and wide
  coverage routes.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Blaine as adaptive first-three: Magcargo / Ninetales / Rapidash.
- Spikes source: `engine/battle/move_effects/spikes.asm`; this romhack allows
  up to three layers, and a fourth click fails.
- Sunny Day source: `engine/battle/move_effects/sunny_day.asm`; local weather
  lasts five turns.
- Safeguard source: `engine/battle/move_effects/safeguard.asm`; local
  Safeguard lasts five turns and blocks status attempts while active.
- Priority caveat: Quick Attack and ExtremeSpeed both use
  `EFFECT_PRIORITY_HIT` in `data/moves/moves.asm`, so do not import modern
  ExtremeSpeed priority brackets unless the local source changes.
- Curse, Agility, Quick Attack, ExtremeSpeed, Fire Blast, Flamethrower,
  Double-Edge, Crunch, Iron Tail, ThunderPunch, Psychic, Hidden Power, and
  Rock Slide are listed in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Life Orb, Muscle Band, Wise Glasses, Charcoal, Rocky Helmet, and contact
  behavior: `docs/agent_navigation/gen2_vs_modern_mechanics.md`,
  `docs/agent_navigation/hack_mechanics_reference.md`, and
  `data/moves/contact_flags.asm`.
- Fire low-HP passive fixture:
  `tools/damage_debugger/clobber_smoke.py::special_fire_low_hp` verifies the
  full-Fire below-one-third damage boost on the main damage path. Ninetales,
  Rapidash, Arcanine, and Magmar are full-Fire in
  `data/pokemon/base_stats/*.asm`; Magcargo is Fire/Rock and still needs the
  half-Fire boundary fixture before using exact 11/10 advice as runtime proof.
- Expert principle sources: Smogon GSC Spikes, GSC Explosion, Sunny Day,
  priority, setup, and weather-control material.

Boss roster:

```text
Lv64 Magcargo @ Rocky Helmet:
  Spikes / Curse / Flamethrower / Rock Slide

Lv64 Ninetales @ Charcoal:
  Sunny Day / Fire Blast / Psychic / Safeguard

Lv64 Rapidash @ Muscle Band:
  Agility / Fire Blast / Quick Attack / Double-Edge

Lv64 Arcanine @ Life Orb:
  Flamethrower / ExtremeSpeed / Crunch / Iron Tail

Lv65 Magmar @ Wise Glasses:
  Fire Blast / ThunderPunch / Psychic / Hidden Power
```

Boss likely openings:

- Blaine is source-listed as adaptive first-three, not fixed Magcargo.
- Plan for Magcargo / Ninetales / Rapidash, with Magcargo favored by the
  current weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Blaine's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Magcargo route:

- Goal: use high physical bulk, Rocky Helmet, Spikes, Curse, Flamethrower, and
  Rock Slide to make the player's obvious contact or physical answer pay a
  long-term tax.
- What it punishes: slow contact-heavy leads, ignoring three-layer Spikes, and
  letting Curse turn a hazard setter into a physical win route.
- Denial idea: decide whether turn 1 must stop Spikes, stop Curse, avoid
  Rocky Helmet contact, or remove Magcargo before the Fire attackers inherit
  the hazard advantage.

Ninetales route:

- Goal: set Sunny Day, protect the team from status with Safeguard, and turn
  Charcoal Fire Blast into the center of a five-turn weather window. If
  Ninetales is below one-third HP, the full-Fire passive can make the next Fire
  Blast stronger rather than harmless.
- What it punishes: status-first plans, Water-only answers that lose value in
  sun, and damage lines that ignore weather-boosted Fire pressure.
- Denial idea: if Sunny Day or Safeguard goes up, start a five-turn clock. The
  next move should either consume the clock safely, change weather, force
  Ninetales out, or use a route that does not rely on blocked status or weakened
  Water damage.

Rapidash route:

- Goal: use Agility to change Speed control, then clean weakened targets with
  Fire Blast, Double-Edge, and Quick Attack. Below one-third HP, its Fire Blast
  also gets the verified full-Fire passive boost, so low HP is not by itself a
  safe pivot signal.
- What it punishes: assuming the faster player piece remains faster, and
  leaving key Pokemon in priority range after hazard or recoil math changes.
- Denial idea: before Rapidash can use Agility, decide whether immediate
  damage, status, phazing/Haze, priority, or a planned sacrifice denies the
  boosted sequence.

Arcanine route:

- Goal: use Life Orb Flamethrower and coverage while keeping ExtremeSpeed as a
  late-route finisher. Below one-third HP, the full-Fire passive stacks as a
  separate damage fact from Life Orb, while Life Orb recoil may also move
  Arcanine closer to fainting.
- What it punishes: stabilizing at low HP, assuming revenge speed is enough,
  and ignoring Life Orb recoil as both a clock and a damage amplifier.
- Denial idea: track ExtremeSpeed range separately from normal Speed order. If
  the player's cleaner is in priority range, it may no longer be a live route
  even if it outspeeds Arcanine.

Magmar route:

- Goal: use Wise Glasses Fire Blast plus ThunderPunch, Psychic, and Hidden
  Power to break the expected Fire answers. Below one-third HP, full-Fire
  passive Fire Blast damage is debugger-verified and should be re-scored before
  calling the obvious pivot safe.
- What it punishes: a single-type defensive plan and assuming Fire resist means
  all Magmar turns are safe.
- Denial idea: require local type/passive/damage evidence for the intended
  pivot. Once Hidden Power type or damage is revealed, update the pivot map
  immediately.

## Player Plan Template

Primary route:

- Blaine tries to make the player answer Fire pressure while paying extra
  clocks: Spikes, sun, Safeguard, Agility, priority, recoil, and coverage. The
  player should keep one real Fire route answer healthy while preventing
  Magcargo and Ninetales from making the rest of the fight cheaper for Blaine.

Backup route:

- If Magcargo gets Spikes or Ninetales gets sun/Safeguard, stop assuming the
  original defensive math. Rebuild around hazard layers, weather turns, status
  availability, priority ranges, and which Blaine attacker is now closest to
  cleaning.

Best lead profile:

- A lead that pressures Magcargo without relying on unsafe contact, does not
  let Ninetales set free sun/Safeguard, and does not lose to a Rapidash Agility
  start. It must not be the only answer to sun-boosted Fire Blast or Arcanine's
  ExtremeSpeed.
- The first move should either deny Spikes/Curse, force immediate damage, or
  create a position where Ninetales/Rapidash cannot take over the next turn.

Avoid as lead:

- A contact-first physical lead that is badly punished by Rocky Helmet.
- A status-first lead if Ninetales can make Safeguard free.
- A Water-only plan that collapses if Sunny Day is active.
- The only priority-proof or Fire-resistant piece if Magcargo can chip it into
  Rapidash or Arcanine range.

First-turn question:

```text
Which adaptive opener appeared?

Magcargo: can we deny Spikes / Curse without donating Rocky Helmet contact or
Fire pressure?

Ninetales: can we stop Sunny Day or Safeguard from rewriting the damage/status
map?

Rapidash: can we deny Agility or avoid falling into Fire Blast plus Quick
Attack range?
```

If Magcargo sets Spikes:

- Count layers. Re-score grounded player Pokemon and ask whether Rapidash,
  Arcanine, or Magmar now reaches revenge or priority thresholds sooner.

If Magcargo uses Curse:

- Decide whether Magcargo itself is becoming the route or whether the Curse
  turn merely bought time for Spikes. Do not answer setup with low-impact chip.

If Ninetales opens or uses Sunny Day:

- Start the weather ledger. Water damage and Fire damage assumptions change for
  five turns, and SolarBeam-style shortcuts from other formats should not be
  imported unless the local moveset has the move.

If Ninetales uses Safeguard:

- Do not spend key status PP into the protected side. Use the screen/status
  window recipe: attack through it, pivot, stall the clock, or pressure the
  setter.

If Rapidash opens or uses Agility:

- Re-score Speed immediately. If the player cannot survive the next boosted
  attack plus Quick Attack range, the denial move may need to be sacrifice,
  phazing/Haze, or immediate KO rather than normal pivoting.

If Arcanine enters:

- Track Life Orb recoil and ExtremeSpeed range together. A line that wins after
  one more recoil tick may be better than trading the cleaner into priority.

Worst plausible branch:

- The player lets Magcargo stack Spikes or Curse, then lets Ninetales set sun
  or Safeguard, leaving the Fire answer chipped into Rapidash Quick Attack or
  Arcanine ExtremeSpeed range while Magmar punishes the obvious pivot with
  coverage.

Abandon conditions:

- Spikes layers change the required HP threshold for the Fire answer.
- Sunny Day is active and the plan depends on Water damage or surviving Fire
  Blast without recalculation.
- Safeguard is active and the plan depends on landing status.
- Rapidash has boosted with Agility and no immediate denial route remains.
- Arcanine's ExtremeSpeed range covers the planned cleaner.
- Magmar reveals Hidden Power or coverage damage that contradicts the assumed
  pivot.
- A full-Fire Blaine attacker crosses below one-third HP and still has a Fire
  attack available; re-score the next-hit survival math instead of treating low
  HP as spent.
- Type-chart, passive, item, contact, weather, or damage evidence contradicts
  the assumed answer.

Snorlax study transfer:

- Blaine teaches clock stacking. The useful GSC transfer is to avoid viewing
  hazards, weather, priority, and recoil as separate facts; together they
  change whether a defensive answer can still perform its job two turns later.
