# Misty Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Opening policy source:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md`; Misty is in
  `AdaptiveLeadMap`, so the opening can be Politoed, Starmie, or Quagsire
  rather than guaranteed Politoed.
- Weather source: `engine/battle/move_effects/rain_dance.asm`,
  `engine/battle/move_effects/thunder.asm`, and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; rain lasts five turns,
  boosts Water damage, weakens Fire damage, and makes Thunder bypass the
  accuracy check.
- Hypnosis is 60 accuracy according to
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Recover restores 50% max HP; Rest fully heals and applies Rest sleep timing
  according to `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Curse, Thunder Wave, Thunder, Hydro Pump, Ice Beam, Surf, and Psychic are
  listed in `docs/agent_navigation/hack_mechanics_reference.md`.
- Wise Glasses, Magnet, Soft Sand, and Leftovers behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert principle sources: Smogon Rain Offense, GSC status, GSC Quagsire,
  setup denial, recovery pressure, and weather timer planning.
- Lead principle sources: Smogon Team Preview material only as route-triage
  analogy, plus Creating / Selecting a Lead; judge the player lead by Misty's
  source-known adaptive opener set and by its later role after turns 1-2. Do
  not treat this as symmetrical Team Preview.
- Worked recovery tempo note:
  `docs/pokemon_mastery/worked_examples/misty_starmie_meganium_recover_tempo.md`

Boss roster:

```text
Lv58 Politoed @ Leftovers:
  Rain Dance / Hypnosis / Surf / Ice Beam

Lv63 Starmie @ Wise Glasses:
  Recover / Hydro Pump / Psychic / Thunder

Lv60 Quagsire @ Soft Sand:
  Curse / Earthquake / Surf / Rest

Lv61 Lapras @ Leftovers:
  Rain Dance / Surf / Ice Beam / Thunder

Lv62 Lanturn @ Magnet:
  Thunder Wave / Surf / Thunder / Ice Beam
```

Boss likely openings:

- Misty is source-listed as adaptive first-three, not fixed Politoed.
- Plan for Politoed / Starmie / Quagsire, with Politoed favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Misty's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Politoed route:

- Goal: start rain, land Hypnosis, and make Surf / Ice Beam trades happen under
  Misty's preferred tempo.
- What it punishes: slow leads, plans that ignore sleep miss/hit branches, and
  assuming rain is only a damage buff rather than a five-turn clock.
- Denial idea: decide whether the live danger is sleep or rain. If Hypnosis
  hits, re-score the sleeping Pokemon's role; if rain starts, count the five
  turns before choosing a pivot.

Starmie route:

- Goal: use Speed, Wise Glasses, Recover, Hydro Pump, Psychic, and rain-accurate
  Thunder pressure to deny weak chip and punish wrong pivots.
- What it punishes: trying to win by small damage while Recover resets the
  exchange, and switching by type slogan without local damage evidence.
- Denial idea: either cross a real damage threshold, force Recover on a turn
  that gives the player progress, status it if legal, or preserve a verified
  answer until rain and Thunder pressure are understood.

Quagsire route:

- Goal: use Curse, Earthquake, Surf, and Rest to become Misty's physical-side
  anchor.
- What it punishes: teams that prepare only for special Water pressure, weak
  chip that lets it Curse/Rest, and assuming Rest turns are automatically
  punishable.
- Denial idea: prevent free Curse turns. If Quagsire Rests, punish the sleep
  turns only if the player can actually convert before it wakes or switches the
  matchup.

Lapras route:

- Goal: reset or extend the rain plan, then pressure with Surf, Ice Beam, and
  Thunder while Leftovers stretches the exchange.
- What it punishes: single-answer Water plans and overcommitting the Starmie
  answer before Lapras appears.
- Denial idea: treat Lapras as a bulky route extender. If rain is up, its
  attack choices and Thunder reliability are different from a clear-weather
  exchange.

Lanturn route:

- Goal: use Thunder Wave, Magnet Thunder, Surf, and Ice Beam to slow the
  player's route and cover the pivots that expect only Water damage.
- What it punishes: relying on one fast cleaner, or letting paralysis make
  Starmie/Lapras/Quagsire easier to support.
- Denial idea: identify whether Lanturn is the status spreader, special tank,
  or coverage bridge. If the player's route needs speed, Thunder Wave may be
  more important than raw damage.

## Player Plan Template

Primary route:

- Cover the adaptive opening set of Politoed / Starmie / Quagsire, then decide
  who owns the rain and recovery clocks. Misty wants rain, sleep, recovery,
  paralysis, and bulky Water pressure to make the player run out of stable
  answers before Starmie or Lapras trades favorably.

Backup route:

- If Hypnosis lands, rain starts, or Thunder Wave hits the cleaner, abandon the
  original clean matchup plan. Rebuild around sleep state, rain turns,
  paralysis, and which Water answer is still healthy.

Best lead profile:

- A lead that has a real first-turn job into Politoed, Starmie, and Quagsire
  without being the only answer to Starmie, Quagsire, or Lapras. It should
  either deny the rain/sleep opening, cross a Starmie threshold before Recover
  matters, or prevent Quagsire from taking a free Curse.

Avoid as lead:

- The only Starmie or Lapras answer if Politoed can sleep it.
- A slow setup Pokemon that lets Politoed start rain, Starmie Recover-loop, or
  Quagsire Curse for free.
- A fast cleaner that loses its route if Lanturn later lands Thunder Wave.
- A damage-only plan that cannot beat Recover or Rest cycles.

First-turn question:

```text
Which adaptive opener appeared?

Politoed: can we deny or price Rain Dance and Hypnosis without spending the
Starmie, Quagsire, or Lapras answer?

Starmie: can we cross a Recover threshold, apply decisive status, or preserve
the answer before rain-accurate Thunder pressure matters?

Quagsire: can we deny free Curse or prove the boosted-Quagsire answer still
works without exposing the special Water answers?
```

## Adaptive Opener Matrix

Use this before choosing a lead or first move. Misty can open with any of the
first three source-party Pokemon, so a Politoed-only plan is not a plan.

Lead candidate check:

```text
candidate:
job into Politoed:
job into Starmie:
job into Quagsire:
later role after turns 1-2:
what opener invalidates it:
what route it preserves:
```

Politoed opener:

- Required first-turn job: deny or price Rain Dance and Hypnosis. If the lead
  takes sleep, its remaining job must still function while asleep or the team
  must have a separate Starmie / Quagsire / Lapras plan.
- Route ladder: sleep or rain state -> Starmie/Lapras Thunder and Water
  pressure, or Quagsire entry into a slower team.
- Good first move classes: direct pressure that punishes Rain Dance, status or
  sleep absorption that still preserves the route, or pivoting only if the
  pivot does not become the only later Water answer.

Starmie opener:

- Required first-turn job: cross a damage threshold, force bad Recover timing,
  apply decisive status, or create safe entry for the real Starmie answer.
- Route ladder: failed threshold -> Recover reset -> Misty keeps speed and
  coverage control while the player spends the wrong answer.
- Good first move classes: immediate threshold damage, status that changes the
  Recover loop, item/control pressure, or preservation if the current lead is
  the only Lapras/Lanturn answer.

Quagsire opener:

- Required first-turn job: deny free Curse or prove the player has a stable
  boosted-Quagsire answer that does not also need to cover Starmie/Lapras.
- Route ladder: free Curse -> Rest reset or boosted Earthquake/Surf -> player
  loses the physical-side answer while still needing special Water answers.
- Good first move classes: strong special pressure, phazing/Haze/status if
  available and locally legal, or a pivot that brings in the Quagsire answer
  without donating the first Curse.

Lead approval rule:

- Approve a lead only if it has a coherent first-turn job into all three
  adaptive openers, or if the uncovered opener is explicitly accepted as forced
  risk with a backup route.
- Downgrade a lead that wins Politoed but lets Starmie Recover-loop or
  Quagsire Curse for free.
- Downgrade a lead that beats one opener by spending the only Starmie, Lapras,
  or Lanturn answer.
- If the lead's best line differs by opener, write the first move as a
  conditional matrix, not as one script.

If Misty opens Politoed:

- Decide whether the live danger is sleep or rain. Price Hypnosis hit/miss and
  Rain Dance before treating Surf or Ice Beam as the whole exchange.

If Politoed uses Rain Dance:

- Start the weather ledger. Count rain turns, price boosted Water attacks,
  Thunder accuracy, and whether the player can punish the setup turn before
  Misty gets the payoff.

If Politoed uses Hypnosis:

- Separate hit/miss outcome from decision quality. Re-score the sleeping
  Pokemon's future role and whether sleep opened Starmie, Quagsire, or Lapras.

If Misty opens Starmie:

- The recovery-pressure route is immediate. Ask whether the lead can force a
  damage threshold, status, bad Recover timing, or clean pivot before Starmie
  starts trading with Wise Glasses coverage.

If Starmie enters:

- Ask whether direct damage crosses a threshold before Recover matters. If not,
  the plan must be status, forcing bad recovery timing, preserving a stronger
  answer, or using another route.

If Misty opens Quagsire:

- The physical-anchor route is immediate. Deny Curse or identify the exact
  special/phazing/Haze/status route that beats Curse plus Rest without spending
  the Starmie or Lapras answer.

If Quagsire uses Curse:

- Stop treating Misty as pure special pressure. Count boosted Earthquake,
  Surf, Rest timing, and whether the Quagsire answer is still available.

If Lapras enters:

- Check the weather state first. Lapras in rain is a different route from
  Lapras outside rain because Surf and Thunder change practical pressure.

If Lanturn enters:

- Price Thunder Wave before switching a faster route piece. A paralyzed cleaner
  may no longer be a real plan against Misty's remaining bulk.

## Post-KO Handoff Matrix

Use this after any correct KO or forced removal. The KO is progress only if the
next Misty route is covered.

If Politoed is removed:

- Rain and Hypnosis pressure may be reduced, but Starmie, Quagsire, Lapras, and
  Lanturn still test different answers.
- Re-rank the next route by current weather: Starmie/Lapras become more urgent
  in rain; Quagsire becomes more urgent if the player spent the physical-side
  answer to beat Politoed.
- Do not spend the only Starmie or Lapras answer just because the sleep lead is
  gone.

If Starmie is removed:

- The fast Recover bridge is gone, but the player must immediately re-score
  Quagsire Curse/Rest, Lapras rain extension, Lanturn Thunder Wave, and
  Politoed sleep/rain if still alive.
- Preserve a Grass or special-pressure route for Quagsire unless exact damage
  says the current active can also handle Lapras/Lanturn afterward.
- This is the route tested by
  `worked_examples/misty_starmie_meganium_followup_chain.md`: correct first
  move -> new state -> new route owner.

If Quagsire is removed:

- The physical Curse/Rest anchor is gone, so special Water pressure may become
  the whole fight.
- Re-rank Starmie/Lapras/Lanturn by rain turns, paralysis risk, and whether the
  Quagsire answer can now be spent as a status absorber, sack, or pivot.
- Do not over-preserve the Quagsire answer by old role memory if its unique job
  is complete.

If Lapras is removed:

- Rain extension and bulky Surf / Ice Beam / Thunder pressure are reduced, but
  Starmie can still own recovery tempo and Lanturn can still paralyze the
  cleaner.
- If rain is gone and Politoed is also gone, fire/ground/electric routes may
  change value; verify local type/passive and damage evidence before claiming a
  new safe pivot.

If Lanturn is removed:

- The Thunder Wave bridge is gone, so speed-dependent routes become more
  reliable if they survived earlier damage.
- Re-rank remaining Water anchors by recovery and rain, not by fear of
  paralysis that no longer exists.

Replacement uncertainty rule:

- If local post-KO replacement policy is unknown, choose the next entry or move
  that covers the highest-severity remaining route family, not the one a human
  would most likely send.
- If the current active is low, statused, or needed later, do not stay in after
  a KO unless the likely replacement can be removed immediately or the route is
  already forced.
- If a replacement route would punish the current active but another teammate
  can enter only on the free switch, use the free switch now; do not wait for a
  damaging turn to make the same entry.

Worst plausible branch:

- The player chooses a Politoed-only lead plan, Misty opens Starmie or
  Quagsire, and the first turn either lets Recover stabilize or gives Curse a
  free anchor route. The team then spends the wrong answer to catch up and
  later loses speed or pivot freedom to Lapras and Lanturn while rain turns
  make Thunder and Water pressure more reliable.

Abandon conditions:

- Misty opens Starmie or Quagsire instead of Politoed, invalidating the
  rain/sleep-first script.
- The only Starmie/Lapras answer is asleep, paralyzed, or below its required
  damage threshold.
- Rain is active and the current route assumed clear-weather damage.
- Starmie can Recover without giving up meaningful pressure.
- Quagsire has boosted and no immediate denial route remains.
- Lanturn has paralyzed the speed-control piece.
- Type-chart, passive, item, weather, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Misty replaces Snorlax with several anchor shapes: Starmie as fast recovery
  pressure, Quagsire as Curse/Rest anchor, Lapras as bulky weather extender, and
  Lanturn as paralysis bridge. The transferable GSC habit is to ask which
  recovery or status clock must be denied before it becomes the endgame.
