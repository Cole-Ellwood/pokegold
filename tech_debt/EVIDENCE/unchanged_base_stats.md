# Unchanged Base Stats — Audit Snapshot

**Generated:** 2026-05-03  
**Comparator:** local `data/pokemon/base_stats/<name>.asm` vs `pret/pokegold@upstream/master (fetched 2026-05-03)`  
**Total species compared:** 251  
**Unchanged:** 74  
**Changed:** 177  

Scope: the **six base stats** (HP, ATK, DEF, SPE, SPA, SPD) only.
Other fields (types, catch rate, base exp, items, gender, growth
rate, egg groups, TM/HM, learnsets, evolution data) are NOT compared
here — many local files differ from upstream in those fields without
touching base stats. "Unchanged" in this file means stat-line-equal,
not file-equal.

Comparator source: `.local/compare_base_stats.py` (scratch; not
checked in). Reproduce with `git fetch upstream master &&
python3 .local/compare_base_stats.py`.

Spot-checks (5/5 PASS, 2026-05-03): BULBASAUR=match, SUNKERN=match,
SNORLAX=match, CELEBI=match, WOBBUFFET=mismatch (220/33/65/33/33/65
vs upstream 190/33/58/33/33/58 — confirmed buff per
`docs/balance_intent.md`).

Cross-check vs `docs/balance_intent.md` locked/provisional rows with
"Raw stats" entries: all 17 species (UNOWN, DITTO, SMEARGLE,
WOBBUFFET, LEDIAN, SUDOWOODO, JYNX, LANTURN, MANTINE, DEWGONG,
POLITOED, QWILFISH, CORSOLA, DELIBIRD, ARIADOS, YANMA, FARFETCH_D)
are in the Changed list. ELECTRODE — documented as a moveset-only
buff in balance_intent — also shows stat changes (Speed 140→170,
SpA 80→100); the doc is incomplete on that species, but the
comparator is faithful to source.

## Exclusions

- `UNOWN_*` letter variants do not exist as separate base_stats
  records in this codebase; only `UNOWN` (#201) has a base_stats
  file. The 26 letter forms share that one record.
- `EGG` and `NO_MON` are pokemon constants but have no base_stats
  file (they are not in the include chain).
- All 251 entries below are full-form Pokémon (Johto + Kanto).
  No species was excluded for being non-final-evolution; the
  comparison is purely "stats == upstream". Pre-evolutions like
  PICHU, CLEFFA, IGGLYBUFF, TYROGUE, etc. are evaluated like any
  other species.

## Unchanged (base stats == pret/pokegold canonical)

These species have **not been touched at the stat level** by this
hack. They are candidates for the user's rebalance pass.

| Dex# | Name | HP | ATK | DEF | SPE | SPA | SPD | Match? |
|-----:|------|---:|----:|----:|----:|----:|----:|:------:|
| 001 | BULBASAUR | 45 | 49 | 49 | 45 | 65 | 65 | Y |
| 002 | IVYSAUR | 60 | 62 | 63 | 60 | 80 | 80 | Y |
| 004 | CHARMANDER | 39 | 52 | 43 | 65 | 60 | 50 | Y |
| 005 | CHARMELEON | 58 | 64 | 58 | 80 | 80 | 65 | Y |
| 007 | SQUIRTLE | 44 | 48 | 65 | 43 | 50 | 64 | Y |
| 008 | WARTORTLE | 59 | 63 | 80 | 58 | 65 | 80 | Y |
| 010 | CATERPIE | 45 | 30 | 35 | 45 | 20 | 20 | Y |
| 013 | WEEDLE | 40 | 35 | 30 | 50 | 20 | 20 | Y |
| 029 | NIDORAN_F | 55 | 47 | 52 | 41 | 40 | 40 | Y |
| 032 | NIDORAN_M | 46 | 57 | 40 | 50 | 40 | 40 | Y |
| 035 | CLEFAIRY | 70 | 45 | 48 | 35 | 60 | 65 | Y |
| 039 | JIGGLYPUFF | 115 | 45 | 20 | 20 | 45 | 25 | Y |
| 041 | ZUBAT | 40 | 45 | 35 | 55 | 30 | 40 | Y |
| 043 | ODDISH | 45 | 50 | 55 | 30 | 75 | 65 | Y |
| 044 | GLOOM | 60 | 65 | 70 | 40 | 85 | 75 | Y |
| 046 | PARAS | 35 | 70 | 55 | 25 | 45 | 55 | Y |
| 048 | VENONAT | 60 | 55 | 50 | 45 | 40 | 55 | Y |
| 052 | MEOWTH | 40 | 45 | 35 | 90 | 40 | 40 | Y |
| 058 | GROWLITHE | 55 | 70 | 45 | 60 | 70 | 50 | Y |
| 060 | POLIWAG | 40 | 50 | 40 | 90 | 40 | 40 | Y |
| 063 | ABRA | 25 | 20 | 15 | 90 | 105 | 55 | Y |
| 069 | BELLSPROUT | 50 | 75 | 35 | 40 | 70 | 30 | Y |
| 072 | TENTACOOL | 40 | 40 | 35 | 70 | 50 | 100 | Y |
| 074 | GEODUDE | 40 | 80 | 100 | 20 | 30 | 30 | Y |
| 077 | PONYTA | 50 | 85 | 55 | 90 | 65 | 65 | Y |
| 079 | SLOWPOKE | 90 | 65 | 65 | 15 | 40 | 40 | Y |
| 084 | DODUO | 35 | 85 | 45 | 75 | 35 | 35 | Y |
| 086 | SEEL | 65 | 45 | 55 | 45 | 45 | 70 | Y |
| 088 | GRIMER | 80 | 80 | 50 | 25 | 40 | 50 | Y |
| 090 | SHELLDER | 30 | 65 | 100 | 40 | 45 | 25 | Y |
| 092 | GASTLY | 30 | 35 | 30 | 80 | 100 | 35 | Y |
| 095 | ONIX | 35 | 45 | 160 | 70 | 30 | 45 | Y |
| 096 | DROWZEE | 60 | 48 | 45 | 42 | 43 | 90 | Y |
| 098 | KRABBY | 30 | 105 | 90 | 50 | 25 | 25 | Y |
| 102 | EXEGGCUTE | 60 | 40 | 80 | 40 | 60 | 45 | Y |
| 104 | CUBONE | 50 | 50 | 95 | 35 | 40 | 50 | Y |
| 109 | KOFFING | 40 | 65 | 95 | 35 | 60 | 45 | Y |
| 118 | GOLDEEN | 45 | 67 | 60 | 63 | 35 | 50 | Y |
| 120 | STARYU | 30 | 45 | 55 | 85 | 70 | 55 | Y |
| 129 | MAGIKARP | 20 | 10 | 55 | 80 | 15 | 20 | Y |
| 133 | EEVEE | 55 | 55 | 50 | 55 | 45 | 65 | Y |
| 137 | PORYGON | 65 | 60 | 70 | 40 | 85 | 75 | Y |
| 138 | OMANYTE | 35 | 40 | 100 | 35 | 90 | 55 | Y |
| 140 | KABUTO | 30 | 80 | 90 | 55 | 55 | 45 | Y |
| 143 | SNORLAX | 160 | 110 | 65 | 30 | 65 | 110 | Y |
| 147 | DRATINI | 41 | 64 | 45 | 50 | 50 | 50 | Y |
| 150 | MEWTWO | 106 | 110 | 90 | 130 | 154 | 90 | Y |
| 151 | MEW | 100 | 100 | 100 | 100 | 100 | 100 | Y |
| 158 | TOTODILE | 50 | 65 | 64 | 43 | 44 | 48 | Y |
| 167 | SPINARAK | 40 | 60 | 40 | 30 | 40 | 40 | Y |
| 170 | CHINCHOU | 75 | 38 | 38 | 67 | 56 | 56 | Y |
| 172 | PICHU | 20 | 40 | 15 | 60 | 35 | 35 | Y |
| 173 | CLEFFA | 50 | 25 | 28 | 15 | 45 | 55 | Y |
| 174 | IGGLYBUFF | 90 | 30 | 15 | 15 | 40 | 20 | Y |
| 175 | TOGEPI | 35 | 20 | 65 | 20 | 40 | 65 | Y |
| 177 | NATU | 40 | 50 | 45 | 70 | 70 | 45 | Y |
| 179 | MAREEP | 55 | 40 | 40 | 35 | 65 | 45 | Y |
| 180 | FLAAFFY | 70 | 55 | 55 | 45 | 80 | 60 | Y |
| 187 | HOPPIP | 35 | 35 | 40 | 50 | 35 | 55 | Y |
| 188 | SKIPLOOM | 55 | 45 | 50 | 80 | 45 | 65 | Y |
| 191 | SUNKERN | 30 | 30 | 30 | 30 | 30 | 30 | Y |
| 194 | WOOPER | 55 | 45 | 45 | 15 | 25 | 25 | Y |
| 209 | SNUBBULL | 60 | 80 | 50 | 30 | 40 | 40 | Y |
| 220 | SWINUB | 50 | 50 | 40 | 50 | 30 | 30 | Y |
| 223 | REMORAID | 35 | 65 | 35 | 65 | 65 | 35 | Y |
| 228 | HOUNDOUR | 45 | 60 | 30 | 65 | 80 | 50 | Y |
| 231 | PHANPY | 90 | 60 | 60 | 40 | 40 | 40 | Y |
| 236 | TYROGUE | 35 | 35 | 35 | 35 | 35 | 35 | Y |
| 238 | SMOOCHUM | 45 | 30 | 15 | 65 | 85 | 65 | Y |
| 239 | ELEKID | 45 | 63 | 37 | 95 | 65 | 55 | Y |
| 240 | MAGBY | 45 | 75 | 37 | 83 | 70 | 55 | Y |
| 246 | LARVITAR | 50 | 64 | 50 | 41 | 45 | 50 | Y |
| 247 | PUPITAR | 70 | 84 | 70 | 51 | 65 | 70 | Y |
| 251 | CELEBI | 100 | 100 | 100 | 100 | 100 | 100 | Y |

**Unchanged count:** 74

## Changed (stats already rebalanced)

Names only — full per-species rows in the "Full reference table"
section below if needed. The Changed list is what the rebalance
has already touched; do not re-buff without checking
`docs/balance_intent.md`.

| | | |
|---|---|---|
| VENUSAUR | MUK | CROBAT |
| CHARIZARD | CLOYSTER | LANTURN |
| BLASTOISE | HAUNTER | TOGETIC |
| METAPOD | GENGAR | XATU |
| BUTTERFREE | HYPNO | AMPHAROS |
| KAKUNA | KINGLER | BELLOSSOM |
| BEEDRILL | VOLTORB | MARILL |
| PIDGEY | ELECTRODE | AZUMARILL |
| PIDGEOTTO | EXEGGUTOR | SUDOWOODO |
| PIDGEOT | MAROWAK | POLITOED |
| RATTATA | HITMONLEE | JUMPLUFF |
| RATICATE | HITMONCHAN | AIPOM |
| SPEAROW | LICKITUNG | SUNFLORA |
| FEAROW | WEEZING | YANMA |
| EKANS | RHYHORN | QUAGSIRE |
| ARBOK | RHYDON | ESPEON |
| PIKACHU | CHANSEY | UMBREON |
| RAICHU | TANGELA | MURKROW |
| SANDSHREW | KANGASKHAN | SLOWKING |
| SANDSLASH | HORSEA | MISDREAVUS |
| NIDORINA | SEADRA | UNOWN |
| NIDOQUEEN | SEAKING | WOBBUFFET |
| NIDORINO | STARMIE | GIRAFARIG |
| NIDOKING | MR__MIME | PINECO |
| CLEFABLE | SCYTHER | FORRETRESS |
| VULPIX | JYNX | DUNSPARCE |
| NINETALES | ELECTABUZZ | GLIGAR |
| WIGGLYTUFF | MAGMAR | STEELIX |
| GOLBAT | PINSIR | GRANBULL |
| VILEPLUME | TAUROS | QWILFISH |
| PARASECT | GYARADOS | SCIZOR |
| VENOMOTH | LAPRAS | SHUCKLE |
| DIGLETT | DITTO | HERACROSS |
| DUGTRIO | VAPOREON | SNEASEL |
| PERSIAN | JOLTEON | TEDDIURSA |
| PSYDUCK | FLAREON | URSARING |
| GOLDUCK | OMASTAR | SLUGMA |
| MANKEY | KABUTOPS | MAGCARGO |
| PRIMEAPE | AERODACTYL | PILOSWINE |
| ARCANINE | ARTICUNO | CORSOLA |
| POLIWHIRL | ZAPDOS | OCTILLERY |
| POLIWRATH | MOLTRES | DELIBIRD |
| KADABRA | DRAGONAIR | MANTINE |
| ALAKAZAM | DRAGONITE | SKARMORY |
| MACHOP | CHIKORITA | HOUNDOOM |
| MACHOKE | BAYLEEF | KINGDRA |
| MACHAMP | MEGANIUM | DONPHAN |
| WEEPINBELL | CYNDAQUIL | PORYGON2 |
| VICTREEBEL | QUILAVA | STANTLER |
| TENTACRUEL | TYPHLOSION | SMEARGLE |
| GRAVELER | CROCONAW | HITMONTOP |
| GOLEM | FERALIGATR | MILTANK |
| RAPIDASH | SENTRET | BLISSEY |
| SLOWBRO | FURRET | RAIKOU |
| MAGNEMITE | HOOTHOOT | ENTEI |
| MAGNETON | NOCTOWL | SUICUNE |
| FARFETCH_D | LEDYBA | TYRANITAR |
| DODRIO | LEDIAN | LUGIA |
| DEWGONG | ARIADOS | HO_OH |

**Changed count:** 177

## Full reference table (all 251)

Match column: `Y` = stats line is byte-for-byte equal to upstream;
`N` = at least one of the six stats differs (the upstream values
are shown in parentheses).

| Dex# | Name | HP | ATK | DEF | SPE | SPA | SPD | Base-game match? |
|-----:|------|---:|----:|----:|----:|----:|----:|:----------------:|
| 001 | BULBASAUR | 45 | 49 | 49 | 45 | 65 | 65 | Y |
| 002 | IVYSAUR | 60 | 62 | 63 | 60 | 80 | 80 | Y |
| 003 | VENUSAUR | 95 | 97 | 98 | 95 | 115 | 115 | N (80/82/83/80/100/100) |
| 004 | CHARMANDER | 39 | 52 | 43 | 65 | 60 | 50 | Y |
| 005 | CHARMELEON | 58 | 64 | 58 | 80 | 80 | 65 | Y |
| 006 | CHARIZARD | 93 | 99 | 93 | 115 | 124 | 100 | N (78/84/78/100/109/85) |
| 007 | SQUIRTLE | 44 | 48 | 65 | 43 | 50 | 64 | Y |
| 008 | WARTORTLE | 59 | 63 | 80 | 58 | 65 | 80 | Y |
| 009 | BLASTOISE | 94 | 98 | 115 | 93 | 100 | 120 | N (79/83/100/78/85/105) |
| 010 | CATERPIE | 45 | 30 | 35 | 45 | 20 | 20 | Y |
| 011 | METAPOD | 60 | 30 | 55 | 30 | 25 | 25 | N (50/20/55/30/25/25) |
| 012 | BUTTERFREE | 90 | 45 | 50 | 110 | 95 | 110 | N (60/45/50/70/80/80) |
| 013 | WEEDLE | 40 | 35 | 30 | 50 | 20 | 20 | Y |
| 014 | KAKUNA | 45 | 40 | 50 | 35 | 25 | 25 | N (45/25/50/35/25/25) |
| 015 | BEEDRILL | 75 | 120 | 40 | 120 | 45 | 80 | N (65/80/40/75/45/80) |
| 016 | PIDGEY | 50 | 45 | 40 | 56 | 35 | 35 | N (40/45/40/56/35/35) |
| 017 | PIDGEOTTO | 70 | 60 | 60 | 71 | 50 | 60 | N (63/60/55/71/50/50) |
| 018 | PIDGEOT | 113 | 80 | 95 | 91 | 70 | 110 | N (83/80/75/91/70/70) |
| 019 | RATTATA | 30 | 70 | 35 | 72 | 25 | 35 | N (30/56/35/72/25/35) |
| 020 | RATICATE | 55 | 120 | 60 | 97 | 50 | 70 | N (55/81/60/97/50/70) |
| 021 | SPEAROW | 40 | 70 | 30 | 70 | 31 | 31 | N (40/60/30/70/31/31) |
| 022 | FEAROW | 110 | 130 | 65 | 100 | 50 | 50 | N (65/90/65/100/61/61) |
| 023 | EKANS | 45 | 60 | 44 | 55 | 40 | 54 | N (35/60/44/55/40/54) |
| 024 | ARBOK | 100 | 85 | 99 | 80 | 80 | 79 | N (60/85/69/80/65/79) |
| 025 | PIKACHU | 50 | 55 | 30 | 90 | 80 | 40 | N (35/55/30/90/50/40) |
| 026 | RAICHU | 80 | 110 | 55 | 110 | 125 | 80 | N (60/90/55/100/90/80) |
| 027 | SANDSHREW | 70 | 75 | 85 | 40 | 20 | 30 | N (50/75/85/40/20/30) |
| 028 | SANDSLASH | 105 | 110 | 130 | 65 | 45 | 55 | N (75/100/110/65/45/55) |
| 029 | NIDORAN_F | 55 | 47 | 52 | 41 | 40 | 40 | Y |
| 030 | NIDORINA | 90 | 62 | 77 | 56 | 55 | 65 | N (70/62/67/56/55/55) |
| 031 | NIDOQUEEN | 130 | 85 | 100 | 75 | 75 | 100 | N (90/82/87/76/75/85) |
| 032 | NIDORAN_M | 46 | 57 | 40 | 50 | 40 | 40 | Y |
| 033 | NIDORINO | 61 | 102 | 57 | 75 | 55 | 55 | N (61/72/57/65/55/55) |
| 034 | NIDOKING | 95 | 115 | 77 | 100 | 100 | 78 | N (81/92/77/85/85/75) |
| 035 | CLEFAIRY | 70 | 45 | 48 | 35 | 60 | 65 | Y |
| 036 | CLEFABLE | 120 | 50 | 90 | 45 | 85 | 100 | N (95/70/73/60/85/90) |
| 037 | VULPIX | 55 | 41 | 40 | 65 | 70 | 65 | N (38/41/40/65/50/65) |
| 038 | NINETALES | 80 | 76 | 75 | 100 | 100 | 100 | N (73/76/75/100/81/100) |
| 039 | JIGGLYPUFF | 115 | 45 | 20 | 20 | 45 | 25 | Y |
| 040 | WIGGLYTUFF | 160 | 100 | 55 | 45 | 75 | 80 | N (140/70/45/45/75/50) |
| 041 | ZUBAT | 40 | 45 | 35 | 55 | 30 | 40 | Y |
| 042 | GOLBAT | 80 | 80 | 80 | 90 | 65 | 75 | N (75/80/70/90/65/75) |
| 043 | ODDISH | 45 | 50 | 55 | 30 | 75 | 65 | Y |
| 044 | GLOOM | 60 | 65 | 70 | 40 | 85 | 75 | Y |
| 045 | VILEPLUME | 120 | 80 | 85 | 50 | 100 | 90 | N (75/80/85/50/100/90) |
| 046 | PARAS | 35 | 70 | 55 | 25 | 45 | 55 | Y |
| 047 | PARASECT | 90 | 130 | 80 | 30 | 80 | 80 | N (60/95/80/30/60/80) |
| 048 | VENONAT | 60 | 55 | 50 | 45 | 40 | 55 | Y |
| 049 | VENOMOTH | 70 | 65 | 60 | 100 | 100 | 75 | N (70/65/60/90/90/75) |
| 050 | DIGLETT | 10 | 70 | 25 | 95 | 35 | 45 | N (10/55/25/95/35/45) |
| 051 | DUGTRIO | 35 | 110 | 50 | 130 | 50 | 70 | N (35/80/50/120/50/70) |
| 052 | MEOWTH | 40 | 45 | 35 | 90 | 40 | 40 | Y |
| 053 | PERSIAN | 65 | 110 | 60 | 115 | 70 | 65 | N (65/70/60/115/65/65) |
| 054 | PSYDUCK | 50 | 52 | 48 | 55 | 90 | 50 | N (50/52/48/55/65/50) |
| 055 | GOLDUCK | 80 | 82 | 78 | 85 | 120 | 80 | N (80/82/78/85/95/80) |
| 056 | MANKEY | 60 | 80 | 35 | 70 | 35 | 45 | N (40/80/35/70/35/45) |
| 057 | PRIMEAPE | 100 | 120 | 120 | 95 | 60 | 40 | N (65/105/60/95/60/70) |
| 058 | GROWLITHE | 55 | 70 | 45 | 60 | 70 | 50 | Y |
| 059 | ARCANINE | 120 | 115 | 80 | 90 | 130 | 80 | N (90/110/80/95/100/80) |
| 060 | POLIWAG | 40 | 50 | 40 | 90 | 40 | 40 | Y |
| 061 | POLIWHIRL | 75 | 65 | 75 | 90 | 70 | 50 | N (65/65/65/90/50/50) |
| 062 | POLIWRATH | 120 | 85 | 110 | 70 | 70 | 90 | N (90/85/95/70/70/90) |
| 063 | ABRA | 25 | 20 | 15 | 90 | 105 | 55 | Y |
| 064 | KADABRA | 50 | 35 | 30 | 105 | 120 | 70 | N (40/35/30/105/120/70) |
| 065 | ALAKAZAM | 60 | 50 | 45 | 120 | 135 | 100 | N (55/50/45/120/135/85) |
| 066 | MACHOP | 80 | 80 | 50 | 35 | 35 | 35 | N (70/80/50/35/35/35) |
| 067 | MACHOKE | 100 | 100 | 70 | 45 | 50 | 60 | N (80/100/70/45/50/60) |
| 068 | MACHAMP | 110 | 130 | 80 | 55 | 65 | 85 | N (90/130/80/55/65/85) |
| 069 | BELLSPROUT | 50 | 75 | 35 | 40 | 70 | 30 | Y |
| 070 | WEEPINBELL | 75 | 90 | 60 | 55 | 85 | 60 | N (65/90/50/55/85/45) |
| 071 | VICTREEBEL | 95 | 120 | 65 | 70 | 120 | 60 | N (80/105/65/70/100/60) |
| 072 | TENTACOOL | 40 | 40 | 35 | 70 | 50 | 100 | Y |
| 073 | TENTACRUEL | 80 | 80 | 65 | 100 | 100 | 120 | N (80/70/65/100/80/120) |
| 074 | GEODUDE | 40 | 80 | 100 | 20 | 30 | 30 | Y |
| 075 | GRAVELER | 70 | 95 | 115 | 35 | 45 | 45 | N (55/95/115/35/45/45) |
| 076 | GOLEM | 100 | 110 | 150 | 45 | 55 | 65 | N (80/110/130/45/55/65) |
| 077 | PONYTA | 50 | 85 | 55 | 90 | 65 | 65 | Y |
| 078 | RAPIDASH | 65 | 100 | 70 | 105 | 120 | 80 | N (65/100/70/105/80/80) |
| 079 | SLOWPOKE | 90 | 65 | 65 | 15 | 40 | 40 | Y |
| 080 | SLOWBRO | 115 | 75 | 110 | 30 | 100 | 80 | N (95/75/110/30/100/80) |
| 081 | MAGNEMITE | 25 | 75 | 70 | 45 | 95 | 55 | N (25/35/70/45/95/55) |
| 082 | MAGNETON | 80 | 100 | 110 | 80 | 120 | 50 | N (50/60/95/70/120/70) |
| 083 | FARFETCH_D | 60 | 130 | 55 | 60 | 58 | 62 | N (52/65/55/60/58/62) |
| 084 | DODUO | 35 | 85 | 45 | 75 | 35 | 35 | Y |
| 085 | DODRIO | 80 | 110 | 70 | 120 | 60 | 60 | N (60/110/70/100/60/60) |
| 086 | SEEL | 65 | 45 | 55 | 45 | 45 | 70 | Y |
| 087 | DEWGONG | 120 | 70 | 95 | 80 | 95 | 105 | N (90/70/80/70/70/95) |
| 088 | GRIMER | 80 | 80 | 50 | 25 | 40 | 50 | Y |
| 089 | MUK | 120 | 105 | 120 | 50 | 65 | 100 | N (105/105/75/50/65/100) |
| 090 | SHELLDER | 30 | 65 | 100 | 40 | 45 | 25 | Y |
| 091 | CLOYSTER | 80 | 95 | 180 | 70 | 85 | 45 | N (50/95/180/70/85/45) |
| 092 | GASTLY | 30 | 35 | 30 | 80 | 100 | 35 | Y |
| 093 | HAUNTER | 45 | 70 | 45 | 95 | 115 | 55 | N (45/50/45/95/115/55) |
| 094 | GENGAR | 60 | 130 | 60 | 100 | 130 | 75 | N (60/65/60/110/130/75) |
| 095 | ONIX | 35 | 45 | 160 | 70 | 30 | 45 | Y |
| 096 | DROWZEE | 60 | 48 | 45 | 42 | 43 | 90 | Y |
| 097 | HYPNO | 85 | 73 | 120 | 67 | 73 | 115 | N (85/73/70/67/73/115) |
| 098 | KRABBY | 30 | 105 | 90 | 50 | 25 | 25 | Y |
| 099 | KINGLER | 55 | 130 | 115 | 75 | 80 | 50 | N (55/130/115/75/50/50) |
| 100 | VOLTORB | 40 | 30 | 50 | 100 | 65 | 55 | N (40/30/50/100/55/55) |
| 101 | ELECTRODE | 60 | 50 | 70 | 170 | 100 | 80 | N (60/50/70/140/80/80) |
| 102 | EXEGGCUTE | 60 | 40 | 80 | 40 | 60 | 45 | Y |
| 103 | EXEGGUTOR | 105 | 95 | 85 | 55 | 125 | 80 | N (95/95/85/55/125/65) |
| 104 | CUBONE | 50 | 50 | 95 | 35 | 40 | 50 | Y |
| 105 | MAROWAK | 100 | 120 | 110 | 45 | 50 | 80 | N (60/80/110/45/50/80) |
| 106 | HITMONLEE | 50 | 120 | 53 | 102 | 35 | 110 | N (50/120/53/87/35/110) |
| 107 | HITMONCHAN | 50 | 80 | 79 | 75 | 120 | 110 | N (50/105/79/76/35/110) |
| 108 | LICKITUNG | 125 | 55 | 80 | 30 | 60 | 105 | N (90/55/75/30/60/75) |
| 109 | KOFFING | 40 | 65 | 95 | 35 | 60 | 45 | Y |
| 110 | WEEZING | 110 | 90 | 120 | 60 | 85 | 70 | N (65/90/120/60/85/70) |
| 111 | RHYHORN | 100 | 85 | 95 | 25 | 30 | 30 | N (80/85/95/25/30/30) |
| 112 | RHYDON | 130 | 130 | 120 | 40 | 45 | 45 | N (105/130/120/40/45/45) |
| 113 | CHANSEY | 250 | 5 | 5 | 50 | 105 | 105 | N (250/5/5/50/35/105) |
| 114 | TANGELA | 130 | 55 | 115 | 60 | 100 | 60 | N (65/55/115/60/100/40) |
| 115 | KANGASKHAN | 105 | 125 | 80 | 90 | 40 | 80 | N (105/95/80/90/40/80) |
| 116 | HORSEA | 50 | 40 | 70 | 60 | 70 | 25 | N (30/40/70/60/70/25) |
| 117 | SEADRA | 70 | 65 | 95 | 85 | 95 | 45 | N (55/65/95/85/95/45) |
| 118 | GOLDEEN | 45 | 67 | 60 | 63 | 35 | 50 | Y |
| 119 | SEAKING | 80 | 92 | 65 | 68 | 80 | 80 | N (80/92/65/68/65/80) |
| 120 | STARYU | 30 | 45 | 55 | 85 | 70 | 55 | Y |
| 121 | STARMIE | 60 | 75 | 85 | 115 | 110 | 85 | N (60/75/85/115/100/85) |
| 122 | MR__MIME | 40 | 45 | 65 | 90 | 100 | 180 | N (40/45/65/90/100/120) |
| 123 | SCYTHER | 80 | 110 | 80 | 105 | 55 | 80 | N (70/110/80/105/55/80) |
| 124 | JYNX | 75 | 50 | 55 | 115 | 135 | 95 | N (65/50/35/95/115/95) |
| 125 | ELECTABUZZ | 65 | 105 | 57 | 105 | 95 | 85 | N (65/83/57/105/95/85) |
| 126 | MAGMAR | 65 | 95 | 57 | 82 | 125 | 85 | N (65/95/57/93/100/85) |
| 127 | PINSIR | 80 | 140 | 100 | 85 | 55 | 70 | N (65/125/100/85/55/70) |
| 128 | TAUROS | 75 | 120 | 95 | 110 | 40 | 70 | N (75/100/95/110/40/70) |
| 129 | MAGIKARP | 20 | 10 | 55 | 80 | 15 | 20 | Y |
| 130 | GYARADOS | 100 | 125 | 79 | 81 | 90 | 100 | N (95/125/79/81/60/100) |
| 131 | LAPRAS | 130 | 85 | 110 | 60 | 85 | 110 | N (130/85/80/60/85/95) |
| 132 | DITTO | 100 | 48 | 48 | 48 | 48 | 48 | N (48/48/48/48/48/48) |
| 133 | EEVEE | 55 | 55 | 50 | 55 | 45 | 65 | Y |
| 134 | VAPOREON | 130 | 65 | 60 | 65 | 110 | 110 | N (130/65/60/65/110/95) |
| 135 | JOLTEON | 65 | 65 | 60 | 145 | 110 | 95 | N (65/65/60/130/110/95) |
| 136 | FLAREON | 65 | 145 | 60 | 65 | 95 | 110 | N (65/130/60/65/95/110) |
| 137 | PORYGON | 65 | 60 | 70 | 40 | 85 | 75 | Y |
| 138 | OMANYTE | 35 | 40 | 100 | 35 | 90 | 55 | Y |
| 139 | OMASTAR | 80 | 80 | 125 | 55 | 115 | 70 | N (70/60/125/55/115/70) |
| 140 | KABUTO | 30 | 80 | 90 | 55 | 55 | 45 | Y |
| 141 | KABUTOPS | 60 | 125 | 115 | 90 | 65 | 70 | N (60/115/105/80/65/70) |
| 142 | AERODACTYL | 100 | 105 | 80 | 130 | 60 | 75 | N (80/105/65/130/60/75) |
| 143 | SNORLAX | 160 | 110 | 65 | 30 | 65 | 110 | Y |
| 144 | ARTICUNO | 100 | 95 | 100 | 85 | 105 | 125 | N (90/85/100/85/95/125) |
| 145 | ZAPDOS | 100 | 100 | 85 | 100 | 135 | 90 | N (90/90/85/100/125/90) |
| 146 | MOLTRES | 100 | 110 | 90 | 90 | 135 | 85 | N (90/100/90/90/125/85) |
| 147 | DRATINI | 41 | 64 | 45 | 50 | 50 | 50 | Y |
| 148 | DRAGONAIR | 90 | 84 | 65 | 70 | 110 | 70 | N (61/84/65/70/70/70) |
| 149 | DRAGONITE | 121 | 134 | 95 | 20 | 130 | 100 | N (91/134/95/80/100/100) |
| 150 | MEWTWO | 106 | 110 | 90 | 130 | 154 | 90 | Y |
| 151 | MEW | 100 | 100 | 100 | 100 | 100 | 100 | Y |
| 152 | CHIKORITA | 55 | 49 | 65 | 45 | 49 | 65 | N (45/49/65/45/49/65) |
| 153 | BAYLEEF | 70 | 72 | 80 | 60 | 73 | 80 | N (60/62/80/60/63/80) |
| 154 | MEGANIUM | 110 | 82 | 100 | 80 | 83 | 100 | N (80/82/100/80/83/100) |
| 155 | CYNDAQUIL | 45 | 52 | 43 | 65 | 60 | 50 | N (39/52/43/65/60/50) |
| 156 | QUILAVA | 68 | 74 | 58 | 80 | 90 | 65 | N (58/64/58/80/80/65) |
| 157 | TYPHLOSION | 78 | 84 | 78 | 100 | 130 | 85 | N (78/84/78/100/109/85) |
| 158 | TOTODILE | 50 | 65 | 64 | 43 | 44 | 48 | Y |
| 159 | CROCONAW | 75 | 90 | 90 | 58 | 59 | 63 | N (65/80/80/58/59/63) |
| 160 | FERALIGATR | 85 | 105 | 100 | 87 | 95 | 83 | N (85/105/100/78/79/83) |
| 161 | SENTRET | 35 | 60 | 34 | 20 | 35 | 45 | N (35/46/34/20/35/45) |
| 162 | FURRET | 85 | 100 | 64 | 90 | 100 | 55 | N (85/76/64/90/45/55) |
| 163 | HOOTHOOT | 60 | 50 | 30 | 50 | 36 | 56 | N (60/30/30/50/36/56) |
| 164 | NOCTOWL | 100 | 50 | 50 | 70 | 110 | 120 | N (100/50/50/70/76/96) |
| 165 | LEDYBA | 40 | 40 | 30 | 55 | 40 | 80 | N (40/20/30/55/40/80) |
| 166 | LEDIAN | 90 | 115 | 65 | 105 | 45 | 120 | N (55/35/50/85/55/110) |
| 167 | SPINARAK | 40 | 60 | 40 | 30 | 40 | 40 | Y |
| 168 | ARIADOS | 110 | 90 | 100 | 40 | 60 | 60 | N (70/90/70/40/60/60) |
| 169 | CROBAT | 100 | 90 | 80 | 130 | 70 | 80 | N (85/90/80/130/70/80) |
| 170 | CHINCHOU | 75 | 38 | 38 | 67 | 56 | 56 | Y |
| 171 | LANTURN | 125 | 58 | 76 | 75 | 105 | 105 | N (125/58/58/67/76/76) |
| 172 | PICHU | 20 | 40 | 15 | 60 | 35 | 35 | Y |
| 173 | CLEFFA | 50 | 25 | 28 | 15 | 45 | 55 | Y |
| 174 | IGGLYBUFF | 90 | 30 | 15 | 15 | 40 | 20 | Y |
| 175 | TOGEPI | 35 | 20 | 65 | 20 | 40 | 65 | Y |
| 176 | TOGETIC | 55 | 40 | 85 | 40 | 140 | 105 | N (55/40/85/40/80/105) |
| 177 | NATU | 40 | 50 | 45 | 70 | 70 | 45 | Y |
| 178 | XATU | 90 | 75 | 70 | 150 | 95 | 70 | N (65/75/70/95/95/70) |
| 179 | MAREEP | 55 | 40 | 40 | 35 | 65 | 45 | Y |
| 180 | FLAAFFY | 70 | 55 | 55 | 45 | 80 | 60 | Y |
| 181 | AMPHAROS | 112 | 75 | 75 | 55 | 115 | 90 | N (90/75/75/55/115/90) |
| 182 | BELLOSSOM | 85 | 80 | 85 | 60 | 90 | 100 | N (75/80/85/50/90/100) |
| 183 | MARILL | 70 | 60 | 50 | 40 | 20 | 50 | N (70/20/50/40/20/50) |
| 184 | AZUMARILL | 100 | 150 | 80 | 50 | 50 | 80 | N (100/50/80/50/50/80) |
| 185 | SUDOWOODO | 90 | 125 | 145 | 45 | 30 | 75 | N (70/100/115/30/30/65) |
| 186 | POLITOED | 100 | 70 | 80 | 85 | 115 | 105 | N (90/75/75/70/90/100) |
| 187 | HOPPIP | 35 | 35 | 40 | 50 | 35 | 55 | Y |
| 188 | SKIPLOOM | 55 | 45 | 50 | 80 | 45 | 65 | Y |
| 189 | JUMPLUFF | 110 | 55 | 70 | 135 | 55 | 85 | N (75/55/70/110/55/85) |
| 190 | AIPOM | 90 | 100 | 55 | 110 | 40 | 55 | N (55/70/55/85/40/55) |
| 191 | SUNKERN | 30 | 30 | 30 | 30 | 30 | 30 | Y |
| 192 | SUNFLORA | 75 | 75 | 55 | 30 | 150 | 85 | N (75/75/55/30/105/85) |
| 193 | YANMA | 85 | 110 | 60 | 95 | 50 | 80 | N (65/65/45/95/75/45) |
| 194 | WOOPER | 55 | 45 | 45 | 15 | 25 | 25 | Y |
| 195 | QUAGSIRE | 120 | 100 | 85 | 35 | 70 | 65 | N (95/85/85/35/65/65) |
| 196 | ESPEON | 65 | 65 | 60 | 125 | 140 | 95 | N (65/65/60/110/130/95) |
| 197 | UMBREON | 120 | 65 | 110 | 65 | 60 | 130 | N (95/65/110/65/60/130) |
| 198 | MURKROW | 110 | 100 | 80 | 91 | 100 | 80 | N (60/85/42/91/85/42) |
| 199 | SLOWKING | 95 | 75 | 80 | 30 | 120 | 110 | N (95/75/80/30/100/110) |
| 200 | MISDREAVUS | 80 | 120 | 80 | 85 | 70 | 85 | N (60/60/60/85/85/85) |
| 201 | UNOWN | 148 | 102 | 48 | 48 | 102 | 48 | N (48/72/48/48/72/48) |
| 202 | WOBBUFFET | 220 | 33 | 65 | 33 | 33 | 65 | N (190/33/58/33/33/58) |
| 203 | GIRAFARIG | 70 | 80 | 65 | 112 | 90 | 65 | N (70/80/65/85/90/65) |
| 204 | PINECO | 80 | 65 | 90 | 15 | 35 | 35 | N (50/65/90/15/35/35) |
| 205 | FORRETRESS | 90 | 90 | 140 | 40 | 60 | 80 | N (75/90/140/40/60/60) |
| 206 | DUNSPARCE | 120 | 120 | 120 | 20 | 20 | 20 | N (100/70/70/45/65/65) |
| 207 | GLIGAR | 85 | 95 | 125 | 85 | 35 | 65 | N (65/75/105/85/35/65) |
| 208 | STEELIX | 100 | 100 | 200 | 30 | 55 | 40 | N (75/85/200/30/55/65) |
| 209 | SNUBBULL | 60 | 80 | 50 | 30 | 40 | 40 | Y |
| 210 | GRANBULL | 90 | 120 | 120 | 45 | 60 | 60 | N (90/120/75/45/60/60) |
| 211 | QWILFISH | 85 | 105 | 130 | 95 | 65 | 65 | N (65/95/75/85/55/55) |
| 212 | SCIZOR | 70 | 130 | 120 | 65 | 55 | 80 | N (70/130/100/65/55/80) |
| 213 | SHUCKLE | 60 | 10 | 230 | 5 | 10 | 230 | N (20/10/230/5/10/230) |
| 214 | HERACROSS | 80 | 125 | 75 | 105 | 40 | 95 | N (80/125/75/85/40/95) |
| 215 | SNEASEL | 95 | 115 | 55 | 120 | 75 | 75 | N (55/95/55/115/35/75) |
| 216 | TEDDIURSA | 80 | 80 | 50 | 40 | 50 | 50 | N (60/80/50/40/50/50) |
| 217 | URSARING | 120 | 145 | 75 | 55 | 75 | 75 | N (90/130/75/55/75/75) |
| 218 | SLUGMA | 40 | 40 | 40 | 20 | 90 | 40 | N (40/40/40/20/70/40) |
| 219 | MAGCARGO | 80 | 80 | 120 | 30 | 100 | 80 | N (50/50/120/30/80/80) |
| 220 | SWINUB | 50 | 50 | 40 | 50 | 30 | 30 | Y |
| 221 | PILOSWINE | 140 | 100 | 120 | 50 | 60 | 90 | N (100/100/80/50/60/60) |
| 222 | CORSOLA | 95 | 80 | 130 | 45 | 75 | 130 | N (55/55/85/35/65/85) |
| 223 | REMORAID | 35 | 65 | 35 | 65 | 65 | 35 | Y |
| 224 | OCTILLERY | 75 | 105 | 75 | 80 | 105 | 75 | N (75/105/75/45/105/75) |
| 225 | DELIBIRD | 100 | 55 | 45 | 75 | 65 | 150 | N (45/55/45/75/65/45) |
| 226 | MANTINE | 95 | 40 | 85 | 90 | 105 | 140 | N (65/40/70/70/80/140) |
| 227 | SKARMORY | 75 | 80 | 140 | 70 | 40 | 70 | N (65/80/140/70/40/70) |
| 228 | HOUNDOUR | 45 | 60 | 30 | 65 | 80 | 50 | Y |
| 229 | HOUNDOOM | 75 | 90 | 50 | 115 | 130 | 80 | N (75/90/50/95/110/80) |
| 230 | KINGDRA | 95 | 95 | 95 | 85 | 95 | 95 | N (75/95/95/85/95/95) |
| 231 | PHANPY | 90 | 60 | 60 | 40 | 40 | 40 | Y |
| 232 | DONPHAN | 110 | 120 | 120 | 50 | 60 | 60 | N (90/120/120/50/60/60) |
| 233 | PORYGON2 | 115 | 80 | 100 | 60 | 105 | 105 | N (85/80/90/60/105/95) |
| 234 | STANTLER | 73 | 115 | 62 | 85 | 85 | 65 | N (73/95/62/85/85/65) |
| 235 | SMEARGLE | 90 | 45 | 75 | 110 | 45 | 75 | N (55/20/35/75/20/45) |
| 236 | TYROGUE | 35 | 35 | 35 | 35 | 35 | 35 | Y |
| 237 | HITMONTOP | 110 | 85 | 95 | 70 | 35 | 110 | N (50/95/95/70/35/110) |
| 238 | SMOOCHUM | 45 | 30 | 15 | 65 | 85 | 65 | Y |
| 239 | ELEKID | 45 | 63 | 37 | 95 | 65 | 55 | Y |
| 240 | MAGBY | 45 | 75 | 37 | 83 | 70 | 55 | Y |
| 241 | MILTANK | 105 | 80 | 105 | 100 | 40 | 70 | N (95/80/105/100/40/70) |
| 242 | BLISSEY | 255 | 10 | 10 | 55 | 135 | 135 | N (255/10/10/55/75/135) |
| 243 | RAIKOU | 90 | 85 | 75 | 115 | 135 | 100 | N (90/85/75/115/115/100) |
| 244 | ENTEI | 115 | 135 | 85 | 100 | 90 | 75 | N (115/115/85/100/90/75) |
| 245 | SUICUNE | 120 | 75 | 115 | 85 | 90 | 115 | N (100/75/115/85/90/115) |
| 246 | LARVITAR | 50 | 64 | 50 | 41 | 45 | 50 | Y |
| 247 | PUPITAR | 70 | 84 | 70 | 51 | 65 | 70 | Y |
| 248 | TYRANITAR | 100 | 134 | 110 | 61 | 95 | 140 | N (100/134/110/61/95/100) |
| 249 | LUGIA | 116 | 100 | 140 | 120 | 100 | 164 | N (106/90/130/110/90/154) |
| 250 | HO_OH | 116 | 140 | 100 | 100 | 120 | 164 | N (106/130/90/90/110/154) |
| 251 | CELEBI | 100 | 100 | 100 | 100 | 100 | 100 | Y |
