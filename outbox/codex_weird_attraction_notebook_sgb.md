# Weird Attraction Notebook: Super Game Boy Packets

Date: 2026-04-26
Repo: C:\Users\lolno\Downloads\pokemon gold hack

Subject: the Super Game Boy border and color-transfer machinery, especially
`data/sgb_ctrl_packets.asm` and `engine/gfx/color.asm`.

This is the thing I am weirdly attracted to.

I almost chose the Game Boy Printer code first. That path is beautiful in a more
obvious way: Cianwood photo studio, Unown stamps, Pokedex pages, diploma pages,
thermal-printer errors, "Press B to Cancel." It is a whole dead user-facing
feature. But it is still a feature. It still imagines a player holding a printed
souvenir.

The SGB packets feel less useful and more alien. They are not really content.
They are the game reaching outward into the machine around the game.

## Read Set

- `engine/gfx/color.asm`
- `data/sgb_ctrl_packets.asm`
- `engine/gfx/sgb_layouts.asm`
- `constants/hardware.inc`
- `constants/scgb_constants.asm`
- nearby printer files, mostly as the first wrong turn:
  - `engine/printer/printer.asm`
  - `engine/printer/printer_serial.asm`
  - `engine/events/print_unown.asm`
  - `engine/events/print_photo.asm`

## First Pull

The load-bearing assumption was: "no value to the player" means a dead feature.
The printer fit that. In 2026, nobody using this hack needs the Game Boy Printer
path to work.

Invert it: maybe the least player-valued thing is not a dead feature, but a
compatibility ritual for a host machine the target player will never see. Under
that inversion, the Super Game Boy code wins.

The printer says, "Here is a souvenir."

The SGB path says, "I know there is a SNES wrapped around me, and I know how to
whisper into it through the joypad register."

That second sentence is ridiculous. I like it.

## What The Code Is Doing

`InitSGBBorder` in `engine/gfx/color.asm` refuses the CGB path, disables normal
joypad/SGB overlap, then probes for SGB behavior with `PushSGBBorderPalsAndWait`.
If the probe says yes, it sets `hSGB`, pushes special setup packets, pushes
palettes, clears VRAM, pushes border graphics, clears VRAM again, and finally
unfreezes the screen with `MaskEnCancelPacket`.

The little core is `_PushSGBPals`. It reads a packet count from the first byte,
then sends each 16-byte SGB packet bit by bit through `rJOYP`. The constants in
`constants/hardware.inc` make the trick plain:

- `JOYP_SGB_START`
- `JOYP_SGB_ONE`
- `JOYP_SGB_ZERO`
- `JOYP_SGB_FINISH`

So the joypad register is not just input here. It becomes an output wire. A
button register becomes a courier.

Then `data/sgb_ctrl_packets.asm` drops the real trapdoor:

```asm
; These are packets containing SNES code.
; This set of packets is found in several Japanese SGB-compatible titles.
; It appears to be part of NCL's SGB devkit.
```

After that, the file is data declarations that are also little 65c816 fragments:
`cpx`, `bne`, `rts`, `lda`, `sta`, `inx`, `wai`, `jmp`, `nop`. The Game Boy ROM
is carrying code for another CPU as packet payload.

That is the part I cannot stop looking at.

## The Beautiful Wrongness

This is not gameplay. It is not balance. It is not even really presentation for
your likely target runtime. It is hardware diplomacy.

The code talks to the SGB by pretending color and controller machinery are mail
slots:

- SGB command packets are encoded as 16-byte structures.
- Packet bytes are shifted out through `rJOYP`.
- Border palette data gets staged through VRAM after setting `rBGP` to the magic
  SGB transfer value, `BGP_SGB_TRANSFER`.
- The SGB receives graphics/palette payloads via `PAL_TRN`, `CHR_TRN`, and
  `PCT_TRN` packets.
- Before the visible border work, the ROM sends `DATA_SND` packets that appear
  to install a standard SNES-side helper from Nintendo's SGB devkit.

It has the shape of smuggling, but polite smuggling. The cartridge has no direct
business writing SNES code, so it packages the code as sanctioned peripheral
commands and lets the host accept it.

## Tiny Details That Caught

`PushSGBBorderPalsAndWait` asks for multiplayer mode with `MltReq2Packet`, then
pokes and rereads `rJOYP` in a very physical way. It is not abstract detection.
It is "tap the wall, listen for the wall to tap back."

`_PushSGBPals` is patient in a way modern code rarely is. For each byte, for
each bit, it writes one of two magic JOYP values, then writes FINISH. It is a
protocol made out of tiny gestures.

`_InitSGBBorderPals` sends exactly nine packet pointers:

- `MaskEnFreezePacket`
- `DataSndPacket1`
- `DataSndPacket2`
- `DataSndPacket3`
- `DataSndPacket4`
- `DataSndPacket5`
- `DataSndPacket6`
- `DataSndPacket7`
- `DataSndPacket8`

That is such a strange procession. Freeze the display, mail eight shards of
foreign CPU code, continue.

`UpdateSGBBorder` is unreferenced, which makes the whole area feel even more
like a preserved machine room. The init path matters if you care about SGB
support. The update path just sits there, labelled by absence.

## Why It Has Almost No Value Here

For this hack, the valuable work is bosses, balance, source truth, traceability,
QoL, and keeping the first playthrough dangerous. This SGB packet machinery does
none of that.

It does not make Morty smarter. It does not make Johto scarier. It does not help
a modern player understand a changed learnset. If the user plays on a normal GBC
emulator path, the CGB branch skips the whole ritual.

Its value is archival and aesthetic. It preserves the old fact that Pokemon Gold
was not only software for a Game Boy. In one strange mode, it was software inside
a Game Boy inside a SNES, negotiating with both.

That has no real product value to this project.

I still think it is beautiful.

## Do Not Accidentally "Clean" This

This is not a request to change anything.

If a future session ever needs space and asks whether SGB support is expendable,
this area could become a deliberate scope question. But it should not be removed
as generic clutter. Dead-to-the-current-player is not the same as meaningless.

The weird historical organs are part of why a disassembly feels alive.

