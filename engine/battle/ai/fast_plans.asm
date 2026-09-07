; Owned action plans use the fixed 64-byte contract. Amounts are valid only
; while non-HP public context inputs (including projected defense) are fixed.
; The compiler leaves explicit fallback plans for families not represented.
DEF FSP_BASE EQU $a2f8
DEF FSP_SIZE EQU 64
DEF FSP_INDEX EQU 0
DEF FSP_KIND EQU 1
DEF FSP_SLOT EQU 2
DEF FSP_MOVE EQU 3
DEF FSP_OPCODE EQU 4
DEF FSP_ACCURACY EQU 5
DEF FSP_PRIORITY EQU 6
DEF FSP_CAN_ACT EQU 7
DEF FSP_CHECK_FLAGS EQU 8
DEF FSP_DAMAGE_FLAGS EQU 9
DEF FSP_HIT_FLAGS EQU 10
DEF FSP_SETUP_FLAGS EQU 11
DEF FSP_HP_DEPEND EQU 12
DEF FSP_VALID EQU 13
DEF FSP_RANGE EQU 14
DEF FSP_SUPPORT EQU 15
DEF FSP_RAW_MIN EQU 16 ; four BE words, attacker-low + 2*defender-high
DEF FSP_RAW_MAX EQU 24 ; opposite endpoint retained for exact range metadata
DEF FSP_HIT_HP EQU 32
DEF FSP_MISS_HP EQU 36
DEF FSP_HIT_DELTA EQU 40
DEF FSP_MISS_DELTA EQU 42
DEF FSP_MOMENT EQU 44
DEF FSP_STANDALONE_HIT_FLAGS EQU 47
DEF FSP_STANDALONE_MISS_FLAGS EQU 48
DEF FSP_DEFENSE_AXIS EQU 49
DEF FSP_DEFENSE_STAGE EQU 50
DEF FSP_DEFENSE EQU 51
DEF FSP_RECOVERY_QUOTA EQU 53
DEF FSP_ITEM_QUOTA EQU 55
DEF FSP_STEEL EQU 57
DEF FSP_MIN_HITS EQU 58
DEF FSP_MAX_HITS EQU 59
DEF FSP_DESCRIPTOR EQU 60 ; same-bank command descriptor for native executor
DEF FSP_MIN_POSTROLL EQU 62
DEF FSP_MAX_POSTROLL EQU 63
DEF FSP_FALLBACK EQU 0
DEF FSP_DAMAGE EQU 1
DEF FSP_RECOVERY EQU 2
ASSERT FSP_BASE + 4 * FSP_SIZE == FSA_OWN

; Compiler scratch is in the existing producer bridge, after entry loss.
DEF FSB_PLAN_PTR EQU $a489
DEF FSB_PLAN_INDEX EQU $a48b
DEF FSB_PLAN_FLAGS EQU $a48c
DEF FSB_PLAN_POSTROLL EQU $a48d
DEF FSB_PLAN_REGIME EQU $a48e
ASSERT FSB_PLAN_REGIME < FSB_PREFIX

MACRO fsp_store
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

MACRO fsp_context_byte
	ad_address \1
	ld a, [hl]
	fsp_store \2
ENDM

BossAI_FastCompileOwnedPlan::
; C=original PP slot0..3, DE=prepared owned AD/AV context, SRAM bank0 open.
; Carry=represented recovery/single-hit amount plan. Clear means an explicit
; fallback opcode (or invalid input, rejected without writes). No transitions
; or standalone moments are computed here; caller supplies actor state.
; Writes only selected plan + bridge; AD range/output scratch may change.
; Restores source flags and maximum postroll; AV and DE/SP are preserved.
; Requires AD_DIRECTION=1. A future defense override invalidates this plan.
	ld a, c
	cp 4
	jp nc, .invalid
	ad_address AD_DIRECTION
	ld a, [hl]
	cp 1
	jp nz, .invalid
	ld a, c
	ld [FSB_PLAN_INDEX], a
	ld b, 0
	rept 6
	sla c
	rl b
	endr
	ld hl, FSP_BASE
	add hl, bc
	ld a, h
	ld [FSB_PLAN_PTR], a
	ld a, l
	ld [FSB_PLAN_PTR + 1], a
	ld b, FSP_SIZE
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ld c, 0
	call BossAI_FastExportActionPrefix
	call BossAI_FastExportSetupFlags
	ld a, [FSB_PLAN_INDEX]
	fsp_store FSP_INDEX
	fsp_context_byte AV_KIND, FSP_KIND
	fsp_context_byte AD_OWN_SLOT, FSP_SLOT
	fsp_context_byte AD_MOVE, FSP_MOVE
	fsp_context_byte AD_ACCURACY, FSP_ACCURACY
	fsp_context_byte AD_PRIORITY, FSP_PRIORITY
	ld a, [FSB_PREFIX_CAN_ACT]
	fsp_store FSP_CAN_ACT
	ld a, [FSB_PREFIX_CHECK]
	fsp_store FSP_CHECK_FLAGS
	ld a, [FSB_PREFIX_EFFECT_FLAGS]
	ld b, a
	ld a, [FSB_PREFIX_HIT_FLAGS]
	or b
	fsp_store FSP_DAMAGE_FLAGS
	ld a, [FSB_SETUP_FLAGS]
	fsp_store FSP_SETUP_FLAGS
	fsp_context_byte AD_MIN_HITS, FSP_MIN_HITS
	fsp_context_byte AD_MAX_HITS, FSP_MAX_HITS
	fsp_context_byte AD_POSTROLL, FSP_MIN_POSTROLL
	fsp_context_byte AD_MAX_POSTROLL, FSP_MAX_POSTROLL
	call BossAI_ValuePublicExchange.DefenseAxis
	jp c, .invalid ; zero opcode, no amount/support masks
	ld a, [FSB_PREFIX_RECOVERY]
	and a
	jr z, .damage
	ld a, [FSB_PREFIX_QUOTA]
	fsp_store FSP_RECOVERY_QUOTA
	ld a, [FSB_PREFIX_QUOTA + 1]
	fsp_store FSP_RECOVERY_QUOTA + 1
	ld a, FSP_RECOVERY
	fsp_store FSP_OPCODE
	scf
	ret
.damage
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SELFDESTRUCT
	jp z, .invalid
	cp EFFECT_FALSE_SWIPE
	jp z, .invalid
	cp EFFECT_SUPER_FANG
	jp z, .invalid
	ad_address AD_MIN_HITS
	ld a, [hli]
	cp 1
	jp nz, .invalid
	ld a, [hl]
	cp 1
	jp nz, .invalid
	ld a, STEEL
	call BossAI_DamageKernel.AttackerContribution
	fsp_store FSP_STEEL
	call .Descriptor
	ld a, h
	fsp_store FSP_DESCRIPTOR
; Descriptor was saved in the bridge by the descriptor builder.
	ld a, [FSB_PREFIX_QUOTA + 1]
	fsp_store FSP_DESCRIPTOR + 1
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
	add FSP_RAW_MIN
	call .PlanAddress
	ld a, [FSB_RAW_MIN]
	ld [hli], a
	ld a, [FSB_RAW_MIN + 1]
	ld [hl], a
	ld a, [FSB_PLAN_REGIME]
	add a
	add FSP_RAW_MAX
	call .PlanAddress
	ld a, [FSB_RAW_MAX]
	ld [hli], a
	ld a, [FSB_RAW_MAX + 1]
	ld [hl], a
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
	ld a, FSP_SUPPORT
	call .PlanAddress
	pop af
	push af
	or [hl]
	ld [hl], a
.range_flag
	ld a, [FSB_RANGE_FLAGS]
	and 1 << AV_AMOUNT_RANGE_F
	jr z, .next
	ld a, FSP_RANGE
	call .PlanAddress
	pop af
	push af
	or [hl]
	ld [hl], a
.next
	pop af
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
	ld a, 3
	fsp_store FSP_HP_DEPEND
	ld a, 15
	fsp_store FSP_VALID
	ld a, FSP_DAMAGE
	fsp_store FSP_OPCODE
	scf
	ret
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
; Select native same-bank descriptor: effect tag0plain/1drain/2recoil,
; then item tag0none/1LifeOrb/2ShellBell. No item command executes here.
	call BossAI_BuildPublicDamageContext.OwnItem
	ld c, 0
	cp LIFE_ORB
	jr nz, .shell_bell
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, 1
	ld h, LIFE_ORB_RECOIL_DEN
	call BossAI_DamageKernel.Scale
	push bc
	ld a, b
	fsp_store FSP_ITEM_QUOTA
	pop bc
	ld a, c
	fsp_store FSP_ITEM_QUOTA + 1
	ld c, 1
	jr .effect
.shell_bell
	cp SHELL_BELL
	jr nz, .effect
	ld c, 2
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
