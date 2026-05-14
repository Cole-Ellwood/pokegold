# Worked Example: Controlled Sack For Clean Entry In Boss Fights

Purpose: distinguish a route-preserving sacrifice from a lazy "this Pokemon is
low HP" sack.

Source basis:

- Smogon Long Term Thinking:
  https://www.smogon.com/rs/articles/long_term_thinking
- Smogon Risk/Reward:
  https://www.smogon.com/resources/beginner/bw_risk_reward
- Smogon Introduction to Prediction:
  https://www.smogon.com/smog/issue1/introduction_to_prediction

## Pattern

Public state:

```text
Current active:
Pokemon that wins if it enters safely:
Boss route that must be denied:
Sacrificed piece's remaining jobs:
Opponent's best response if we do not sack:
Opponent's best response if we do sack:
```

Decision:

```text
Sack is legal only if:
  the sacrificed piece has no unique remaining job;
  hard-switching the route piece risks breaking the route;
  the next entry creates progress immediately;
  and the boss cannot use the sack turn to create a worse setup, recovery,
  weather, hazard, or status route.
```

## Bugsy Shape

Boss route:

- Ariados and Ledian soften or support the team so Scyther can convert.

Controlled-sack line:

- If the player's true Scyther answer cannot safely hard-switch through Toxic,
  Reflect, Quiver Dance, or boosted contact damage, it can be better to let a
  spent early-game piece faint and bring the Scyther answer in clean.

Illegal version:

- Sacking the only Scyther answer, or sacking a piece while Ledian is still free
  to boost/pass instead of taking the KO.

Answer-changing information:

- Whether the sacrificed piece still handles Ledian's Baton Pass route.
- Whether the incoming Scyther answer survives Quick Attack cleanup after entry.
- Whether Bugsy is likely to attack, boost, pass, or use a status/drain move.

## Karen Shape

Boss route:

- Gengar starts hazard/sleep pressure, Donphan contests hazards or phazes,
  Crobat disrupts with Toxic/Confuse Ray/Safeguard, then Tyranitar or Houndoom
  converts with Dragon Dance or Sunny Day.

Controlled-sack line:

- A sack can bring the correct answer into Tyranitar after a Dragon Dance or
  Houndoom after sun without eating the boosted hit on the switch.

Illegal version:

- Sacking the only piece that still answers the other late route. For example,
  spending a Water or bulky special answer to enter safely on Houndoom may lose
  if that same piece was still required for Tyranitar, Crobat, or Donphan.

Answer-changing information:

- Sun turns remaining.
- Whether Tyranitar has already boosted.
- Whether Crobat's Safeguard blocks the intended status answer.
- Whether the sack gives Gengar or Donphan free hazard/spin/phaze value.

## Lance Shape

Boss route:

- Lance presents repeated Dragon Dance or Quiver Dance threats, with Outrage and
  Hyper Beam creating commitment windows.

Controlled-sack line:

- A sack can absorb Outrage or Hyper Beam and give the real answer a clean entry
  into a locked move, confusion branch, or recharge turn.

Illegal version:

- Sacking a piece that is still the only answer to Kingdra, Gyarados, or final
  Dragonite. A clean entry now is not useful if it leaves the next setup route
  uncovered.

Answer-changing information:

- Which Lance threats remain.
- Whether Outrage is locked and how many turns remain.
- Whether Hyper Beam recharge actually applies in the current state.
- Whether the incoming answer survives the next boosted hit after entry.

## Transfer Rule

The transferable lesson is not "sack more." The lesson is:

```text
Preserve pieces that still answer live routes.
Spend pieces that no longer answer live routes if doing so creates a clean
entry for the actual win condition.
```

When unsure, compare the line to hard-switching. The sack is only better if it
improves the next state, not merely because the current Pokemon is damaged.
