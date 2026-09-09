; Compact incoming plan lives in the caller's fixed WRAM window.
; Tagged payload12..27 holds either four selected RAW_MAX words + Helmet
; quota + original power, or recovery quota. No owned plan is overwritten.
DEF FSR_BASE EQU 399
DEF FSR_SIZE EQU 48
DEF FSR_MOVE EQU 0
DEF FSR_OPCODE EQU 1
DEF FSR_ACCURACY EQU 2
DEF FSR_PRIORITY EQU 3
DEF FSR_CAN_ACT EQU 4
DEF FSR_CHECK_FLAGS EQU 5
DEF FSR_DAMAGE_FLAGS EQU 6
DEF FSR_HIT_FLAGS EQU 7
DEF FSR_HP_DEPEND EQU 8
DEF FSR_VALID EQU 9
DEF FSR_RANGE EQU 10
DEF FSR_SUPPORT EQU 11
DEF FSR_RAW_MAX EQU 12
DEF FSR_RECOVERY_QUOTA EQU 12
DEF FSR_ITEM_QUOTA EQU 20
DEF FSR_POWER EQU 22
DEF FSR_HIT_HP EQU 28
DEF FSR_MISS_HP EQU 32
DEF FSR_HIT_DELTA EQU 36
DEF FSR_MISS_DELTA EQU 38
DEF FSR_MOMENT EQU 40
DEF FSR_MIN_HITS EQU 43
DEF FSR_MAX_HITS EQU 44
DEF FSR_STEEL EQU 45
DEF FSR_DESCRIPTOR EQU 46
DEF FSR_FALLBACK EQU 0
DEF FSR_DAMAGE EQU 1
DEF FSR_RECOVERY EQU 2
DEF FSR_PURSUIT EQU 3
DEF FSR_ABSENT EQU 4
DEF FSR_MULTI EQU 5 ; multi-hit damage: per-hit maxima, HP advanced hit by hit
DEF FSR_FANG EQU 6 ; Super Fang: half the target's current HP at execution
DEF FSR_FALSE_SWIPE EQU 7 ; single hit capped at target HP-1 at execution
DEF FSR_SELFDESTRUCT EQU 8 ; user faints before its hit/miss check; halved defense
DEF FSR_BOOST EQU 9 ; deterministic defense boost: no HP change, raises the own plans' defender
DEF FSR_BOOST_STEPS EQU 43 ; 1 or 2 stages (reuses the hit bytes)
DEF FSR_BOOST_AXIS EQU 44 ; 1 Defense, 4 Special Defense
; Multi-hit and False Swipe keep the per-regime maximum minus minimum in
; four otherwise unused header/payload bytes so executors can rebuild the
; minimum endpoint for the range flag at the real state.
DEF FSR_MIN_DELTA0 EQU 7
DEF FSR_MIN_DELTA1 EQU 8
DEF FSR_MIN_DELTA2 EQU 23
DEF FSR_MIN_DELTA3 EQU 26
; A plain damage reply keeps its amounts against the boss's own defense boosts
; in the same free bytes (a family never carries both): the raw maximum word
; at the start regime at Defense+1 or Special Defense+2 in bytes 7..8 (byte 8,
; FSR_HP_DEPEND, is never read) and at Defense+2 in bytes 26..27, with a valid
; and a range bit per own boost slot in byte 23 (slot 0 Defense+1 bits 0/1,
; slot 1 Defense+2 bits 2/3, slot 2 Special Defense+2 bits 4/5).
; BossAI_FastCompileReplyVariants writes them after the native compile;
; neither compiler does.
DEF FSR_VARIANT_A EQU 7
DEF FSR_VARIANT_B EQU 26
DEF FSR_VARIANT_FLAGS EQU 23
ASSERT FSR_BASE + FSR_SIZE == 447

MACRO fsr_store
	push af
	ld a, [FSB_PLAN_PTR]
	ld b, a
	ld a, [FSB_PLAN_PTR + 1]
	ld c, a
	ld hl, \1
	add hl, bc
	pop af
	ld [hl], a
ENDM

MACRO fsr_context_byte
	ad_address \1
	ld a, [hl]
	fsr_store \2
ENDM

BossAI_FastCompileReplyPlan::
; DE=prepared incoming AD/AV context, SRAM0 open. Carry=represented.
; AV_REPLY=0 accepts absent without reading any AD or running producers.
; Otherwise require AD_DIRECTION=0 and AD_MOVE=AV_REPLY; bad input rejects
; without writes. Fixed non-HP context/defense is a caller precondition.
; Writes reply48 + bridge + AD range scratch; restores flags/postroll.
; Other WRAM records, all four owned plans, AV and DE/SP are preserved.
; This entry compiles all four HP regimes.
	ld c, 15
.Masked
; C=regime mask. Only masked regimes get amounts/range/support bits; the
; mask is recorded in FSR_VALID and the executor faults on any other regime.
	ld a, c
	ld [FSB_REPLY_REGIMES], a
	ad_address AV_REPLY
	ld a, [hl]
	and a
	jr z, .valid_input
	ld c, a
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jp nz, .invalid
	ad_address AD_MOVE
	ld a, [hl]
	cp c
	jp nz, .invalid
.valid_input
	ld hl, FSR_BASE
	add hl, de
	ld a, h
	ld [FSB_PLAN_PTR], a
	ld a, l
	ld [FSB_PLAN_PTR + 1], a
	ld b, FSR_SIZE
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ad_address AV_REPLY
	ld a, [hl]
	and a
	jr nz, .present
	ld a, FSR_ABSENT
	fsr_store FSR_OPCODE
	scf
	ret
.present
	ld c, 1
	call BossAI_FastExportActionPrefix
	fsr_context_byte AD_MOVE, FSR_MOVE
	fsr_context_byte AD_ACCURACY, FSR_ACCURACY
	fsr_context_byte AD_PRIORITY, FSR_PRIORITY
	ld a, [FSB_PREFIX_CAN_ACT]
	fsr_store FSR_CAN_ACT
	ld a, [FSB_PREFIX_CHECK]
	fsr_store FSR_CHECK_FLAGS
	ld a, [FSB_PREFIX_EFFECT_FLAGS]
	ld b, a
	ld a, [FSB_PREFIX_HIT_FLAGS]
	or b
	fsr_store FSR_DAMAGE_FLAGS
	fsr_context_byte AD_MIN_HITS, FSR_MIN_HITS
	fsr_context_byte AD_MAX_HITS, FSR_MAX_HITS
	ad_address AV_KIND
	ld a, [hl]
	cp AV_SWITCH_ACTION
	jr nz, .ordinary
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_PURSUIT
	jr nz, .ordinary
	ld a, FSR_PURSUIT
	fsr_store FSR_OPCODE
	scf
	ret
.ordinary
	call BossAI_ValuePublicExchange.DefenseAxis
	jr nc, .not_boost
; B=stages, C=axis. The boost itself never changes HP and carries only the
; check flags; the selector applies it to the own plans' variants.
	push bc
	ld a, b
	fsr_store FSR_BOOST_STEPS ; the store macro uses BC
	pop bc
	ld a, c
	fsr_store FSR_BOOST_AXIS
	xor a
	fsr_store FSR_DAMAGE_FLAGS
	ld a, FSR_BOOST
	fsr_store FSR_OPCODE
	scf
	ret
.not_boost
	ld a, [FSB_PREFIX_RECOVERY]
	and a
	jr z, .damage
	ld a, [FSB_PREFIX_QUOTA]
	fsr_store FSR_RECOVERY_QUOTA
	ld a, [FSB_PREFIX_QUOTA + 1]
	fsr_store FSR_RECOVERY_QUOTA + 1
	ld a, FSR_RECOVERY
	fsr_store FSR_OPCODE
	scf
	ret
.damage
	ad_address AD_EFFECT
	ld a, [hl]
	ld b, a
	ld a, FSR_DAMAGE
	ld [FSB_PLAN_OPCODE], a
	xor a
	ld [FSB_PLAN_PATCH], a
	ld [FSB_PLAN_DELTAS], a
	ld a, b
	cp EFFECT_SELFDESTRUCT
	jr nz, .not_selfdestruct
	ld a, FSR_SELFDESTRUCT
	ld [FSB_PLAN_OPCODE], a
	jr .family_ready
.not_selfdestruct
	cp EFFECT_SUPER_FANG
	jr nz, .not_fang
	ld a, FSR_FANG
	ld [FSB_PLAN_OPCODE], a
	jr .family_ready
.not_fang
	cp EFFECT_FALSE_SWIPE
	jr nz, .not_false_swipe
	ld a, FSR_FALSE_SWIPE
	ld [FSB_PLAN_OPCODE], a
	ld a, 1
	ld [FSB_PLAN_PATCH], a
	ld [FSB_PLAN_DELTAS], a
	ad_address AD_EFFECT
	ld [hl], EFFECT_NORMAL_HIT
	jr .family_ready
.not_false_swipe
	ad_address AD_MIN_HITS
	ld a, [hli]
	dec a
	jr nz, .multi
	ld a, [hl]
	dec a
	jr z, .family_ready
.multi
; hits cross HP regimes inside one action: compile every regime
	ld a, FSR_MULTI
	ld [FSB_PLAN_OPCODE], a
	ld a, 2
	ld [FSB_PLAN_PATCH], a
	ld a, 1
	ld [FSB_PLAN_DELTAS], a
	ld a, 15
	ld [FSB_REPLY_REGIMES], a
	ad_address AD_MIN_HITS
	ld [hl], 1
	inc hl
	ld [hl], 1
.family_ready
	ld a, STEEL
	call BossAI_DamageKernel.AttackerContribution
	fsr_store FSR_STEEL
	fsr_context_byte AD_POWER, FSR_POWER
	call .Descriptor
	ld a, h
	fsr_store FSR_DESCRIPTOR
; Descriptor was saved in the bridge by the descriptor builder.
	ld a, [FSB_PREFIX_QUOTA + 1]
	fsr_store FSR_DESCRIPTOR + 1
	ad_address AD_FLAGS
	ld a, [hl]
	ld [FSB_PLAN_FLAGS], a
	ad_address AD_MAX_POSTROLL
	ld a, [hl]
	ld [FSB_PLAN_POSTROLL], a
	xor a
	ld [FSB_PLAN_REGIME], a
.regime
	ld a, [FSB_PLAN_REGIME]
	ld c, a
	ld b, 0
	ld hl, .Bits
	add hl, bc
	ld a, [FSB_REPLY_REGIMES]
	and [hl]
	jp z, .next_regime ; unreachable regime: amount and masks stay zero
	ld a, [FSB_PLAN_REGIME]
	add a ; maps regime bits0..1 to AD flags1..2
	ld b, a
	ld a, [FSB_PLAN_FLAGS]
	and ~((1 << AD_ATTACKER_LOW_F) | (1 << AD_DEFENDER_HIGH_F))
	or b
	ad_address AD_FLAGS
	ld [hl], a
	call BossAI_FastExportDamageRange
	ld a, [FSB_PLAN_REGIME]
	add a
	add FSR_RAW_MAX
	call .PlanAddress
	ld a, [FSB_RAW_MAX]
	ld [hli], a
	ld a, [FSB_RAW_MAX + 1]
	ld [hl], a
	ld a, [FSB_PLAN_DELTAS]
	and a
	jr z, .no_delta
	ld a, [FSB_PLAN_REGIME]
	ld c, a
	ld b, 0
	ld hl, .MinDeltaOffsets
	add hl, bc
	ld a, [hl]
	call .PlanAddress
	ld a, [FSB_RAW_MIN + 1]
	ld c, a
	ld a, [FSB_RAW_MAX + 1]
	sub c
	ld [hl], a
	ld a, [FSB_RAW_MIN]
	ld c, a
	ld a, [FSB_RAW_MAX]
	sbc c
	jr z, .no_delta
	xor a
	ld [FSB_PLAN_OPCODE], a ; a delta wider than a byte leaves the reply to the fallback
.no_delta
	ld a, [FSB_PLAN_REGIME]
	ld c, a
	ld b, 0
	ld hl, .Bits
	add hl, bc
	ld a, [hl]
	push af
	ld a, [FSB_RANGE_SUPPORT]
	and a
	jr z, .range_flag
	ld a, FSR_SUPPORT
	call .PlanAddress
	pop af
	push af
	or [hl]
	ld [hl], a
.range_flag
	ld a, [FSB_RANGE_FLAGS]
	and 1 << AV_AMOUNT_RANGE_F
	jr z, .next
	ld a, FSR_RANGE
	call .PlanAddress
	pop af
	push af
	or [hl]
	ld [hl], a
.next
	pop af
.next_regime
	ld hl, FSB_PLAN_REGIME
	inc [hl]
	ld a, [hl]
	cp 4
	jp c, .regime
	ld a, [FSB_PLAN_FLAGS]
	ad_address AD_FLAGS
	ld [hl], a
	ld a, [FSB_PLAN_POSTROLL]
	ad_address AD_MAX_POSTROLL
	ld [hl], a
	call .RestorePatch
	ld a, [FSB_PLAN_DELTAS]
	and a
	jr nz, .hp_depend_ready ; byte 8 carries the regime-1 delta instead
	ld a, 3
	fsr_store FSR_HP_DEPEND
.hp_depend_ready
	ld a, [FSB_REPLY_REGIMES]
	fsr_store FSR_VALID
	ld a, [FSB_PLAN_OPCODE]
	fsr_store FSR_OPCODE
	and a
	ret z ; unrepresented after all: header written, fallback follows
	scf
	ret
.RestorePatch
	ld a, [FSB_PLAN_PATCH]
	and a
	ret z
	dec a
	jr nz, .restore_hits
	ad_address AD_EFFECT
	ld [hl], EFFECT_FALSE_SWIPE
	ret
.restore_hits
	ld a, FSR_MIN_HITS
	call .PlanAddress
	ld a, [hli]
	ld b, [hl]
	ad_address AD_MIN_HITS
	ld [hli], a
	ld [hl], b
	ret
.MinDeltaOffsets
	db FSR_MIN_DELTA0, FSR_MIN_DELTA1, FSR_MIN_DELTA2, FSR_MIN_DELTA3
.invalid
	and a
	ret
.PlanAddress
; A=plan offset. BC/HL scratch; DE preserved.
	ld l, a
	ld h, 0
	ld a, [FSB_PLAN_PTR]
	ld b, a
	ld a, [FSB_PLAN_PTR + 1]
	ld c, a
	add hl, bc
	ret
.Descriptor
; Only the known owned defender's Helmet is available to this public model.
	call BossAI_BuildPublicDamageContext.OwnItem
	cp ROCKY_HELMET
	jr nz, .no_helmet
	ad_address AD_FLAGS
	bit AD_SUBSTITUTE_F, [hl]
	jr nz, .no_helmet
	ad_address AD_MOVE
	ld a, [hl]
	dec a
	ld c, a
	ld b, 0
	ld hl, MoveContactFlags
	add hl, bc
	ld a, BANK(MoveContactFlags)
	call GetFarByte
	and a
	jr z, .no_helmet
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, 1
	ld h, ROCKY_HELMET_DEN
	call BossAI_DamageKernel.Scale
	push bc
	ld a, b
	fsr_store FSR_ITEM_QUOTA
	pop bc
	ld a, c
	fsr_store FSR_ITEM_QUOTA + 1
	ld c, 1
	jr .effect
.no_helmet
	ld c, 0
.effect
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_LEECH_HIT
	jr z, .drain
	cp EFFECT_DREAM_EATER
	jr z, .drain
	cp EFFECT_RECOIL_HIT
	jr nz, .descriptor
	ld a, c
	add 6
	ld c, a
	jr .descriptor
.drain
	ld a, c
	add 3
	ld c, a
.descriptor
	sla c
	ld b, 0
	ld hl, BossAI_FastOwnCommandDescriptors
	add hl, bc
	ld a, l
	ld [FSB_PREFIX_QUOTA + 1], a
	ret
.Bits
	db 1, 2, 4, 8

