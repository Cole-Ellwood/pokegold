# Koga Turn-1 Route Sheet

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
  list Koga as adaptive first-three: Ariados / Tentacruel / Muk.
- Spider Web uses `EFFECT_MEAN_LOOK` in `data/moves/moves.asm`; the battle
  command sets `SUBSTATUS_CANT_RUN` in `engine/battle/effect_commands.asm`.
- Haze uses `EFFECT_RESET_STATS` and resets both sides' stat stages in
  `engine/battle/effect_commands.asm`.
- Pursuit doubles damage on switching targets according to
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Moonlight recovery depends on time and weather in
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Leftovers, Mint Berry, and Expert Belt behavior is listed in
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`; Expert Belt requires
  local type-effectiveness evidence before assuming the boost on a specific
  matchup.
- Expert principle sources: Smogon GSC status, Spikes, threat-list, and
  trapping discussions.
- Forced drill:
  `../worked_examples/koga_first_three_turn_clock_ownership_drill.md`

Boss roster:

```text
Lv40 Ariados @ Leftovers:
  Spikes / Toxic / Leech Life / Spider Web

Lv41 Tentacruel @ Mystic Water:
  Rapid Spin / Surf / Sludge Bomb / Haze

Lv42 Muk @ Leftovers:
  Curse / Sludge Bomb / Toxic / Rest

Lv43 Nidoking @ Expert Belt:
  Earthquake / Sludge Bomb / Ice Beam / Thunderbolt

Lv42 Umbreon @ Mint Berry:
  Pursuit / Confuse Ray / Moonlight / Toxic

Lv44 Crobat @ Sharp Beak:
  Wing Attack / Toxic / Sludge Bomb / Hyper Beam
```

Boss likely openings:

- Koga is source-listed as adaptive first-three, not fixed Ariados.
- Plan for Ariados / Tentacruel / Muk, with Ariados favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Koga's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Ariados route:

- Goal: start the fight by stacking Spikes, Toxic, and Spider Web so the player
  loses switch freedom before Koga's bulk and fast cleanup matter.
- What it punishes: passive leads, setup leads that do not immediately convert,
  and letting an irreplaceable answer become trapped or poisoned.
- Denial idea: either remove Ariados quickly, force it to choose between hazard
  progress and survival, or pivot before Spider Web turns a normal bad matchup
  into a locked bad matchup.

Tentacruel route:

- Goal: undo the player's hazard or setup route with Rapid Spin and Haze while
  still threatening Water/Poison damage.
- What it punishes: assuming Spikes are progress before Koga's spinner is
  pressured, or setting up without checking whether Tentacruel can reset boosts.
- Denial idea: if the win route depends on hazards or boosts, Tentacruel must be
  forced out, chipped into range, trapped by a better clock, or made unable to
  spend the spin/Haze turn safely.

Muk route:

- Goal: become the bulky anchor through Curse, Sludge Bomb pressure, Toxic, and
  Rest.
- What it punishes: low-damage chip that lets Muk boost and Rest on schedule,
  and teams with no phaze, Haze, immediate damage, or Rest-punish plan.
- Denial idea: prevent free Curse turns. Force Rest only if the sleep turns can
  be punished; otherwise the damage just resets while poison and hazards keep
  working against the player.

Nidoking route:

- Goal: break the player's pivot map with four-way coverage and Expert Belt
  boosted super-effective hits.
- What it punishes: type-slogan switching and over-preserving one answer while
  the actual damage table says another coverage move is decisive.
- Denial idea: treat every intended pivot as unverified until type chart,
  passive, and damage evidence are checked. Preserve the real Nidoking answer
  even if it is not the obvious type-chart answer.

Umbreon route:

- Goal: stretch exchanges with Toxic, Confuse Ray, Moonlight, Mint Berry sleep
  insurance, and Pursuit pressure on switches.
- What it punishes: letting a weak attacker sit in while Toxic and recovery win,
  or switching a vulnerable special attacker without pricing Pursuit.
- Denial idea: do not fight Umbreon on vague "wallbreaker pressure." Name the
  resource being won: forcing Moonlight PP, landing a status it cannot shrug,
  bringing in a real breaker safely, or using the turn to stop a different Koga
  route.

Crobat route:

- Goal: convert prior poison, Spikes, and coverage damage into fast cleanup.
- What it punishes: spending the Crobat answer earlier to win a minor exchange,
  letting Toxic put that answer on a timer, or leaving weakened targets in Hyper
  Beam range.
- Denial idea: preserve one reliable Crobat answer or a faster revenge route
  until its damage thresholds are known. Slow Toxic from Crobat is less scary
  than immediate KO pressure if the player can remove it now.

## Player Plan Template

Primary route:

- Decide who owns the clock. Koga wants every early exchange to create a poison,
  hazard, trap, recovery, or cleanup timer. The player should either short-circuit
  that clock with immediate pressure or make Koga's timer land on a Pokemon whose
  role is already expendable.

Backup route:

- If Ariados gets Spikes or Toxic, stop treating the battle as six clean
  one-on-ones. Rebuild around layer count, trapped status, which Pokemon can
  still pivot, and whether Tentacruel can remove our hazards or Haze our setup.

Best lead profile:

- A lead that pressures Ariados, does not donate free Rapid Spin/Haze value to
  Tentacruel, and does not let Muk begin a Curse/Rest clock for free. It must
  not be the only answer to Nidoking or Crobat.
- A hazard or setup lead is good only if it can either survive Spider Web
  pressure, punish Tentacruel's reset, or force Koga to answer immediately.

Avoid as lead:

- The only Nidoking or Crobat answer if Ariados can poison or trap it.
- A slow setup Pokemon whose boosts are erased by Tentacruel.
- A hazard setter whose progress is immediately spun by Tentacruel with no
  punish.
- A special attacker that cannot hurt Umbreon and must switch through Pursuit
  pressure.

First-turn question:

```text
Which adaptive opener appeared?

Ariados: can we stop Spikes / Toxic / Spider Web from owning the next three
turns?

Tentacruel: is Rapid Spin, Haze, Surf, or Sludge Bomb the live reset route, and
does our lead punish that route?

Muk: can we prevent a free Curse / Toxic / Rest clock without spending the
Nidoking or Crobat answer?
```

Use the forced drill when this question is still fuzzy. The important early
classification is whether the proposed lead is an expendable pressure piece, an
irreplaceable Nidoking / Crobat answer, or a setup / hazard piece that
Tentacruel can reset.

If Ariados sets Spikes:

- Re-score around layer count, grounded player Pokemon, Tentacruel's spin role,
  and whether the player can punish Koga's next status or trap attempt.

If Ariados uses Toxic:

- Check whether the poisoned Pokemon is irreplaceable. If yes, pivot before the
  poison clock combines with Spikes or Crobat cleanup. If no, use the poisoned
  Pokemon to create progress before it is spent.

If Ariados uses Spider Web:

- Treat the trapped Pokemon as an active-state emergency. Ask whether it wins
  the locked exchange, can force Ariados out by damage, or must preserve HP for
  a later Koga threat. Do not assume normal pivot plans still exist.

If Tentacruel opens or enters:

- Decide whether the live reset is Rapid Spin or Haze. If the player's route
  does not depend on hazards or boosts, do not overchase Tentacruel while
  Nidoking, Muk, Umbreon, or Crobat remains the real converter.

If Muk opens or enters:

- Deny free Curse if the player lacks a stable boosted-Muk answer. Force Rest
  only when the sleep turns can be converted before Koga's poison and hazard
  clocks make the exchange worse.

Worst plausible branch:

- The player lets Ariados start Spikes plus Toxic or trap pressure, then uses a
  setup or hazard route that Tentacruel erases, while Muk gains Curse/Rest
  tempo and Nidoking or Crobat finishes once the real answers are poisoned or
  chipped.

Abandon conditions:

- The only Nidoking or Crobat answer is poisoned, trapped, or below its required
  damage threshold.
- Tentacruel can spin or Haze without giving up a decisive turn.
- Muk reaches a Curse/Rest loop that cannot be broken before poison and hazards
  keep ticking.
- Umbreon turns the exchange into Moonlight/Toxic/confusion/Pursuit attrition
  instead of losing a concrete resource.
- Crobat can clean with fast attacks or Hyper Beam after prior chip.
- Type-chart, passive, or damage evidence contradicts the assumed pivot.

Snorlax study transfer:

- Koga does not need Snorlax to teach the Snorlax lesson. Muk is the bulky
  anchor, Umbreon is the attrition wall, Nidoking is the coverage breaker, and
  Crobat is the cleaner. The transferable principle is to identify the role that
  owns the long game, then preserve or remove the specific pieces that decide
  that route.
