; Direction-free, noncritical damage arithmetic over an explicit public context.
; Adapters must normalize conditional power/category, screens and known stat
; items BEFORE calling. No live battle fields, item getters or RNG are read here.
; DE points to AD_CONTEXT_SIZE writable bytes. Input words are big endian.
; BC = HP loss for the requested roll and hit count; carry = supported context.
; DE preserved; AF/HL, HRAM math and standard banking scratch clobbered.
; AD_MATCHUP and AD_DAMAGE are output scratch in the caller-owned context.
;
; HP loss is capped at starting HP, before Substitute/Endure/Focus Band/Psychic
; negation; the action model, not this arithmetic kernel, handles those outcomes.

DEF AD_LEVEL EQU 0
DEF AD_POWER EQU 1
DEF AD_EFFECT EQU 2
DEF AD_TYPE EQU 3
DEF AD_CATEGORY EQU 4
DEF AD_ATTACK EQU 5
DEF AD_DEFENSE EQU 7
DEF AD_ATTACKER_TYPES EQU 9
DEF AD_DEFENDER_TYPES EQU 11
DEF AD_DEFENDER_HP EQU 13
DEF AD_FLAGS EQU 15
DEF AD_WEATHER EQU 16
DEF AD_TYPE_ITEM_PERCENT EQU 17
DEF AD_ITEM_NUM EQU 18
DEF AD_ITEM_DEN EQU 19
DEF AD_HITS EQU 20
DEF AD_ROLL EQU 21
DEF AD_MATCHUP EQU 22
DEF AD_DAMAGE EQU 23
DEF AD_DEFENDER_MAXHP EQU 25
DEF AD_DIRECTION EQU 27
DEF AD_MOVE EQU 28
DEF AD_MIN_HITS EQU 29
DEF AD_MAX_HITS EQU 30
DEF AD_ACCURACY EQU 31
DEF AD_PRIORITY EQU 32
DEF AD_POSTROLL EQU 33
DEF AD_MAX_POSTROLL EQU 34
DEF AD_TOTAL EQU 35
DEF AD_HITS_LEFT EQU 37
DEF AD_USER_ACC_STAGE EQU 38
DEF AD_TARGET_EVA_STAGE EQU 39
DEF AD_NEGATION_CHANCE EQU 40
DEF AD_SURVIVAL_CHANCE EQU 41
DEF AD_OWN_SLOT EQU 42 ; $ff=active known own battler, otherwise owned party slot
DEF AD_RAW_MIN EQU 43 ; raw damage sum, before HP-loss capping (side effects)
DEF AD_RAW_MAX EQU 45
DEF AD_ATTACKER_HP EQU 47
DEF AD_ATTACKER_MAXHP EQU 49
DEF AD_CONTEXT_SIZE EQU 51

DEF AD_IDENTIFIED_F EQU 0
DEF AD_ATTACKER_LOW_F EQU 1
DEF AD_DEFENDER_HIGH_F EQU 2
DEF AD_DEFENDER_STATUS_F EQU 3
DEF AD_SUBSTITUTE_F EQU 4
DEF AD_BALLOON_F EQU 5
DEF AD_STRUGGLE_F EQU 6
DEF AD_UNSUPPORTED_F EQU 7

MACRO ad_address
	ld hl, \1
	add hl, de
ENDM

; ai-layer: POLICY
BossAI_DamageKernel::
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	push bc
	ad_address AD_FLAGS
	ld a, [hl]
	push af
	ad_address AD_TOTAL
	xor a
	ld [hli], a
	ld [hl], a
	ad_address AD_HITS
	ld a, [hl]
	ad_address AD_HITS_LEFT
	ld [hl], a
	and a
	jp z, .range_unknown
.hit_loop
	call .PerHit
	jp nc, .range_unknown
	push bc
	ad_address AD_TOTAL
	ld a, [hli]
	ld l, [hl]
	ld h, a
	add hl, bc
	jr nc, .total_ok
	ld hl, $ffff
.total_ok
	ld b, h
	ld c, l
	ad_address AD_TOTAL
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc ; this hit's damage
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a
	jr nc, .remaining_hp
	ld hl, 0
.remaining_hp
	ld b, h
	ld c, l
	ad_address AD_DEFENDER_HP
	ld [hl], b
	inc hl
	ld [hl], c
	ld a, b
	or c
	jr z, .finish_range
; Later hits see Ice's threshold after earlier direct HP damage. This matters
; even for a lower/upper noncritical envelope; multiplying the first hit can
; underestimate the upper bound after the defender falls below half HP.
	sla c
	rl b
	ad_address AD_FLAGS
	res AD_DEFENDER_HIGH_F, [hl]
	ad_address AD_DEFENDER_MAXHP
	ld a, [hli]
	cp b
	jr c, .still_high
	jr nz, .next_hit
	ld a, [hl]
	cp c
	jr nc, .next_hit
.still_high
	ad_address AD_FLAGS
	set AD_DEFENDER_HIGH_F, [hl]
.next_hit
	ad_address AD_HITS_LEFT
	dec [hl]
	jp nz, .hit_loop
.finish_range
	pop af
	ad_address AD_FLAGS
	ld [hl], a
	pop bc
	ad_address AD_DEFENDER_HP
	ld [hl], b
	inc hl
	ld [hl], c
	push bc ; initial HP bounds aggregate HP loss, including final-hit overkill
	ad_address AD_TOTAL
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, c
	sub l
	ld a, b
	sbc h
	jr c, .bounded
	ld b, h
	ld c, l
.bounded
	ad_address AD_DAMAGE
	ld [hl], b
	inc hl
	ld [hl], c
	ad_address AD_HITS_LEFT
	ld a, [hl]
	cp $ff
	jr z, .range_unsupported
	scf
	ret
.range_unknown
	ad_address AD_HITS_LEFT
	ld [hl], $ff
	ad_address AD_TOTAL
	xor a
	ld [hli], a
	ld [hl], a
	jr .finish_range
.range_unsupported
	and a
	ret

.PerHit
	call .PreRoll
	ret nc
	and a
	jp z, .supported
	jp .variation

.PreRoll
; BC=damage before random variation; A=1 for a variable hit, 0 for fixed
; damage or immunity. Carry reports support. No endpoint scratch is written.
	ad_address AD_FLAGS
	bit AD_UNSUPPORTED_F, [hl]
	jr nz, .unsupported
	ad_address AD_POWER
	ld a, [hl]
	and a
	jr z, .unsupported
	ld bc, EFFECTIVE
	call .Chart
	ad_address AD_MATCHUP
	ld [hl], c
	ld a, b
	or c
	jp z, .fixed_supported
	ad_address AD_FLAGS
	bit AD_BALLOON_F, [hl]
	jr z, .check_fixed
	ad_address AD_TYPE
	ld a, [hl]
	cp GROUND
	jr nz, .check_fixed
	ld bc, 0
	jp .fixed_supported
.unsupported
	ld bc, 0
	and a
	ret
.check_fixed
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_STATIC_DAMAGE
	jr z, .static
	cp EFFECT_LEVEL_DAMAGE
	jr z, .level
	cp EFFECT_SUPER_FANG
	jp z, .fang
	call .Formula
	call .Items
	call .CapBase
	ad_address AD_FLAGS
	bit AD_STRUGGLE_F, [hl]
	jr nz, .variable_supported
	call .Weather
	ad_address AD_TYPE
	ld a, [hl]
	call .AttackerContribution
	and a
	jr z, .no_stab
	ld a, 3
	ld h, 2
	call .Scale
.no_stab
	call .Chart
	call .Passives
.variable_supported
	ld a, 1
	scf
	ret
.variation
	ad_address AD_ROLL
	ld a, [hl]
	ld h, 255
	call .Scale
	ad_address AD_POSTROLL
	ld a, [hl]
	and a
	jr z, .false_swipe
	ld h, 1
	call .Scale
.false_swipe
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_FALSE_SWIPE
	jr nz, .supported
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	cp b
	jr c, .false_swipe_cap
	jr nz, .supported
	ld a, [hl]
	cp c
	jr z, .false_swipe_cap
	jr nc, .supported
.false_swipe_cap
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, b
	or c
	jr z, .supported
	dec bc
	jr .supported
.static
	ad_address AD_POWER
	jr .fixed_byte
.level
	ad_address AD_LEVEL
.fixed_byte
	ld b, 0
	ld c, [hl]
	jr .fixed_supported
.fang
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	srl b
	rr c
	call .MinOne
.fixed_supported
	xor a
	scf
	ret
.supported
	ad_address AD_DAMAGE
	ld [hl], b
	inc hl
	ld [hl], c
	scf
	ret

.SingleHitRange
; Both endpoints share all pre-roll arithmetic. Keep the general kernel for
; multiple hits, whose later hits observe changed HP-dependent passives.
; Entered by jp from BossAI_PublicDamageRange and returns its contract:
; BC = min, DE = max HP loss, so unlike the kernel above DE is not preserved.
	ad_address AD_POSTROLL
	ld a, [hl]
	push af
	call .PreRoll
	jr c, .single_supported
	pop af
	jp BossAI_PublicDamageRange.unknown
.single_supported
	push af
	push bc
	ad_address AD_HITS
	ld [hl], 1
	inc hl
	ld [hl], 217
	call .FinishSingle
	ad_address AD_TOTAL
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_RAW_MIN
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc
	pop af
	push af
	ad_address AD_MAX_POSTROLL
	ld a, [hl]
	ad_address AD_POSTROLL
	ld [hl], a
	pop af
	ad_address AD_ROLL
	ld [hl], 255
	call .FinishSingle
	push bc
	ad_address AD_TOTAL
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_RAW_MAX
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc
	pop af
	ad_address AD_POSTROLL
	ld [hl], a
	push bc
	ad_address AD_RAW_MIN
	ld a, [hli]
	ld b, a
	ld c, [hl]
	call .CapSingle
	pop hl
	ld d, h
	ld e, l
	scf
	ret

.FinishSingle
	and a
	jr z, .single_fixed
	call .variation
	jr .single_raw
.single_fixed
	call .supported
.single_raw
	ad_address AD_TOTAL
	ld [hl], b
	inc hl
	ld [hl], c
; Match the general kernel's final hit counter as well as its damage outputs.
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	cp b
	jr c, .single_exhausted
	jr nz, .single_remaining
	ld a, [hl]
	cp c
	jr c, .single_exhausted
	jr nz, .single_remaining
.single_exhausted
	ld a, 1
	jr .single_counter
.single_remaining
	xor a
.single_counter
	ad_address AD_HITS_LEFT
	ld [hl], a
	call .CapSingle
	ad_address AD_DAMAGE
	ld [hl], b
	inc hl
	ld [hl], c
	ret

.CapSingle
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	cp b
	jr c, .single_cap
	jr nz, .single_uncapped
	ld a, [hl]
	cp c
	jr nc, .single_uncapped
.single_cap
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
.single_uncapped
	ret

.Formula
; Match TruncateHL_BC: if either stat exceeds 255, divide BOTH by four
; exactly once, floor/min-one the full words, then use their LOW bytes.
	ad_address AD_DEFENSE
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_ATTACK
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, h
	or b
	jr z, .truncated
	srl b
	rr c
	srl b
	rr c
	call .MinOne
	srl h
	rr l
	srl h
	rr l
	ld a, h
	or l
	jr nz, .truncated
	inc l
.truncated
	ld b, l
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SELFDESTRUCT
	jr nz, .defense_nonzero
	srl c
.defense_nonzero
	ld a, c
	and a
	jr nz, .raw
	inc c
.raw
	push de
	ad_address AD_LEVEL
	ld a, [hli]
	ld d, [hl]
	ld e, a
	call .RawQuotient
	pop de
	ret

.RawQuotient
; Same integer order as ConfusionDamageCalc, before item factors and +2.
; B attack, C defense, D power, E level. Output HRAM four-byte quotient.
	xor a
	ldh [hDividend], a
	ldh [hDividend + 1], a
	ld a, e
	add a
	ldh [hDividend + 3], a
	ld a, 0
	adc 0
	ldh [hDividend + 2], a
	ld a, 5
	ldh [hDivisor], a
	push bc
	ld b, 4
	call BossAI_Divide
	pop bc
	ldh a, [hQuotient + 3]
	add 2
	ldh [hQuotient + 3], a
	ld a, d
	ldh [hMultiplier], a
	call BossAI_Multiply
	ld a, b
	ldh [hMultiplier], a
	call BossAI_Multiply
	ld a, c
	ldh [hDivisor], a
	ld b, 4
	call BossAI_Divide
	ld a, 50
	ldh [hDivisor], a
	ld b, 4
	jp BossAI_Divide

.Items
; Normalized known item factors preserve combat's pre-+2 rounding.
	ad_address AD_TYPE_ITEM_PERCENT
	ld a, [hl]
	and a
	jr z, .late_item
	add 100
	ld b, a
	ld c, 100
	call .ScaleQuotient
.late_item
	ad_address AD_ITEM_NUM
	ld b, [hl]
	inc hl
	ld c, [hl]
	ld a, b
	and a
	ret z
	ld a, c
	and a
	ret z
.ScaleQuotient
	ld a, b
	cp c
	jr nz, .scale_quotient_fraction
; Multiply consumes only the low 24 bits, even for an identity fraction.
; Preserve that input-width rule and Divide's zero remainder.
	xor a
	ldh [hQuotient], a
	ldh [hRemainder], a
	ret
.scale_quotient_fraction
	ld a, b
	ldh [hMultiplier], a
	call BossAI_Multiply
	ld a, c
	ldh [hDivisor], a
	ld b, 4
	jp BossAI_Divide

.CapBase
; Cap to 997 and then add two, exactly as DamageCalc's noncritical path.
	ldh a, [hQuotient]
	ld b, a
	ldh a, [hQuotient + 1]
	or b
	jr nz, .cap
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
	ld a, b
	cp HIGH(998)
	jr c, .plus_two
	jr nz, .cap
	ld a, c
	cp LOW(998)
	jr c, .plus_two
.cap
	ld bc, 997
.plus_two
	inc bc
	inc bc
	ret

.Weather
	ad_address AD_WEATHER
	ld a, [hl]
	cp WEATHER_RAIN
	jr z, .rain
	cp WEATHER_SUN
	ret nz
	ad_address AD_TYPE
	ld a, [hl]
	cp FIRE
	jr z, .weather_up
	cp WATER
	ret nz
	jr .weather_down
.rain
	ad_address AD_TYPE
	ld a, [hl]
	cp WATER
	jr z, .weather_up
	cp FIRE
	jr z, .weather_down
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SOLARBEAM
	ret nz
.weather_down
	ld a, 1
	ld h, 2
	jp .Scale
.weather_up
	ld a, 3
	ld h, 2
	jp .Scale

.Chart
; Apply each matching chart row in source order; do not multiply an aggregate
; factor into damage, since intermediate floors matter. The first call folds
; EFFECTIVE=10 into an aggregate for defensive passives and item eligibility.
	ad_address AD_FLAGS
	bit AD_STRUGGLE_F, [hl]
	ret nz
	xor a
	call .chart_pointer
	call .chart_loop
	ad_address AD_FLAGS
	bit AD_IDENTIFIED_F, [hl]
	ret nz
	ld a, 2
	call .chart_pointer
.chart_loop
	ld a, [hli]
	cp -1
	ret z
	cp -2
	ret z
	push hl
	push af
	ad_address AD_TYPE
	ld a, [hl]
	ld h, a
	pop af
	cp h
	pop hl
	ret nz ; this attacker's contiguous group has ended
	ld a, [hli]
	push hl
	push bc
	ld b, a
	ad_address AD_DEFENDER_TYPES
	ld a, [hli]
	cp b
	jr z, .chart_type_match
	ld a, [hl]
	cp b
.chart_type_match
	pop bc
	pop hl
	jr nz, .chart_next
	ld a, [hli]
	push hl
	call .MajestyFactor
	and a
	jr z, .immune
	ld h, 10
	call .Scale
	pop hl
	jr .chart_loop
.immune
	pop hl
	ld bc, 0
	ret
.chart_next
	inc hl
	jr .chart_loop
.chart_pointer
; A=0 ordinary rows or 2 Foresight-only rows. Preserve the scaled amount.
	push bc
	push af
	ad_address AD_TYPE
	ld a, [hl]
	cp TYPES_END
	jr nc, .chart_empty
	add a
	add a
	ld c, a
	ld b, 0
	ld hl, BossAI_TypeMatchupIndex
	add hl, bc
	pop af
	ld c, a
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop bc
	ret
.chart_empty
	pop af
	pop bc
	ld hl, BossAI_TypeMatchups.END
	ret

.MajestyFactor
	and a
	ret nz
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_STATIC_DAMAGE
	jr z, .zero
	cp EFFECT_LEVEL_DAMAGE
	jr z, .zero
	cp EFFECT_SUPER_FANG
	jr z, .zero
	cp EFFECT_PSYWAVE
	jr z, .zero
	cp EFFECT_COUNTER
	jr z, .zero
	cp EFFECT_MIRROR_COAT
	jr z, .zero
	cp EFFECT_BIDE
	jr z, .zero
	cp EFFECT_FUTURE_SIGHT
	jr z, .zero
	ld a, DRAGON
	call .AttackerContribution
	and a
	ret z
	ld a, NOT_VERY_EFFECTIVE
	ret
.zero
	xor a
	ret

.AttackerContribution
	push bc
	ld b, a
	ad_address AD_ATTACKER_TYPES
	jr .contribution
.DefenderContribution
	push bc
	ld b, a
	ad_address AD_DEFENDER_TYPES
.contribution
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	cp b
	ld a, 0
	jr nz, .contribution_done
	ld a, 2
	jr .contribution_done
.dual
	cp b
	jr z, .half
	ld a, c
	cp b
	ld a, 0
	jr nz, .contribution_done
.half
	ld a, 1
.contribution_done
	pop bc
	ret

.Passives
	ld a, b
	or c
	ret z
	ad_address AD_TYPE
	ld a, [hl]
	cp NORMAL
	jr nz, .fire
	ld a, NORMAL
	call .AttackerContribution
	and a
	jr z, .fire
	cp 2
	ld a, 31
	ld h, 30
	jr nz, .normal_scale
	ld a, 16
	ld h, 15
.normal_scale
	call .Scale
.fire
	ad_address AD_TYPE
	ld a, [hl]
	cp FIRE
	jr nz, .ghost
	ad_address AD_FLAGS
	bit AD_ATTACKER_LOW_F, [hl]
	jr z, .ghost
	ld a, FIRE
	call .AttackerContribution
	and a
	jr z, .ghost
	cp 2
	ld a, 11
	ld h, 10
	jr nz, .fire_scale
	ld a, 6
	ld h, 5
.fire_scale
	call .Scale
.ghost
	ad_address AD_FLAGS
	bit AD_DEFENDER_STATUS_F, [hl]
	jr z, .dragon
	ld a, GHOST
	call .AttackerContribution
	and a
	jr z, .dragon
	cp 2
	ld a, 21
	ld h, 20
	jr nz, .ghost_scale
	ld a, 11
	ld h, 10
.ghost_scale
	call .Scale
.dragon
	ad_address AD_MATCHUP
	ld a, [hl]
	cp EFFECTIVE + 1
	jr nc, .ground
	ld a, DRAGON
	call .DefenderContribution
	and a
	jr z, .category
	cp 2
	ld a, 2
	ld h, 3
	jr nz, .dragon_scale
	ld a, 1
	ld h, 2
.dragon_scale
	call .Scale
	jr .category
.ground
	ld a, GROUND
	call .DefenderContribution
	and a
	jr z, .category
	cp 2
	ld a, 19
	ld h, 20
	jr nz, .ground_scale
	ld a, 9
	ld h, 10
.ground_scale
	call .Scale
.category
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	jr nc, .water
	ld a, BUG
	call .DefenderContribution
	and a
	jr z, .ice
	cp 2
	ld a, 19
	ld h, 20
	jr nz, .category_scale
	ld a, 9
	ld h, 10
	jr .category_scale
.water
	ld a, WATER
	call .DefenderContribution
	and a
	jr z, .ice
	cp 2
	ld a, 39
	ld h, 40
	jr nz, .category_scale
	ld a, 19
	ld h, 20
.category_scale
	call .Scale
.ice
	ad_address AD_FLAGS
	bit AD_DEFENDER_HIGH_F, [hl]
	ret z
	ld a, ICE
	call .DefenderContribution
	and a
	ret z
	cp 2
	ld a, 39
	ld h, 40
	jr nz, .Scale
	ld a, 19
	ld h, 20

.Scale
; BC * A / H, floor with minimum one for positive input. Zero stays zero.
; Saturate only true 16-bit overflow; context callers use bounded real stats.
	push af
	ld a, b
	or c
	jr nz, .scale_nonzero
	pop af
	ret
.scale_nonzero
	pop af
	cp h
	ret z ; avoid multiplication/division for neutral stages and item factors
	ldh [hMultiplier], a
	push hl
	xor a
	ldh [hMultiplicand], a
	ld a, b
	ldh [hMultiplicand + 1], a
	ld a, c
	ldh [hMultiplicand + 2], a
	call BossAI_Multiply
	pop hl
	ld a, h
	ldh [hDivisor], a
	ld b, 4
	call BossAI_Divide
	ldh a, [hQuotient]
	ld b, a
	ldh a, [hQuotient + 1]
	or b
	ld bc, $ffff
	ret nz
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
.MinOne
	ld a, b
	or c
	ret nz
	inc c
	ret

; Emit the authoritative rows in this bank to avoid switching banks for every
; chart byte. Row order and Foresight boundaries remain identical to combat.
DEF BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS EQU 1
INCLUDE "data/types/type_matchups.asm"
PURGE BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS
BossAI_TypeMatchupsEnd:
ASSERT BANK(BossAI_TypeMatchups) == BANK(BossAI_DamageKernel)

; The data file marks each contiguous attacker group. Its combat row bytes
; and their order are unchanged. Empty/unused types point at the terminator.
BossAI_TypeMatchupIndex:
	dw BossAI_TypeMatchups.NORMAL, BossAI_TypeMatchups.NORMAL_FORESIGHT
	dw BossAI_TypeMatchups.FIGHTING, BossAI_TypeMatchups.FIGHTING_FORESIGHT
	dw BossAI_TypeMatchups.FLYING, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.POISON, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.GROUND, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.ROCK, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.END, BossAI_TypeMatchups.END ; BIRD
	dw BossAI_TypeMatchups.BUG, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.GHOST, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.STEEL, BossAI_TypeMatchups.END
REPT SPECIAL - STEEL - 1
	dw BossAI_TypeMatchups.END, BossAI_TypeMatchups.END
ENDR
	dw BossAI_TypeMatchups.FIRE, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.WATER, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.GRASS, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.ELECTRIC, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.PSYCHIC_TYPE, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.ICE, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.DRAGON, BossAI_TypeMatchups.END
	dw BossAI_TypeMatchups.DARK, BossAI_TypeMatchups.END
BossAI_TypeMatchupIndexEnd:
ASSERT @ - BossAI_TypeMatchupIndex == TYPES_END * 4

; A restoring quotient bit. The carry from RLA is the ninth remainder bit;
; subtracting the byte divisor then wraps to the correct byte remainder.
MACRO bossai_divide_bit
	sla [hl]
	rla
	jr c, .subtract\@
	cp b
	jr c, .next\@
.subtract\@
	sub b
	inc [hl]
.next\@
ENDM

; ai-layer: POLICY
BossAI_Divide::
; Four-byte unsigned hDividend / byte hDivisor. Exact hQuotient/remainder;
; BC/DE/HL preserved. b is ignored: all four dividend bytes are always
; processed. Leading zero bytes need no quotient trials. No bank change or
; RAM, except that a zero divisor falls back to the ROM0 Divide (which does
; bank-switch) to keep the original undefined result rather than inventing a
; supported damage number.
	ldh a, [hDivisor]
	and a
	jp z, Divide
	push hl
	push bc
	ld b, a
	ld c, 4
	ld hl, hDividend
.leading_zero
	ld a, [hl]
	and a
	jr nz, .start
	inc hl
	dec c
	jr nz, .leading_zero
	jr .done
.start
	xor a
.byte
REPT 8
	bossai_divide_bit
ENDR
	inc hl
	dec c
	jr nz, .byte
.done
	ldh [hRemainder], a
	pop bc
	pop hl
	ret
PURGE bossai_divide_bit

; ai-layer: POLICY
BossAI_Multiply::
; Exact low-24-bit multiplicand * byte multiplier -> full 32-bit hProduct.
; Preserve BC/DE/HL like Multiply, without a far call or memory-based shifts.
	push hl
	push bc
	push de
	ldh a, [hMultiplicand]
	push af ; high multiplicand byte for the second, usually empty, product
	ldh a, [hMultiplicand + 1]
	ld b, a
	ldh a, [hMultiplicand + 2]
	ld c, a
	ldh a, [hMultiplier]
	ld d, a
	ld e, 8
	ld hl, 0
	xor a
.low_product
	add hl, hl
	rla
	sla d
	jr nc, .low_next
	add hl, bc
	adc 0
.low_next
	dec e
	jr nz, .low_product
	ldh [hProduct + 1], a
	ld a, h
	ldh [hProduct + 2], a
	ld a, l
	ldh [hProduct + 3], a
	pop af
	and a
	jr z, .high_zero
	ld c, a
	ld b, 0
	ldh a, [hMultiplier]
	ld d, a
	ld e, 8
	ld hl, 0
.high_product
	add hl, hl
	sla d
	jr nc, .high_next
	add hl, bc
.high_next
	dec e
	jr nz, .high_product
	ldh a, [hProduct + 1]
	add l
	ldh [hProduct + 1], a
	ld a, h
	adc 0
.high_zero
	ldh [hProduct], a
	xor a
	ldh [hMultiplier], a
	pop de
	pop bc
	pop hl
	ret
