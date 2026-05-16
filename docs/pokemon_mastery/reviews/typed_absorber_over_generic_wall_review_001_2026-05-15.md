# Typed Absorber Over Generic Wall Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_015_gen2ou-2609398768_p1_2026-05-15.md`

Reason for study:
The fresh packet was not progress. The active-converter repair worked on
Tyranitar Roar and Cloyster Explosion, but I repeatedly chose generic special
bulk before pricing typed/status absorbers.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/converter_before_script.md`

Current web sources:

- Smogon, Starmie through the years:
  `https://www.smogon.com/articles/starmie-through-years`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, GSC OU lead analysis:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Confirmed Lessons

Starmie in GSC is a support Pokemon, not just a weak special attacker. Smogon
sources describe Rapid Spin, Recover, Reflect, Thunder Wave, and defensive
coverage as core parts of its role. Sending Snorlax into Starmie without
pricing Thunder Wave can donate status to a central route piece.

Nidoking's Electric immunity is not a no-Team-Preview leak when Nidoking is
our known teammate. Smogon threat material treats that immunity as part of its
value into Electric pressure. The fallback is to price Hidden Power Ice/Water,
not to ignore the typed absorber and default to Snorlax.

Zapdos still threatens with coverage. The correction is not "always go
Nidoking." It is: if the likely move is Electric and the typed absorber creates
progress, promote it; if Hidden Power coverage is revealed or the range is bad,
use the generic wall or another owner.

## Policy Correction

- `role_package_ledger.md`: added a typed/status absorber check before generic
  wall handoffs.
- `public_info_tiers.md`: strong-prior STAB/status can promote typed/status
  absorbers, with fallback for coverage.
- `name_next_board_owner.md`: owner selection now asks whether generic bulk or
  typed/status absorption actually owns the board.

## Measurement Note

Not progress. Transfer 015 was 3/8 top and had one hidden-info error from
failing to price Starmie's strong-prior Thunder Wave.

