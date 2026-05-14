# Boss Turn Advice Template

Purpose: use this shape when the user asks what to do on a real Gym Leader Lab
turn. The answer should be compact, but it must still show long-term planning.

Source basis:

- Smogon's long-term thinking guide: build a plan, identify what must be
  weakened, and save the win-condition piece until its counters are known or
  damaged.
- Smogon's risk/reward guide: compare the likely opponent action with the worst
  plausible branch, and change risk tolerance based on whether our position is
  ahead, stable, or losing.
- Smogon's prediction guide: prediction is information-based, not a blind
  guessing contest.

## Required Input

Ask for or infer:

- Mechanics profile: `romhack_gym_leader_lab`, `vanilla_gsc`, or unknown.
- Our active Pokemon, HP, status, boosts, item if known, and moves.
- Opponent active Pokemon, HP, status, boosts, item if known, and revealed
  moves.
- Bench state for both sides, including fainted Pokemon.
- Hazards, screens, weather, sleep clause, and major PP constraints.
- Known boss roster, if this is a planned boss fight.
- Any local mechanic that might matter: type-chart delta, passive type ability,
  three-layer Spikes, move/item change, or damage-debugger result.

If a required field is missing, do not freeze. State the assumption and the
information that would flip the answer.

Information boundary:

- There is no Team Preview in vanilla GSC or Gym Leader Lab. Do not assume both
  teams are visible at turn 0.
- For player-side advice, known boss rosters and local source docs are allowed
  because the advisor can inspect trainer data before a planned boss fight.
- For boss AI advice or future AI policy, do not use the unrevealed player
  team. The AI may use public state, seen player species, revealed player
  moves, observed damage/status/switches, and explicitly allowed legal/source
  priors only.
- As turns pass, re-plan from reveals. Do not backfill hidden player-team
  knowledge into earlier recommendations.

## Live Answer Shape

Use this order:

```text
Recommendation:
  [move or switch] ([confidence])

Plan:
  [one sentence naming the current route to win]

State read:
  [key HP/status/boost/hazard/speed/reveal facts that decide the turn]

Win condition:
  [our live route and the opponent route that must be denied]

Candidate ranking:
  1. [best action: route gained, risk covered]
  2. [main alternative: why acceptable or worse]
  3. [bad/catastrophic action: why it fails]

Opponent's best route:
  [what they are trying to make happen]

Worst plausible branch:
  [the branch we must not ignore]

Key piece:
  [our irreplaceable piece this turn, if any]

What changes the answer:
  [revealed move, damage range, wake turn, crit risk, hidden item, passive,
   type-chart issue, or bench info]

Next turn if it works:
  [planned follow-up, not a full script]
```

For a trivial forced KO or forced survival turn, shorten the answer, but still
name what the KO or switch exposes afterward.

## Decision Procedure

1. Reconstruct the public state.
2. Name our original plan and whether it is still live.
3. Re-label any piece whose first job failed into its remaining narrower job,
   such as one pivot, revenge hit, status move, setup chance, sacrifice entry,
   or no remaining job.
4. Name the opponent's current route.
5. Identify irreplaceable pieces on both sides.
6. List serious candidates: attack, switch, status, setup, recover, phaze,
   hazards, scout, sacrifice.
7. Reject moves that fail mechanically under the current profile.
8. Reject moves that expose an irreplaceable answer without opening a stronger
   route.
9. Compare the likely opponent action with the worst plausible branch.
10. Choose the move that improves the best live route or prevents the opponent's
   best route.
11. Name the next-turn plan and the information that would invalidate it.

## Risk Posture

Ahead:

- Prefer low-risk moves that preserve the route and deny the opponent's game
  changer.
- Do not predict if the safe move keeps the opponent boxed in.

Stable:

- Prefer moves that improve the route while covering the worst plausible
  branch.
- Take a medium risk only if the reward is a concrete route improvement.

Behind:

- Safe play that loses slowly is not actually safe.
- Accept risk when it creates the only realistic route back into the game.

## Romhack Verification Hooks

Before using these words in a final recommendation, check local evidence when
the answer depends on them:

- `super effective`, `resisted`, `immune`, `neutral`
- exact hazard damage
- passive type ability interaction
- sleep / Rest / Sleep Talk timing
- move legality, item behavior, or boss moveset
- exact KO range

Useful local anchors:

- Type chart: `data/types/type_matchups.asm`
- Mechanics overview: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Generated reference: `docs/agent_navigation/hack_mechanics_reference.md`
- Type passives: `engine/battle/type_passive_damage_mods.asm`
- Type-passive route triage:
  `docs/pokemon_mastery/romhack_deltas/type_passive_route_impacts.md`
- Type-passive fixture priority:
  `docs/pokemon_mastery/romhack_deltas/type_passive_fixture_priorities.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`

## Common Failure Modes

- Recommending damage without naming what route the damage changes.
- Treating a boss Pokemon like its competitive species role without checking
  local moves, stats, passives, and roster.
- Preserving a piece only because it is generally good, not because it has a
  live role.
- Sacrificing a low-HP piece that is still the only answer to a boss route.
- Continuing a plan after a miss, wake, crit, switch, reveal, or unexpected
  damage.
- Discarding a damaged or slept piece before checking its remaining narrower
  job.
- Calling a move safe because the opponent has not revealed the punish yet.
- Overpredicting when the straightforward move already preserves the win route.
