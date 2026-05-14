# Jasmine Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; notably, local
  Steelix is Steel/Dragon, not vanilla Steel/Ground.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Jasmine as adaptive first-three: Magneton / Forretress / Scizor.
- Roar / Whirlwind priority caveat:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; do not import modern
  phazing assumptions.
- Swords Dance is `EFFECT_ATTACK_UP_2` in `data/moves/moves.asm`.
- Rocky Helmet recoil is contact-gated in
  `engine/battle/late_gen_held_items.asm`; contact flags live in
  `data/moves/contact_flags.asm`.
- Metal Coat and Magnet are type-boost items listed in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert principle sources: Smogon GSC Spikes, Explosion, Steelix, Forretress,
  and Scizor discussions.
- Threshold drill: `../worked_examples/jasmine_steelix_quilava_fire_threshold.md`
  covers Steelix versus Quilava fire-pressure branching with local damage
  evidence.

Boss roster:

```text
Lv31 Magneton @ Magnet:
  Spikes / Thunderbolt / Thunder Wave / Swift

Lv32 Forretress @ Leftovers:
  Rapid Spin / Toxic / Protect / Explosion

Lv33 Scizor @ Metal Coat:
  Swords Dance / Steel Wing / Quick Attack / Wing Attack

Lv34 Steelix @ Metal Coat:
  Earthquake / Iron Tail / Rock Slide / Roar

Lv33 Skarmory @ Rocky Helmet:
  Spikes / Steel Wing / Toxic / Whirlwind
```

Boss likely openings:

- Jasmine is source-listed as adaptive first-three, not fixed Magneton.
- Plan for Magneton / Forretress / Scizor, with Magneton favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Jasmine's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Magneton route:

- Goal: open with Spikes or speed control, then pressure with Electric damage
  while the player tries to identify the real Steel answer.
- What it punishes: turn-1 plans that ignore Thunder Wave, or leads that let
  Magneton start the hazard clock without forcing a tradeoff.
- Denial idea: decide whether Magneton must be removed, statused, forced out,
  or used as an entry point for the player's own route. Do not spend the only
  Scizor or Steelix answer just to win the Magneton exchange.

Forretress route:

- Goal: compress Rapid Spin, Toxic, Protect scouting, Leftovers stalling, and
  Explosion into one piece.
- What it punishes: hazard plans with no spin punish, contactless chip that
  never forces a resource loss, and setup routes that forget Explosion.
- Denial idea: if the player's route needs hazards, Forretress must be pressured
  before it spins. If the player's route needs a specific sweeper, do not donate
  it to Explosion without naming the trade.

Scizor route:

- Goal: convert a free turn into Swords Dance pressure, then use Steel Wing,
  Wing Attack, and Quick Attack to punish weakened answers.
- What it punishes: using the Scizor answer to absorb early paralysis, Toxic,
  Spikes, Rocky Helmet recoil, or Explosion.
- Denial idea: preserve the Scizor answer until boost state and HP thresholds
  are known. If Scizor has not boosted and can be removed immediately, direct
  pressure may beat over-preservation.

Steelix route:

- Goal: use high physical bulk, broad coverage, Metal Coat-boosted Steel
  pressure, and Roar to turn Spikes into repeated forced-switch damage.
- What it punishes: passive recovery or setup turns that let Steelix phaze the
  player through hazards.
- Denial idea: verify the local Steel/Dragon matchup before choosing a pivot.
  If Spikes are up, every Steelix Roar turn should be treated as hazard
  conversion, not harmless stalling.

Skarmory route:

- Goal: add more Spikes pressure, spread Toxic, punish contact with Rocky
  Helmet, and Whirlwind the player through hazard damage.
- What it punishes: contact-heavy attacks that ignore recoil, slow setup lines,
  and assuming a wall is passive when it is multiplying hazard turns.
- Denial idea: use non-contact pressure, status, phazing, or direct damage when
  available. If contact is required, price Rocky Helmet recoil before spending
  the attacker.

## Player Plan Template

Primary route:

- Prevent the Steel core from turning the fight into Spikes plus phazing plus
  spin control. Jasmine can start hazards with two different Pokemon, remove the
  player's hazards with Forretress, and then convert with Scizor or Roar /
  Whirlwind cycles.

Backup route:

- If Spikes are established and cannot be removed, shorten the battle. Stop
  switching as though it is free, force direct KOs, and preserve the exact piece
  that prevents Scizor from turning one boost into cleanup.

Best lead profile:

- A lead that pressures Magneton, does not let Forretress get free Rapid Spin,
  Toxic, Protect, or Explosion value, and does not give Scizor a free Swords
  Dance. It must not be the only Steelix or Scizor answer.
- Paralysis blocking or recovery helps only if it still creates real pressure.

Avoid as lead:

- A passive setup lead that gives Magneton or Skarmory a free Spikes turn.
- A contact-dependent attacker if Skarmory can force Rocky Helmet trades before
  the attacker completes its job.
- A hazard setter whose layers are immediately spun by Forretress with no
  punish.
- The only Scizor answer if Magneton can paralyze it or Forretress can explode
  on it.

First-turn question:

```text
Which adaptive opener appeared?

Magneton: can we deny Spikes / Thunder Wave without spending the Scizor or
Steelix answer?

Forretress: is Rapid Spin, Toxic, Protect, or Explosion the live compression
route, and does our lead punish it?

Scizor: can we prevent a free Swords Dance or Quick Attack cleanup map before
the Scizor answer is chipped?
```

If Magneton sets Spikes:

- Re-score grounded switch count, Forretress's spin role, Skarmory's second
  Spikes route, and the player's ability to attack without constant pivoting.

If Forretress opens or enters:

- Decide whether it is a spinner, Toxic wall, Protect scout, or Explosion
  threat in the current state. The correct answer can change by HP, route, and
  whether the player's hazards matter.

If Scizor opens or uses Swords Dance:

- Stop the previous plan and count the boosted threat. Ask whether immediate
  damage, phazing, Haze, status, priority, or sacrifice prevents cleanup before
  Quick Attack ranges matter.

If Skarmory or Steelix phazes:

- Do not call it a stall turn. Update Spikes damage, revealed switch-ins, and
  whether the forced Pokemon gives Jasmine a better route than the previous
  active did.
- If the player or boss is on last material, first check the target pool. Roar
  / Whirlwind is not route control when there is no living non-active target to
  drag.

Worst plausible branch:

- The player lets Magneton or Skarmory set Spikes, fails to punish Forretress's
  spin or Explosion role, chips the Scizor answer with contact and phazing
  cycles, then loses when Scizor gets one Swords Dance or Steelix/Skarmory keeps
  forcing hazard entries.

Abandon conditions:

- Forretress can remove hazards for free and still keep Explosion available.
- Scizor's answer is paralyzed, poisoned, exploded on, or below the required HP
  threshold.
- Rocky Helmet recoil makes the planned contact attacker no longer able to
  finish its job.
- Steelix or Skarmory can phaze repeatedly while Spikes are up.
- The assumed type matchup is based on vanilla memory rather than local
  Steel/Ghost/Dark/type-passive evidence.

Snorlax study transfer:

- Jasmine is a structure lesson: hazard setters, a spinner, phazers, a setup
  converter, and a one-time trade resource. The Snorlax-transfer idea is not
  "prepare for Snorlax"; it is to preserve the specific answer to the route that
  can still win after passive damage has accumulated.
