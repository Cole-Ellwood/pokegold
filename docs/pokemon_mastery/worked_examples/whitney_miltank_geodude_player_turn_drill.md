# Worked Example: Whitney Miltank vs Geodude Player-Turn Drill

Purpose: convert `whitney_miltank_rollout_commitment.md` into user-facing
advice from Geodude's side. The hard part is not being scared by the word
Rollout; it is punishing Miltank before Body Slam paralysis or Milk Drink timing
makes Rollout safe.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- `whitney_miltank_rollout_commitment.md`
- Public card:
  `tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`,
  `fixture_whitney_miltank_vs_geodude_rollout_lock_001`
- Hidden oracle:
  `tools/boss_ai_preference/benchmarks/state_transition_oracles.json`,
  `fixture_whitney_miltank_vs_geodude_rollout_lock_001`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `whitney_miltank_vs_geodude_rollout_temptation`

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

Damage anchors from the source note:

```text
Miltank Body Slam -> Geodude at 78%:
  7-9 damage, 15-19% of Geodude's current HP.

Miltank first-turn Rollout -> Geodude at 78%:
  2-3 damage, 4-6% of Geodude's current HP.

Geodude Rock Throw -> Miltank at 92%:
  15-18 damage, 21-25% of Miltank's current HP.

Geodude Magnitude 7/8/9/10 -> Miltank at 92%:
  20-24 / 25-30 / 30-36 / 40-48 damage.
```

## Live-Turn Advice

Recommendation: use Magnitude if Geodude actually has it. If Magnitude is not
available, use Rock Throw. Confidence: medium-high for the move class, capped
because Magnitude is only a public prior in the source card.

Plan: make Miltank spend its flexibility on damage control before it can create
the Body Slam paralysis branch or safely commit to Rollout.

State read: first-turn Rollout is weak from this board, but Body Slam can add
paralysis pressure and Milk Drink can reset shallow chip. Geodude's best job is
to create enough damage that Whitney's flexible Miltank turns become reactive.

Win condition: keep Geodude functional long enough to force Miltank into an
unsafe recovery or lock decision, then re-score around paralysis, current HP,
and whether Miltank is committed to Rollout.

Candidate ranking:

1. Magnitude, if available: best. It is the only public branch that can create
   large immediate pressure and make Milk Drink or Rollout timing awkward.
2. Rock Throw: acceptable if Magnitude is absent. It is real chip and does not
   donate a free setup turn, but it may not force recovery by itself.
3. Defense Curl: usually wrong on this exact turn unless Miltank has already
   committed to Rollout and survival is the route. Before the lock, it lets
   Body Slam, Milk Drink, or a switch happen without enough pressure.

Opponent's best route: Body Slam first, hoping paralysis or chip makes later
Rollout safer while preserving Milk Drink flexibility.

Worst plausible branch: Body Slam paralyzes Geodude, Magnitude rolls low or is
not available, and Miltank can later Milk Drink or start Rollout with the main
punish reduced.

Key piece: Geodude is the current Miltank pressure piece. It is not expendable
until the Miltank route is denied or another answer is confirmed.

What changes the answer:

- Geodude does not know Magnitude.
- Geodude is already paralyzed or below a Body Slam plus follow-up threshold.
- Miltank has already started Rollout.
- A different teammate punishes Miltank more directly or absorbs Body Slam
  paralysis better.
- Attract, gender, Mint Berry state, or exact speed information changes the
  route.

Next turn if it works:

- If Miltank uses Body Slam, re-score around paralysis and Geodude's current HP.
- If Miltank uses Milk Drink, use the tempo to keep pressure or pivot to the
  stronger Miltank answer.
- If Miltank starts Rollout, price whether Geodude can attack through the lock
  or must use survival/pivot options.

## Lesson Extracted

Against a commitment move, punish the setup state before the lock becomes safe.
Do not spend the answer on passive preparation while the opponent still has
flexible status, recovery, and switching options.
