# Pokémon Gold/Silver Romhacking — LLM Operating Manual

> **Audience:** an LLM coding agent about to edit `pret/pokegold` (RGBDS assembly).
> **Read this end-to-end before writing a single instruction.** It is reference, not tutorial. If a fact here conflicts with what you "remember" about the Z80, this doc wins.

---

## 0. If You Only Read One Page, Read This

| You must remember | Why it bites |
|---|---|
| The CPU is **Sharp SM83** (a.k.a. **LR35902**, fan name **"GBZ80"**). It is **not a Z80**. | No `IX/IY`, no shadow regs, no `IN/OUT`, no `LDIR/CPIR/EX`, no `DJNZ`, no `LD A,(BC)` indirect-via-arbitrary-pair. |
| The repo is `github.com/pret/pokegold`. It is **far less documented** than `pret/pokecrystal`. Crystal shares >95% of subsystem code with G/S — **search Crystal first** when looking for docs/comments. | Almost every "how does X work" answer lives in pokecrystal `docs/*.md`, `STYLE.md`, the wiki, or `pret.github.io/pokecrystal/`. Apply with care: a few subsystems (Pokégear/radio, Battle Tower wiring, Mobile Adapter stubs) differ. |
| Toolchain is **RGBDS** (`rgbasm`, `rgblink`, `rgbfix`, `rgbgfx`). pokegold's `INSTALL.md` says **rgbds 1.0.0**; `rgbdscheck.asm` enforces a minimum (currently v0.6.0+). Use `rgbasm`/`rgblink` syntax, **not** WLA-DX, **not** ASMotor, **not** xAsm. | Mixing dialects produces silent miscompiles or "Section name already in use" errors. |
| The cart is **MBC3 + RTC + battery** (Gold/Silver use MBC3, **not MBC5**). ROM bank switch = write byte to `$2000-$3FFF`. The pokegold helper is `rst Bankswitch` (RST $10), backed by `hROMBank` in HRAM. | Crystal JP uses MBC30; international G/S/C use MBC3. Don't paste MBC5-style 9-bit bank writes. |
| **Cross-bank calls MUST use `farcall` / `callfar` / `homecall`.** A bare `call` to a label in another ROMX bank silently jumps to whatever happens to be paged in. | `farcall Foo` expands via `rst FarCall` and saves/restores the bank. |
| **HL and DE are little-endian** in memory (`dw $1234` → byte `$34`, then `$32`). The register **pair** is big-endian in mnemonics (`H` = high, `L` = low). `ld a, [hli]` then `ld h, [hl] / ld l, a` is the canonical "load pointer" idiom and the LO byte comes first. | Easy to reverse pointer reads. See §9.2. |
| Hardware regs live at **`$FF00-$FF7F`** + `IE` at `$FFFF`. HRAM is **`$FF80-$FFFE`**. Use **`ldh [rXxx], a`** for `$FF00-$FFFF` accesses — it's 2 bytes/3 cycles vs `ld [$FFxx], a` at 3 bytes/4 cycles. RGBDS will *not* auto-pick `ldh`; you must write it. | Many pokegold sources use `ldh` explicitly. Don't "optimize" them to `ld`. |
| **Real Z80 instructions that DO NOT EXIST on SM83:** `EX`, `EXX`, `EX AF,AF'`, `EX (SP),HL`, `LDI/LDD/LDIR/LDDR/CPI/CPD/CPIR/CPDR`, `IN/OUT`, `DJNZ`, `JP (IX)/JP (IY)`, `RLC/RRC/RL/RR/SLA/SRA/SRL r,(IX+d)`, `IM 0/1/2`, `RETI` exists but `RETN` doesn't, `LD A,I`, `LD A,R`, all `IX/IY` ops, `SBC HL,rr`, `ADC HL,rr`, `NEG` (use `cpl`+`inc`), index-displacement addressing `(IX+d)`. | If you emit these, `rgbasm` will reject them — but only if you noticed. The dangerous case is when you write Z80-style logic *thinking* something exists. |
| **Real Z80 instructions ADDED on SM83 that don't exist on Z80:** `LDH a,[n8]` / `LDH [n8],a` / `LDH [c],a` / `LDH a,[c]`, `LD [HL+],A` / `LD [HL-],A` / `LD A,[HL+]` / `LD A,[HL-]` (a.k.a. `LDI/LDD A,(HL)` syntax — RGBDS prefers the `+/-` form), `LD HL,SP+e8`, `ADD SP,e8`, `STOP`, `SWAP r`, `RETI` (different encoding). | Use the SM83 forms. RGBDS warns/errors on legacy `JP [HL]` (use `jp hl`) and `LD HL,[SP+e8]` (use `LD HL,SP+e8`). |
| The flag register has only **Z N H C** (bits 7-4). There is **no P/V (parity/overflow) flag** and **no S (sign) flag**. Condition codes are exactly: `Z`, `NZ`, `C`, `NC`. **Not** `PE/PO/M/P`. | Don't write `jp pe,...`. |
| Calling convention is informal but consistent: small args in `A`/`BC`/`DE`/`HL`; pointer in `HL`; bank-byte in `A` (especially before `rst Bankswitch`); **everything else may be clobbered** unless the function comment says otherwise. Carry is the standard "found / success" return. | `FarCall_hl` and `FarCall_de` *do* preserve registers; ordinary `call` does not. |
| Charmap: `"@"` is **string terminator** (`$50`), not the at-sign. `"<PLAYER>"`, `"<RIVAL>"`, `"<PKMN>"`, `<LINE>`, `<NEXT>`, `<PARA>`, `<CONT>`, `<DONE>` are charmap entries — write them inside double-quoted strings. | If you write text that needs to fit on a line, the line text macro inserts the line-break opcode for you; don't hand-pack `$4f`. |
| A label written in the disassembly with `::` (double colon) is **exported** (visible across object files). Single `:` is local to the file. `.foo` is local to the most recent global label. | `LabelName:: ; comment` is the pret canonical export form. |

---

## 1. Hardware: Sharp SM83 / LR35902 / "GBZ80"

### 1.1 Naming
- **SM83** = the CPU core (Sharp datasheet name).
- **LR35902** = die marking on early DMG; refers to the whole SoC (CPU + PPU + APU + DMA + interrupt controller).
- **GBZ80** = community fan name. Acceptable. **Z80** alone is **wrong** and misleads code generation.
- pokegold/pokecrystal `docs/` and the GitHub topic tag use `gbz80`. RGBDS's manpage for the ISA is `gbz80(7)`.

### 1.2 Register file & flags

| Reg | Size | Notes |
|---|---|---|
| A | 8 | Accumulator. Almost every ALU op targets A. |
| F | 8 | Flags `ZNHC----`. Lower 4 bits always read 0. |
| B, C, D, E, H, L | 8 | General. Only `BC`, `DE`, `HL` form pairs. **No** `IX/IY`. **No** shadow set (`A'`, `F'`, etc.). |
| AF, BC, DE, HL | 16 | Pair forms. Endianness in memory: low byte first (`push de` writes E then D? — actually push writes high then decrements, but `ld [addr], hl` writes L then H; see §9.2). |
| SP | 16 | Stack pointer. Default top set by boot ROM, then by game. pokegold sets it early in `Init`. |
| PC | 16 | Program counter. |

**Flags / condition codes:**

| Flag | Bit | Meaning |
|---|---|---|
| Z | 7 | Zero. Set when result is 0 (or for `bit n, r` when bit is 0). |
| N | 6 | Subtract. Set after `sub`/`sbc`/`dec`/`cp`. Used by `daa`. |
| H | 5 | Half-carry (carry from bit 3). Used by `daa`. |
| C | 4 | Carry. |

Condition codes accepted by `jp/jr/call/ret`: `Z`, `NZ`, `C`, `NC`. **That's all.**

### 1.3 Memory map

| Range | Region | Notes |
|---|---|---|
| `$0000-$3FFF` | ROM bank 0 (fixed) | Always mapped. pokegold's `home/` and the RST/IRQ vectors live here. |
| `$4000-$7FFF` | ROMX (banked) | Switchable via MBC3. The "current bank" is mirrored in `hROMBank` ($FF…). |
| `$8000-$9FFF` | VRAM | 2 banks on CGB (`rVBK`). Tile data $8000-$97FF, BG maps $9800-$9FFF. **Inaccessible to CPU during PPU mode 3.** |
| `$A000-$BFFF` | SRAM (or MBC3 RTC register) | Battery-backed. Must be unlocked via $0A→`$0000-$1FFF`. |
| `$C000-$CFFF` | WRAM bank 0 (fixed) | |
| `$D000-$DFFF` | WRAMX (banked, CGB) | 7 banks. `rSVBK` ($FF70). pokegold uses banked WRAM in CGB mode. |
| `$E000-$FDFF` | Echo RAM | Mirrors $C000-$DDFF. **Don't use.** |
| `$FE00-$FE9F` | OAM | Sprite attribute table. Inaccessible during PPU modes 2/3. |
| `$FEA0-$FEFF` | Prohibited / unusable | Has bizarre behavior on real hardware. |
| `$FF00-$FF7F` | I/O registers | See §1.5. |
| `$FF80-$FFFE` | HRAM | 127 bytes. Accessible during OAM DMA. The OAM-DMA copy routine lives here. |
| `$FFFF` | IE | Interrupt enable mask. |

### 1.4 Interrupts

| Vector | Source | IF / IE bit |
|---|---|---|
| `$40` | V-Blank | 0 |
| `$48` | LCD STAT | 1 |
| `$50` | Timer overflow | 2 |
| `$58` | Serial transfer | 3 |
| `$60` | Joypad (transition) | 4 |

`IE` ($FFFF) enables; `IF` ($FF0F) is the pending flag set by hardware. `EI` enables interrupts after the *next* instruction; `DI` disables immediately. `HALT` waits for any enabled+pending interrupt; **the famous HALT bug** (when IME is off) replays the next byte twice — pokegold does not rely on HALT-bug behavior.

The pokegold (and pokecrystal) RST table is laid out in `home.asm` / linker script:

| RST | Use in pokegold |
|---|---|
| `rst $00` | reset / unused stub |
| `rst $08` (`rst FarCall`) | call into far routine; arg in registers, follows table |
| `rst $10` (`rst Bankswitch`) | `a` = new ROM bank → write to `[hROMBank]` and to `$2000` (MBC3) |
| `rst $18` | (game-specific helper) |
| `rst $20` | unused (returns to `$38`) |
| `rst $28` (`rst JumpTable`) | indexed jumptable; `a` = index, `hl` = table base |
| `rst $30` | continuation of $28 |
| `rst $38` | crash / debug trap |

> ❌ "Use `rst $00` to soft-reset" — pokegold's `rst $00` is not the same as a Z80 hard reset; treat all RST slots as game-specific functions defined in `home/` / `main.asm`.

### 1.5 Hardware registers (the ones you'll actually touch)

Defined as `rXxx EQU $FFnn` in `hardware.inc` (community-standard) which pokegold has migrated to.

| Symbol | Addr | Purpose |
|---|---|---|
| `rJOYP` | `$FF00` | Joypad select/read |
| `rSB`/`rSC` | `$FF01/02` | Serial data / control |
| `rDIV` | `$FF04` | Divider (writing resets to 0) |
| `rTIMA`/`rTMA`/`rTAC` | `$FF05/06/07` | Timer counter / modulo / control |
| `rIF` | `$FF0F` | Pending interrupts |
| `rNR10..rNR52` | `$FF10-$FF26` | APU |
| `rLCDC` | `$FF40` | LCD control (display on, BG/OBJ enable, tile maps, …) |
| `rSTAT` | `$FF41` | LCD status (PPU mode in low 2 bits, LYC=LY, …) |
| `rSCY`/`rSCX` | `$FF42/43` | BG scroll |
| `rLY` | `$FF44` | Current scanline (read-only) |
| `rLYC` | `$FF45` | LY compare |
| `rDMA` | `$FF46` | OAM DMA source page (write triggers transfer) |
| `rBGP`/`rOBP0`/`rOBP1` | `$FF47-49` | DMG palettes |
| `rWY`/`rWX` | `$FF4A/4B` | Window position |
| `rKEY1` | `$FF4D` | CGB speed switch |
| `rVBK` | `$FF4F` | VRAM bank (CGB) |
| `rHDMA1..rHDMA5` | `$FF51-55` | CGB VRAM DMA |
| `rRP` | `$FF56` | CGB IR port |
| `rBCPS/rBCPD/rOCPS/rOCPD` | `$FF68-6B` | CGB palette index/data |
| `rSVBK` | `$FF70` | WRAM bank (CGB) |
| `rIE` | `$FFFF` | Interrupt enable |

> ✅ `ldh a, [rLY]` ✅ `ldh [rDMA], a`
> ❌ Don't write a numeric literal: prefer the `r*` symbol from `hardware.inc`.

### 1.6 MBC3 (Pokémon G/S cart)

MBC3 is selected by header byte `$0147 = $10` (MBC3+RAM+BATTERY+TIMER, the G/S configuration).

| Write range | Effect |
|---|---|
| `$0000-$1FFF` | RAM/RTC enable: write `$0A` to enable, anything else (typically `$00`) to disable. |
| `$2000-$3FFF` | ROM bank select (7 bits). Writing 0 selects bank 1. Banks $20/$40/$60 are *valid* on MBC3 (unlike MBC1). |
| `$4000-$5FFF` | RAM bank ($00-$03) **or** RTC register select ($08=S, $09=M, $0A=H, $0B=DL, $0C=DH/flags). |
| `$6000-$7FFF` | Latch clock data. Write `$00` then `$01` to freeze RTC into the registers for reading. |

The pokegold helper `rst Bankswitch` does:

```asm
; from home/
Bankswitch::
    ldh [hROMBank], a
    ld [rROMBank], a   ; rROMBank = $2000
    ret
```

> ❌ Don't bank-switch by writing `[$2000], a` directly. Always go through `rst Bankswitch` so `hROMBank` stays in sync. Other code reads `hROMBank` to push/pop the current bank.
> ❌ Don't try to read RTC seconds without first latching. Don't access SRAM without the `$0A` enable, then **disable when done** (`xor a; ld [rRAMG], a`). pokegold has helpers in `home/sram.asm` (`OpenSRAM`, `CloseSRAM`).

---

## 2. Instruction Reference

### 2.1 Canonical SM83 instruction set (reference table — bytes / cycles in M-cycles unless noted)

| Mnemonic | Bytes | Cycles | Notes |
|---|---|---|---|
| `nop` | 1 | 1 | |
| `ld r8, r8'` | 1 | 1 | 8-bit reg→reg copy (`A,B,C,D,E,H,L`). |
| `ld r8, n8` | 2 | 2 | Immediate. |
| `ld [hl], r8` / `ld r8, [hl]` | 1 | 2 | |
| `ld [hl], n8` | 2 | 3 | |
| `ld a, [bc]` / `ld [bc], a` | 1 | 2 | Only `bc`/`de` allowed for indirect, **not** arbitrary pairs. |
| `ld a, [de]` / `ld [de], a` | 1 | 2 | |
| `ld [nn], a` / `ld a, [nn]` | 3 | 4 | 16-bit absolute. |
| `ldh [n8], a` / `ldh a, [n8]` | 2 | 3 | High RAM / IO ($FF00+n8). |
| `ldh [c], a` / `ldh a, [c]` | 1 | 2 | $FF00+C. |
| `ld [hl+], a` / `ld a, [hl+]` | 1 | 2 | Post-increment. SM83-only. |
| `ld [hl-], a` / `ld a, [hl-]` | 1 | 2 | Post-decrement. SM83-only. |
| `ld r16, n16` | 3 | 3 | `bc/de/hl/sp`. |
| `ld [nn], sp` | 3 | 5 | SM83-only. |
| `ld sp, hl` | 1 | 2 | |
| `ld hl, sp+e8` | 2 | 3 | Signed offset. **Use this form, not the obsolete `ld hl,[sp+e8]`.** |
| `push r16` | 1 | 4 | `bc/de/hl/af`. |
| `pop r16` | 1 | 3 | |
| `add a, r8` / `adc/sub/sbc/and/xor/or/cp` | 1 | 1 | Sets flags. |
| `add a, [hl]` / etc. | 1 | 2 | |
| `add a, n8` / etc. | 2 | 2 | |
| `inc r8` / `dec r8` | 1 | 1 | Sets Z, N, H. **Does not set C.** |
| `inc [hl]` / `dec [hl]` | 1 | 3 | |
| `inc r16` / `dec r16` | 1 | 2 | **Does not set any flags.** |
| `add hl, r16` | 1 | 2 | Sets N=0, H, C. **Does not affect Z.** |
| `add sp, e8` | 2 | 4 | Signed. |
| `daa` | 1 | 1 | BCD adjust. Behavior depends on N flag. |
| `cpl` | 1 | 1 | A ← ~A. |
| `ccf`/`scf` | 1 | 1 | |
| `rlca/rrca/rla/rra` | 1 | 1 | Rotate A; **clears Z** (this differs from the CB-prefix rotates which set Z normally). |
| `cb`-prefixed `rlc/rrc/rl/rr/sla/sra/swap/srl r` | 2 | 2 (8 if `[hl]`: 4 cycles) | `swap` is SM83-only. |
| `cb` `bit n, r` | 2 | 2 (3 if `[hl]`) | Sets Z. |
| `cb` `res n, r` / `set n, r` | 2 | 2 (4 if `[hl]`) | |
| `jp nn` | 3 | 4 | |
| `jp cc, nn` | 3 | 4/3 | Taken/not. |
| `jp hl` | 1 | 1 | **Write `jp hl`. Old `jp [hl]` is deprecated; RGBDS warns.** |
| `jr e8` | 2 | 3 | Range −128..+127 from *next* instruction. |
| `jr cc, e8` | 2 | 3/2 | |
| `call nn` / `call cc, nn` | 3 | 6 / 6 or 3 | |
| `ret` / `ret cc` | 1 | 4 / 5 or 2 | |
| `reti` | 1 | 4 | RET + EI. |
| `rst $00/$08/$10/$18/$20/$28/$30/$38` | 1 | 4 | |
| `halt` | 1 | 1 | |
| `stop` | 2 | — | Encoded `$10 $00`. CGB speed-switch trigger. |
| `di` / `ei` | 1 | 1 | |

**M-cycle vs T-state:** RGBDS docs and Pan Docs use M-cycles (1 M-cycle = 4 T-cycles at DMG speed). pokegold timing comments are usually in M-cycles.

### 2.2 ❌ Real-Z80 instructions that DO NOT exist on SM83 — never emit these

```
EX DE,HL          EX AF,AF'         EXX            EX (SP),HL
LDI / LDD / LDIR / LDDR              CPI / CPD / CPIR / CPDR
DJNZ d            JR PO/PE/M/P,d    JP PO/PE/M/P,nn   CALL PO/PE/M/P,nn   RET PO/PE/M/P
IN A,(n)          IN r,(C)          OUT (n),A      OUT (C),r
LD A,I            LD A,R            LD I,A         LD R,A
IM 0 / IM 1 / IM 2                  RETN
NEG               SBC HL,rr         ADC HL,rr
LD (nn),BC/DE/SP via ED-prefix      LD BC,(nn) etc.
RLD / RRD
All IX/IY: LD IX,nn ; ADD IX,rr ; LD r,(IX+d) ; (IX+d) addressing in any form
SLL r (undocumented Z80)
```

If your training corpus suggests these for "Game Boy," it is wrong.

### 2.3 ✅ SM83-only instructions you must use

```
LDH [n8],A    LDH A,[n8]    LDH [C],A    LDH A,[C]
LD [HL+],A    LD A,[HL+]    LD [HL-],A   LD A,[HL-]
LD HL,SP+e8   LD [nn],SP    ADD SP,e8
SWAP r        STOP          RETI
```

`LDI A,(HL)` / `LDD A,(HL)` syntax is accepted by RGBDS as an alias but pokegold uses `ld a, [hli]` / `ld a, [hld]`. **Match the codebase.**

### 2.4 Anti-hallucination quick checks

| ❌ Looks plausible | ✅ Correct |
|---|---|
| `ld a, (hl)` | `ld a, [hl]` (RGBDS uses square brackets) |
| `ld bc, (de)` | not legal — only `bc`/`de` allow indirect, and only with A: `ld a, [de]` |
| `djnz .loop` | `dec b` + `jr nz, .loop` (two instructions) |
| `ex de, hl` | `push de / pop hl / push hl / pop de` (or use a temp) — there is **no swap** |
| `ldir` (block copy) | call `CopyBytes` from `home/copy.asm` |
| `in a, ($00)` | hardware reads use `ldh a, [rJOYP]` etc. |
| `jp (hl)` | `jp hl` |
| `ld hl, [sp+4]` | `ld hl, sp+4` |
| `out ($46), a` | `ldh [rDMA], a` |
| `cp 0` | `and a` (smaller, faster, sets Z the same) |
| `ld a, 0` | `xor a` (1 byte, 1 cycle) — pokegold uses this idiom everywhere |

---

## 3. RGBDS Assembler

### 3.1 Toolchain components

| Tool | Role |
|---|---|
| `rgbasm` | Assembler. Reads `.asm`, emits `.o`. |
| `rgblink` | Linker. Reads `.o` + linker script (`layout.link` for pokegold). |
| `rgbfix` | Fixes ROM header (logo, complement, global checksum). |
| `rgbgfx` | Converts PNG → `.2bpp` / `.1bpp` tile data. |

`pokegold/Makefile` invokes them with `RGBASMFLAGS += -Q8 -P includes.asm` (Q8 = fixed-point precision; P = preinclude). The build also defines `_GOLD`, `_SILVER`, `_DEBUG`, `_GOLD_VC`, `_SILVER_VC` per target.

### 3.2 Section directives (the only ones you'll see)

```asm
SECTION "Some name", ROM0                    ; goes in fixed bank 0
SECTION "Some name", ROM0[$0150]             ; pinned to address
SECTION "Some name", ROMX                    ; floating, any non-zero bank
SECTION "bank4",     ROMX, BANK[$04]         ; pinned bank
SECTION "Vars",      WRAM0                   ; fixed WRAM bank 0 ($C000)
SECTION "MoreVars",  WRAMX, BANK[1]          ; banked WRAM (CGB)
SECTION "Save",      SRAM, BANK[0]
SECTION "HRAM Vars", HRAM
SECTION UNION "Buffer", WRAM0                ; overlay (multiple defs of same name overlap)
```

`SECTION FRAGMENT "Foo", ROMX` lets you concatenate pieces of the same section across files. pokegold uses unions (especially for `wOverworldMapBlocks` etc.).

### 3.3 Labels & locals

```asm
GlobalLabel:           ; visible in this object file
GlobalLabel::          ; exported (other files can reference) — note the double colon
.local                 ; scoped to the most recent global label
.local2:               ; trailing colon allowed
```

Naming convention (from `pokecrystal/STYLE.md`, applied to pokegold):

| Prefix | Meaning |
|---|---|
| `wPascalCase` | WRAM variable |
| `sPascalCase` | SRAM (save) variable |
| `vPascalCase` | VRAM tile/map address |
| `hPascalCase` | HRAM variable |
| `rPascalCase` | hardware register |
| `PascalCase` | ROM label (function or data) |
| `.snake_case` | local jump |
| `.PascalCase` | local block (a sub-routine local to the parent) |
| `UPPER_CASE` | constant (`EQU` / `DEF`) |

### 3.4 Macros and pseudo-ops you will use constantly

```asm
db   $aa, $bb, "string@"           ; byte(s); RGBDS expands strings via charmap
dw   Label, AnotherLabel           ; little-endian 16-bit
dl   $12345678                     ; 32-bit
ds   16                            ; reserve N bytes (typical RAM use)
ds   16, $ff                       ; reserve and fill
INCBIN "gfx/foo.2bpp"
INCLUDE "engine/bar.asm"
```

pokegold/pokecrystal data macros (in `macros/data.asm`):

| Macro | Expands to | Use |
|---|---|---|
| `dba Label` | `db BANK(Label) :: dw Label` | far pointer (bank, addr) — table entries |
| `dab Label` | `dw Label :: db BANK(Label)` | reverse order (rare) |
| `dbw b, w` | `db b :: dw w` | trainer-class entries, etc. |
| `dwb w, b` | `dw w :: db b` | |
| `dbbw b1, b2, w` / `dbww` / `dbwww` | obvious | varied tables |
| `dn hi, lo` | `db (hi << 4) | (lo & $f)` | DV pairs |
| `bigdw n` | big-endian 16-bit | rare |
| `dt n`, `dd n` | 3-byte / 4-byte big-endian | |

`BANK(Label)` evaluates to the bank number where `Label` was placed; `LOW(x)` and `HIGH(x)` extract bytes. **Always written in caps in modern pokegold/pokecrystal style.**

`rst FarCall` macros:

| Macro | Equivalent |
|---|---|
| `farcall Label` | `ld a, BANK(Label) :: ld hl, Label :: rst FarCall` (preserves regs through helper) |
| `callfar Label` | older spelling — pokecrystal commit history standardized on `farcall` for the calling form and `callfar` for an explicit longer one; both are aliased via `macros/legacy.asm`. **Default to `farcall`.** |
| `homecall Label` | call into home bank from anywhere |

```asm
; macros/legacy.asm shim:
DEF callba EQUS "farcall"
DEF callab EQUS "callfar"
```

Old hacks use `callba`/`callab`/`predef`; new code uses `farcall`/`callfar`/`predef`. **Never write `callba` in new code.**

### 3.5 RGBDS dialect differences (don't blend syntaxes)

| Feature | RGBDS | WLA-DX | ASMotor | xAsm/legacy |
|---|---|---|---|---|
| Memory indirection | `[hl]`, `[$ff80]` | `(hl)`, `($FF80)` | `[hl]` | `[hl]` |
| Section start | `SECTION "X", ROM0` | `.bank 0 .org $0150` | similar to RGBDS | similar |
| Hex prefix | `$abcd`, `0xabcd`, `&habcd` (deprecated) | `$abcd` | `$abcd` | `$abcd` |
| Binary | `%1010` | `%1010` | | |
| Char literal | `"@"` is a string of 1 byte (charmap-mapped) | `'A'` | | |
| Constant | `DEF NAME EQU 1` (modern) | `.def NAME 1` | | older RGBDS allowed `NAME EQU 1` without `DEF`; modern style requires `DEF` |
| Macro | `MACRO foo` … `ENDM` | `.macro foo` | | |
| Conditional | `IF` / `ELIF` / `ELSE` / `ENDC` | `.ifdef` | | |
| Bank-of | `BANK(label)` | `:label` | | |
| Concat | `\1`, `\2` … inside macros; `\@` for unique label suffix | | | |

> ❌ **Don't paste WLA-DX syntax** — `(hl)` will be parsed as a parenthesized expression, not memory access, and silently miscompile. RGBDS requires `[hl]`.

### 3.6 The pokegold linker script (`layout.link`)

`layout.link` is a flat list:

```
ROM0
    "Header"
    "Home"
ROMX $01
    "bank1"
ROMX $04
    "bank4"
...
WRAM0
    "WRAM"
WRAMX $01
    "WRAM 1"
HRAM
    "HRAM"
SRAM $00
    "SRAM Bank 0"
```

The `Makefile` enforces RGBDS version with `rgbdscheck.asm`. Object file list is in `Makefile` under `rom_obj`.

---

## 4. pokegold Codebase Layout

```
pokegold/
├── audio/                  ; audio engine + music data
├── constants/              ; *_constants.asm (every gameplay constant)
├── data/                   ; static data tables (battle/, items/, maps/, moves/, pokemon/, trainers/, etc.)
├── docs/                   ; bugs_and_glitches.md and a few notes (much sparser than pokecrystal/docs/)
├── engine/                 ; runtime code organized by subsystem
│   ├── battle/             ; core.asm, ai/, effect_commands, anim_hp_bar.asm
│   ├── battle_anims/
│   ├── events/             ; overworld events (bug contest, fishing, surf, etc.)
│   ├── games/              ; slots, memory game, etc.
│   ├── gfx/                ; pic loading, palettes, dump routines
│   ├── items/              ; item_effects.asm, tmhm.asm, switch_items.asm
│   ├── link/               ; cable link + Mystery Gift + Time Capsule
│   ├── menus/              ; start menu, naming screen, scrolling menu, trainer card
│   ├── movie/              ; intro / credits / hof
│   ├── overworld/          ; map_objects, player_movement, scripting (NOTE: scripting interpreter), wildmons
│   ├── phone/              ; phone calls
│   ├── pokedex/
│   ├── pokegear/           ; map / radio / clock
│   ├── pokemon/            ; party, evolve, mail, mon_menu, breeding helpers
│   ├── rtc/                ; clock setup
│   ├── sprite_anims/
│   └── sprites/
├── gfx/                    ; 2bpp/PNG art, tilesets, sprites
├── home/                   ; "home bank" code — always paged in (bank 0). Common helpers.
├── macros/                 ; macros/{predef,farcall,data,code,gfx,coords,vc}.asm + macros/scripts/*
├── maps/                   ; one .asm per map (events/scripts) + .blk binaries
├── ram/                    ; wram.asm, hram.asm, sram.asm declarations
├── tools/                  ; helper C/Python tools for build
├── vc/                     ; Virtual Console patch templates
├── audio.asm  home.asm  main.asm  ram.asm           ; section drivers (mostly INCLUDEs)
├── includes.asm                                      ; preincluded constants/macros
├── layout.link                                       ; rgblink script
├── Makefile
├── rgbdscheck.asm                                    ; rejects too-old RGBDS
└── INSTALL.md / README.md
```

### 4.1 Where each subsystem lives (cheatsheet)

| Subsystem | Files |
|---|---|
| **Boot / interrupts / RST table** | `home.asm` and surrounding `home/`, plus `engine/movie/intro*.asm` |
| **OAM DMA routine (in HRAM)** | `home/copy.asm` (the loader) + `ram/hram.asm` (`hPushOAM`) |
| **Banking helpers** | `home/farcall.asm` (`FarCall_hl`, `FarCall_de`, `ReturnFarCall`), `home.asm` `Bankswitch::` at `rst $10` |
| **`predef` (table-dispatched home calls)** | `home/predef.asm` + `macros/predef.asm`; predef list in `data/predef_pointers.asm` |
| **Random** | `home/random.asm` (`Random`, `BattleRandom`) |
| **Bytewise copy / fill** | `home/copy.asm` (`CopyBytes`, `ByteFill`) |
| **Math (multiply, divide, BCD)** | `home/math.asm`, `home/print_bcd.asm` |
| **Text engine** | `home/text.asm` (`PrintText`, `DoTextUntilTerminator`, `TextCommands` jump table); macros in `macros/scripts/text.asm`; charmap in `constants/charmap.asm` |
| **Map / event runtime** | `home/map.asm`, `engine/overworld/events.asm`, `engine/overworld/scripting.asm` (`ScriptCommandTable`, `RunScriptCommand`) |
| **Map data (per map)** | `maps/<MapName>.asm` (events + scripts), `maps/<MapName>.blk` (block layout), declared in `data/maps/maps.asm` |
| **Battle engine core** | `engine/battle/core.asm` (huge — `DoBattle`, `StartBattle`, `BattleCommand_DamageCalc`) |
| **Battle command opcodes** | `engine/battle/effect_commands.asm` + `data/battle/effect_command_pointers.asm` + `data/moves/effects.asm` |
| **AI (trainer)** | `engine/battle/ai/*.asm` (`scoring.asm`, `move.asm`, `items.asm`) |
| **Trainer parties data** | `data/trainers/parties.asm` (FALKNER, BUGSY, …); attributes in `data/trainers/attributes.asm`; DVs in `data/trainers/dvs.asm` |
| **Pokémon base stats** | `data/pokemon/base_stats/<name>.asm` (one file each, INCLUDEd via `data/pokemon/base_stats.asm`) |
| **Learnsets / evolutions** | `data/pokemon/evos_attacks.asm`, pointers in `data/pokemon/evos_attacks_pointers.asm` |
| **Egg moves** | `data/pokemon/egg_moves.asm` |
| **Move data** | `data/moves/moves.asm`, `data/moves/names.asm`, `data/moves/effects.asm`, `data/moves/tmhm_moves.asm` |
| **Items** | `data/items/*.asm`, `engine/items/item_effects.asm` |
| **Audio engine** | `audio/engine.asm`; sound data in `audio/music/*` and `audio/sfx/*` |
| **Graphics decompression** | `engine/gfx/load_pics.asm`, `home/decompress.asm` (LZ-style scheme used by pic data) |
| **Save / SRAM** | `home/sram.asm` (`OpenSRAM`/`CloseSRAM`), `engine/menus/save.asm` |
| **Wild Pokémon** | `data/wild/*.asm`, `engine/overworld/wildmons.asm` |
| **WRAM declarations** | `ram/wram.asm` (every `wXxx::` label) |
| **HRAM declarations** | `ram/hram.asm` (every `hXxx` constant) |

### 4.2 Build

```make
# from pokegold/Makefile (excerpt)
RGBASMFLAGS += -Q8 -P includes.asm
$(pokegold_obj):   RGBASMFLAGS += -D _GOLD
$(pokesilver_obj): RGBASMFLAGS += -D _SILVER
```

`make` produces `pokegold.gbc`, `pokesilver.gbc`, `pokegold_debug.gbc`, `pokesilver_debug.gbc`, plus the VC patch files. `make compare` checks the SHA-1s in `roms.sha1` (e.g. `d8b8a3600a465308c9953dfa04f0081c05bdcb94` for Gold UE).

> **Toolchain version gotcha:** `pokegold/INSTALL.md` currently specifies **rgbds 1.0.0**. `rgbdscheck.asm` enforces a minimum (was v0.6.0 historically; check the current file). Newer RGBDS is generally fine; older RGBDS will fail with cryptic syntax errors.

### 4.3 Crystal vs Gold/Silver — when to reuse pokecrystal docs

**Reuse freely:** text engine, charmap, scripting commands (the table is a near-superset; Crystal added two opcodes `$52` and `$9F`, so script *opcodes* shift after `$51` between G/S and Crystal but the macro names do not), battle engine flow, base stats / learnset / evolution layout, audio engine, OAM/DMA setup, banking helpers, RAM map for party, `farcall` semantics, naming style, RGBDS macros.

**Verify on pokegold first:** any feature added in Crystal (Battle Tower, Mobile Adapter, Suicune scripting, GS Ball event handler, Crystal-only NPCs/maps, the unown puzzles, expanded Pokégear radio shows). The trainer class table differs slightly (no `MYSTICALMAN` in G/S, etc.). Several `engine/events/` files have different filenames or are absent in pokegold.

**Authoritative pokecrystal docs to consult:**
- `pokecrystal/docs/text_commands.md` — every text control code
- `pokecrystal/docs/event_commands.md` — script command list
- `pokecrystal/docs/map_event_scripts.md` — `def_warp_events` etc.
- `pokecrystal/docs/music_commands.md`
- `pokecrystal/docs/bugs_and_glitches.md` (also exists as `pokegold/docs/bugs_and_glitches.md`, partially mirrored)
- `pokecrystal/docs/design_flaws.md`
- `pokecrystal/STYLE.md`
- pokecrystal wiki tutorials: "Add a new Pokémon", "Add a new map and landmark", "Add a new trainer class", etc.

---

## 5. Idioms — Canonical Examples

### 5.1 Far call

```asm
; ✅ canonical: pokecrystal home/farcall.asm (pokegold has the same shape)
FarCall_hl::
    ldh [hTempBank], a
    ldh a, [hROMBank]
    push af
    ldh a, [hTempBank]
    rst Bankswitch
    call FarCall_JumpToHL
    ; fallthrough to ReturnFarCall

ReturnFarCall::
    ld a, b
    ld [wFarCallBC], a
    ld a, c
    ld [wFarCallBC + 1], a
    pop bc
    ld a, b
    rst Bankswitch
    ld a, [wFarCallBC]
    ld b, a
    ld a, [wFarCallBC + 1]
    ld c, a
    ret
```

Use site:

```asm
    farcall ChangeHappiness        ; ✅ macro expands to bank+addr load + rst FarCall
```

❌ Don't:

```asm
    ld a, BANK(ChangeHappiness)
    ld [rROMBank], a                ; WRONG: bypasses hROMBank shadow
    call ChangeHappiness
    ; ... no bank restore ...
```

### 5.2 Bank-aware data table (pointer in another bank)

```asm
; ✅ data/pokemon/evos_attacks_pointers.asm style
EvosAttacksPointers::
    table_width 2, EvosAttacksPointers
    dw BulbasaurEvosAttacks
    dw IvysaurEvosAttacks
    ; ...

; …but if entries cross banks, switch to dba:
SomeCrossBankTable::
    table_width 3, SomeCrossBankTable
    dba RoutineInBank3
    dba RoutineInBank7
```

To call one:

```asm
    ld hl, SomeCrossBankTable
    ld bc, 3
    ld a, INDEX
    call AddNTimes      ; hl += a * bc
    ld a, [hli]         ; bank
    ld h, [hl]
    ld l, a             ; ⚠ read address into hl LO-then-HI
    ; oops — order matters; see §9.2
```

Idiomatic full pattern, lifted from pokegold:

```asm
    ld hl, .Table
    rst JumpTable          ; rst $28: a = index, hl = base of dw table → jp [hl]
.Table:
    dw .Case0
    dw .Case1
```

### 5.3 Loading a 16-bit pointer from memory (HL/DE order)

A `dw Foo` in memory is `LOW(Foo), HIGH(Foo)`. Reading into HL:

```asm
; ✅ canonical
    ld hl, PointerInMemory
    ld a, [hli]            ; A = LOW
    ld h, [hl]             ; H = HIGH
    ld l, a                ; L = LOW
```

> ❌ Don't reverse it. The memory layout is little-endian; the *register pair* HL holds H in the high byte, but you must load LOW first because that's what's at the lower address.

### 5.4 OAM DMA (HRAM-resident routine)

```asm
; pokegold has the standard 10-byte routine copied into hPushOAM ($FF80):
;   ld a, HIGH(wShadowOAM)
;   ldh [rDMA], a
;   ld a, 40
; .wait:
;   dec a
;   jr nz, .wait
;   ret

; ✅ At init: copy DMA stub into HRAM
    ld c, LOW(hPushOAM)
    ld b, .end - .start
    ld hl, .start
.copy
    ld a, [hli]
    ldh [c], a
    inc c
    dec b
    jr nz, .copy
```

> ❌ Don't try to write to OAM during rendering by spinning over `[hl]`. Either DMA it during VBlank or queue into `wShadowOAM` and let the per-frame `call hPushOAM` flush it.

### 5.5 Text printing

```asm
; data/text/foo.asm or maps/Whatever.asm
HelloText::
    text  "Hi, this is text!"
    line  "Second visible line."
    cont  "Third (scroll)."
    para  "New paragraph."
    done                       ; emits text terminator $50 ("@") + TX_END

; call site (anywhere)
    ld hl, HelloText
    call PrintText
```

Charmap caveats (see `constants/charmap.asm`):

| Source | Byte | Behavior |
|---|---|---|
| `"@"` | `$50` | string terminator (NOT the at-sign character) |
| `"<PLAYER>"` | `$52` | placeholder, replaced at print time with `wPlayerName` |
| `"<RIVAL>"` | `$53` | ditto for rival |
| `"<MOM>"` | `$49` | mom's name |
| `"<PKMN>"` | `$4a` | "PK" + "MN" tiles |
| `"<POKE>"` | `$24` | "PO" + "KE" tiles |
| `"<LINE>"` | `$4f` | move to next line |
| `"<NEXT>"` | `$4e` | move down a line |
| `"<PARA>"` | `$51` | new textbox (paragraph) |
| `"<CONT>"` | `$4b` | scroll arrow + scroll |
| `"%"` | `$25` | soft line break in landmark names |
| `"¯"` (U+00AF macron) | `$1f` | soft line break |

> ❌ Don't include literal `'@'` in dialog. ❌ Don't insert `\n` — the GB charmap has no concept of `\n`; use `<LINE>` / `next` / `cont` / `para` macros. ❌ Don't put more than 18 characters on a single line (the textbox is 18 wide). The `text` engine will not wrap for you.

### 5.6 Adding a script to a map

```asm
; maps/PalletTown.asm style
PalletTown_MapScripts:
    def_scene_scripts
    def_callbacks

PalletTown_MapEvents:
    db 0, 0 ; filler

    def_warp_events
    warp_event  6, 7, ELMS_LAB,        1
    warp_event  9, 0, PLAYERS_HOUSE_2F, 1

    def_coord_events
    coord_event  4, 4, SCENE_DEFAULT, .CoordScript

    def_bg_events
    bg_event     5, 5, BGEVENT_READ, .SignScript

    def_object_events
    object_event 8, 4, SPRITE_YOUNGSTER, SPRITEMOVEDATA_STANDING_DOWN, \
                 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, .NPCScript, EVENT_PALLET_NPC

.NPCScript:
    faceplayer
    opentext
    writetext .Hello
    waitbutton
    closetext
    end

.Hello:
    text "Hi!"
    done
```

> ❌ Don't write `warp_event x, y, MAP_NAME, 1` as the third value when the *destination* map has more than one warp; the third value is the destination warp's **index** (1-based) within that map's `def_warp_events`. The most common new-hacker bug.

### 5.7 Trainer party (data/trainers/parties.asm)

```asm
; - db "NAME@", TRAINERTYPE_*
; - 1 to 6 mons; format depends on TRAINERTYPE_*
; - db -1 ; end

FalknerGroup:
    ; FALKNER (1)
    db "FALKNER@", TRAINERTYPE_MOVES
    db 7, PIDGEY,    TACKLE, MUD_SLAP, NO_MOVE, NO_MOVE
    db 9, PIDGEOTTO, TACKLE, MUD_SLAP, GUST,    NO_MOVE
    db -1
```

| TRAINERTYPE | Per-mon bytes |
|---|---|
| `TRAINERTYPE_NORMAL` | `level, species` |
| `TRAINERTYPE_MOVES` | `level, species, m1, m2, m3, m4` |
| `TRAINERTYPE_ITEM` | `level, species, item` |
| `TRAINERTYPE_ITEM_MOVES` | `level, species, item, m1, m2, m3, m4` |

### 5.8 Base stats record

`data/pokemon/base_stats/<name>.asm`:

```asm
    db 0   ; species ID placeholder (filled at link)
    db 45,  49,  49,  45,  65,  65   ; hp atk def spd satk sdef
    db GRASS, POISON                 ; types
    db 45                            ; catch rate
    db 64                            ; base exp
    db NO_ITEM, NO_ITEM              ; held items
    db GENDER_F12_5                  ; gender ratio
    db 100                           ; unknown / hatch counter
    db 20                            ; step cycles to hatch
    db 5, BANK(BulbasaurFrontpic)    ; etc.
    db GROWTH_MEDIUM_SLOW
    db EGG_MONSTER, EGG_PLANT
    tmhm CUT, HEADBUTT, ...          ; tmhm macro packs into 8 bytes
```

`BASE_DATA_SIZE` is a constant; `assert_table_length NUM_POKEMON` after the include list verifies count.

### 5.9 Calling convention summary (pokegold-style)

| In | Out | Convention |
|---|---|---|
| `hl` | — | Pointer in/out for almost every "find / lookup" routine |
| `de` | — | Secondary pointer, often destination for copies |
| `bc` | — | Byte count for copies, or counter |
| `a` | `a` + `Z`/`C` | Single-byte arg / return; `carry set` typically means "found" / "error" depending on routine |
| `hl, bc` | `a` | `AddNTimes` (in `home/math.asm`): `hl += a * bc` |
| `hl, bc` | `hl, bc` | `CopyBytes`: copy `bc` bytes from `hl` to `de` |
| `de, hl, bc` | — | `ByteFill`: write `a` to `bc` bytes at `hl` |
| Bank in `a`, addr in `hl` | preserved | `Bankswitch` via `rst $10`; or `farcall` macro |

**Clobbers:** Unless the comment header says "preserves regs," assume any `call` may clobber `a`, `bc`, `de`, `hl`, `f`. Save with `push`/`pop` *the registers you need*. The `FarCall_hl` helper is special: it preserves all GP registers across the far call.

---

## 6. The Script Command Engine

Defined in `engine/overworld/scripting.asm`. The interpreter reads bytes from a script pointer; each opcode indexes `ScriptCommandTable` (a `dw` table). Macros in `macros/scripts/events.asm` emit the opcodes by name.

Common commands (subset; full list in pokecrystal `docs/event_commands.md`):

| Macro | Purpose |
|---|---|
| `scall .label` | call a sub-script |
| `sjump .label` | jump to a sub-script |
| `farscall ROUTINE` / `farsjump` | far variants |
| `iftrue .label` / `iffalse` / `ifequal n, .label` / `ifgreater` / `ifless` / `ifnotequal` | branches based on script var |
| `setflag EVENT_FOO` / `clearflag` / `checkflag` | event flag (a bit-flag in SRAM) |
| `setevent EVENT_FOO` / `checkevent` / `clearevent` | similar but in a different table |
| `giveitem ITEM, qty` / `takeitem` / `checkitem` | inventory |
| `givepoke SPECIES, level[, item]` / `givepokemail` | party |
| `loadtrainer CLASS, NUM` / `startbattle` / `reloadmapafterbattle` | trainer fights |
| `playmusic MUSIC_X` / `playsound SFX_X` | audio |
| `applymovement OBJECT, .moves` | NPC movement |
| `opentext` / `writetext .label` / `waitbutton` / `closetext` | dialog |
| `special SPECIAL_X` | call out to a hardcoded routine via `data/event/special_pointers.asm` |
| `warpcheck` / `warp MAP, x, y` | maps |
| `end` | terminate script |

> ❌ **Don't** invent script opcodes by writing raw `db` bytes; always use the macro names. The opcode numbering differs between Gold/Silver and Crystal (Crystal inserted opcodes at $52 and $9F, shifting later ones) — using the macro insulates you.

---

## 7. Audio Engine (high-level)

`audio/engine.asm` is shared with pokecrystal. Songs are byte-coded sequences:

```asm
musicheader 4, 1, Music_Foo_Ch1
    channel_count 4
    channel 1, Music_Foo_Ch1
    channel 2, Music_Foo_Ch2
    ...

Music_Foo_Ch1:
    tempo 144
    volume $77
    notetype 12, 11, 7
    octave 3
    note C_, 4
    note D_, 4
    sound_loop 0, Music_Foo_Ch1
```

Documented in `pokecrystal/docs/music_commands.md`. Channels 1-3 use `note`, channel 4 uses `drum_note`, SFX channels 5-8 use `square_note`/`noise_note`. **Reuse pokecrystal docs verbatim.**

---

## 8. Pitfalls — High-Value Section

### 8.1 Z80 "muscle memory" pitfalls

```asm
; ❌
ldir                       ; doesn't exist
djnz .loop                 ; doesn't exist
ex de, hl                  ; doesn't exist
in a, ($00)                ; doesn't exist
jp pe, .nope               ; PE is a Z80 flag — SM83 has only Z/NZ/C/NC
add hl, a                  ; A is 8-bit; SM83 only has add hl, r16

; ✅
call CopyBytes             ; or write the loop manually
dec b
jr nz, .loop
push de :: pop hl :: ...   ; manual swap
ldh a, [rJOYP]
jr nz, .nope               ; or jr c / jr nc
ld c, a :: ld b, 0 :: add hl, bc
```

### 8.2 Endianness traps

`dw Foo` in memory: byte at `addr` = `LOW(Foo)`, byte at `addr+1` = `HIGH(Foo)`. **Reading order matters:**

```asm
; ✅ HL ← *(HL) (i.e., load 16-bit from address HL)
    ld a, [hli]
    ld h, [hl]
    ld l, a

; ❌ This puts HIGH(Foo) into L:
    ld l, [hl]
    inc hl
    ld h, [hl]
```

Push/pop, however, work in expected order: `push hl` writes H first (at `[--SP]`), then L. So after `push hl :: pop de`, `D=H, E=L` (the same logical 16-bit value). That part is intuitive.

### 8.3 Bank-switching mistakes

| ❌ Mistake | ✅ Correct |
|---|---|
| Plain `call SomeFarRoutine` to a label in another bank | `farcall SomeFarRoutine` |
| Reading data from another bank without switching | `ldh a, [hROMBank] :: push af :: ld a, BANK(Data) :: rst Bankswitch :: ... :: pop af :: rst Bankswitch` |
| Switching banks but forgetting `[hROMBank]` | Always go through `rst Bankswitch` (it updates both `hROMBank` and `rROMBank`) |
| Reading SRAM without enable | `call OpenSRAM` (sets bank, writes $0A) → ... → `call CloseSRAM` |
| Changing the RTC mode while RAM is mapped | Write the bank-select register ($4000-$5FFF) before any read at $A000 |
| Latching RTC twice in a row with `01,01` | Sequence is `00` then `01` — repeating `01` does nothing |
| Assuming `BANK(Foo)` works for SRAM/HRAM labels | `BANK(Foo)` is meaningful for ROMX labels; for HRAM use the symbol directly with `ldh` |

### 8.4 HRAM vs WRAM — addressing mode subtlety

```asm
; ✅ short form, 2 bytes, 3 cycles
    ldh a, [rLY]              ; rLY = $FF44

; ❌ long form, 3 bytes, 4 cycles, identical effect
    ld a, [$FF44]
```

RGBDS will **not** automatically pick `ldh` for you when the symbol resolves to `$FFxx`. You must write `ldh` explicitly. pokegold uses `ldh` consistently for HRAM and IO; matching style is mandatory.

### 8.5 VRAM / OAM access timing

- VRAM (`$8000-$9FFF`): inaccessible during PPU mode 3 (drawing). Writes during mode 3 are discarded; reads return `$FF`. Safe in V-Blank, H-Blank, and mode 2 — but pokegold conventionally only writes VRAM during V-Blank or with the LCD off.
- OAM (`$FE00-$FE9F`): inaccessible during modes 2 and 3. Always update via the OAM DMA from `wShadowOAM`.
- During OAM DMA, **the CPU can only execute from HRAM** (DMG; on CGB it can also access ROM/SRAM if WRAM isn't on the bus). pokegold handles this by spinning entirely inside the HRAM stub.
- **Don't disable the LCD outside V-Blank** — Pan Docs warns this can damage real hardware. pokegold's screen-off paths always wait for `rLY ≥ 144`.

### 8.6 Signed vs unsigned arithmetic, JR ranges

- `jr e8` range is **−128…+127** measured from the address of the *next* instruction. Long branches need `jp`.
- `add sp, e8` and `ld hl, sp+e8` use a *signed* 8-bit displacement.
- All other ALU ops are unsigned by default. Sign-magnitude is up to your code (e.g., the AI scoring code in `engine/battle/ai/scoring.asm` operates on unsigned scores and uses `bit 7, a` to test sign manually).
- `cp` is `sub` without storing — sets C iff `A < r` (unsigned). For signed compare you have to decompose: `xor` the sign bits or test with `bit 7`.
- `inc r8` / `dec r8` set Z and H but **do not touch C**. Don't expect `dec b` to give you a borrow flag.

### 8.7 `jp hl` / `rst JumpTable` semantics

- `jp hl` jumps to the address in HL. RGBDS used to accept `jp [hl]` and now warns that it is obsolete — write `jp hl`.
- `rst JumpTable` (RST $28) does: `de` saved on stack, `hl` += `a*2`, then `hl` = `[hl]`, then `jp hl`. Tables for it are written as `dw` lists. Use it for small jump dispatches.

### 8.8 Charmap pitfalls

- The charmap is *active* at assembly time. The instant `db "string"` is encountered, RGBDS substitutes via the current charmap.
- A `"@"` literal becomes `$50` (terminator). If you want the actual at-sign glyph, you can't have it; G/S charmap has no `@` rendering.
- `<PLAYER>` etc. are **dynamic**; if you call PrintText and the player has not been initialized, `wPlayerName` is whatever junk is there.
- `"\n"` is **not** a charmap entry. It's a C-style escape; in RGBDS it's a literal newline byte (`$0a`) which the GB text engine doesn't understand. Use the `line` / `next` / `cont` / `para` macros.

### 8.9 Sundry

- `STOP` is 2 bytes (`$10 $00`). Don't drop the `$00`.
- `HALT` followed by an instruction is risky if IME=0 and an interrupt is pending (HALT bug). pokegold's `Init` enables IME early to avoid the issue.
- `daa` only behaves correctly immediately after an arithmetic op that set N/H meaningfully. Don't `daa` after a load.
- `add hl, hl` is the canonical "shift HL left by 1." The half-carry flag is from bit 11.
- `bit n, [hl]` takes 3 M-cycles (not 4 as one might expect from the "memory" pattern); `set/res n, [hl]` take 4.
- `pop af` will pop into F **and the low 4 bits of F always read as 0**. Code that pushes/pops AF to preserve flags is OK; code that uses F as a scratch byte is not.

---

## 9. Pre-Edit Checklist (must run mentally before writing code)

Before you produce any assembly:

1. **Where am I?** Identify the bank of the file you are editing (`SECTION "...", ROMX, BANK[$xx]` near the top, or check `layout.link`). Are you in `home.asm` (always paged in) or in some banked section?
2. **What do I need to call?** For each call target: same-bank? `home/`? Or somewhere else?
   - Same bank → plain `call`.
   - In `home/` → plain `call` works from anywhere (home is always paged).
   - Different ROMX bank → **must** be `farcall` / `callfar`.
3. **What do I need to read?** If reading a data table in another bank, you must `push af :: ldh a, [hROMBank] :: push af :: ld a, BANK(Table) :: rst Bankswitch :: ... :: pop af :: rst Bankswitch :: pop af`.
4. **Is the routine documented?** Search:
   - `pokegold/docs/` and `pokegold/docs/bugs_and_glitches.md`
   - `pokecrystal/docs/*.md`, `pokecrystal/STYLE.md`, the Crystal wiki, and `pret.github.io/pokecrystal/`
   - The function header comment (`; Foo: ...`)
5. **Am I in HRAM scope?** If touching `$FF80-$FFFE` symbols, use `ldh`. If declaring HRAM, define in `ram/hram.asm` (constants, not labels — pokegold uses `EQU $FFxx` so `ldh` works).
6. **Do I need to touch VRAM / OAM?** If yes, are you in V-Blank, with LCD off, or queueing into a shadow buffer? Don't poke `$9800` mid-frame.
7. **Banking discipline:** if you change banks inside a routine, restore the previous bank before `ret`. Pattern: `ldh a, [hROMBank] :: push af` … `pop af :: rst Bankswitch`.
8. **Signed math?** If you're doing JR offsets, `add sp,e8`, or `ld hl,sp+e8`, your displacement is signed 8-bit. Otherwise everything is unsigned.
9. **Endianness:** when `dw Label` in memory, low byte is at lower address. Reads that load HL must put L first, H second. Stack push/pop is intuitive.
10. **Charmap:** any `db "..."` is charmap-translated. Double-check the file's charmap context (most data files INCLUDE `constants/charmap.asm` via `includes.asm`).
11. **Macro vs pseudo-op:** prefer macros (`farcall`, `dba`, `text`, `warp_event`) over hand-rolled bytes — they survive opcode-number shifts between G/S and Crystal and they document intent.
12. **Verify with `make compare`:** if you're doing a parity-preserving change, the SHA-1 must still match `roms.sha1`. If you're intentionally diverging, diffing `pokegold.sym` / `pokegold.map` (built with `DEBUG=1`) helps locate displacement.
13. **Don't mix dialects.** No `(hl)`, no `.bank`, no `callba` in new code, no `JP [HL]`, no `LD HL,[SP+e8]`.
14. **Match local style.** Tab indentation, `PascalCase` labels, double-colon for exports, address comments removed (per the pokegold/pokecrystal style migration), capitalize `BANK`/`HIGH`/`LOW`/`DEF`.
15. **If unsure, search Crystal.** Almost any pokegold question — *except* in the few subsystems that genuinely diverged — has a documented answer in the Crystal disassembly. Reuse the implementation pattern, then verify against pokegold's actual file before committing.

---

### Appendix A — Single-line "is this real?" checklist

| Token | Real? |
|---|---|
| `LDIR` | ❌ |
| `LDH` | ✅ |
| `STOP` | ✅ (2 bytes: `$10 $00`) |
| `EX DE,HL` | ❌ |
| `SWAP A` | ✅ |
| `RETN` | ❌ (`RETI` exists) |
| `IM 1` | ❌ |
| `JP HL` | ✅ |
| `JP [HL]` | ⚠ deprecated, RGBDS warns — use `JP HL` |
| `ADD HL, BC/DE/HL/SP` | ✅ |
| `ADC HL, BC` | ❌ |
| `SBC HL, BC` | ❌ |
| `LD HL, SP+e8` | ✅ |
| `LD HL,[SP+e8]` | ⚠ deprecated, use `LD HL, SP+e8` |
| `LD A,(IX+5)` | ❌ |
| `RLD` / `RRD` | ❌ |
| `DJNZ d` | ❌ |
| `JR Z,d` / `JR NZ,d` / `JR C,d` / `JR NC,d` | ✅ (only those four conditions) |
| `JR PE,d` etc. | ❌ |
| `IN A,(C)` / `OUT (C),A` | ❌ |
| `LD A,I` / `LD A,R` | ❌ |
| `BIT 7,(HL)` | ✅ |
| `RES 0,A` / `SET 0,A` | ✅ |
| `CALL NC,nn` | ✅ |
| `RST $40` | ❌ — only `$00,$08,$10,$18,$20,$28,$30,$38` |
| `LD [BC],HL` | ❌ |
| `LD [DE],A` | ✅ |
| `LD [BC],A` | ✅ |
| `LD [HL+],A` / `LD A,[HL-]` | ✅ |
| `EI :: HALT` (with pending IRQ, IME=0) | ⚠ HALT bug; pokegold avoids it |
| Calling a `farcall` target with plain `call` | ❌ silent bank-mismatch bug |
| `db BANK(X) :: dw X` | ✅ — but use `dba X` instead |
| `callba Foo` in new code | ❌ — write `farcall Foo` |
| `ld a, 0` to zero A | ⚠ legal but bigger/slower than `xor a` — match the codebase (`xor a`) |
| `cp 0` to test A | ⚠ same — pokegold uses `and a` |
| `ld [$FF44], a` | ⚠ legal but write `ldh [rLY], a` |

### Appendix B — pokegold-specific facts vs pokecrystal

| Topic | pokegold | pokecrystal |
|---|---|---|
| Cart | MBC3+RAM+BAT+TIMER ($10) | MBC3+RAM+BAT+TIMER ($10); JP Crystal uses MBC30 |
| Build SHA-1 (UE) | `d8b8…cb94` (Gold), `49b1…2dae` (Silver) | `301899b8087289a6436b0a241fbbb474757`-ish (varies by region) |
| Script opcodes $52/$9F | not present | added in Crystal |
| Battle Tower | absent (post-game stub) | present |
| Mobile Adapter | absent | partial (JP) / stubbed (US) |
| Trainer class roster | no MYSTICALMAN/EUSINE | adds MYSTICALMAN, KIMONO_GIRL changes, etc. |
| Time Capsule | present | present (slight differences) |
| GS Ball event | hardcoded for the unreleased event | scripted |
| `data/pokemon/` layout | identical structure | identical structure |
| `audio/engine.asm` | older version | newer macros (Crystal Tracker compatible) |
| `home/farcall.asm` | same shape, slight buffer-name differences (`wFarCallBC` vs `wFarCallBCBuffer`) | |
| Documentation | sparse `docs/` | rich `docs/`, wiki, GitHub Pages |

When in doubt: read the pokegold source, **then** consult pokecrystal as a documentation companion, **then** consult Pan Docs / RGBDS docs. Never the reverse.

---

*End of operating manual. If you finish reading and immediately want to write `LDIR` or `EX DE,HL`, re-read §2.2 and §8.1.*