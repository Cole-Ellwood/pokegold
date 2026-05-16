# Sleep Cash-Out Hazard Sack Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_024_smogtours-gen2ou-935947`. This is not fresh progress
proof.

Source basis:

- `reviews/sleep_cashout_hazard_sack_review_001_2026-05-15.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/branch_punish_ranking.md`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Mid-HP Lovely Kiss Lax

Prompt:
Zapdos enters clean against opposing Snorlax at 78%. Snorlax has revealed
Lovely Kiss and Double-Edge, but not Rest or a fourth move. Our Cloyster is
asleep, healthy enough to take a Normal trade, and no Ghost remains. Thunder
damages Snorlax but does not KO before Self-Destruct.

Frozen answer:
Top action: switch the lower-value Normal resist/sack, here Cloyster. Treat
Lovely Kiss + Double-Edge as sleep pressure plus possible Self-Destruct even
before low HP. Thunder is second only if the post-trade route is acceptable.

Answer key: hit.

## Scenario 2 - Surf Was The Bluff

Prompt:
Our sleeping Snorlax faces opposing Cloyster at 36%. Cloyster has already used
Spikes and Surf. Last turn Surf hit Snorlax, but our own sleeping Cloyster can
still enter and resist Normal. If Cloyster Explodes into Snorlax, the endgame
is lost.

Frozen answer:
Top action: switch our Cloyster. After Surf, re-run the low-support four-way
check; do not assume the next turn is Surf again when Explosion now decides the
route.

Answer key: hit.

## Scenario 3 - Hazard-Death Clean Entry

Prompt:
Our Nidoking is at 10% with Spikes on our side, so it cannot re-enter. Opposing
Snorlax is active and likely to attack or use Lovely Kiss. Zapdos is healthy
and wants a clean entry without taking the selected Snorlax move.

Frozen answer:
Top action: switch Nidoking as a controlled hazard-death sack, then bring in
Zapdos. The sack is positive because future Nidoking value is fake and the
Spikes faint cancels the opponent's action in this vanilla replay context.

Answer key: hit.

## Scenario 4 - Do Not Overguard Exact Removal

Prompt:
Zapdos faces Snorlax at 18%. Snorlax has revealed Lovely Kiss and Double-Edge,
but Thunder is guaranteed to KO before Snorlax moves because Snorlax is
paralyzed and in range. Cloyster can switch but would give Snorlax a Rest turn
if Thunder is not used.

Frozen answer:
Top action: Thunder. Cash-out is priced, but exact removal before
Self-Destruct/reset wins. Guarding is wrong when it gives the package another
turn and the active move removes it first.

Answer key: hit.

## Next Use

Resume with one fresh side-known packet, preferably Smogtours or high-ladder.
Before every Snorlax/Cloyster/Gengar/Steelix/Exeggutor turn, freeze:
`package delivered? -> cash-out target? -> guard/sack? -> clean-entry owner`.

