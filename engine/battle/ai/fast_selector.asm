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
; Fast pair facts (WRAMX bank 1, reference build only). Per plan: what a
; plain damage pair reads per reply; per reply: the same for the current one.
DEF FPP_SIZE EQU 16
DEF FPP_STATE EQU 0 ; bit0 plain damage or recovery plan, bit1 the own hit leaves a fainted actor, bit2 recovery
DEF FPP_REGIME EQU 1 ; the reply's amount regime after the own hit
DEF FPP_FLAGS_HIT EQU 2 ; own hit flags at each of the four regimes
DEF FPP_FLAGS_MISS EQU 6
DEF FPP_Z EQU 7 ; own hit mass 0..256
DEF FPP_ACC EQU 9 ; five-byte sum of weight*z_reply*K over the sweep
DEF FPP_UNION EQU 14 ; reached flags over the sweep
DEF FPP_REST EQU 15 ; recovery plan: 1 when its Rest transition can apply (can act, quota, Rest)
DEF FRP_STATE EQU 0 ; bit0 plain damage reply, bit1 the reply hit leaves a fainted actor
DEF FRP_REGIME EQU 1 ; the own amount regime after the reply hit
DEF FRP_FLAGS_HIT EQU 2
DEF FRP_FLAGS_MISS EQU 6
DEF FRP_Z EQU 7
DEF FRP_SIZE EQU 9
PUSHS
SECTION "Boss AI Fast Sweep State", WRAMX, BANK[1]
wFastPlanPairs:: ds 4 * FPP_SIZE
wFastReplyPair:: ds FRP_SIZE
wFastStartOutRegime:: db ; the own attack regime at the start state
wFastStartGated:: db ; 1 when the start state has a fainted actor
SECTION "Boss AI Fast Reply Weights", WRAMX, BANK[1], ALIGN[8]
wFastReplyWeights:: ds 256 ; per move: 0 impossible, else its reply weight (set by .ReplyMass)
POPS

BossAI_ComparePublicActionsFastPrototype::
; DE=472-byte context, A=decision0/2, B=scan0..15, SRAM closed. Same full
; record ABI/finalizer as the compatibility adapter. Both decision kinds are
; evaluated natively; ordinary pairs may use the direct fallback (status 1).
	ld c, a
	push bc
	farcall BossAI_FastPreparePublicInputsFar
	pop bc
	jp nc, .reference
	xor a
	call OpenSRAM
	farcall BossAI_FastClearResults
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
	farcall BossAI_FastFinalizeResults
	ret

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
	farcall BossAI_FastBuildOwnHPTableFar
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
	farcall BossAI_FastFinalizeResults
	ret

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
	jr c, .mass_store
	xor a
.mass_store
	pop bc
	pop hl ; H=move
	push hl
	ld l, h
	ld h, HIGH(wFastReplyWeights)
	ld [hl], a ; the sweeps read the weight here
	and a
	jr z, .mass_next
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
; C=plan slot 0..3, A=field offset. HL=field address; BC/DE preserved.
	ld l, a
	ld a, c
	rrca
	rrca ; 64*slot
	add l ; below 256
	add LOW(FSP_BASE)
	ld l, a
	ld a, HIGH(FSP_BASE)
	adc 0
	ld h, a
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
	farcall BossAI_FastImportActorHP
	ret nc
	farcall BossAI_FastPrepareReplyFacts
	call .OwnVariants
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
	call .PreparePlanPairs
	call .ReplySweep
	ret nc
	call .CommitIncoming
	call .CommitPairs
	scf
	ret

.ReplyRegimes
; FS_REPLY_REGIMES=bit per incoming HP regime reachable on this defender: the
; start state plus every live plan's original-event successors. Regime bit0 is
; the player's attacker-low predicate 3*HP<max, bit1 the own defender-high
; predicate 2*HP>max, both in the executor's wrapped 16-bit arithmetic. Also
; the start state's outgoing regime and gate for the fast standalone/pairs.
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	ld hl, FSA_PLAYER
	call .OutgoingRegimeIndex
	ld [wFastStartOutRegime], a
	ld hl, FSA_START_HP
	call .StateGated
	ld [wFastStartGated], a
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	ld hl, FSA_PLAYER
	call .ReplyRegimeBit
	ld b, a
	ld c, $ff
.start_regime_index
	inc c
	rra
	jr nc, .start_regime_index
	ld a, c
	ld [FSA_START_REGIME], a
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
	farcall BossAI_FastImportActorHP
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
	farcall BossAI_FastPrepareReplyFacts
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
	ld l, [hl]
	ld h, HIGH(wFastReplyWeights)
	ld a, [hl]
	and a
	jr z, .reply_next ; impossible
	ad_address FS_REPLY_W
	ld [hl], a
	call .PrepareReply
	jr nc, .reply_fallback
	ld a, [FSA_OWN_VARIANT_MASK]
	and a
	call nz, BossAI_FastCompileReplyVariants ; the active defender's own boosts only
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
	xor a
	ld [wFastReplyPair + FRP_STATE], a ; only .PlainStandalone marks a reply for the fast pairs
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
	cp FSR_DAMAGE
	jr nz, .general_standalone
	call .PlainStandalone
	ret c
.general_standalone
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
	jp z, .pair_fallback
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
	ld b, a
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_BOOST
	jr z, .pair_own_boost
	ld a, b
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
.pair_own_boost
; B=reply opcode. The boss's own boost is native unless the reply's amounts
; depend on HP advanced within the action (multihit, False Swipe) or it is a
; Selfdestruct: those keep the exact direct fallback.
	ld a, b
	cp FSR_MULTI
	jr z, .pair_fallback
	cp FSR_FALSE_SWIPE
	jr z, .pair_fallback
	cp FSR_SELFDESTRUCT
	jr z, .pair_fallback
	pop af
	call .OwnBoostPair
	jr .pair_total
.pair_native
	pop af
	push af
	push bc
	call .FastPair
	pop bc
	jr c, .pair_fast
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
.pair_fast
; accumulated on the plan; nothing to add to the record now
	pop af
	pop bc
	scf
	ret
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
.OwnBoostPair
; C=plan slot, A=order. The own plan is a deterministic defense boost: mass
; 256, no HP change, check flags only. Reply first leaves the reply's
; standalone transition (correction zero). Own first raises the own defense
; for the reply's hit: when the plan can act and the reply carries a variant
; for this boost (FSR_VARIANT_FLAGS), the reply runs from the start state with
; the variant amount and the correction is V(that terminal)-V(start) minus
; the reply's hit delta. Flags: the reply's standalone flags per positive
; reply event, the own check flags whenever an order reaches the boss (own
; first always, reply first when the reply's successor leaves both alive),
; and on the own-first hit path with a live variant the reply's flags at the
; variant instead of its standalone hit flags. Outputs FPK_TOTAL/FPK_FLAGS as
; the factored pair does; carry set.
	ld [FPK_ORDER], a
	ld a, c
	ld [FPK_INDEX], a
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	ld a, 1
	ld [FPK_MODE], a
	ld [FPK_OWN_Z], a ; 256
	xor a
	ld [FPK_OWN_Z + 1], a
	ld [FPK_K], a
	ld [FPK_K + 1], a
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	ld a, [FPK_ORDER]
	ld b, 0
	cp 2
	jr nz, .own_boost_flags
	ld b, 1 << AV_UNKNOWN_ORDER_F
.own_boost_flags
	call .OwnBoostReached
	call .identity_reply_reached ; the reply's standalone flags per positive event
	ld a, b
	ld [FPK_FLAGS], a
	ld a, [FPK_ORDER]
	cp 1
	jp z, .own_boost_total ; reply first: the boost lands after the hit
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jp z, .own_boost_total ; no boost happens
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jp z, .own_boost_total ; no reply hit mass
	call .OwnBoostVariant
	jp nc, .own_boost_total ; the reply carries no amount for this boost
; the reply's hit at the variant, from the start state
	call BossAI_FastNormalizedPair.InitialContinuation
	ld hl, $a448
	xor a
	call BossAI_FastExecuteReplyPlan
	xor a
	ld [FSV_OVERRIDE], a
	ld a, [FPK_ORDER]
	cp 2
	jr z, .own_boost_variant_flags
; own first only: the reply's standalone hit flags do not apply on this path;
; rebuild the union from the own check flags, the miss path and the variant
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_CHECK_FLAGS
	call .PlanAddress
	ld b, [hl]
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	cp 255
	jr z, .own_boost_miss_flags ; no miss mass
	ld hl, FSR_BASE + FSR_STANDALONE_MISS_FLAGS
	add hl, de
	ld a, [hl]
	or b
	ld b, a
.own_boost_miss_flags
	ld a, b
	ld [FPK_FLAGS], a
.own_boost_variant_flags
	ld a, [$a458]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	push de
	call BossAI_FastBuildOwnedStandalone.Delta ; BC=V(terminal)-V(start)
	pop de
	ld hl, FSR_BASE + FSR_HIT_DELTA + 1
	add hl, de
	ld a, c
	sub [hl]
	ld c, a
	dec hl
	ld a, b
	sbc [hl]
	ld b, a
	ld a, [FPK_ORDER]
	cp 2
	jr z, .own_boost_k
	sla c
	rl b ; a single order counts twice, like the factored pair
.own_boost_k
	ld a, b
	ld [FPK_K], a
	ld a, c
	ld [FPK_K + 1], a
.own_boost_total
	push de
	call BossAI_FastNormalizedPair.Total
	pop de
	scf
	ret
.OwnBoostReached
; B=flag union. Adds the own plan's check flags when an order reaches the
; boss: own first always (both alive at the start state), reply first when
; some positive reply event leaves both alive.
	ld a, [FPK_ORDER]
	cp 1
	jr nz, .own_boost_reached
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .own_boost_miss_successor
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	call .BothAlive
	jr c, .own_boost_reached
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
.own_boost_miss_successor
	cp 255
	ret z ; no miss mass
	ld hl, FSR_BASE + FSR_MISS_HP
	add hl, de
	call .BothAlive
	ret nc
.own_boost_reached
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_CHECK_FLAGS
	call .PlanAddress
	ld a, [hl]
	or b
	ld b, a
	ret
.BothAlive
; HL=successor state (own HP word, player HP word). Carry when both live.
	ld a, [hli]
	or [hl]
	ret z
	inc hl
	ld a, [hli]
	or [hl]
	ret z
	scf
	ret
.OwnBoostVariant
; FSV_OVERRIDE (active) from the reply's variant for this plan's boost. Carry
; when the reply carries a valid variant for it.
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_DEFENSE_AXIS
	call .PlanAddress
	ld a, [hli]
	ld b, [hl] ; B=stages
	ld c, FSR_VARIANT_A
	cp 4
	ld a, 4 ; Special Defense+2: bits 4/5
	jr z, .own_variant_bits
	xor a ; Defense+1: bits 0/1
	dec b
	jr z, .own_variant_bits
	ld a, 2 ; Defense+2: bits 2/3
	ld c, FSR_VARIANT_B
.own_variant_bits
	ld hl, FSR_BASE + FSR_VARIANT_FLAGS
	add hl, de
	ld b, [hl]
	and a
	jr z, .own_variant_shifted
.own_variant_shift
	srl b
	dec a
	jr nz, .own_variant_shift
.own_variant_shifted
	ld a, b
	and 1
	ret z ; no variant: carry clear
	ld a, b
	rra ; the range bit into bit0
	and 1
	or 2 ; supported: the compile stored an amount
	ld [FSV_OVERRIDE + 3], a
	ld l, c
	ld h, 0
	ld bc, FSR_BASE
	add hl, bc
	add hl, de
	ld a, [hli]
	ld [FSV_OVERRIDE + 1], a
	ld a, [hl]
	ld [FSV_OVERRIDE + 2], a
	ld a, 1
	ld [FSV_OVERRIDE], a
	scf
	ret
.OwnVariants
; FSA_OWN_VARIANTS and FSA_OWN_VARIANT_MASK for the boss's own boost plans:
; one slot per distinct boost (0 Defense+1, 1 Defense+2, 2 Special Defense+2)
; holding the truncated (attack, defense) operands an incoming attack on that
; axis meets at the raised own defense (BossAI_FastProjectOwnDefense, then
; the kernel's joint quartering with the player's prepared attack). The live
; AD must be this defender's owned context.
	xor a
	ld [FSA_OWN_VARIANT_MASK], a
	ld c, 0
.own_variant_plan
	push bc
	call .PlanIndex
	cp $ff
	jr z, .own_variant_next
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_BOOST
	jr nz, .own_variant_next
	ld a, FSP_DEFENSE_AXIS
	call .PlanAddress
	ld a, [hli]
	ld c, a ; axis
	ld b, [hl] ; stages
	cp 4
	ld a, 2
	jr z, .own_variant_slot
	ld a, b
	dec a
.own_variant_slot
	ld [FSM_TEMP + 4], a ; slot (compile scratch, no compile in progress)
	add LOW(.SlotBits)
	ld l, a
	adc HIGH(.SlotBits)
	sub l
	ld h, a
	ld a, [hl] ; the slot's bit
	ld hl, FSA_OWN_VARIANT_MASK
	push af
	and [hl]
	jr z, .own_variant_new
	pop af
	jr .own_variant_next ; staged by an equivalent boost already
.own_variant_new
	pop af
	or [hl]
	ld [hl], a
	farcall BossAI_FastProjectOwnDefense ; BC=own defense after the boost
	ld a, b
	ld [FSM_TEMP + 2], a
	ld a, c
	ld [FSM_TEMP + 3], a
	ld a, [FSM_TEMP + 4]
	cp 2
	jr z, .own_variant_special
	ad_address AV_PREPARED_STATS ; the player's physical attack word
	jr .own_variant_attack
.own_variant_special
	ad_address AV_PREPARED_STATS + 4 ; the player's special attack word
.own_variant_attack
	ld a, [hli]
	ld [FSM_TEMP], a
	ld a, [hl]
	ld [FSM_TEMP + 1], a
	ld bc, FSM_TEMP
	farcall BossAI_FastTruncateStatsFar ; B=attack byte, C=defense byte
	ld a, [FSM_TEMP + 4]
	add a
	add LOW(FSA_OWN_VARIANTS)
	ld l, a
	ld h, HIGH(FSA_OWN_VARIANTS)
	ld [hl], b
	inc hl
	ld [hl], c
.own_variant_next
	pop bc
	inc c
	ld a, c
	cp 4
	jr c, .own_variant_plan
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

; ---------------------------------------------------------------------------
; Fast pairs: a plain damage own plan against a plain damage reply. K and the
; flags equal BossAI_FastScalarPair's, from per-plan facts prepared once per
; defender and per-reply facts prepared with the standalone record. The
; reply's delta after the own hit differs from its standalone delta only when
; the own hit changed the reply's amount regime (the player's HP fell under a
; third) or fainted an actor, and the own delta after the reply hit likewise;
; every other pair has K=0 and only flags. The products weight*z_reply*K
; accumulate per plan and z_own multiplies the sum once at .CommitPairs; the
; flags accumulate per plan the same way.

.PlanPairFacts
; HL=wFastPlanPairs entry of the plan FPK_INDEX. BC/DE preserved.
	ld a, [FPK_INDEX]
	swap a
	add LOW(wFastPlanPairs)
	ld l, a
	adc HIGH(wFastPlanPairs)
	sub l
	ld h, a
	ret

.StateGated
; HL=state (own HP word, player HP word). A=1 when an actor is fainted.
; BC/DE preserved.
	ld a, [hli]
	or [hl]
	jr z, .state_gated
	inc hl
	ld a, [hli]
	or [hl]
	jr z, .state_gated
	xor a
	ret
.state_gated
	ld a, 1
	ret

.IncomingRegimeIndex
; BC=own HP, HL=player HP word. A=the player's attack regime index from that
; state (bit0 3*player HP<player max, bit1 2*own HP>own max) in the
; executors' wrapped 16-bit arithmetic. DE preserved.
	push de
	push bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc ; 3*player HP
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
	ld e, a
	sla c
	rl b ; 2*own HP
	ld a, [FSA_MAX_HP]
	cp b
	jr c, .incoming_regime_high
	jr nz, .incoming_regime_done
	ld a, [FSA_MAX_HP + 1]
	cp c
	jr nc, .incoming_regime_done
.incoming_regime_high
	set 1, e
.incoming_regime_done
	ld a, e
	pop de
	ret

.OutgoingRegimeIndex
; BC=own HP, HL=player HP word. A=the own attack regime index from that state
; (bit0 3*own HP<own max, bit1 2*player HP>player max). DE preserved.
	push de
	push hl
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc ; 3*own HP
	ld a, [FSA_MAX_HP + 1]
	ld e, a
	ld a, [FSA_MAX_HP]
	ld d, a
	ld a, l
	sub e
	ld a, h
	sbc d
	ld a, 0
	adc 0
	ld e, a
	pop hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b ; 2*player HP
	ld a, [FSA_PLAYER + 2]
	cp b
	jr c, .outgoing_regime_high
	jr nz, .outgoing_regime_done
	ld a, [FSA_PLAYER + 3]
	cp c
	jr nc, .outgoing_regime_done
.outgoing_regime_high
	set 1, e
.outgoing_regime_done
	ld a, e
	pop de
	ret

.RegimeFlags
; B=hit flags at any regime, [FSK_STATE]=range mask, [FSK_STATE+1]=support
; mask. Writes the hit flags at each of the four regimes at HL (advanced past
; them): the range flag where the amount is a range, unknown damage where it
; is unsupported. BC/DE preserved.
	push bc
	ld c, 1 ; the regime's bit
.regime_flags_byte
	ld a, [FSK_STATE + 1]
	and c
	ld a, 0
	jr nz, .regime_flags_supported
	ld a, 1 << AV_UNKNOWN_DAMAGE_F
.regime_flags_supported
	or b
	ld [hl], a
	ld a, [FSK_STATE]
	and c
	jr z, .regime_flags_next
	ld a, [hl]
	or 1 << AV_AMOUNT_RANGE_F
	ld [hl], a
.regime_flags_next
	inc hl
	sla c
	bit 4, c
	jr z, .regime_flags_byte
	pop bc
	ret

.PreparePlanPairs
; Per-plan facts for this defender's plans (after their standalone records and
; .ReplyRegimes, which sets the start state's outgoing regime and gate).
	ld c, 0
.prepare_plan
	push bc
	ld a, c
	ld [FPK_INDEX], a
	call .PlanPairFacts
	push hl
	ld b, FPP_SIZE
	xor a
.prepare_clear
	ld [hli], a
	dec b
	jr nz, .prepare_clear
	pop hl
	call .PlanIndex
	cp $ff
	jp z, .prepare_next
	ld a, FSP_OPCODE
	call .PlanAddress
	ld a, [hl]
	cp FSP_RECOVERY
	jr z, .prepare_recovery
	cp FSP_DAMAGE
	jp nz, .prepare_next
	ld a, FSP_DESCRIPTOR
	call .PlanAddress
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, [hli]
	or [hl]
	jp nz, .prepare_next ; drain, recoil or an item: the sequential pair
	ld b, 1 ; plain damage
	jr .prepare_state
.prepare_recovery
	ld b, 5 ; recovery
.prepare_state
	ld a, FSP_HIT_HP
	call .PlanAddress
	call .StateGated
	add a
	or b ; and whether the own hit leaves a fainted actor
	push af
	call .PlanPairFacts
	pop af
	ld [hli], a
	push hl
	ld a, FSP_HIT_HP
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	inc hl
	call .IncomingRegimeIndex
	pop hl
	ld [hli], a ; FPP_REGIME
	ld a, [FPK_INDEX]
	ld c, a
	call .PlanPairFacts
	bit 2, [hl]
	jr nz, .prepare_recovery_flags
; the own flags at each regime, then on a miss
	ld a, FSP_CHECK_FLAGS
	call .PlanAddress
	ld b, [hl]
	ld a, FSP_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .prepare_own_constant ; cannot act: the check flags on every path
	ld a, FSP_DAMAGE_FLAGS
	call .PlanAddress
	ld a, [hl]
	or b
	ld b, a
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .prepare_own_constant ; no hit: no amount bits
	ld a, FSP_RANGE
	call .PlanAddress
	ld a, [hli]
	ld [FSK_STATE], a
	ld a, [hl]
	ld [FSK_STATE + 1], a
	call .PlanPairFacts
	inc hl
	inc hl
	call .RegimeFlags
	ld [hl], b ; FPP_FLAGS_MISS
	jr .prepare_own_mass
.prepare_own_constant
	call .PlanPairFacts
	inc hl
	inc hl
	ld a, b
	rept 5
	ld [hli], a
	endr
.prepare_own_mass
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode ; BC=z
	jr .prepare_own_z_store
.prepare_recovery_flags
; check flags on every path (FPP_FLAGS_MISS), the Rest transition where the
; own HP is below the maximum when it can act with a quota, mass 256
	ld a, FSP_CHECK_FLAGS
	call .PlanAddress
	ld b, [hl]
	call .PlanPairFacts
	push hl
	ld a, l
	add FPP_FLAGS_MISS
	ld l, a
	jr nc, .prepare_recovery_check
	inc h
.prepare_recovery_check
	ld [hl], b
	pop hl
	ld a, l
	add FPP_REST
	ld l, a
	jr nc, .prepare_recovery_rest
	inc h
.prepare_recovery_rest
	push hl
	ld a, FSP_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .prepare_recovery_no_rest
	ld a, FSP_RECOVERY_QUOTA
	call .PlanAddress
	ld a, [hli]
	or [hl]
	jr z, .prepare_recovery_no_rest
	ld a, FSP_MOVE
	call .PlanAddress
	ld a, [hl]
	cp REST
	jr nz, .prepare_recovery_no_rest
	pop hl
	ld [hl], 1
	jr .prepare_recovery_mass
.prepare_recovery_no_rest
	pop hl
	ld [hl], 0
.prepare_recovery_mass
	ld bc, 256
.prepare_own_z_store
	call .PlanPairFacts
	ld a, l
	add FPP_Z
	ld l, a
	jr nc, .prepare_own_z
	inc h
.prepare_own_z
	ld [hl], b
	inc hl
	ld [hl], c
.prepare_next
	pop bc
	inc c
	ld a, c
	cp 4
	jp c, .prepare_plan
	ret

.PlainStandalone
; The compiled reply is a damage opcode that is not identity. When its
; descriptor is plain (no drain/recoil, no Helmet): the standalone record as
; BossAI_FastScalarReplyStandalone writes it, plus wFastReplyPair for the
; fast pairs; carry set. Otherwise carry clear without writes.
	ld hl, FSR_BASE + FSR_DESCRIPTOR
	add hl, de
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, [hli]
	or [hl]
	ret nz
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
; both successors start as the start state, deltas and moment zero
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	ld b, 2
.plain_successor
	ld a, [FSA_START_HP]
	ld [hli], a
	ld a, [FSA_START_HP + 1]
	ld [hli], a
	ld a, [FSA_PLAYER]
	ld [hli], a
	ld a, [FSA_PLAYER + 1]
	ld [hli], a
	dec b
	jr nz, .plain_successor
	xor a
	rept 7
	ld [hli], a
	endr
; the hit: from a living start state, a reply that can act and can hit takes
; its amount at the start regime off the own HP
	ld a, [wFastStartGated]
	and a
	jp nz, .plain_facts
	ld hl, FSR_BASE + FSR_CAN_ACT
	add hl, de
	ld a, [hl]
	and a
	jp z, .plain_facts
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jp z, .plain_facts
	ld a, [FSA_START_REGIME]
	ld c, a
	ld b, 0
	ld hl, .RegimeBits
	add hl, bc
	ld a, [hl]
	ld hl, FSR_BASE + FSR_SUPPORT
	add hl, de
	and [hl]
	jr z, .plain_unsupported
	ld a, c
	add a
	add FSR_RAW_MAX
	ld l, a
	ld h, 0
	add hl, de
	ld bc, FSR_BASE
	add hl, bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	call BossAI_FastLoseHP
	jr .plain_hit_delta
.plain_unsupported
	ld hl, FSR_BASE + FSR_POWER
	add hl, de
	ld a, [hl]
	and a
	jr z, .plain_facts ; no amount: the start state
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	xor a
	ld [hli], a
	ld [hl], a ; the conservative KO
.plain_hit_delta
; hit delta = Phi(own HP after) - Phi(start); moment = p * hit delta
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	call BossAI_FastScalarPair.OwnPhi ; BC=Phi; D clobbered
	ld a, [FSA_START_PHI + 1]
	ld l, a
	ld a, c
	sub l
	ld l, a
	ld a, [FSA_START_PHI]
	ld h, a
	ld a, b
	sbc h
	ld h, a
	call BossAI_FastNormalizedPair.Context
	push hl
	ld hl, FSR_BASE + FSR_HIT_DELTA
	add hl, de
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	cp 255
	jr nz, .plain_moment
	xor a ; 256
.plain_moment
	ld h, b
	ld l, c
	call BossAI_FastMulSigned16By8 ; A:HL=signed 24-bit product
	push hl
	ld hl, FSR_BASE + FSR_MOMENT
	add hl, de
	ld [hli], a
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
.plain_facts
	ad_address FS_DEFENDER
	ld a, [hl]
	inc a
	jp nz, .plain_bench_flags ; a bench defender has no plans
; the reply facts: gate and the own regime after the hit, flags per regime
; and on a miss, mass
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	push hl
	call .StateGated
	add a
	or 1
	ld [wFastReplyPair + FRP_STATE], a
	pop hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	inc hl
	call .OutgoingRegimeIndex
	ld [wFastReplyPair + FRP_REGIME], a
	ld hl, FSR_BASE + FSR_CHECK_FLAGS
	add hl, de
	ld b, [hl]
	dec hl ; FSR_CAN_ACT
	ld a, [hl]
	and a
	jr z, .plain_flags_constant
	inc hl
	inc hl ; FSR_DAMAGE_FLAGS
	ld a, [hl]
	or b
	ld b, a
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .plain_flags_constant
	ld hl, FSR_BASE + FSR_RANGE
	add hl, de
	ld a, [hli]
	ld [FSK_STATE], a
	ld a, [hl]
	ld [FSK_STATE + 1], a
	ld hl, wFastReplyPair + FRP_FLAGS_HIT
	call .RegimeFlags
	ld [hl], b
	jr .plain_mass
.plain_flags_constant
	ld hl, wFastReplyPair + FRP_FLAGS_HIT
	ld a, b
	rept 5
	ld [hli], a
	endr
.plain_mass
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode
	ld a, b
	ld [wFastReplyPair + FRP_Z], a
	ld a, c
	ld [wFastReplyPair + FRP_Z + 1], a
; the standalone flags at the start state for both original events
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld a, [wFastStartGated]
	and a
	jr z, .plain_standalone_flags
	xor a
	ld [hli], a
	ld [hl], a
	scf
	ret
.plain_standalone_flags
	push hl
	ld a, [FSA_START_REGIME]
	add LOW(wFastReplyPair + FRP_FLAGS_HIT)
	ld l, a
	adc HIGH(wFastReplyPair + FRP_FLAGS_HIT)
	sub l
	ld h, a
	ld a, [hl]
	pop hl
	ld [hli], a
	ld a, [wFastReplyPair + FRP_FLAGS_MISS]
	ld [hl], a
	scf
	ret
.plain_bench_flags
; the standalone flags at the start state only: the check flags, then when the
; reply can act its damage flags and, on a hit with mass, the range/support
; bits of the start regime
	ld hl, FSR_BASE + FSR_STANDALONE_HIT_FLAGS
	add hl, de
	ld a, [wFastStartGated]
	and a
	jr z, .plain_bench_living
	xor a
	ld [hli], a
	ld [hl], a
	scf
	ret
.plain_bench_living
	push hl
	ld hl, FSR_BASE + FSR_CHECK_FLAGS
	add hl, de
	ld b, [hl]
	dec hl ; FSR_CAN_ACT
	ld a, [hl]
	and a
	jr z, .plain_bench_constant
	inc hl
	inc hl ; FSR_DAMAGE_FLAGS
	ld a, [hl]
	or b
	ld b, a
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .plain_bench_constant
	push bc
	ld a, [FSA_START_REGIME]
	ld c, a
	ld b, 0
	ld hl, .RegimeBits
	add hl, bc
	ld a, [hl]
	ld [FSK_STATE], a
	pop bc
	ld hl, FSR_BASE + FSR_SUPPORT
	add hl, de
	ld a, [FSK_STATE]
	and [hl]
	ld a, b
	jr nz, .plain_bench_supported
	or 1 << AV_UNKNOWN_DAMAGE_F
.plain_bench_supported
	ld c, a
	ld hl, FSR_BASE + FSR_RANGE
	add hl, de
	ld a, [FSK_STATE]
	and [hl]
	jr z, .plain_bench_ranged
	set AV_AMOUNT_RANGE_F, c
.plain_bench_ranged
	pop hl
	ld [hl], c
	inc hl
	ld [hl], b
	scf
	ret
.plain_bench_constant
	pop hl
	ld [hl], b
	inc hl
	ld [hl], b
	scf
	ret

.FastPair
; C=plan slot, A=order (0 own first, 1 reply first, 2 tie). Carry=handled
; (both sides plain damage; the plan's sum and union updated); clear=not
; eligible, nothing written. DE preserved.
	ld [FPK_ORDER], a
	ld a, c
	ld [FPK_INDEX], a
	call .PlanPairFacts
	ld a, [hl]
	and 1
	ret z
	ld a, [wFastReplyPair + FRP_STATE]
	and 1
	ret z
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	push de
	xor a
	ld [FPK_K], a
	ld [FPK_K + 1], a
; no correction without both hit masses
	ld a, [wFastReplyPair + FRP_Z]
	ld hl, wFastReplyPair + FRP_Z + 1
	or [hl]
	jr z, .fast_pair_flags
	call .PlanPairFacts
	ld bc, FPP_Z
	add hl, bc
	ld a, [hli]
	or [hl]
	jr z, .fast_pair_flags
	ld a, [FPK_ORDER]
	cp 1
	jr z, .fast_pair_reply_first
	call .FastK1
	ld a, [FPK_ORDER]
	cp 2
	jr z, .fast_pair_k1
	add hl, hl
.fast_pair_k1
	call BossAI_FastScalarPair.AddK
	ld a, [FPK_ORDER]
	and a
	jr z, .fast_pair_flags
.fast_pair_reply_first
	call .FastK2
	ld a, [FPK_ORDER]
	cp 2
	jr z, .fast_pair_k2
	add hl, hl
.fast_pair_k2
	call BossAI_FastScalarPair.AddK
.fast_pair_flags
	call .FastFlags
	push af
	call .PlanPairFacts ; clobbers A
	ld bc, FPP_UNION
	add hl, bc
	pop af
	or [hl]
	ld [hl], a
	ld hl, FPK_K
	ld a, [hli]
	or [hl]
	call nz, .FastAccumulate
	pop de
	scf
	ret

.FastK1
; HL=K1: the reply's delta after the own hit minus its standalone delta.
	call .PlanPairFacts
	ld a, [hli]
	and 2
	jr nz, .k1_nothing ; an actor fainted: the reply never happens
	ld b, [hl] ; the reply's regime after the own hit
	ld hl, FSR_BASE + FSR_CAN_ACT
	add hl, de
	ld a, [hl]
	and a
	jr z, .k1_nothing
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld a, [hl]
	and a
	jr z, .k1_nothing
	call .PlanPairFacts
	bit 2, [hl]
	jr nz, .k1_regime_changed ; a healed own HP: the reply's delta differs
	ld a, [FSA_START_REGIME]
	cp b
	jr nz, .k1_regime_changed
	ld hl, 0 ; the same amount as standalone: K1=0
	ret
.k1_regime_changed
	ld c, b
	ld b, 0
	ld hl, .RegimeBits
	add hl, bc
	ld a, [hl]
	ld hl, FSR_BASE + FSR_SUPPORT
	add hl, de
	and [hl]
	jr z, .k1_unsupported
	ld a, c
	add a
	add FSR_RAW_MAX
	ld l, a
	ld h, 0
	add hl, de
	ld bc, FSR_BASE
	add hl, bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	call .OwnHPAfterOwnHit ; HL=FSK_STATE with the own HP after the own hit
	call BossAI_FastLoseHP
	jr .k1_phi
.k1_unsupported
	ld hl, FSR_BASE + FSR_POWER
	add hl, de
	ld a, [hl]
	and a
	jr z, .k1_nothing ; no amount: the reply changes nothing
	xor a
	ld [FSK_STATE], a
	ld [FSK_STATE + 1], a ; the conservative KO
.k1_phi
	ld hl, FSK_STATE
	call BossAI_FastScalarPair.OwnPhi ; BC=Phi(own HP after both hits); D clobbered
	call .OwnPhiAfterOwnHit ; HL=Phi(own HP after the own hit)
	ld a, c
	sub l
	ld l, a
	ld a, b
	sbc h
	ld h, a
	call BossAI_FastNormalizedPair.Context
	jr .k1_minus_standalone
.k1_nothing
	ld hl, 0
.k1_minus_standalone
	push hl
	ld hl, FSR_BASE + FSR_HIT_DELTA
	add hl, de
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	jp BossAI_FastScalarPair.SubtractWord

.FastK2
; HL=K2: the own delta after the reply hit minus its standalone delta.
	ld a, [wFastReplyPair + FRP_STATE]
	and 2
	jr nz, .k2_nothing ; an actor fainted: the own plan never happens
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_CAN_ACT
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .k2_nothing
	call .PlanPairFacts
	bit 2, [hl]
	jp nz, .k2_recovery
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld a, [hl]
	and a
	jr z, .k2_nothing
	ld a, [wFastReplyPair + FRP_REGIME]
	ld b, a
	ld a, [wFastStartOutRegime]
	cp b
	jr nz, .k2_regime_changed
	ld hl, 0
	ret
.k2_regime_changed
	push bc
	ld c, b
	ld b, 0
	ld hl, .RegimeBits
	add hl, bc
	ld a, [hl]
	pop bc
	push af
	ld a, FSP_SUPPORT
	call .PlanAddress
	pop af
	and [hl]
	jr z, .k2_nothing ; an unsupported own amount changes nothing
	ld a, b
	add a
	add FSP_RAW_MIN
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_PLAYER]
	ld [FSK_STATE + 2], a
	ld a, [FSA_PLAYER + 1]
	ld [FSK_STATE + 3], a
	ld hl, FSK_STATE + 2
	call BossAI_FastLoseHP
	ld hl, FSK_STATE + 2
	call BossAI_FastScalarPair.PlayerPhi ; BC=Phi(player HP after both hits); D clobbered
	ld a, [FSA_PLAYER + 5]
	sub c
	ld l, a
	ld a, [FSA_PLAYER + 4]
	sbc b
	ld h, a ; the start player Phi minus the new
	call BossAI_FastNormalizedPair.Context
	jr .k2_minus_standalone
.k2_nothing
	ld hl, 0
.k2_minus_standalone
	push hl
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_HIT_DELTA
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	jp BossAI_FastScalarPair.SubtractWord
.k2_recovery
; the own heal from the own HP the reply hit left: the standalone transition
; when that HP is the start HP, else Phi(healed)-Phi(after the reply hit)
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_START_HP]
	cp b
	jr nz, .k2_heal
	ld a, [FSA_START_HP + 1]
	cp c
	jr nz, .k2_heal
	ld hl, 0
	ret
.k2_heal
	ld a, b
	ld [FSK_STATE], a
	ld a, c
	ld [FSK_STATE + 1], a
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_RECOVERY_QUOTA
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_MAX_HP]
	ld d, a
	ld a, [FSA_MAX_HP + 1]
	ld e, a
	ld hl, FSK_STATE
	call BossAI_FastGainHP
	ld hl, FSK_STATE
	call BossAI_FastScalarPair.OwnPhi ; BC=Phi(healed)
	call BossAI_FastNormalizedPair.Context
	push bc
	ld hl, FSR_BASE + FSR_HIT_DELTA
	add hl, de
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_START_PHI + 1]
	ld l, a
	ld a, [FSA_START_PHI]
	ld h, a
	add hl, bc ; Phi(own HP after the reply hit)
	pop bc
	ld a, c
	sub l
	ld l, a
	ld a, b
	sbc h
	ld h, a
	jr .k2_minus_standalone

.OwnHPAfterOwnHit
; FSK_STATE=the own HP after the own hit (the plan's hit successor); HL=FSK_STATE.
; BC/DE preserved.
	push bc
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_HIT_HP
	call .PlanAddress
	ld a, [hli]
	ld [FSK_STATE], a
	ld a, [hl]
	ld [FSK_STATE + 1], a
	pop bc
	ld hl, FSK_STATE
	ret

.OwnPhiAfterOwnHit
; HL=Phi(own HP after the own hit): the start Phi, plus the own hit delta for a
; recovery plan (whose player side is unchanged). BC/DE preserved.
	push bc
	call .PlanPairFacts
	bit 2, [hl]
	ld a, [FSA_START_PHI + 1]
	ld l, a
	ld a, [FSA_START_PHI]
	ld h, a
	jr z, .own_phi_ready
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_HIT_DELTA
	push hl
	call .PlanAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	add hl, bc
.own_phi_ready
	pop bc
	ret

.RecoveryOwnFlags
; HL=own HP word of a state. A=a recovery plan's flags there: its check flags,
; plus the Rest transition when FPP_REST and that HP is below the maximum.
	push hl
	call .PlanPairFacts
	push hl
	ld bc, FPP_REST
	add hl, bc
	ld a, [hl]
	pop hl
	ld bc, FPP_FLAGS_MISS
	add hl, bc
	ld b, [hl]
	pop hl
	and a
	ld a, b
	ret z
	push af
	ld a, [hli]
	ld l, [hl]
	ld h, a ; HL=the own HP
	ld a, [FSA_MAX_HP + 1]
	ld c, a
	ld a, [FSA_MAX_HP]
	ld b, a
	ld a, l
	sub c
	ld a, h
	sbc b ; carry when HP<max
	pop bc
	ld a, b
	ret nc
	or 1 << AV_UNKNOWN_TRANSITION_F
	ret

.FastFlags
; A=union of reached flags over every positive original-event path and every
; modeled order (BossAI_FastScalarPair.Flags with the prepared flags).
	xor a
	ld [FPK_FLAGS], a
	ld a, [FPK_ORDER]
	cp 2
	jr nz, .ff_orders
	ld a, 1 << AV_UNKNOWN_ORDER_F
	ld [FPK_FLAGS], a
.ff_orders
	xor a
	ld [FPK_FIRST_EVENT], a
.ff_own_event
	ld a, [FPK_INDEX]
	ld c, a
	ld a, FSP_ACCURACY
	call .PlanAddress
	ld b, [hl]
	ld a, [FPK_FIRST_EVENT]
	and a
	ld a, b
	jr nz, .ff_own_miss_mass
	and a
	jp z, .ff_next_own ; no hit mass
	jr .ff_own_mass
.ff_own_miss_mass
	cp 255
	jp z, .ff_next_own ; no miss mass
.ff_own_mass
	xor a
	ld [FPK_SECOND_EVENT], a
.ff_reply_event
	ld hl, FSR_BASE + FSR_ACCURACY
	add hl, de
	ld b, [hl]
	ld a, [FPK_SECOND_EVENT]
	and a
	ld a, b
	jr nz, .ff_reply_miss_mass
	and a
	jp z, .ff_next_reply
	jr .ff_reply_mass
.ff_reply_miss_mass
	cp 255
	jp z, .ff_next_reply
.ff_reply_mass
	ld a, [FPK_ORDER]
	cp 1
	jr z, .ff_reply_first
; own first: the own standalone flags, then the reply's at the own successor
	ld a, [FPK_INDEX]
	ld c, a
	ld a, [FPK_FIRST_EVENT]
	add FSP_STANDALONE_HIT_FLAGS
	call .PlanAddress
	ld a, [hl]
	ld [FSK_UNION], a
	ld a, [FPK_FIRST_EVENT]
	and a
	jr nz, .ff_own_first_start
	call .PlanPairFacts
	ld a, [hli]
	and 2
	jr nz, .ff_own_first_done ; fainted after the own hit
	ld a, [hl] ; the reply's regime there
	jr .ff_own_first_reply
.ff_own_first_start
	ld a, [wFastStartGated]
	and a
	jr nz, .ff_own_first_done
	ld a, [FSA_START_REGIME]
.ff_own_first_reply
	ld c, a
	ld a, [FPK_SECOND_EVENT]
	and a
	jr z, .ff_own_first_reply_hit
	ld a, [wFastReplyPair + FRP_FLAGS_MISS]
	jr .ff_own_first_union
.ff_own_first_reply_hit
	ld b, 0
	ld hl, wFastReplyPair + FRP_FLAGS_HIT
	add hl, bc
	ld a, [hl]
.ff_own_first_union
	ld hl, FSK_UNION
	or [hl]
	ld [hl], a
.ff_own_first_done
	ld a, [FSK_UNION]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	ld a, [FPK_ORDER]
	and a
	jr z, .ff_next_reply
.ff_reply_first
; the reply's standalone flags, then the own at the reply successor
	ld a, [FPK_SECOND_EVENT]
	add FSR_STANDALONE_HIT_FLAGS
	ld l, a
	ld h, 0
	add hl, de
	ld bc, FSR_BASE
	add hl, bc
	ld a, [hl]
	ld [FSK_UNION], a
	ld a, [FPK_SECOND_EVENT]
	and a
	jr nz, .ff_reply_first_start
	ld a, [wFastReplyPair + FRP_STATE]
	and 2
	jr nz, .ff_reply_first_done ; fainted after the reply hit
	call .PlanPairFacts
	bit 2, [hl]
	jr z, .ff_reply_first_hit_regime
	ld hl, FSR_BASE + FSR_HIT_HP
	add hl, de
	call .RecoveryOwnFlags
	jr .ff_reply_first_union
.ff_reply_first_hit_regime
	ld a, [wFastReplyPair + FRP_REGIME]
	jr .ff_reply_first_own
.ff_reply_first_start
	ld a, [wFastStartGated]
	and a
	jr nz, .ff_reply_first_done
	call .PlanPairFacts
	bit 2, [hl]
	jr z, .ff_reply_first_start_regime
	ld hl, FSA_START_HP
	call .RecoveryOwnFlags
	jr .ff_reply_first_union
.ff_reply_first_start_regime
	ld a, [wFastStartOutRegime]
.ff_reply_first_own
	ld c, a
	ld a, [FPK_FIRST_EVENT]
	and a
	jr z, .ff_reply_first_own_hit
	call .PlanPairFacts
	ld bc, FPP_FLAGS_MISS
	add hl, bc
	ld a, [hl]
	jr .ff_reply_first_union
.ff_reply_first_own_hit
	call .PlanPairFacts
	ld a, c
	add FPP_FLAGS_HIT
	ld c, a
	ld b, 0
	add hl, bc
	ld a, [hl]
.ff_reply_first_union
	ld hl, FSK_UNION
	or [hl]
	ld [hl], a
.ff_reply_first_done
	ld a, [FSK_UNION]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
.ff_next_reply
	ld hl, FPK_SECOND_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .ff_reply_event
.ff_next_own
	ld hl, FPK_FIRST_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .ff_own_event
	ld a, [FPK_FLAGS]
	ret

.FastAccumulate
; The plan's sum += weight*z_reply*K (signed 40-bit).
	ld a, [FPK_K]
	ld h, a
	ld a, [FPK_K + 1]
	ld l, a
	ld a, [wFastReplyPair + FRP_Z + 1] ; 0 means 256
	call BossAI_FastMulSigned16By8 ; A:HL=signed 24-bit product
	ld [FSC_TEMP + 2], a
	add a
	sbc a
	ld [FSC_TEMP], a
	ld [FSC_TEMP + 1], a
	ld a, h
	ld [FSC_TEMP + 3], a
	ld a, l
	ld [FSC_TEMP + 4], a
	ad_address FS_REPLY_W
	ld a, [hl]
	cp JC_REVEALED_WEIGHT
	jr nz, .fast_accumulate_add
	ld hl, FSC_TEMP
	ld b, 3
	call .ShiftLeft
.fast_accumulate_add
	call .PlanPairFacts
	ld bc, FPP_ACC + 4
	add hl, bc
	ld bc, FSC_TEMP + 4
	push de
	ld d, 5
	and a
.fast_accumulate_byte
	ld a, [bc]
	adc [hl]
	ld [hl], a
	dec hl
	dec bc
	dec d
	jr nz, .fast_accumulate_byte
	pop de
	ret

.CommitPairs
; T[plan]+=z_own*sum and flags|=union for every plain damage plan of this
; defender.
	ld c, 0
.commit_pair
	push bc
	call .PlanIndex
	cp $ff
	jr z, .commit_pair_next
	ld [FSK_STATE], a ; the record index
	ld a, c
	ld [FPK_INDEX], a
	call .PlanPairFacts
	ld a, [hli]
	and 1
	jr z, .commit_pair_next
	push hl
	ld bc, FPP_Z - 1
	add hl, bc
	ld a, [hli]
	ld [FS_MULTIPLIER + 1], a
	ld a, [hl]
	ld [FS_MULTIPLIER + 2], a
	xor a
	ld [FS_MULTIPLIER], a
	pop hl
	ld bc, FPP_ACC - 1
	add hl, bc
	push de
	ld de, FS_MULTIPLICAND
	ld b, 5
.commit_pair_copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .commit_pair_copy
	pop de
	call BossAI_FastMultiply40By24
	ld a, [FSK_STATE]
	ld hl, FS_PRODUCT
	call .AddToRecord
	call .PlanPairFacts
	ld bc, FPP_UNION
	add hl, bc
	ld b, [hl]
	ld a, [FSK_STATE]
	call .OrRecordFlags
.commit_pair_next
	pop bc
	inc c
	ld a, c
	cp 4
	jr c, .commit_pair
	ret
