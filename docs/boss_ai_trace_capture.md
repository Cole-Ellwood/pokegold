# Boss AI Trace Capture

## Canonical Trace Build Command

Use this command for Boss AI trace builds:

```bash
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc DEFINES="-D BOSS_AI_TRACE"
```

Build interface note:
- `Makefile` now appends `DEFINES` to `RGBASMFLAGS`, so the command above is the canonical trace entrypoint.

## Where Trace Output Appears (Actual Behavior)

`BOSS_AI_TRACE` does not print to stdout, file logs, serial, or in-game text.
It writes trace fields into WRAM symbols only:
- `wBossAITraceTopMoves`
- `wBossAITraceTopScores`
- `wBossAITraceChosenMove`
- `wBossAITraceSwitchConfidence`
- `wBossAITracePlanId`
- `wBossAITracePlanPhase`
- `wBossAITracePlanConfidence`
- `wBossAITracePlausibleMask`
- `wBossAITraceRiskFlags`
- `wBossAITraceLookaheadBonusTop`

`wBossAITraceRiskFlags` bit meanings:
- bit 0: plausible-risk / scout trigger logic fired
- bit 1: scout move was chosen (Protect/Substitute branch)
- bit 2: scout pivot switch branch fired

Practical capture method:
- run a trace ROM in an emulator with memory/debugger access;
- read these WRAM symbols at decision points;
- export/save the observed values as text excerpts.

## Boss Capture Checklist

Capture at least one full battle trace for each target:
- Falkner
- Whitney
- Morty
- Elite Four (at minimum one member; preferred all four)
- Champion (Lance)

## Trace Excerpt Storage

Save excerpts under:
- `audit/boss_ai_trace/<boss>.txt`

Recommended filenames:
- `audit/boss_ai_trace/falkner.txt`
- `audit/boss_ai_trace/whitney.txt`
- `audit/boss_ai_trace/morty.txt`
- `audit/boss_ai_trace/e4_will.txt` (or per-member variants)
- `audit/boss_ai_trace/champion_lance.txt`
