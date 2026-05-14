# Worked Example: Erika Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Erika as a sleep, Encore, Leech
Seed, weather, setup, spin, and Explosion control-chain fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `ErikaGroup`.
- Boss route map: `../boss_route_maps/erika_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Type chart, item behavior, sleep clause, Sunny Day, Synthesis, Encore,
  Explosion, setup, move categories, and Grass/Flying caveats:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Move data: `data/moves/moves.asm`.
- Leech Seed source: `engine/battle/move_effects/leech_seed.asm`.
- Rapid Spin source: `engine/battle/move_effects/rapid_spin.asm`.
- AI tendency evidence, not a strategic law:
  `engine/battle/ai/boss_policy_move.asm` and
  `engine/battle/ai/scoring.asm`.

Expert study anchors:

- GSC status material: sleep is powerful, but Sleep Talk, wake turns, clause
  state, and the target chosen determine whether it creates a route or only a
  temporary delay.
- GSC Exeggutor material: Sleep Powder, status pressure, and Explosion are
  route-enabling tools; Exeggutor rarely sweeps by itself but can remove or
  disable the piece that made another route safe.
- GSC Explosion material: Explosion is a trade into a named route, not an
  automatic value move; the defender must know which answer cannot be offered
  to the boom.
- Weather and setup material: manual weather turns are only valuable if they
  let a later attack, recovery turn, or setup window convert before the weather
  expires.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Erika

Known boss roster:
  Tangela / Jumpluff / Bellossom / Victreebel / Exeggutor

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a sleep plan, a Jumpluff Encore / Leech Seed plan, a Bellossom
  anti-setup plan, a Victreebel physical/setup answer, and a way to avoid
  losing the wrong piece to Exeggutor's Explosion; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  local Sleep Clause, three-layer Spikes, Rapid Spin clearing all Spikes and
  Leech Seed on the spinner, Sunny Day lasting five turns, Synthesis recovery
  depending on both weather and time of day, Encore lasting 3-6 turns,
  Explosion halving target Defense, Grass hitting Flying neutrally in this
  hack, Grass-type immunity to Leech Seed, MiracleBerry curing Jumpluff's first
  status, Muscle Band boosting Victreebel's physical damage by 1.1x, Life Orb
  boosting Exeggutor's damage by 1.3x with recoil, and type-boost items using
  1.2x when relevant

Missing evidence:
  exact player team, HP, levels, moves, items, sleep-clause state, speed
  relations, damage ranges, whether the lead is Grass-type or otherwise immune
  to Leech Seed, whether the lead can punish Tangela's Rapid Spin, whether
  Bellossom outspeeds after Quiver Dance, whether Victreebel survives the
  chosen hit after Swords Dance, and whether Exeggutor's Explosion removes an
  irreplaceable answer
```

## Output Shape

Primary route:

- Deny Erika's control chain before it reaches a converter. Tangela can remove
  hazards or put up Reflect, Jumpluff can sleep, seed, Encore, or set sun,
  Bellossom and Victreebel convert free turns into setup, and Exeggutor can
  trade with Sleep Powder or Explosion. The first plan should reduce Erika's
  control turns without sacrificing the Bellossom, Victreebel, or Explosion
  answers.

Backup route:

- If the opener is slept, paralyzed, seeded, Encored, or forced through
  Reflect/weather, stop following the opening script. Rebuild around the
  remaining sleep-clause state, weather turns, screen turns, and which anti-
  setup answer is still healthy.

Boss route priority:

```text
immediate:
  Jumpluff Sleep Powder or Encore if it locks the current Pokemon into setup,
  recovery, hazards, or another low-impact move; Exeggutor Explosion if it can
  remove the only Bellossom or Victreebel answer; Victreebel Swords Dance if no
  immediate denial remains.

accumulating:
  Tangela Rapid Spin or Reflect, Leech Seed plus switches, Stun Spore speed
  loss, Sunny Day enabling SolarBeam and Synthesis timing, and repeated Life
  Orb attacks forcing the wrong defensive piece into Explosion range.

endgame:
  Bellossom or Victreebel cleans once sleep, Reflect, weather, or Explosion has
  damaged the player's answer map. Exeggutor can also simplify into an endgame
  by trading for the wrong piece.
```

Boss route to deny first:

- Deny whichever control turn makes the next converter hard to answer. If the
  user's team relies on hazards, Tangela's spin matters immediately. If the
  user's route relies on setup, recovery, or a passive support turn, Jumpluff's
  Encore matters immediately. If the user's only Grass answer is one piece,
  Exeggutor's Sleep Powder / Explosion branch may be the true first route to
  preserve against even before Exeggutor appears.

Boss route that can be delayed:

- Tangela can be delayed if hazards are not the user's route and Reflect does
  not change a key physical threshold. Bellossom can be delayed while it is
  unboosted and there is a confirmed anti-setup answer. Victreebel cannot be
  delayed once Swords Dance plus Muscle Band Sludge Bomb / Razor Leaf changes
  from "damage" into a sweep route.

Best lead:

- A lead that pressures Tangela without being ruined by Stun Spore, does not
  give Jumpluff an obvious Encore target, and is not the only answer to
  Bellossom, Victreebel, or Exeggutor. A Grass-type or status-resistant lead is
  useful only if it also makes progress; merely resisting the first annoyance
  lets Erika build the next one.

Avoid as lead:

- A hazard lead if Tangela spins for free and the team has no spin punish.
- A passive setup or recovery lead that Jumpluff can Encore for 3-6 turns.
- The only Victreebel or Bellossom answer if Sleep Powder can remove it.
- The only Exeggutor answer if Explosion would open the rest of Erika's team.
- Any plan that assumes Grass/Flying, Psychic/Poison, or other type matchups
  from memory instead of the local chart.

First move plan:

- Give the first move a job: remove or force Tangela, deny spin/Reflect, status
  something after checking MiracleBerry and sleep clause, set pressure that
  prevents Jumpluff from entering freely, or pivot before the wrong piece is
  paralyzed or seeded. Do not click a passive move unless the Encore branch has
  already been priced.

First 3 turns as intentions, not a script:

1. Identify whether Tangela's first action changes the route: Rapid Spin,
   Reflect, Stun Spore, or Giga Drain each asks for a different answer.
2. If Jumpluff enters or is likely to enter, stop and price Sleep Powder, Leech
   Seed, Encore, and Sunny Day before any setup, recovery, hazard, or low-
   damage move.
3. When Bellossom, Victreebel, or Exeggutor appears, switch from "beat the
   active" to "protect the answer map": which piece must survive the setup or
   Explosion branch?

Piece to preserve:

- The piece that can answer both Bellossom after Quiver Dance and Victreebel
  after Swords Dance, if one exists. If those jobs are split, do not spend
  either answer on Tangela chip or Jumpluff annoyance unless the exchange
  removes the route it was preserving against.
- The Explosion absorber or low-value sacrifice that prevents Exeggutor from
  trading into an irreplaceable answer.

Piece that can be spent:

- A slept or seeded Pokemon can be spent only if Sleep Clause, Leech Seed,
  weather, and setup state mean its future role is gone and the sacrifice gives
  clean entry to the converter or anti-setup answer. Low HP alone is not enough
  to call it expendable.

Worst plausible branch:

- Tangela removes hazards or paralyzes the speed-control piece, Jumpluff locks
  the player into a passive move or seeds the pivot, Sunny Day lets Bellossom
  use SolarBeam / Synthesis cleanly, Victreebel gets the free Swords Dance
  turn, and Exeggutor keeps Explosion available to remove the last answer.

Abandon conditions:

- The current Pokemon is asleep, seeded, paralyzed, or Encored and that state
  changes its future role.
- Sleep Clause is occupied or cleared in a way that changes Erika's next sleep
  line.
- Reflect, Sunny Day, or a changed Synthesis value flips the damage race.
- Bellossom has boosted and the assumed anti-setup answer no longer wins.
- Victreebel has boosted and the current line cannot immediately KO, phaze,
  Haze, status, or pivot to a confirmed answer.
- Exeggutor can Explode on the only remaining converter answer.
- Tangela can remove hazards without giving up a worse route.

What information would flip the lead or first move:

- Whether the lead can punish Rapid Spin or does not care about hazards.
- Whether Stun Spore ruins the speed control needed for Jumpluff, Bellossom, or
  Victreebel.
- Whether the team has a safe sleep absorber and whether Sleep Clause is free.
- Whether Jumpluff is faster than the intended move and can Encore it.
- Whether Bellossom's Quiver Dance crosses a Speed or survival threshold.
- Whether Victreebel's +2 Muscle Band damage crosses a KO threshold.
- Whether Exeggutor's Life Orb damage plus Explosion removes an irreplaceable
  piece.
- Whether local type/passive evidence changes a planned "safe" switch.

## Extracted Lesson

Erika is a conversion-timing fight. Her individual moves look annoying rather
than lethal, but each is trying to buy a later turn: spin buys hazard freedom,
Reflect buys a physical setup window, Sleep Powder buys agency loss, Leech Seed
buys switching pressure, Encore punishes passive sequencing, Sunny Day buys
SolarBeam and recovery timing, and Explosion buys route removal. The correct
plan is not "bring a Fire or Flying move." The correct plan is to decide which
control turn matters for the user's team, deny that turn, and preserve the
answer that stops the actual converter.
