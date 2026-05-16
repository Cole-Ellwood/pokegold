# Low Rest Race Cash-Out Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not fresh replay-transfer
evidence and does not count as proof of broad improvement.

Parent artifact:
`workspace/quick_tests/low_self_ko_transfer_002_smogtours-gen2ou-831951_2026-05-14.md`

Selected action:
Convert the turn-9 severe miss from `831951` into a four-scenario gate for
low-HP Rest races and recoil cash-outs.

## Docs Checked

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/low_self_ko_transfer_002_smogtours-gen2ou-831951_2026-05-14.md`

No new web search was needed for this correction probe because the
decision-relevant source is the parent fresh replay plus existing local policy.
Use web search again before selecting another fresh replay or extracting a new
external rule.

## Score Summary

Scenarios: 4.

Correct top action: 4 / 4.

Speed/order named: 4 / 4.

Target recovery before hit priced: 4 / 4.

Recoil/survival priced: 4 / 4.

Preserved route piece named: 4 / 4.

Positive-selection: 4 / 4.

Severe blunders: 0.

Hidden-info errors: 0.

Measurement status: regression only. The next countable test must be a fresh
unseen replay segment with this Rest-race gate active.

## Scenario 1 - Parent Severe: Low Curselax Into Faster Low Zapdos

Public state:
Vanilla GSC spectator-public. Our Snorlax is at 10%, paralyzed, and +2
Attack/+2 Defense with Curse and Double-Edge revealed. Opponent Zapdos is at
13% with Thunder and Hidden Power revealed. No Rest has been revealed, but Rest
is a strong Zapdos prior. Snorlax may have Rest because it has shown a Curse
set and is at emergency HP.

Frozen answer:
Top action for Snorlax: Rest, confidence medium.

Speed/order:
Zapdos acts before paralyzed Snorlax. If Zapdos has Rest, it heals before
Snorlax's attack lands.

Target recovery before hit:
The target may become 100% before Double-Edge connects, so the target is not
really "13% Zapdos" on the worst serious branch.

Recoil/survival:
Double-Edge into a healed Zapdos likely causes enough recoil to KO 10% Snorlax
while leaving Zapdos alive. That is a bad cash-out.

Preserved route piece:
Rest preserves the boosted Snorlax route and forces the Zapdos route to keep
playing through sleep turns.

Ranked candidates:

1. Rest to preserve Snorlax and deny the recoil cash-out.
2. Switch only if a teammate cleanly owns full Zapdos and Snorlax is no longer
   needed.
3. Double-Edge only if Zapdos cannot Rest before the hit or the recoil math
   still preserves Snorlax.

Score:
Correct. This directly fixes the parent severe.

## Scenario 2 - Non-Recoil Attack Still Fails Into Faster Rest

Public state:
Vanilla GSC spectator-public. Our Cloyster is at 38% against Zapdos at 16%.
Cloyster has revealed Surf and Spikes. Zapdos has revealed Thunder, Hidden
Power, and Rest. Snorlax is healthy in back and owns sleeping or low Zapdos
better than Cloyster does.

Frozen answer:
Top action: switch Snorlax, confidence medium-high.

Speed/order:
Zapdos acts before Cloyster.

Target recovery before hit:
If Zapdos uses Rest first, Surf hits a full-health sleeping Zapdos and does not
convert the route.

Recoil/survival:
Surf has no recoil, but Cloyster may take Thunder before moving if Zapdos
attacks instead. The issue is not recoil here; it is that the attack does not
beat the serious Rest branch.

Preserved route piece:
Cloyster has already set Spikes and can still preserve Explosion/pivot utility.
Snorlax is the cleaner owner of the full or sleeping Zapdos board.

Ranked candidates:

1. Switch Snorlax to own both Rest and Thunder branches.
2. Surf only if Zapdos cannot Rest or if Surf damage into sleeping Zapdos
   creates a named immediate converter.
3. Explosion only if the target, absorber tier, and post-trade converter are
   named; otherwise do not spend Cloyster.

Score:
Correct. Non-recoil damage is still wrong when it fails the Rest branch and
hands over the better owner.

## Scenario 3 - Faster KO Before Rest Is A Real Cash-Out

Public state:
Vanilla GSC spectator-public. Our +2 Snorlax is at 44% and is not paralyzed.
Opponent Zapdos is paralyzed at 13% and has revealed Thunder, Hidden Power,
and Rest. Double-Edge is revealed and KOs Zapdos from current HP. No Ghost,
Rock, or Steel absorber is revealed.

Frozen answer:
Top action: Double-Edge, confidence high.

Speed/order:
Snorlax moves before Zapdos in this constructed state, so Zapdos cannot Rest
before the hit.

Target recovery before hit:
Recovery is not available before damage because Zapdos moves second.

Recoil/survival:
At 44%, Snorlax survives the recoil from KOing a 13% Zapdos and remains a route
piece after Leftovers.

Preserved route piece:
The route piece preserved is Snorlax itself: it removes Zapdos without dying or
letting Zapdos reset.

Ranked candidates:

1. Double-Edge to remove Zapdos before Rest.
2. Rest only if Snorlax is slower, paralyzed, or recoil math changes.
3. Switch only if a revealed absorber branch outweighs the clean KO.

Score:
Correct. The Rest-race gate is not "never attack"; it is "attack only after
speed/order and survival are favorable."

## Scenario 4 - No Strong Recovery Prior Means Active Removal

Public state:
Vanilla GSC spectator-public. Our Zapdos is at 62% against Nidoking at 18%.
Zapdos has Hidden Power Ice revealed. Nidoking has revealed Earthquake and
Lovely Kiss. Rest has not been revealed and is not a strong Nidoking prior.
No Ground immunity or low-value sack is public for the opponent.

Frozen answer:
Top action: Hidden Power Ice, confidence high.

Speed/order:
Zapdos moves before Nidoking.

Target recovery before hit:
There is no revealed or strong-prior recovery branch that changes Nidoking's HP
before the hit.

Recoil/survival:
Hidden Power has no recoil, and Zapdos survives the ordinary counter-branches
well enough to keep its route job.

Preserved route piece:
Zapdos preserves itself by removing the Ground-type pressure immediately rather
than switching and giving Nidoking another support turn.

Ranked candidates:

1. Hidden Power Ice to remove Nidoking.
2. Switch only if Sleep Clause, Zapdos's HP, or a revealed receiver makes the
   support branch more dangerous than the KO.
3. Thunder only if Hidden Power is not available or does not KO.

Score:
Correct. Possible-only recovery cannot block the clear active conversion.

## Transfer Rule

Before attacking a low target with a low or irreplaceable route piece:

1. Who moves first?
2. Can the target heal before the hit, and is that revealed, strong prior, or
   possible only?
3. If the target heals first, does our attack still convert the route?
4. Does recoil, counterdamage, or self-KO leave our piece alive with a job?
5. If attacking fails the Rest branch, which owner takes the healed or sleeping
   target next?

If the target can heal first and the attack no longer converts, choose Rest,
handoff, setup, phaze, or preservation instead of cashing out by habit.
