; Compact exact floor(W*h/M) tables. Construction uses W threshold events,
; plus at most M+1 direct entries or floor(M/8)+1 rank blocks. No HP division
; occurs in a lookup. Only the private reference build includes these routines.
DEF FHP_DIRECT EQU 0
DEF FHP_RANK8 EQU 1
DEF FHP_THRESHOLDS EQU 2
; Construction owns the arithmetic workspace before any live accumulation.
DEF FHP_MAX EQU FS_MATH
DEF FHP_WEIGHT EQU FS_MATH + 2
DEF FHP_MODE EQU FS_MATH + 3
DEF FHP_BASE EQU FS_MATH + 4
DEF FHP_QUOTIENT EQU FS_MATH + 6
DEF FHP_STEP_REM EQU FS_MATH + 8
DEF FHP_ACC_REM EQU FS_MATH + 9
DEF FHP_NEXT EQU FS_MATH + 10
DEF FHP_RANK EQU FS_MATH + 12

; Construction runs once per defender: it lives in its own aligned section
; behind far entries, with the mask table it indexes, so the hot
; fast-prototype bank keeps its space. The lookups further down stay hot.
PUSHS
SECTION "Boss AI Fast HP Tables", ROMX, ALIGN[8]
INCLUDE "engine/battle/ai/fast_hp_masks.asm"

BossAI_FastBuildOwnHPTableFar::
; farcall entry for the own reservation: BC=max HP, weight from FSA_WEIGHT.
; The far return leaves A=mode (mirrored through C) and carry as below.
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastBuildHPTable
	ld c, a
	ret
BossAI_FastBuildPlayerHPTableFar::
; farcall entry for the player reservation (weight 128), same outputs.
	ld a, 128
	ld hl, $a180
	call BossAI_FastBuildHPTable
	ld c, a
	ret

BossAI_FastBuildHPTable::
; HL=$a000 owned reservation or $a180 player reservation. BC=max HP (>0).
; A=weight: owned 128/192, player 128. SRAM bank0 open. DE preserved.
; Carry=success, A=mode (0 direct, 1 rank8, 2 thresholds); invalid inputs
; return A=$ff/carry clear without table writes. Math workspace is scratch.
	push de
	ld d, a
	ld a, b
	or c
	jp z, .reject
	ld a, h
	cp $a0
	jr z, .own
	cp $a1
	jp nz, .reject
	ld a, l
	cp $80
	jp nz, .reject
	ld a, d
	cp 128
	jp nz, .reject
	jr .accepted
.own
	ld a, l
	and a
	jp nz, .reject
	ld a, d
	cp 128
	jr z, .accepted
	cp 192
	jp nz, .reject
.accepted
	ld a, d
	ld [FHP_WEIGHT], a
	ld a, b
	ld [FHP_MAX], a
	ld a, c
	ld [FHP_MAX + 1], a
	ld a, h
	ld [FHP_BASE], a
	ld a, l
	ld [FHP_BASE + 1], a
	ld a, b
	and a
	jr nz, .larger
	ld a, c
	cp d
	ld a, FHP_DIRECT
	jr c, .mode
.larger
; Direct mode is restricted to M<W; rank8 uses the complete reservation.
	ld a, l
	and a
	ld a, 6 ; owned rank8: M<1536
	jr z, .rank_limit
	ld a, 4 ; player rank8: M<1024
.rank_limit
	cp b
	ld a, FHP_RANK8
	jr nz, .rank_compare
	ld a, FHP_THRESHOLDS
	jr .mode
.rank_compare
	jr nc, .mode
	ld a, FHP_THRESHOLDS
.mode
	ld [FHP_MODE], a
; q,r = divmod(M,W). Threshold k is ceil(k*M/W). Starting the accumulated
; remainder at W-1 makes each q/r step produce that ceiling, including M<W.
	xor a
	ld [FS_DIVIDEND], a
	ld [FS_DIVISOR], a
	ld a, b
	ld [FS_DIVIDEND + 1], a
	ld a, c
	ld [FS_DIVIDEND + 2], a
	ld a, d
	ld [FS_DIVISOR + 1], a
	farcall BossAI_FastDivide24By16 ; memory operands; BC and carry survive the far return
	ld a, c
	ld [FHP_STEP_REM], a
	ld a, [FS_DIVIDEND + 1]
	ld [FHP_QUOTIENT], a
	ld a, [FS_DIVIDEND + 2]
	ld [FHP_QUOTIENT + 1], a
	ld a, [FHP_WEIGHT]
	dec a
	ld [FHP_ACC_REM], a
	xor a
	ld [FHP_NEXT], a
	ld [FHP_NEXT + 1], a
	ld [FHP_RANK], a
	ld a, [FHP_BASE]
	ld d, a
	ld a, [FHP_BASE + 1]
	ld e, a
	ld a, [FHP_MODE]
	cp FHP_RANK8
	jr z, .rank_dispatch
	call .NextThreshold
	ld a, [FHP_MODE]
	cp FHP_THRESHOLDS
	jr z, .threshold_table
.direct_table
	ld h, d
	ld l, e
	ld a, [FHP_MAX + 1]
	ld b, a
	ld c, a
	ld a, [FHP_WEIGHT]
	cp 128
	jr z, .direct128
	call BossAI_FastBuildHPDirect192
	jr .done
.direct128
	call BossAI_FastBuildHPDirect128
	jr .done
.threshold_table
	ld a, [FHP_NEXT]
	ld [de], a
	inc de
	ld a, [FHP_NEXT + 1]
	ld [de], a
	inc de
	call .ConsumeThreshold
	jr c, .threshold_table
	jr .done
.rank_dispatch
; The rank domain has a byte quotient and unique thresholds. Keep its event
; stream in registers; generic descriptor traffic costs too much per event.
	ld a, e
	and a
	jr nz, .rank_player
	ld a, [FHP_WEIGHT]
	cp 128
	jr z, .rank_own128
	call BossAI_FastBuildHPRankOwn192
	jr .done
.rank_own128
	call BossAI_FastBuildHPRankOwn128
	jr .done
.rank_player
	call BossAI_FastBuildHPRankPlayer128
.done
	ld a, [FHP_MODE]
	pop de
	scf
	ret
.reject
	ld a, $ff
	pop de
	and a
	ret

.HasThreshold
	ld a, [FHP_WEIGHT]
	ld b, a
	ld a, [FHP_RANK]
	cp b
	ret

.ConsumeThreshold
	ld hl, FHP_RANK
	inc [hl]
	call .HasThreshold
	ret nc
	call .NextThreshold
	scf
	ret

.NextThreshold
; Only called for the W valid thresholds. No M+q overflow after the last.
	ld a, [FHP_QUOTIENT]
	ld b, a
	ld a, [FHP_QUOTIENT + 1]
	ld c, a
	ld a, [FHP_STEP_REM]
	ld hl, FHP_ACC_REM
	add [hl]
	jr c, .remainder_wrap
	ld hl, FHP_WEIGHT
	cp [hl]
	jr c, .remainder_ready
.remainder_wrap
	ld hl, FHP_WEIGHT
	sub [hl] ; a carried byte sum subtracts W modulo256, yielding exact <W
	inc bc
.remainder_ready
	ld [FHP_ACC_REM], a
	ld a, [FHP_NEXT]
	ld h, a
	ld a, [FHP_NEXT + 1]
	ld l, a
	add hl, bc
	ld a, h
	ld [FHP_NEXT], a
	ld a, l
	ld [FHP_NEXT + 1], a
	ret

MACRO fhp_direct_kernel
; B=max (1..W-1), C=remaining HP entries, HL=table. D=fraction, E=remainder.
	ld de, 0
	xor a
	ld [hl], a
.next
	ld a, e
	add \1
	jr c, .subtract
	cp b
	jr c, .store
.subtract
	sub b
	inc d
	cp b
	jr nc, .subtract
.store
	ld e, a
	inc hl
	ld [hl], d
	dec c
	jr nz, .next
	ret
ENDM

BossAI_FastBuildHPDirect128:
	fhp_direct_kernel 128
BossAI_FastBuildHPDirect192:
	fhp_direct_kernel 192
PURGE fhp_direct_kernel

; Specialized rank construction: HL=next threshold, B=rank, C=remainder,
; DE=current block's output pointer. Each event flushes only intervening
; blocks, then changes either the destination block base or its mask.
; This owns the same construction scratch and never materializes a second table.
MACRO fhp_rank_kernel
	ld hl, 0
	ld b, 0
if \1 == 128
	ld c, 254 ; twice the remainder: carry from addition is the /128 wrap
else
	ld c, 191
endc
	xor a
	ld [de], a
	inc de
	ld [de], a
	dec de
.next
	ld a, [FHP_STEP_REM]
if \1 == 128
	add a ; add doubled remainders; carry is the exact threshold extra unit
	add c
	ld c, a
else
	add c
	jr c, .wrap
	cp 192
	jr c, .no_wrap
.wrap
	sub 192
	ld c, a
	scf
	jr .step
.no_wrap
	ld c, a
	and a
.step
endc
	ld a, [FHP_QUOTIENT + 1]
	adc l
	ld l, a
	jr nc, .threshold_ready
	inc h
.threshold_ready
	push hl ; threshold
	srl h
	rr l
	srl h
	rr l
	res 0, l
if \2 == $a180
	ld a, l
	add $80
	ld l, a
endc
; Only the target pointer's low byte is needed. In the rank domain the next
; threshold advances by at most12HP, hence by at most4table bytes. Current and
; target block addresses can never differ by256, even across a page boundary.
.blocks
	ld a, e
	cp l
	jr z, .event
.advance_block
	inc de
	inc de
	ld a, b
	ld [de], a
	inc de
	xor a
	ld [de], a
	dec de
	jr .blocks
.event
	pop hl ; threshold, rank/remainder still in BC
	inc b
	ld a, l
	and 7
	jr z, .block_start
	push hl
	ld h, HIGH(BossAI_FastHPEventMasks)
	ld a, [hl] ; indexed by threshold's low byte
	ld h, d
	ld l, e
	inc hl
	or [hl]
	ld [hl], a
	pop hl
	jr .event_done
.block_start
	ld a, b
	ld [de], a
.event_done
	ld a, b
	cp \1
	jr nz, .next
; The last event is exactly M, so its block is the final allocated block.
	ret
ENDM

BossAI_FastBuildHPRankOwn128:
	fhp_rank_kernel 128, $a000
BossAI_FastBuildHPRankOwn192:
	fhp_rank_kernel 192, $a000
BossAI_FastBuildHPRankPlayer128:
	fhp_rank_kernel 128, $a180
PURGE fhp_rank_kernel
POPS

; BossAI_FastHPEventMasks (same-bank, byte-indexed ROM data that removes
; pointer arithmetic from every threshold event) lives in fast_hp_masks.asm,
; first in the construction section so its page alignment costs no bank space.

BossAI_FastHPDirect::
; HL=table, BC=h (0<=h<=M). A=floor(W*h/M). DE preserved.
	add hl, bc
	ld a, [hl]
	ret

BossAI_FastHPRank8::
; HL=table, BC=h (0<=h<=M). A=floor(W*h/M). DE preserved.
	push de
	ld a, c
	and 7
	ld e, a
	ld d, 0
	srl b
	rr c
	srl b
	rr c
	res 0, c ; 2*floor(h/8)
	add hl, bc
	ld b, [hl]
	inc hl
	ld c, [hl]
	ld hl, .masks
	add hl, de
	ld a, [hl]
	and c
	ld e, a
	ld hl, .popcount
	add hl, de
	ld a, [hl]
	add b
	pop de
	ret
.masks
	db 0, 1, 3, 7, 15, 31, 63, 127
.popcount
for n, 128
	db (n & 1) + ((n >> 1) & 1) + ((n >> 2) & 1) + ((n >> 3) & 1) + ((n >> 4) & 1) + ((n >> 5) & 1) + ((n >> 6) & 1)
endr

BossAI_FastHPThresholds::
; HL=table, BC=h, A=weight (128/192). Return number of BE thresholds<=h.
; Binary upper-bound search includes duplicate thresholds. BC/DE preserved.
	push de
	ld d, h
	ld e, l
	ld l, a
	ld h, 0
.search
	ld a, h
	cp l
	jr nc, .found
	push hl
	add l
	rra ; divide the nine-bit sum, preserving carry from add
	push af
	ld l, a
	ld h, 0
	add hl, hl
	add hl, de
	ld a, [hli]
	cp b
	jr c, .lower
	jr nz, .upper
	ld a, [hl]
	cp c
	jr c, .lower
	jr nz, .upper
.lower
	pop af
	pop hl
	inc a
	ld h, a
	jr .search
.upper
	pop af
	pop hl
	ld l, a
	jr .search
.found
	pop de
	ret

BossAI_FastOwnPotentialFar::
; BC=own HP. BC=Phi with the own table, weight and mode; for cold callers
; (reached by farcall; DE preserved).
	push de
	ld a, [FSA_HP_MODE]
	ld d, a
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastHPPotential
	pop de
	ret
BossAI_FastPlayerPotentialFar::
; BC=player HP. BC=Phi with the player table and mode; for cold callers.
	push de
	ld a, [FSA_PLAYER + 37]
	ld d, a
	ld a, 128
	ld hl, $a180
	call BossAI_FastHPPotential
	pop de
	ret
BossAI_FastHPPotential::
; HL=table, BC=HP (0..max), A=weight, D=valid table mode0..2.
; BC=Phi(HP): zero at zero HP, otherwise 2W+floor(W*HP/max).
; DE/SP preserved, AF/HL scratch, no memory writes.
	push af
	ld a, b
	or c
	jr nz, .living
	pop af
	ret ; BC already zero; never read a table for a fainted actor
.living
	pop af
	push de
	ld e, a
	ld a, d
	and a
	jr z, .direct
	dec a
	jr z, .rank
	ld a, e
	call BossAI_FastHPThresholds
	jr .value
.direct
	call BossAI_FastHPDirect
	jr .value
.rank
	call BossAI_FastHPRank8
.value
	ld c, a
	ld b, 0
	ld l, e
	ld h, 0
	add hl, hl
	add hl, bc
	ld b, h
	ld c, l
	pop de
	ret
