# Trainer And Boss Roster Micro-Index

Use this when a task mentions a gym leader, Rival, Elite Four member, Champion,
Red, Kanto leader, trainer party, boss item, or AI tier.

This is a routing matrix. For exact current teams, items, levels, moves, and
trainer type, inspect `data/trainers/parties.asm`.

## Core Source Surfaces

| Need | Go to |
| --- | --- |
| Boss AI tier membership | `data/trainers/ai_tiers.asm` |
| Trainer parties, items, moves | `data/trainers/parties.asm` |
| Trainer attributes and base AI flags | `data/trainers/attributes.asm` |
| Party pointer order | `data/trainers/party_pointers.asm` |
| Trainer constants and IDs | `constants/trainer_constants.asm`, `constants/trainer_data_constants.asm` |
| Boss AI implementation | `engine/battle/ai/boss.asm` |
| Boss AI activation | `engine/battle/read_trainer_attributes.asm`, `engine/battle/start_battle.asm` |

## Boss AI Tier Map

| Surface | Trainer class/id | Current tier | Party label |
| --- | --- | --- | --- |
| Falkner | `FALKNER, FALKNER1` | `AI_TIER_EARLY` | `FalknerGroup` |
| Bugsy | `BUGSY, BUGSY1` | `AI_TIER_EARLY` | `BugsyGroup` |
| Whitney | `WHITNEY, WHITNEY1` | `AI_TIER_EARLY` | `WhitneyGroup` |
| Morty | `MORTY, MORTY1` | `AI_TIER_MID` | `MortyGroup` |
| Chuck | `CHUCK, CHUCK1` | `AI_TIER_MID` | `ChuckGroup` |
| Jasmine | `JASMINE, JASMINE1` | `AI_TIER_MID` | `JasmineGroup` |
| Pryce | `PRYCE, PRYCE1` | `AI_TIER_LATE` | `PryceGroup` |
| Clair | `CLAIR, CLAIR1` | `AI_TIER_LATE` | `ClairGroup` |
| Rival early/mid/late milestones | `RIVAL1`, `RIVAL2` variants | mixed early/mid/late | `Rival1Group`, `Rival2Group` |
| Will | `WILL, WILL1` | `AI_TIER_LATE` | `WillGroup` |
| Bruno | `BRUNO, BRUNO1` | `AI_TIER_LATE` | `BrunoGroup` |
| Koga | `KOGA, KOGA1` | `AI_TIER_LATE` | `KogaGroup` |
| Karen | `KAREN, KAREN1` | `AI_TIER_LATE` | `KarenGroup` |
| Champion Lance | `CHAMPION, LANCE` | `AI_TIER_LATE` | `ChampionGroup` |
| Brock | `BROCK, BROCK1` | `AI_TIER_LATE` | `BrockGroup` |
| Misty | `MISTY, MISTY1` | `AI_TIER_LATE` | `MistyGroup` |
| Lt. Surge | `LT_SURGE, LT_SURGE1` | `AI_TIER_LATE` | `LtSurgeGroup` |
| Erika | `ERIKA, ERIKA1` | `AI_TIER_LATE` | `ErikaGroup` |
| Janine | `JANINE, JANINE1` | `AI_TIER_LATE` | `JanineGroup` |
| Sabrina | `SABRINA, SABRINA1` | `AI_TIER_LATE` | `SabrinaGroup` |
| Blaine | `BLAINE, BLAINE1` | `AI_TIER_LATE` | `BlaineGroup` |
| Blue | `BLUE, BLUE1` | `AI_TIER_LATE` | `BlueGroup` |
| Red | `RED, RED1` | `AI_TIER_LATE` | `RedGroup` |

## Trace Priority Overlay

Live trace priority currently focuses on:

| Boss/scenario | Ledger output |
| --- | --- |
| Morty | `audit/boss_ai_trace/morty_live.txt` |
| Jasmine | `audit/boss_ai_trace/jasmine_live.txt` |
| Clair | `audit/boss_ai_trace/clair_live.txt` |
| Koga | `audit/boss_ai_trace/koga_live.txt` |
| Champion Lance | `audit/boss_ai_trace/champion_lance_live.txt` |
| Shared switch-loop | `audit/boss_ai_trace/shared_switch_loop_live.txt` |

Use `docs/agent_navigation/subsystems/boss_ai_trace.md` before claiming live
proof for any row.

## Review Shortcuts

```powershell
rg -n "^(MortyGroup|JasmineGroup|ClairGroup|KogaGroup|ChampionGroup|RedGroup):" data\trainers\parties.asm
rg -n "\b(MORTY|JASMINE|CLAIR|KOGA|CHAMPION|RED)\b" data\trainers\ai_tiers.asm data\trainers\attributes.asm constants
```

## Verification

Use `docs/agent_navigation/verification_matrix.md` row
`Trainer parties, boss held items, AI tiers`. Then build both ROMs for source
changes. Keep trainer-party legality separate from species learnset legality
unless the user explicitly asks to change both.
