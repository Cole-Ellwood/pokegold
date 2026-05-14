# Worked Example: Koga First-Three-Turn Clock Ownership

Purpose: convert Koga's route sheet into a forced lead and early-turn planning
drill. This is not a full player-team plan until the user's team, levels, HP,
moves, and items are known.

Local evidence:

- Boss route sheet: `../boss_route_maps/koga_turn1_route_sheet.md`
- Roster source: `data/trainers/parties.asm`, `KogaGroup`
- Live AI trace: `audit/boss_ai_trace/koga_live.txt`
- Status absorber recipe: `status_absorber_assignment_boss_examples.md`
- Status reset recipe: `status_reset_map_boss_examples.md`
- Contained waiting policy: `smogtours_909431_contained_waiting_loop.md`

Expert source anchors:

- Smogon's GSC status material treats poison as strongest when the team can
  make switching and time costly.
- Smogon's GSC Spikes material treats Spikes, poison, phazing, and forced Rest
  as route pressure only when the rest of the position supports the clock.

## Public Boss State

```text
Koga lead: Ariados @ Leftovers
Moves: Spikes / Toxic / Leech Life / Spider Web

Known backline routes:
- Tentacruel can Rapid Spin and Haze.
- Muk can Curse / Toxic / Rest.
- Nidoking has broad Expert Belt coverage.
- Umbreon can Toxic, Confuse Ray, Moonlight, Pursuit, and use Mint Berry.
- Crobat can clean after poison, hazards, and chip.
```

The live Koga trace records Toxic, Giga Drain, and Spider Web among top
first-turn options and chooses Toxic in that captured state. Do not generalize
that to every player team, but treat early Toxic / trap pressure as a real
branch, not flavor.

## Drill Prompt

Before choosing the lead or first move, answer:

```text
If Ariados uses Spikes, Toxic, or Spider Web on turn 1, which side owns turns
2-3?
```

Rank these move classes:

```text
attack Ariados / pivot to absorber / set hazards / use status / setup /
recover-wait / sacrifice for clean entry
```

## Public State A: Expendable Pressure Lead

- Our active threatens a clean 2HKO or better on Ariados.
- This active is not the only Nidoking answer, Crobat answer, spinner, phazer,
  or late revenge piece.
- If poisoned, it can still complete its Ariados job before the poison clock
  matters.
- If trapped, it still wins the locked exchange or forces Ariados low enough
  that Koga loses the opening clock.

Expected policy A: attack Ariados or force immediate survival pressure. Toxic
is acceptable to absorb only because the active's remaining job is already
scheduled and short. Waiting, weak setup, or hazards are lower unless they also
deny Ariados's next clock.

## Public State B: Irreplaceable Answer In Front

- Our active is the only reliable Nidoking or Crobat answer.
- Ariados can Toxic or Spider Web before the active has completed that later
  job.
- The active's damage does not remove Ariados before poison / trap changes the
  next route.

Expected policy B: do not volunteer the irreplaceable answer into the clock.
Pivot before trap if possible, attack only if it prevents the clock, or choose
a controlled sacrifice that creates clean entry for a less valuable Ariados
answer. Calling this "status absorption" is a preservation failure unless the
later Nidoking / Crobat route is otherwise covered.

## Public State C: Setup Or Hazard Lead

- Our active can set hazards or boost.
- Tentacruel is alive with Rapid Spin and Haze.
- The setup / hazard turn does not immediately force Ariados, Tentacruel, Muk,
  or Crobat into a losing response.
- No spinblock, Haze punish, or immediate converter is already named.

Expected policy C: setup or hazards are suspect. Koga can use Ariados to start
the clock, Tentacruel to erase the route, and Muk / Crobat / Nidoking to cash
out the poisoned or chipped answer. Pressure the route owner first, or name the
specific punish that makes Tentacruel's reset turn bad.

## Public State D: Contained Waiting Claim

- Ariados has already been removed or made harmless.
- Koga's active is on a poison / recoil / low-HP / Rest-sleep clock.
- Our answer still covers the immediate punish, and Koga cannot spin, Haze,
  setup, heal, or trap into a better route this turn.

Expected policy D: waiting can be legal only here. The answer must name the
external clock, the contained punish branch, and the piece that remains
irreplaceable. If any one is missing, choose active denial instead.

## Answer-Changing Information

- Whether the proposed lead is the only Nidoking or Crobat answer.
- Whether Ariados is in immediate KO or forced-survival range.
- Whether the player has poison immunity, Rest, Heal Bell, item cure, Haze,
  phazing, spinblock, or priority.
- Whether Koga's Full Restore has been spent before a Toxic plan is trusted.
- Whether type chart, passive, or damage evidence changes Nidoking or Crobat
  answer assignments.
- Whether Tentacruel can spin or Haze without losing route material.

## Common Wrong Answers

- "Absorb Toxic with the low-HP Pokemon" without naming its remaining job.
- "Set hazards because Koga has a long team" while Tentacruel can remove them
  for little cost.
- "Use setup because Ariados is passive" while Spider Web or Toxic changes
  switch freedom before the boost converts.
- "Wait out poison / recovery" before proving that Koga cannot use the turn to
  start a stronger clock.

## Transfer Lesson

Koga teaches clock ownership. Poison, Spikes, Spider Web, Haze, Rapid Spin,
Rest, Moonlight, Pursuit, and fast cleanup are not separate annoyances. They
are ways to decide who controls the next three turns. The correct lead and move
are the ones that keep Koga's first clock from landing on an irreplaceable
piece.
