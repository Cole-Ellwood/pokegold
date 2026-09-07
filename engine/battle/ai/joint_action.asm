; Joint move/switch/replacement comparison over the complete public reply set.
; This draft matrix averages accuracy outcomes and modeled speed ties; other
; event branches remain conditional on the exchange model's base event branch.
; It exposes uncertainty per action and is not yet a production selector.

DEF JC_ACTIONS EQU AV_PREPARED_CONTEXT_SIZE
DEF JC_REPLIES EQU JC_ACTIONS + AC_CONTEXT_SIZE
DEF JC_SCORES EQU JC_REPLIES + PR_CONTEXT_SIZE
DEF JC_RECORD_SIZE EQU 3 ; BE utility word, uncertainty byte; $ffff=not an action
DEF JC_NUM_ACTIONS EQU NUM_MOVES + PARTY_LENGTH + 2
DEF JC_KIND EQU JC_SCORES + JC_NUM_ACTIONS * JC_RECORD_SIZE
DEF JC_SCAN EQU JC_KIND + 1 ; bits0..3 reverse actions/replies/tie orders/hit events
DEF JC_INDEX EQU JC_SCAN + 1
DEF JC_LEFT EQU JC_INDEX + 1
DEF JC_REPLY EQU JC_LEFT + 1
DEF JC_REPLY_LEFT EQU JC_REPLY + 1
DEF JC_TOTAL EQU JC_REPLY_LEFT + 1 ; 40-bit sum, with 16 fractional event bits
DEF JC_MASS EQU JC_TOTAL + 5 ; 16-bit reply/order mass; /65536 is implicit
DEF JC_WEIGHT EQU JC_MASS + 2
DEF JC_OWN_ACCURACY EQU JC_WEIGHT + 1
DEF JC_REPLY_ACCURACY EQU JC_OWN_ACCURACY + 1
DEF JC_EVENT EQU JC_REPLY_ACCURACY + 1
DEF JC_UNCERTAIN EQU JC_EVENT + 1
DEF JC_BEST EQU JC_UNCERTAIN + 1
DEF JC_BEST_INDEX EQU JC_BEST + 2
DEF JC_USE_SRAM EQU JC_BEST_INDEX + 1
DEF JC_CONTEXT_SIZE EQU JC_USE_SRAM + 1
DEF JC_REVEALED_WEIGHT EQU 8
DEF JC_PUBLIC_PRIOR_F EQU 5
ASSERT JC_CONTEXT_SIZE - JC_ACTIONS < 256 ; byte-counted metadata clear only
ASSERT JC_CONTEXT_SIZE <= wBattle - wBattleAnimTileDict
; Conservative bound even if every reply received the revealed weight.
; Both tie branches together have the same doubled mass as a non-tied reply.
; Multiplying the second bound by 65536 fits the five-byte event numerator.
ASSERT 2 * NUM_ATTACKS * JC_REVEALED_WEIGHT < $10000
ASSERT 2048 * 2 * NUM_ATTACKS * JC_REVEALED_WEIGHT < $1000000

; ai-layer: POLICY
BossAI_ComparePublicActionsWithTables::
; Same result as the reference entry below. SRAM MUST be closed on entry;
; all graphics transfers must have completed. No graphics/menu/RTC callbacks
; may run during this synchronous evaluation. SRAM is closed on every return.
; B bit4 disables first-action reuse for attribution benchmarks only.
	push af
	xor a
	call OpenSRAM
	pop af
	ld c, 3
	bit 4, b
	jr z, .mode_ready
	ld c, 1
.mode_ready
	call BossAI_ComparePublicActions.with_mode
	push af
	push hl
	ad_address AV_PREPARED_DAMAGE
	res AV_PREPARED_HP_F, [hl]
	pop hl
	pop af
	jp CloseSRAM

; ai-layer: POLICY
BossAI_ComparePublicActions::
; DE=JC_CONTEXT_SIZE caller-owned bytes. A=decision kind (0 or replacement 2),
; B=traversal flags. All traversal orders produce the same indexed score vector.
; Action indices: 0..3 exact active PP slots; 4..9 owned party entries;
; 10 forced selected move; 11 forced wait. Invalid entries have utility $ffff.
; BC=best conditional utility; JC_BEST_INDEX identifies it ($ff if none).
; Carry only means at least one legal action exists, NOT a reliable prediction.
; Revealed replies have weight 8, natural priors weight 1. These are explicit
; policy priors awaiting battle validation, not facts about the player's choice.
; Uncertainty is ORed across replies; bit5 additionally marks an open moveset.
; Equal-priority modeled speed ties average both orders at equal event mass.
; Both actors' hit/miss outcomes use exact /256 public accuracy weights.
; Other probability branches, successor state/future offense and promotion
; remain pending.
	ld c, 0
.with_mode
	push af
	push bc
	ad_address JC_ACTIONS
	ld b, JC_CONTEXT_SIZE - JC_ACTIONS
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	pop bc
	pop af
	ad_address JC_USE_SRAM
	ld [hl], c
	ad_address JC_KIND
	ld [hli], a
	ld [hl], b
	push af
	ad_address JC_SCORES
	ld b, JC_NUM_ACTIONS * JC_RECORD_SIZE
	ld a, $ff
.invalid
	ld [hli], a
	dec b
	jr nz, .invalid
	ad_address JC_BEST_INDEX
	ld [hl], a
	pop af
	push de
	ad_address JC_ACTIONS
	ld d, h
	ld e, l
	call BossAI_EnumeratePublicActions
	pop de
	push de
	ad_address JC_REPLIES
	ld d, h
	ld e, l
	call BossAI_BuildPublicReplySet
	pop de
	ad_address JC_SCAN
	bit 0, [hl]
	ld a, 0
	jr z, .first_action
	ld a, JC_NUM_ACTIONS - 1
.first_action
	ad_address JC_INDEX
	ld [hli], a
	ld [hl], JC_NUM_ACTIONS
.action
	call .Candidate
	jr nc, .next_action
	call .ValueCandidate
	call .StoreScore
	call .ChooseBest
.next_action
	ad_address JC_LEFT
	dec [hl]
	jr z, .done
	ad_address JC_SCAN
	bit 0, [hl]
	ad_address JC_INDEX
	jr nz, .previous_action
	inc [hl]
	jr .action
.previous_action
	dec [hl]
	jr .action
.done
	av_load_word JC_BEST
	ad_address JC_BEST_INDEX
	ld a, [hl]
	cp $ff
	jr z, .no_candidate
	scf
	ret
.no_candidate
	and a
	ret

.Candidate
	ad_address JC_INDEX
	ld a, [hl]
	cp NUM_MOVES
	jr nc, .not_move
	ld c, a
	ld b, 0
	ad_address JC_ACTIONS + AC_MOVES
	add hl, bc
	ld a, [hl]
	and a
	ret z
	ld c, a
	ld b, AV_MOVE_ACTION
	ld a, $ff
	jp .StoreAction
.not_move
	cp NUM_MOVES + PARTY_LENGTH
	jr nc, .forced
	sub NUM_MOVES
	ld c, a
	ld a, 1
	inc c
.switch_bit
	dec c
	jr z, .test_switch
	add a
	jr .switch_bit
.test_switch
	ad_address JC_ACTIONS + AC_SWITCH_MASK
	and [hl]
	ret z
	ad_address JC_KIND
	ld a, [hl]
	cp AV_REPLACEMENT_ACTION
	ld b, AV_SWITCH_ACTION
	jr nz, .switch_kind
	ld b, AV_REPLACEMENT_ACTION
.switch_kind
	ad_address JC_INDEX
	ld a, [hl]
	sub NUM_MOVES
	ld c, STRUGGLE ; actor-fact carrier, never executed on entry
	jp .StoreAction
.forced
	cp NUM_MOVES + PARTY_LENGTH
	jr nz, .wait
	ad_address JC_ACTIONS + AC_MODE
	ld a, [hl]
	cp AC_FORCED
	jr nz, .no_candidate
	ad_address JC_ACTIONS + AC_FORCED_MOVE
	ld c, [hl]
	ld a, c
	and a
	jr z, .forced_wait
	cp CANNOT_MOVE
	jr z, .forced_wait
	ld a, [wEnemySubStatus4]
	bit SUBSTATUS_RECHARGE, a
	jr nz, .forced_wait
	call .ForcedCanExecute
	jr nc, .forced_wait
	ld b, AV_MOVE_ACTION
	ld a, $ff
	jr .StoreAction
.wait
	ad_address JC_ACTIONS + AC_MODE
	ld a, [hl]
	cp AC_WAIT
	jp nz, .no_candidate
.forced_wait
	ld b, AV_WAIT_ACTION
	ld c, STRUGGLE
	ld a, $ff
.StoreAction
	ad_address AV_SLOT
	ld [hl], a
	ad_address AV_KIND
	ld [hl], b
	ad_address AV_MOVE
	ld [hl], c
	ad_address AV_BRANCH
	ld [hl], 0
	scf
	ret

.ForcedCanExecute
; Selected Encore actions may fail despite being forced. CheckEnemyTurn ages
; Disable before testing the move, and DoTurn checks the exact selected PP slot.
; C=selected move, preserved. Carry means these checks do not deny execution;
; status and unsupported charged/continuous effects remain exchange concerns.
	ld a, [wEnemyDisabledMove]
	and a
	jr z, .forced_pp
	cp c
	jr nz, .forced_pp
	ld a, [wEnemyDisableCount]
	and a
	ret z
	dec a
	and $f
	jr nz, .forced_denied
.forced_pp
	ld a, c
	cp STRUGGLE
	jr z, .forced_allowed
	ld a, [wEnemySubStatus3]
	and 1 << SUBSTATUS_IN_LOOP | 1 << SUBSTATUS_RAMPAGE | 1 << SUBSTATUS_BIDE | 1 << SUBSTATUS_CHARGED
	jr nz, .forced_allowed
	push bc
	ad_address JC_ACTIONS + AC_FORCED_SLOT
	ld a, [hl]
	cp NUM_MOVES
	jr nc, .forced_bad_slot
	ld c, a
	ld b, 0
	ld hl, wEnemyMonPP
	add hl, bc
	ld a, [hl]
	and PP_MASK
	pop bc
	jr nz, .forced_allowed
.forced_denied
	and a
	ret
.forced_bad_slot
	pop bc
	jr .forced_denied
.forced_allowed
	scf
	ret

.ValueCandidate
	farcall BossAI_PreparePublicAction
	ad_address JC_USE_SRAM
	ld a, [hl]
	and a
	jr z, .no_hp_tables
	farcall BossAI_PrepareHPValues
	ad_address JC_USE_SRAM
	bit 1, [hl]
	jr z, .no_hp_tables
	farcall BossAI_PrepareFirstActionStates
.no_hp_tables
	ad_address JC_TOTAL
	ld b, JC_UNCERTAIN - JC_TOTAL + 1
	xor a
.clear_sum
	ld [hli], a
	dec b
	jr nz, .clear_sum
	ad_address AV_KIND
	ld a, [hl]
	cp AV_REPLACEMENT_ACTION
	jr nz, .reply_scan
; Entry after a faint does not give the opponent a third action.
	ad_address AV_REPLY
	ld [hl], 0
	ad_address JC_WEIGHT
	ld [hl], 1
	call .EvaluateReply
	jp .Mean
.reply_scan
	ad_address JC_REPLIES + PR_FLAGS
	bit PR_FOUR_REVEALED_F, [hl]
	jr nz, .reply_order
	ad_address JC_UNCERTAIN
	set JC_PUBLIC_PRIOR_F, [hl]
.reply_order
	ad_address JC_SCAN
	bit 1, [hl]
	ld a, 1
	jr z, .first_reply
	ld a, NUM_ATTACKS
.first_reply
	ad_address JC_REPLY
	ld [hli], a
	ld [hl], NUM_ATTACKS
.reply
	ad_address JC_REPLY
	ld a, [hl]
	ld bc, JC_REPLIES + PR_POSSIBLE
	call .TestReplyBit
	jr z, .next_reply
	ad_address JC_REPLY
	ld a, [hl]
	ad_address AV_REPLY
	ld [hl], a
	ld bc, JC_REPLIES + PR_REVEALED
	call .TestReplyBit
	ld a, 1
	jr z, .weight
	ld a, JC_REVEALED_WEIGHT
.weight
	ad_address JC_WEIGHT
	ld [hl], a
	call .EvaluateReply
.next_reply
	ad_address JC_REPLY_LEFT
	dec [hl]
	jp z, .Mean
	ad_address JC_SCAN
	bit 1, [hl]
	ad_address JC_REPLY
	jr nz, .previous_reply
	inc [hl]
	jr .reply
.previous_reply
	dec [hl]
	jr .reply

.EvaluateReply
	farcall BossAI_PreparePublicReply
	farcall BossAI_PreparedExchangeAccuracy
	ad_address JC_OWN_ACCURACY
	ld [hl], b
	inc hl
	ld [hl], c
; Sum of all hit/miss and order weights is always 2 * reply_weight * 65536.
; Store the integer mass once; the common 65536 factor is removed only by Mean.
	ad_address JC_WEIGHT
	ld a, [hl]
	add a
	ld c, a
	ad_address JC_MASS + 1
	ld a, [hl]
	add c
	ld [hld], a
	ld a, [hl]
	adc 0
	ld [hl], a
	ad_address JC_SCAN
	bit 3, [hl]
	ld a, 0
	jr z, .first_event
	ld a, 3
.first_event
	ad_address JC_EVENT
	ld [hl], a
.event
	ad_address JC_EVENT
	ld c, [hl]
	ad_address AV_BRANCH
	ld a, [hl]
	and $fc
	or c
	ld [hl], a
	call .OwnProbability
	ld a, b
	or c
	jr z, .next_event
	call .ReplyProbability
	ld a, b
	or c
	jr z, .next_event
	call .EvaluateOrders
.next_event
	ad_address JC_SCAN
	bit 3, [hl]
	ad_address JC_EVENT
	jr nz, .previous_event
	inc [hl]
	ld a, [hl]
	cp 4
	jr c, .event
	jr .events_done
.previous_event
	ld a, [hl]
	and a
	jr z, .events_done
	dec [hl]
	jr .event
.events_done
	ad_address AV_BRANCH
	res 0, [hl]
	res 1, [hl]
	ret

.EvaluateOrders
	farcall BossAI_PreparedActionHasSpeedTie
	jr nc, .single_order
	ad_address AV_BRANCH
	set 2, [hl]
	res 3, [hl]
	ad_address JC_SCAN
	bit 2, [hl]
	jr z, .first_tie_order
	ad_address AV_BRANCH
	set 3, [hl]
.first_tie_order
	call .EvaluateBranch
	ad_address AV_BRANCH
	ld a, [hl]
	xor 1 << 3
	ld [hl], a
	call .EvaluateBranch
	ad_address AV_BRANCH
	res 2, [hl]
	res 3, [hl]
	ret
.single_order
; Every reply has equal total event mass, whether evaluated once or twice.
	ad_address JC_WEIGHT
	sla [hl]
	call .EvaluateBranch
	ad_address JC_WEIGHT
	srl [hl]
	ret
.EvaluateBranch
	farcall BossAI_ValuePreparedPublicExchange
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ad_address JC_UNCERTAIN
	or [hl]
	ld [hl], a
; Multiply utility by reply/order weight first, then both event probabilities.
; Each Multiply input fits its low 24-bit contract; the final product fits 32.
	xor a
	ldh [hMultiplicand], a
	ld a, b
	ldh [hMultiplicand + 1], a
	ld a, c
	ldh [hMultiplicand + 2], a
	ad_address JC_WEIGHT
	ld a, [hl]
	ldh [hMultiplier], a
	call Multiply
	call .OwnProbability
	call .ScaleProbability
	call .ReplyProbability
	call .ScaleProbability
	ad_address JC_TOTAL + 4
	ldh a, [hProduct + 3]
	add [hl]
	ld [hld], a
	ldh a, [hProduct + 2]
	adc [hl]
	ld [hld], a
	ldh a, [hProduct + 1]
	adc [hl]
	ld [hld], a
	ldh a, [hProduct]
	adc [hl]
	ld [hld], a
	ld a, [hl]
	adc 0
	ld [hl], a
	ret

.OwnProbability
	ad_address JC_OWN_ACCURACY
	ld a, [hl]
	call .DecodeAccuracy
	ad_address AV_BRANCH
	bit 0, [hl]
	ret z
	jr .ComplementProbability
.ReplyProbability
	ad_address JC_REPLY_ACCURACY
	ld a, [hl]
	call .DecodeAccuracy
	ad_address AV_BRANCH
	bit 1, [hl]
	ret z
.ComplementProbability
	xor a
	sub c
	ld c, a
	ld a, 1
	sbc b
	ld b, a
	ret
.DecodeAccuracy
	ld b, 0
	ld c, a
	cp 255
	ret nz
	inc b
	inc c
	ret
.ScaleProbability
; BC=0..256, hProduct has a low-24-bit input. Result is full 32-bit product.
	ld a, b
	and a
	jr nz, .probability_256
	ld a, c
	ldh [hMultiplier], a
	jp Multiply
.probability_256
	ldh a, [hProduct + 1]
	ldh [hProduct], a
	ldh a, [hProduct + 2]
	ldh [hProduct + 1], a
	ldh a, [hProduct + 3]
	ldh [hProduct + 2], a
	xor a
	ldh [hProduct + 3], a
	ret

.Mean
; Exact floor(T / (65536 * M)) = floor((T >> 16) / M). Drop only the final
; accumulated fractional bytes, never a per-event or per-reply fraction.
; Utility bounds repeated subtraction independently of the number of replies.
	push de
	av_load_word JC_MASS
	push bc
	ad_address JC_TOTAL
	ld a, [hli]
	ldh [hDividend], a
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld h, b
	ld l, c
	pop de
	ld bc, 0
	ld a, d
	or e
	jr z, .mean_done
.divide
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	ldh a, [hDividend]
	sbc 0
	jr c, .mean_done
	ldh [hDividend], a
	inc bc
	jr .divide
.mean_done
	pop de
	ret

.StoreScore
	push bc
	ad_address JC_INDEX
	ld a, [hl]
	ld c, a
	add a
	add c
	ld c, a
	ld b, 0
	ad_address JC_SCORES
	add hl, bc
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	ad_address JC_UNCERTAIN
	ld a, [hl]
	pop hl
	ld [hl], a
	ret

.ChooseBest
	push bc
	av_load_word JC_BEST
	pop hl
	ld a, h
	cp b
	ret c
	jr nz, .better
	ld a, l
	cp c
	ret c
	jr nz, .better
; Stable action identity breaks exact ties, never traversal order.
	ad_address JC_INDEX
	ld a, [hl]
	ad_address JC_BEST_INDEX
	cp [hl]
	ret nc
	ld [hl], a
	ret
.better
	ld b, h
	ld c, l
	av_store_word JC_BEST
	ad_address JC_INDEX
	ld a, [hl]
	ad_address JC_BEST_INDEX
	ld [hl], a
	ret

.TestReplyBit
; A=move ID, BC=set offset in the joint context. Z means absent.
	ld h, d
	ld l, e
	add hl, bc
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
	ld a, 1
	jr z, .test_bit
.bit_shift
	add a
	dec c
	jr nz, .bit_shift
.test_bit
	and [hl]
	ret
