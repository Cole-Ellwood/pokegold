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
DEF FSE_OPCODE EQU $a53f
; Amount override for a defensive variant (the selector's boost pairs): the
; flag byte is exactly 1 while live (any other value is inactive, so poisoned
; scratch cannot arm it), then the raw minimum and bit0 range / bit1 supported.
DEF FSV_OVERRIDE EQU $a4b4
; Family scratch. It aliases the damage script's inputs and is consumed
; before .Script writes them.
DEF FSX_A EQU $a530 ; working amount (transition endpoint)
DEF FSX_B EQU $a532 ; working amount (other endpoint)
DEF FSX_HP EQU $a534
DEF FSX_TOTAL EQU $a536
DEF FSX_HITS EQU $a538
DEF FSX_MODE EQU $a539
DEF FSX_TOTAL2 EQU $a53a
DEF FSX_REGIME EQU $a53c
ASSERT FSX_REGIME < FSE_OPCODE
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
	and a
	jr z, .unrepresented
	cp FSP_BOOST + 1
	jr c, .represented
.unrepresented
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
	cp FSP_BOOST
	jp z, .done ; check flags only; the boost acts through the replies' variants
	cp FSP_RECOVERY
	jp z, .recovery
	ld [FSE_OPCODE], a
	ld a, FSP_DAMAGE_FLAGS
	call .PlanAddress
	ld a, [FSE_FLAGS]
	or [hl]
	ld [FSE_FLAGS], a
; amounts use the regime before Selfdestruct's self-faint
	call .Regime
	ld a, [FSE_OPCODE]
	cp FSP_SELFDESTRUCT
	jr nz, .no_self_faint
	ld a, [FSE_MODE]
	and a
	jr nz, .no_self_faint
	call .Continuation
	xor a
	ld [hli], a
	ld [hl], a ; the user faints even when it misses
.no_self_faint
	ld a, [FSE_EVENT]
	and a
	jp nz, .done
	ld a, FSP_ACCURACY
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
	ld a, [FSE_OPCODE]
	cp FSP_MULTI
	jr z, .support ; these families decide their range at execution
	cp FSP_FALSE_SWIPE
	jr z, .support
	cp FSP_FANG
	jr z, .support
	ld a, [FSV_OVERRIDE]
	cp 1 ; exactly 1 is live; poisoned or cleared scratch is not
	jr nz, .plan_range
	ld a, [FSV_OVERRIDE + 3]
	bit 0, a
	jr z, .support
	jr .range_flag
.plan_range
	ld a, FSP_RANGE
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr z, .support
.range_flag
	ld a, [FSE_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSE_FLAGS], a
.support
	ld a, [FSV_OVERRIDE]
	cp 1 ; exactly 1 is live; poisoned or cleared scratch is not
	jr nz, .plan_support
	ld a, [FSV_OVERRIDE + 3]
	bit 1, a
	jr nz, .raw
	jr .unsupported
.plan_support
	ld a, FSP_SUPPORT
	call .PlanAddress
	ld a, [FSE_MASK]
	and [hl]
	jr nz, .raw
.unsupported
	ld a, [FSE_FLAGS]
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld [FSE_FLAGS], a
	jp .done
.raw
	ld a, [FSE_OPCODE]
	cp FSP_MULTI
	jp z, .multi
	cp FSP_FANG
	jp z, .fang
	cp FSP_FALSE_SWIPE
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
	add FSP_RAW_MIN
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
.multi
; Hits advance the target's HP one at a time so later hits read the
; defender-high predicate at the reduced HP; the sequence stops at a KO and
; the saturating total keeps the final hit's overkill, like the kernel. The
; range flag compares the two endpoint paths' totals; the transition applies
; the minimum path's total through the single-hit script, whose items and
; drain use the total as the raw amount.
	ld a, FSP_MIN_HITS
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
	ld a, FSP_MAX_HITS
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
; minima, 1 the maxima.
; Leaves the saturating FSX_TOTAL.
	call .Continuation
	inc hl
	inc hl
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
	ld a, [FSA_PLAYER + 2]
	cp h
	jr c, .multi_high
	jr nz, .multi_regime
	ld a, [FSA_PLAYER + 2 + 1]
	cp l
	jr nc, .multi_regime
.multi_high
	set 1, c
.multi_regime
	ld a, c
	add a
	ld b, a
	ld a, [FSX_MODE]
	and a
	ld a, b
	jr nz, .multi_maximum
	add FSP_RAW_MIN
	jr .multi_word
.multi_maximum
	add FSP_RAW_MAX
.multi_word
	call .PlanWord
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
	add FSP_RAW_MIN
	call .PlanWord
	ld a, b
	or c
	jp z, .done
	call .Continuation
	inc hl
	inc hl
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
; differ; the transition applies the minimum endpoint.
	ld a, [FSE_REGIME]
	add a
	add FSP_RAW_MIN
	call .PlanWord
	ld a, b
	ld [FSX_A], a
	ld a, c
	ld [FSX_A + 1], a
	ld a, [FSE_REGIME]
	add a
	add FSP_RAW_MAX
	call .PlanWord
	ld a, b
	ld [FSX_B], a
	ld a, c
	ld [FSX_B + 1], a
	call .Continuation
	inc hl
	inc hl
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
