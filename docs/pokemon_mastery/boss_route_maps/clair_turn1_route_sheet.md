# Clair Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; local Steelix is
  Steel/Dragon.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Clair as adaptive first-three: Gligar / Mantine / Kingdra.
- Dragon Dance source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  this hack boosts the user's current higher offensive stat plus Speed.
- Outrage source: `data/moves/moves.asm` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; local Outrage is 100 BP,
  Dragon, contact, and has a Dragon-user category exception.
- Rampage source: `engine/battle/effect_commands.asm`; Outrage-style rampage
  lasts 2-3 total turns and then can confuse.
- Quick Claw and MiracleBerry behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Haze source: `engine/battle/effect_commands.asm`; it resets both sides' stat
  stages.
- Hidden-coverage stay-in example:
  `docs/pokemon_mastery/worked_examples/clair_dragonair_suicune_hidden_coverage.md`
- Expert principle sources: Smogon Dragon Dance / Kingdra material, setup
  control, and GSC hazard/phazing principles.

Boss roster:

```text
Lv37 Gligar @ Quick Claw:
  Spikes / Earthquake / Wing Attack / Toxic

Lv37 Mantine @ Leftovers:
  Rapid Spin / Surf / Haze / Confuse Ray

Lv39 Kingdra @ Leftovers:
  Dragon Dance / Surf / Outrage / Ice Beam

Lv38 Dragonair @ Expert Belt:
  Thunder / Fire Blast / Outrage / Thunder Wave

Lv38 Steelix @ Metal Coat:
  Earthquake / Iron Tail / Outrage / Roar

Lv37 Dragonair @ MiracleBerry:
  Dragon Dance / Surf / Fire Blast / Outrage
```

Boss likely openings:

- Clair is source-listed as adaptive first-three, not fixed Gligar.
- Plan for Gligar / Mantine / Kingdra, with Gligar favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Clair's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Gligar route:

- Goal: start Spikes or Toxic, then use Quick Claw variance to steal turns the
  player thought were speed-safe.
- What it punishes: using the Kingdra answer as the early hazard absorber, or
  assuming a faster lead always moves first.
- Denial idea: pressure Gligar without exposing the only Dragon Dance answer.
  If Quick Claw changes turn order, separate variance from decision quality and
  re-score the new HP/status state.

Mantine route:

- Goal: erase the player's hazards with Rapid Spin, reset boosts with Haze, and
  buy disruption turns with Confuse Ray.
- What it punishes: setup plans that ignore Haze and hazard plans that do not
  pressure the spinner.
- Denial idea: if the player needs hazards or boosts, Mantine must be forced to
  spend the turn under pressure. If Mantine Hazes, abandon the old setup math.

Kingdra route:

- Goal: use Dragon Dance and bulk to create a boosted Surf / Outrage endgame.
- What it punishes: letting the first Dragon Dance happen for free, or spending
  the Kingdra answer before Outrage ranges are known.
- Denial idea: preserve the Kingdra answer and identify the anti-setup tool:
  immediate damage, Haze, phazing, status, sacrifice, or revenge. Once Outrage
  starts, treat it as a locked commitment that can sometimes be punished.

Expert Belt Dragonair route:

- Goal: use Thunder, Fire Blast, Thunder Wave, and Outrage to punish the pivot
  that expects only Dragon damage.
- What it punishes: type-slogan switching and assuming unrevealed coverage is
  absent.
- Denial idea: every "safe" pivot requires local type-chart, passive, and damage
  evidence. If the coverage move is revealed, update the route immediately.

Steelix route:

- Goal: use local Steel/Dragon typing, coverage, Outrage, and Roar to disrupt
  attempts to set up or wall Clair with one piece.
- What it punishes: vanilla Steelix assumptions and passive turns that let Roar
  plus Spikes decide the position.
- Denial idea: check local matchup evidence before pivoting. If Spikes are up,
  Steelix Roar is a route-conversion move, not a blank defensive turn.

MiracleBerry Dragonair route:

- Goal: use Dragon Dance while holding a one-time status cure, then pressure
  with Surf, Fire Blast, and Outrage.
- What it punishes: relying on a single status move as the anti-setup plan, or
  using that status before the berry is spent.
- Denial idea: either force the berry on a turn that still preserves the answer,
  or use non-status counterplay: damage, phazing, Haze, sacrifice, or revenge.

## Player Plan Template

Primary route:

- Keep the anti-Dragon Dance plan intact. Clair's early hazards and status exist
  to make Kingdra, Dragonair, or Steelix harder to answer later.

Backup route:

- If Spikes, Toxic, or Thunder Wave lands on the intended answer, shorten the
  game and preserve a second line: Haze/phaze, revenge range, sacrifice into a
  safe attacker, or exploiting Outrage lock.

Best lead profile:

- A lead that pressures Gligar's Spikes/Toxic plan, does not donate free Rapid
  Spin/Haze/Confuse Ray value to Mantine, and can stop or immediately punish a
  Kingdra Dragon Dance opener. It must not be the only Dragonair answer.
- A hazard lead is useful only if Mantine cannot spin for free.

Avoid as lead:

- A slow setup lead that Mantine can Haze or Kingdra can outscale.
- The only Dragon Dance answer if Gligar can Toxic it or force it through
  Spikes early.
- A status-only answer if MiracleBerry Dragonair can absorb the first status and
  keep boosting.
- A plan that relies on vanilla type memory against Steelix or Outrage.

First-turn question:

```text
Which adaptive opener appeared?

Gligar: can we deny Spikes / Toxic without spending the Kingdra or Dragonair
answer?

Mantine: is Rapid Spin, Haze, Surf, or Confuse Ray the live reset route, and
does our lead punish it?

Kingdra: can we stop Dragon Dance immediately, or do we have a named Haze,
phaze, status, damage, sacrifice, or revenge line after +1 Speed?
```

If Gligar sets Spikes:

- Re-score grounded switch count, Mantine's spin role, and whether phazing or
  Outrage lock will force repeated entries.

If Mantine opens or enters:

- Decide whether Mantine is currently a spinner, Haze reset, confusion staller,
  or special wall. Do not set up or re-set hazards unless the follow-up punishes
  its likely reset move.

If Kingdra opens or Kingdra/Dragonair uses Dragon Dance:

- Stop the old plan and count the boosted state under local mechanics. Ask
  whether the current answer still survives, whether Haze/phazing is live, and
  whether Outrage lock can be baited.

If Outrage starts:

- Treat the user as committed for a short sequence. Identify the pivot,
  sacrifice, Haze/phaze, recovery, or revenge line that improves because the
  move is locked.

Worst plausible branch:

- The player lets Gligar start hazards or Toxic the main answer, Mantine erases
  the player's own hazard/setup route, Kingdra or Dragonair gets one Dragon
  Dance, and the player has no healthy piece left to stop boosted Surf/coverage
  or exploit Outrage lock.

Abandon conditions:

- The intended Kingdra or Dragonair answer is poisoned, paralyzed, or below the
  required damage threshold.
- Mantine can Haze or spin without giving up decisive pressure.
- MiracleBerry Dragonair still has its one-time status cure and the current plan
  depends on status.
- Quick Claw changes a speed assumption that mattered.
- Steelix's local Steel/Dragon type or Outrage category behavior invalidates a
  vanilla matchup assumption.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Clair is a setup-conversion lesson. The useful GSC transfer is not species
  centrality; it is the habit of preserving the one piece that stops the live
  win condition, then updating immediately when hazards, status, boosts, or
  locked-move commitments change whether that piece still works.
