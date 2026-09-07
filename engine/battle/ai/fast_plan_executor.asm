; Consume an owned plan without reading the mutable producer context.
; This is one action, not a complete pair or selector. Setup/order flags are
; owned by the enclosing evaluation; reached flags accumulate in continuation16.
DEF FSA_PLAYER EQU FSA_OWN + 40
DEF FSE_PLAN EQU $a540
DEF FSE_CONT EQU FSE_PLAN + 2
DEF FSE_EVENT EQU FSE_CONT + 2
DEF FSE_FLAGS EQU FSE_EVENT + 1
DEF FSE_REGIME EQU FSE_FLAGS + 1
DEF FSE_MASK EQU FSE_REGIME + 1
; Sequential alias of standalone Delta's low byte. A flags-only pass never
; runs Delta; a normal action resets this byte before executing its script.
DEF FSE_MODE EQU $a54b ; 0execute,1flags only
ASSERT FSE_MASK < $a560
ASSERT FST_ACTUAL_LOSS + 2 <= FSE_PLAN

BossAI_FastExecuteOwnedPlan::
; C=plan index0..3, A=original event0hit/1miss, HL=24-byte continuation.
; SRAM0 open; own/player actor max HP words populated. DE/SP preserved.
; Preconditions: compiled plan, HP<=max, fixed non-HP public facts and unchanged
; defense regime. Caller falls back if an earlier action invalidates those facts.
; Carry=accepted. Unsupported opcode returns clear without continuation writes.
; Invalid index/event rejects before any write. Accepted writes only own/player
; HP and flags in this continuation, plus the assigned executor working area.
	ld b, 0
	jr .validate
.FlagsOnly
; Same ABI/acceptance, but only continuation16 changes. Used to union flags
; over positive original-event paths without computing terminal damage again.
	ld b, 1
.validate
	cp 2
	jr nc, .invalid
	push af
	ld a, c
	cp 4
	jr nc, .invalid_pop
	pop af
	ld [FSE_EVENT], a
	ld a, b
	ld [FSE_MODE], a
	ld a, h
	ld [FSE_CONT], a
	ld a, l
	ld [FSE_CONT + 1], a
	push de
	ld b, 0
	rept 6
	sla c
	rl b
	endr
	ld hl, FSP_BASE
	add hl, bc
	ld a, h
	ld [FSE_PLAN], a
	ld a, l
	ld [FSE_PLAN + 1], a
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_DAMAGE
	jr z, .represented
	cp FSP_RECOVERY
	jr z, .represented
	pop de
	and a
	ret
.invalid_pop
	pop af
.invalid
	and a
	ret
.represented
	xor a
	ld [FSE_FLAGS], a
	call .Continuation
	ld a, [hli]
	or [hl]
	jp z, .done
	inc hl
	ld a, [hli]
	or [hl]
	jp z, .done
	ld a, FSP_CHECK_FLAGS
	call .PlanAddress
	ld a, [hl]
	ld [FSE_FLAGS], a
	ld a, FSP_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .done
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_RECOVERY
	jp z, .recovery
	ld a, FSP_DAMAGE_FLAGS
	call .PlanAddress
	ld a, [FSE_FLAGS]
	or [hl]
	ld [FSE_FLAGS], a
	ld a, [FSE_EVENT]
	and a
	jp nz, .done
	ld a, FSP_ACCURACY
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
	ld a, FSP_RANGE
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr z, .support
	ld a, [FSE_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSE_FLAGS], a
.support
	ld a, FSP_SUPPORT
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr nz, .raw
	ld a, [FSE_FLAGS]
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld [FSE_FLAGS], a
	jp .done
.raw
	ld a, [FSE_MODE]
	and a
	jp nz, .done
	ld a, [FSE_REGIME]
	add a
	add FSP_RAW_MIN
	call .PlanWord
	ld a, b
	ld [FST_RAW], a
	ld a, c
	ld [FST_RAW + 1], a
	or b
	jp z, .done
	call .Continuation
	ld a, h
	ld [FST_USER_HP], a
	ld a, l
	ld [FST_USER_HP + 1], a
	inc hl
	inc hl
	ld a, h
	ld [FST_TARGET_HP], a
	ld a, l
	ld [FST_TARGET_HP + 1], a
	ld a, [FSA_MAX_HP]
	ld [FST_USER_MAX], a
	ld a, [FSA_MAX_HP + 1]
	ld [FST_USER_MAX + 1], a
	ld a, FSP_STEEL
	call .PlanAddress
	ld a, [hl]
	ld [FST_RECOIL], a
	ld a, FSP_DESCRIPTOR
	call .PlanWord
	ld h, b
	ld l, c
	ld a, [hli]
	ld [FST_EFFECT], a
	ld a, [hl]
	ld [FST_ITEM], a
	cp 2
	jr z, .shell_bell
	ld a, FSP_ITEM_QUOTA
	call .PlanWord
	jr .item_quota
.shell_bell
	ld a, [FST_RAW]
	ld b, a
	ld a, [FST_RAW + 1]
	ld c, a
	rept 3
	srl b
	rr c
	endr
	ld a, b
	or c
	jr nz, .item_quota
	inc c
.item_quota
	ld a, b
	ld [FST_ITEM_QUOTA], a
	ld a, c
	ld [FST_ITEM_QUOTA + 1], a
	call BossAI_FastDamageScript
	jp .done
.recovery
	ld a, FSP_RECOVERY_QUOTA
	call .PlanWord
	call .Continuation
	call .OwnMaximum
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
	ld a, FSP_MOVE
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
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	call .OwnMaximum
	ld a, l
	sub e
	ld a, h
	sbc d
	ld a, 0
	adc 0
	ld [FSE_REGIME], a
	call .Continuation
	inc hl
	inc hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ld a, [FSA_PLAYER + 2]
	cp b
	jr c, .high
	ret nz
	ld a, [FSA_PLAYER + 3]
	cp c
	ret nc
.high
	ld a, [FSE_REGIME]
	or 2
	ld [FSE_REGIME], a
	ret
.OwnMaximum
	ld a, [FSA_MAX_HP]
	ld d, a
	ld a, [FSA_MAX_HP + 1]
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

ASSERT BANK(BossAI_FastExecuteOwnedPlan) == BANK(BossAI_FastOwnCommandDescriptors)
