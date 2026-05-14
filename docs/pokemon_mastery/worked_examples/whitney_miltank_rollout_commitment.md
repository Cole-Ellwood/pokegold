# Worked Example: Whitney Miltank Rollout Commitment

Purpose: practice locked-move timing. Rollout is dangerous after the board is
prepared; opening with it can be wrong when the first hit is tiny and the ace
needs flexible Body Slam / Milk Drink timing.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Boss roster: `data/trainers/parties.asm`, `WhitneyGroup`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_whitney_miltank_vs_geodude_rollout_lock_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_whitney_miltank_vs_geodude_rollout_lock_001`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `whitney_miltank_vs_geodude_rollout_temptation`
- Rollout source: `engine/battle/move_effects/rollout.asm`
- Magnitude power table: `data/moves/magnitude_power.asm`
- Damage tool self-test: `python -m tools.damage_debugger.matchup --self-test`

Expert-source framing:

- Smogon's move-restriction guide treats Rollout as a move that automatically
  continues after selection:
  <https://www.smogon.com/dp/articles/move_restrictions>.
- Smogon's setup-move guide frames setup as a question of timing and control,
  not just whether the move can snowball:
  <https://www.smogon.com/smog/issue26/setting_up>.
- Smogon's risk/reward guide applies to the lock decision: compare the reward
  of a future snowball with the immediate punish and the cost of being wrong:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Public State

```text
Boss active:
  Miltank Lv21 at 92%, Mint Berry
  Known moves: Body Slam, Milk Drink, Rollout
  Bench: Clefairy at 74%, Girafarig at 100%

Player active:
  Geodude Lv20 at 78%
  Revealed moves: Rock Throw, Defense Curl
  Public prior: Magnitude plausible

Field:
  No weather or screens
```

The public benchmark labels Body Slam as best, Milk Drink as acceptable, and
Rollout / switch to Girafarig as catastrophic in this exact state.

The mutation `mut_whitney_rollout_after_status_001` flips toward Rollout after
Geodude is paralyzed and the lock is marked safe. That answer flip is the core
lesson: Rollout is a conversion move, not an automatic opener.

## Damage Anchors

```text
Miltank Body Slam -> Geodude at 78%:
  7-9 damage.
  15-19% of Geodude's current HP.
  No KO, but it preserves flexibility and can create paralysis pressure.

Miltank first-turn Rollout -> Geodude at 78%:
  2-3 damage.
  4-6% of Geodude's current HP.
  No KO, and it starts the commitment before status or safety is established.

Geodude Rock Throw -> Miltank at 92%:
  15-18 damage.
  21-25% of Miltank's current HP.
  This is chip, not an immediate forced heal from the shown state.

Geodude Magnitude examples -> Miltank at 92%:
  Magnitude 7 / 70 BP: 20-24 damage, 28-34% of Miltank's current HP.
  Magnitude 8 / 90 BP: 25-30 damage, 35-42% of Miltank's current HP.
  Magnitude 9 / 110 BP: 30-36 damage, 42-51% of Miltank's current HP.
  Magnitude 10 / 150 BP: 40-48 damage, 56-68% of Miltank's current HP.
```

The exact Magnitude roll is random. The important planning fact is not a single
damage number; it is that a high roll can make early lock-in or greedy healing
much worse, while the common Rock Throw branch alone does not force immediate
Milk Drink.

## Route Interpretation

Why Rollout is bad now:

- The first hit does almost nothing from the public state.
- Locking Miltank removes the option to Body Slam, Milk Drink, or switch after
  seeing the next Geodude branch.
- Geodude is not yet paralyzed, and public information still includes Rock
  Throw plus plausible Magnitude pressure.
- Miltank is the ace; spending its flexibility must open a route, not just look
  iconic.

Why Body Slam is better:

- It keeps the ace's move choice flexible.
- It can create the status branch that makes later Rollout safer.
- It creates chip without letting Geodude exploit a predictable locked sequence.
- It has a named follow-up: Body Slam pressure, Milk Drink around the danger
  threshold, then consider Rollout once paralysis or HP state supports it.

Why Milk Drink is only acceptable:

- Miltank is high enough that immediate healing delays progress.
- Milk Drink becomes stronger after Geodude damage makes the next hit matter or
  when preserving Miltank is required before continuing pressure.
- At 92%, Body Slam is a better first route action because it changes the
  opponent's future branch instead of resetting a state that is not yet urgent.

## Decision Recipe

Commit to a locked move when:

```text
the first locked hit changes the route;
the opponent's punish branches are already reduced;
the user is not giving up a required recovery/status/switch option;
the board at the end of the lock is favorable or forced.
```

Delay the locked move when:

```text
the first hit is only chip;
the opponent can punish the predictable sequence;
the user is the ace or irreplaceable answer;
status, chip, or healing would make the lock safer later.
```

## Player-Side Advice

If advising the user with Geodude active:

1. Treat early Rollout as an opening to punish, not as already lost.
2. Keep Geodude unstatused if possible; Body Slam paralysis is the branch that
   makes later Rollout cleaner for Whitney.
3. If Miltank uses Body Slam first, re-score around paralysis and current HP.
4. If Miltank uses Milk Drink too early, use the free tempo to improve Geodude's
   branch or pivot to the real Miltank answer.

If advising Whitney:

1. Do not click Rollout just because Miltank is the famous ace.
2. Use Body Slam first when the opponent is healthy, unstatused, and able to
   punish a predictable lock.
3. Use Milk Drink when the current HP threshold makes the next punish relevant.
4. Start Rollout only after the lock has a concrete conversion route.

## Transfer Lesson

A commitment move is not a plan by itself. The move becomes good when the state
has been prepared enough that the forced turns are winning turns. Before that,
flexible pressure, recovery timing, or a pivot can be stronger than the
apparently decisive snowball button.

## Unverified Before Real Turn Advice

- Exact user Geodude stats, current HP, item, PP, and unrevealed moves.
- Whether Geodude actually has Magnitude in the user's current save.
- Current gender state for Attract branches.
- Whether Miltank's Mint Berry is still unspent.
- Whether a different user team member punishes Rollout more directly than
  Geodude does.
