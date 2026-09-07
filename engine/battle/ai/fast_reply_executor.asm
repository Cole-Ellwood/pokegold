; Execute the compact incoming plan without mutable producer reads.
; Uses the same sequential executor scratch as owned actions, never their plans.
BossAI_FastExecuteReplyPlan::
; DE=context base (only reply399..446 read), HL=continuation24,
; A=original event0hit/1miss. SRAM0 open; actors' maximum HP populated.
; DE/SP preserved. Carry=accepted; unsupported opcode rejects without
; continuation writes. Invalid event rejects without any writes.
; Fixed defense/status/other non-HP facts must match the compiled plan.
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
	cp FSR_ABSENT + 1
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
	ld a, FSR_DAMAGE_FLAGS
	call .PlanAddress
	ld a, [FSE_FLAGS]
	or [hl]
	ld [FSE_FLAGS], a
	ld a, [FSE_EVENT]
	and a
	jp nz, .done
	ld a, FSR_ACCURACY
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .done
	call .Regime
	ld a, [FSE_REGIME]
	ld c, a
	ld b, 0
	ld hl, .Bits
	add hl, bc
	ld a, [hl]
	ld [FSE_MASK], a
	ld a, FSR_RANGE
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr z, .support
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
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSE_REGIME]
	add a
	add FSR_RAW_MAX
	call .PlanWord
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
