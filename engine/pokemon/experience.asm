; GrowthRates entry byte packing (data/growth_rates.asm `growth_rate` macro):
; byte 0 = dn cubic numerator, cubic denominator; byte 1 = quadratic
; coefficient in signed magnitude; byte 2 = linear coefficient;
; byte 3 = constant term.
DEF GROWTH_CUBIC_NUM_MASK EQU $f0
DEF GROWTH_CUBIC_DEN_MASK EQU $0f
DEF GROWTH_QUAD_COEF_MASK EQU $7f
DEF GROWTH_QUAD_SIGN_MASK EQU $80

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
; The three terms accumulate in b:c:e (big endian). These survive the
; math calls: the Multiply/Divide home wrappers push/pop bc (and de for
; Divide), and _Multiply touches neither d nor e. Term order differs
; from the classic stack version, which is safe: 3-byte add/sub is
; commutative mod 2^24. d (the level) is read-only throughout; caller's
; e is restored from the stack at exit.
	push de
	ld a, [wBaseGrowthRate]
	add a
	add a
	ld c, a
	ld b, 0
	ld hl, GrowthRates
	add hl, bc

; (a/b)*n**3: n*n, *n, *a, then a 4-byte divide by b. The quotient's top
; byte is 0 for every reachable input (a*n**3 <= 6,000,000), so bytes
; 1-3 seed the accumulator.
	call .LevelSquared
	ld a, d
	ldh [hMultiplier], a
	call Multiply
	ld a, [hl]
	and GROWTH_CUBIC_NUM_MASK
	swap a
	ldh [hMultiplier], a
	call Multiply
	ld a, [hl]
	and GROWTH_CUBIC_DEN_MASK
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 1]
	ld b, a
	ldh a, [hQuotient + 2]
	ld c, a
	ldh a, [hQuotient + 3]
	ld e, a

; + d*n
	inc hl
	inc hl
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, d
	ldh [hMultiplicand + 2], a
	ld a, [hli]
	ldh [hMultiplier], a
	call Multiply
	ldh a, [hProduct + 3]
	add e
	ld e, a
	ldh a, [hProduct + 2]
	adc c
	ld c, a
	ldh a, [hProduct + 1]
	adc b
	ld b, a

; - e
	ld a, e
	sub [hl]
	ld e, a
	ld a, c
	sbc 0
	ld c, a
	ld a, b
	sbc 0
	ld b, a

; +/- c*n**2 (signed magnitude: bit 7 of the coefficient is the sign)
	call .LevelSquared
	dec hl
	dec hl
	ld a, [hl]
	and GROWTH_QUAD_COEF_MASK
	ldh [hMultiplier], a
	call Multiply
	ld a, [hl]
	and GROWTH_QUAD_SIGN_MASK
	jr nz, .subtract_quadratic
	ldh a, [hProduct + 3]
	add e
	ld e, a
	ldh a, [hProduct + 2]
	adc c
	ld c, a
	ldh a, [hProduct + 1]
	adc b
	ld b, a
	jr .store_result

.subtract_quadratic
; No table reads remain, so l is free as a scratch byte.
	ldh a, [hProduct + 3]
	ld l, a
	ld a, e
	sub l
	ld e, a
	ldh a, [hProduct + 2]
	ld l, a
	ld a, c
	sbc l
	ld c, a
	ldh a, [hProduct + 1]
	ld l, a
	ld a, b
	sbc l
	ld b, a

.store_result
; Callers read the result from hProduct + 1..3 (hMultiplicand and
; hQuotient alias the same union bytes); the top byte is always 0.
	xor a
	ldh [hProduct + 0], a
	ld a, b
	ldh [hProduct + 1], a
	ld a, c
	ldh [hProduct + 2], a
	ld a, e
	ldh [hProduct + 3], a
	pop de
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
; Returns the current progression cap in a AND c.
; - Before Rival 1 / mystery egg returned: pre-rival cap (low, for level-5 starter).
; - Before 8 Johto badges: strongest mon at the next Johto gym.
; - At 8 badges: Lance cap.
; - After first League clear: Blue cap.
; - After beating Blue: Red cap.
;
; The mirror of `a` into `c` is required for cross-bank callers via
; `farcall`, which loses target's `a` but preserves target's `c`. See
; `home/farcall.asm` — after farcall, caller's `a` equals target's exit `c`.
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
	and a
	jr nz, .badge_table_lookup

	; Zero badges. Distinguish "right after starter, Rival 1 still ahead"
	; from "Rival 1 fought, on the way to Falkner". We use
	; EVENT_GAVE_MYSTERY_EGG_TO_ELM as the cutoff: it's set in ElmsLab right
	; after the player returns post-Rival-1 with the egg. Clear during
	; Routes 29/30 / Cherrygrove / Mr Pokemon's House traversal with a
	; level-5 starter; set thereafter.
	ld de, EVENT_GAVE_MYSTERY_EGG_TO_ELM
	ld b, CHECK_FLAG
	call EventFlagAction
	ld a, c
	and a
	jr nz, .badge_table_lookup    ; egg given → continue to pre-Falkner row
	ld a, 9                       ; pre-rival cap (yields wild floor of 3)
	ld c, a
	ret

.badge_table_lookup
	ld a, [wNumSetBits]
	ld e, a
	ld d, 0
	ld hl, .NextJohtoGymCaps
	add hl, de
	ld a, [hl]
	ld c, a
	ret

.lance_cap
	ld a, 50
	ld c, a
	ret

.blue_cap
	ld a, 69
	ld c, a
	ret

.red_cap
	ld a, 81
	ld c, a
	ret

.NextJohtoGymCaps:
	db 14 ; before Falkner
	db 17 ; before Bugsy
	db 21 ; before Whitney
	db 26 ; before Morty
	db 34 ; before Pryce
	db 34 ; before Jasmine
	db 34 ; before Chuck
	db 39 ; before Clair

ApplyProgressionExpScaling::
; Apply global EXP pacing.
; Pre-Rival-1 (EVENT_GAVE_MYSTERY_EGG_TO_ELM clear):
;   - 1.3x EXP when at least 3 levels below the cap
;   - 1x EXP when close to the cap (within 2)
;   - 0.1x EXP at or above the cap
; Post-Rival-1 (egg returned to Elm, persists for the rest of the game):
;   - 2x EXP under the cap (Falkner-grind relief)
;   - 0.1x EXP at or above the cap
	push de
	push hl
; Load cap first; GetProgressionLevelCap clobbers d/e via internal `ld de, ...`,
; so we must not stash the level in d before calling it.
	call GetProgressionLevelCap
	and a
	jr z, .done
	ld b, a
	ld a, MON_LEVEL
	call GetPartyParamLocation
	ld d, [hl]
	ld a, b
	cp d
	jr z, .above_cap
	jr c, .above_cap

; Under cap. Pick multiplier based on Rival-1 progress.
; EventFlagAction clobbers d; preserve b (cap) and d (level).
	push bc
	push de
	ld de, EVENT_GAVE_MYSTERY_EGG_TO_ELM
	ld b, CHECK_FLAG
	call EventFlagAction
	ld a, c
	pop de
	pop bc
	and a
	jr nz, .scale_2x

; Pre-Rival-1: 1.3x with a 3-level "near cap" softening zone at 1x.
	ld a, b
	sub d
	cp 3
	jr c, .done
	ld a, 13
	jr .apply_scale

.scale_2x
; Post-Rival-1: 2x flat under cap. No softening — the .above_cap branch
; hard-gates progression at the cap line.
	ld a, 20

.apply_scale
; Multiply the low 16 bits of hProduct by (a/10), clamp to 0xffff.
	ldh [hMultiplier], a
	xor a
	ldh [hMultiplicand + 0], a
	ldh a, [hProduct + 2]
	ldh [hMultiplicand + 1], a
	ldh a, [hProduct + 3]
	ldh [hMultiplicand + 2], a
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
