# Worked Example: Misty Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Misty as a rain-clock,
sleep/paralysis, recovery-anchor, and mixed Water-pressure fight. This is a
team-agnostic planning artifact; exact advice still depends on the player's
team, HP, moves, items, Speed, damage ranges, and current Sleep Clause state.

## Evidence Checked

Local evidence:

- Roster source: `data/trainers/parties.asm`; Misty uses Politoed, Starmie,
  Quagsire, Lapras, and Lanturn.
- Existing local boss map:
  `docs/pokemon_mastery/boss_route_maps/misty_turn1_route_sheet.md`.
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`;
  Misty can open with Politoed, Starmie, or Quagsire.
- Move table: `data/moves/moves.asm`; relevant moves are Rain Dance,
  Hypnosis, Surf, Ice Beam, Recover, Hydro Pump, Psychic, Thunder, Curse,
  Earthquake, Rest, and Thunder Wave.
- Weather source: `engine/battle/move_effects/rain_dance.asm`,
  `engine/battle/move_effects/thunder.asm`, and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; rain lasts five turns,
  boosts Water damage, weakens Fire damage, and lets Thunder bypass the
  accuracy check.
- Recovery and item source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Recover restores 50%
  max HP, Rest fully heals with local Rest sleep timing, Leftovers heals 1/16
  max HP, type-boost items are 1.2x, and Wise Glasses boost special damage by
  1.1x.
- Generated mechanics table:
  `docs/agent_navigation/hack_mechanics_reference.md`; Hypnosis is 60%
  accurate, Hydro Pump is 120 BP / 80% accurate, Surf and Ice Beam are 95 BP,
  Thunder is 120 BP / 70% accurate before rain, and Thunder Wave is 100%
  accurate subject to normal immunity/failure rules.

Expert anchors:

- Smogon weather material treats weather as a mechanic-changing condition and
  emphasizes that manual rain teams operate on a finite timer.
- Smogon GSC threat material highlights Starmie's Speed, versatility, and
  instant recovery as the reason it can keep coming back in long games.
- Smogon GSC Spikes material uses Starmie as a classic example of why recovery
  must be pressured by status, forced switches, or thresholds rather than
  shallow chip.
- Smogon GSC lower-tier discussion of Rain Dance Lapras is useful as an
  abstraction: rain-boosted Water pressure plus Ice / Electric coverage can
  turn a bulky Water into a short-window breaker.

## Boss Snapshot

```text
Politoed @ Leftovers:
  Rain Dance / Hypnosis / Surf / Ice Beam

Starmie @ Wise Glasses:
  Recover / Hydro Pump / Psychic / Thunder

Quagsire @ Soft Sand:
  Curse / Earthquake / Surf / Rest

Lapras @ Leftovers:
  Rain Dance / Surf / Ice Beam / Thunder

Lanturn @ Magnet:
  Thunder Wave / Surf / Thunder / Ice Beam
```

Known boss fixed/adaptive opener source:

```text
Adaptive first-three:
  Politoed / Starmie / Quagsire
```

## Turn-1 Game Plan

Primary route:

- Cover the adaptive first-three opening while deciding who owns rain and
  recovery. If Politoed opens, price sleep/rain. If Starmie opens, deny free
  Recover stabilization. If Quagsire opens, deny free Curse. Misty wants five
  rain turns, sleep, paralysis, Recover, Rest, and Leftovers to make the
  player's answers run out before Misty's bulk does.

Backup route:

- If Hypnosis lands, rain starts, Thunder Wave hits a speed-control piece, or
  Quagsire gets a Curse, stop using the original clean matchup plan. Rebuild
  around the active clock: sleep turns, rain turns, paralysis, recovery PP, or
  Curse boosts.

Best lead profile:

- Has a useful first-turn job into Politoed, Starmie, and Quagsire.
- Does not become useless if Politoed spends turn 1 on Rain Dance, Starmie
  uses Recover pressure, or Quagsire starts Curse.
- Is not the only answer to Starmie, Lapras, or Quagsire.
- Can tolerate or punish the Hypnosis hit branch, or lets another expendable
  piece absorb sleep without opening Starmie.

Avoid as lead:

- The only Starmie or Lapras answer if Politoed can remove it with Hypnosis.
- A slow setup lead that lets Politoed get rain, Starmie Recover-loop, or
  Quagsire Curse without immediate cost.
- A fast cleaner whose entire route dies if Lanturn later lands Thunder Wave.
- A type-slogan answer that ignores Quagsire, Lanturn, Ice Beam, rain Thunder,
  and local type/passive evidence.

First move job:

- Give the first move one job based on the actual opener: deny Politoed
  rain/sleep, force Starmie below a meaningful Recover threshold, deny Quagsire
  Curse, or pivot while preserving the separate Starmie/Lapras/Quagsire
  answers. A first move that only deals chip is suspect if Starmie, Lapras, or
  Quagsire can later erase or exploit that exchange.

## Boss Route Triage

Must deny first:

- Politoed's Hypnosis if the target would be the only Starmie, Lapras, or
  Quagsire answer.
- Rain Dance if the current player team cannot survive five turns of boosted
  Water damage plus reliable Thunder.
- Quagsire's Curse if the player lacks Haze, phazing, strong special pressure,
  Grass-route proof, or a way to punish Rest.
- Lanturn's Thunder Wave if the player needs Speed to revenge Starmie or
  Lapras.

Can sometimes delay:

- Politoed's raw Surf / Ice Beam if it is not sleeping a key piece or enabling
  rain.
- Starmie's Recover if the player is using the recovery turn to set up a real
  converter, status it, force a threshold, or pivot into a better route.
- Lapras if rain is not active and the player's Lapras answer is distinct from
  the Starmie answer.
- Lanturn damage if paralysis is irrelevant to the current route.

Immediate punish branches:

- Politoed sleeps the only safe Water or Starmie answer.
- Politoed sets rain and Starmie enters with Wise Glasses Hydro Pump, Psychic,
  or reliable Thunder pressure.
- Quagsire Curses while the player stays in with shallow damage.
- Lanturn paralyzes the revenge killer or setup converter.

Accumulating branches:

- Rain lasts five turns; every switch or low-value move spends one of those
  turns while Misty's attacks are improved.
- Starmie's Recover resets weak chip unless the player reaches a threshold,
  applies status, forces bad timing, or uses the turn to advance a concrete
  route.
- Quagsire's Curse plus Rest asks a different question from Misty's special
  attackers: can the player stop a physical anchor without spending the pieces
  needed for Starmie and Lapras?
- Lapras can reset rain and continue the same weather clock after Politoed.
- Lanturn can make Misty's slower bulk easier to support by spreading
  paralysis.

Endgame branches:

- Starmie wins by outspeeding and recovering through anything that fails to
  cross a real threshold.
- Quagsire wins if Curse/Rest turns make the player's physical answers
  irrelevant and the special answer has already been spent.
- Lapras or Lanturn wins if rain/paralysis leaves only damaged pivots.

## Resource Rules

Preserve:

- At least one Starmie answer that works before and after rain is active.
- A distinct Quagsire answer; do not assume the same Water answer covers Curse
  plus Soft Sand Earthquake.
- A sleep plan for Politoed's Hypnosis.
- A speed-control plan that remains live after Lanturn's Thunder Wave branch.
- Damage evidence for any type claim, especially if relying on Electric,
  Grass, Water, Ice, or Ground labels under the romhack chart and passive
  system.

Spend:

- A slept Pokemon only if its job is replaceable and Sleep Clause or clean
  entry makes the trade useful.
- A rain turn by pivoting only if the pivot denies a stronger route than it
  gives Misty.
- A low-value piece to absorb a rain-boosted hit if that preserves the true
  Starmie, Quagsire, or Lapras answer.

Do not spend:

- The only fast route into Lanturn's Thunder Wave unless the rest of the plan
  does not depend on Speed.
- The Starmie answer just to punish Politoed if Lapras or Lanturn can then
  force the same answer later.
- The Quagsire answer before Quagsire's Curse route has been accounted for.
- A strong special attacker into random chip if Starmie can Recover and
  Quagsire still needs to be denied.

## Turn Ledger Prompts

Before turn 1:

```text
What happens if Misty opens Politoed?
What happens if Misty opens Starmie?
What happens if Misty opens Quagsire?
Which Pokemon handles Starmie in rain?
Which Pokemon handles Quagsire after one Curse?
Which Pokemon can absorb Thunder Wave without killing the route?
What exact evidence supports any type-effectiveness claim?
```

If Misty opens Politoed:

- Price Hypnosis and Rain Dance before choosing the punish. The goal is not
  only to beat Politoed; it is to prevent sleep or rain from making Starmie,
  Lapras, or Quagsire harder to answer.

If Politoed uses Rain Dance:

- Set a five-turn rain ledger. Re-rank Surf, Hydro Pump, Thunder, Fire damage,
  and every switch cost. The next move should either cash out the setup turn,
  force Misty to waste rain turns, or preserve the piece needed after rain
  expires.

If Politoed uses Hypnosis:

- Separate hit/miss from decision quality. If it hits, name the sleeping
  Pokemon's role and decide whether the fight can continue without that role.
  If it misses, do not overextend unless the miss branch creates a real route.

If Misty opens Starmie:

- Ask whether the lead can cross a threshold before Recover matters. If not,
  the best move may be status, pivoting, forcing a Recover punish, or preserving
  the stronger answer for rain turns.

If Starmie enters:

- Ask whether the current move crosses a threshold before Recover matters. If
  not, choose between status, pivoting, forcing a Recover punish, or preserving
  the real answer.

If Starmie uses Recover:

- Treat it as a route reset unless the player used that turn to gain something
  concrete: setup, status, a safe entry, PP pressure, or a forced damage range.

If Misty opens Quagsire:

- Deny Curse immediately or name the exact answer to boosted Earthquake / Surf
  / Rest. Do not spend the Starmie or Lapras answer just because Quagsire is
  the current active.

If Quagsire uses Curse:

- Reclassify Misty from pure special pressure to mixed-anchor pressure. The
  answer now needs to beat boosted Earthquake / Surf / Rest, not merely "a
  Water type."

If Quagsire uses Rest:

- Check whether the sleep turns are convertible before calling Rest a win for
  the player. If the player cannot force damage, setup, phazing, or a safe
  entry, Rest may have reset the route.

If Lapras enters:

- Check rain first. Lapras outside rain is bulky coverage pressure; Lapras in
  rain is a short-window breaker with Surf and reliable Thunder.

If Lanturn enters:

- Price Thunder Wave before damage. The important outcome may be the loss of
  the player's Speed route, not the HP lost this turn.

## Worst Plausible Branch

The player chooses a Politoed-only lead plan, Misty opens Starmie or Quagsire,
and the first turn either lets Recover stabilize or gives Curse a free anchor
route. The player spends the wrong answer to catch up, later loses the
remaining speed route to Lanturn's Thunder Wave, and Lapras resets rain.

## Abandon Conditions

- Misty opens Starmie or Quagsire instead of Politoed.
- Rain is active and the current route assumed clear-weather damage or
  unreliable Thunder.
- The only Starmie, Lapras, or Quagsire answer is asleep, paralyzed, or below
  the required threshold.
- Starmie can Recover without giving up meaningful pressure.
- Quagsire has boosted and no immediate denial route remains.
- Lanturn has paralyzed the speed-control piece.
- Lapras resets rain when the plan depended on rain ending.
- Type-chart, passive, item, weather, or damage evidence contradicts the
  assumed pivot.

## Answer-Changing Information

- Player roster, current HP, items, moves, Speed order, and PP.
- Whether Sleep Clause is free.
- Which adaptive opener appeared.
- Whether rain is active and how many turns remain.
- Whether Politoed and Lapras can still reset rain.
- Whether Starmie is in Recover range or can be forced below a threshold.
- Whether Quagsire has Curse boosts or Rest PP pressure.
- Which Pokemon can take Thunder Wave without losing the route.
- Whether the proposed Electric, Grass, Ground, or Water pivot is supported by
  local type-chart, passive, and damage evidence.

## Extracted Recipe

Misty is a weather-ownership, adaptive-opening, and anchor-map fight. Rain
changes damage and Thunder reliability for only five turns, so every switch,
sleep turn, recovery turn, and paralysis matters. The correct plan is not
"bring a Water answer"; it is to preserve the separate answers to Starmie
recovery, Quagsire Curse/Rest, Lapras rain extension, and Lanturn paralysis
while making Misty's rain turns expire or fail to convert.
