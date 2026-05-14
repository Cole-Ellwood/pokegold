# Adaptive Lead Audit: Boss Route Maps

Purpose: connect the local adaptive-lead source rule to the boss route maps so
pre-battle plans do not assume the wrong opener.

Source checked:

- `engine/battle/core.asm`
- `engine/battle/ai/boss_policy_move.asm`
- `constants/battle_constants.asm`
- `data/trainers/ai_tiers.asm`
- `data/trainers/parties.asm`
- `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md`

## Result

For bosses in `AdaptiveLeadMap`, plan against the first three living source
party members, with the first member favored. For bosses not in that map, treat
the first listed living party member as the opener unless a runtime trace or
special script contradicts it.

| Boss | Opening policy | Source-party opener set |
| --- | --- | --- |
| Falkner | fixed-first | Pidgeotto |
| Bugsy | fixed-first | Ariados |
| Whitney | fixed-first | Clefairy |
| Morty | fixed-first | Haunter |
| Chuck | adaptive first-three | Sudowoodo / Hitmontop / Hitmonlee |
| Jasmine | adaptive first-three | Magneton / Forretress / Scizor |
| Pryce | adaptive first-three | Cloyster / Dewgong / Sneasel |
| Clair | adaptive first-three | Gligar / Mantine / Kingdra |
| Brock | adaptive first-three | Omastar / Corsola / Golem |
| Misty | adaptive first-three | Politoed / Starmie / Quagsire |
| Lt. Surge | adaptive first-three | Magneton / Electrode / Raichu |
| Erika | adaptive first-three | Tangela / Jumpluff / Bellossom |
| Janine | adaptive first-three | Qwilfish / Tentacruel / Muk |
| Sabrina | adaptive first-three | Mr. Mime / Jynx / Espeon |
| Blaine | adaptive first-three | Magcargo / Ninetales / Rapidash |
| Blue | adaptive first-three | Pidgeot / Porygon2 / Gyarados |
| Will | adaptive first-three | Forretress / Starmie / Slowbro |
| Koga | adaptive first-three | Ariados / Tentacruel / Muk |
| Bruno | adaptive first-three | Onix / Hitmontop / Hitmonlee |
| Karen | adaptive first-three | Gengar / Donphan / Murkrow |
| Lance | adaptive first-three | Steelix / Gyarados / Ampharos |
| Red | fixed-first | Pikachu |

## Strategic Implication

Route sheets that say "pressure the lead" must be read through this audit.
For fixed-first bosses, the first listed Pokemon can receive most of the
turn-1 attention. For adaptive bosses, the lead plan must survive the whole
first-three opener set.

Examples:

- Brock is not only an Omastar opening. A player lead also has to avoid losing
  the route map to Corsola or Golem.
- Misty is not only a Politoed rain/sleep opening. Starmie and Quagsire can be
  first-turn route tests.
- Blue can open with Pidgeot, Porygon2, or Gyarados, so the lead must not spend
  the only Dragon Dance answer just because it beats Pidgeot.
- Red remains a fixed Pikachu opening from current source, so Red's first-turn
  plan can focus on Pikachu while preserving answers to the later routes.

## Notebook Follow-Up

- Future pre-battle sheets for adaptive bosses should fill `Boss likely
  openings` with the first-three set above.
- Existing route maps remain useful, but any map that lacks an inline opener
  family should be read through this audit before choosing a lead.
- Runtime traces should be added later for at least one adaptive boss and one
  fixed-first boss.

## Route Sheet Coverage Update - 2026-05-14

Explicit opener-family section or equivalent matrix already present:

```text
Brock: Omastar / Corsola / Golem
Misty: Politoed / Starmie / Quagsire
Janine: Qwilfish / Tentacruel / Muk
Blue: Pidgeot / Porygon2 / Gyarados
Koga: Ariados / Tentacruel / Muk
Will: Forretress / Starmie / Slowbro
Bruno: Onix / Hitmontop / Hitmonlee
Karen: Gengar / Donphan / Murkrow
Lance: Steelix / Gyarados / Ampharos
Sabrina: Mr. Mime / Jynx / Espeon
Blaine: Magcargo / Ninetales / Rapidash
Chuck: Sudowoodo / Hitmontop / Hitmonlee
Jasmine: Magneton / Forretress / Scizor
Pryce: Cloyster / Dewgong / Sneasel
Clair: Gligar / Mantine / Kingdra
Lt. Surge: Magneton / Electrode / Raichu
Erika: Tangela / Jumpluff / Bellossom
```

Adaptive sheets that still need inline opener-family cleanup: none as of this
audit update.

Cleanup standard:

- Add `Boss likely openings` near the roster.
- Update `Best lead profile` so it covers all three possible starts, not only
  the first-listed Pokemon.
- Reword the first-turn question as "Which adaptive opener appeared?" when the
  sheet otherwise reads like a fixed-lead fight.
- Keep the no-Team-Preview boundary explicit: player-side prep can use
  source-known boss opener policy; ordinary boss AI cannot know the player's
  unrevealed team.
