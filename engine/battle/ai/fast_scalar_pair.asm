; Scalar pair corrections for plain families. No executor runs: the hit/hit
; terminal of each order is at most two potential lookups, and reached flags
; come from the compact records evaluated at the first action's successor.
; Eligible when the own plan is plain single-hit damage (descriptor effect 0,
; item 0) or recovery, and the reply is plain damage (no Helmet/drain/recoil)
; or recovery. Unsupported incoming amounts keep their conservative KO. Every
; other family stays with the sequential evaluator, whose semantics this
; mirrors field for field (see fast_plan_executor/fast_reply_executor).
DEF FSK_STATE EQU $a560 ; own HP, player HP after the first action
DEF FSK_NEXT EQU $a564 ; state after the second action
DEF FSK_EVENT EQU $a568 ; second action's original event during flag passes
DEF FSK_REGIME EQU $a569 ; regime index of the second action
DEF FSK_BIT EQU $a56a ; its bit
DEF FSK_FLAGS EQU $a56b ; flags reached by the second action
DEF FSK_UNION EQU $a56c ; flags of one order/event path
DEF FSR_STANDALONE_HIT_FLAGS EQU 24 ; reply record bytes filled by the selector
DEF FSR_STANDALONE_MISS_FLAGS EQU 25
ASSERT FSK_UNION < $a578

BossAI_FastScalarPair::
; C=owned plan0..3, A=order0..2, DE=context whose compact reply carries its
; standalone flags at FSR_BASE+24/25. Same outputs as
; BossAI_FastNormalizedPair.CorrectionOnly: FPK_TOTAL=z_own*z_reply*K in the
; signed40 ring and FPK_FLAGS. Carry=handled; clear=not eligible, in which
; case only pair scratch changed. DE/SP preserved.
	cp 3
	jp nc, .reject
	push af
	ld a, c
	cp 4
	jp nc, .reject_af
	pop af
	ld [FPK_ORDER], a
	ld a, c
	ld [FPK_INDEX], a
	ld a, d
	ld [FPK_CONTEXT], a
	ld a, e
	ld [FPK_CONTEXT + 1], a
	ld a, FSP_OPCODE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	cp FSP_RECOVERY
	jr z, .own_ok
	cp FSP_DAMAGE
	jp nz, .reject
	ld a, FSP_DESCRIPTOR
	call BossAI_FastNormalizedPair.OwnAddress
	call .PlainDescriptor
	jp nc, .reject
.own_ok
	ld a, FSR_OPCODE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	cp FSR_RECOVERY
	jr z, .reply_ok
	cp FSR_DAMAGE
	jp nz, .reject
	ld a, FSR_DESCRIPTOR
	call BossAI_FastNormalizedPair.ReplyAddress
	call .PlainDescriptor
	jp nc, .reject
.reply_ok
	push de
	ld a, 1
	ld [FPK_MODE], a
	xor a
	ld [FPK_K], a
	ld [FPK_K + 1], a
	ld [FPK_FLAGS], a
	ld a, [FPK_ORDER]
	cp 2
	jr nz, .masses
	ld a, 1 << AV_UNKNOWN_ORDER_F
	ld [FPK_FLAGS], a
.masses
	ld a, FSP_OPCODE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ld bc, 256
	cp FSP_RECOVERY
	jr z, .own_mass
	ld a, FSP_ACCURACY
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode
.own_mass
	ld a, b
	ld [FPK_OWN_Z], a
	ld a, c
	ld [FPK_OWN_Z + 1], a
	ld a, FSR_OPCODE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	ld bc, 256
	cp FSR_RECOVERY
	jr z, .reply_mass
	ld a, FSR_ACCURACY
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	call BossAI_FastNormalizedPair.Decode
.reply_mass
	ld a, b
	ld [FPK_REPLY_Z], a
	ld a, c
	ld [FPK_REPLY_Z + 1], a
	ld a, FSP_HIT_DELTA
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hli]
	ld [FPK_OWN_DELTA], a
	ld a, [hl]
	ld [FPK_OWN_DELTA + 1], a
	ld a, FSR_HIT_DELTA
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hli]
	ld [FPK_REPLY_DELTA], a
	ld a, [hl]
	ld [FPK_REPLY_DELTA + 1], a
	ld hl, FPK_OWN_Z
	ld a, [hli]
	or [hl]
	jr z, .flags
	inc hl
	ld a, [hli]
	or [hl]
	jr z, .flags
	ld a, [FPK_ORDER]
	cp 1
	jr z, .reply_first_order
	call .OwnFirst
	ld a, [FPK_ORDER]
	cp 2
	jr z, .own_first_add
	add hl, hl
.own_first_add
	call .AddK
	ld a, [FPK_ORDER]
	and a
	jr z, .flags
.reply_first_order
	call .ReplyFirst
	ld a, [FPK_ORDER]
	cp 2
	jr z, .reply_first_add
	add hl, hl
.reply_first_add
	call .AddK
.flags
	call .Flags
	call BossAI_FastNormalizedPair.Total
	pop de
	scf
	ret
.reject_af
	pop af
.reject
	and a
	ret

.PlainDescriptor
; HL=big-endian descriptor pointer field. Carry when effect and item tags are 0.
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, [hli]
	or [hl]
	ret nz
	scf
	ret
.AddK
; HL=signed order correction.
	ld a, [FPK_K + 1]
	add l
	ld [FPK_K + 1], a
	ld a, [FPK_K]
	adc h
	ld [FPK_K], a
	ret

.OwnFirst
; HL=K1: value of (own hit, then reply hit) minus both standalone deltas.
	ld a, FSP_HIT_HP
	call BossAI_FastNormalizedPair.OwnAddress
	call .LoadState
	jr c, .own_first_gated
	call .ApplyReply
	call .DeltaV
	jr .minus_reply_delta
.own_first_gated
	ld hl, 0
.minus_reply_delta
	ld a, [FPK_REPLY_DELTA + 1]
	ld c, a
	ld a, [FPK_REPLY_DELTA]
	ld b, a
	jr .SubtractWord
.ReplyFirst
; HL=K2: value of (reply hit, then own hit) minus both standalone deltas.
	ld a, FSR_HIT_HP
	call BossAI_FastNormalizedPair.ReplyAddress
	call .LoadState
	jr c, .reply_first_gated
	call .ApplyOwn
	call .DeltaV
	jr .minus_own_delta
.reply_first_gated
	ld hl, 0
.minus_own_delta
	ld a, [FPK_OWN_DELTA + 1]
	ld c, a
	ld a, [FPK_OWN_DELTA]
	ld b, a
.SubtractWord
; HL-=BC
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a
	ret

.LoadState
; HL=four-byte state. Copies it to FSK_STATE and FSK_NEXT; carry when either
; actor is fainted (the second action is gated).
	ld de, FSK_STATE
	ld b, 4
.load_state_byte
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .load_state_byte
	ld hl, FSK_STATE
	ld de, FSK_NEXT
	ld b, 4
.copy_state_byte
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_state_byte
	ld hl, FSK_STATE
	ld a, [hli]
	or [hl]
	jr z, .gated
	inc hl
	ld a, [hli]
	or [hl]
	jr z, .gated
	and a
	ret
.gated
	scf
	ret

.ApplyReply
; FSK_NEXT: the reply's hit transition from FSK_STATE (both living).
	ld a, FSR_CAN_ACT
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	and a
	ret z
	ld a, FSR_OPCODE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	cp FSR_RECOVERY
	jr nz, .reply_damage
	ld a, FSR_RECOVERY_QUOTA
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_PLAYER + 2]
	ld d, a
	ld a, [FSA_PLAYER + 3]
	ld e, a
	ld hl, FSK_NEXT + 2
	jp BossAI_FastGainHP
.reply_damage
	call .IncomingRegime
	ld a, FSR_SUPPORT
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [FSK_BIT]
	and [hl]
	jr z, .reply_unsupported
	ld a, [FSK_REGIME]
	add a
	add FSR_RAW_MAX
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld hl, FSK_NEXT
	jp BossAI_FastLoseHP
.reply_unsupported
	ld a, FSR_POWER
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	and a
	ret z
	xor a
	ld [FSK_NEXT], a
	ld [FSK_NEXT + 1], a
	ret
.ApplyOwn
; FSK_NEXT: the own plan's hit transition from FSK_STATE (both living).
	ld a, FSP_CAN_ACT
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	and a
	ret z
	ld a, FSP_OPCODE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	cp FSP_RECOVERY
	jr nz, .own_damage
	ld a, FSP_RECOVERY_QUOTA
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_MAX_HP]
	ld d, a
	ld a, [FSA_MAX_HP + 1]
	ld e, a
	ld hl, FSK_NEXT
	jp BossAI_FastGainHP
.own_damage
	call .OutgoingRegime
	ld a, FSP_SUPPORT
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [FSK_BIT]
	and [hl]
	ret z ; unsupported own amount: no HP change, flag only
	ld a, [FSK_REGIME]
	add a
	add FSP_RAW_MIN
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld hl, FSK_NEXT + 2
	jp BossAI_FastLoseHP

.IncomingRegime
; From FSK_STATE, the player's attack regime (attacker-low 3*player<max,
; defender-high 2*own>max) in the executor's wrapped 16-bit arithmetic.
; Stores FSK_REGIME/FSK_BIT. AF/BC/DE/HL scratch.
	ld hl, FSK_STATE + 2
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	ld a, [FSA_PLAYER + 3]
	ld e, a
	ld a, [FSA_PLAYER + 2]
	ld d, a
	ld a, l
	sub e
	ld a, h
	sbc d
	ld a, 0
	adc 0
	ld e, a
	ld hl, FSK_STATE
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ld a, [FSA_MAX_HP]
	cp b
	jr c, .incoming_high
	jr nz, .StoreRegime
	ld a, [FSA_MAX_HP + 1]
	cp c
	jr nc, .StoreRegime
.incoming_high
	set 1, e
	jr .StoreRegime
.OutgoingRegime
; From FSK_STATE, the own attack regime (attacker-low 3*own<max,
; defender-high 2*player>max).
	ld hl, FSK_STATE
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
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
	ld hl, FSK_STATE + 2
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ld a, [FSA_PLAYER + 2]
	cp b
	jr c, .outgoing_high
	jr nz, .StoreRegime
	ld a, [FSA_PLAYER + 3]
	cp c
	jr nc, .StoreRegime
.outgoing_high
	set 1, e
.StoreRegime
	ld a, e
	ld [FSK_REGIME], a
	ld d, 0
	ld hl, .Bits
	add hl, de
	ld a, [hl]
	ld [FSK_BIT], a
	ret
.Bits
	db 1, 2, 4, 8

.DeltaV
; HL=V(FSK_NEXT)-V(FSK_STATE): own potential change minus the player's.
	ld hl, 0
	push hl
	ld hl, FSK_STATE
	ld de, FSK_NEXT
	call .SameWord
	jr z, .own_same
	ld hl, FSK_NEXT
	call .OwnPhi
	push bc
	ld hl, FSK_STATE
	call .OwnPhi
	pop hl
	call .SubtractWord
	pop bc
	add hl, bc
	push hl
.own_same
	ld hl, FSK_STATE + 2
	ld de, FSK_NEXT + 2
	call .SameWord
	jr z, .player_same
	ld hl, FSK_STATE + 2
	call .PlayerPhi
	push bc
	ld hl, FSK_NEXT + 2
	call .PlayerPhi
	pop hl
	call .SubtractWord
	pop bc
	add hl, bc
	push hl
.player_same
	pop hl
	ret
.SameWord
; Z when the words at HL and DE are equal.
	ld a, [de]
	cp [hl]
	ret nz
	inc de
	inc hl
	ld a, [de]
	cp [hl]
	ret
.OwnPhi
; HL=HP word. BC=Phi with the own table/weight/mode.
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_HP_MODE]
	ld d, a
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	jp BossAI_FastHPPotential
.PlayerPhi
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_PLAYER + 37]
	ld d, a
	ld a, 128
	ld hl, $a180
	jp BossAI_FastHPPotential

.Flags
; Union of reached flags over every positive original-mass event path and
; every modeled order, into FPK_FLAGS.
	xor a
	ld [FPK_FIRST_EVENT], a
.own_event
	xor a
	call BossAI_FastNormalizedPair.Accuracy
	ld a, [FPK_FIRST_EVENT]
	call BossAI_FastNormalizedPair.EventMass
	ld a, b
	or c
	jp z, .next_own_event
	xor a
	ld [FPK_SECOND_EVENT], a
.reply_event
	ld a, 1
	call BossAI_FastNormalizedPair.Accuracy
	ld a, [FPK_SECOND_EVENT]
	call BossAI_FastNormalizedPair.EventMass
	ld a, b
	or c
	jr z, .next_reply_event
	ld a, [FPK_ORDER]
	cp 1
	jr z, .flags_reply_first
; own first: own standalone flags, then the reply at the own successor
	ld a, [FPK_FIRST_EVENT]
	add FSP_STANDALONE_HIT_FLAGS
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ld [FSK_UNION], a
	ld a, [FPK_FIRST_EVENT]
	add a
	add a
	add FSP_HIT_HP
	call BossAI_FastNormalizedPair.OwnAddress
	call .LoadState
	jr c, .own_first_flags_done
	ld a, [FPK_SECOND_EVENT]
	ld [FSK_EVENT], a
	call .ReplyFlagsAt
	ld hl, FSK_UNION
	or [hl]
	ld [hl], a
.own_first_flags_done
	ld a, [FSK_UNION]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
	ld a, [FPK_ORDER]
	and a
	jr z, .next_reply_event
.flags_reply_first
	ld a, [FPK_SECOND_EVENT]
	add FSR_STANDALONE_HIT_FLAGS
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	ld [FSK_UNION], a
	ld a, [FPK_SECOND_EVENT]
	add a
	add a
	add FSR_HIT_HP
	call BossAI_FastNormalizedPair.ReplyAddress
	call .LoadState
	jr c, .reply_first_flags_done
	ld a, [FPK_FIRST_EVENT]
	ld [FSK_EVENT], a
	call .OwnFlagsAt
	ld hl, FSK_UNION
	or [hl]
	ld [hl], a
.reply_first_flags_done
	ld a, [FSK_UNION]
	ld hl, FPK_FLAGS
	or [hl]
	ld [hl], a
.next_reply_event
	ld hl, FPK_SECOND_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .reply_event
.next_own_event
	ld hl, FPK_FIRST_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .own_event
	ret

.ReplyFlagsAt
; A=flags the reply reaches from FSK_STATE (both living) at event FSK_EVENT,
; mirroring BossAI_FastExecuteReplyPlan's gates.
	ld a, FSR_CHECK_FLAGS
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	ld [FSK_FLAGS], a
	ld a, FSR_CAN_ACT
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	and a
	jr z, .reply_flags_done
	ld a, FSR_OPCODE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	cp FSR_RECOVERY
	jr nz, .reply_damage_flags
	ld a, FSR_RECOVERY_QUOTA
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hli]
	or [hl]
	jr z, .reply_flags_done
	ld hl, FSK_STATE + 2
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, [FSA_PLAYER + 3]
	ld c, a
	ld a, [FSA_PLAYER + 2]
	call .BelowMaximum
	jr nc, .reply_flags_done
	ld a, FSR_MOVE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	cp REST
	jr nz, .reply_flags_done
	ld a, [FSK_FLAGS]
	or 1 << AV_UNKNOWN_TRANSITION_F
	ld [FSK_FLAGS], a
	jr .reply_flags_done
.reply_damage_flags
	ld a, FSR_DAMAGE_FLAGS
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	ld hl, FSK_FLAGS
	or [hl]
	ld [hl], a
	ld a, [FSK_EVENT]
	and a
	jr nz, .reply_flags_done
	ld a, FSR_ACCURACY
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [hl]
	and a
	jr z, .reply_flags_done
	call .IncomingRegime
	ld a, FSR_RANGE
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [FSK_BIT]
	and [hl]
	jr z, .reply_support_flag
	ld a, [FSK_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSK_FLAGS], a
.reply_support_flag
	ld a, FSR_SUPPORT
	call BossAI_FastNormalizedPair.ReplyAddress
	ld a, [FSK_BIT]
	and [hl]
	jr nz, .reply_flags_done
	ld a, [FSK_FLAGS]
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld [FSK_FLAGS], a
.reply_flags_done
	ld a, [FSK_FLAGS]
	ret

.OwnFlagsAt
; A=flags the own plan reaches from FSK_STATE (both living) at event
; FSK_EVENT, mirroring BossAI_FastExecuteOwnedPlan's gates.
	ld a, FSP_CHECK_FLAGS
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ld [FSK_FLAGS], a
	ld a, FSP_CAN_ACT
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	and a
	jr z, .own_flags_done
	ld a, FSP_OPCODE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	cp FSP_RECOVERY
	jr nz, .own_damage_flags
	ld a, FSP_RECOVERY_QUOTA
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hli]
	or [hl]
	jr z, .own_flags_done
	ld hl, FSK_STATE
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, [FSA_MAX_HP + 1]
	ld c, a
	ld a, [FSA_MAX_HP]
	call .BelowMaximum
	jr nc, .own_flags_done
	ld a, FSP_MOVE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	cp REST
	jr nz, .own_flags_done
	ld a, [FSK_FLAGS]
	or 1 << AV_UNKNOWN_TRANSITION_F
	ld [FSK_FLAGS], a
	jr .own_flags_done
.own_damage_flags
	ld a, FSP_DAMAGE_FLAGS
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	ld hl, FSK_FLAGS
	or [hl]
	ld [hl], a
	ld a, [FSK_EVENT]
	and a
	jr nz, .own_flags_done
	ld a, FSP_ACCURACY
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [hl]
	and a
	jr z, .own_flags_done
	call .OutgoingRegime
	ld a, FSP_RANGE
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [FSK_BIT]
	and [hl]
	jr z, .own_support_flag
	ld a, [FSK_FLAGS]
	or 1 << AV_AMOUNT_RANGE_F
	ld [FSK_FLAGS], a
.own_support_flag
	ld a, FSP_SUPPORT
	call BossAI_FastNormalizedPair.OwnAddress
	ld a, [FSK_BIT]
	and [hl]
	jr nz, .own_flags_done
	ld a, [FSK_FLAGS]
	or 1 << AV_UNKNOWN_DAMAGE_F
	ld [FSK_FLAGS], a
.own_flags_done
	ld a, [FSK_FLAGS]
	ret
.BelowMaximum
; HL=HP, A/C=maximum high/low. Carry when HP<maximum.
	ld d, a
	ld a, l
	sub c
	ld a, h
	sbc d
	ret
