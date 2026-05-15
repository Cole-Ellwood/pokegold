# Post-Phaze Receiver Map Probe 001 - 2026-05-14

Mode: constructed side-known policy regression.

Purpose: convert the `replay_turn_pause_023` turn-12 miss into six compact
prompts that force the question: "After phazing drags or exposes a receiver,
what job does this exact Pokemon have now?"

This is not final-exam evidence. The prompts were built after studying the
policy and prior replay, so the score is a regression/checklist result, not a
fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_023_receiver_phaze_counterplay_smogtours-gen2ou-933853_2026-05-14.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon GSC Teambuilding Compendium:
  `https://www.smogon.com/forums/threads/gsc-teambuilding-compendium.3547538/`
- Smogon Scizor OU Revamp:
  `https://www.smogon.com/forums/threads/scizor-ou-revamp.3510707/`

Source note: current sample-team material says Marowak endgames need chip on
Cloyster, Suicune, and Skarmory, and that Fire Blast exists specifically to
pressure Skarmory. The compendium and Scizor discussion keep the other side of
the rule honest: phazers such as Skarmory and Steelix are still central
anti-pass answers, and Scizor often needs Baton Pass rather than a solo sweep.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenario 1 is the original miss converted into a
known-own-set case. It still needs a fresh replay check where the coverage is
not given in the prompt and must be inferred only as a possibility, not fact.

## Scenario 1 - Coverage Punish

Public state: vanilla GSC, player-side known set. Our Scizor just Baton Passed
Swords Dance, but opposing Skarmory revealed Whirlwind and dragged in our
Marowak at 100%. Marowak's known moves are Earthquake / Rock Slide /
Swords Dance / Fire Blast. Spikes are on the opponent's side. Skarmory is 100%
and has Toxic / Whirlwind revealed. Our Jolteon is poisoned and still useful
for Thunder pressure.

Frozen answer: use Fire Blast. Confidence: high. The route is to punish the
exact revealed blocker before handing Skarmory another Whirlwind or Toxic
cycle; Fire Blast is the route-specific coverage that the species matchup
otherwise hides. Serious alternatives: switch Jolteon only if Fire Blast is
not in the known set or Marowak must be preserved from a hidden Water pivot;
Swords Dance is too slow into Whirlwind. Worst branch: Fire Blast misses,
Skarmory Thiefs/Toxics, or the opponent pivots to a Water.

Policy key: after phazing exposes a receiver, check the receiver's known route
coverage before auto-switching from an apparently bad species matchup.

Grade: complete.

## Scenario 2 - Auto-Switch

Public state: vanilla GSC, player-side known set. Skarmory's Whirlwind dragged
in our Marowak at 88%. Marowak's known moves are Earthquake / Rock Slide /
Hidden Power Bug / Swords Dance. Opposing Skarmory is 100% with Whirlwind and
Toxic revealed. Our Zapdos is 91% and has Thunder revealed. Spikes are on both
sides.

Frozen answer: switch Zapdos. Confidence: high. The route is to stop giving
Skarmory a free reset against a Marowak set that lacks the coverage to change
the board. Serious alternatives: Rock Slide only if Skarmory is in a precise
flinch-or-chip emergency and switching loses anyway; Swords Dance is a route
error because Whirlwind already owns the clock. Worst branch: Skarmory doubles
to Raikou or Toxic catches Zapdos.

Policy key: the coverage-punish rule does not license staying in when the
known set cannot punish the phazer.

Grade: complete.

## Scenario 3 - Re-Pass

Public state: vanilla GSC, player-side known set. Skarmory used Whirlwind to
break the first Scizor pass and dragged in our Jolteon at 64% poisoned. Jolteon
has Thunder / Agility / Baton Pass / Hidden Power Ice. Opposing Skarmory is
52%, paralyzed, and has Whirlwind / Toxic / Drill Peck revealed. Opposing
Snorlax is 31%, Raikou is asleep, and our Scizor is 55% with Baton Pass and
Swords Dance revealed. Marowak is still unrevealed but healthy.

Frozen answer: use Baton Pass to Scizor if Snorlax is the expected pivot;
otherwise Thunder is acceptable into a Skarmory stay. Confidence: medium. The
route is to keep the chain cycling: poisoned Jolteon should not spend its last
healthy turns trading status with Skarmory if a pass to Scizor catches
Snorlax's Double-Edge lane and rebuilds the receiver map. Worst branch:
Skarmory stays in and Whirlwinds again, or Drill Peck chips Scizor into range.

Policy key: after a phaze, the chain may still have a re-pass route. Do not
collapse every post-phaze board into attack or hard switch.

Grade: complete.

## Scenario 4 - Sacrifice

Public state: vanilla GSC, player-side known team. Opposing Skarmory has just
Whirlwinded and dragged in our Smeargle at 19%. Smeargle already used Spore,
Spikes, and Agility earlier; Sleep Clause blocks another Spore target. Our
Marowak and Machamp are healthy on the bench, and our Snorlax is the only
special sponge. Skarmory is 100% with Whirlwind / Toxic / Drill Peck revealed.
Spikes are on our side.

Frozen answer: let Smeargle spend its last turn on the best available support
or chip, then use the clean entry. Confidence: high. The route is to stop
feeding the phaze loop with valuable switches; Smeargle has delivered its
route job and can become the spacer that gives Marowak, Machamp, or Snorlax a
safe entry. Serious alternative: hard switch only if the incoming Pokemon must
enter before Skarmory attacks or if Smeargle still has Encore/Spore value.
Worst branch: Skarmory uses Whirlwind instead of attacking and the sack fails
to produce the chosen entry.

Policy key: a dragged support piece can become a controlled sacrifice if its
remaining job is lower value than a clean receiver entry.

Grade: complete.

## Scenario 5 - Absorber Switch

Public state: vanilla GSC, player-side known team. Skarmory's Whirlwind
dragged in our Marowak. On the following turn the opponent pivoted to burned
Vaporeon at 81%. Marowak is 94% with Earthquake / Rock Slide / Swords Dance /
Fire Blast. Our Snorlax is 100%, Raikou is healthy, and Jolteon is poisoned at
71%. Vaporeon has Surf revealed.

Frozen answer: switch to Snorlax or Raikou depending on the broader special
route; do not leave Marowak in front of Surf. Confidence: high. The route is
to preserve the route-defining Marowak once the Water answer is public and a
lower-value absorber can take the hit. Serious alternative: Earthquake only if
Vaporeon is in range and Marowak winning now matters more than preserving it.
Worst branch: Vaporeon doubles to Skarmory or Roars on the switch.

Policy key: coverage punish ends once the opponent reveals the real absorber.
Rebuild again and preserve the irreplaceable receiver.

Grade: complete.

## Scenario 6 - Immediate Attack

Public state: vanilla GSC, player-side known set. Skarmory has been removed.
Raikou used Roar to stop a Jolteon pass and dragged in our Machamp at 88%.
Machamp has Cross Chop / Hidden Power Bug / Rock Slide / Curse. Opposing
Snorlax is active at 38% after Spikes and has Double-Edge / Earthquake /
Self-Destruct revealed. Our Marowak is fainted, and Machamp is the remaining
converter.

Frozen answer: use Cross Chop. Confidence: high. The route is immediate
conversion: the phaze delivered the correct attacker into a low target, so
adding Curse or trying to rebuild the chain gives Snorlax a Self-Destruct or
Earthquake branch. Serious alternative: Rock Slide only if a Zapdos/Gengar
switch is the dominant public branch; switching is too slow. Worst branch:
Cross Chop misses or Snorlax switches to a Ghost/Flying answer.

Policy key: sometimes the post-phaze receiver map says the route is already
in front of you. Attack before the opponent resets or trades.

Grade: complete.

## Resulting Rule

After phazing exposes a receiver, rebuild the local map in this order:

1. Known coverage into the phazer or blocker.
2. Whether the known set cannot progress and must switch.
3. Whether re-pass or chain cycling remains live.
4. Whether a spent support piece should become a controlled sacrifice.
5. Whether a revealed absorber means preserving the receiver.
6. Whether immediate damage already converts the route.

## Next Study Target

Run a fresh unseen replay segment where a phaze or Roar exposes a non-obvious
attacker, and score whether the coverage possibility is priced without
treating unrevealed moves as fact.
