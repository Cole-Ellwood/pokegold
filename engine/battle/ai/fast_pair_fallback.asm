; Cold whole-pair and unary fallback evaluators, in their own bank behind far
; entries so the hot fast-prototype bank keeps its space. Complete unweighted
; pair over every positive original-event pair and every modeled order.
; Terminals come from the direct reference (only the old producer prefix is
; mutable; no legacy JC or SRAM HP-table lifetime is entered) or, in the
; native mode, from the compact executors reached through main-bank stubs.

BossAI_FastFallbackPairCorrectionFar::
; Selector entry: C=plan, DE=context, order descriptor in FS_ORDER (the
; farcall macro clobbers A and HL). Carry and BC survive the far return.
	ld hl, FS_ORDER
	add hl, de
	ld a, [hl]
	jr BossAI_FastFallbackPair.CorrectionOnly
BossAI_FastFallbackPairNativeFar::
	ld hl, FS_ORDER
	add hl, de
	ld a, [hl]
	jr BossAI_FastFallbackPair.Native

BossAI_FastFallbackPair::
; C=compiled owned plan0..3 (including opcode0), DE=current reply/context,
; A=actual order descriptor0own first/1reply first/2modeled tie.
; Ordinary move kind only; original plan/reply accuracies must be current.
; For a single order the direct evaluator resolves public order itself. The
; caller must supply the actual descriptor; only a genuine tie is expanded.
; SRAM0 open. Output FPK_TOTAL=N, FPK_FLAGS includes setup/order/action flags.
; DE/SP preserved; carry=accepted, other registers scratch. Reject before writes.
	ld b, 0
	jr .validate
.CorrectionOnly
; Return N minus the exact standalone baseline already assigned by the caller.
; Opcode0 moments are zero; never subtract a made-up rounded utility.
	ld b, 1
	jr .validate
.Native
; Correction only, with both actions executed from their compact plans in
; every order (a Selfdestruct miss is not identity, so all four terminals
; interact). Both standalone records, actors and HP tables must be live;
; both opcodes must be represented. FPK_FLAGS holds action flags plus the
; modeled-tie flag, like BossAI_FastFallbackPair.
	ld b, 3
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
	ld hl, FSP_BASE + FSP_KIND
	add hl, bc
	ld a, [hl]
	and a
	jp nz, .reject_bc
	pop bc
	bit 1, b
	jr z, .modes_ok
	inc hl
	inc hl
	inc hl ; FSP_OPCODE
	ld a, [hl]
	and a
	jp z, .reject_af
	cp FSP_SELFDESTRUCT + 1
	jp nc, .reject_af
	ad_address FSR_BASE + FSR_OPCODE
	ld a, [hl]
	and a
	jp z, .reject_af
	cp FSR_SELFDESTRUCT + 1
	jp nc, .reject_af
.modes_ok
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
	ld [FPK_FIRST_EVENT], a
	ld hl, FPK_TOTAL
	ld b, 5
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ld a, [FPK_MODE]
	bit 1, a
	jr z, .own_event
	ld a, [FPK_ORDER]
	cp 2
	jr nz, .own_event
	ld a, 1 << AV_UNKNOWN_ORDER_F ; the direct evaluator raises this itself
	ld [FPK_FLAGS], a
.own_event
	xor a
	call BossAI_FastFallbackPair.Accuracy
	ld a, [FPK_FIRST_EVENT]
	call BossAI_FastFallbackPair.EventMass
	ld a, b
	ld [FPK_OWN_Z], a
	ld a, c
	ld [FPK_OWN_Z + 1], a
	or b
	jp z, .next_own
	xor a
	ld [FPK_SECOND_EVENT], a
.reply_event
	ld a, 1
	call BossAI_FastFallbackPair.Accuracy
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastFallbackPair.EventMass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	or b
	jp z, .next_reply
	ld a, [FPK_ORDER]
	ld b, 1
	cp 2
	jr nz, .first_order
	xor a
	inc b
.first_order
	ld [FPK_CURRENT], a ; a single order starts as the actual one (native mode executes it)
	ld a, b
	ld [FPK_LEFT], a
.order
	ld a, [FPK_MODE]
	bit 1, a
	jr nz, .native_terminal
	call .EventContext
	farcall BossAI_ValuePublicExchangeFromContext
	ad_address AV_UNCERTAIN
	ld a, [hl]
	jr .accumulate
.native_terminal
	call BossAI_FastFallbackPair.InitialContinuation
	ld a, [FPK_CURRENT]
	and a
	jr nz, .reply_first
	farcall BossAI_FastFallbackOwnAction
	farcall BossAI_FastFallbackReplyAction
	jr .terminal
.reply_first
	farcall BossAI_FastFallbackReplyAction
	farcall BossAI_FastFallbackOwnAction
.terminal
	farcall BossAI_FastFallbackDelta ; BC=V(final)-V(initial)
	ld hl, 1024
	add hl, bc ; U=1024+V(final)-V(initial), positive
	ld b, h
	ld c, l
	ld a, [$a458]
.accumulate
; A=reached flags, BC=U
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	ld a, b
	ld [FS_MULTIPLICAND + 3], a
	ld a, c
	ld [FS_MULTIPLICAND + 4], a
	xor a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld [FS_MULTIPLICAND + 2], a
	ld [FS_MULTIPLIER], a
	ld a, [FPK_OWN_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_OWN_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	farcall BossAI_FastMultiply40By24
	ld hl, FS_PRODUCT
	ld de, FS_MULTIPLICAND
	ld b, 5
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	xor a
	ld [FS_MULTIPLIER], a
	ld a, [FPK_REPLY_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_REPLY_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	farcall BossAI_FastMultiply40By24
	ld a, [FPK_ORDER]
	cp 2
	jr z, .add
	ld hl, FS_PRODUCT + 4
	sla [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
	dec hl
	rl [hl]
.add
	ld hl, FS_PRODUCT + 4
	call BossAI_FastFallbackPair.AddTotal
	ld hl, FPK_LEFT
	dec [hl]
	jr z, .next_reply
	ld hl, FPK_CURRENT
	inc [hl]
	jp .order
.next_reply
	ld hl, FPK_SECOND_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .reply_event
.next_own
	ld hl, FPK_FIRST_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .own_event
	ld a, [FPK_MODE]
	and a
	call nz, BossAI_FastFallbackPair.SubtractBaseline
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
.EventContext
; All FarCall inputs live in the producer prefix, not A/HL. The direct entry
; rebuilds AD and initializes HP/defense/uncertainty on every original event.
	call BossAI_FastFallbackPair.Context
	ld a, FSP_SLOT
	call BossAI_FastFallbackPair.OwnAddress
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	ld a, FSP_MOVE
	call BossAI_FastFallbackPair.OwnAddress
	ld a, [hl]
	ad_address AV_MOVE
	ld [hl], a
	ad_address AV_KIND
	ld [hl], AV_MOVE_ACTION
	ld a, FSR_MOVE
	call BossAI_FastFallbackPair.ReplyAddress
	ld a, [hl]
	ad_address AV_REPLY
	ld [hl], a
	ld a, [FPK_SECOND_EVENT]
	add a
	ld b, a
	ld a, [FPK_FIRST_EVENT]
	or b
	ld b, a
	ld a, [FPK_ORDER]
	cp 2
	ld a, b
	jr nz, .branch
	or 1 << 2
	ld b, a
	ld a, [FPK_CURRENT]
	and a
	ld a, b
	jr nz, .branch
	or 1 << 3 ; first modeled order is owned first, matching native convention
.branch
	ad_address AV_BRANCH
	ld [hl], a
	ret

; Local copies of the factored pair's small helpers (the originals live in
; the fast-prototype bank).
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
.InitialContinuation
	ld hl, $a448
	ld b, 24
	xor a
.clear_continuation
	ld [hli], a
	dec b
	jr nz, .clear_continuation
	ld a, [FSA_START_HP]
	ld [$a448], a
	ld a, [FSA_START_HP + 1]
	ld [$a449], a
	ld a, [FSA_PLAYER]
	ld [$a44a], a
	ld a, [FSA_PLAYER + 1]
	ld [$a44b], a
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
.add_total
	ld a, [de]
	adc [hl]
	ld [de], a
	dec de
	dec hl
	dec b
	jr nz, .add_total
	ret
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
.shift_moment
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
	jr nz, .shift_moment
	ld hl, FS_MULTIPLICAND + 4
	ret

BossAI_FastUnaryFallback::
; B=candidate kind (switch or wait), C=owned slot ($ff active), DE=context whose
; compact reply supplies FSR_MOVE/FSR_ACCURACY (opcode may be 0). FSC_BASELINE
; must hold the exact standalone baseline already assigned to this candidate.
; Only positive original reply events run, through the direct unprepared
; evaluator: own event mass 256 and a single order, so
; FPK_TOTAL = 512*sum(p*U) - baseline in the signed40 ring and FPK_FLAGS is the
; union of reached flags. SRAM0 open, DE/SP preserved, carry=accepted; other
; kinds reject before any write. The producer prefix is rebuilt per event.
	ld a, b
	cp AV_SWITCH_ACTION
	jr z, .kind_ok
	cp AV_WAIT_ACTION
	jp nz, .reject
.kind_ok
	ld [FPK_CURRENT], a
	ld a, c
	ld [FPK_INDEX], a
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	push de
	xor a
	ld [FPK_FLAGS], a
	ld [FPK_SECOND_EVENT], a
	ld hl, FPK_TOTAL
	ld b, 5
.clear
	ld [hli], a
	dec b
	jr nz, .clear
.event
	ld a, 1
	call BossAI_FastFallbackPair.Accuracy
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastFallbackPair.EventMass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	or b
	jp z, .next
	call BossAI_FastFallbackPair.Context
	ld a, [FPK_INDEX]
	ad_address AV_SLOT
	ld [hl], a
	ld a, [FPK_CURRENT]
	ad_address AV_KIND
	ld [hl], a
	ad_address AV_MOVE
	ld [hl], STRUGGLE
	ld a, FSR_MOVE
	call BossAI_FastFallbackPair.ReplyAddress
	ld a, [hl]
	ad_address AV_REPLY
	ld [hl], a
	ld a, [FPK_SECOND_EVENT]
	add a
	ad_address AV_BRANCH
	ld [hl], a
	farcall BossAI_ValuePublicExchangeFromContext
	xor a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld [FS_MULTIPLICAND + 2], a
	ld a, b
	ld [FS_MULTIPLICAND + 3], a
	ld a, c
	ld [FS_MULTIPLICAND + 4], a
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	xor a
	ld [FS_MULTIPLIER], a
	ld a, [FPK_REPLY_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_REPLY_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	farcall BossAI_FastMultiply40By24
	ld b, 9
.shift
	ld hl, FS_PRODUCT + 4
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
	ld hl, FS_PRODUCT + 4
	call BossAI_FastFallbackPair.AddTotal
.next
	ld hl, FPK_SECOND_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .event
	ld hl, FSC_BASELINE + 4
	ld de, FPK_TOTAL + 4
	ld b, 5
	and a
.subtract
	ld a, [de]
	sbc [hl]
	ld [de], a
	dec de
	dec hl
	dec b
	jr nz, .subtract
	pop de
	scf
	ret
.reject
	and a
	ret
