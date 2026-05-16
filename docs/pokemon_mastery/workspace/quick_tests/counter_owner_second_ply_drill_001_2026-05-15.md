# Counter-Owner Second-Ply Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_011_gen2ou-2609904983`. This is not fresh progress proof.

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Support Board Owner

Prompt:
Your Umbreon is healthy against opposing Forretress. Forretress has not yet
used Spikes, and your available pressure owners are Jolteon and Vaporeon.

Frozen answer:
Switch Jolteon if the route is to meet the Forretress support board with speed
and status/electric pressure. Vaporeon is acceptable only when the plan names
the Electric counter-owner and the immediate Water hit still converts through
that branch.

Answer key: hit.

## Scenario 2 - First Handoff Invites Snorlax

Prompt:
Your Jolteon is in against Forretress after Spikes went up. Snorlax is public,
already paralyzed, and is the natural Electric/status absorber.

Frozen answer:
Switch to the Snorlax owner instead of using generic Thunder Wave. Thunder Wave
does not convert if the named branch is already paralyzed Snorlax.

Answer key: hit.

## Scenario 3 - Vaporeon Invites Electric

Prompt:
Your Vaporeon faces paralyzed Snorlax. Raikou is public at mid health and is
the natural counter-owner. Vaporeon has Growth and Hydro Pump.

Frozen answer:
Hydro Pump if the Electric counter-owner is the main branch. Growth is top only
when Snorlax staying is the route or when the answer explicitly accepts the
Electric branch as a high-risk read with fallback.

Answer key: hit.

## Scenario 4 - Do Not Overlearn

Prompt:
Your Vaporeon faces Snorlax, no Electric has been revealed, and the opponent's
best public response is to stay or use a normal special wall that does not
force Vaporeon out immediately.

Frozen answer:
Growth. The second-ply rule is not a command to always attack; it promotes the
counter-owner punish only when that counter-owner is revealed or a strong
prior.

Answer key: hit.

