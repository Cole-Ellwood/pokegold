# Worked Example: Sabrina Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Sabrina as a screens, Encore,
sleep, Perish Song, Baton Pass, Choice-lock, and bulky-Rest fight. This is a
team-agnostic planning artifact; exact move choices still depend on the
player's roster, HP, items, Speed, damage ranges, and current Sleep Clause
state.

## Evidence Checked

Local evidence:

- Roster source: `data/trainers/parties.asm`; Sabrina uses Mr. Mime, Jynx,
  Espeon, Alakazam, and Hypno.
- Existing local boss map:
  `docs/pokemon_mastery/boss_route_maps/sabrina_turn1_route_sheet.md`.
- Move table: `data/moves/moves.asm`; the relevant moves are Light Screen,
  Reflect, Encore, Lovely Kiss, Ice Beam, Psychic, Perish Song, Hidden Power,
  Morning Sun, Baton Pass, Ice Punch, ThunderPunch, Fire Punch, Seismic Toss,
  Rest, and Thunder Wave.
- Generated mechanics table:
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Screens: `engine/battle/effect_commands.asm` sets local Light Screen and
  Reflect counters to 5; `engine/battle/core.asm` ticks them down.
- Encore: `engine/battle/move_effects/encore.asm` locks the target into the
  last legal move for 3-6 turns, subject to last-move and PP failure cases.
- Sleep Clause and Rest: `engine/battle/effect_commands.asm`.
- Baton Pass: `engine/battle/move_effects/baton_pass.asm`; it requires another
  living party member, applies stat multipliers to the incoming enemy, applies
  Spikes damage, and clears several volatile states such as Encore.
- Choice Specs: `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `engine/battle/late_gen_held_items.asm`; local Choice Specs boosts special
  damage by 1.5x and move-locks.
- Morning Sun and Hidden Power:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Morning Sun recovery
  depends on time of day and weather, and Hidden Power type plus base power
  depend on DVs.

Expert anchors:

- Smogon GSC Jynx material treats Lovely Kiss as a major tempo tool and notes
  that Sleep Talk users can absorb sleep while threatening Jynx back.
- Smogon GSC Jynx discussion treats Perish Song as a way to punish passive
  answers, but also emphasizes Jynx's limited bulk.
- Smogon GSC Espeon material frames Morning Sun, Speed, Special Attack, and
  Hidden Power coverage as the source of its longevity and threat pressure.
- Smogon Baton Pass material is a useful abstraction here: screens, sleep,
  Encore, Perish Song, phazing, and Haze are all chain-control or
  anti-control tools. Sabrina is not a full Baton Pass team, but Espeon can
  still preserve position.
- Smogon move-restriction material reinforces the general lock principle:
  once a Choice or Encore lock is established, the next move is about exploiting
  or escaping the lock, not replaying the pre-lock plan.

## Boss Snapshot

```text
Mr. Mime @ TwistedSpoon:
  Light Screen / Reflect / Encore / Psychic

Jynx @ NeverMeltIce:
  Lovely Kiss / Ice Beam / Psychic / Perish Song

Espeon @ TwistedSpoon:
  Hidden Power / Psychic / Morning Sun / Baton Pass

Alakazam @ Choice Specs:
  Psychic / Ice Punch / ThunderPunch / Fire Punch

Hypno @ Leftovers:
  Seismic Toss / Rest / Thunder Wave / Psychic
```

## Turn-1 Game Plan

Primary route:

- Enter with a lead that pressures Mr. Mime without donating a passive move to
  Encore. The opening goal is not simply "hit Psychic types"; it is to prevent
  Mr. Mime from turning the first turns into a screen clock that protects Jynx,
  Espeon, Alakazam, or Hypno.

Backup route:

- If a screen, Encore, sleep, Perish Song, paralysis, Baton Pass, Rest, or
  Choice lock appears, stop following the opener script and rebuild around that
  active clock.

Best lead profile:

- Pressures Mr. Mime immediately.
- Still has a plan if Light Screen or Reflect goes up.
- Does not need to click setup, recovery, hazards, or a low-value status move
  into Encore.
- Is not the only Jynx sleep answer or the only Alakazam coverage answer.

Avoid as lead:

- A passive setup or recovery Pokemon that Mr. Mime can Encore.
- The only sleep absorber if Jynx can later use Lovely Kiss to remove it from
  the battle.
- A one-pivot special wall plan that must answer all of Jynx, Espeon,
  Alakazam, and Hypno.
- A type-slogan pivot into Espeon before Hidden Power type and damage are
  verified.

First move job:

- Remove or force Mr. Mime, deny a free screen if the damage race requires it,
  or choose a line that remains playable if the screen goes up. Do not click a
  support move unless the Encore branch is already acceptable.

## Boss Route Triage

Must deny first:

- Mr. Mime's screen plus Encore route if the player's opener is passive.
- Jynx's Lovely Kiss route if the player has only one sleep-safe answer or if
  losing that piece opens Alakazam, Espeon, or Hypno.
- Alakazam's first Choice Specs attack if no safe coverage map exists yet.

Can sometimes delay:

- Mr. Mime's raw Psychic damage if screen and Encore are not winning routes.
- Hypno if the player can force Rest and convert the sleep turns, or if
  Thunder Wave does not disable a required speed-control piece.
- Espeon if Hidden Power has not shown the coverage needed to beat the current
  answer and Morning Sun cannot erase meaningful progress.

Immediate punish branches:

- Mr. Mime Encores a support, recovery, setup, hazard, or low-value status
  move for 3-6 turns.
- Jynx lands Lovely Kiss on the one piece needed to handle Alakazam or Espeon.
- Jynx uses Perish Song and forces a switch sequence that gives Sabrina the
  better entry.
- Alakazam reveals a Choice Specs attack that breaks the assumed pivot map.
- Hypno uses Thunder Wave on the only revenge or tempo piece.

Accumulating branches:

- A five-turn Light Screen or Reflect changes which attacking category can
  make progress.
- Morning Sun erases chip if the player never reaches a threshold that forces
  Espeon out or into a bad Baton Pass.
- Hypno's Leftovers and Rest turn shallow damage into a reset unless the player
  has a planned cash-out during sleep.
- Baton Pass preserves Espeon's position or passes a boosted state if one
  exists; the incoming target must be evaluated as the new board, not as the
  previous matchup.

Endgame branches:

- Choice Specs Alakazam cleans after the real special answer is slept,
  paralyzed, or chipped below coverage range.
- Hypno slows the endgame with Thunder Wave, Seismic Toss, Rest, and
  Leftovers.
- Jynx creates the final forced switch with Lovely Kiss or Perish Song.

## Resource Rules

Preserve:

- A sleep plan for Jynx.
- A broad Alakazam plan before its Choice Specs lock is known.
- The piece that can pressure Hypno during or immediately after Rest.
- The piece that can still make progress through the active screen category.
- Any answer whose job depends on Espeon's Hidden Power type remaining
  unverified.

Spend:

- A Pokemon already Encored into a harmless move only if switching loses less
  than staying.
- A slept Pokemon only if Sleep Clause, role completion, or a clean-entry
  route makes its remaining job replaceable.
- A screen turn by pivoting or stalling only if the pivot does not hand
  Sabrina a stronger Jynx, Alakazam, Espeon, or Hypno entry.

Do not spend:

- The only Alakazam answer before the lock is revealed.
- The only Jynx answer as a generic lead.
- A special wall that is also the Hypno breaker or Thunder Wave absorber.
- A revenge route just to deal chip that Morning Sun or Rest can erase.

## Turn Ledger Prompts

Before turn 1:

```text
Which of my Pokemon handles Mr. Mime without becoming Encore bait?
Which Pokemon can absorb or punish Lovely Kiss?
Which Pokemon handles Alakazam before its Choice lock is known?
Which Pokemon handles Hypno after Thunder Wave or Rest?
What changes if Espeon's Hidden Power is Fire, Water, or another type?
```

If Mr. Mime uses Light Screen or Reflect:

- Record which screen, set the counter to five turns, and re-rank physical
  versus special pressure. The correct response may be attacking through the
  other category, forcing Mr. Mime out, pivoting, or preserving material until
  the screen fades.

If Mr. Mime uses Encore:

- Identify the locked move, remaining lock turns, and whether the active
  Pokemon can still improve a route. If not, switch immediately unless the
  switch gives Sabrina an even stronger entry.

If Jynx uses Lovely Kiss:

- Do not label the result by hit or miss alone. Ask whether the sleeping
  Pokemon was expendable, whether Sleep Clause is now occupied, and what Jynx's
  next best move is into the new state.

If Jynx uses Perish Song:

- Start the perish-count ledger and plan the forced switch sequence. The
  danger is often the entry Perish Song creates for another Sabrina Pokemon.

If Espeon uses Hidden Power:

- Treat the type and damage as evidence. Do not use "resisted," "neutral,"
  "super effective," or "immune" in the plan unless the claim is tied to the
  romhack type chart, passive effects, and observed damage.

If Espeon uses Morning Sun:

- Check time of day and weather. If recovery erases the damage race, switch to
  a route that forces status, threshold damage, PP pressure, or a bad Baton
  Pass instead of repeating chip.

If Espeon uses Baton Pass:

- Rebuild from the incoming Pokemon with any passed stat context and Spikes
  damage. Do not keep arguing about the Espeon matchup after Espeon has left.

If Alakazam attacks:

- Record the locked move immediately. Exploit the lock only if the pivot used
  to exploit it is not also required for Jynx, Espeon, or Hypno.

If Hypno uses Thunder Wave:

- Recalculate Speed-dependent routes. A paralyzed revenge killer may no longer
  be a revenge route.

If Hypno uses Rest:

- Decide whether the sleep turns are convertible. If not, Rest reset the damage
  race and the player needs a new route.

## Worst Plausible Branch

The player opens with a passive support move into Encore or free screens, then
uses the wrong category into a screen while Jynx sleeps the key special answer.
Alakazam enters before its Choice lock has been mapped and forces the player to
spend the backup answer. Hypno then paralyzes or Rests through the remaining
route, and Espeon uses Morning Sun or Baton Pass to deny the last attempt at
chip progress.

## Abandon Conditions

- A screen is active and the current route depends on the blocked category.
- The active Pokemon is Encored into a move that does not improve a route.
- The planned sleep absorber or Alakazam answer is asleep, paralyzed, or below
  its needed threshold.
- Perish Song is active and the next forced switch favors Sabrina.
- Alakazam's locked move contradicts the assumed pivot map.
- Espeon's Hidden Power type or damage contradicts the assumed answer.
- Morning Sun or Rest erases the damage race without creating a punish window.
- Baton Pass changes the active matchup.

## Answer-Changing Information

- Player roster, current HP, items, moves, Speed order, and PP.
- Whether Sleep Clause is free.
- Which screen is active and how many turns remain.
- Whether Mr. Mime has already spent or failed Encore.
- Whether Jynx is still healthy enough to force sleep or Perish Song.
- Espeon's actual Hidden Power type, base power, and damage.
- Time of day and weather for Morning Sun recovery.
- Alakazam's current Choice Specs lock.
- Whether Hypno can be forced to Rest and punished during sleep.
- Current paralysis state on the player's speed-control pieces.

## Extracted Recipe

Sabrina is a clock-and-lock fight. Light Screen, Reflect, Encore, sleep, Perish
Song, Choice Specs, Morning Sun, Baton Pass, Thunder Wave, and Rest all change
the time horizon of the battle. The correct move is usually the one that uses
or denies the active clock while preserving the piece that handles the next
Sabrina route. Type advantage is only useful after the romhack chart, passive
effects, Hidden Power evidence, and damage thresholds are known.
