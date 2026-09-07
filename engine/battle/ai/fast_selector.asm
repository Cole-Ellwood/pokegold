; Native selector orchestration. Ordinary decisions stream one compiled reply
; per defender over standalone moments plus correction-only pair terms;
; replacement decisions value entry potentials directly. Invalid HP domains
; discard native state and restart through the complete compatibility adapter.
; This is the structural prototype, not the timing gate.
DEF FS_DEFENDER EQU FS_CONTROL + 2 ; $ff active, else bench slot (also the bench cursor)
DEF FS_NATIVE_SLOT EQU FS_DEFENDER
DEF FS_NATIVE_LEFT EQU FS_CONTROL + 3
DEF FS_PLAN EQU FS_CONTROL + 5 ; plan cursor
DEF FS_REPLY_ID EQU FS_CONTROL + 6
DEF FS_REPLY_LEFT EQU FS_CONTROL + 7
DEF FS_REPLY_W EQU FS_CONTROL + 8
DEF FS_UNARY_INDEX EQU FS_CONTROL + 9 ; wait/switch record index, $ff none
DEF FS_UNARY_KIND EQU FS_CONTROL + 10
DEF FS_PLAN_FLAGS EQU FS_CONTROL + 11 ; setup|open prior|unknown order, move plans
DEF FS_UNARY_FLAGS EQU FS_CONTROL + 12 ; setup|open prior(|wait checks), unary candidate; reached reply flags accumulate here during the sweep
DEF FS_TIE_ORDER EQU FS_CONTROL + 4 ; order of an equal-priority pair for this defender's speeds
; Defensive variants of the four plans at the start regime: per plan two
; three-byte slots (raw minimum, then bit0 range / bit1 supported / bit2
; special-defense axis / bit7 valid): slot 0 Defense+1, slot 1 Defense+2 for
; a physical plan or Special Defense+2 for a special one.
DEF FSV_BASE EQU $a4f8 ; 24 bytes (the former physical base cache high part)
DEF FS_REPLY_REGIMES EQU FS_CONTROL + 13 ; HP regimes a reply can reach for this defender
DEF FS_REPLY_IDENTITY EQU FS_CONTROL + 18 ; 1 when the current reply never changes HP
DEF FS_ORDER EQU FS_CONTROL + 19 ; order descriptor of the pair being evaluated
DEF FS_PLAN_INDEX EQU FS_CONTROL + 14 ; four original result indices, $ff unused
DEF FSA_OWN_SPEED EQU FSA_OWN + 14
DEF FSA_ITEM_CLASS EQU FSA_OWN + 32 ; 1=Quick Claw
DEF FSA_SETUP_FLAGS EQU FSA_OWN + 35
DEF FSA_SPEED_MODE EQU FSA_OWN + 36 ; bit0: public order unknown
DEF FSA_PLAYER_SPEED EQU FSA_PLAYER + 14
ASSERT FS_PLAN_INDEX + 4 <= FS_LEGAL_MASK - 1

BossAI_ComparePublicActionsFastPrototype::
; DE=472-byte context, A=decision0/2, B=scan0..15, SRAM closed. Same full
; record ABI/finalizer as the compatibility adapter. Both decision kinds are
; evaluated natively; ordinary pairs may use the direct fallback (status 1).
	ld c, a
	push bc
	call BossAI_FastPreparePublicInputs
	pop bc
	jp nc, .reference
	xor a
	call OpenSRAM
	call BossAI_FastClearResults
	ad_address FS_LEGAL_MASK
	xor a
	ld [hli], a
	ld [hl], a
	ad_address FS_KIND ; result clearing clobbers C
	ld a, [hl]
	cp AV_REPLACEMENT_ACTION
	jr z, .replacement
	ad_address FS_BACKEND
	ld [hl], 0
	xor a
	ld [FSC_FAULT], a
	ld [FSV_OVERRIDE], a ; no defensive variant is live
	call .ReplyMass
	jp nc, .restart
	call .ActiveDefender
	jp nc, .restart
	call .BenchStart
.bench
	call .BenchLegal
	jr z, .bench_next
	call .SwitchDefender
	jp nc, .restart
.bench_next
	call .BenchAdvance
	jr nz, .bench
	ld a, [FSC_FAULT]
	and a
	jp nz, .restart ; an incoming plan ran at a regime the mask did not cover
	jp BossAI_FastFinalizeResults

.replacement
; One absent reply, weight 1: T=2*65536*(1024+entry delta) from HP potentials.
	call .BenchStart
.replacement_slot
	call .BenchLegal
	jr z, .replacement_next
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	farcall BossAI_FastPrepareReplacementFacts
	ld a, [FSA_MAX_HP]
	ld b, a
	ld a, [FSA_MAX_HP + 1]
	ld c, a
	ld a, [FSA_START_HP]
	cp b
	jr c, .valid_hp
	jp nz, .restart
	ld a, [FSA_START_HP + 1]
	cp c
	jr c, .valid_hp
	jp nz, .restart
.valid_hp
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastBuildHPTable
	jp nc, .restart
	ld [FSA_HP_MODE], a
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	call .Potential
	ld a, b
	ld [FSA_START_PHI], a
	ld a, c
	ld [FSA_START_PHI + 1], a
	call .ApplyEntry
	ld hl, 1024
	add hl, bc
	ld a, [FSA_START_PHI + 1]
	ld c, a
	ld a, l
	sub c
	ld c, a
	ld a, [FSA_START_PHI]
	ld b, a
	ld a, h
	sbc b
	ld b, a
	call .StoreReplacementRecord
.replacement_next
	call .BenchAdvance
	jr nz, .replacement_slot
	ad_address FS_BACKEND
	ld [hl], 0
	jp BossAI_FastFinalizeResults

.restart
	call CloseSRAM ; discard native state before the old JC lifetime begins
	ad_address FS_KIND
	ld c, [hl]
	inc hl
	ld b, [hl]
.reference
	farcall BossAI_FastReferenceRestartFromC
	ret

.BenchStart
	ad_address FS_SCAN
	bit 0, [hl]
	ld a, 0
	jr z, .bench_first
	ld a, PARTY_LENGTH - 1
.bench_first
	ad_address FS_NATIVE_SLOT
	ld [hli], a
	ld [hl], PARTY_LENGTH
	ret
.BenchLegal
; Z when the cursor's bench slot is not a legal switch/replacement entry.
	ad_address FS_NATIVE_SLOT
	ld c, [hl]
	ld b, 0
	ld hl, .SlotBits
	add hl, bc
	ld a, [hl]
	ad_address FS_ACTIONS + AC_SWITCH_MASK
	and [hl]
	ret
.BenchAdvance
; Z when every bench slot has been visited.
	ad_address FS_NATIVE_LEFT
	dec [hl]
	ret z
	ad_address FS_SCAN
	bit 0, [hl]
	ad_address FS_NATIVE_SLOT
	jr nz, .bench_previous
	inc [hl]
	jr .bench_advanced
.bench_previous
	dec [hl]
.bench_advanced
	or 1
	ret

.ApplyEntry
; Own actor and table live. Entry HP/Phi follow the bridge's entry loss;
; BC=entry Phi.
	ld a, [FSB_ENTRY_LOSS]
	ld b, a
	ld a, [FSB_ENTRY_LOSS + 1]
	ld c, a
	ld hl, FSA_ENTRY_HP
	call BossAI_FastLoseHP
	ld a, [FSA_ENTRY_HP]
	ld b, a
	ld a, [FSA_ENTRY_HP + 1]
	ld c, a
	call .Potential
	ld a, b
	ld [FSA_ENTRY_PHI], a
	ld a, c
	ld [FSA_ENTRY_PHI + 1], a
	ret
.Potential
	push de
	ld a, [FSA_HP_MODE]
	ld d, a
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastHPPotential
	pop de
	ret
.StoreReplacementRecord
; BC=1024+entryPhi-startPhi. One absent reply/order has M=2 and T=score*2*65536.
	push bc
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	add NUM_MOVES
	call .RecordPointer
	pop bc
	xor a
	ld [hli], a
	sla c
	rl b
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld a, 2
	ld [hli], a
	xor a
	ld [hli], a
	ld [hli], a
	ld a, [FSB_SETUP_FLAGS]
	ld [hl], a
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	add NUM_MOVES
	jp .SetLegal
.SlotBits
	db 1, 2, 4, 8, 16, 32

; ---------------------------------------------------------------------------
; Ordinary decisions

.ReplyMass
; W_R=sum of reply weights into FS_REPLY_WEIGHT; M=2*W_R into FSC_MASS.
; Carry iff 1<=W_R<=282 so that M<=564 stays inside the finalizer's domain.
	ld bc, 0
	ld a, 1
.mass_reply
	push af
	push bc
	call .ReplyWeight
	pop bc
	jr nc, .mass_next
	add c
	ld c, a
	ld a, b
	adc 0
	ld b, a
.mass_next
	pop af
	inc a
	cp NUM_ATTACKS + 1
	jr c, .mass_reply
	ld a, b
	or c
	ret z
	ld a, b
	cp HIGH(283)
	jr c, .mass_ok
	ret nz
	ld a, c
	cp LOW(283)
	ret nc
.mass_ok
	av_store_word FS_REPLY_WEIGHT
	sla c
	rl b
	ld a, b
	ld [FSC_MASS], a
	ld a, c
	ld [FSC_MASS + 1], a
	scf
	ret

.ReplyWeight
; A=move ID. Carry when the reply is possible, then A=its weight.
	ld c, a
	ld hl, FS_REPLIES + PR_POSSIBLE
	call .ReplyBit
	ret z
	ld a, c
	ld hl, FS_REPLIES + PR_REVEALED
	call .ReplyBit
	ld a, 1
	jr z, .weight_ready
	ld a, JC_REVEALED_WEIGHT
.weight_ready
	scf
	ret
.ReplyBit
; A=move ID, HL=set offset in the context. Z means absent; C preserved.
	push bc
	add hl, de
	ld c, a
	srl a
	srl a
	srl a
	ld b, 0
	push bc
	ld c, a
	add hl, bc
	pop bc
	ld a, c
	and 7
	ld c, a
	push hl
	ld hl, .BitMasks
	add hl, bc
	ld a, [hl]
	pop hl
	and [hl]
	pop bc
	ret
.BitMasks
	db 1, 2, 4, 8, 16, 32, 64, 128

.OpenPrior
; A=the open-moveset prior flag for non-replacement candidates, else 0.
	ad_address FS_REPLIES + PR_FLAGS
	bit PR_FOUR_REVEALED_F, [hl]
	ld a, 0
	ret nz
	ld a, 1 << JC_PUBLIC_PRIOR_F
	ret

.ClearPlanIndex
	ad_address FS_PLAN_INDEX
	ld a, $ff
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ret
.PlanIndex
; C=plan slot. A=original result index ($ff unused); BC preserved.
	push bc
	ad_address FS_PLAN_INDEX
	ld b, 0
	add hl, bc
	ld a, [hl]
	pop bc
	ret
.PlanAddress
; C=plan slot, A=field offset. HL=field address; BC/DE preserved.
	push bc
	ld l, c
	ld h, 0
	rept 6
	add hl, hl
	endr
	ld c, a
	ld b, 0
	add hl, bc
	ld bc, FSP_BASE
	add hl, bc
	pop bc
	ret

.ActiveDefender
; Moves, the forced action and wait share the active actor, one reply sweep
; and one shared incoming moment sum. Carry=complete; clear=invalid HP domain.
	ld a, $ff
	ad_address FS_DEFENDER
	ld [hl], a
	ad_address FS_UNARY_INDEX
	ld [hl], a
	call .ClearPlanIndex
	ad_address FS_UNARY_KIND
	ld [hl], AV_WAIT_ACTION
	ad_address FS_ACTIONS + AC_MODE
	ld a, [hl]
	cp AC_CHOICE
	jr z, .choice
	cp AC_WAIT
	ld a, NUM_MOVES + PARTY_LENGTH + 1
	jr z, .unary_index
	farcall BossAI_FastForcedAction
	ld a, c
	dec a
	jr nz, .forced_wait
	ld c, 0
	ld a, NUM_MOVES + PARTY_LENGTH
	call .AddPlan
	jr .candidates_ready
.forced_wait
	ld a, NUM_MOVES + PARTY_LENGTH
.unary_index
	ad_address FS_UNARY_INDEX
	ld [hl], a
	jr .candidates_ready
.choice
	ld c, 0
.choice_slot
	ad_address FS_ACTIONS + AC_MOVES
	ld b, 0
	add hl, bc
	ld a, [hl]
	and a
	jr z, .choice_next
	ld b, a
	ld a, c
	push bc
	call .AddPlan
	pop bc
.choice_next
	inc c
	ld a, c
	cp NUM_MOVES
	jr c, .choice_slot
.candidates_ready
	farcall BossAI_FastPrepareActiveFacts
	ad_address AV_WEIGHT
	ld c, [hl]
	call BossAI_FastImportActorHP
	ret nc
	call BossAI_FastPrepareReplyFacts
	call .ImportOrderFacts
	call .TieOrder
	ld a, [FSA_SETUP_FLAGS]
	ld b, a
	call .OpenPrior
	or b
	ld b, a
	ld a, [FSB_PREFIX_CHECK]
	or b
	ad_address FS_UNARY_FLAGS
	ld [hl], a
	ld a, [FSA_SPEED_MODE]
	and a
	ld a, b
	jr z, .plan_flags
	or 1 << AV_UNKNOWN_ORDER_F
.plan_flags
	ad_address FS_PLAN_FLAGS
	ld [hl], a
	xor a
	ld [FSC_ENTRY_DELTA], a
	ld [FSC_ENTRY_DELTA + 1], a
	call .UnaryBaseline
	ld c, 0
.plan_init
	call .PlanIndex
	cp $ff
	jr z, .plan_init_next
	push bc
	call BossAI_FastBuildOwnedStandalone ; fallback plans keep zero moments
	pop bc
	push bc
	call .InitMovePlan
	pop bc
.plan_init_next
	inc c
	ld a, c
	cp 4
	jr c, .plan_init
	call .InitUnaryRecord
	call .ReplyRegimes
	call .ReplySweep
	ret nc
	call .CommitIncoming
	scf
	ret

.ReplyRegimes
; FS_REPLY_REGIMES=bit per incoming HP regime reachable on this defender: the
; start state plus every live plan's original-event successors. Regime bit0 is
; the player's attacker-low predicate 3*HP<max, bit1 the own defender-high
; predicate 2*HP>max, both in the executor's wrapped 16-bit arithmetic.
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	ld hl, FSA_PLAYER
	call .ReplyRegimeBit
	ld b, a
	ld c, 0
.regime_plan
	push bc
	call .PlanIndex
	cp $ff
	jr z, .regime_next
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .regime_next
	ld a, FSP_HIT_HP
	call .PlanAddress
	call .SuccessorRegimeBit
	pop bc
	or b
	ld b, a
	push bc
	ld a, FSP_MISS_HP
	call .PlanAddress
	call .SuccessorRegimeBit
	pop bc
	or b
	ld b, a
	push bc
.regime_next
	pop bc
	inc c
	ld a, c
	cp 4
	jr c, .regime_plan
	ld a, b
	ad_address FS_REPLY_REGIMES
	ld [hl], a
	ret
.SuccessorRegimeBit
; HL=plan successor: own HP word then player HP word.
	ld a, [hli]
	ld b, a
	ld c, [hl]
	inc hl
.ReplyRegimeBit
; BC=own HP, HL=player HP word. A=1<<regime for an incoming action from that
; state. BC/HL scratch; DE preserved.
	push de
	push bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc ; 3*player HP, wrapped like the executor
	ld a, [FSA_PLAYER + 3]
	ld e, a
	ld a, [FSA_PLAYER + 2]
	ld d, a
	ld a, l
	sub e
	ld a, h
	sbc d
	ld a, 0
	adc 0 ; 1 when 3*HP<max
	pop bc
	sla c
	rl b ; 2*own HP, wrapped
	ld e, a
	ld a, [FSA_MAX_HP]
	cp b
	jr c, .regime_high
	jr nz, .regime_bit
	ld a, [FSA_MAX_HP + 1]
	cp c
	jr nc, .regime_bit
.regime_high
	set 1, e
.regime_bit
	ld d, 0
	ld hl, .RegimeBits
	add hl, de
	ld a, [hl]
	pop de
	ret
.RegimeBits
	db 1, 2, 4, 8

.AddPlan
; C=plan slot, B=move, A=original result index. Compiles the plan now.
	push bc
	push af
	ad_address FS_PLAN_INDEX
	ld b, 0
	add hl, bc
	pop af
	ld [hl], a
	pop bc
	ad_address AV_SLOT
	ld [hl], $ff
	ad_address AV_KIND
	ld [hl], AV_MOVE_ACTION
	ad_address AV_MOVE
	ld [hl], b
	ad_address AV_BRANCH
	ld [hl], 0
	push bc
	farcall BossAI_FastPrepareOwnedCandidate
	pop bc
	jr .PlanVariants
.PlanVariants
; C=plan slot, AD prefix=this plan's outgoing context. For a plain damage plan
; store the raw minimum at the start regime against the player's raised
; defense (see FSV_BASE); other opcodes leave both slots invalid.
	ld a, c
	add a
	ld l, a
	add a
	add l ; 6*slot
	ld l, a
	ld h, 0
	push bc
	ld bc, FSV_BASE
	add hl, bc
	pop bc
	ld a, h
	ld [FSC_TEMP], a
	ld a, l
	ld [FSC_TEMP + 1], a
	xor a
	inc hl
	inc hl
	ld [hli], a ; slot 0 invalid
	inc hl
	inc hl
	ld [hl], a ; slot 1 invalid
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_DAMAGE
	ret nz
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	jr nc, .special_variants
	ld bc, $0101 ; Defense+1
	call .Variant
	call .NextVariantSlot
	ld bc, $0201 ; Defense+2
	jr .Variant
.special_variants
	call .NextVariantSlot
	ld bc, $0204 ; Special Defense+2
	jr .Variant
.NextVariantSlot
; FSC_TEMP += 3 (the slots straddle the $a500 page boundary).
	ld a, [FSC_TEMP + 1]
	add 3
	ld [FSC_TEMP + 1], a
	ret nc
	ld hl, FSC_TEMP
	inc [hl]
	ret
.Variant
; B=stages, C=axis, FSC_TEMP=destination slot. Runs the producer's range at
; the start regime with the raised player defense and restores the plan's
; context bytes it changed.
	push bc
	ad_address AD_DEFENSE
	ld a, [hli]
	ld [FSC_TEMP + 2], a
	ld a, [hl]
	ld [FSC_TEMP + 3], a
	ad_address AD_FLAGS
	ld a, [hl]
	ld [FSC_TEMP + 4], a
	call .OutgoingStartRegime
	add a
	ld b, a
	ld a, [FSC_TEMP + 4]
	and ~((1 << AD_ATTACKER_LOW_F) | (1 << AD_DEFENDER_HIGH_F))
	or b
	ad_address AD_FLAGS
	ld [hl], a
	pop bc
	push bc
	farcall BossAI_FastProjectPlayerDefense
	farcall BossAI_FastExportDamageRange
	pop bc
	ld a, [FSC_TEMP]
	ld h, a
	ld a, [FSC_TEMP + 1]
	ld l, a
	ld a, [FSB_RAW_MIN]
	ld [hli], a
	ld a, [FSB_RAW_MIN + 1]
	ld [hli], a
	ld a, [FSB_RANGE_FLAGS]
	and 1 << AV_AMOUNT_RANGE_F
	jr z, .variant_range_ready
	ld a, 1
.variant_range_ready
	ld b, a
	ld a, [FSB_RANGE_SUPPORT]
	and a
	jr z, .variant_support_ready
	ld a, 2
.variant_support_ready
	or b
	set 7, a
	ld b, a
	ld a, c
	cp 4
	ld a, b
	jr nz, .variant_axis_ready
	set 2, a
.variant_axis_ready
	ld [hl], a
	ld a, [FSC_TEMP + 2]
	ad_address AD_DEFENSE
	ld [hli], a
	ld a, [FSC_TEMP + 3]
	ld [hl], a
	ld a, [FSC_TEMP + 4]
	ad_address AD_FLAGS
	ld [hl], a
	ret
.OutgoingStartRegime
; A=the own attack's regime at the start state from the plan context:
; attacker-low (3*own HP below own max) plus twice defender-high (2*player HP
; above player max), in the executors' wrapped 16-bit arithmetic.
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	push hl
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, l
	sub c
	ld a, h
	sbc b
	ld a, 0
	adc 0
	push af
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ad_address AD_DEFENDER_MAXHP
	ld a, [hli]
	cp b
	jr c, .outgoing_high
	jr nz, .outgoing_low
	ld a, [hl]
	cp c
	jr nc, .outgoing_low
.outgoing_high
	pop af
	or 2
	ret
.outgoing_low
	pop af
	ret

.ImportOrderFacts
; Speeds, speed mode, item class and setup flags into the actor views.
	av_load_word AV_OWN_SPEED
	ld a, b
	ld [FSA_OWN_SPEED], a
	ld a, c
	ld [FSA_OWN_SPEED + 1], a
	av_load_word AV_PLAYER_SPEED
	ld a, b
	ld [FSA_PLAYER_SPEED], a
	ld a, c
	ld [FSA_PLAYER_SPEED + 1], a
	ad_address AV_BRANCH
	ld a, [hl]
	and 1 << AV_PREPARED_SPEED_UNKNOWN_F
	ld a, 0
	jr z, .speed_mode
	inc a
.speed_mode
	ld [FSA_SPEED_MODE], a
	ld a, [FSB_QUICK_CLAW]
	ld [FSA_ITEM_CLASS], a
	ld a, [FSB_SETUP_FLAGS]
	ld [FSA_SETUP_FLAGS], a
	ret

.SwitchDefender
; One bench entry at the cursor: entry hazards on a fresh actor, then one reply
; sweep whose baseline is the post-entry state. Carry=complete.
	call .ClearPlanIndex
	ad_address FS_DEFENDER
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	add NUM_MOVES
	ad_address FS_UNARY_INDEX
	ld [hl], a
	ad_address FS_UNARY_KIND
	ld [hl], AV_SWITCH_ACTION
	ad_address AV_KIND
	ld [hl], AV_SWITCH_ACTION
	ad_address AV_MOVE
	ld [hl], STRUGGLE
	ad_address AV_BRANCH
	ld [hl], 0
	farcall BossAI_FastPrepareReplacementFacts
	ld a, [FSA_WEIGHT]
	ld c, a
	call BossAI_FastImportActorHP
	ret nc
	call .ApplyEntry
	ld a, [FSA_START_PHI + 1]
	ld l, a
	ld a, c
	sub l
	ld [FSC_ENTRY_DELTA + 1], a
	ld a, [FSA_START_PHI]
	ld h, a
	ld a, b
	sbc h
	ld [FSC_ENTRY_DELTA], a
; The post-entry state is the standalone baseline for every reply.
	ld hl, FSA_ENTRY_HP
	ld a, [hli]
	ld [FSA_START_HP], a
	ld a, [hli]
	ld [FSA_START_HP + 1], a
	ld a, [hli]
	ld [FSA_START_PHI], a
	ld a, [hl]
	ld [FSA_START_PHI + 1], a
	ld a, [FSB_SETUP_FLAGS]
	ld b, a
	call .OpenPrior
	or b
	ad_address FS_UNARY_FLAGS
	ld [hl], a
	call .UnaryBaseline
	call .InitUnaryRecord
	call .ReplyRegimes
	farcall BossAI_PreparePublicAction ; this bench actor's reply epoch
	call BossAI_FastPrepareReplyFacts
	call .ReplySweep
	ret nc
	call .CommitIncoming
	scf
	ret

.EntryUtility
; BC=1024+entry delta.
	ld a, [FSC_ENTRY_DELTA + 1]
	ld c, a
	ld a, [FSC_ENTRY_DELTA]
	ld b, a
	ld hl, 1024
	add hl, bc
	ld b, h
	ld c, l
	ret
.UnaryBaseline
; FSC_BASELINE=(1024+entry delta)<<17.
	ld hl, FSC_BASELINE
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	push hl
	call .EntryUtility
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	ld hl, FSC_BASELINE
	ld b, 17
	jp .ShiftLeft

.InitMovePlan
; C=plan slot. T=M<<26+(M<<8)*mu_own, mass M, plan flags, legal bit.
	call .PlanIndex
	cp $ff
	ret z
	push bc
	push af
	ld hl, FSC_TEMP
	ld b, 26
	call .MassShiftedTo
	pop af
	push af
	ld hl, FSC_TEMP
	call .CopyToRecord
	pop af
	pop bc
	push af
	ld a, FSP_MOMENT
	call .PlanAddress
	call .SignExtend24
	call .MassMultiplier8
	call BossAI_FastMultiply40By24
	pop af
	push af
	ld hl, FS_PRODUCT
	call .AddToRecord
	pop af
	ad_address FS_PLAN_FLAGS
	ld b, [hl]
	jp .SetRecordMeta

.InitUnaryRecord
; Wait or switch: T=(M<<16)*(1024+entry delta), mass M, unary flags, legal bit.
	ad_address FS_UNARY_INDEX
	ld a, [hl]
	cp $ff
	ret z
	push af
	ld hl, FS_MULTIPLICAND
	ld b, 16
	call .MassShiftedTo
	call .EntryUtility
	xor a
	ld [FS_MULTIPLIER], a
	ld a, b
	ld [FS_MULTIPLIER + 1], a
	ld a, c
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
	pop af
	push af
	ld hl, FS_PRODUCT
	call .CopyToRecord
	pop af
	ad_address FS_UNARY_FLAGS
	ld b, [hl]
	jp .SetRecordMeta

.ReplySweep
; Stream every possible reply once for the current defender. Carry=complete.
	ld hl, FSC_INCOMING
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ad_address FS_SCAN
	bit 1, [hl]
	ld a, 1
	jr z, .first_reply
	ld a, NUM_ATTACKS
.first_reply
	ad_address FS_REPLY_ID
	ld [hli], a
	ld [hl], NUM_ATTACKS
.reply
	ad_address FS_REPLY_ID
	ld a, [hl]
	call .ReplyWeight
	jr nc, .reply_next
	ad_address FS_REPLY_W
	ld [hl], a
	call .PrepareReply
	jr nc, .reply_fallback
	call .ReplyStandalone
	ret nc
	call .AccumulateIncoming
	jr .reply_plans
.reply_fallback
; A rejected compile must still have written this reply's header; a stale
; record would feed the direct fallback the wrong move.
	ld hl, FSR_BASE + FSR_MOVE
	add hl, de
	ld a, [hl]
	ad_address FS_REPLY_ID
	cp [hl]
	jr z, .header_ok
	and a
	ret
.header_ok
	call .UnaryFallback
	ret nc
.reply_plans
	call .Plans
	ret nc
.reply_next
	ad_address FS_REPLY_LEFT
	dec [hl]
	jr z, .sweep_done
	ad_address FS_SCAN
	bit 1, [hl]
	ad_address FS_REPLY_ID
	jr nz, .previous_reply
	inc [hl]
.skip_empty
; Forward walks skip whole empty bytes of the possible set.
	ld a, [hl]
	and 7
	jp nz, .reply
	ld a, [hl]
	rrca
	rrca
	rrca
	and $1f
	ld c, a
	ld b, 0
	ad_address FS_REPLIES + PR_POSSIBLE
	add hl, bc
	ld a, [hl]
	and a
	jp nz, .reply
	ad_address FS_REPLY_LEFT
	ld a, [hl]
	cp 9
	jp c, .reply ; fewer than eight IDs left: finish them one by one
	sub 8
	ld [hl], a
	ad_address FS_REPLY_ID
	ld a, [hl]
	add 8
	ld [hl], a
	jr .skip_empty
.previous_reply
	dec [hl]
	jp .reply
.sweep_done
	scf
	ret

.PrepareReply
; Marshal the defender/reply selectors, then bridge template + compile.
	ad_address FS_DEFENDER
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	inc a
	ld a, AV_MOVE_ACTION
	jr z, .reply_kind
	ld a, AV_SWITCH_ACTION
.reply_kind
	ad_address AV_KIND
	ld [hl], a
	ad_address FS_REPLY_ID
	ld a, [hl]
	ad_address AV_REPLY
	ld [hl], a
	ad_address AV_BRANCH
	ld [hl], 0
	ad_address FS_REPLY_REGIMES
	ld c, [hl]
	ad_address FS_REPLY_ID
	ld a, [hl]
	jp BossAI_FastCompileReplyNative

.ReplyStandalone
; Standalone record for the compiled reply. Identity replies (no HP change
; from any state) get their trivial record directly; plain families take the
; scalar path; the rest use the sequential builder, whose continuation flags
; are copied into the record. Carry=complete.
	call .ClassifyIdentity
	ad_address FS_REPLY_IDENTITY
	ld a, [hl]
	and a
	jr nz, .IdentityStandalone
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_BOOST
	jr z, .IdentityStandalone ; no HP change, check flags only (damage flags are zero)
	call BossAI_FastScalarReplyStandalone
	ret c
	call BossAI_FastBuildReplyStandalone
	ret nc
	ld a, [$a458] ; original-hit continuation flags
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld [hli], a
	ld a, [$a470] ; original-miss continuation flags
	ld [hl], a
	scf
	ret
.IdentityStandalone
; Both successors are the start state and the deltas and moment are zero.
; The flags follow the executor's gates at the start state: the check flags,
; plus the damage flags when the reply can act, plus unknown damage on the
; hit of a reply whose compiled regimes are unsupported (accuracy permitting).
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	ld b, 2
.identity_successor
	ld a, [FSA_START_HP]
	ld [hli], a
	ld a, [FSA_START_HP + 1]
	ld [hli], a
	ld a, [FSA_PLAYER]
	ld [hli], a
	ld a, [FSA_PLAYER + 1]
	ld [hli], a
	dec b
	jr nz, .identity_successor
	xor a
	rept 7
	ld [hli], a
	endr
	ld hl, FSR_BASE + FSR_CHECK_FLAGS
	add hl, de
	ld b, [hl]
	ld c, b
	dec hl
	ld a, [hl] ; FSR_CAN_ACT
	and a
	jr z, .identity_flags
	inc hl
	inc hl
	ld a, [hl] ; FSR_DAMAGE_FLAGS
	or b
	ld b, a
	ld c, a
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_BOOST
	jr z, .identity_flags ; a boost is not an amount: no unknown-damage bit
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .identity_flags
	ld hl, FSR_BASE + FSR_VALID
	add hl, de
	ld a, [hli]
	inc hl
	and [hl] ; FSR_SUPPORT within the compiled regimes
	jr nz, .identity_flags
	ld a, b
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld b, a
.identity_flags
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld a, b
	ld [hli], a
	ld [hl], c
	scf
	ret
.ClassifyIdentity
; FS_REPLY_IDENTITY=1 when the reply changes no HP from any state and its
; flags do not depend on the state: a damage opcode whose compiled regimes
; are all unsupported with zero power, or all supported with zero amounts and
; no range bits, or a reply that cannot act.
	xor a
	ad_address FS_REPLY_IDENTITY
	ld [hl], a
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_DAMAGE
	ret nz
	ld hl, FSR_BASE + FSR_CAN_ACT
	add hl, de
	ld a, [hl]
	and a
	jr z, .identity
	ld hl, FSR_BASE + FSR_VALID
	add hl, de
	ld a, [hli] ; mask
	ld b, a
	ld a, [hli] ; range
	and b
	ret nz
	ld a, [hl] ; support
	and b
	jr nz, .supported_identity
	ld hl, FSR_BASE + FSR_POWER
	add hl, de
	ld a, [hl]
	and a
	ret nz
	jr .identity
.supported_identity
	cp b
	ret nz ; mixed support across compiled regimes
	ld hl, FSR_BASE + FSR_RAW_MAX
	add hl, de
	ld c, 8
.identity_raw
	ld a, [hli]
	and a
	ret nz
	dec c
	jr nz, .identity_raw
.identity
	ad_address FS_REPLY_IDENTITY
	ld [hl], 1
	ret

.AccumulateIncoming
; B+=weight*mu_reply (signed32). The unary candidate collects the reply's
; standalone flags over its positive original events.
	ad_address FS_REPLY_IDENTITY
	ld a, [hl]
	and a
	jr nz, .incoming_flags ; zero moment
	ld hl, FSR_BASE + FSR_MOMENT
	add hl, de
	ld a, [hli]
	ld b, a
	add a
	sbc a
	ld [FSC_TEMP], a
	ld a, b
	ld [FSC_TEMP + 1], a
	ld a, [hli]
	ld [FSC_TEMP + 2], a
	ld a, [hl]
	ld [FSC_TEMP + 3], a
	ad_address FS_REPLY_W
	ld a, [hl]
	cp JC_REVEALED_WEIGHT
	jr nz, .add_incoming
	ld b, 3
.shift_incoming
	ld hl, FSC_TEMP + 3
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec b
	jr nz, .shift_incoming
.add_incoming
	ld hl, FSC_TEMP + 3
	ld bc, FSC_INCOMING + 3
	push de
	ld d, 4
	and a
.add_incoming_byte
	ld a, [bc]
	adc [hl]
	ld [bc], a
	dec hl
	dec bc
	dec d
	jr nz, .add_incoming_byte
	pop de
.incoming_flags
	ad_address FS_UNARY_INDEX
	ld a, [hl]
	cp $ff
	ret z
	push af
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	ld b, 0
	and a
	jr z, .miss_flags
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld b, [hl]
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
.miss_flags
	cp 255
	jr z, .reply_flags_ready
	ld hl, FSR_BASE + FSR_STANDALONE_MISS_FLAGS
	add hl, de
	ld a, [hl]
	or b
	ld b, a
.reply_flags_ready
	pop af
	ld a, b
	ad_address FS_UNARY_FLAGS
	or [hl]
	ld [hl], a ; committed to the unary record once per defender
	ret

.UnaryFallback
; Unrepresented reply: the wait/switch candidate takes the direct evaluator's
; complete value minus its already assigned baseline. Carry=accepted.
	ad_address FS_UNARY_INDEX
	ld a, [hl]
	cp $ff
	scf
	ret z
	ad_address FS_UNARY_KIND
	ld b, [hl]
	ad_address FS_DEFENDER
	ld c, [hl]
	farcall BossAI_FastUnaryFallback
	ret nc
	ad_address FS_BACKEND
	ld [hl], 1
	ad_address FS_UNARY_INDEX
	ld a, [hl]
	jp .AddPairTotal

.Plans
; Each live plan consumes one correction for the current reply. Carry=complete.
; A bench defender has no plans: skip the slot walk.
	ad_address FS_PLAN_INDEX
	ld a, [hli]
	and [hl]
	inc hl
	and [hl]
	inc hl
	and [hl]
	inc a
	scf
	ret z
	ad_address FS_SCAN
	bit 0, [hl]
	ld a, 0
	jr z, .first_plan
	ld a, 3
.first_plan
	ad_address FS_PLAN
	ld [hl], a
	ld b, 4
.plan
	push bc
	ad_address FS_PLAN
	ld c, [hl]
	ld b, 0
	ad_address FS_PLAN_INDEX
	add hl, bc
	ld a, [hl]
	cp $ff
	jr z, .plan_skip
	call .PlanPair
	jr c, .plan_skip
	pop bc
	ret
.plan_skip
	pop bc
	ad_address FS_SCAN
	bit 0, [hl]
	ad_address FS_PLAN
	jr nz, .previous_plan
	inc [hl]
	jr .plan_next
.previous_plan
	dec [hl]
.plan_next
	dec b
	jr nz, .plan
	scf
	ret

.PlanPair
; C=plan slot, A=original index. Native correction when both sides are
; represented, otherwise the direct pair fallback. Carry=accepted.
	push af
	call .OrderDescriptor
	push af
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .pair_fallback
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	and a
	jr z, .pair_fallback
	ad_address FS_REPLY_IDENTITY
	ld a, [hl]
	and a
	jr nz, .pair_identity
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_BOOST
	jr z, .pair_boost
	cp FSR_SELFDESTRUCT
	jr z, .pair_full
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_SELFDESTRUCT
	jr nz, .pair_native
.pair_full
; a miss that is not identity: every event pair through the executors
	pop af
	ad_address FS_ORDER
	ld [hl], a
	farcall BossAI_FastFallbackPairNativeFar
	jr .pair_total
.pair_identity
	pop af
	call .IdentityPair
	pop af
	call .OrRecordFlags
	scf
	ret
.pair_boost
	pop af
	call .BoostPair
	jr .pair_total
.pair_native
	pop af
	push af
	push bc
	call BossAI_FastScalarPair
	pop bc
	jr c, .pair_scalar
	pop af
	call BossAI_FastNormalizedPair.CorrectionOnly
	jr .pair_total
.pair_scalar
	pop af
	scf
	jr .pair_total
.pair_fallback
	pop af
	cp 2
	jr z, .fallback_order
	xor a
.fallback_order
	ad_address FS_ORDER
	ld [hl], a
	farcall BossAI_FastFallbackPairCorrectionFar
	jr nc, .pair_total
	ad_address FS_BACKEND
	ld [hl], 1
	scf
.pair_total
	pop bc
	ret nc
	ld a, b
	jp .AddPairTotal

.IdentityPair
; C=plan slot, A=order. The reply never changes HP, so the correction is zero
; and only the reached flags matter: the plan's standalone flags for each
; positive original event, plus the reply's standalone flags whenever some
; order reaches it (reply first always; own first only when the plan's
; successor for that event leaves both actors alive). B=flag union.
	push af
	ad_address FS_ORDER
	pop af
	ld [hl], a
	ld b, 0
	cp 2
	jr nz, .identity_orders
	ld b, 1 << AV_UNKNOWN_ORDER_F
.identity_orders
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	push af
	and a
	jr z, .identity_own_miss ; no hit mass
	ld a, FSP_STANDALONE_HIT_FLAGS
	call .PlanAddress
	ld a, [hl]
	or b
	ld b, a
	ld a, FSP_HIT_HP
	call .PlanAddress
	call .IdentityReplyFlags
.identity_own_miss
	pop af
	cp 255
	ret z ; no miss mass
	ld a, FSP_STANDALONE_MISS_FLAGS
	call .PlanAddress
	ld a, [hl]
	or b
	ld b, a
	ld a, FSP_MISS_HP
	call .PlanAddress
	jp .IdentityReplyFlags
.BoostPair
; C=plan slot, A=order. The reply is a deterministic defense boost: mass 256,
; no HP change, check flags only. Own first leaves the own standalone
; transition (correction zero). Reply first raises the player's defense for
; the own hit: the own plan runs with its variant amount and the correction is
; V(that terminal)-V(start) minus the own hit delta. Flags: the own standalone
; flags per positive own event with the reply's flags when reached (as the
; identity pair), and on the reply-first hit path the own flags at the
; variant instead of the standalone hit flags. Outputs FPK_TOTAL/FPK_FLAGS as
; the factored pair does; carry set.
	push af
	ld [FPK_ORDER], a
	ld a, c
	ld [FPK_INDEX], a
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	ld a, 1
	ld [FPK_MODE], a
	ld [FPK_REPLY_Z], a ; 256
	xor a
	ld [FPK_REPLY_Z + 1], a
	ld [FPK_K], a
	ld [FPK_K + 1], a
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode
	ld a, b
	ld [FPK_OWN_Z], a
	ld a, c
	ld [FPK_OWN_Z + 1], a
	pop af
	push af
	ld a, [FPK_INDEX]
	ld c, a
	pop af
	call .IdentityPair ; B=flag union for own first, the miss paths and the tie flag
	ld a, b
	ld [FPK_FLAGS], a
	ld a, [FPK_ORDER]
	and a
	jp z, .boost_total ; own first: the boost lands after the hit
	ld hl, FSR_BASE + FSR_CAN_ACT
	add hl, de
	ld a, [hl]
	and a
	jp z, .boost_total ; no boost happens
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .boost_total ; no own hit mass
	call .BoostVariant
	jp nc, .boost_total ; the boost does not touch this plan's defense axis
; the own hit at the variant, from the start state
	call BossAI_FastNormalizedPair.InitialContinuation
	ld a, [FPK_INDEX]
	ld c, a
	xor a
	ld hl, $a448
	call BossAI_FastExecuteOwnedPlan
	xor a
	ld [FSV_OVERRIDE], a
	ld a, [FPK_INDEX]
	ld c, a ; the executor and Delta clobber BC
	ld a, [FPK_ORDER]
	cp 2
	jr z, .boost_variant_flags
; reply first only: the standalone hit flags the identity pair added do not
; apply on this path; rebuild the union from the miss path and the variant
	ld a, FSP_STANDALONE_MISS_FLAGS
	call .PlanAddress
	ld b, [hl]
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	cp 255
	jr nz, .boost_miss_flags
	ld b, 0 ; no miss mass
.boost_miss_flags
	ld hl, FSR_BASE + FSR_CHECK_FLAGS
	add hl, de
	ld a, [hl]
	or b
	ld [FPK_FLAGS], a
.boost_variant_flags
	ld a, [$a458]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	push de
	call BossAI_FastBuildOwnedStandalone.Delta
	pop de
	push bc
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_HIT_DELTA
	call .PlanAddress
	inc hl
	pop bc
	ld a, c
	sub [hl]
	ld c, a
	dec hl
	ld a, b
	sbc [hl]
	ld b, a
	ld a, [FPK_ORDER]
	cp 2
	jr z, .boost_k
	sla c
	rl b ; a single order counts twice, like the factored pair
.boost_k
	ld a, b
	ld [FPK_K], a
	ld a, c
	ld [FPK_K + 1], a
.boost_total
	push de
	call BossAI_FastNormalizedPair.Total
	pop de
	scf
	ret
.BoostVariant
; The variant slot for this plan and the current boost reply into
; FSV_OVERRIDE (active). Carry when the boost touches the plan's defense axis
; and the slot is valid.
	ld a, [FPK_INDEX]
	add a
	ld l, a
	add a
	add l
	ld l, a
	ld h, 0
	ld bc, FSV_BASE
	add hl, bc
	push hl
	ld hl, FSR_BASE + FSR_BOOST_STEPS
	add hl, de
	ld a, [hli]
	ld c, [hl] ; C=axis
	pop hl
	dec a
	jr z, .boost_slot_ready ; one stage: slot 0 (Defense only)
	inc hl
	inc hl
	inc hl ; slot 1
.boost_slot_ready
	ld a, [hli]
	ld [FSV_OVERRIDE + 1], a
	ld a, [hli]
	ld [FSV_OVERRIDE + 2], a
	ld a, [hl]
	ld [FSV_OVERRIDE + 3], a
	bit 7, a
	ret z ; invalid slot: carry clear
	bit 2, a
	ld b, 1
	jr z, .boost_slot_axis
	ld b, 4
.boost_slot_axis
	ld a, b
	cp c
	jr z, .boost_axis_matches
	and a ; axis mismatch: the boost does not change this plan's amount
	ret
.boost_axis_matches
	ld a, 1
	ld [FSV_OVERRIDE], a
	scf
	ret
.IdentityReplyFlags
; HL=plan successor state for one positive own event. Adds the reply's
; standalone flags to B when an order reaches the reply from that state.
	push hl
	ad_address FS_ORDER
	ld a, [hl]
	pop hl
	and a
	jr nz, .identity_reply_reached ; reply first or tie: the reply always acts
	ld a, [hli]
	or [hl]
	ret z ; own KO'd itself before the reply
	inc hl
	ld a, [hli]
	or [hl]
	ret z ; own KO'd the player: no reply
.identity_reply_reached
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .identity_reply_miss
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld a, [hl]
	or b
	ld b, a
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
.identity_reply_miss
	cp 255
	ret z
	ld hl, FSR_BASE + FSR_STANDALONE_MISS_FLAGS
	add hl, de
	ld a, [hl]
	or b
	ld b, a
	ret

.OrderDescriptor
; C=plan slot. A=0 own first, 1 reply first, 2 genuine modeled tie. Priority
; first; unknown speed or Quick Claw at equal speed keeps the reference's
; conservative reply-first order (their flags are candidate/setup flags).
	push bc
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_ABSENT
	ld a, 0
	jr z, .order_done
	ld a, FSP_PRIORITY
	call .PlanAddress
	ld b, [hl]
	ld hl, FSR_BASE + FSR_PRIORITY
	add hl, de
	ld a, [hl]
	cp b
	ld a, 0
	jr c, .order_done
	ld a, 1
	jr nz, .order_done
	ad_address FS_TIE_ORDER
	ld a, [hl]
.order_done
	pop bc
	ret
.TieOrder
; FS_TIE_ORDER: the order of an equal-priority pair from the imported speeds.
; Unknown public order or Quick Claw at equal speed keeps the reference's
; conservative reply-first order; only a genuine same-speed pair without
; Quick Claw is the two-order tie.
	ld a, [FSA_SPEED_MODE]
	and a
	ld a, 1
	jr nz, .tie_ready
	ld a, [FSA_OWN_SPEED + 1]
	ld c, a
	ld a, [FSA_PLAYER_SPEED + 1]
	sub c
	ld c, a
	ld a, [FSA_OWN_SPEED]
	ld b, a
	ld a, [FSA_PLAYER_SPEED]
	sbc b
	jr c, .tie_own_first
	or c
	ld a, 1
	jr nz, .tie_ready
	ld a, [FSA_ITEM_CLASS]
	and a
	ld a, 1
	jr nz, .tie_ready
	ld a, 2
	jr .tie_ready
.tie_own_first
	xor a
.tie_ready
	ad_address FS_TIE_ORDER
	ld [hl], a
	ret

.AddPairTotal
; A=record index. T+=weight*FPK_TOTAL; uncertainty|=FPK_FLAGS. Carry set.
	push af
	ld hl, FPK_TOTAL
	ld bc, FSC_TEMP
	call .CopyFive
	ad_address FS_REPLY_W
	ld a, [hl]
	cp JC_REVEALED_WEIGHT
	jr nz, .weighted
	ld hl, FSC_TEMP
	ld b, 3
	call .ShiftLeft
.weighted
	pop af
	push af
	ld hl, FSC_TEMP
	call .AddToRecord
	pop af
	ld hl, FPK_FLAGS
	ld b, [hl]
	call .OrRecordFlags
	scf
	ret

.CommitIncoming
; T+=512*B for every live plan and the unary candidate of this defender.
	ld a, [FSC_INCOMING]
	ld [FSC_TEMP + 1], a
	add a
	sbc a
	ld [FSC_TEMP], a
	ld a, [FSC_INCOMING + 1]
	ld [FSC_TEMP + 2], a
	ld a, [FSC_INCOMING + 2]
	ld [FSC_TEMP + 3], a
	ld a, [FSC_INCOMING + 3]
	ld [FSC_TEMP + 4], a
	ld hl, FSC_TEMP
	ld b, 9
	call .ShiftLeft
	ld c, 0
.commit_plan
	call .PlanIndex
	cp $ff
	jr z, .commit_next
	push bc
	ld hl, FSC_TEMP
	call .AddToRecord
	pop bc
.commit_next
	inc c
	ld a, c
	cp 4
	jr c, .commit_plan
	ad_address FS_UNARY_INDEX
	ld a, [hl]
	cp $ff
	ret z
	push af
	ld hl, FSC_TEMP
	call .AddToRecord
	pop af
	ad_address FS_UNARY_FLAGS
	ld b, [hl]
	jp .OrRecordFlags

; ---------------------------------------------------------------------------
; Record and wide-arithmetic helpers. Records are big-endian five-byte T,
; two-byte M, two-byte score (finalizer), one uncertainty byte.

.RecordPointer
; A=index. HL=record address; BC scratch.
	ld c, a
	add a
	add a
	add c
	add a
	ld c, a
	ld b, 0
	ld hl, FS_RESULTS
	add hl, bc
	ret
.CopyToRecord
; A=index, HL=five-byte source. Record T=source.
	push hl
	call .RecordPointer
	pop bc
	push de
	ld d, 5
.copy_record_byte
	ld a, [bc]
	ld [hli], a
	inc bc
	dec d
	jr nz, .copy_record_byte
	pop de
	ret
.AddToRecord
; A=index, HL=five-byte big-endian addend. Record T+=addend modulo 2^40.
	push hl
	call .RecordPointer
	pop bc
	rept 4
	inc hl
	inc bc
	endr
	push de
	ld d, 5
	and a
.add_record_byte
	ld a, [bc]
	adc [hl]
	ld [hl], a
	dec hl
	dec bc
	dec d
	jr nz, .add_record_byte
	pop de
	ret
.OrRecordFlags
; A=index, B=flags.
	push bc
	call .RecordPointer
	ld bc, 9
	add hl, bc
	pop bc
	ld a, [hl]
	or b
	ld [hl], a
	ret
.SetRecordMeta
; A=index, B=initial flags. Stores M, the flags and the legal bit.
	push bc
	push af
	call .RecordPointer
	ld bc, 5
	add hl, bc
	ld a, [FSC_MASS]
	ld [hli], a
	ld a, [FSC_MASS + 1]
	ld [hli], a
	inc hl
	inc hl
	pop af
	pop bc
	ld [hl], b
.SetLegal
; A=index. Sets its bit in the big-endian legal mask.
	ad_address FS_LEGAL_MASK + 1
	cp 8
	jr c, .legal_low
	dec hl
	sub 8
.legal_low
	ld b, a
	ld a, 1
	inc b
.legal_shift
	dec b
	jr z, .legal_set
	add a
	jr .legal_shift
.legal_set
	or [hl]
	ld [hl], a
	ret
.CopyFive
; HL=source, BC=destination. DE preserved.
	push de
	ld d, b
	ld e, c
	ld b, 5
.copy_five_byte
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_five_byte
	pop de
	ret
.ShiftLeft
; HL=five-byte big-endian value, B=bit count (0 allowed).
	inc b
	dec b
	ret z
.shift_left_bit
	push hl
	rept 4
	inc hl
	endr
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	pop hl
	dec b
	jr nz, .shift_left_bit
	ret
.MassShiftedTo
; HL=five-byte destination, B=shift. Destination=M<<B.
	push hl
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld a, [FSC_MASS]
	ld [hli], a
	ld a, [FSC_MASS + 1]
	ld [hl], a
	pop hl
	jp .ShiftLeft
.MassMultiplier8
; FS_MULTIPLIER=M<<8.
	ld a, [FSC_MASS]
	ld [FS_MULTIPLIER], a
	ld a, [FSC_MASS + 1]
	ld [FS_MULTIPLIER + 1], a
	xor a
	ld [FS_MULTIPLIER + 2], a
	ret
.SignExtend24
; HL=signed 24-bit big-endian value. FS_MULTIPLICAND=its five-byte extension.
	ld a, [hli]
	ld [FS_MULTIPLICAND + 2], a
	add a
	sbc a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld a, [hli]
	ld [FS_MULTIPLICAND + 3], a
	ld a, [hl]
	ld [FS_MULTIPLICAND + 4], a
	ret
