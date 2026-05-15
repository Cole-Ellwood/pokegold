# Self-Destruct Receiver Branch Regression 001 - smogtours-gen2ou-934904 - 2026-05-14

Mode: post-oracle regression.

Source replay: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934904`.

Purpose: turn the severe turn-14 miss from `replay_turn_pause_021` into a
three-scenario threshold check. Before setting up with a passed receiver, price
whether Snorlax can spend Self-Destruct into the current route piece.

This is not fresh skill evidence. The actual turn-14 outcome is known, so this
is regression evidence that the branch can be named and applied after review.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_021_cashout_threshold_partial_smogtours-gen2ou-934904_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon GSC BP forum thread:
  `https://www.smogon.com/forums/threads/gsc-bp.3541165/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: GSC Baton Pass can make slow physical receivers immediately
dangerous, and Snorlax Self-Destruct is strong enough to be route-defining.
That means the receiver's setup turn must be priced against the opponent's
one-time trade, not only against ordinary attacks.

## Score Summary

Scenarios: 3.

Branch-bundle hits: 3 / 3.

Acceptable action bundles: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

## Scenario 1 - Actual Turn 14, Attack Before Setup

Public state: vanilla GSC spectator-public. Jolteon has just passed Agility to
Marowak. Marowak is at 53% with passed Speed. Opposing Snorlax is 93%, with
Double-Edge and Earthquake revealed. Spikes are on p2's side. Snorlax has not
revealed Self-Destruct yet, but it is a serious GSC Snorlax branch.

Frozen answer: attack immediately with Earthquake or another best damage move;
do not Swords Dance first. Confidence: medium-high. The route is to cash the
passed Speed before Snorlax can erase the receiver with Self-Destruct. Serious
alternative: switch only if a lower-value Self-Destruct absorber is available
and preserving Marowak is mandatory. Worst branch: Snorlax uses Self-Destruct
and trades for Marowak before the receiver converts.

Policy key: a passed receiver is often the route piece; identify it as the
one-time trade target before boosting.

Grade: complete.

## Scenario 2 - Absorber Exists, Preserve Receiver

Public state: vanilla GSC side-known variant. Agility has been passed to
Marowak at 53%. Opposing Snorlax is 40%, has revealed Self-Destruct, and is
unlikely to survive Marowak's next attack. Our Gengar is healthy and is not
needed for the endgame except to absorb Normal-type self-KO moves. Snorlax has
Earthquake revealed, so the absorber switch is not free if the opponent reads
it.

Frozen answer: if Self-Destruct is the route-losing branch and Gengar is
expendable, switch Gengar; if Earthquake is more likely or Gengar is required,
attack with Marowak. Confidence: medium. The route is to preserve the
irreplaceable receiver while making the opponent spend Snorlax's one-time
trade into an immune target. Worst branch: Snorlax reads the absorber and uses
Earthquake, or stays asleep/does not boom and the switch gives up the KO.

Policy key: lower-value or immune absorbers matter only when they cover the
specific one-time branch better than attacking does.

Grade: complete.

## Scenario 3 - Setup Is Allowed Only After The Trade Is Accounted For

Public state: vanilla GSC side-known variant. Agility has been passed to
Marowak at 80%. Opposing Snorlax is 93%, but its set is fully revealed as
Curse / Double-Edge / Earthquake / Rest, with no Self-Destruct. The opponent's
healthy Skarmory is gone, and Reflect is not up. Marowak needs Swords Dance to
finish the remaining team through Snorlax and Raikou.

Frozen answer: Swords Dance is acceptable. Confidence: high. The route is to
boost only after the one-time trade branch has been removed from the state.
Serious alternative: attack if a crit, phaze, or status branch makes the setup
turn too expensive. Worst branch: treating "no Self-Destruct" as permission to
ignore other counters such as phazing, status, or Rest timing.

Policy key: setup is not banned; it is gated by whether the immediate
one-time-trade branch is live.

Grade: complete.

## Resulting Rule

Before boosting with a passed physical receiver:

- name the receiver's job and whether it is irreplaceable;
- ask whether the opposing active can spend Explosion/Self-Destruct into that
  receiver;
- if yes, choose between immediate damage, an absorber switch, or accepting the
  trade only after naming what route remains;
- boost only when the one-time trade is unavailable, covered, or worth the
  risk.

## Next Study Target

Fresh replay segment at the first Agility/Baton Pass receiver or setup
receiver. Score whether Self-Destruct, Explosion, phazing, and immediate attack
are priced before any boost.
