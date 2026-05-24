# Graphics / Emulator Debugging

Use this when a report mentions scrambled tiles, wrong palettes, broken
textbox/map graphics, emulator-only behavior, save states, or PyBoy/VBA
differences.

## Fast Triage

| Symptom | First suspicion | Inspect first |
| --- | --- | --- |
| Sprites still look correct, but map/textbox background tiles turn into letters, window pieces, or garbage. The screen fixes itself after the textbox closes. | BG map / VRAM transfer timing, not map data corruption. | `hBGMapMode`, `WaitBGMap`, `UpdateBGMap`, `wTileMap` vs `vBGMap`, text/window routines, and any sound-wait or animation path active during the textbox. |
| Palettes are wrong after a map transition, whiteout, Fly, or reload. | Palette reload/state lifetime. | `engine/gfx/color.asm`, map reload paths, whiteout/respawn path, and CGB palette buffers. |
| Sprites are corrupted or the wrong icon appears. | Sprite/icon graphics loading or stale object graphics state. | `gfx/`, `data/sprites/`, icon/pic loaders, and map object refresh paths. |
| PyBoy looks clean but VBA glitches. | Emulator timing difference; PyBoy did not rule it out. | Try to reproduce in VBA and capture BG Map Viewer evidence if possible. |

## Known VBA Tile-Jumble Pattern

Observed in May 2026 on VBA: map tiles can temporarily turn into font/window
garbage while an overworld textbox is open, then snap back when the textbox
closes. Confirmed reports involved starter receive/nickname flow, Pokemon
Center heal, berry tree item receipt, and the Berry Master. Plain signs and
plain dialogue were not enough to trigger it.

Interpretation:

- If closing the textbox restores the map, assume `wTileMap` may still be good
  and the visible BG map / VRAM copy is suspect.
- If sprites remain correct, do not start in Pokemon party data, map object
  data, or save-format code.
- Scenes with a textbox plus a jingle/fanfare are higher-risk because text
  printing, BG map updates, and sound waits can overlap.

Current fix note:

- 2026-05-12: `home/audio.asm` `WaitSFX` now clears pending BG map copying
  before and after SFX waits. This fixed the starter nickname prompt tile
  jumble reported on VBA, then was tightened after a one-off Mom day/DST prompt
  report showed the same class could survive into the next textbox/menu.
- 2026-05-23: `home/tilemap.asm` `CopyTilemapAtOnce` now waits until
  `LY_VBLANK - 1` instead of line `$7f`, matching the safer phone-ring
  full-copy variant. Full tilemap copy helpers also clear pending incremental
  row/column BG-map updates because the full copy supersedes them.
- 2026-05-23: `home/gfx.asm` `Request1bpp` and `Request2bpp` now wait until
  the VBlank handler clears the queued request size. This keeps late-VBlank
  skips from making callers overwrite or drop a still-pending tile copy.
- If the same symptom returns, first check whether a path waits for SFX, cry,
  music, or animation while `hBGMapMode` is still enabled. Then inspect
  `home/window.asm`, `home/text.asm`, `home/map.asm`, and
  `engine/overworld/scripting.asm` around the active script command.

## Capture Checklist

Ask the player for:

- the ROM path and save path;
- a screenshot or phone photo taken while the screen is still glitched;
- whether closing the textbox fixes it;
- whether sprites, menus, and cursor graphics stay readable;
- the emulator name/version.

If using VBA, the best extra evidence is Tools -> BG Map Viewer paused while the
screen is glitched. That can show whether the bad write is in the visible BG map
or only in tile data.

## PyBoy Save Notes

PyBoy does not automatically load this repo's `pokegold.sav` as a battery save
for an arbitrary copied ROM name. It looks for a sidecar named after the ROM,
such as `repro.gbc.ram`.

For a temporary PyBoy repro, copy the ROM to `.local/`, then copy the first
32 KiB of `pokegold.sav` into a matching `.gbc.ram` sidecar. Do not overwrite
the user's real save.

```powershell
New-Item -ItemType Directory -Force .local\pyboy_repro | Out-Null
Copy-Item .\pokegold.gbc .local\pyboy_repro\repro.gbc
$bytes = [System.IO.File]::ReadAllBytes("pokegold.sav")
$ram = New-Object byte[] 32768
[System.Array]::Copy($bytes, $ram, 32768)
[System.IO.File]::WriteAllBytes(".local\pyboy_repro\repro.gbc.ram", $ram)
```

Save states are emulator-specific. A VBA-M `.sgm` can be useful as static crash
evidence, but do not assume PyBoy can load it directly. Use the omni debugger to
decode it before trying replay:

```powershell
python -m tools.debugger state-inspect --save-state for_codex1.sgm --rom pokegold.gbc --symbols pokegold.sym --json-out .local\tmp\for_codex1_runtime_state.json
python -m tools.debugger script-resume-gate --report .local\tmp\for_codex1_runtime_state.json
```
