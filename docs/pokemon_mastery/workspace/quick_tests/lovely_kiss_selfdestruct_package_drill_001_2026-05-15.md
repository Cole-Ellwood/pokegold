# Lovely Kiss Self-Destruct Package Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_020_smogtours-gen2ou-935952`. This is not fresh progress
proof.

Source basis:

- `reviews/lovely_kiss_selfdestruct_package_review_001_2026-05-15.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/branch_punish_ranking.md`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/gs/articles/status`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Low Lovely Kiss Snorlax Cash-Out

Prompt:
p1 sleeping RestTalk Snorlax is active at 48%. p2 Snorlax is at 18%, has
revealed Lovely Kiss and Double-Edge, and has not revealed Rest. p1 Skarmory is
healthy and can enter. p2 Snorlax is slower than p1 Skarmory but can
Self-Destruct before p1 sleeping Snorlax gets useful damage.

Frozen answer:
Switch Skarmory. Sleep Talk damage is tempting, but Self-Destruct into the
RestTalk special wall is the losing branch. Skarmory preserves Snorlax and
still leaves the next owner named.

Answer key: hit.

## Scenario 2 - Sleep Absorber Before Cash-Out Is Live

Prompt:
p1 Skarmory faces p2 Snorlax at 58%. p2 Snorlax has revealed Lovely Kiss only.
p1 RestTalk Snorlax is healthy and can take sleep; p2 Snorlax is not yet low
enough for Self-Destruct to be the main route.

Frozen answer:
Switch RestTalk Snorlax if the sleep attempt is the main package. If staying
with Skarmory, it must be because Toxic or phaze changes the route before sleep
lands, not because Lovely Kiss was ignored.

Answer key: hit.

## Scenario 3 - Exact KO Beats Cash-Out

Prompt:
p1 Snorlax is awake at 82% and p2 Lovely Kiss Snorlax is at 12%. p1's
Double-Edge KOs before p2 can move because p2 is fully paralyzed this turn by a
public speed-control condition, and no switch is expected. p1 Skarmory is
healthy.

Frozen answer:
Take the exact KO. The cash-out branch is priced, but public turn order removes
it this turn. If the KO or move order is uncertain, use the resist/sack instead.

Answer key: hit.

## Scenario 4 - Revealed Rest Boundary

Prompt:
p2 Snorlax has revealed Lovely Kiss, Double-Edge, and Rest. It is at 19% and
cannot Self-Destruct because all four moves are known. p1 sleeping RestTalk
Snorlax is active at 55%; p1 Skarmory is healthy.

Frozen answer:
Do not invent Self-Destruct after the fourth move is revealed. Sleep Talk or
Skarmory handoff can be ranked by the Rest/reset clock instead.

Answer key: hit.

## Next Use

Resume fresh replay transfer. On any Snorlax that reveals Lovely Kiss, write
the package as `sleep -> absorber -> low-HP cash-out? -> preserved route piece`
before choosing damage.

