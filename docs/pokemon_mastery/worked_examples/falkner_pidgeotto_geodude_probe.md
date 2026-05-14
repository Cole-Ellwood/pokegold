# Worked Example: Falkner Pidgeotto vs Geodude Probe

Purpose: turn a local Falkner benchmark into a reusable advice recipe for
probe turns. This is opponent-model calibration, not a rule that Falkner must
always click Sand Attack.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster: `data/trainers/parties.asm`, `FalknerGroup`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_falkner_pidgeotto_vs_geodude_scout_probe_001`
- Move data: `data/moves/moves.asm`; Sand Attack is 100 accuracy,
  Rock Throw is 90 accuracy, and Gust is 100 accuracy.
- Accuracy stages: `data/battle/accuracy_multipliers.asm`; one accuracy drop
  uses the 75/100 multiplier.
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`

Expert-source framing:

- Smogon's risk/reward article emphasizes comparing the likely line with the
  most dangerous outcome, not treating prediction as style points:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.
- Smogon's prediction introduction says prediction should be based on risk and
  reward, with more information improving decision quality:
  <https://www.smogon.com/smog/issue1/introduction_to_prediction>.
- Smogon's lead articles frame lead choice as a tradeoff between the first
  turns and the full battle plan:
  <https://www.smogon.com/smog/issue10/leads> and
  <https://www.smogon.com/smog/issue9/leads>.

## Public State

```text
Boss active:
  Pidgeotto Lv12 at 72%, Sharp Beak
  Known moves: Tackle, Gust, Sand Attack
  Candidate moves: Sand Attack, Gust, switch Noctowl

Player active:
  Geodude Lv12 at 86%
  Revealed moves: Tackle, Defense Curl
  Public priors: Rock Throw plausible, Magnitude plausible
```

The oracle labels one Sand Attack as best, Gust as acceptable, and switching to
Noctowl as catastrophic in this exact public card.

## Damage And Accuracy Anchors

```text
Pidgeotto Gust -> Geodude:
  2-3 damage, 6-9% of Geodude's current HP.

Pidgeotto Quick Attack -> Geodude:
  2-3 damage, 6-9% of Geodude's current HP.

Pidgeotto Tackle -> Geodude:
  2-3 damage, 6-9% of Geodude's current HP.

Geodude Tackle -> Pidgeotto:
  7-9 damage, 25-32% of Pidgeotto's current HP.

Geodude Rock Throw -> Pidgeotto:
  27-32 damage, 96-114% of Pidgeotto's current HP.
  This is not a guaranteed KO at Pidgeotto's shown 72% HP because the minimum
  roll can leave Pidgeotto alive.
```

Accuracy anchor:

```text
Rock Throw starts at 90 accuracy.
After one Sand Attack, Geodude's next Rock Throw is priced around 90 * 0.75,
before any other local modifiers or later state changes.
```

## Route Interpretation

Why one probe is defensible:

- Pidgeotto's direct damage into Geodude is tiny in this state.
- Geodude's plausible Rock Throw branch can nearly remove Pidgeotto at once.
- Sand Attack does not solve the matchup permanently, but it changes the swing
  branch before Pidgeotto commits to damage.
- Switching to Noctowl avoids the decision while preserving none of Pidgeotto's
  lead pressure and does not prove the Rock-risk branch is handled.

Why repeated probing is bad:

- Accuracy drops disappear if Geodude leaves and later returns.
- Pidgeotto still needs to make progress before Geodude, another answer, or a
  switch clears the value of the first probe.
- If Sand Attack already landed once, the next turn must be re-scored around
  current HP, current accuracy, and whether Rock Throw still changes the fight.

## Player-Side Advice

If advising the user with Geodude active:

1. Treat Rock Throw as the main pressure route, but do not call it guaranteed
   from the shown state.
2. If Pidgeotto uses Sand Attack, immediately re-score hit reliability.
3. Do not keep clicking Rock Throw automatically if a miss plus Gust leaves the
   player in a worse Noctowl or Spearow position.
4. Consider whether switching clears the accuracy drop without handing Falkner
   a better route.
5. If Pidgeotto is in lower HP range, attacking rises because the probe no
   longer changes enough.

If modeling Falkner:

1. One Sand Attack is a risk-reduction probe when Pidgeotto damage is tiny and
   Geodude's Rock Throw branch is live.
2. After the probe lands or misses, Falkner must move toward progress: Gust,
   Quick Attack range, switch timing, or a re-scored plan.
3. Repeating Sand Attack without a conversion plan is not the lesson.

## Decision Recipe

Use a probe move when all of these are true:

```text
direct damage barely changes the route;
the opponent has a plausible swing move;
the probe reduces that branch immediately;
the wrong branch is survivable;
the next turn has a concrete progress plan.
```

Do not use a probe move when:

```text
the opponent is already in guaranteed removal range;
the probe can be cleared for free;
the probe gives a setup, sleep, recovery, or switch route;
the probe user must be preserved and cannot afford the current turn;
there is no planned conversion after the probe.
```

## Transfer Lesson

This is the small-boss version of high-level risk management. A move can be
correct even when it does no damage, but only if it changes the branch that
actually decides the route. The moment the branch has been changed, the job
becomes conversion, not repeating the same safety move.

## Unverified Before Real Turn Advice

- Exact user Geodude stats, current HP, moves, item, and PP.
- Whether Rock Throw is actually known, available, and selected by the user.
- Whether Geodude has a safer current move or a teammate that handles Pidgeotto
  and Noctowl better.
- Whether local battle modifiers, passives, crits, misses, or prior chip have
  changed the damage or accuracy thresholds.
