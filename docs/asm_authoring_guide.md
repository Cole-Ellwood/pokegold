# Z80 / RGBDS Authoring Guide for This ROM

**Audience:** an LLM coding agent about to edit `.asm` files in this
pokegold hack. Read end-to-end before writing a single instruction. If a
fact here conflicts with what you "remember" about the Z80, this doc wins.

This guide is the long-form reference. A SessionStart hook
(`scripts/inject_asm_guide.py`) auto-injects §0 (critical rules), §6
(verification floor), and a TOC of the remaining sections with line
ranges. Read other sections on demand when the work calls for them.
If you find an error in any section, fix the source file and the next
session inherits the fix.

Companion files (treat as authoritative for their domains):
- `CLAUDE.md` — workflow, build, escalation, stat-math source of truth.
- `docs/mechanics_changes_from_base.md` — what this hack changed from
  vanilla GSC.
- `home/`, `macros/` — the helper library. Always grep here before
  rolling your own loop.

## 0) If you only read one section, read this

| You must remember | Why it bites |
| --- | --- |
| The CPU is **Sharp SM83** (a.k.a. LR35902, "GBZ80"). It is **not a Z80.** | No `IX`/`IY`, no shadow regs, no `IN`/`OUT`, no `LDIR`/`CPIR`/`EX`, no `DJNZ`. See §2. |
| **`Label:` is local; `Label::` is exported.** Never silently downgrade `::` to `:`. | Cross-file references fail to link. |
| **Cross-bank calls MUST use `farcall` / `callfar` / `homecall`.** A bare `call` to a label in another ROMX bank silently jumps to whatever is paged in. | The single most common load-bearing mistake. §3.4. |
| **`farcall` clobbers caller's `hl` BEFORE the target runs.** Macro expands to `ld a, BANK :: ld hl, target :: rst FarCall`. | Shipped twice in this repo (April 2026 one-shot damage; May 2026 rival 1 softlock). §3.2. |
| **After `farcall`, caller's `a` = target's exit `c`, NOT target's exit `a`.** See `home/farcall.asm:13-28`. | Shipped May 2026 wild-floor no-op. §3.3. |
| **Memory is little-endian.** `dw Foo` writes `LOW(Foo)` then `HIGH(Foo)`. Pointer-load idiom: `ld a, [hli] :: ld h, [hl] :: ld l, a` — **LO byte first**. | §3.10. |
| **HRAM/IO uses `ldh`, not `ld`.** `ldh [rXX], a` is 2 bytes / 3 cycles vs 3 bytes / 4 for `ld [$FFxx], a`. RGBDS will NOT auto-pick. | Style consistency + size. §1.4. |
| Stat math: **base ≠ computed.** `wBattleMonSpeed` is the computed stat. Stat-stage bytes use **base-7 encoding** (`BASE_STAT_LEVEL = 7 = +0`). | Confusing the two has cost a debug session. CLAUDE.md is source of truth. |
| `ram/` is high-caution. **Reordering or resizing WRAM/SRAM fields silently misaligns old saves; there is no migration code in this repo.** | Save-format bumps shipping to public release require user approval. |
| Save-format change → bump `SAVE_FORMAT_VERSION` and **escalate** to user. | `tools/audit/check_save_format_version.py` enforces. |

## 1) The CPU model

### 1.1 Registers and flags

8-bit: `a` `b` `c` `d` `e` `h` `l` `f` (flags).
16-bit pairs: `af` `bc` `de` `hl` `sp` `pc`.

There is **no** `ix`/`iy`, **no** shadow set (`a'`/`f'`), **no** alternate
register bank.

Only `hl` can dereference arbitrary memory via `[hl]`. `bc` and `de` can
be dereferenced for byte loads to/from `a` only (`ld a, [bc]` / `ld [de], a`
and the matching forms). Everything else goes through `hl`.

Flag register `f` holds, in bits 7..4: **Z** (zero), **N** (subtract),
**H** (half-carry), **C** (carry). Lower 4 bits always read 0.

There is **no P/V (parity/overflow) flag** and **no S (sign) flag**.
Condition codes accepted by `jp` / `jr` / `call` / `ret` are exactly:
`z`, `nz`, `c`, `nc`. Don't write `jp pe, ...`.

### 1.2 The "useful side effect" idiom

Most ALU ops set flags as a side effect; the codebase relies on this:

```asm
ld a, [hl]
and a       ; sets Z if a == 0; clears C
ret z       ; bail if zero
```

`and a` (or `or a`) is a one-byte way to test `a` against zero **and**
clear the carry flag. If you see it and don't know why, that's the answer.

### 1.3 Memory map

| Range | Region | Notes |
| --- | --- | --- |
| `$0000-$3FFF` | ROM bank 0 (fixed) | Always mapped. `home/` and the RST/IRQ vectors live here. |
| `$4000-$7FFF` | ROMX (banked) | Switchable via MBC3. Current bank shadowed in `hROMBank`. |
| `$8000-$9FFF` | VRAM | 2 banks on CGB (`rVBK`). Tile data $8000-$97FF, BG maps $9800-$9FFF. **Inaccessible to CPU during PPU mode 3.** |
| `$A000-$BFFF` | SRAM (or MBC3 RTC reg) | Battery-backed. Must be enabled via `OpenSRAM` / disabled via `CloseSRAM`. |
| `$C000-$CFFF` | WRAM bank 0 (fixed) | |
| `$D000-$DFFF` | WRAMX (banked, CGB) | 7 banks via `rSVBK`. Boss AI lives in bank 1. |
| `$E000-$FDFF` | Echo RAM | Mirrors $C000-$DDFF. Don't use. |
| `$FE00-$FE9F` | OAM | Sprite attributes. Inaccessible during PPU modes 2/3. |
| `$FEA0-$FEFF` | Prohibited | Bizarre real-hardware behavior. |
| `$FF00-$FF7F` | I/O registers | See `constants/hardware.inc`. |
| `$FF80-$FFFE` | HRAM | 127 bytes. Accessible during OAM DMA. |
| `$FFFF` | `rIE` | Interrupt enable mask. |

ROM banks are **`$4000` bytes (16 KiB) each**. Growth past free space is a
link-time failure. Check `Tight Banks` in `docs/generated/dev_index.md`
before adding bytes to a hot bank.

### 1.4 HRAM / IO addressing — use `ldh`

```asm
; RIGHT — 2 bytes, 3 cycles
ldh a, [rLY]              ; rLY = $FF44

; WRONG-ISH — 3 bytes, 4 cycles, identical effect, breaks style
ld a, [$FF44]
```

RGBDS will **not** automatically pick `ldh` for you when the symbol
resolves to `$FFxx`. You must write `ldh` explicitly. This codebase uses
`ldh` consistently for everything in `$FF00-$FFFF`; matching style is
mandatory.

### 1.5 The RST table (this codebase, `home/header.asm`)

| RST | Symbol | Use |
| --- | --- | --- |
| `$00` | `Start` (`di :: jp Start`) | Boot entry. |
| `$08` | `FarCall::` (jumps to `FarCall_hl`) | Far call dispatcher. Used by `farcall` macro. |
| `$10` | `Bankswitch::` | `a` = new ROM bank → write to `[hROMBank]` and `[rROMB]`. |
| `$18` | trap (`rst $38`) | Crash. |
| `$20` | trap (`rst $38`) | Crash. |
| `$28` | `JumpTable::` | Indexed jump-table dispatch. `a` = index, `hl` = `dw` table base. |
| `$30` | (continuation of `$28`) | |
| `$38` | trap | Crash / debug. |

### 1.6 Hardware registers (the ones you'll touch)

Defined in `constants/hardware.inc`. Selected entries:

| Symbol | Addr | Purpose |
| --- | --- | --- |
| `rJOYP` | `$FF00` | Joypad select/read |
| `rDIV` | `$FF04` | Divider (writing resets to 0) |
| `rIF` | `$FF0F` | Pending interrupts |
| `rLCDC` | `$FF40` | LCD control |
| `rSTAT` | `$FF41` | LCD status (PPU mode in low 2 bits) |
| `rLY` | `$FF44` | Current scanline |
| `rDMA` | `$FF46` | OAM DMA source page |
| `rVBK` | `$FF4F` | VRAM bank (CGB) |
| `rSVBK` | `$FF70` | WRAM bank (CGB) |
| `rIE` | `$FFFF` | Interrupt enable |
| `rRAMG` | `$0000` | MBC: RAM/RTC enable (`$0A` = on, `$00` = off) |
| `rROMB` | `$2000` | MBC3: ROM bank select |

### 1.7 MBC3 (this cart)

The cart is **MBC3 + RAM + battery + RTC**. Bank-switching mechanics:

| Write range | Effect |
| --- | --- |
| `$0000-$1FFF` (`rRAMG`) | RAM/RTC enable: `$0A` = on, anything else = off. |
| `$2000-$3FFF` (`rROMB`) | ROM bank select (7 bits). Writing 0 selects bank 1. Banks `$20`/`$40`/`$60` are valid here (unlike MBC1). |
| `$4000-$5FFF` | RAM bank ($00-$03) **or** RTC register select. |
| `$6000-$7FFF` | Latch clock data. Write `$00` then `$01` to freeze RTC. |

The pokegold helper at `home/header.asm:12-15`:

```asm
Bankswitch::
    ldh [hROMBank], a
    ld [rROMB], a   ; rROMB = $2000
    ret
```

Don't bank-switch by writing `[$2000], a` directly — always go through
`rst Bankswitch` so `hROMBank` stays in sync. Other code reads
`hROMBank` to push/pop the current bank. SRAM access goes through
`OpenSRAM` / `CloseSRAM` in `home/sram.asm`.

## 2) What doesn't exist on SM83 (hallucination defense)

If your training corpus suggests these for "Game Boy," it is wrong. RGBDS
will reject them — but only if you notice the error message. The
dangerous case is when you *think* an instruction exists and design
logic around it.

**Real-Z80 instructions that DO NOT exist on SM83:**

```
EX DE,HL          EX AF,AF'         EXX            EX (SP),HL
LDI / LDD / LDIR / LDDR             CPI / CPD / CPIR / CPDR
DJNZ d            JR PE/PO/M/P,d    JP PE/PO/M/P,nn
CALL PE/PO/M/P,nn                   RET PE/PO/M/P
IN A,(n)          IN r,(C)          OUT (n),A      OUT (C),r
LD A,I            LD A,R            LD I,A         LD R,A
IM 0 / IM 1 / IM 2                  RETN
NEG               SBC HL,rr         ADC HL,rr
RLD               RRD               SLL r          (undocumented Z80)
LD (nn),BC/DE/SP via ED prefix      LD BC,(nn)
All IX/IY: LD IX,nn ; ADD IX,rr ; (IX+d) addressing in any form
```

**SM83-only instructions you MUST use:**

```
LDH [n8],A    LDH A,[n8]    LDH [C],A    LDH A,[C]
LD [HL+],A    LD A,[HL+]    LD [HL-],A   LD A,[HL-]
LD HL,SP+e8   LD [nn],SP    ADD SP,e8
SWAP r        STOP          RETI
```

This codebase uses `ld a, [hli]` / `ld a, [hld]` syntax (RGBDS also
accepts `ldi`/`ldd` aliases — match the codebase).

### 2.1 Anti-hallucination quick checks

| Looks plausible (WRONG) | Correct |
| --- | --- |
| `ld a, (hl)` | `ld a, [hl]` (RGBDS uses square brackets) |
| `ld bc, (de)` | not legal — only `bc`/`de` indirect, only with `a` |
| `djnz .loop` | `dec b :: jr nz, .loop` (two instructions) |
| `ex de, hl` | `push de :: pop hl :: ...` or use a temp |
| `ldir` (block copy) | `call CopyBytes` (see `home/copy.asm`) |
| `in a, ($00)` | `ldh a, [rJOYP]` |
| `jp (hl)` | `jp hl` (RGBDS warns on `[hl]` form) |
| `ld hl, [sp+4]` | `ld hl, sp+4` |
| `out ($46), a` | `ldh [rDMA], a` |
| `cp 0` | `and a` (1 byte vs 2, sets Z the same) |
| `ld a, 0` | `xor a` (1 byte / 1 cycle — codebase idiom) |
| `add hl, a` | `ld c, a :: ld b, 0 :: add hl, bc` |
| `adc hl, bc` | doesn't exist — decompose by byte |

## 3) Common mistakes (ranked by how often models make them)

### 3.1 Confusing `Label:` with `Label::`

**Symptom:** linker error `Unknown symbol "Foo"` from a different file.

```asm
; WRONG — silently downgraded :: to :
MyHelper:
    ret

; in another bank:
    farcall MyHelper    ; LINK ERROR: MyHelper not exported
```

```asm
; RIGHT
MyHelper::
    ret
```

Single colon = file-local. Double colon = exported. If anything outside
the source file references the label, it must be `::`.

### 3.2 The `farcall` `hl` clobber

**This bug has shipped twice in this repo** (April 2026 one-shot damage;
May 2026 rival 1 softlock). The single most expensive Z80 mistake an LLM
makes here. From `macros/farcall.asm:7-11`:

```asm
MACRO farcall ; bank, address
    ld a, BANK(\1)
    ld hl, \1            ; <-- clobbers caller's hl BEFORE the call
    rst FarCall
ENDM
```

So:

```asm
; WRONG — TargetFn reads hl as input
    ld hl, MyDataTable
    farcall TargetFn      ; hl is garbage by the time TargetFn runs
```

Three valid patterns, in order of preference:

```asm
; (1) RIGHT — push/pop if hl just needs to survive the call
    ld hl, MyDataTable
    push hl
    farcall TargetFn
    pop hl
```

```asm
; (2) RIGHT — homecall via a HOME thunk (preserves hl)
; In home/foo.asm:
TargetFn_Conv::
    homecall TargetFn
    ret
; In caller:
    ld hl, MyDataTable
    call TargetFn_Conv
```

```asm
; (3) RIGHT — pass hl through bc or de, reconstruct inside
    ld b, h
    ld c, l
    farcall TargetFn      ; TargetFn does ld h, b / ld l, c at entry
```

### 3.3 The `farcall` return-`a` clobber

**Same shape, different victim.** From `home/farcall.asm:13-28`:

```asm
; ... after the inner call returns ...
    ld a, b
    ld [wFarCallBC], a
    ld a, c
    ld [wFarCallBC + 1], a
    ; ... bank restore ...
    ld a, [wFarCallBC]
    ld b, a
    ld a, [wFarCallBC + 1]
    ld c, a
    ret
```

Read it carefully: after `farcall`, the caller's `a` ends up holding the
**target's exit `c`**, not the target's exit `a`. The May 2026 wild-floor
no-op was caused by `farcall GetProgressionLevelCap` reading `target_c`
when it expected `target_a`.

```asm
; WRONG
    farcall GetProgressionLevelCap
    cp 30                 ; reading target's c, not its a
```

```asm
; RIGHT — option A: mirror a into c at every ret in the target
GetProgressionLevelCap::
    ; ... compute cap in a ...
    ld c, a
    ret
    ; (do this at EVERY ret in this function)
```

```asm
; RIGHT — option B: stash to HRAM and read back
    farcall TargetFn      ; target writes to hSomeResult
    ldh a, [hSomeResult]
```

For new cross-bank functions returning a value in `a`, default to option
A — one `ld c, a` per ret.

### 3.4 Plain `call` to a label in another bank

```asm
; WRONG — assembles, jumps to garbage
    call SomeLabelInAnotherBank
```

`call` only reaches the current bank or ROM0. The linker can't catch
this because it can't predict which bank you'll be sitting in.

If the target is in another bank, use `farcall`. If the target is in
ROM0 (anything in `home/`), plain `call` is fine.

### 3.5 Confusing base stat with computed stat

`wBattleMonSpeed` / `wEnemyMonSpeed` are **computed** values, not base
stats. Stat-stage values like `wEnemySpdLevel` use **base-7 encoding**:
`BASE_STAT_LEVEL = 7 = +0`, `MAX_STAT_LEVEL = 13 = +6`. Don't read the
byte as the multiplier. CLAUDE.md `Stat math` section is the source of
truth; the failure mode is real and has cost debug sessions.

### 3.6 Mixing assembler dialects

This codebase uses **RGBDS** syntax. Don't paste WLA-DX or ASMotor.

| Feature | RGBDS (this repo) | WLA-DX (don't use) |
| --- | --- | --- |
| Memory indirection | `[hl]`, `[$ff80]` | `(hl)`, `($FF80)` |
| Section start | `SECTION "X", ROM0` | `.bank 0 .org $0150` |
| Constant | `DEF NAME EQU 1` | `.def NAME 1` |
| Macro | `MACRO foo ... ENDM` | `.macro foo` |
| Bank-of | `BANK(label)` | `:label` |

Most dangerous: `(hl)` parses as a parenthesized expression in RGBDS,
not memory access — **silent miscompile**.

### 3.7 Reordering or resizing WRAM/SRAM fields

Save format is byte-positional. Adding a field in the middle of a struct
in `ram/wram.asm`, or growing one, silently misaligns every old save.
`SAVE_FORMAT_VERSION` exists but **no migration code exists in the
repo**. If your change reaches `ram/`, bump the version and escalate to
the user before shipping to public release. See
`tools/audit/check_save_format_version.py`.

WRAMX bank 1 is also reserved for boss AI with a fixed budget. Adding
bytes there without checking `Boss AI WRAM Reserve` in
`docs/generated/dev_index.md` will trip
`check_boss_ai_memory_budget.py`.

### 3.8 Deleting `assert` lines to make the build pass

```asm
; in a table file:
    assert_table_length NUM_POKEMON
```

If this fires, your table count drifted. **Fix the table**, don't delete
the assert. The asserts are the only thing standing between you and a
silently misaligned data structure that ships.

### 3.9 Spending an `ld` where the previous instruction did the work

```asm
; WRONG — verbose
    ld a, [hl]
    cp 0
    jr z, .done
```

```asm
; RIGHT — cp 0 is a no-op for flags; "and a" is one byte cheaper
    ld a, [hl]
    and a
    jr z, .done
```

These don't break anything but they're tells that the model isn't
modeling flag side effects correctly — which is also what causes the
dangerous bugs. Treat them as a smell.

### 3.10 Endianness when loading pointers from memory

`dw Foo` in memory is `LOW(Foo), HIGH(Foo)` (low byte at lower address).

```asm
; RIGHT — HL ← *(HL)
    ld a, [hli]       ; A = LOW
    ld h, [hl]        ; H = HIGH
    ld l, a           ; L = LOW

; WRONG — puts HIGH(Foo) into L
    ld l, [hl]
    inc hl
    ld h, [hl]
```

`push hl` / `pop hl` does the intuitive thing — H first, then L on the
stack. The asymmetry is only when reading a 16-bit value from arbitrary
memory through `hl`.

### 3.11 Hand-rolling something `home/` already provides

`home/` has small, well-named helpers for almost every common operation:

| Need | Helper | File |
| --- | --- | --- |
| Copy `bc` bytes from `hl` to `de` | `CopyBytes` | `home/copy.asm` |
| Fill `bc` bytes at `hl` with `a` | `ByteFill` | `home/copy.asm` |
| Compare `c` bytes at `de` and `hl` | `CompareBytes` | `home/compare.asm` |
| Read one byte from `a:hl` (any bank) | `GetFarByte` | `home/copy.asm` |
| Read a halfword from `a:hl` | `GetFarWord` | `home/copy.asm` |
| Random byte 0..255 | `Random` | `home/random.asm` |
| Random byte 0..N-1 | `RandomRange` | `home/random.asm` |
| Battle-deterministic random | `BattleRandom` | `home/random.asm` |
| `a * c` | `SimpleMultiply` | `home/math.asm` |
| `a / c`, remainder in `a` | `SimpleDivide` | `home/math.asm` |
| Set/reset/check a flag in a flag array | `FlagAction` | `home/flag.asm` |
| Open SRAM (enable + bank-switch) | `OpenSRAM` | `home/sram.asm` |
| Close SRAM (disable) | `CloseSRAM` | `home/sram.asm` |

Before writing a loop, grep `home/` for the operation. Reinventing them
is how you ship a bug.

### 3.12 Case-sensitive `INCLUDE` paths

```asm
; WRONG — Windows-tolerant; Linux/WSL build will fail
INCLUDE "Data/Moves/Effects.asm"
```

```asm
; RIGHT
INCLUDE "data/moves/effects.asm"
```

The build runs through WSL (CLAUDE.md). Lowercase, real paths.

## 4) Best practices used in this codebase

### 4.1 Document register inputs and outputs at the function header

```asm
FlagAction::
; Perform action b on bit de in flag array hl.
;
; inputs:
; b: function (0=RESET, 1=SET, 2=CHECK)
; de: bit number
; hl: pointer to the flag array
```

When you add a function that takes register inputs, write the contract.
This is the only way callers can use it correctly.

### 4.2 Push/pop in opposite order, factor through `.done`

```asm
RaiseWildLevelForProgression:
    push af
    push de
    push hl
    ; ... body ...
.done
    pop hl
    pop de
    pop af
    ret
```

Stack is LIFO. Pops mirror pushes in reverse order. Most "stack balance"
bugs come from forgetting one branch returns early without popping —
factor pops into a single `.done` joiner so all paths converge.

### 4.3 `jr` for short, `jp` for long

`jr` is two bytes, range ±127 from PC. `jp` is three bytes, unlimited
within bank. The assembler will **not** fall back from `jr` to `jp` for
you — out-of-range `jr` is a build error. Default to `jr` inside a
function and `jp` between top-level routines.

### 4.4 Branch on the rare case, fall through on the common case

```asm
    and a
    jr z, .zero      ; rare path branches
    ; common path falls through
    ret
.zero
    ret
```

Fall-through is one byte cheaper than the jump and easier to read.

### 4.5 Symmetric data tables: `table_width` + `assert_table_length`

```asm
table_width 4, MyTable
MyTable:
    db 1, 2, 3, 4
    db 5, 6, 7, 8
    db 9, $A, $B, $C
    assert_table_length 3
```

If you add or remove a row, the assert keeps the indexing math honest.
Use this for any table whose length is referenced by code or by another
table.

### 4.6 Bank-switch idiom: save, switch, work, restore

```asm
    ldh a, [hROMBank]
    push af
    ld a, BANK(SomeData)
    rst Bankswitch
    ; ... do work in the new bank ...
    pop af
    rst Bankswitch
```

`hROMBank` is HRAM that shadows the current ROM bank. Bank-switch
helpers maintain it. **Bypassing them desyncs the shadow** and breaks
subsequent `farcall`s. Don't write to `rROMB` directly; use `rst
Bankswitch`.

`homecall` (`macros/farcall.asm:19-27`) is the one-line wrapper for this
pattern when you're in ROM0 calling another bank. Use it.

### 4.7 Trust the helpers; protect what you care about across calls

`Random` preserves `bc`. `BattleRandom` preserves only what its header
documents. **Always assume a `call` clobbers everything except what its
header explicitly promises.** If you need a register to survive a call
you didn't write, push it first.

### 4.8 VRAM, OAM, LCD timing rules

- **VRAM** (`$8000-$9FFF`): inaccessible during PPU mode 3. Writes drop;
  reads return `$FF`. By convention this codebase only writes VRAM
  during V-Blank or with the LCD off.
- **OAM** (`$FE00-$FE9F`): inaccessible during modes 2 and 3. Update via
  shadow OAM in WRAM and let the per-frame DMA copy flush it. Don't
  write OAM directly mid-frame.
- **Don't disable the LCD outside V-Blank** — Pan Docs warns this can
  damage real hardware. Code that turns the LCD off must wait for `rLY
  >= 144` first.
- During OAM DMA, on DMG **the CPU can only execute from HRAM** — that's
  why the DMA-trigger routine is copied to HRAM at init and run from
  there.

## 5) Cookbook — copy these patterns

### 5.1 Test which side is on turn / pick the defender's struct

```asm
; "attacker's turn picks the defender's struct" — see
; engine/battle/move_effects/spikes.asm:1-7
    ld hl, wEnemyScreens
    ldh a, [hBattleTurn]
    and a
    jr z, .got_screens
    ld hl, wPlayerScreens
.got_screens
```

### 5.2 Read a per-species byte from a pointer table

```asm
; species in a, table base in hl, returns byte in a
    ld c, a
    ld b, 0
    add hl, bc
    ld a, [hl]
```

For a two-byte-wide table, `add hl, bc` twice. For a pointer table, two
adds and then the canonical pointer-load (§3.10).

### 5.3 Loop `n` times with `b`

```asm
    ld b, 6        ; loop 6 times
.loop
    ; ... body ...
    dec b
    jr nz, .loop
```

For 16-bit loops use `bc` and the `ld a, b :: or c :: jr nz, .loop`
test — `dec bc` doesn't set Z. See `home/copy.asm:14-15` for the
`inc b :: inc c` trick that handles boundary cases for `bc`-counted
loops.

### 5.4 Rejection sampling for bounded random

```asm
; pick 0..25 inclusive — from macros/code.asm:31-43
.loop
    call Random
    maskbits 26
    cp 26
    jr nc, .loop
    ; a is now in [0, 25]
```

Don't roll your own `Random mod N` — use `RandomRange` (0..N-1) or this
`maskbits` idiom for power-of-two-aligned ranges.

### 5.5 Conditional negation (absolute value)

```asm
; from home/math.asm:51-58
SubtractAbsolute::
; Return |a - b|, sign in carry.
    sub b
    ret nc
    cpl
    add 1
    scf
    ret
```

`cpl` flips every bit (one's complement); `add 1` makes it two's
complement. Canonical "negate `a`" sequence.

### 5.6 Jump-table dispatch via the `JumpTable` macro

```asm
; from macros/code.asm:13-24
MACRO jumptable
    ld a, [\2]
    ld e, a
    ld d, 0
    ld hl, \1
    add hl, de
    add hl, de
    ld a, [hli]
    ld h, [hl]
    ld l, a
    jp hl
ENDM

; usage:
    jumptable .Pointers, wState
.Pointers:
    dw .state_zero
    dw .state_one
    dw .state_two
```

For dispatching from `a` directly (without a state byte), use `rst
JumpTable` (`$28`) — `home/header.asm:24` — which expects `a` = index,
`hl` = `dw` table base. Adding a state always means add the pointer
**and** any size-keyed `assert`.

### 5.7 Text data and printing

Charmap is **active at assembly time**: every `db "..."` is translated
through `constants/charmap.asm` the moment it's parsed.

```asm
; data/text/foo.asm style — use the macros, not raw bytes
HelloText::
    text "Hi, this is text!"
    line "Second visible line."
    cont "Third (scroll arrow)."
    para "New paragraph."
    done

; call site:
    ld hl, HelloText
    call PrintText
```

Selected charmap entries (verified from `constants/charmap.asm`):

| Source | Byte | Behavior |
| --- | --- | --- |
| `"@"` | `$50` | string terminator (NOT the at-sign character) |
| `"<MOM>"` | `$49` | mom's name |
| `"<PKMN>"` | `$4a` | "PK" + "MN" tiles |
| `"<NEXT>"` | `$4e` | move down a line |
| `"<LINE>"` | `$4f` | move to next line |
| `"<PARA>"` | `$51` | new textbox (paragraph) |
| `"<PLAYER>"` | `$52` | replaced with `wPlayerName` |
| `"<RIVAL>"` | `$53` | replaced with `wRivalName` |
| `"<CONT>"` | `$55` | scroll arrow + scroll |
| `"<POKE>"` | `$24` | "POKé" tiles |
| `"#"` | `$54` | "POKé" |

Pitfalls:
- Don't include literal `'@'` in dialog — it's the string terminator,
  not the glyph. There is no `@` glyph in the GS charmap.
- Don't insert `\n` — the GB text engine has no concept of `\n`. Use
  `line` / `next` / `cont` / `para` macros.
- The textbox is 18 characters wide. The text engine does not wrap.
- `<PLAYER>` etc. are dynamic; they read live from WRAM at print time.

### 5.8 Trainer party data (`data/trainers/parties.asm`)

```asm
FalknerGroup:
    ; FALKNER (1)
    db "FALKNER@", TRAINERTYPE_MOVES
    db 7, PIDGEY,    TACKLE, MUD_SLAP, NO_MOVE, NO_MOVE
    db 9, PIDGEOTTO, TACKLE, MUD_SLAP, GUST,    NO_MOVE
    db -1
```

| TRAINERTYPE | Per-mon byte format |
| --- | --- |
| `TRAINERTYPE_NORMAL` | `level, species` |
| `TRAINERTYPE_MOVES` | `level, species, m1, m2, m3, m4` |
| `TRAINERTYPE_ITEM` | `level, species, item` |
| `TRAINERTYPE_ITEM_MOVES` | `level, species, item, m1, m2, m3, m4` |

Constants in `constants/trainer_data_constants.asm`. Roster terminator
is `db -1` — don't omit.

### 5.9 Base stats record (`data/pokemon/base_stats/<name>.asm`)

Verified shape from `data/pokemon/base_stats/bulbasaur.asm`:

```asm
    db BULBASAUR ; 001
    db  45,  49,  49,  45,  65,  65 ; hp atk def spd sat sdf
    db GRASS, POISON                ; type
    db 45                           ; catch rate
    db 64                           ; base exp
    db NO_ITEM, NO_ITEM             ; held items
    db GENDER_F12_5                 ; gender ratio
    db 100                          ; unknown 1
    db 20                           ; step cycles to hatch
    db 5                            ; unknown 2
IF DEF(_GOLD)
    INCBIN "gfx/pokemon/bulbasaur/front_gold.dimensions"
ELIF DEF(_SILVER)
    INCBIN "gfx/pokemon/bulbasaur/front_silver.dimensions"
ENDC
    dw NULL, NULL                   ; unused (beta front/back pics)
    db GROWTH_MEDIUM_SLOW           ; growth rate
    dn EGG_MONSTER, EGG_PLANT       ; egg groups (`dn` packs to one byte)
    tmhm CUT, HEADBUTT, ...         ; tmhm macro packs into bytes
```

Order, field count, and macro choice are all enforced by
`assert_table_length` downstream. Don't reorder fields.

### 5.10 Far-call data table (cross-bank pointers)

```asm
; data/pokemon/evos_attacks_pointers.asm style
EvosAttacksPointers::
    table_width 2, EvosAttacksPointers
    dw BulbasaurEvosAttacks
    dw IvysaurEvosAttacks
    ; ...

; If entries cross banks, switch to dba:
SomeCrossBankTable::
    table_width 3, SomeCrossBankTable
    dba RoutineInBank3
    dba RoutineInBank7
```

`dba Label` expands to `db BANK(Label) :: dw Label`. Other useful data
macros in `macros/data.asm`: `dab`, `dbw`, `dwb`, `dn` (nybbles), `dba`.
Always written in caps in modern style: `BANK(...)`, `LOW(...)`,
`HIGH(...)`, `DEF`.

## 6) Verification floor

Before reporting "asm change done":

1. Build (CLAUDE.md `Build & verification` for the exact incantation).
2. Run the relevant `tools/audit/check_*.py`. Minimum set:
   - `check_release_smoke.py` always.
   - `check_navigation_floor.py` if you touched docs.
   - `check_boss_ai_*.py` if you touched `engine/battle/ai/`.
   - `check_save_format_version.py` if you touched `ram/`.
3. Regenerate `docs/generated/dev_index.md` after **any** successful
   build (`python scripts/generate_dev_index.py --rom pokegold`).
4. If you touched balance tables, regenerate
   `docs/generated/balance_audit.md`.
5. For parity-preserving changes, `make compare` must still match
   `roms.sha1` (`d8b8a3600a465308c9953dfa04f0081c05bdcb94` for Gold UE,
   `49b163f7e57702bc939d642a18f591de55d92dae` for Silver UE).

A green build proves "it links," not "it works." The audits are the
floor.

## 7) When you're stuck

In order:

1. Grep `home/` and `engine/` for an existing routine that does what
   you're trying to do. Almost always it exists.
2. Read the function header comment of the closest existing analogue.
3. Read **how callers use it** (grep for the label name) to learn the
   register contract empirically.
4. Re-read CLAUDE.md — half the answers live there.
5. **Search pokecrystal** — Crystal shares >95% of subsystem code with
   pokegold and has far richer docs. Reuse pokecrystal patterns
   (text engine, charmap, scripting commands, battle flow, base stats
   layout, audio engine, banking helpers) freely. Verify against
   pokegold source before applying. Diverged subsystems: anything added
   in Crystal (Battle Tower, Mobile Adapter, GS Ball event, Suicune
   scripting, Crystal-only NPCs/maps).
6. Ask the user. He has gameplay taste, not z80 fluency, but he can
   tell you which existing system is the analogue you should be copying.

## Appendix A — RGBDS-isms glossary

- `\1`, `\2`, ... — macro arguments. `\@` is a unique suffix per
  expansion (use it for local labels inside macros).
- `db` / `dw` / `dl` — data byte / data word (2 bytes, little-endian) /
  data long (4 bytes).
- `ds N` — reserve N bytes. `ds N, $ff` — reserve and fill.
- `BANK(label)` — the bank the symbol lives in, resolved at link time.
- `LOW(x)`, `HIGH(x)` — extract low / high byte of a 16-bit value.
- `@` — current PC inside a section. `@ - LabelStart` measures size.
- `rept N ... endr` — repeat block N times.
- `if / elif / else / endc` — conditional assembly. Whole blocks vanish
  when the condition is false. Used heavily for `_GOLD` / `_SILVER`
  variants.
- `DEF X = ...` / `DEF X EQUS "..."` — numeric / string equate. `REDEF`
  to overwrite, `PURGE` to remove.
- `assert <expr>, "msg"` — link-time check. Build fails with `msg` if
  `<expr>` is false. Don't delete; fix the cause.
- `SECTION "Name", ROM0` — fixed bank 0. `ROMX` — any non-zero bank.
  `ROMX, BANK[$04]` — pinned bank. `WRAM0`, `WRAMX, BANK[1]`, `SRAM,
  BANK[0]`, `HRAM` — RAM regions.
- `SECTION FRAGMENT "Name", ROMX` — concatenable across files.
- `SECTION UNION "Name", WRAM0` — overlay (multiple defs at the same
  address).
- `MACRO foo ... ENDM` — macro definition.
- `INCLUDE "path"`, `INCBIN "path"` — text include (asm) / binary
  include.

## Appendix B — "Is this real?" instruction lookup

Quick reference for "does this exist on SM83?" Use when in doubt.

| Token | Real? |
| --- | --- |
| `LDIR` | NO |
| `LDH` | YES |
| `STOP` | YES (2 bytes: `$10 $00`) |
| `EX DE,HL` | NO |
| `EXX` | NO |
| `SWAP A` | YES |
| `RETN` | NO (`RETI` exists) |
| `IM 1` | NO |
| `JP HL` | YES |
| `JP [HL]` | DEPRECATED — RGBDS warns; use `JP HL` |
| `ADD HL, BC/DE/HL/SP` | YES |
| `ADC HL, BC` | NO |
| `SBC HL, BC` | NO |
| `LD HL, SP+e8` | YES |
| `LD HL, [SP+e8]` | DEPRECATED — use `LD HL, SP+e8` |
| `LD A, (IX+5)` | NO (no IX/IY at all) |
| `RLD` / `RRD` | NO |
| `DJNZ d` | NO |
| `JR Z/NZ/C/NC, d` | YES (only those four) |
| `JR PE,d` etc. | NO |
| `IN A,(C)` / `OUT (C),A` | NO |
| `LD A,I` / `LD A,R` | NO |
| `BIT 7, [HL]` | YES |
| `RES 0, A` / `SET 0, A` | YES |
| `CALL NC, nn` | YES |
| `RST $40` | NO (only `$00,$08,$10,$18,$20,$28,$30,$38`) |
| `LD [BC], HL` | NO |
| `LD [DE], A` | YES |
| `LD [BC], A` | YES |
| `LD [HL+], A` / `LD A, [HL-]` | YES |
| `EI :: HALT` (with pending IRQ, IME=0) | HALT bug — this codebase avoids |
| Calling a `farcall` target with plain `call` | NO — silent bank-mismatch bug |
| `db BANK(X) :: dw X` | YES — but use `dba X` instead |
| `callba Foo` in new code | NO — write `farcall Foo` |
| `ld a, 0` to zero A | LEGAL but bigger/slower than `xor a` |
| `cp 0` to test A | LEGAL but pokegold uses `and a` |
| `ld [$FF44], a` | LEGAL but write `ldh [rLY], a` |

## Appendix C — Out of scope for this guide

Patterns specialized enough that you should read existing code first
rather than apply general rules:

- **Audio engine** — its own bytecode DSL on top of asm. See `audio/`,
  `engine/audio.asm`, and pokecrystal's `docs/music_commands.md`.
- **Map scripting** — bytecode VM with its own macros in
  `macros/scripts/events.asm`. Read existing maps in `maps/` and copy.
  Opcode numbering differs between G/S and Crystal — always use macro
  names, never raw `db` opcodes.
- **Graphics / palette pipeline** — `home/gfx.asm`, `home/palettes.asm`,
  `gfx/`. Specialized; ask the user before refactoring.
- **Boss AI architecture** — see `docs/boss_ai_spec.md` and
  `engine/battle/ai/boss.asm`. Read those before touching that code.

If you finish reading and immediately want to write `LDIR` or `EX DE,HL`,
re-read §2.
