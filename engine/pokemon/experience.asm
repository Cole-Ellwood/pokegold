CalcLevel:
	ld a, [wTempMonSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld d, 1
.next_level
	inc d
	ld a, d
	cp LOW(MAX_LEVEL + 1)
	jr z, .got_level
	call CalcExpAtLevel
	push hl
	ld hl, wTempMonExp + 2
	ldh a, [hProduct + 3]
	ld c, a
	ld a, [hld]
	sub c
	ldh a, [hProduct + 2]
	ld c, a
	ld a, [hld]
	sbc c
	ldh a, [hProduct + 1]
	ld c, a
	ld a, [hl]
	sbc c
	pop hl
	jr nc, .next_level

.got_level
	dec d
	ret

CalcExpAtLevel:
; (a/b)*n**3 + c*n**2 + d*n - e
	ld a, d
	dec a
	jr nz, .UseExpFormula
; Pokémon have 0 experience at level 1.
	ld hl, hProduct
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ret

.UseExpFormula
	ld a, [wBaseGrowthRate]
	add a
	add a
	ld c, a
	ld b, 0
	ld hl, GrowthRates
	add hl, bc
; Cube the level
	call .LevelSquared
	ld a, d
	ldh [hMultiplier], a
	call Multiply

; Multiply by a
	ld a, [hl]
	and $f0
	swap a
	ldh [hMultiplier], a
	call Multiply
; Divide by b
	ld a, [hli]
	and $f
	ldh [hDivisor], a
	ld b, 4
	call Divide
; Push the cubic term to the stack
	ldh a, [hQuotient + 1]
	push af
	ldh a, [hQuotient + 2]
	push af
	ldh a, [hQuotient + 3]
	push af
; Square the level and multiply by the lower 7 bits of c
	call .LevelSquared
	ld a, [hl]
	and $7f
	ldh [hMultiplier], a
	call Multiply
; Push the absolute value of the quadratic term to the stack
	ldh a, [hProduct + 1]
	push af
	ldh a, [hProduct + 2]
	push af
	ldh a, [hProduct + 3]
	push af
	ld a, [hli]
	push af
; Multiply the level by d
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, d
	ldh [hMultiplicand + 2], a
	ld a, [hli]
	ldh [hMultiplier], a
	call Multiply
; Subtract e
	ld b, [hl]
	ldh a, [hProduct + 3]
	sub b
	ldh [hMultiplicand + 2], a
	ld b, 0
	ldh a, [hProduct + 2]
	sbc b
	ldh [hMultiplicand + 1], a
	ldh a, [hProduct + 1]
	sbc b
	ldh [hMultiplicand], a
; If bit 7 of c is set, c is negative; otherwise, it's positive
	pop af
	and $80
	jr nz, .subtract
; Add c*n**2 to (d*n - e)
	pop bc
	ldh a, [hProduct + 3]
	add b
	ldh [hMultiplicand + 2], a
	pop bc
	ldh a, [hProduct + 2]
	adc b
	ldh [hMultiplicand + 1], a
	pop bc
	ldh a, [hProduct + 1]
	adc b
	ldh [hMultiplicand], a
	jr .done_quadratic

.subtract
; Subtract c*n**2 from (d*n - e)
	pop bc
	ldh a, [hProduct + 3]
	sub b
	ldh [hMultiplicand + 2], a
	pop bc
	ldh a, [hProduct + 2]
	sbc b
	ldh [hMultiplicand + 1], a
	pop bc
	ldh a, [hProduct + 1]
	sbc b
	ldh [hMultiplicand], a

.done_quadratic
; Add (a/b)*n**3 to (d*n - e +/- c*n**2)
	pop bc
	ldh a, [hProduct + 3]
	add b
	ldh [hMultiplicand + 2], a
	pop bc
	ldh a, [hProduct + 2]
	adc b
	ldh [hMultiplicand + 1], a
	pop bc
	ldh a, [hProduct + 1]
	adc b
	ldh [hMultiplicand], a
	ret

.LevelSquared:
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, d
	ldh [hMultiplicand + 2], a
	ldh [hMultiplier], a
	jp Multiply

GetProgressionLevelCap::
; Returns the current progression cap in a.
; - Before 8 Johto badges: strongest mon at the next Johto gym.
; - At 8 badges: Lance cap.
; - After first League clear: Blue cap.
; - After beating Blue: Red cap.
	ld de, EVENT_BEAT_BLUE
	ld b, CHECK_FLAG
	call EventFlagAction
	ld a, c
	and a
	jr nz, .red_cap

	ld de, EVENT_BEAT_CHAMPION_LANCE
	ld b, CHECK_FLAG
	call EventFlagAction
	ld a, c
	and a
	jr nz, .blue_cap

	ld hl, wJohtoBadges
	ld b, 1
	call CountSetBits
	ld a, [wNumSetBits]
	cp NUM_JOHTO_BADGES
	jr nc, .lance_cap

	ld e, a
	ld d, 0
	ld hl, .NextJohtoGymCaps
	add hl, de
	ld a, [hl]
	ret

.lance_cap
	ld a, 50
	ret

.blue_cap
	ld a, 69
	ret

.red_cap
	ld a, 81
	ret

.NextJohtoGymCaps:
	db 11 ; before Falkner
	db 17 ; before Bugsy
	db 21 ; before Whitney
	db 26 ; before Morty
	db 34 ; before Pryce
	db 34 ; before Jasmine
	db 34 ; before Chuck
	db 39 ; before Clair

ApplyProgressionExpScaling::
; Apply global EXP pacing:
; - 1.3x EXP when at least 3 levels below the current progression cap
; - 1x EXP when close to the cap
; - 0.1x EXP at or above the cap
	push de
	push hl
	ld a, MON_LEVEL
	call GetPartyParamLocation
	ld d, [hl]
	call GetProgressionLevelCap
	and a
	jr z, .done
	cp d
	jr z, .above_cap
	jr c, .above_cap
	sub d
	cp 3
	jr c, .done

; 1.3x EXP (13/10), clamped to 0xffff.
	xor a
	ldh [hMultiplicand + 0], a
	ldh a, [hProduct + 2]
	ldh [hMultiplicand + 1], a
	ldh a, [hProduct + 3]
	ldh [hMultiplicand + 2], a
	ld a, 13
	ldh [hMultiplier], a
	call Multiply
	ld a, 10
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 1]
	and a
	jr z, .store_scaled
	ld a, $ff
	ldh [hProduct + 2], a
	ldh [hProduct + 3], a
	jr .done

.store_scaled
	ldh a, [hQuotient + 2]
	ldh [hProduct + 2], a
	ldh a, [hQuotient + 3]
	ldh [hProduct + 3], a
	jr .done

.above_cap
; 0.1x EXP.
	xor a
	ldh [hDividend + 0], a
	ldh [hDividend + 1], a
	ld a, 10
	ldh [hDivisor], a
	ld b, 4
	call Divide

.done
	pop hl
	pop de
	ret

INCLUDE "data/growth_rates.asm"
