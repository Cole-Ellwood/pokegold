# Toxic Recover Clock Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_023_gen2ou-2608738130_p1_2026-05-15.md`

Reason for study:
Transfer 023 was not a strong replay oracle, but it exposed two live-card
failures. I treated Thunder into Shellder as exact removal even though
paralysis let Explosion move first, then I kept choosing Double-Edge while
Toxic already made Corsola's Recover loop lose and Curse converted the rest of
the game.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/role_package_ledger.md`
- `source_to_policy_ledger.md` STP-017, recovery reset policy
- `cookbook.md` recovery window and retaliation-move tests
- `worked_examples/brock_pre_battle_route_sheet.md` Corsola recovery/hazard
  route notes

Current web sources:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Corsola analysis:
  `https://www.smogon.com/forums/threads/corsola-qc-3-3-gp-2-2.3460776/`
- Smogon Gold/Silver Competitive Resources:
  `https://www.smogon.com/resources/competitive/gs/`

## Confirmed Lessons

Explosion is a route trade, not just a low-HP trick:
The GSC Explosion guide frames Explosion as a deliberate trade-down tool, and
the Cloyster material ties Explosion to trading after the support job is done.
The local cash-out rule was correct, but I applied the "exact removal beats
fear" exception too loosely. Exact removal must include move order. A paralyzed
Raikou that cannot act before Shellder is not removing the self-KO user first.

Toxic can be the converter:
The local recovery policy already says recovery is a route reset only if it
erases the damage race. Corsola material makes Recover plus Toxic its main
stalling structure, and Mirror Coat is a real surprise branch against special
attackers. In this replay, once Corsola was badly poisoned, Recover stopped
resetting progress because the poison counter outpaced it. Curse used those
forced Recover turns to build the game-winning piece.

Mirror Coat remains a priced branch, not an anchor:
Corsola's Mirror Coat can surprise a special attacker, but the source also
frames it as costly and force-out prone. Because Surf matched the actual move
and Tentacruel had already delivered Toxic, this is a risk-pricing note rather
than a second hidden-info error.

## Policy Correction

- `reset_loop_denial.md`: added Toxic/poison clock wording for Recover loops.
- `spend_or_save_piece.md`: clarified that exact removal includes turn order,
  paralysis, and whether the self-KO move acts first.
- `migration_map.md`: added the compressed Toxic/Recover clock row.

## Measurement Note

This packet is a failed low-oracle transfer, not proof of regression by itself.
It does count against the structural-repair sample because the miss repeated a
live decision-shape problem: safe active damage was promoted over the move that
improved the next board. The next packets should be stronger tournament or
high-ladder replays where the same clock/cash-out rules can be tested without
novelty-team noise.

