# Worked Example: Jasmine Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Jasmine as a Steel-core hazard,
spin, phaze, Explosion, and setup-conversion fight. This is a team-agnostic
planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `JasmineGroup`.
- Boss route map: `../boss_route_maps/jasmine_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Steel type-chart deltas, Steel physical category, Rocky Helmet, Protect,
  Explosion, Roar / Whirlwind timing, Swords Dance, Quick Attack priority, and
  Metal Coat references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Spikes material: Forretress can compress Spikes, Rapid Spin, Toxic
  immunity, and Explosion pressure; hazard advantage must be paired with a way
  to keep or exploit it.
- GSC Explosion material: Forretress's Explosion is usually defensive emergency
  trading or endgame simplification, not a generic wallbreaking button.
- GSC Steelix and Skarmory material: phazing turns become progress when Spikes
  are up; they are not harmless stall turns.
- Cross-generation setup material: Swords Dance plus priority turns chip into
  a cleanup route once the answer has been softened.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Jasmine

Known boss roster:
  Magneton / Forretress / Scizor / Steelix / Skarmory

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Scizor answer, a Steelix answer, a hazard/spin plan if the
  team needs repeated switching, and a way to avoid or absorb Forretress's
  Explosion trade; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Steel as physical, local
  Steel/Ghost/Dark chart changes, Steelix as Steel/Dragon rather than
  Steel/Ground, Ground being 2x into local Steelix, Rocky Helmet contact recoil,
  Protect priority, Roar / Whirlwind timing, Explosion halving target Defense,
  and Quick Attack sharing the standard priority-hit tier

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  contact flags, damage ranges, passive type states, whether the Scizor answer
  survives +2 Quick Attack / Steel Wing, whether Forretress's Explosion removes
  a critical route piece, and whether the lead can deny a free Spikes layer
```

## Output Shape

Primary route:

- Stop Jasmine from turning the fight into hazard control plus forced switches.
  Her team can create Spikes with Magneton or Skarmory, remove the player's
  layers with Forretress, then convert chip through Scizor setup or Steelix /
  Skarmory phazing.

Backup route:

- If Spikes land and cannot be removed, shorten the battle. Treat every switch,
  Roar, Whirlwind, Protect, and Explosion threat as route material. Preserve
  the exact answer to Scizor and Steelix instead of chasing generic Steel
  matchups.

Boss route priority:

```text
immediate:
  Magneton Thunder Wave if it cripples the only Scizor or Steelix answer.
  Forretress Explosion if it can remove the current route piece.
  Scizor Swords Dance if the answer is chipped or paralyzed.

accumulating:
  Magneton or Skarmory Spikes into repeated grounded switching.
  Forretress Rapid Spin if the player's plan depends on hazards.
  Skarmory Toxic / Whirlwind with Spikes active.
  Steelix Roar with Spikes active.

endgame:
  Scizor cleaning with Swords Dance plus Quick Attack after chip.
  Steelix forcing repeated hazard entries if the local matchup answer is gone.
  Skarmory turning contact recoil, Toxic, and Whirlwind into a slow loss.
```

Boss route to deny first:

- Deny the route that makes later switching impossible. If the user's team
  needs pivots, Magneton or Skarmory getting early Spikes is urgent. If the
  user's team relies on one sweeper or one wallbreaker, Forretress Explosion and
  Scizor's setup window are more urgent than the first layer itself.

Boss route that can be delayed:

- Magneton can be delayed if Thunder Wave does not matter and the team can
  punish or ignore one layer. It cannot be delayed if paralysis turns the
  Scizor or Steelix answer into a liability.

- Forretress can be delayed only when the player's route does not depend on
  hazards and Explosion has no valuable target. If either condition is false,
  Forretress is not passive.

Best lead profile:

- A lead that contests Magneton without being the only Scizor or Steelix
  answer. It should either force Magneton to spend turn 1 defensively, make
  Spikes too slow, or absorb Thunder Wave without losing a later route.

Avoid as lead:

- The only Scizor answer if Magneton can paralyze it or Forretress can trade
  Explosion into it.
- A contact-dependent attacker if Skarmory can turn Rocky Helmet recoil into
  the difference between checking and losing to Scizor.
- A hazard lead whose layers are immediately spun by Forretress with no punish.
- A setup lead that lets Skarmory or Steelix phaze through Spikes.
- A Ghost- or Dark-based type plan that has not been checked against the
  romhack chart, because local Steel interactions differ from vanilla memory.

First move plan:

- Give turn 1 one job: deny the first route that lets Jasmine own the next
  three turns. Attacking Magneton is good only if it changes the hazard,
  paralysis, or switch map. Switching is good only if it preserves a specific
  later answer. Setting hazards is good only if Forretress cannot erase them
  without cost.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Magneton's Spikes, Thunder Wave, Thunderbolt, and Swift branches against
  the lead's later role.

Turn 2:
  If Spikes or paralysis landed, rebuild around grounded switch cost and the
  speed/control loss. If Magneton was denied, prepare for Forretress spin/boom,
  Scizor setup, Steelix Roar, or Skarmory Spikes/Whirlwind.

Turn 3:
  Start the relevant ledger: Spikes layers on both sides, Forretress Explosion
  availability, Scizor boost state, Steelix/Skarmory phaze access, Rocky Helmet
  contact recoil, and type-evidence claims used by the current answer.
```

Piece to preserve:

- The Scizor answer by default. Swords Dance plus Quick Attack means a chipped
  team can lose even when it still has faster Pokemon.

- The Steelix answer, but only after verifying local type evidence. This
  Steelix is Steel/Dragon, not the vanilla Steel/Ground memory case.

- A hazard-control or hazard-punish piece if the team needs repeated switching.
  Against two Spikes users plus a spinner, the question is who benefits from
  the next layer, not whether Spikes are generically good.

Piece that can be spent:

- A paralyzed lead only if it has already denied Magneton's route and no longer
  needs Speed to stop Scizor, Steelix, or Skarmory.

- A low-value attacker only if sacrificing it gives clean entry to the real
  converter and does not let Forretress keep both spin and Explosion value.

Worst plausible branch:

- Magneton gets Spikes or Thunder Wave, Forretress removes the player's hazard
  progress while keeping Explosion available, Skarmory or Steelix phazes through
  the layer, and Scizor gets one Swords Dance after the real answer has been
  chipped by entry damage, contact recoil, or paralysis.

Abandon conditions:

- The Scizor answer is paralyzed, exploded on, or below the required threshold.
- Forretress can Rapid Spin for free while still threatening Explosion.
- Skarmory or Steelix can repeatedly phaze while Spikes are up.
- Rocky Helmet recoil makes the chosen contact attacker unable to complete its
  later job.
- The plan uses "resisted," "immune," "neutral," or "super-effective" language
  without checking the romhack type chart and passive/type-item evidence.
- The local Steelix matchup contradicts the assumed vanilla Steelix answer.

What information would flip the lead or first move:

- Damage evidence showing the lead can or cannot remove Magneton before Spikes
  or Thunder Wave matters.
- Whether the player has a separate Scizor answer that does not care about
  paralysis.
- Whether Forretress Explosion removes the only route piece or trades into
  something expendable.
- Whether the player can punish Rapid Spin, or whether hazards are a wasted
  tempo investment.
- Whether the intended Skarmory answer uses contact and loses too much to Rocky
  Helmet recoil.
- Whether local type/passive evidence changes the Steelix answer.
- Whether Scizor has already boosted or can be denied before Quick Attack ranges
  matter.

## Extracted Lesson

Jasmine is not "hit Steel with Fire or Ground." Jasmine is a route-compression
boss. Magneton and Skarmory start hazard/control clocks, Forretress can erase
progress or trade Explosion, Steelix and Skarmory convert hazards through
phazing, and Scizor converts one free turn into cleanup pressure. The right
opening is the one that names which route is urgent, preserves the specific
answer to that route, and refuses to use vanilla type memory where the romhack
chart is the real source of truth.
