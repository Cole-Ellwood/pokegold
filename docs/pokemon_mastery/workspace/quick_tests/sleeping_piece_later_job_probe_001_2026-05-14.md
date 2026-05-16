# Sleeping Piece Later Job Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_019` misses into six compact prompts
that force the question: "Is this sleeping Pokemon still an active route
piece?"

This is not final-exam evidence. The prompts were built after studying the
policy and prior replay, so the score is a regression/checklist result, not a
fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_019_sleeper_later_job_smogtours-gen2ou-934335_2026-05-14.md`

Web sources checked:

- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Snorlax analysis thread:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: GSC sleep has to be priced together with Sleep Talk, Heal Bell,
wake-and-act timing, and the Spikes switch economy. A sleeping Pokemon may be
inactive this turn but still define the next route.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenario 4 and scenario 6 should be tested in a
fresh replay because they map directly to real misses: using sleeping RestTalk
Snorlax as a coverage absorber, and valuing Rapid Spin because it makes
preserved sleeping pieces cheaper to move later.

## Scenario 1 - Sleep Talk Attack

Public state: vanilla GSC. Our active Snorlax is 74%, asleep from Rest, with
Double-Edge / Rest / Sleep Talk revealed. The opponent's active Zapdos is 100%
and has revealed Thunderbolt. Spikes are on our side. Our Raikou is low, and no
other healthy Electric answer is public.

Frozen answer: stay in and use Sleep Talk. Confidence: high. The route is to
keep Snorlax functioning as the special sponge while preserving the team from
Zapdos pressure; switching gives Zapdos a free Thunderbolt and more Spikes
damage. Serious alternative: switch only if Snorlax is needed later for a
specific physical route and a safe Electric answer exists. Worst branch:
Sleep Talk calls the wrong move, Zapdos crits, or a phazing teammate exploits
the sleeping Snorlax afterward.

Policy key: sleeping RestTalk users can attack or reset while asleep; do not
auto-preserve them as inert Sleep Clause material.

Grade: complete.

## Scenario 2 - Heal Bell Reset

Public state: vanilla GSC. Our active Miltank is 82% and has Heal Bell
revealed. Our Snorlax is asleep on the bench from the opponent's Hypnosis at
79%, with Curse and Double-Edge revealed. The opponent's active Gengar is 94%
and has Hypnosis revealed. Spikes are on both sides.

Frozen answer: use Heal Bell unless Gengar has an immediate route-ending
Explosion read. Confidence: high. The route is to wake Snorlax, unlock its
Curse/Double-Edge pressure, and remove the opponent's Sleep Clause leverage.
Serious alternatives: Growl only if Gengar cannot punish and Snorlax's wake is
not urgent; switch only if Miltank is about to be removed. Worst branch:
Gengar Explodes into Miltank or doubles to a Snorlax answer while Heal Bell
spends the turn.

Policy key: cleric support can make a slept teammate live again before it ever
returns to the field.

Grade: complete.

## Scenario 3 - Phaze Bait

Public state: vanilla GSC. Our active Snorlax is 100%, asleep from Rest, and
has not revealed Sleep Talk. The opponent's active Skarmory is 100% and has
Whirlwind revealed. Spikes are on our side. Our Zapdos is healthy and can
pressure Skarmory.

Frozen answer: switch to Zapdos. Confidence: high. The route is to deny a free
Whirlwind cycle and stop Skarmory from turning sleeping Snorlax into Spikes
damage. Serious alternative: stay only if Sleep Talk is revealed or if the
sleep turn/wake branch is better than the phaze punish. Worst branch: Skarmory
doubles to a Zapdos answer or uses Toxic/Drill Peck into the switch.

Policy key: non-Talk sleeping Pokemon can be phaze bait; preserving them may
mean switching before the opponent converts the sleep turn.

Grade: complete.

## Scenario 4 - Coverage Absorber

Public state: vanilla GSC. Our active Alakazam is 40% against Nidoking at
100%. Nidoking has revealed Lovely Kiss, Earthquake, and Thunder. Our Zapdos is
asleep from Lovely Kiss, while our Snorlax is 82%, asleep from Rest, and has
Rest / Sleep Talk / Double-Edge revealed. Spikes are on our side.

Frozen answer: if Nidoking is likely to press Thunder or mixed coverage to
catch the Electric slot, switch sleeping RestTalk Snorlax into it; if
Earthquake is clearly the immediate line, Recover with Alakazam remains
serious. Confidence: medium. The route is to use Snorlax as a live absorber
even while asleep, because Sleep Talk means it can still act and it protects
Alakazam/Zapdos from the coverage fork. Worst branch: Nidoking simply clicks
Earthquake into the Snorlax switch or uses a fourth move that pressures
Snorlax.

Policy key: sleeping does not erase a piece's defensive job if it still covers
the expected attack class and has Sleep Talk.

Grade: complete.

## Scenario 5 - Wake-And-Act Trade

Public state: vanilla GSC. Our boosted Marowak is the only remaining win
route. The opponent's Cloyster is 50%, asleep from Lovely Kiss, has spent
several eligible turns on the field, and has Explosion revealed. Our Jolteon
is low and no longer needed except as a sack.

Frozen answer: do not attack blindly with Marowak; switch Jolteon into the
possible wake Explosion if Marowak is irreplaceable. Confidence: medium-high.
The route is to cover the worst plausible branch: in GSC a Pokemon that wakes
can move that turn, and Cloyster's later job is to trade with the route
piece. Serious alternative: attack only if Cloyster cannot wake yet, if
Marowak still wins after the trade, or if switching gives up the whole route.
Worst branch: Cloyster stays asleep and the switch spends tempo.

Policy key: wake-and-act turns make sleeping Explosion users live threats
before the wake is shown.

Grade: complete.

## Scenario 6 - Hazard Removal Enables Preservation

Public state: vanilla GSC. The opponent's Snorlax is asleep on the bench from
our Hypnosis and wants to be preserved as Sleep Clause material. Our Spikes are
up on their side, and our Cloyster is fainted. Their active Cloyster is 35%,
with Spikes, Toxic, and Rapid Spin revealed, facing our Snorlax at 73%.

Frozen answer: use Rapid Spin before cashing out. Confidence: high. The route
is to remove the hazard while the opponent no longer has Cloyster to reset it,
making future switches into the sleeping Snorlax, Raikou, Skarmory, or Miltank
cheaper. Serious alternatives: Toxic only if the status clock matters more
than the whole-team switch economy; Explosion only if Snorlax is the exact
blocker and Cloyster will not get another support turn. Worst branch: Snorlax
KOs Cloyster before spin value matters or a Ghost blocks the spin.

Policy key: preserving sleeping pieces depends on entry costs. Rapid Spin can
be the move that keeps the later sleep route affordable.

Grade: complete.

## Resulting Rule

Before treating a sleeping Pokemon as disabled, ask which of these jobs is
still live:

- Sleep Talk attack or Rest reset;
- Heal Bell or cleric reset;
- phaze bait that must be moved out;
- predicted coverage absorber;
- wake-and-act attack or Explosion;
- preservation made cheaper by Rapid Spin or hazard removal.

## Next Study Target

Run a fresh unseen replay segment that includes either RestTalk or Heal Bell,
and score whether these six prompts transfer under real turn pressure.
