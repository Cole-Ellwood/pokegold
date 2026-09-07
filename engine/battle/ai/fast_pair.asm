; Factored normalized pair: standalone baseline plus active/active correction.
; Original-event paths below are visited only for uncertainty, using FlagsOnly.
DEF FPK_INDEX EQU $a54c
DEF FPK_ORDER EQU $a54d ; 0own first,1reply first,2modeled tie
DEF FPK_FLAGS EQU $a54e
DEF FPK_CURRENT EQU $a54f
DEF FPK_K EQU $a550 ; signed16 combined order correction
DEF FPK_OWN_DELTA EQU $a552
DEF FPK_REPLY_DELTA EQU $a554
DEF FPK_CONTEXT EQU $a556
DEF FPK_FIRST_EVENT EQU $a558
DEF FPK_SECOND_EVENT EQU $a559
DEF FPK_OWN_Z EQU $a55a ; unsigned0..256
DEF FPK_REPLY_Z EQU $a55c
DEF FPK_LEFT EQU $a55e
DEF FPK_MODE EQU $a55f ; 0full numerator,1interaction correction only
DEF FPK_TOTAL EQU $a578 ; five bytes, unweighted numerator, denominator2*65536
ASSERT FSO_DELTA + 2 == FPK_INDEX
ASSERT FPK_MODE < $a560
ASSERT FPK_TOTAL + 5 <= $a590

BossAI_FastNormalizedPair::
; C=owned plan0..3, A=order0..2, DE=context with compact reply.
; Both standalone plans and imported actors/tables must already be complete.
; Fixed public facts/defense must remain valid for every reachable successor.
; SRAM0 open. DE/SP preserved. Carry=accepted, BC=combined signed correction K.
; Outputs FPK_TOTAL and FPK_FLAGS (action flags plus modeled tie uncertainty).
; Setup/open-prior/unknown-speed flags belong to the caller. No plan changes.
; Unsupported or invalid entry returns clear before all writes.
	ld b, 0
	jr .validate
.CorrectionOnly
; Same entry/flags, but FPK_TOTAL is z_own*z_reply*K in the signed40 ring.
; The selector owns standalone initialization and the shared incoming sum.
	ld b, 1
.validate
	cp 3
	jp nc, .reject
	push af
	ld a, c
	cp 4
	jp nc, .reject_af
	push bc
	ld b, 0
	rept 6
	sla c
	rl b
	endr
; The factoring needs a miss to be identity: Selfdestruct pairs use
; BossAI_FastFullNativePair instead.
	ld hl, FSP_BASE + FSP_OPCODE
	add hl, bc
	ld a, [hl]
	and a
	jp z, .reject_bc
	cp FSP_SELFDESTRUCT
	jp nc, .reject_bc
	ad_address FSR_BASE + FSR_OPCODE
	ld a, [hl]
	and a
	jp z, .reject_bc
	cp FSR_SELFDESTRUCT
	jp nc, .reject_bc
	pop bc
	pop af
	ld [FPK_ORDER], a
	ld a, b
	ld [FPK_MODE], a
	ld a, c
	ld [FPK_INDEX], a
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	push de
	xor a
	ld [FPK_FLAGS], a
	ld [FPK_K], a
	ld [FPK_K + 1], a
	ld a, FSP_OPCODE
	call .OwnAddress
	ld a, [hl]
	ld bc, 256
	cp FSP_RECOVERY
	jr z, .own_mass
	ld a, FSP_ACCURACY
	call .OwnAddress
	ld a, [hl]
	call .Decode
.own_mass
	ld a, b
	ld [FPK_OWN_Z], a
	ld a, c
	ld [FPK_OWN_Z + 1], a
	ld a, FSR_OPCODE
	call .ReplyAddress
	ld a, [hl]
	ld bc, 256
	cp FSR_RECOVERY
	jr z, .reply_mass
	ld bc, 0
	cp FSR_PURSUIT
	jr z, .reply_mass
	cp FSR_ABSENT
	jr z, .reply_mass
	ld a, FSR_ACCURACY
	call .ReplyAddress
	ld a, [hl]
	call .Decode
.reply_mass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	ld a, FSP_HIT_DELTA
	call .OwnAddress
	ld a, [hli]
	ld [FPK_OWN_DELTA], a
	ld a, [hl]
	ld [FPK_OWN_DELTA + 1], a
	ld a, FSR_HIT_DELTA
	call .ReplyAddress
	ld a, [hli]
	ld [FPK_REPLY_DELTA], a
	ld a, [hl]
	ld [FPK_REPLY_DELTA + 1], a
	ld a, [FPK_ORDER]
	ld b, 1
	cp 2
	jr nz, .first_order
	ld a, 1 << AV_UNKNOWN_ORDER_F
	ld [FPK_FLAGS], a
	xor a
	inc b
.first_order
	ld [FPK_CURRENT], a
	ld a, b
	ld [FPK_LEFT], a
.order
	call .Correction
	call .Flags
	ld hl, FPK_LEFT
	dec [hl]
	jr z, .total
	ld a, [FPK_CURRENT]
	xor 1
	ld [FPK_CURRENT], a
	jr .order
.total
	call .Total
	ld a, [FPK_K]
	ld b, a
	ld a, [FPK_K + 1]
	ld c, a
	pop de
	scf
	ret
.reject_bc
	pop bc
.reject_af
	pop af
.reject
	and a
	ret

.Correction
; Only the normalized active/active terminal value is evaluated numerically.
	ld hl, FPK_OWN_Z
	ld a, [hli]
	or [hl]
	ret z
	inc hl
	ld a, [hli]
	or [hl]
	ret z
	call .InitialContinuation
	xor a
	ld [FPK_FIRST_EVENT], a
	call .FirstHP
	call .Context
	ld hl, $a448
	ld a, [FPK_CURRENT]
	and a
	jr nz, .own_second
	xor a
	call BossAI_FastExecuteReplyPlan
	jr .terminal
.own_second
	ld a, [FPK_INDEX]
	ld c, a
	xor a
	call BossAI_FastExecuteOwnedPlan
.terminal
	call BossAI_FastBuildOwnedStandalone.Delta
	ld a, [FPK_OWN_DELTA + 1]
	ld l, a
	ld a, c
	sub l
	ld c, a
	ld a, [FPK_OWN_DELTA]
	ld h, a
	ld a, b
	sbc h
	ld b, a
	ld a, [FPK_REPLY_DELTA + 1]
	ld l, a
	ld a, c
	sub l
	ld c, a
	ld a, [FPK_REPLY_DELTA]
	ld h, a
	ld a, b
	sbc h
	ld b, a
	ld a, [FPK_ORDER]
	cp 2
	jr z, .add_correction
	sla c
	rl b
.add_correction
	ld a, [FPK_K + 1]
	add c
	ld [FPK_K + 1], a
	ld a, [FPK_K]
	adc b
	ld [FPK_K], a
	ret

.Flags
; Only positive original masses are reachable, even for normalized z=0/256.
	xor a
	ld [FPK_FIRST_EVENT], a
.first_event
	ld a, [FPK_CURRENT]
	call .Accuracy
	ld a, [FPK_FIRST_EVENT]
	call .EventMass
	ld a, b
	or c
	jp z, .next_first
	call .InitialContinuation
	ld a, [FPK_CURRENT]
	and a
	jr nz, .first_reply_flags
	ld a, [FPK_FIRST_EVENT]
	add FSP_STANDALONE_HIT_FLAGS
	call .OwnAddress
	ld a, [hl]
	ld [$a458], a
	jr .first_flags_ready
.first_reply_flags
	call .Context
	ld hl, $a448
	ld a, [FPK_FIRST_EVENT]
	call BossAI_FastExecuteReplyPlan.FlagsOnly
.first_flags_ready
	call .FirstHP
	xor a
	ld [FPK_SECOND_EVENT], a
.second_event
	ld a, [FPK_CURRENT]
	xor 1
	call .Accuracy
	ld a, [FPK_SECOND_EVENT]
	call .EventMass
	ld a, b
	or c
	jr z, .next_second
	call .Context
	ld hl, $a448
	ld a, [FPK_CURRENT]
	and a
	jr nz, .second_own_flags
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastExecuteReplyPlan.FlagsOnly
	jr .next_second
.second_own_flags
	ld a, [FPK_INDEX]
	ld c, a
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastExecuteOwnedPlan.FlagsOnly
.next_second
	ld hl, FPK_SECOND_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jr c, .second_event
	ld a, [$a458]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
.next_first
	ld hl, FPK_FIRST_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .first_event
	ret

.InitialContinuation
	ld hl, $a448
	ld b, 24
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ld a, [FSA_START_HP]
	ld [$a448], a
	ld a, [FSA_START_HP + 1]
	ld [$a449], a
	ld a, [FSA_PLAYER]
	ld [$a44a], a
	ld a, [FSA_PLAYER + 1]
	ld [$a44b], a
	ret
.FirstHP
	ld a, [FPK_FIRST_EVENT]
	add a
	add a
	ld c, a
	ld a, [FPK_CURRENT]
	and a
	ld a, c
	jr nz, .reply_hp
	add FSP_HIT_HP
	call .OwnAddress
	jr .copy_first
.reply_hp
	add FSR_HIT_HP
	call .ReplyAddress
.copy_first
	ld de, $a448
	ld b, 4
.copy_hp
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_hp
	ret
.Accuracy
; A=0owned/1reply. Original p, including ignored original recovery accuracy.
	and a
	jr nz, .reply_accuracy
	ld a, FSP_ACCURACY
	call .OwnAddress
	jr .read_accuracy
.reply_accuracy
	ld a, FSR_ACCURACY
	call .ReplyAddress
.read_accuracy
	ld a, [hl]
.Decode
	ld b, 0
	ld c, a
	cp 255
	ret nz
	inc b
	inc c
	ret
.EventMass
	and a
	ret z
	xor a
	sub c
	ld c, a
	ld a, 1
	sbc b
	ld b, a
	ret
.OwnAddress
	push af
	ld a, [FPK_INDEX]
	ld c, a
	ld b, 0
	rept 6
	sla c
	rl b
	endr
	ld hl, FSP_BASE
	add hl, bc
	pop af
	ld c, a
	ld b, 0
	add hl, bc
	ret
.ReplyAddress
	push af
	call .Context
	ld hl, FSR_BASE
	add hl, de
	pop af
	ld c, a
	ld b, 0
	add hl, bc
	ret
.Context
	ld a, [FPK_CONTEXT]
	ld d, a
	ld a, [FPK_CONTEXT + 1]
	ld e, a
	ret

.Total
; 2*65536*1024 + 512*(mu_own+mu_reply) + z_own*z_reply*K.
	ld hl, FPK_TOTAL
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ld a, [FPK_MODE]
	and a
	jr nz, .correction_total
	ld a, 8
	ld [FPK_TOTAL + 1], a
	ld a, FSP_MOMENT
	call .OwnAddress
	call .Moment512
	ld a, FSR_MOMENT
	call .ReplyAddress
	call .Moment512
.correction_total
	ld a, [FPK_K]
	ld b, a
	ld a, [FPK_K + 1]
	ld c, a
	or b
	ret z
	ld a, b
	ld [FS_MULTIPLICAND + 3], a
	ld a, c
	ld [FS_MULTIPLICAND + 4], a
	ld a, b
	add a
	sbc a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld [FS_MULTIPLICAND + 2], a
	xor a
	ld [FS_MULTIPLIER], a
	ld a, [FPK_OWN_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_OWN_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
	ld hl, FS_PRODUCT
	ld de, FS_MULTIPLICAND
	ld b, 5
.product
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .product
	xor a
	ld [FS_MULTIPLIER], a
	ld a, [FPK_REPLY_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_REPLY_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
	ld hl, FS_PRODUCT + 4
	jr .AddTotal
.Moment512
; HL=signed24 moment; sign-extend before shifting nine bits.
	call .ShiftMoment512
	jr .AddTotal
.ShiftMoment512
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
	ld b, 9
.shift
	ld hl, FS_MULTIPLICAND + 4
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec b
	jr nz, .shift
	ld hl, FS_MULTIPLICAND + 4
	ret
.SubtractBaseline
; FPK_TOTAL already contains the full fallback N. Replace the same baseline
; assigned to this pair, using current stored moments (zero for opcode0).
	ld hl, FPK_TOTAL + 1
	ld a, [hl]
	sub 8
	ld [hld], a
	ld a, [hl]
	sbc 0
	ld [hl], a
	ld a, FSP_MOMENT
	call .OwnAddress
	call .SubtractMoment512
	ld a, FSR_MOMENT
	call .ReplyAddress
.SubtractMoment512
	call .ShiftMoment512
	ld b, 5
	scf
.negate
	ld a, [hl]
	cpl
	adc 0
	ld [hld], a
	dec b
	jr nz, .negate
	ld hl, FS_MULTIPLICAND + 4
.AddTotal
	ld de, FPK_TOTAL + 4
	ld b, 5
	and a
.add
	ld a, [de]
	adc [hl]
	ld [de], a
	dec de
	dec hl
	dec b
	jr nz, .add
	ret
