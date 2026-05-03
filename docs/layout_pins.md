# Layout pins (`layout.link` `org` directives)

Five sections in `layout.link` use explicit `org $XXXX` directives to
pin their contents to specific in-bank addresses. These pins exist for
real reasons (Stadium 2 checksum compatibility, pic-pointer table
addressing, banked-data co-location). Removing or moving any of them
will silently break a downstream consumer.

`tools/audit/check_layout_orgs.py` validates that this set of pins is
intact. If you intend to add, move, or delete a pin, update both this
doc and the audit's expected-pin set in the same change.

## The five pins

### 1. `ROMX $12 / org $4000` — `Pic Pointers` (+ `Pics 1`)

**Source declaration:** `gfx/pics_gold.asm:5` (`SECTION "Pic Pointers", ROMX`).
**What it backs:** `PokemonPicPointers` table, the `(bank << 16 | offset)`
pointer-per-species table consumed by sprite loading.
**Why pinned:** the pointer table starts at the bank base ($4000) so
that `BANK(PokemonPicPointers) << 16 | $4000` is the canonical address
the engine code computes. Moving "Pic Pointers" out of the bank-base
slot would force a recompute of every consumer's offset math.
**What breaks if removed:** silent corruption of every Pokémon front-pic
load — `LowVHigh` math in `home/pic.asm` (and equivalents) would
produce wrong addresses.

### 2. `ROMX $1f / org $4000` — `Unown Pic Pointers` (+ `Pics 12`)

**Source declaration:** `gfx/pics_gold.asm:10` (`SECTION "Unown Pic Pointers", ROMX`).
**What it backs:** `UnownPicPointers` — Unown's variant pointer table.
**Why pinned:** same reason as #1 — bank-base alignment for pointer
arithmetic on a per-bank table.
**What breaks if removed:** Unown sprite loading uses wrong addresses
for some or all letter variants.

### 3. `ROMX $2e / org $6300` — `bank2E` (after `Pics 14`)

**Source declaration:** `main.asm:274` (`SECTION "bank2E", ROMX`).
**What it backs:** non-pic data living in bank 0x2e after the "Pics 14"
section ends.
**Why pinned:** pic data is sized exactly to fill $4000-$62ff; the pin
ensures `bank2E` content begins immediately after, and removing the
pin would let the linker shuffle ordering. The pic data has fixed-size
expectations elsewhere; reordering would break sprite cross-references.
**What breaks if removed:** undefined section ordering, possibly
breaking sprite loads or whatever consumer expects bank2E content at
$6300+.

### 4. `ROMX $31 / org $7a40` — `bank31` (after `Sprites 2`)

**Source declaration:** `main.asm:282` (`SECTION "bank31", ROMX`).
**What it backs:** non-sprite data after the "Sprites 2" section.
**Why pinned:** "Sprites 2" is sized exactly to end at $7a3f; the pin
asserts the boundary so any sprite-size change produces a link error
rather than silently shifting downstream data.
**What breaks if removed:** sprite-size growth could push `bank31`
content into a different address range without a build-time error.

### 5. `ROMX $7f / org $7df8` — `Stadium 2 Checksums` ★

**Source declaration:** `main.asm:417`
(`SECTION "Stadium 2 Checksums", ROMX[$7DF8], BANK[$7F]`).
The section reserves `ds $208` (520 bytes) for the checksum table.
**What it backs:** Pokémon Stadium 2 reads the trainer ROM's content
checksums at fixed ROM offset `0x1ffdf8` (= bank 0x7f × $4000 + $3df8).
The table has the `N64PS3` header (which the Stadium 2 firmware
recognizes).
**Why pinned:** Stadium 2 is external; we cannot change where it reads.
The `tools/stadium` post-build step (Makefile:200) computes and writes
the checksums to this exact ROM offset.
**What breaks if removed:**
- `tools/stadium` post-build step writes to ROM offset 0x1ffdf8 anyway;
  if `Stadium 2 Checksums` doesn't reserve that range, `tools/stadium`
  would either overwrite real ROM data or fail outright.
- Real-hardware Stadium 2 transfer reads garbage and refuses to import.

★ This is the most fragile pin. Stadium 2 hardware/emulator testing is
the only authoritative verification, and it's release-gated. See TD-003
"Updated 2026-05-03" in `tech_debt/TECH_DEBT_REPORT_ADDENDUM.md` for
the full migration discussion.

## Adding, moving, or deleting a pin

1. Decide whether the pin is still needed. Document the new
   contract here.
2. Update `tools/audit/check_layout_orgs.py` `EXPECTED_PINS` to match
   the new pin set.
3. Build (`make pokegold.gbc`) and verify both ROM byte locations and
   downstream consumers (Stadium 2 transfer if pin #5 changed; pic
   loads if pin #1 or #2; the audit script for any change).
4. If you removed pin #5, also remove the `tools/stadium` step in
   `Makefile`.

The audit script's verification floor is **exact match**: any drift
flips it from PASS to FAIL with a side-by-side diff so the reviewer
can decide whether the change was intentional.

## Cross-references

- `tech_debt/TECH_DEBT_REPORT.md` TD-003 — original finding.
- `tech_debt/FIX_PROPOSALS.md` TD-003 — fix path (Option 1: this audit;
  Option 2: this doc; Option 3: relocation, release-gated).
- `tech_debt/TECH_DEBT_REPORT_ADDENDUM.md` — close-out note when
  TD-003 partial advances or fully closes.
- `tools/audit/check_layout_orgs.py` — the audit.
