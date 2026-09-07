; Complete unweighted direct-reference pair fallback. Only the old producer
; prefix is mutable; no legacy JC or SRAM HP-table lifetime is entered.
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
.own_event
	xor a
	call BossAI_FastNormalizedPair.Accuracy
	ld a, [FPK_FIRST_EVENT]
	call BossAI_FastNormalizedPair.EventMass
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
	call BossAI_FastNormalizedPair.Accuracy
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastNormalizedPair.EventMass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	or b
	jp z, .next_reply
	xor a
	ld [FPK_CURRENT], a
	ld a, [FPK_ORDER]
	cp 2
	ld a, 1
	jr nz, .order_count
	inc a
.order_count
	ld [FPK_LEFT], a
.order
	call .EventContext
	farcall BossAI_ValuePublicExchangeFromContext
	ld a, b
	ld [FS_MULTIPLICAND + 3], a
	ld a, c
	ld [FS_MULTIPLICAND + 4], a
	xor a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld [FS_MULTIPLICAND + 2], a
	ld [FS_MULTIPLIER], a
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	ld a, [FPK_OWN_Z]
	ld [FS_MULTIPLIER + 1], a
	ld a, [FPK_OWN_Z + 1]
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
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
	call BossAI_FastMultiply40By24
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
	call BossAI_FastNormalizedPair.AddTotal
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
	call nz, BossAI_FastNormalizedPair.SubtractBaseline
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
	call BossAI_FastNormalizedPair.Context
	ld a, FSP_SLOT
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	ld a, FSP_MOVE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ad_address AV_MOVE
	ld [hl], a
	ad_address AV_KIND
	ld [hl], AV_MOVE_ACTION
	ld a, FSR_MOVE
	call BossAI_FastNormalizedPair.ReplyAddress
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

; Common-sum allocation after the pair total: $a578..$a58f.
DEF FSC_INCOMING EQU $a57d ; signed32 sum of weight*reply moment, current defender
DEF FSC_MASS EQU $a581 ; M=2*W_R for the whole decision
DEF FSC_ENTRY_DELTA EQU $a583 ; signed16 entry potential change, zero when active
DEF FSC_BASELINE EQU $a585 ; 2*65536*(1024+entry delta): the unary standalone baseline
DEF FSC_TEMP EQU $a58a ; five-byte accumulation temporary
ASSERT FPK_TOTAL + 5 == FSC_INCOMING
ASSERT FSC_TEMP + 5 <= $a590

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
	call BossAI_FastNormalizedPair.Accuracy
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastNormalizedPair.EventMass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	or b
	jr z, .next
	call BossAI_FastNormalizedPair.Context
	ld a, [FPK_INDEX]
	ad_address AV_SLOT
	ld [hl], a
	ld a, [FPK_CURRENT]
	ad_address AV_KIND
	ld [hl], a
	ad_address AV_MOVE
	ld [hl], STRUGGLE
	ld a, FSR_MOVE
	call BossAI_FastNormalizedPair.ReplyAddress
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
	call BossAI_FastMultiply40By24
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
	call BossAI_FastNormalizedPair.AddTotal
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
