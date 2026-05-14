# Worked Example: Whitney Clefairy Encore Reflect Trap

Purpose: practice forced-control timing. Encore is strong when public state
shows a low-value last move that can be trapped; it is not a blind default
utility button.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster: `data/trainers/parties.asm`, `WhitneyGroup`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_whitney_clefairy_vs_bayleef_encore_reflect_001`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `whitney_clefairy_vs_bayleef_encore_window`
- Encore source: `engine/battle/move_effects/encore.asm`
- Mechanics note: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`

Expert-source framing:

- Smogon's old Encore move analysis frames Encore as a game-changing move when
  it catches recovery, status, or setup:
  <https://www.smogon.com/forums/threads/move-analysis-encore.6211/>.
- Smogon's Infernape Encore discussion gives the practical sequence: trap a
  non-attacking move, then use the forced switch or free turn to choose the
  next route:
  <https://www.smogon.com/forums/goto/post?id=3059222>.
- Smogon's risk/reward guide is the arbitration rule: a clever utility move is
  only correct if the reward is concrete and the wrong branch is acceptable:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Public State

```text
Boss active:
  Clefairy Lv19 at 100%, Evolite
  Known moves: Encore, Thunder Wave, Double Team, DoubleSlap
  Bench: Girafarig, Miltank

Player active:
  Bayleef Lv20 at 100%
  Revealed move: Reflect
  Public priors: Razor Leaf likely, Synthesis plausible

Field:
  Player Reflect active
  Player last move: Reflect

Benchmark mechanics flags:
  encore_trap_live = true
  encore_user_faster = true
  encore_locks_low_value_move = true
  safe_one_setup_turn = true
```

The public benchmark labels Encore as best, Double Team as acceptable, and
DoubleSlap as catastrophic in this exact state.

The mutation `mut_whitney_encore_trap_absent_double_team_001` removes the
visible Encore trap and flips the answer toward Double Team. That answer flip
is the core lesson: Encore needs public last-move and timing evidence.

## Damage Anchors

```text
Bayleef Razor Leaf -> Clefairy with Evolite:
  20-24 damage.
  34-41% of Clefairy's max HP.
  Clefairy survives one public hit.

Bayleef Giga Drain -> Clefairy with Evolite:
  21-25 damage.
  36-43% of Clefairy's max HP.
  Clefairy survives one public hit.

Clefairy DoubleSlap -> Bayleef, no screen adjustment:
  5-6 damage per hit.
  7-8% of Bayleef's max HP per hit.
  Player Reflect is already active in the benchmark, so this raw no-screen
  number should not be treated as the final in-battle DoubleSlap result.
```

The default damage debugger output supports the benchmark's key claim:
Clefairy has time for one utility action, and DoubleSlap is not the route that
best uses the visible Reflect last-move state.

## Route Interpretation

Why Encore is best here:

- Bayleef's last visible move is Reflect, and Reflect is already active.
- The benchmark explicitly marks Clefairy as faster for this public state.
- Encore can lock Bayleef into repeating a low-value support move for 3-6 turns
  under the local source.
- The move has a named follow-up: after the trap, re-score for Double Team,
  Thunder Wave, chip, or a pivot while Bayleef is constrained.

Why Double Team is only acceptable:

- Clefairy survives one public Bayleef hit, so one setup turn is plausible.
- It loses priority to Encore while the concrete Reflect trap exists.
- It becomes better in the mutation where the last-move trap is absent.

Why DoubleSlap is bad:

- It ignores the public control route.
- It gives Bayleef the chance to return to Razor Leaf, Synthesis, or another
  useful move after Reflect.
- It treats the turn as damage race when the better route is temporary control.

## Decision Recipe

Use Encore when:

```text
the target's last move is known;
the last move is low-value if repeated;
the Encore user acts before the target's next meaningful action;
the user survives the public punish;
there is a concrete plan for the trapped turns.
```

Use setup, status, attack, or pivot instead when:

```text
the target's last move is unknown or high-value;
the Encore user is slower or speed is unverified;
the target can switch or punish without losing route value;
the trapped turns do not create progress;
direct damage or status already denies the route.
```

## Player-Side Advice

If advising the user with Bayleef active:

1. After using Reflect, ask whether the opposing Encore user is faster before
   taking another passive turn.
2. If Encore is likely and Bayleef would be trapped into Reflect, consider
   attacking or switching rather than donating several low-value turns.
3. If Bayleef is already Encored, do not keep following the old plan. Re-score
   the switch, stall, and sack options.
4. If the trap evidence is absent, Clefairy may choose Double Team or Thunder
   Wave instead, so the answer changes.

If advising Whitney:

1. Click Encore only because Reflect is the public last move and timing works.
2. After Encore lands, do not assume the fight is solved; decide whether the
   trapped turns are best spent on evasion, paralysis, chip, or a pivot.
3. If Bayleef attacks, switches, or reveals a faster branch, abandon the Encore
   script and re-score.

## Transfer Lesson

Forced-control moves are strongest when they punish something the opponent
already did, not when they guess at something the opponent might do. The better
question is not "is Encore good?" It is "what exact move am I forcing, for how
many turns, and what route improves while that move is forced?"

## Unverified Before Real Turn Advice

- Actual Speed relation in the user's save; base Speed alone does not prove the
  benchmark's `encore_user_faster` flag.
- Exact Bayleef level, stats, item, current HP, PP, and unrevealed moves.
- Whether Reflect is actually the last move or only a known move.
- Whether the player can switch without losing the route.
- Whether Clefairy's Evolite is still present and functioning as expected.
