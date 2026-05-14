# Boss Route Map Source Alignment Audit - 2026-05-13

Purpose: confirm that the boss route maps are grounded in the current trainer
party source before using them as study material for turn-1 planning.

## Scope

Checked every `*_turn1_route_sheet.md` in this folder against the first party
entry for its matching boss group in `data/trainers/parties.asm`.

The audit checked:

- boss species names;
- explicit moves listed in source parties;
- held items listed in source parties;
- route-map text after normalizing assembly constants such as `WING_ATTACK`
  into human text such as `Wing Attack`;
- `PSYCHIC_M` as `Psychic`;
- `MR__MIME` as `Mr. Mime`.
- item constants with implementation suffixes, such as `BLACKBELT_I`, as their
  displayed item names, such as `Black Belt`.

Ignored:

- empty `NO_MOVE` slots;
- exact damage, type, passive, item, and AI behavior claims. Those still require
  local mechanics evidence before turn advice.

## Result

No substantive roster, moveset, or held-item mismatch was found across the
current boss route maps.

The only literal residual after normalization was Falkner Spearow's two
`NO_MOVE` placeholders, which are not battle actions and should not be treated
as missing route-map content.

## Practical Meaning

The route maps can be used as source-grounded pre-battle study sheets for boss
species, public movesets, and held items. They are not proof of damage
thresholds, local type interactions, passive behavior, or AI choice behavior.

Before giving exact turn advice, still check:

- the user's team, levels, HP, status, moves, and items;
- `data/types/type_matchups.asm` and type passive sources for type claims;
- damage debugger or fixture evidence for KO/survival thresholds;
- boss AI traces or current public-state incentives for likely moves.
