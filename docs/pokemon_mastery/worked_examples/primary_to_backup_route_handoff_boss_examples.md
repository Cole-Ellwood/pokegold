# Worked Example: Primary-To-Backup Route Handoff

Purpose: practice abandoning an opening plan before it becomes a forced loss.

Source basis:

- Smogon Knowing How to Find Your Win Condition:
  https://www.smogon.com/forums/threads/knowing-how-to-find-your-win-condition.3474271/
- Smogon Prediction and Planning:
  https://www.smogon.com/smog/issue20/prediction_ubers
- Smogon Long Term Thinking:
  https://www.smogon.com/rs/articles/long_term_thinking
- Smogon Risk/Reward:
  https://www.smogon.com/resources/beginner/bw_risk_reward

## Pattern

Public state:

```text
Primary route before:
Required resources:
Changed fact:
Primary route after:
Best backup route:
Piece to preserve for backup:
Resource from old route now spendable:
Opponent route to deny now:
```

Decision:

```text
Handoff when:
  the primary route now needs unsafe assumptions;
  the backup route has a concrete next move;
  and the move also covers or shortens the opponent's live route.
```

## Misty Shape

Primary route before:

- Pressure Politoed, deny rain/sleep tempo, then use the prepared Water answer
  against Starmie or Lapras.

Changed fact:

- Hypnosis lands on the Water answer, Rain Dance starts, or Lanturn paralyzes
  the planned cleaner.

Handoff:

- Stop trying to play the clean special-Water plan. Rebuild around the healthy
  remaining answer: status Starmie if legal, force Recover with stronger damage,
  deny Quagsire's Curse/Rest route, or spend a lesser piece to reset weather
  turns before the true answer re-enters.

Bad continuation:

- Keeping the asleep/paralyzed piece as the center of the plan while Misty gets
  rain-accurate Thunder, Recover, or Curse turns.

Answer-changing information:

- Sleep state and wake risk.
- Rain turns remaining.
- Whether Starmie is in Recover loop range.
- Whether Quagsire has boosted or Rests safely.

## Clair Shape

Primary route before:

- Use the planned anti-Dragon Dance answer while pressuring Gligar's hazards.

Changed fact:

- Gligar gets Spikes or Toxic onto the answer, Mantine Hazes the setup route, or
  MiracleBerry Dragonair absorbs the first status attempt.

Handoff:

- Shorten the plan. If the preserved answer no longer survives repeated entries,
  switch to immediate damage, Haze/phazing, controlled sack into revenge range,
  or exploiting Outrage lock. The backup route may be less elegant, but it may
  be the only route that does not depend on a poisoned or chipped answer.

Bad continuation:

- Continuing the hazard or status plan while Mantine can erase it and Kingdra or
  Dragonair can boost behind the lost turns.

Answer-changing information:

- Spikes layer count and grounded switch count.
- Toxic/paralysis on the anti-Dragon Dance answer.
- Whether Mantine is alive and can Haze or Rapid Spin.
- Whether Outrage is locked and punishable.

## Red Shape

Primary route before:

- Beat Pikachu cleanly while preserving answers to Espeon, Snorlax, sun users,
  and Blastoise.

Changed fact:

- Pikachu chips or paralyzes the intended Snorlax answer, Espeon gets Reflect or
  Calm Mind, Snorlax begins a Curse/RestTalk route, or sun changes the starter
  damage map.

Handoff:

- If the Snorlax answer is compromised, the fight may need to become shorter:
  force Snorlax low before Rest, use phazing/Haze if available, spend a one-time
  route trade, or preserve a different emergency answer even if it means giving
  up the original anti-Pikachu plan. If Espeon owns the setup route instead,
  hand off to the special setup denial plan before Snorlax appears.

Bad continuation:

- Winning the Pikachu exchange while spending the only answer to CurseLax or
  Calm Mind Espeon, then treating the later loss as bad luck.

Answer-changing information:

- Snorlax answer HP/status/PP.
- Reflect turns and Calm Mind boosts.
- Sun turns and whether SolarBeam is one-turn.
- Whether Blastoise can punish the intended special route with Mirror Coat.

## Transfer Rule

The handoff is not surrendering the plan. It is updating the win route after the
public state changes:

```text
Old route cost went up.
New route cost went down.
Spend resources according to the new route map.
```

In live advice, the sentence should be explicit:

```text
The old plan was X. It changed because Y. The new plan is Z, so this turn we
must preserve A and can spend B.
```
