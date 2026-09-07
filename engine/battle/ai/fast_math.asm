; Private arithmetic for the exact selector prototype. No gameplay caller.
; SRAM bank 0 must be open; all operands are big-endian. This allocation is
; disjoint from the producer prefix and the plan/result/actor records.
DEF FS_MATH EQU $a510 ; 32 bytes within $a4f8..$a5ff
ASSERT sScratch == $a000
DEF FS_MULTIPLICAND EQU FS_MATH ; five bytes, signed by caller extension
DEF FS_MULTIPLIER EQU FS_MATH + 5 ; three bytes, unsigned
DEF FS_PRODUCT EQU FS_MATH + 8 ; five bytes, modulo 2^40
DEF FS_DIVIDEND EQU FS_MATH + 13 ; three bytes; becomes 24-bit quotient
DEF FS_DIVISOR EQU FS_MATH + 16 ; two bytes, nonzero
DEF FS_MATH_COUNT EQU FS_MATH + 18
ASSERT FS_MATH + 32 <= sScratch + $600

BossAI_FastMultiply40By24::
; Destructive operands; result in FS_PRODUCT. DE preserved. The caller must
; sign-extend negative contributions to five bytes BEFORE multiplication.
; Unsigned multiplier, including 65536 and grouped mass 72192, stays 24-bit.
	push de
	ld hl, FS_PRODUCT
	ld b, 5
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
.next
	ld hl, FS_MULTIPLIER
	ld a, [hli]
	or [hl]
	inc hl
	or [hl]
	jr z, .done
	ld hl, FS_MULTIPLIER
	srl [hl]
	inc hl
	rr [hl]
	inc hl
	rr [hl]
	jr nc, .shift
	ld hl, FS_MULTIPLICAND + 4
	ld de, FS_PRODUCT + 4
	ld b, 5
	and a
.add
	ld a, [de]
	adc [hl]
	ld [de], a
	dec hl
	dec de
	dec b
	jr nz, .add
.shift
	ld hl, FS_MULTIPLICAND + 4
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	jr .next
.done
	pop de
	ret

BossAI_FastDivide24By16::
; FS_DIVIDEND /= FS_DIVISOR, exact unsigned floor. Fixed 24 iterations.
; Remainder in BC; DE preserved. Carry set on zero divisor, dividend untouched.
; A seventeenth remainder bit is retained in carry during trial subtraction.
	push de
	ld hl, FS_DIVISOR
	ld a, [hli]
	ld b, a
	ld c, [hl]
	or c
	jr z, .zero
	ld de, 0
	ld a, 24
	ld [FS_MATH_COUNT], a
.bit
	ld hl, FS_DIVIDEND + 2
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	rl e
	rl d
	jr c, .subtract
	ld a, d
	cp b
	jr c, .advance
	jr nz, .subtract
	ld a, e
	cp c
	jr c, .advance
.subtract
	ld a, e
	sub c
	ld e, a
	ld a, d
	sbc b
	ld d, a
	ld hl, FS_DIVIDEND + 2
	inc [hl] ; low bit was zero after shift
.advance
	ld hl, FS_MATH_COUNT
	dec [hl]
	jr nz, .bit
	ld b, d
	ld c, e
	pop de
	and a
	ret
.zero
	pop de
	scf
	ret
