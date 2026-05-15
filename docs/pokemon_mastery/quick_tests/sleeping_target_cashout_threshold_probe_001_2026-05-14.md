# Sleeping Target Cash-Out Threshold Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_020` miss into a six-scenario
threshold check: when a target is asleep, should the player keep steady
pressure, switch to a wake absorber, or spend Explosion/Self-Destruct?

This is not final-exam evidence. The prompts were created after studying the
source policy and the replay miss, so the score is a regression checklist, not
a fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_020_sleeper_transfer_smogtours-gen2ou-935572_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Introduction to Competitive GSC:
  `https://www.smogon.com/smog/issue28/gsc`
- Smogon GSC Snorlax analysis thread:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

Source note: Explosion is a route trade, not a panic button. Sleep can create
a window, but GSC wake-and-act, Sleep Talk, Rest, Self-Destruct, phazing, and
the user's remaining job decide whether cashing out is necessary.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 2 and 3 need a fresh replay check
because they are the hardest live distinction: switch to a wake absorber when
the trade is bad, but Explode when a wake/rest/action would undo the win route.

## Scenario 1 - Steady Pressure Before Threshold

Public state: vanilla GSC. Our Exeggutor is 97% and has Psychic, Sleep Powder,
and Explosion revealed. Opposing Snorlax is asleep from Sleep Powder at 68%,
with no moves revealed yet. Spikes are off the opponent's side. Our team still
needs Exeggutor as a second look into Ground- and Water-type pressure.

Frozen answer: use Psychic, not Explosion. Confidence: high. The route is to
keep damaging the sleeping Snorlax while preserving Exeggutor's future job.
Explosion is a serious alternative only if Snorlax is about to wake into a
route-ending action or if a post-trade converter is already named. Worst
branch: Snorlax wakes early and Self-Destructs or reveals Rest/Sleep Talk, but
that risk is not yet enough to spend Exeggutor.

Policy key: wake risk alone does not meet the cash-out threshold.

Grade: complete.

## Scenario 2 - Wake Absorber Over Trade

Public state: vanilla GSC. Our Exeggutor is 100% against sleeping Snorlax at
35%. Snorlax has revealed Double-Edge and Self-Destruct earlier. Our Gengar is
healthy and can enter on a predicted Self-Destruct. Exeggutor is still needed
to threaten the opponent's Vaporeon and Golem. Psychic should KO or almost KO
if Snorlax stays asleep.

Frozen answer: switch Gengar if the wake Self-Destruct branch is the only
route-losing punish; otherwise Psychic is acceptable if the KO is guaranteed
and Gengar's entry costs are too high. Confidence: medium-high. The route is
to cover the worst plausible wake branch without spending Exeggutor's one-time
trade into a target that is already low. Worst branch: Snorlax stays asleep
and the switch gives up a clean KO, or Snorlax wakes and attacks with coverage
instead of Self-Destruct.

Policy key: when a lower-value or immune absorber covers the wake trade, use
it before cashing out the active route piece.

Grade: complete.

## Scenario 3 - Cash Out Now

Public state: vanilla GSC. Our Exeggutor is 74% and will be outsped and KOed
next turn by the opponent's awake Zapdos if it pivots in. Opposing Snorlax is
asleep at 52%, has Curse and Rest revealed, and is the only blocker to our
Vaporeon endgame. If Snorlax wakes or switches out, it can Rest later and the
Vaporeon route is gone. No Ghost or Normal resist has been revealed, and the
opponent's likely switch-ins are already low.

Frozen answer: use Explosion. Confidence: medium-high. The route is to remove
the exact endgame blocker while Exeggutor still gets the trade and before
Snorlax can wake, Rest, or be preserved. Serious alternative: Psychic only if
it creates a clean KO range without risking Rest; switch only if Exeggutor is
needed for a more important blocker. Worst branch: a hidden Ghost/Normal resist
or low-value sack catches Explosion.

Policy key: cash out when the sleeper's wake, Rest, or preservation would undo
the named win route and the post-trade converter is clear.

Grade: complete.

## Scenario 4 - RestTalk Is Active, Do Not Farm It

Public state: vanilla GSC. Our Gengar is 60% and has Thunderbolt. Opposing
Vaporeon is asleep from Rest at 99%, with Surf and Sleep Talk revealed. Our
Zapdos is 90%, while Gengar is needed later to block a low Cloyster's Rapid
Spin or Explosion line.

Frozen answer: switch Zapdos. Confidence: high. The route is to preserve
Gengar from Sleep Talk Surf while bringing in the stronger direct pressure.
Thunderbolt is acceptable only if Gengar is expendable or Zapdos cannot take
the Surf branch. Worst branch: Sleep Talk picks Surf into Zapdos again, but
that is still better than losing Gengar's route job.

Policy key: a sleeping RestTalk target is an active attacker; do not treat the
sleep turn as free damage.

Grade: complete.

## Scenario 5 - Do Not Cash Out Into A Replaceable Target

Public state: vanilla GSC. Our Cloyster is 45%, poisoned, with Explosion,
Surf, and Toxic revealed. Opposing sleeping Snorlax is 41%, but the opponent
also has healthy Skarmory and Golem revealed. Our Machamp route needs Skarmory
removed more than it needs Snorlax chipped. Cloyster can still Toxic or Surf
the likely switch.

Frozen answer: do not Explosion into Snorlax. Use Toxic/Surf or switch to the
Machamp enabler depending on the expected response. Confidence: medium. The
route is to save the one-time trade for the actual blocker, not spend it on a
target that the opponent can replace defensively. Worst branch: Snorlax wakes
and makes progress, but exploding into it still fails to open the Machamp
route.

Policy key: a sleeping target is not automatically the correct trade target;
name the blocker the Explosion removes.

Grade: complete.

## Scenario 6 - Sleep Clause Reset After Trade

Public state: vanilla GSC. Earlier, our Exeggutor put opposing Snorlax to
sleep; Snorlax has now fainted after using Self-Destruct. Our Gengar faces
Vaporeon at 67% and has Hypnosis and Thunderbolt revealed. Vaporeon may Rest
or switch to Raikou. No opponent Pokemon is currently asleep from our induced
sleep move.

Frozen answer: Hypnosis is live again and should be ranked with Thunderbolt.
Confidence: medium. If sleeping Vaporeon opens the route more than immediate
damage, click Hypnosis; if Raikou is the obvious answer, Thunderbolt or a
double may be better. Worst branch: Hypnosis misses and Vaporeon Rests or
surfs; the key is not to reject Hypnosis as illegal after the prior sleeper
fainted.

Policy key: after the induced sleeping target faints or is cured, Sleep Clause
no longer blocks the next sleep route.

Grade: complete.

## Resulting Rule

Before cashing out into a sleeping target, answer three questions:

- What exact wake, Rest, Sleep Talk, Self-Destruct, or switch branch beats us?
- Can steady pressure or a lower-value absorber cover that branch?
- What named route opens after the one-time trade, and what role is lost?

## Next Study Target

Run a fresh replay segment at the first sleeping target with a one-time trade
available, and score whether the cash-out threshold transfers without
overcorrecting.
