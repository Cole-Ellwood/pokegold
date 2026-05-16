# Growth Pass Sequence Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_021_gen2ou-2609820489`. This is not fresh progress proof.

Source basis:

- `reviews/growth_pass_sequence_review_001_2026-05-15.md`
- `heuristic_core/rescore_after_reveal.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Attack Before Pass

Prompt:
Umbreon is at +1 Special Attack against Cloyster at 100%. Umbreon's Hidden
Power is super effective and drops Cloyster into forced range. Cloyster can set
Spikes, Toxic, or threaten Explosion on the following turn. Jolteon is a strong
receiver but would enter through Spikes if they go up.

Frozen answer:
Use Hidden Power first. The current boosted coverage changes the active target
before the pass; passing immediately lets Cloyster keep its support/cash-out
sequence intact.

Answer key: hit.

## Scenario 2 - Guard The Low Support Cash-Out

Prompt:
After boosted Hidden Power, Cloyster is at 38% and has set Spikes. Gengar is
available. Umbreon is still useful as the Growth passer.

Frozen answer:
Switch Gengar. The low support piece has delivered Spikes and now has
Explosion as the branch. Damage is no longer the punish; the Ghost guard is.

Answer key: hit.

## Scenario 3 - Boost Mirror

Prompt:
Umbreon and opposing Vaporeon are both at full HP and both at +1 Special
Attack. Umbreon survives a +1 Hydro Pump, and another Growth makes its Hidden
Power damage force Vaporeon into pass-or-attack pressure. Passing to Jolteon
this turn would make Jolteon take Spikes plus +1 Hydro Pump.

Frozen answer:
Use Growth. Passing now loses the receiver to the immediate hit; attacking now
does not yet force the next board. The boost is progress because the next
attack or pass survives and converts.

Answer key: hit.

## Scenario 4 - Pass Now

Prompt:
Vaporeon has received +2 Special Attack from Umbreon and faces opposing
Vaporeon at +2. Vaporeon resists the incoming Hydro Pump this turn, but Jolteon
would not have survived it on the previous turn. After this turn, Jolteon can
enter at enough HP to KO with boosted Thunderbolt.

Frozen answer:
Baton Pass to Jolteon now. The receiver survives the Spikes tax and owns the
next board; the pass timing is correct because Vaporeon already absorbed the
dangerous hit.

Answer key: hit.

## Next Use

Resume fresh replay transfer. On every Growth or Baton Pass turn, freeze a
three-way ranking: `boost-now`, `attack-now`, `pass-now`, with receiver HP after
Spikes and the incoming hit.

