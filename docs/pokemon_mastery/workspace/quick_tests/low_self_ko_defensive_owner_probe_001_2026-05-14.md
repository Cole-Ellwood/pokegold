# Low Self-KO Defensive Owner Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not fresh replay-transfer
evidence and does not count as proof of broad improvement.

Parent artifact:
`workspace/quick_tests/positive_selection_transfer_004_smogtours-gen2ou-690716_2026-05-14.md`

Selected action:
Convert the severe turn-12 miss from `690716` into a four-scenario defensive
gate for low support pieces that can spend Explosion or Self-Destruct.

## Docs Checked

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md` section `STP-003`
- `docs/pokemon_mastery/workspace/quick_tests/support_entry_explosion_absorber_probe_001_2026-05-14.md`

No new web search was needed for this correction probe because the
decision-relevant source is the parent fresh replay plus existing local policy.
Use web search again before selecting another fresh replay or extracting a new
external rule.

## Score Summary

Scenarios: 4.

Correct top action: 4 / 4.

Speed/order named: 4 / 4.

Survival priced: 4 / 4.

Defensive owner named when needed: 4 / 4.

Positive-selection: 4 / 4.

Severe blunders: 0.

Hidden-info errors: 0.

Measurement status: regression only. The next countable test must be a fresh
unseen replay segment with this self-KO gate active.

## Scenario 1 - Parent Severe: Low Gengar Into Valuable Zapdos

Public state:
Vanilla GSC spectator-public. Our Zapdos is healthy and is the current special
pressure route. Opponent Gengar is low, has revealed Thief, and is active.
Explosion is not revealed, but low GSC Gengar spending itself into Zapdos is a
strong prior. We have Steelix available and it is not our only answer to a
larger threat.

Frozen answer:
Top action: switch Steelix, confidence medium-high.

Speed/order:
Gengar is naturally faster than Zapdos, so if Explosion is clicked, Zapdos does
not get to move first.

Survival:
Zapdos likely does not survive a clean Explosion well enough to preserve the
route. Steelix resists the Normal-type self-KO and keeps Zapdos intact.

Ranked candidates:

1. Switch Steelix to cover Explosion while preserving Zapdos.
2. Thunder only if the Gengar set or previous turns make Explosion a low-prior
   branch and Gengar staying without self-KO is the larger route.
3. Hidden Power or other coverage only if the Golem/Ground switch is stronger
   than the self-KO branch.

Worst branch:
Gengar uses Thief or switches and Steelix gives up immediate pressure. That is
acceptable because losing Zapdos to a faster self-KO is route-ending.

Score:
Correct. This is the direct fix for `690716` turn 12.

## Scenario 2 - Active KO Beats The Self-KO Branch

Public state:
Vanilla GSC. Our Raikou is active against paralyzed Gengar at 9%. Gengar has
revealed Explosion. Raikou has Thunderbolt, which KOs from this range. There
is no Ground-type already revealed; a Ground switch is possible only.

Frozen answer:
Top action: Thunderbolt, confidence high.

Speed/order:
Paralysis makes Gengar slower than Raikou, so Raikou can KO before Explosion if
Gengar stays.

Survival:
Raikou does not need to survive Explosion if it moves first and KOs. Switching
to an absorber would preserve against a lower-priority branch while giving up
the clean removal.

Ranked candidates:

1. Thunderbolt to remove Gengar before self-KO.
2. Switch to Ghost/Steel only if speed order is uncertain or Raikou is not
   actually faster.
3. Coverage into a possible Ground switch only if that switch is a strong prior
   from public play, not merely legal.

Worst branch:
Opponent switches a Ground into Thunderbolt. Because that branch is possible
only, it cannot outrank the revealed faster KO.

Score:
Correct. The self-KO gate does not mean auto-switching.

## Scenario 3 - Side-Known Ghost Absorber Into Low Cloyster

Public state:
Vanilla GSC side-known mode. Our Machamp is the main breaker. Opponent
Cloyster has already set Spikes, is at 35%, and has revealed Explosion. Our
healthy Gengar is available and is not the only remaining answer to the
opponent's Snorlax.

Frozen answer:
Top action: switch Gengar, confidence high.

Speed/order:
Cloyster is faster than Machamp in normal GSC order, so Machamp does not get
to safely move first.

Survival:
Machamp is too important to trade into Cloyster's spent support piece. Gengar
blanks Explosion and preserves the breaker route.

Ranked candidates:

1. Switch Gengar to absorb Explosion.
2. Stay and attack only if damage rolls and speed/order prove Machamp removes
   Cloyster before Explosion.
3. Switch to a lower-value resist if Gengar has a more important irreplaceable
   job.

Worst branch:
Cloyster uses Surf or switches, costing Gengar entry tempo. That is acceptable
because the high-cost branch is losing Machamp to a live revealed self-KO.

Score:
Correct. Side-known mode must use the known absorber when the role cost is
acceptable.

## Scenario 4 - Coverage Into Branch When Self-KO Is Denied By Order

Public state:
Vanilla GSC. Our Zapdos is active against Golem at 42%. Golem has revealed
Explosion, but Zapdos has Hidden Power Water and is faster. Opponent's sleeping
Snorlax is the obvious switch if Golem is preserved; Cloyster is also possible.

Frozen answer:
Top action: Hidden Power Water, confidence medium-high.

Speed/order:
Zapdos moves before Golem, so if Golem stays, Hidden Power Water removes it
before Explosion.

Survival:
No defensive owner is needed if Zapdos can act first with accurate coverage.
The owner switch becomes worse because it lets Golem preserve itself or gives
Snorlax a free reset.

Ranked candidates:

1. Hidden Power Water to cover the stay-in self-KO user and punish the Ground
   branch.
2. Switch to Steel/Ghost only if Zapdos is not actually faster, Hidden Power is
   not revealed to our side, or a miss/roll changes survival.
3. Thunder only if the opponent is very likely to switch out and the Ground
   stay is no longer a serious branch.

Worst branch:
Snorlax switches into Hidden Power Water and takes modest damage. That is
acceptable because the move removes Golem if it stays and does not risk Zapdos
to Explosion.

Score:
Correct. The defensive gate still allows active coverage when speed/order
denies the self-KO.

## Transfer Rule

Before attacking a low Gengar, Cloyster, Forretress, Golem, or other self-KO
candidate with a valuable active:

1. Is Explosion, Self-Destruct, Destiny Bond, or a similar one-time trade
   revealed, a strong prior, or possible only?
2. Who moves first, and does our active KO before the self-KO move?
3. If the self-KO lands, does our active survive with its route job intact?
4. Which lower-value owner, immunity, resist, or sack preserves the route?
5. If we stay in, what concrete route does active pressure or coverage improve
   enough to accept the self-KO branch?

If questions 2 and 3 are bad for us and question 4 has an available owner, the
top action should usually be the defensive owner, not active pressure.
