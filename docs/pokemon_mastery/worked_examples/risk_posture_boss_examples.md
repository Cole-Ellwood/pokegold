# Worked Example: Risk Posture In Boss Fights

Purpose: decide whether a turn should minimize catastrophe or accept a
calculated risk because the safe line is losing.

Source basis:

- Smogon Risk/Reward:
  https://www.smogon.com/resources/beginner/bw_risk_reward
- Smogon Long Term Thinking:
  https://www.smogon.com/rs/articles/long_term_thinking
- Smogon Introduction to Prediction:
  https://www.smogon.com/smog/issue1/introduction_to_prediction

## Pattern

Public state:

```text
Current route posture:
  ahead / stable / losing slowly / forced risk

Our live route:
  converter:
  blockers:
  required resources:

Boss live route:
  converter:
  next step:
  what makes it irreversible:

Candidate safe move:
Candidate risky move:
Worst plausible branch:
Payoff if risky move works:
```

Decision:

```text
Ahead or stable:
  prefer the move that preserves the route and avoids irreversible branches.

Losing slowly:
  prefer the move that creates a real route, even if it accepts a plausible
  punish, because the no-risk line is not actually safe.
```

## Case 1: Ahead, Do Not Gamble The Answer

Boss shape:

```text
The boss has one remaining setup converter.
Our team has one healthy answer and one slower cleaner.
The current active can make chip but risks losing the answer to surprise
coverage, status, or a one-time trade.
```

Bad advice:

```text
Stay in for extra damage because it might end the fight faster.
```

Better posture:

```text
If the existing route wins by preserving the answer, do not invite an
irreversible branch just to shorten the battle. Attack only if the damage
crosses a forced threshold or the answer is no longer needed.
```

Boss transfer:

- Against Lance or Blue, if the final setup answer is still required, do not
  spend it on a midgame prediction unless the current threat becomes
  unanswerable otherwise.
- Against Morty or Sabrina, do not take a KO into a known Destiny Bond, Perish,
  Encore, or trap branch if switching or non-KO control keeps the route covered.

## Case 2: Behind, Safe Play Loses Slowly

Boss shape:

```text
The boss has a recovery loop, hazard clock, or setup route that our normal
switching cannot break.
Our only possible route is to reveal coverage, use sleep/status, explode,
double-switch, or force a narrow damage threshold now.
```

Bad advice:

```text
Use the safest-looking switch because the risky move might fail.
```

Better posture:

```text
If the safe switch only returns to the same losing loop, it is not safe. Accept
the risk when the payoff creates a named route: removes the blocker, forces the
boss's last recovery, creates clean entry, denies setup, or opens revenge range.
```

Boss transfer:

- Against Misty, if Starmie or Quagsire can reset forever, the correct turn may
  be a risky status, lure, or setup denial rather than another harmless pivot.
- Against Jasmine, if Spikes plus phazing already makes repeated switching
  impossible, a direct conversion or sacrifice can become better than preserving
  material that no longer has time to matter.

## Case 3: Unknown Posture, Audit Before Choosing

Boss shape:

```text
Both sides have plausible routes, but it is unclear whether we are ahead.
```

Audit:

1. If we choose the low-risk move five turns in a row, who wins?
2. Which piece becomes irreplaceable in that sequence?
3. What boss action makes the position irreversible?
4. What one move changes that route map?
5. Is the risk branch avoidable, or is it the price of creating a route?

Extracted rule:

```text
Safe means preserving a winning or stable route.
Safe does not mean avoiding variance while the opponent's route becomes
inevitable.
```

## Expert-Play Anchor: Forced Dynamic Punch Route

Review:

- `../reviews/2026-05-13_smogtours-gen2ou-891179.md`

In that GSC game, Glfgno7 spent Steelix's Explosion to remove Zapdos, then had
to try Gengar Dynamic Punch into a sleeping Snorlax. That was not a clean
endgame plan: misses and Sleep Talk Rest / Earthquake branches could ruin it.
But after the phazing/trade resource was spent, the line became a forced
high-variance conversion attempt rather than a reckless style play.

Boss transfer:

- If the boss's recovery loop, setup route, or hazard clock already beats every
  conservative move, choose the narrow line that actually changes the route:
  status before Rest, sacrifice into clean entry, high-damage coverage, phaze,
  Haze, Encore, or a damage roll that opens priority range.
- Do not label a line "safe" if it only preserves material while the boss's
  route becomes irreversible.
