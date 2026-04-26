# Boss AI Post-Patch Notes

Date: 2026-04-26
Scope: boss AI release-safety patch and trace/tuning follow-up

## Implemented Patch Summary

The release-safety patch was implemented in `engine/battle/ai/boss.asm` with no
new boss WRAM fields, SRAM fields, HRAM fields, or Battle Core bank `0f` hooks.

Implemented behavior:

- Revealed player move knowledge is no longer one global exact-move bitmap.
  `wBossAIRevealedMovesBitmap` is reused as six 4-byte per-seen-species
  revealed type masks, with 8 spare bytes left in that existing 32-byte block.
- Switch loop prevention now checks the proposed switch target against the last
  mon switched out, so immediate A->B->A reversals can be penalized unless an
  emergency exception applies.
- Boss move scoring now hard-discourages visible status failures: already
  statused target, Safeguard, Poison/Toxic into Poison or Steel, paralysis into
  real type-chart immunities such as Thunder Wave into Ground or Glare into
  Ghost, and Leech Seed into Grass.
- First-layer Spikes treats `wBossAITurnsElapsed <= 1` as the first scoring
  turn after `BossAI_IncrementTurnsElapsed`, and avoids high hazard greed under
  immediate public pressure.
- Late-tier class role bias is restored, so late bosses keep identity bonuses
  and Lance-style non-KO Hyper Beam discouragement.
- Phase 2 heuristics were added without a simulator: Spikes plus phazing bias,
  +2 setup punishment via denial moves, and a small immunity-pivot tie-break.

Important anchors:

- `BossAI_RecordRevealedPlayerMove`
- `BossAI_GetActiveSpeciesRevealedMaskPointer`
- `BossAI_HasRevealedSuperEffectiveMove`
- `BossAI_AddRevealedDamagingTypesToMask`
- `.StatusMoveWouldFailPublicly`
- `.ApplySetupPunishBias`
- `.ApplyPhazingPlanBias`
- `.spikes_layer1`
- `.ApplyLegacyRoleBiasIfNeeded`
- `BossAI_NeedsLoopPenalty`
- `.ApplyPrimaryThreatImmunityTieBreak`

## Memory And Bank Facts

Current generated facts are in `docs/generated/dev_index.md`.

Current post-patch memory summary:

- Boss WRAM reserve: normal build still uses 75 bytes and leaves 65 reserved
  bytes.
- Boss WRAM reserve with `BOSS_AI_TRACE`: still uses 94 bytes and leaves 46
  reserved bytes.
- `wBossAIStateEnd` remains before `wEventFlags`.
- `Battle Core` remains in bank `0f`: normal range is `0f:4000-7b9a`; trace
  range is `0f:4000-7fca`.
- Boss AI logic lives in the Enemy Trainers section, bank `0e`: normal range is
  `0e:4000-722b`; trace range is `0e:4000-7318`.
- Plausible player move inference now uses a possible mask plus
  `wBossAILikelyTypeMaskCache`; the likely mask reuses old spare bytes from the
  revealed-move reserve and does not grow the Boss AI WRAM block.

Do not add persistent chaos or overprediction state to the boss AI block:
`ClearBossAIState` clears it at trainer load.

## Verification Already Performed

`make` was unavailable in the local PowerShell environment, so the ROMs were
built with the bundled RGBDS tools.

Built successfully:

- `pokegold.gbc`
- `pokesilver.gbc`
- `pokegold_trace.gbc`

Audits passed:

```powershell
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
git diff --check -- engine/battle/ai/boss.asm ram/wram.asm docs/generated/dev_index.md
```

## Manual Build Fallback

Prefer the Makefile when `make` is available:

```powershell
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc
make -j4 RGBDS=rgbds-1.0.1/ pokesilver.gbc
make -j4 RGBDS=rgbds-1.0.1/ pokegold.gbc DEFINES="-D BOSS_AI_TRACE"
```

If `make` is unavailable but the existing non-boss object files are current,
reassemble the touched objects and relink:

```powershell
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -o main_gold.o main.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _SILVER -o main_silver.o main.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -o ram_gold.o ram.asm
.\rgbds-1.0.1\rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _SILVER -o ram_silver.o ram.asm
```

Relink Gold/Silver using the same object lists from `Makefile`, then run
`rgbfix` and `tools\stadium.exe`. If trace output is needed without overwriting
normal Gold objects, assemble `main_gold_trace.o` and `ram_gold_trace.o` with
`-D BOSS_AI_TRACE` and link them into `pokegold_trace.gbc`.

After any successful relink that changes addresses, regenerate:

```powershell
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
```

## Trace Priorities

Primary trace bosses:

- Morty
- Jasmine
- Clair
- Koga
- Lance

Required behavior checks:

- Alakazam reveals Ice Punch, then another player species enters; the revealed
  Ice threat must not transfer globally.
- Boss switches A->B, then considers B->A; loop penalty should apply unless
  imminent KO prevention, immunity pivot, or ace timing applies.
- Spikes lead on the actual first scoring turn; hazard bias should be high only
  when public pressure is not immediate.
- Toxic, Thunder Wave, Confuse Ray, sleep, and Leech Seed should be heavily
  discouraged into visible fail states. Thunder Wave/Glare paralysis gating
  follows actual type-chart immunity, not a blanket Electric-target immunity,
  and player Substitute, existing confusion, or existing Leech Seed are treated
  as public fail states.
- Already-active Reflect/Light Screen, impossible Substitute, and Protect while
  already behind a Substitute should also be heavily discouraged by the boss
  model, as should healing moves at full HP.
- Late-tier Lance should keep role identity and avoid non-KO Hyper Beam.
- Spikes plus Roar/Whirlwind should gain value after repeated player switching
  or public setup pressure.
- Public +2 Attack, Special Attack, Speed, or Evasion should make Haze, Roar,
  Whirlwind, or Encore more attractive when no immediate KO line exists.
- A public/revealed threat type should make a true immunity pivot slightly
  preferable to a merely neutral pivot.
- Current enemy move pressure should discount non-super-effective hits into
  visible Dragon defenders because Imperial Scales lowers that damage in the
  actual battle engine.

Store excerpts under `audit/boss_ai_trace/`.
