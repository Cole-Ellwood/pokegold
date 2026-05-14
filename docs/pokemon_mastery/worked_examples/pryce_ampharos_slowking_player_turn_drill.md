# Worked Example: Pryce Slowking vs Ampharos Player-Turn Drill

Purpose: convert `pryce_slowking_ampharos_preservation.md` into user-facing
advice from Ampharos's side. The hard part is planning for Pryce's best pivot
without overpredicting away from a guaranteed active-target KO.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- `pryce_slowking_ampharos_preservation.md`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `romhack_defensive_answer_preservation_pryce_001`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `pryce_slowking_vs_ampharos_ground_pivot`
- Damage evidence checked with `python -m tools.damage_debugger.matchup`.

Expert-source framing:

- Smogon double-switch and pivot material: a likely switch can be punished, but
  only when the predicted branch is strong enough to justify the risk.
- Smogon checks/counters material: Piloswine is not an abstract answer; it is a
  current-entry durability and retaliation question.

## Public State

```text
Pryce active:
  Slowking Lv33 at 68%, Leftovers
  Revealed moves: Surf / Psychic / Thunder Wave

Pryce bench:
  Dewgong at 41%
  Sneasel at 100%
  Piloswine at 63%

Player active:
  Ampharos Lv34 at 80%
  Revealed moves: ThunderPunch / Thunder Wave
  Public prior: Dragon coverage plausible

Field:
  No weather
  No screens
```

Damage anchors:

```text
Ampharos ThunderPunch -> Slowking at 68%:
  75-89 damage, guaranteed KO from current HP.

Ampharos ThunderPunch -> Piloswine at 63%:
  22-26 damage, 25-30% of Piloswine's current HP.

Piloswine Soft Sand Earthquake -> Ampharos at 80%:
  88-104 damage, 76-90% of Ampharos's current HP.

Slowking Surf -> Ampharos at 80%:
  11-14 damage, 9-12% of Ampharos's current HP.
```

## Live-Turn Advice

Recommendation: ThunderPunch. Confidence: high if Ampharos has no confirmed
coverage that cleanly punishes Piloswine and the user's bench is unknown.

Plan: force Pryce to either lose Slowking or reveal the Piloswine preservation
pivot, then re-score from the new active before spending Ampharos.

State read: Slowking cannot safely stay in because ThunderPunch removes it from
the shown HP. Pryce's best branch is switching to Piloswine, which takes the hit
much better and threatens Ampharos with Earthquake next turn.

Win condition: use Ampharos's immediate pressure to deny Slowking's support
role while keeping enough HP or bench flexibility to answer Piloswine after the
pivot.

Candidate ranking:

1. ThunderPunch: best. It KOs Slowking if Pryce stays and still chips the
   obvious Piloswine switch enough to reveal the next route.
2. Switch or double-switch to a Piloswine answer: acceptable only if the user's
   bench has a verified answer and Pryce's pivot is strongly expected.
3. Thunder Wave: usually worse here. It can help long-term, but it gives
   Slowking or Piloswine a turn when direct pressure already forces action.
4. Staying in next turn after Piloswine enters: potentially catastrophic unless
   Ampharos has verified coverage or survives and converts.

Opponent's best route: preserve Slowking through Piloswine, take a reduced hit,
then threaten Ampharos with Earthquake or force the player to reveal a pivot.

Worst plausible branch: Pryce switches Piloswine into ThunderPunch, Ampharos
stays next turn by inertia, and Earthquake removes or cripples the current
route.

Key piece: Ampharos is the pressure piece now, but it may not be the Piloswine
answer after the switch. Its job can change from attacker to pivot-out target.

What changes the answer:

- Ampharos has confirmed Dragon or other coverage that heavily damages
  Piloswine.
- The user's bench has a safe Piloswine answer, making a double-switch more
  attractive if Pryce is strongly incentivized to pivot.
- Piloswine is fainted, lower, statused, or needed by Pryce for a later route.
- Ampharos is lower than the public HP and cannot survive Earthquake afterward.
- Slowking is more valuable to remove immediately than preserving Ampharos HP.

Next turn if it works:

- If Slowking faints, update the Pryce route around Piloswine, Dewgong, and
  Sneasel before keeping Ampharos in.
- If Piloswine enters, do not autopilot. Check Ampharos coverage and survival;
  otherwise pivot to the piece that handles Earthquake and Ice/Ground pressure.

## Scorecard

```text
mechanics and public-state accuracy: 4/4
route and win-condition clarity: 4/4
candidate ranking with resource gain and cost: 4/4
worst plausible branch identified: 3/3
preservation or expendability reasoning: 2/2
answer-changing information: 2/2
concise recommendation grounded in the state: 1/1
total: 20/20 for the abstract drill
```

Caps that would apply in a real battle:

- If the user's bench has a known clean Piloswine punish, this becomes a
  double-switch or coverage arbitration turn rather than automatic
  ThunderPunch.
- If Ampharos's current HP is lower, the Piloswine branch may become
  unacceptable.
- If local type/passive evidence differs from the damage tool output, recheck
  the move before using type or damage claims.

## Lesson Extracted

A forcing attack can be correct even when the opponent has a good pivot. The
question is whether the pivot branch is survivable and planned. Strong advice
does not stop at "ThunderPunch KOs Slowking"; it says what to do when Pryce
chooses the best preservation switch.
