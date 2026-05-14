# Worked Example: Falkner Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Falkner as an early accuracy,
priority, sleep, item, and lead-fit fight. This is a team-agnostic planning
artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `FalknerGroup`.
- Boss route map: `../boss_route_maps/falkner_turn1_route_sheet.md`.
- Sand Attack, Gust, Fury Attack, Peck, Confusion, Hypnosis, Quick Attack,
  Sharp Beak, Mint Berry, contact flags, priority, and local type-chart
  references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Move data: `data/moves/moves.asm`; Hypnosis is 60 accuracy, Quick Attack uses
  `EFFECT_PRIORITY_HIT`, and Sand Attack uses `EFFECT_ACCURACY_DOWN`.
- Contact evidence: `data/moves/contact_flags.asm`; Fury Attack, Peck, Tackle,
  and Quick Attack are contact, while Gust, Sand Attack, Confusion, and
  Hypnosis are not.

Expert study anchors:

- Smogon lead material: the lead should fit the whole battle plan. A lead that
  wins turn 1 but spends the later answer can still be wrong.
- Smogon priority material: priority changes revenge and endgame math; a faster
  Pokemon is not automatically safe at low HP.
- Smogon status material: sleep creates a temporary route change, not a script,
  and a miss or cure requires immediate re-scoring.
- Smogon Flying-type material: Flying pressure is often broad and reliable, so
  the answer must be a real route piece, not just a vague defensive label.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Falkner

Known boss roster:
  Pidgeotto / Spearow / Noctowl

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Pidgeotto pressure plan, a way to avoid an accuracy snowball,
  a Quick Attack range plan, and a Noctowl sleep plan; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  Quick Attack using the local priority-hit tier, Sharp Beak boosting Flying
  damage, Mint Berry curing sleep once, Hypnosis being 60 accuracy, Sand Attack
  reducing accuracy, Fury Attack being multi-hit, and contact flags being
  move-specific

Missing evidence:
  exact player team, HP, levels, moves, items, speed relations, damage ranges,
  passive type states, whether the lead can remove Pidgeotto before Sand Attack
  compounds, whether the intended cleaner enters Quick Attack range, whether
  the Noctowl answer can absorb or avoid Hypnosis, and whether any sleep plan
  is invalidated by Mint Berry
```

## Output Shape

Primary route:

- Stop Falkner from turning small early control into lost agency. Pidgeotto can
  lower accuracy and pick off weakened targets with Quick Attack, Spearow can
  keep tempo with Peck or Fury Attack variance, and Noctowl can use Hypnosis or
  Confusion to disrupt the piece meant to finish the fight.

Backup route:

- If Sand Attack lands or Hypnosis hits, abandon the original script. The
  backup route should name whether the player is switching, attacking through
  reduced reliability, using a guaranteed or high-reliability move, sacrificing
  a low-value piece, or preserving the Noctowl answer for a cleaner entry.

Boss route priority:

```text
immediate:
  Pidgeotto Sand Attack if the player's route needs repeated accurate hits.
  Pidgeotto Quick Attack if the current or next Pokemon is near priority range.
  Noctowl Hypnosis if it targets the only closer or stable answer.

accumulating:
  Accuracy drops turning safe attacks into miss-prone turns.
  Spearow forcing extra damage after Pidgeotto chip.
  Mint Berry invalidating the player's first sleep attempt into Noctowl.

endgame:
  Quick Attack cleanup after low-HP survival.
  Noctowl buying enough turns with Hypnosis or Confusion for prior chip to
  matter.
```

Boss route to deny first:

- Deny the route that makes the only answer unreliable. If the lead depends on
  repeated hits, Sand Attack is urgent. If the closer survives at low HP,
  Quick Attack range is urgent. If the plan needs one sleep move into Noctowl,
  Mint Berry is the hidden failure branch.

Boss route that can be delayed:

- Spearow can usually be delayed if the current answer remains healthy and does
  not need to preserve HP for Noctowl. It cannot be delayed if Fury Attack or
  Peck puts the only Noctowl answer into range for the final route.

- Noctowl can be delayed while the sleep absorber or sleep-risk plan is intact.
  It cannot be delayed once the intended Noctowl answer is already accuracy-
  dropped, chipped, or needed to finish Pidgeotto.

Best lead profile:

- A lead that pressures Pidgeotto immediately with reliable damage and does not
  rely on a single low-accuracy move. It should either deny Sand Attack from
  compounding, stay useful if accuracy drops once, or preserve the piece that
  answers Noctowl's Hypnosis branch.

Avoid as lead:

- A slow setup lead that gives Pidgeotto free Sand Attack turns.
- A lead whose plan depends on one low-accuracy attack landing repeatedly.
- The only Noctowl answer if Pidgeotto can chip it or lower its accuracy before
  Noctowl appears.
- A sleep-first plan into Noctowl before Mint Berry is accounted for.
- A fragile cleaner that can win the visible matchup but falls into Quick
  Attack range before the end.

First move plan:

- Give turn 1 one job: prevent the first accuracy drop from deciding the fight.
  Attacking is good if it removes or heavily pressures Pidgeotto before Sand
  Attack becomes a route. Switching is good only if it preserves the real
  Noctowl answer and does not hand Pidgeotto the same control turn for free.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Pidgeotto's Sand Attack, Gust, Quick Attack, and Tackle branches
  against the lead's later role.

Turn 2:
  If accuracy dropped, rebuild around hit reliability and Quick Attack range.
  If Pidgeotto was denied, prepare for Spearow tempo or Noctowl sleep.

Turn 3:
  Start the ledger: accuracy stages, priority range, multi-hit variance,
  Noctowl Mint Berry state, sleep status, and whether the current active is
  still needed later.
```

Piece to preserve:

- The Noctowl answer by default if it is also the sleep absorber, special
  pressure piece, or only reliable finisher after accuracy drops.

- The priority-safe cleaner if Falkner can put the faster route into Quick
  Attack range.

Piece that can be spent:

- A lead that has already denied Pidgeotto and has no unique role against
  Spearow or Noctowl.

- A low-accuracy attacker after it has already failed its route and a cleaner
  can enter safely.

Worst plausible branch:

- The player keeps clicking the original move after Sand Attack, misses through
  the accuracy drop, gets chipped into Quick Attack or Spearow range, then
  reaches Noctowl with the sleep answer damaged or with the sleep plan consumed
  into Mint Berry.

Abandon conditions:

- The active Pokemon has lost accuracy and the plan requires repeated hits.
- The intended cleaner is in Quick Attack range.
- Noctowl still has Mint Berry and the plan depends on sleep.
- Hypnosis lands on a piece with an irreplaceable role.
- Fury Attack variance or Sharp Beak damage changes a survival threshold.
- Type-chart, passive, item, contact, accuracy, sleep, or damage evidence
  contradicts the assumed answer.

What information would flip the lead or first move:

- Whether the lead can remove or force Pidgeotto before Sand Attack matters.
- Whether the lead has a reliable move that remains acceptable after one
  accuracy drop.
- Whether the intended Noctowl answer is also needed to beat Pidgeotto.
- Whether Quick Attack reaches the planned cleaner after one Gust, Peck, or
  Fury Attack sequence.
- Whether the player has a sleep absorber that does not mind Hypnosis.
- Whether a sleep move into Noctowl only consumes Mint Berry rather than
  changing the route.

## Extracted Lesson

Falkner is the small version of long-game route discipline. Accuracy drops,
priority, and sleep are only scary because they buy turns for the next piece.
The correct opening is the one that prevents Pidgeotto from making the player's
plan unreliable while preserving enough structure to handle Spearow tempo and
Noctowl sleep without falling into a script.
