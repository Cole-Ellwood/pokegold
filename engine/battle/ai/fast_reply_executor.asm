; Execute the compact incoming plan without mutable producer reads.
; Uses the same sequential executor scratch as owned actions, never their plans.
DEF FSC_FAULT EQU $a58f ; sticky: an incoming plan was executed at an uncompiled regime
BossAI_FastExecuteReplyPlan::
; DE=context base (only reply399..446 read), HL=continuation24,
; A=original event0hit/1miss. SRAM0 open; actors' maximum HP populated.
; DE/SP preserved. Carry=accepted; unsupported opcode rejects without
; continuation writes. Invalid event rejects without any writes.
; Fixed defense/status/other non-HP facts must match the compiled plan, except
; that FSV_OVERRIDE (flag exactly 1) replaces the raw maximum and range bit
; with a defensive variant for the selector's own-boost pairs.
	ld b, 0
	jr .validate
.FlagsOnly
; Same accepted flags, but no HP mutation or damage/item/recovery arithmetic.
	ld b, 1
.validate
	cp 2
	jp nc, .invalid
	ld [FSE_EVENT], a
	ld a, b
	ld [FSE_MODE], a
	ld a, h
	ld [FSE_CONT], a
	ld a, l
	ld [FSE_CONT + 1], a
	push de
	ld hl, FSR_BASE
	add hl, de
	ld a, h
	ld [FSE_PLAN], a
	ld a, l
	ld [FSE_PLAN + 1], a
	ld a, FSR_OPCODE
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .reject
	cp FSR_BOOST + 1
	jr c, .represented
.reject
	pop de
.invalid
	and a
	ret
.represented
	xor a
	ld [FSE_FLAGS], a
	ld a, FSR_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSR_ABSENT
	jp z, .done
	call .Continuation
	ld a, [hli]
	or [hl]
	jp z, .done
	inc hl
	ld a, [hli]
	or [hl]
	jp z, .done
	ld a, FSR_CHECK_FLAGS
	call .PlanAddress
	ld a, [hl]
	ld [FSE_FLAGS], a
	ld a, FSR_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .done
	ld a, FSR_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSR_PURSUIT
	jp z, .pursuit
	cp FSR_RECOVERY
	jp z, .recovery
	cp FSR_BOOST
	jp z, .done ; check flags only; the boost acts through the own plans' variants
	ld [FSE_OPCODE], a
	ld a, FSR_DAMAGE_FLAGS
	call .PlanAddress
	ld a, [FSE_FLAGS]
	or [hl]
	ld [FSE_FLAGS], a
	ld a, [FSE_EVENT]
	and a
	jr z, .hit_regime
; a miss changes no HP but Selfdestruct's own; its regime is never read
	ld a, [FSE_OPCODE]
	cp FSR_SELFDESTRUCT
	jp nz, .done
	call .SelfFaint
	jp .done
.hit_regime
; amounts use the regime before Selfdestruct's self-faint
	call .Regime
	ld a, [FSE_OPCODE]
	cp FSR_SELFDESTRUCT
	call z, .SelfFaint
	ld a, FSR_ACCURACY
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .done
	ld a, [FSE_REGIME]
	ld c, a
	ld b, 0
	ld hl, .Bits
	add hl, bc
	ld a, [hl]
	ld [FSE_MASK], a
	ld a, FSR_VALID
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr nz, .regime_compiled
	ld a, 1
	ld [FSC_FAULT], a ; the selector restarts through the reference
.regime_compiled
	ld a, [FSE_OPCODE]
	cp FSR_MULTI
	jr z, .support ; these families decide their range at execution
	cp FSR_FALSE_SWIPE
	jr z, .support
	cp FSR_FANG
	jr z, .support
	ld a, [FSV_OVERRIDE]
	cp 1 ; exactly 1 is live; poisoned or cleared scratch is not
	jr nz, .plan_range
	ld a, [FSV_OVERRIDE + 3]
	bit 0, a
	jr z, .support
	jr .range_flag
.plan_range
	ld a, FSR_RANGE
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr z, .support
.range_flag
	ld a, [FSE_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSE_FLAGS], a
.support
	ld a, FSR_SUPPORT
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr nz, .raw
	ld a, [FSE_FLAGS]
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld [FSE_FLAGS], a
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, FSR_POWER
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .done
	call .Continuation
	xor a
	ld [hli], a
	ld [hl], a
	jp .done
.raw
	ld a, [FSE_OPCODE]
	cp FSR_MULTI
	jp z, .multi
	cp FSR_FANG
	jp z, .fang
	cp FSR_FALSE_SWIPE
	jp z, .false_swipe
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSV_OVERRIDE]
	cp 1 ; exactly 1 is live; poisoned or cleared scratch is not
	jr nz, .plan_raw
	ld a, [FSV_OVERRIDE + 1]
	ld b, a
	ld a, [FSV_OVERRIDE + 2]
	ld c, a
	jr .Script
.plan_raw
	ld a, [FSE_REGIME]
	add a
	add FSR_RAW_MAX
	call .PlanWord
.Script
; BC=raw amount for the single-hit script (target loss, user item,
; drain/recoil). Zero is an accepted no-op.
	ld a, b
	ld [FST_RAW], a
	ld a, c
	ld [FST_RAW + 1], a
	or b
	jp z, .done
	call .Continuation
	ld a, h
	ld [FST_TARGET_HP], a
	ld a, l
	ld [FST_TARGET_HP + 1], a
	inc hl
	inc hl
	ld a, h
	ld [FST_USER_HP], a
	ld a, l
	ld [FST_USER_HP + 1], a
	ld a, [FSA_PLAYER + 2]
	ld [FST_USER_MAX], a
	ld a, [FSA_PLAYER + 3]
	ld [FST_USER_MAX + 1], a
	ld a, FSR_STEEL
	call .PlanAddress
	ld a, [hl]
	ld [FST_RECOIL], a
	ld a, FSR_DESCRIPTOR
	call .PlanWord
	ld h, b
	ld l, c
	ld a, [hli]
	ld [FST_EFFECT], a
	ld a, [hl]
	ld [FST_ITEM], a
	ld a, FSR_ITEM_QUOTA
	call .PlanWord
.item_quota
	ld a, b
	ld [FST_ITEM_QUOTA], a
	ld a, c
	ld [FST_ITEM_QUOTA + 1], a
	call BossAI_FastDamageScript
	jp .done
.multi
; Hits advance the target's HP one at a time so later hits read the
; defender-high predicate at the reduced HP; the sequence stops at a KO and
; the saturating total keeps the final hit's overkill, like the kernel. The
; range flag compares the two endpoint paths' totals; the transition applies
; the maximum path's total through the single-hit script, whose items and
; drain use the total as the raw amount.
	ld a, FSR_MAX_HITS
	call .PlanAddress
	ld a, [hl]
	ld [FSX_HITS], a
	xor a
	ld [FSX_MODE], a
	call .MultiPath
	ld a, [FSX_TOTAL]
	ld [FSX_TOTAL2], a
	ld a, [FSX_TOTAL + 1]
	ld [FSX_TOTAL2 + 1], a
	ld a, FSR_MIN_HITS
	call .PlanAddress
	ld a, [hl]
	ld [FSX_HITS], a
	ld a, 1
	ld [FSX_MODE], a
	call .MultiPath
	ld hl, FSX_TOTAL
	ld a, [FSX_TOTAL2]
	cp [hl]
	jr nz, .multi_range
	inc hl
	ld a, [FSX_TOTAL2 + 1]
	cp [hl]
	jr z, .multi_execute
.multi_range
	ld a, [FSE_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSE_FLAGS], a
.multi_execute
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSX_TOTAL2]
	ld b, a
	ld a, [FSX_TOTAL2 + 1]
	ld c, a
	jp .Script
.MultiPath
; FSX_HITS hits from the target's current HP; FSX_MODE 0 uses the compiled
; maxima, 1 the maxima minus the compiled deltas.
; Leaves the saturating FSX_TOTAL.
	call .Continuation
	ld a, [hli]
	ld [FSX_HP], a
	ld a, [hl]
	ld [FSX_HP + 1], a
	xor a
	ld [FSX_TOTAL], a
	ld [FSX_TOTAL + 1], a
.multi_hit
	ld a, [FSX_HP + 1]
	ld l, a
	ld a, [FSX_HP]
	ld h, a
	add hl, hl ; wrapped 2*HP, as in .Regime
	ld a, [FSE_REGIME]
	and 1
	ld c, a
	ld a, [FSA_MAX_HP]
	cp h
	jr c, .multi_high
	jr nz, .multi_regime
	ld a, [FSA_MAX_HP + 1]
	cp l
	jr nc, .multi_regime
.multi_high
	set 1, c
.multi_regime
	ld a, c
	ld [FSX_REGIME], a
	add a
	add FSR_RAW_MAX
	call .PlanWord
	ld a, [FSX_MODE]
	and a
	jr z, .multi_amount
	push bc
	ld a, [FSX_REGIME]
	call .MinDeltaFor
	pop bc
	ld l, a
	ld a, c
	sub l
	ld c, a
	ld a, b
	sbc 0
	ld b, a
.multi_amount
	ld a, [FSX_TOTAL + 1]
	add c
	ld [FSX_TOTAL + 1], a
	ld a, [FSX_TOTAL]
	adc b
	ld [FSX_TOTAL], a
	jr nc, .multi_total_ok
	ld a, $ff
	ld [FSX_TOTAL], a
	ld [FSX_TOTAL + 1], a
.multi_total_ok
	ld hl, FSX_HP
	call BossAI_FastLoseHP
	ld a, [FSX_HP]
	ld hl, FSX_HP + 1
	or [hl]
	ret z ; a KO ends the sequence
	ld hl, FSX_HITS
	dec [hl]
	jr nz, .multi_hit
	ret
.fang
; Super Fang: half the target's current HP, minimum one; a compiled zero is
; the chart immunity. Never a range.
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSE_REGIME]
	add a
	add FSR_RAW_MAX
	call .PlanWord
	ld a, b
	or c
	jp z, .done
	call .Continuation
	ld a, [hli]
	ld b, a
	ld c, [hl]
	srl b
	rr c
	ld a, b
	or c
	jp nz, .Script
	inc c
	jp .Script
.false_swipe
; Single hit capped at the target's current HP minus one. Both endpoints are
; capped the same way and the range flag follows whether the capped amounts
; differ; the transition applies the maximum endpoint.
	ld a, [FSE_REGIME]
	add a
	add FSR_RAW_MAX
	call .PlanWord
	ld a, b
	ld [FSX_A], a
	ld a, c
	ld [FSX_A + 1], a
	ld a, [FSE_REGIME]
	call .MinDeltaFor
	ld l, a
	ld a, [FSX_A + 1]
	sub l
	ld [FSX_B + 1], a
	ld a, [FSX_A]
	sbc 0
	ld [FSX_B], a
	call .Continuation
	ld a, [hli]
	ld b, a
	ld c, [hl]
	dec bc ; the target lives here
	ld hl, FSX_A
	call .CapWord
	ld hl, FSX_B
	call .CapWord
	ld a, [FSX_A]
	ld hl, FSX_B
	cp [hl]
	jr nz, .false_swipe_range
	ld a, [FSX_A + 1]
	inc hl
	cp [hl]
	jr z, .false_swipe_execute
.false_swipe_range
	ld a, [FSE_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSE_FLAGS], a
.false_swipe_execute
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSX_A]
	ld b, a
	ld a, [FSX_A + 1]
	ld c, a
	jp .Script
.CapWord
; Clamp the big-endian word at HL to BC.
	ld a, [hli]
	cp b
	ret c
	jr nz, .cap_clamp
	ld a, [hl]
	cp c
	ret c
	ret z
.cap_clamp
	ld [hl], c
	dec hl
	ld [hl], b
	ret
.MinDeltaFor
; A=regime. A=that regime's compiled maximum minus minimum.
	ld c, a
	ld b, 0
	ld hl, .MinDeltaOffsets
	add hl, bc
	ld a, [hl]
	call .PlanAddress
	ld a, [hl]
	ret
.MinDeltaOffsets
	db FSR_MIN_DELTA0, FSR_MIN_DELTA1, FSR_MIN_DELTA2, FSR_MIN_DELTA3
.pursuit
	ld a, [FSE_FLAGS]
	or 1 << AV_UNKNOWN_TRANSITION_F
	ld [FSE_FLAGS], a
	jp .done
.recovery
	ld a, FSR_RECOVERY_QUOTA
	call .PlanWord
	call .Continuation
	inc hl
	inc hl
	call .PlayerMaximum
	ld a, [FSE_MODE]
	and a
	jr z, .recover_hp
	ld a, b
	or c
	jr z, .done
	ld a, [hli]
	cp d
	jr c, .recovery_gained
	jr nz, .done
	ld a, [hl]
	cp e
	jr nc, .done
	jr .recovery_gained
.recover_hp
	call BossAI_FastGainHP
	ld a, b
	or c
	jr z, .done
.recovery_gained
	ld a, FSR_MOVE
	call .PlanAddress
	ld a, [hl]
	cp REST
	jr nz, .done
	ld a, [FSE_FLAGS]
	or 1 << AV_UNKNOWN_TRANSITION_F
	ld [FSE_FLAGS], a
.done
	call .Continuation
	ld bc, 16
	add hl, bc
	ld a, [FSE_FLAGS]
	or [hl]
	ld [hl], a
	pop de
	scf
	ret
.SelfFaint
; Selfdestruct's user faints whether it hits or misses (not in flags-only mode).
	ld a, [FSE_MODE]
	and a
	ret nz
	call .Continuation
	inc hl
	inc hl
	xor a
	ld [hli], a
	ld [hl], a
	ret
.Regime
; Match the public model's finite 16-bit predicates, including wrapped 3*HP
; and 2*HP in the wide-HP domain. Regime=attacker-low + 2*defender-high.
	call .Continuation
	inc hl
	inc hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	call .PlayerMaximum
	ld a, l
	sub e
	ld a, h
	sbc d
	ld a, 0
	adc 0
	ld [FSE_REGIME], a
	call .Continuation
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ld a, [FSA_MAX_HP]
	cp b
	jr c, .high
	ret nz
	ld a, [FSA_MAX_HP + 1]
	cp c
	ret nc
.high
	ld a, [FSE_REGIME]
	or 2
	ld [FSE_REGIME], a
	ret
.PlayerMaximum
	ld a, [FSA_PLAYER + 2]
	ld d, a
	ld a, [FSA_PLAYER + 3]
	ld e, a
	ret
.PlanWord
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ret
.PlanAddress
	ld l, a
	ld h, 0
	ld a, [FSE_PLAN]
	ld b, a
	ld a, [FSE_PLAN + 1]
	ld c, a
	add hl, bc
	ret
.Continuation
	ld a, [FSE_CONT]
	ld h, a
	ld a, [FSE_CONT + 1]
	ld l, a
	ret
.Bits
	db 1, 2, 4, 8

ASSERT BANK(BossAI_FastExecuteReplyPlan) == BANK(BossAI_FastOwnCommandDescriptors)
