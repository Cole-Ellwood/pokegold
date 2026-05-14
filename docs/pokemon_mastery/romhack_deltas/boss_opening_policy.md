# Romhack Delta: Boss Opening Policy

Status: source-verified from local assembly. Not yet runtime-fixture verified
in an emulator trace.

Scope: Pokemon Gold romhack / Gym Leader Lab trainer battles. This is not a
vanilla GSC or competitive Team Preview claim.

## Source Evidence

- `engine/battle/core.asm`: battle start sets `wEnemySwitchMonIndex` to zero,
  calls `MaybePickAdaptiveEnemyLead`, then calls `EnemySwitch`.
- `engine/battle/core.asm`: if no predetermined switch index exists and
  `wBattleHasJustStarted` is set, `CheckWhetherSwitchmonIsPredetermined`
  returns party index 0.
- `engine/battle/ai/boss_policy_move.asm`: `MaybePickAdaptiveEnemyLead` is a
  blind weighted opener for selected major trainers. It prefers the first
  living party member but can select the next two living party members.
- `constants/battle_constants.asm`: adaptive-lead weights are approximately
  70 / 20 / 10 with three living options, or 80 / 20 with two.
- `data/trainers/ai_tiers.asm`: `AdaptiveLeadMap` lists the trainer classes and
  ids that use this opener.

## Verified Facts

Most trainers start with the first living party member in source-party order.

The following current boss-route targets are adaptive-lead trainers:

```text
Chuck
Jasmine
Pryce
Clair
Will
Bruno
Koga
Karen
Lance
Brock
Misty
Lt. Surge
Erika
Janine
Sabrina
Blaine
Blue
```

For those trainers, the opening lead is not a single fixed species. The source
selects among the first three living party members with weighted odds when
three are available.

The current source check did not find these route-map bosses in
`AdaptiveLeadMap`:

```text
Falkner
Bugsy
Whitney
Morty
Red
```

Treat those as first-listed lead fights unless another local source or runtime
trace contradicts that.

## Strategic Translation

Do not import competitive Team Preview literally. In this romhack, the player
or advisor can inspect boss rosters before a planned fight, but the boss AI
does not get symmetrical knowledge of the player's unrevealed team. The boss
may still have a source-defined adaptive opener.

The opening question is:

```text
Which lead states can the source actually produce, and which player lead keeps
the later answer map intact across those starts?
```

For non-adaptive bosses, pre-battle planning can focus harder on the first
listed party member while still preserving answers to the later routes.

For adaptive bosses, a player lead must be tested against the first three
source-party members, not only the default lead. A lead that beats option 1 but
spends the only answer to option 2 or option 3 is suspect.

## Before Advising A Boss Lead

Ask:

1. Is this trainer in `AdaptiveLeadMap`?
2. If not, what is the first living party member in `data/trainers/parties.asm`?
3. If yes, what are the first three living party members and their route jobs?
4. Which player lead covers the weighted opener set while preserving the later
   anchor, setup, weather, hazard, recovery, or priority answer?
5. Which opening requires a different abandon condition on turn 1?
6. Would a runtime trace or emulator observation contradict the source reading?

## Benchmark / Review Ideas

- Adaptive boss where option 1 is easy but option 2 threatens the only answer
  to the ace.
- Adaptive boss where the best player lead is not best into the most likely
  opener, but survives all three starts and preserves the route map.
- Non-adaptive boss where overplanning for impossible alternate leads makes the
  turn-1 plan too passive.
- Runtime trace check for one adaptive trainer and one non-adaptive trainer.

## Remaining Verification

- Run emulator or trace fixtures to confirm observed lead frequencies for at
  least one adaptive boss.
- Confirm whether any special battle type, rematch table, or script mutates the
  source-party order before this opener runs.
