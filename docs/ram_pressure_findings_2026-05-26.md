# RAM Pressure Findings - 2026-05-26

Read-only investigation of RAM pressure in the current working tree. No source,
asset, project configuration, or build-output changes were made for this pass.

## Scope and Limits

- Source truth: current working tree under `C:\Users\lolno\Downloads\pokemon gold hack`.
- Linker truth: existing `pokegold.map` / `pokegold.sym` and related generated
  docs only. I did not rebuild because a forced rebuild would rewrite build
  outputs, which this task explicitly forbids.
- Staleness note: the normal map and `docs/generated/dev_index.md` agree on the
  current normal Boss AI reserve (`112` used, `28` free). The existing trace map
  appears stale relative to current source: `pokegold_trace.map` reports
  `138` trace bytes used / `2` reserved free, while current `ram/wram.asm`
  source and generated docs expect `140` / `0` after the lookahead-running-best
  and 4-wide lookahead trace changes.

## Current Pressure

| Region | Evidence | Current pressure |
| --- | --- | --- |
| HRAM | `docs/generated/dev_index.md`; `ram/hram.asm` | 127 used / 0 free, but the tail has a 20-byte unnamed pad. |
| WRAM0 | `docs/generated/dev_index.md` | 4049 used / 47 free. Tactical relief exists, but the big UNION floors limit simple savings. |
| WRAMX bank 1 | `tools/audit/check_wramx_bank1_relief.py` normal path | 3685 used / 411 free. Boss AI reserve uses 112 live bytes and leaves 28 normal-build reserved bytes. |
| Boss AI trace reserve | current source + stale trace map caveat | Source shape is full at 140 / 0 under `BOSS_AI_TRACE`; trace build should be treated as no-headroom until rebuilt. |
| WRAMX bank 2+ | `ram/wram.asm`; `check_wramx_bank2_declaration.py` | Bank 2 has a 26-byte Boss AI observation buffer and otherwise lots of room; banks 3-7 are good cold-data hosts. |

## Candidate Findings

### 1. Drop the unnamed HRAM tail pad

- Files / symbols: `ram/hram.asm:160` (`ds 20` after `hDebugRoomMenuPage` / debug placeholder).
- Estimated bytes saved: 20 HRAM bytes reported as free by the linker.
- Behavior impact: none expected; all named HRAM labels stay at the same addresses because the pad is at the end of the section.
- Risk level: low. Keep the VC assertion on `hSerialConnectionStatus == $ffcd`; this change does not move it.
- Recommendation: do this first if HRAM free space matters. It is the cleanest HRAM relief I found.

### 2. Remove `wUnusedMapBuffer`

- Files / symbols: `ram/wram.asm:399` `wUnusedMapBuffer:: ds 24`.
- Estimated bytes saved: 24 WRAM0 bytes.
- Behavior impact: none expected; the declaration comment says the prototype-era map buffer is retained only for layout, and no runtime readers/writers were found in `engine/`, `home/`, or `data/`.
- Risk level: low. This is WRAM0, not the save-copied WRAMX player-data ranges.
- Recommendation: recommended tactical WRAM0 cut.

### 3. Remove `wSafariMonAngerCount`

- Files / symbols: `ram/wram.asm:830` `wSafariMonAngerCount:: db ; unreferenced`.
- Estimated bytes saved: 1 WRAM0 byte.
- Behavior impact: none expected from current source; the neighboring Safari state is still present, but this byte is unreferenced.
- Risk level: low.
- Recommendation: include with any WRAM0 cleanup patch. The byte is tiny but safe.

### 4. Overlay `wMovementBuffer` with `wBattleScriptBuffer`

- Files / symbols: `ram/wram.asm:759` `wBattleScriptBuffer:: ds 40`; `ram/wram.asm:1389` `wMovementBuffer:: ds 55`; users in `engine/battle/effect_commands.asm`, `engine/battle/late_gen_held_items.asm`, `home/movement.asm`, and `engine/events/trainer_scripts.asm`.
- Estimated bytes saved: 40 WRAM0 bytes if `wBattleScriptBuffer` is UNIONed into the movement-buffer slot.
- Behavior impact: no intended player-visible change. Battle scripts and overworld movement scripts should be mutually exclusive at runtime.
- Risk level: medium-low. Needs a battle-entry / battle-exit audit and tests for scripted trainer encounters because movement scripts can be adjacent to battle startup.
- Recommendation: good second-tier candidate after the obvious removals.

### 5. Overlay `wMovementBuffer` with the `wLYOverrides` family

- Files / symbols: `ram/wram.asm:558` `wLYOverrides:: ds SCREEN_HEIGHT_PX`; `ram/wram.asm:570` `wLYOverridesBackup:: ds SCREEN_HEIGHT_PX`; `ram/wram.asm:1389` `wMovementBuffer:: ds 55`; users in `home/lcd.asm`, `home/vblank.asm`, `home/battle.asm`, `engine/battle_anims/*`, `engine/battle/battle_transition.asm`, `engine/movie/*`, `engine/events/magnet_train.asm`, and movement-script code.
- Estimated bytes saved: 55 WRAM0 bytes if `wMovementBuffer` overlays the first 55 bytes of an LY override slot.
- Behavior impact: none intended, but the grep shows LY override use outside ordinary battles too: intro, title, credits, magnet train, and menus. That makes the mutual-exclusion proof wider than "battle vs overworld."
- Risk level: medium-high until timing is proven. LCD STAT / vblank state must not keep reading the LY buffer after a cutscene or transition while a movement script reuses the bytes.
- Recommendation: promising but not first. Require a dedicated timing audit plus emulator smoke: enter/exit battle, magnet train, credits/title transitions, then movement-script triggers.

### 6. Move `wRadioText` to a cold WRAMX bank

- Files / symbols: `ram/wram.asm:1376` `wRadioText:: ds 2 * SCREEN_WIDTH` (40 bytes); users in `engine/pokegear/radio.asm` and `home/battle.asm`.
- Estimated bytes saved: 40 WRAM0 bytes, relocated to WRAMX bank 3 or later.
- Behavior impact: none if all radio text access is wrapped correctly. Radio rendering gets a small bank-switch cost.
- Risk level: medium-low. The field is cold and UI-scoped, but every direct `ld hl/de, wRadioText` site needs a wrapper or copy window.
- Recommendation: recommended if you are willing to add a small banked-access pattern for cold UI buffers.

### 7. Move `wSGBPals` to a cold WRAMX bank

- Files / symbols: `ram/wram.asm:1003` `wSGBPals:: ds 48`; heavy use in `engine/gfx/sgb_layouts.asm`, `engine/gfx/color.asm`, `engine/pokemon/party_menu.asm`, and debug color picker code.
- Estimated bytes saved: 48 WRAM0 bytes, relocated to WRAMX bank 3 or later.
- Behavior impact: no intended visible change on SGB/CGB if wrapped correctly. SGB palette paths get bank-switch overhead.
- Risk level: medium. The symbol is cold-ish but has many direct users and this ROM is still SGB-compatible.
- Recommendation: viable but less clean than `wRadioText`; do only with an SGB palette smoke test.

### 8. Spill or overlay `wStringBuffer5`

- Files / symbols: `ram/wram.asm:1646` `wStringBuffer5:: ds MOVE_NAME_LENGTH`; `constants/text_constants.asm:6` gives `MOVE_NAME_LENGTH = 13`; users include `data/text_buffers.asm`, `home/text.asm`, phone text, and move reminder comments.
- Estimated bytes saved: 13 WRAM0 bytes.
- Behavior impact: possible text-buffer corruption if any multi-buffer text path expects direct WRAM0 access while another subsystem is active.
- Risk level: medium-high for only 13 bytes.
- Recommendation: do not prioritize. Keep it unless a broader text-buffer audit already touches this area.

### 9. Remove or quarantine `wDebugOriginalColors` / `DebugColorPicker`

- Files / symbols: `ram/wram.asm:444` `wDebugOriginalColors:: ds 256 * 4`; `engine/debug/color_picker.asm`.
- Estimated bytes saved: 1024 gross bytes, 0 effective WRAM0 bytes today because this sits in the 1300-byte "Overworld Map" UNION whose floor is still set by `wOverworldMapBlocks` and `wLinkData`.
- Behavior impact: no retail gameplay impact if the debug color picker is truly uncalled.
- Risk level: low for behavior, zero for immediate RAM relief.
- Recommendation: hygiene-only. It is worth removing dead debug code eventually, but do not count it toward RAM-pressure relief unless the 1300-byte UNION floor is also reduced.

### 10. Shrink or redesign `wOverworldMapBlocks`

- Files / symbols: `ram/wram.asm:406` `wOverworldMapBlocks:: ds 1300`; hot users include `home/map.asm:1029`, `home/map.asm:1073`, `home/map.asm:1087`, `home/map.asm:2046`, and `engine/events/overworld.asm:301`.
- Estimated bytes saved: up to 1300 WRAM0 bytes if the whole UNION floor is reduced; realistic first design target might be 500-800 bytes.
- Behavior impact: potentially visible overworld scrolling/loading regressions if done poorly.
- Risk level: high. This is a hot map path, not a cold buffer.
- Recommendation: only open as a separate architecture pass if you need hundreds of bytes. Do not bank-switch this naively.

### 11. Shrink the `wSurroundingTiles` / Miscellaneous UNION floor

- Files / symbols: `ram/wram.asm:168` `wSurroundingTiles:: ds SURROUNDING_WIDTH * SURROUNDING_HEIGHT`; constants make this 24 * 20 = 480 bytes. Main users are in `home/map.asm`.
- Estimated bytes saved: up to 240 WRAM0 bytes if the surrounding-tile window can be roughly halved and peer buffers do not still require 480.
- Behavior impact: map blit / screen-edge behavior changes; risk of rendering garbage or missing edge tiles.
- Risk level: high.
- Recommendation: architecture-only. This is one of the few paths to large WRAM0 relief, but it needs a map streaming design, not a tactical edit.

### 12. Remove `wBossAILookaheadDepthCache`

- Files / symbols: `ram/wram.asm:2465`; reset at `engine/battle/ai/boss_platform.asm:555`; read/write in `engine/battle/ai/boss_policy_move.asm:5741-5757`.
- Estimated bytes saved: 1 normal-build Boss AI reserve byte and 1 trace-build byte.
- Behavior impact: no decision change; `GetProjectionDepth` would recompute from `wBossAITier`. The cost is extra cycles in lookahead, not AI quality.
- Risk level: low.
- Recommendation: acceptable if the Boss AI reserve needs one byte. Not urgent while normal build still has 28 reserved free bytes.

### 13. Fold `wBossAIShouldScoutThresholdCache` into the prereq cache

- Files / symbols: `ram/wram.asm:2474-2477`; `BossAI_ShouldScout` in `engine/battle/ai/boss_policy_move.asm:6264-6317`.
- Estimated bytes saved: 1 normal-build Boss AI reserve byte and 1 trace-build byte.
- Behavior impact: none intended if the prereq byte is recoded as `$ff = uncomputed`, `0 = prereqs failed`, and nonzero threshold values `51/102/153 = prereqs passed`. Random consumption must remain exactly where it is.
- Risk level: medium. Small RAM win but nontrivial code churn in a tight ROM bank.
- Recommendation: good reserve-byte candidate only if ROM byte budget can absorb the rewrite.

### 14. Drop `wBossAIShouldScoutMatchupValue`

- Files / symbols: `ram/wram.asm:2477`; reset/comment at `engine/battle/ai/boss_platform.asm:558-564`; read/write in `engine/battle/ai/boss_policy_move.asm:6271`, `6297`.
- Estimated bytes saved: 1 normal-build Boss AI reserve byte and 1 trace-build byte.
- Behavior impact: cache hits would no longer restore the `wTypeMatchup` side effect from the original prereq chain unless the code recomputes it. That can matter to downstream readers and future branch-local lookahead work.
- Risk level: medium-high.
- Recommendation: do not cut for now. The byte is defensive, but it protects a subtle side effect.

### 15. Remove `wBossAITierWeightRow`

- Files / symbols: `ram/wram.asm:2453`; writers in `engine/battle/read_trainer_attributes.asm`; reader in `engine/battle/ai/boss_policy_move.asm:2618`; ramp data in `data/trainers/ai_tiers.asm`.
- Estimated bytes saved: 1 normal-build Boss AI reserve byte and 1 trace-build byte.
- Behavior impact: Bugsy and Whitney lose bespoke weight-row ramping toward mid-tier weights without enabling mid-tier feature gates.
- Risk level: low technically, medium for fight feel.
- Recommendation: taste call only. Do not cut unless playtesting says the ramp is not felt.

### 16. Remove repeat-tracking state

- Files / symbols: `ram/wram.asm:2435-2436` `wBossAIRepeatCount`, `wBossAILastChosenMove`; update logic in `engine/battle/ai/boss_platform.asm:1358-1373`; scoring in `engine/battle/ai/boss_policy_move.asm:5295`.
- Estimated bytes saved: 2 normal-build Boss AI reserve bytes and 2 trace-build bytes.
- Behavior impact: AI loses the "do not keep mashing the same non-KO move" softener.
- Risk level: medium.
- Recommendation: keep. The Pokemon mastery notes emphasize repeated-cycle adaptation; this state directly supports that promise.

### 17. Remove switch-loop state

- Files / symbols: `ram/wram.asm:2424-2425` `wBossAILastSwitchedOut`, `wBossAISwitchCooldown`; switch execution / cooldown in `engine/battle/ai/boss_policy_switch.asm:501-520`; loop penalty in `boss_policy_switch.asm:589+`.
- Estimated bytes saved: 2 normal-build Boss AI reserve bytes and 2 trace-build bytes.
- Behavior impact: AI can regress toward switch oscillation, especially in public-threat loops.
- Risk level: medium.
- Recommendation: keep. This is a high-value 2 bytes.

### 18. Move or trim the `BOSS_AI_TRACE` block

- Files / symbols: `ram/wram.asm:2482-2494` (`wBossAITraceTopMoves` through `wBossAITraceLookaheadBonusTop`); trace readers in `tools/trace/boss_ai_trace_capture.py`, `tools/trace/boss_ai_trace_state_probe.py`, and `tools/trace/boss_ai_state_factory.py`.
- Estimated bytes saved: 28 trace-build Boss AI reserve bytes if moved out of bank 1 or removed; 0 shipping normal-build bytes.
- Behavior impact: normal ROM unchanged. Trace ROM either pays bank-switch/tooling complexity or loses decision introspection.
- Risk level: medium for tooling, low for gameplay.
- Recommendation: move to WRAMX bank 2/3 if trace reserve pressure blocks future trace fields. Do not remove outright unless trace capture is no longer part of the workflow.

### 19. Reduce the observation log window

- Files / symbols: `ram/wram.asm:2780-2784` `wBossAIWramx2Buffer`; constants in `constants/battle_constants.asm:91-110`; implementation in `engine/battle/ai/observation_log.asm`; consumers at `engine/battle/ai/boss_policy_move.asm:3261` and `3786`.
- Estimated bytes saved: 12 WRAMX bank-2 bytes if LATE uses the MID 3-entry window instead of 6 entries; 26 bytes if the whole observation log is removed.
- Behavior impact: lower-quality public tendency memory. The log passed `tools/audit/check_observation_log_invariants.py`, and the policy docs explicitly allow observed switches and repeated patterns.
- Risk level: medium for AI quality, low for memory pressure because bank 2 is not tight.
- Recommendation: do not cut. It overlaps conceptually with `wBossAIPlayerSwitchCount`, but the RAM it uses is not the constrained RAM, and it is the only recent-pattern substrate for tendency and KO-band calibration.

## Non-Candidates Worth Calling Out

- `data/boss_ai/role_package_classifier.asm` is ROM data, not RAM. Cutting or simplifying it will not relieve RAM pressure.
- `wBossAISeenPlayerSpecies`, `wBossAIRevealedMovesBitmap`, `wBossAISpeciesUsedMoves`, and the plausible/likely type masks are high-value public-info memory. The Pokemon mastery notes repeatedly emphasize revealed moves, seen species, branch ownership, observed damage, and repeated-cycle adaptation; cutting these would save bytes but would directly undermine the intended boss behavior.
- The big dead-looking UNION members do not automatically free RAM. Effective savings come from reducing the largest peer in a UNION, not from deleting a smaller peer inside it.

## Ranked Recommendation

1. HRAM: drop the final 20-byte unnamed HRAM pad.
2. WRAM0 safe cleanup: remove `wUnusedMapBuffer` and `wSafariMonAngerCount` for 25 bytes.
3. WRAM0 tactical relocation: move `wRadioText` first, then consider `wSGBPals` after SGB smoke coverage.
4. WRAM0 structural overlay: audit `wBattleScriptBuffer` + `wMovementBuffer`; treat the `wLYOverrides` overlay as riskier because LY overrides are used in more than battle.
5. Boss AI reserve: if you need 1-2 bytes, cut `wBossAILookaheadDepthCache` and consider folding `wBossAIShouldScoutThresholdCache`; keep the revealed-move, repeat, switch-loop, and observation-memory state.
6. If hundreds of bytes are required, open a separate architecture pass for `wOverworldMapBlocks` or `wSurroundingTiles`. Simple RAM shaving will not reach that scale.

## Verification Notes

Read-only commands run:

- `python tools\audit\check_wramx_bank2_declaration.py` - pass.
- `python tools\audit\check_observation_log_invariants.py` - pass.
- `python tools\audit\check_lookahead_trace_width.py` - pass.
- `python tools\audit\check_boss_ai_memory_budget.py` - failed because the existing trace linker outputs are stale relative to the generated docs/current source expectation.
- `python tools\audit\check_wramx_bank1_relief.py` - normal path reports 3685 used / 411 free; trace path fails because the stale trace map has 2 reserve-pad bytes where the current expectation is 0.

No build was run, by request.
