; One public exchange on a shared material/HP scale. The caller enumerates
; actions and replies; this routine neither nominates candidates nor rolls RNG.
; Intermediate stage-2 implementation: uncertainty is returned explicitly.

DEF AV_KIND EQU AD_CONTEXT_SIZE
DEF AV_SLOT EQU AV_KIND + 1
DEF AV_MOVE EQU AV_SLOT + 1
DEF AV_REPLY EQU AV_MOVE + 1
DEF AV_OWN_START EQU AV_REPLY + 1
DEF AV_OWN_HP EQU AV_OWN_START + 2
DEF AV_OWN_MAX EQU AV_OWN_HP + 2
DEF AV_PLAYER_START EQU AV_OWN_MAX + 2
DEF AV_PLAYER_HP EQU AV_PLAYER_START + 2
DEF AV_PLAYER_MAX EQU AV_PLAYER_HP + 2
DEF AV_OWN_SPEED EQU AV_PLAYER_MAX + 2
DEF AV_PLAYER_SPEED EQU AV_OWN_SPEED + 2
DEF AV_PRIORITY EQU AV_PLAYER_SPEED + 2
DEF AV_UNCERTAIN EQU AV_PRIORITY + 1
DEF AV_RAW EQU AV_UNCERTAIN + 1
DEF AV_DAMAGE EQU AV_RAW + 2
DEF AV_WEIGHT EQU AV_DAMAGE + 2
DEF AV_VALUE EQU AV_WEIGHT + 1
DEF AV_BRANCH EQU AV_VALUE + 2
; Sparse defensive successor overrides: axis (0 unchanged, 1 Def, 4 SpDef),
; stage and effective stat word. Each actor executes at most one move here.
DEF AV_OWN_DEFENSE EQU AV_BRANCH + 1
DEF AV_PLAYER_DEFENSE EQU AV_OWN_DEFENSE + 4
DEF AV_CONTEXT_SIZE EQU AV_PLAYER_DEFENSE + 4
ASSERT AV_CONTEXT_SIZE < 128

; Optional immutable outgoing template, valid only while the live input state
; remains unchanged. Direct/FromContext callers still need only AV_CONTEXT_SIZE.
DEF AV_PREPARED_OUT EQU AV_CONTEXT_SIZE
DEF AV_PREPARED_DAMAGE EQU AV_PREPARED_OUT + AD_CONTEXT_SIZE
DEF AV_PREPARED_IN EQU AV_PREPARED_DAMAGE + 1
DEF AV_PREPARED_IN_DAMAGE EQU AV_PREPARED_IN + AD_CONTEXT_SIZE
DEF AV_PREPARED_ACTOR EQU AV_PREPARED_IN_DAMAGE + 1
DEF AV_PREPARED_STATS EQU AV_PREPARED_ACTOR + AD_CONTEXT_SIZE
DEF AV_FIRST_STATE_SIZE EQU 13 ; own HP, player HP, own defense, raw/damage, flags
DEF AV_FIRST_MIN EQU AV_PREPARED_STATS + 8
DEF AV_FIRST_MAX EQU AV_FIRST_MIN + AV_FIRST_STATE_SIZE
DEF AV_FIRST_MISS EQU AV_FIRST_MAX + AV_FIRST_STATE_SIZE
DEF AV_ACCURACY_COUNT EQU AV_FIRST_MISS + AV_FIRST_STATE_SIZE
DEF AV_ACCURACY_CACHE EQU AV_ACCURACY_COUNT + 1
DEF AV_ACCURACY_ENTRIES EQU 16
DEF AV_PREPARED_CONTEXT_SIZE EQU AV_ACCURACY_CACHE + 2 * AV_ACCURACY_ENTRIES
DEF AV_PREPARED_IN_F EQU 1 ; bit in AV_PREPARED_DAMAGE, keyed by incoming AD_MOVE
DEF AV_PREPARED_HP_F EQU 2 ; valid only during the exclusive SRAM wrapper lifetime
DEF AV_PREPARED_FIRST_F EQU 6 ; lazy owned first-action state cache enabled
DEF AV_FIRST_MIN_F EQU 3
DEF AV_FIRST_MAX_F EQU 4
DEF AV_FIRST_MISS_F EQU 5
ASSERT HIGH(sBossAIOwnHPValues) != HIGH(sBossAIPlayerHPValues)
DEF AV_PREPARED_SPEED_UNKNOWN_F EQU 6
DEF AV_PREPARED_F EQU 7

DEF AV_MOVE_ACTION EQU 0
DEF AV_SWITCH_ACTION EQU 1
DEF AV_REPLACEMENT_ACTION EQU 2
DEF AV_WAIT_ACTION EQU 3
DEF AV_UNKNOWN_DAMAGE_F EQU 0
DEF AV_UNKNOWN_HIT_F EQU 1
DEF AV_UNKNOWN_ORDER_F EQU 2
DEF AV_UNKNOWN_TRANSITION_F EQU 3
DEF AV_AMOUNT_RANGE_F EQU 4

MACRO av_load_word
	ad_address \1
	ld a, [hli]
	ld b, a
	ld c, [hl]
ENDM
MACRO av_store_word
	ad_address \1
	ld [hl], b
	inc hl
	ld [hl], c
ENDM
MACRO av_copy_word
	av_load_word \1
	av_store_word \2
ENDM

; ai-layer: POLICY
BossAI_PreparedExchangeAccuracy::
; DE=prepared context; B=own and C=reply accuracy bytes (255 means 256/256).
; Accuracy is HP-independent in this frozen-state conditional model. Incoming
; construction may replace AD scratch, but leaves prepared/AV fields intact.
; Absent actions get certain latent hits, so they need no duplicate branches.
	ad_address AV_KIND
	ld a, [hl]
	and a
	ld a, 255
	jr nz, .own_accuracy
	ad_address AV_PREPARED_OUT + AD_ACCURACY
	ld a, [hl]
.own_accuracy
	push af
	ad_address AV_REPLY
	ld a, [hl]
	and a
	ld c, 255
	jr z, .done
	ld c, a
	call BossAI_PreparePublicReply.Matches
	jr nc, .uncached_accuracy
	ad_address AV_PREPARED_IN + AD_ACCURACY
	ld c, [hl]
	jr .done
.uncached_accuracy
	ad_address AV_SLOT
	ld a, [hl]
	call BossAI_IncomingAccuracy
.done
	pop af
	ld b, a
	ret

; ai-layer: POLICY
BossAI_PreparedActionHasSpeedTie::
; DE=prepared exchange context. Carry means the public model has a 50/50
; same-priority speed tie. Unknown player stats/items remain model assumptions;
; known Quick Claw and copied-speed uncertainty must not invent a coin flip.
	ad_address AV_KIND
	ld a, [hl]
	and a
	jr nz, .no_tie
	ad_address AV_REPLY
	ld a, [hl]
	and a
	jr z, .no_tie
	ad_address AV_BRANCH
	bit AV_PREPARED_SPEED_UNKNOWN_F, [hl]
	jr nz, .no_tie
	av_load_word AV_OWN_SPEED
	ad_address AV_PLAYER_SPEED
	ld a, [hli]
	cp b
	jr nz, .no_tie
	ld a, [hl]
	cp c
	jr nz, .no_tie
	push de
	ad_address AV_PREPARED_OUT
	ld d, h
	ld e, l
	call BossAI_BuildPublicDamageContext.OwnItem
	pop de
	cp QUICK_CLAW
	jr z, .no_tie
	ad_address AV_REPLY
	ld c, [hl]
	call BossAI_PublicMovePriority
	ad_address AV_PREPARED_OUT + AD_PRIORITY
	ld a, [hl]
	cp b
	jr nz, .no_tie
	scf
	ret
.no_tie
	and a
	ret

; ai-layer: POLICY
BossAI_PreparePublicAction::
; DE=AV_PREPARED_CONTEXT_SIZE bytes, with SLOT/KIND/MOVE/BRANCH supplied.
; Prepare once per candidate in an immutable live-state evaluation. Speeds stay
; in AV_OWN_SPEED/AV_PLAYER_SPEED; bit6 retains their uncertainty across replies.
; Live status/stage/type/item changes require a new preparation epoch. Projected
; defensive changes within this exchange override the cloned damage facts.
	ad_address AV_MOVE
	ld c, [hl]
	ld b, 1
	ad_address AV_SLOT
	ld a, [hl]
	call BossAI_BuildOwnedDamageContext
	call BossAI_ContextSpeeds
	ld a, 0
	adc 0
	push af
	push hl
	av_store_word AV_OWN_SPEED
	pop bc
	av_store_word AV_PLAYER_SPEED
	pop af
	ad_address AV_BRANCH
	res AV_PREPARED_F, [hl]
	res AV_PREPARED_SPEED_UNKNOWN_F, [hl]
	and a
	jr nz, .copy_template
	set AV_PREPARED_SPEED_UNKNOWN_F, [hl]
.copy_template
	ad_address AV_ACCURACY_COUNT
	ld [hl], 0
	ad_address AV_PREPARED_DAMAGE
	ld [hl], 0
	ad_address AV_KIND
	ld a, [hl]
	and a
	jr nz, .save_template
	ad_address AD_MIN_HITS
	ld a, [hli]
	cp 1
	jr nz, .save_template
	ld a, [hl]
	cp 1
	jr nz, .save_template
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SUPER_FANG
	jr z, .save_template
	cp EFFECT_FALSE_SWIPE
	jr z, .save_template
; Only supported single-hit raw endpoints may be reused. These exclusions
; read target HP inside PerHit; multihit also depends on intermediate HP.
	call BossAI_ValuePublicExchange.MoveReplyPursuit
	push de
	call BossAI_PublicDamageRange
	pop de
	jr nc, .save_template
	ad_address AV_PREPARED_DAMAGE
	ld [hl], 1
.save_template
	push de
	ad_address AV_PREPARED_OUT
	ld b, h
	ld c, l
	ld h, d
	ld l, e
	ld d, b
	ld e, c
	ld b, AD_CONTEXT_SIZE
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	pop de
	jp BossAI_PrepareIncomingActor

; ai-layer: POLICY
BossAI_PrepareIncomingActor::
; Freeze the incoming actor once per candidate. The two stat pairs include
; screens and the known owned defender's item; neither depends on reply ID.
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	jr z, .valid_slot
	cp PARTY_LENGTH
	ret nc
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	ret z
	ret c
	ld a, b
.valid_slot
	ld bc, TACKLE
	call BossAI_BuildOwnedDamageContext
; Normalize a neutral physical donor explicitly. Its defaults must not depend
; on Tackle's authored category, power or effect if move data changes later.
	ad_address AD_CATEGORY
	ld [hl], NORMAL
	call BossAI_BuildPublicDamageContext.Stats
	call BossAI_BuildPublicDamageContext.KnownItems
	ad_address AD_POWER
	ld [hl], 1
	call BossAI_PublicHitFacts.SurvivalFacts
	call BossAI_BuildPreparedIncoming.Normalize
	ad_address AV_PREPARED_ACTOR
	call .save_context
	ad_address AV_PREPARED_STATS
	call .save_stats
	ad_address AD_CATEGORY
	ld [hl], SPECIAL
	call BossAI_BuildPublicDamageContext.Stats
	call BossAI_BuildPublicDamageContext.KnownItems
	ad_address AV_PREPARED_STATS + 4
	call .save_stats
	ad_address AV_PREPARED_OUT
	jp BossAI_BuildPreparedIncoming.clone
.save_stats
	ld b, h
	ld c, l
	ad_address AD_ATTACK
	ld a, 4
	jr .save
.save_context
	ld b, h
	ld c, l
	ld h, d
	ld l, e
	ld a, AD_CONTEXT_SIZE
.save
	push de
	ld d, b
	ld e, c
	ld b, a
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	pop de
	ret

; ai-layer: POLICY
BossAI_BuildPreparedIncoming::
; C=reply. Only callable during the current prepared candidate's epoch.
	push bc
	ad_address AV_PREPARED_ACTOR
	call .clone
	pop bc
	ad_address AD_MOVE
	ld [hl], c
; Preserve the direct adapter's early return for invalid slots/move zero.
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	jr z, .valid_slot
	cp PARTY_LENGTH
	jp nc, .direct
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	jp z, .direct
	jp c, .direct
.valid_slot
	ld a, c
	and a
	jp z, .direct
	call BossAI_LoadDamageMoveAttributes
	call BossAI_BuildPublicDamageContext.Category
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ld hl, AV_PREPARED_STATS
	jr c, .stats
	ld hl, AV_PREPARED_STATS + 4
.stats
	add hl, de
	push de
	ld b, h
	ld c, l
	ad_address AD_ATTACK
	ld d, h
	ld e, l
	ld h, b
	ld l, c
	ld b, 4
	call .copy
	pop de
	jp BossAI_FinishPreparedIncoming
.direct
	ad_address AV_SLOT
	ld a, [hl]
	ld b, 0
	jp BossAI_BuildOwnedDamageContext
.Normalize
; Once per candidate, before storing the immutable actor template. Every
; reply clone therefore starts with the direct constructor's neutral defaults.
	ad_address AD_FLAGS
	res AD_STRUGGLE_F, [hl]
	res AD_UNSUPPORTED_F, [hl]
	ld bc, .zero_fields
	call .reset_zero
	ld bc, .one_fields
	ld a, 1
	jr .reset
.reset_zero
	xor a
.reset
	push af
	ld a, [bc]
	inc bc
	cp $ff
	jr z, .reset_done
	ld h, 0
	ld l, a
	add hl, de
	pop af
	ld [hl], a
	jr .reset
.reset_done
	pop af
	ret
.zero_fields
	db AD_TYPE_ITEM_PERCENT, AD_HITS, AD_ROLL, AD_MATCHUP
	db AD_DAMAGE, AD_DAMAGE + 1, AD_PRIORITY, AD_TOTAL, AD_TOTAL + 1
	db AD_HITS_LEFT, AD_USER_ACC_STAGE, AD_TARGET_EVA_STAGE
	db AD_RAW_MIN, AD_RAW_MIN + 1, AD_RAW_MAX, AD_RAW_MAX + 1, $ff
.one_fields
	db AD_ITEM_NUM, AD_ITEM_DEN, AD_MIN_HITS, AD_MAX_HITS
	db AD_POSTROLL, AD_MAX_POSTROLL, $ff
.clone
; HL=template, DE=live context, preserved.
	push de
	ld b, AD_CONTEXT_SIZE
	call .copy
	pop de
	ret
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	ret

; ai-layer: POLICY
BossAI_FinishPreparedIncoming::
	call BossAI_BuildPublicDamageContext.EffectFacts
	call BossAI_PreparedIncomingHitFacts
	jp BossAI_BuildPublicDamageContext.copyguards

; ai-layer: POLICY
BossAI_PreparedIncomingHitFacts::
; The actor's survival probabilities are constant for all damaging replies.
; Power-zero moves clear both fields; damaging moves use the frozen donor.
	ad_address AD_POWER
	ld a, [hl]
	and a
	jr nz, .damaging
	ad_address AD_NEGATION_CHANCE
	ld [hli], a
	ld [hl], a
	jr .priority
.damaging
	av_copy_word AV_PREPARED_ACTOR + AD_NEGATION_CHANCE, AD_NEGATION_CHANCE
.priority
	ad_address AD_MOVE
	ld c, [hl]
	ad_address AD_EFFECT
	ld b, [hl]
	call BossAI_PublicMovePriority.FromEffect
	ad_address AD_PRIORITY
	ld [hl], b
; Resolve move-specific hit rules first. Certain/impossible hits bypass the
; stage/item/type modifiers entirely, including their cache.
	call BossAI_PublicHitFacts.BeforeStages
	ret nc
	ad_address AD_ACCURACY
	ld c, [hl]
	ad_address AV_ACCURACY_COUNT
	ld b, [hl]
	ld a, b
	and a
	jr z, .miss
	ad_address AV_ACCURACY_CACHE
.lookup
	ld a, [hli]
	cp c
	jr z, .found
	inc hl
	dec b
	jr nz, .lookup
.miss
; Only the raw accuracy byte varies in these modifiers during this candidate's
; preparation epoch. A full cache falls back to exact computation.
	push bc
	call BossAI_PublicHitFacts.ApplyAccuracyModifiers
	pop bc
	ad_address AD_ACCURACY
	ld b, [hl]
	ad_address AV_ACCURACY_COUNT
	ld a, [hl]
	cp AV_ACCURACY_ENTRIES
	ret nc
	inc [hl]
	add a
	push bc
	ld c, a
	ld b, 0
	ad_address AV_ACCURACY_CACHE
	add hl, bc
	pop bc
	ld [hl], c
	inc hl
	ld [hl], b
	ret
.found
	ld a, [hl]
	ad_address AD_ACCURACY
	ld [hl], a
	ret

; ai-layer: POLICY
BossAI_PrepareFirstActionStates::
; Optional joint-evaluator acceleration. The owned action has the same result
; before any opposing move, for each owned hit/miss and damage endpoint.
; Cache observable successor HP/defense/uncertainty; AD remains internal scratch.
	ad_address AV_PREPARED_DAMAGE
	ld a, [hl]
	and %10000111
	ld [hl], a
	ad_address AV_KIND
	ld a, [hl]
	and a
	ret nz
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	jr z, .valid_slot
	cp PARTY_LENGTH
	ret nc
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	ret z
	ret c
.valid_slot
	ad_address AV_PREPARED_DAMAGE
	set AV_PREPARED_FIRST_F, [hl]
	ret
.save
	push hl
	av_load_word AV_OWN_HP
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	av_load_word AV_PLAYER_HP
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	av_load_word AV_OWN_DEFENSE
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	av_load_word AV_OWN_DEFENSE + 2
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	av_load_word AV_RAW
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	av_load_word AV_DAMAGE
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	push hl
	ad_address AV_UNCERTAIN
	ld a, [hl]
	pop hl
	ld [hl], a
	ret
.load
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_OWN_HP
	pop hl
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_PLAYER_HP
	pop hl
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_OWN_DEFENSE
	pop hl
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_OWN_DEFENSE + 2
	pop hl
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_RAW
	pop hl
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	av_store_word AV_DAMAGE
	pop hl
	ld a, [hl]
	ad_address AV_UNCERTAIN
	or [hl]
	ld [hl], a
	ret

; ai-layer: POLICY
BossAI_PrepareHPValues::
; SRAM bank 0 is open under the synchronous wrapper's lifetime contract.
; Wider/zero max-HP domains retain the exact arithmetic path.
	ad_address AV_PREPARED_DAMAGE
	res AV_PREPARED_HP_F, [hl]
	av_load_word AD_ATTACKER_MAXHP
	call .valid_domain
	ret nc
	av_load_word AD_DEFENDER_MAXHP
	call .valid_domain
	ret nc
	call BossAI_ValuePublicExchange.SetWeight
	ad_address AV_WEIGHT
	ld a, [hl]
	push af
	av_load_word AD_ATTACKER_MAXHP
	pop af
	ld hl, sBossAIOwnHPValues
	call .table
	av_load_word AD_DEFENDER_MAXHP
	ld a, 128
	ld hl, sBossAIPlayerHPValues
	call .table
	ad_address AV_PREPARED_DAMAGE
	set AV_PREPARED_HP_F, [hl]
	ret
.valid_domain
	ld a, b
	or c
	ret z
	ld a, c
	sub LOW(704)
	ld a, b
	sbc HIGH(704)
	ret
.table
; Fill maxHP+1 exact bytes floor(HP * weight / maxHP), by quotient/remainder
; recurrence. BC=maxHP, A=weight, HL=table. DE preserved. Total quotient
; increments equal weight, even when maxHP is smaller than weight.
	push de
	ldh [hMultiplier], a
	push hl
	add hl, bc
	inc hl
	ld a, h
	ldh [hQuotient], a
	ld a, l
	ldh [hQuotient + 1], a
	pop hl
	ld de, 0
	xor a
	ldh [hQuotient + 3], a
.write
	ldh a, [hQuotient + 3]
	ld [hli], a
	ldh a, [hQuotient]
	cp h
	jr nz, .advance
	ldh a, [hQuotient + 1]
	cp l
	jr z, .done
.advance
	ldh a, [hMultiplier]
	add e
	ld e, a
	jr nc, .reduce
	inc d
.reduce
	ld a, e
	sub c
	ld a, d
	sbc b
	jr c, .write
	ld a, e
	sub c
	ld e, a
	ld a, d
	sbc b
	ld d, a
	ldh a, [hQuotient + 3]
	inc a
	ldh [hQuotient + 3], a
	jr .reduce
.done
	pop de
	ret

; ai-layer: POLICY
BossAI_PreparePublicReply::
; Optional per-reply template for the prepared evaluator. AV_REPLY may change
; between calls; matching the stored move ID prevents stale incoming reuse.
; Live facts and the owned action must remain in the preparation epoch.
	ad_address AV_PREPARED_DAMAGE
	res AV_PREPARED_IN_F, [hl]
	ad_address AV_PREPARED_IN_DAMAGE
	ld [hl], 0
	ad_address AV_REPLY
	ld a, [hl]
	and a
	ret z
	ld c, a
	call BossAI_BuildPreparedIncoming
	call BossAI_ValuePublicExchange.MoveReplyPursuit
	ad_address AD_MIN_HITS
	ld a, [hli]
	cp 1
	jr nz, .save
	ld a, [hl]
	cp 1
	jr nz, .save
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SUPER_FANG
	jr z, .save
	cp EFFECT_FALSE_SWIPE
	jr z, .save
	push de
	call BossAI_PublicDamageRange
	pop de
	jr nc, .save
	ad_address AV_PREPARED_IN_DAMAGE
	ld [hl], 1
.save
	push de
	ad_address AV_PREPARED_IN
	ld b, h
	ld c, l
	ld h, d
	ld l, e
	ld d, b
	ld e, c
	ld b, AD_CONTEXT_SIZE
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	pop de
	ad_address AV_PREPARED_DAMAGE
	set AV_PREPARED_IN_F, [hl]
	ret
.Matches
; C=reply preserved. Carry means a template for this exact reply exists.
	ad_address AV_PREPARED_DAMAGE
	bit AV_PREPARED_IN_F, [hl]
	jr z, .no_match
	ad_address AV_PREPARED_IN + AD_MOVE
	ld a, [hl]
	cp c
	jr nz, .no_match
	scf
	ret
.no_match
	and a
	ret

; ai-layer: POLICY
BossAI_ValuePreparedPublicExchange::
; DE=prepared context. Caller may change AV_REPLY and branch bits0..5 only.
; Template and cached speeds must belong to this candidate and current public
; state. No live input may change until this prepared evaluation is finished.
	ad_address AV_BRANCH
	set AV_PREPARED_F, [hl]
	ad_address AV_UNCERTAIN
	ld [hl], 0
	call BossAI_ValuePublicExchange.LoadPreparedOutgoing
	jp BossAI_ValuePublicExchange.initial_facts

; ai-layer: POLICY
BossAI_ValuePublicExchangeFromContext::
; Farcall-safe input: DE points to a context with AV_SLOT/KIND/MOVE/REPLY/
; BRANCH already supplied. All other inputs match BossAI_ValuePublicExchange.
	ad_address AV_SLOT
	ld a, [hl]
	push af
	ad_address AV_KIND
	ld b, [hl]
	ad_address AV_MOVE
	ld c, [hl]
	ad_address AV_REPLY
	ld a, [hl]
	push af
	ad_address AV_BRANCH
	ld a, [hl]
	ld l, a
	pop af
	ld h, a
	pop af
	jp BossAI_ValuePublicExchange

; ai-layer: POLICY
BossAI_ValuePublicExchange::
; DE=AV_CONTEXT_SIZE caller-owned bytes. A=owned slot ($ff active), B=kind,
; C=owned move, H=explicit public reply (0 means no reply, not an unknown move).
; Caller must validate slot/kind and move legality, including PP, Disable,
; Encore and Choice restrictions. This routine does not nominate legal actions.
; L=branch events: bit0 own miss, bit1 reply miss, bit2 resolve same-priority
; order (bit3 own first, otherwise reply first), bit4 own maximum damage,
; bit5 reply minimum damage. Zero is the conditional successful-hit branch
; with own minimum/reply maximum damage. The caller must enumerate only
; feasible order branches; priority still takes precedence over bits2/3.
; Accuracy/survival uncertainty still requires weighting
; or additional branches by the caller. Critical hits are excluded here.
; A switch's move is retained only for future valuation; it is NOT executed.
; Kind 3 is a forced wait: no entry damage or owned action, only the reply.
; Supply a valid move ID for its initial actor facts (the move is not executed).
; BC=1024 + own HP/material change - player's HP/material change.
; Each ordinary mon is worth 256 material plus 128 HP units. The authored own
; win condition is weighted 1.5x. Score the delta, so switching does not erase
; the retained active mon or award the bench member's preexisting material.
; Carry=modeled deterministic HP exchange; clear means AV_UNCERTAIN explains
; omitted/conditional transitions. No selector may treat clear as a proof.
; AV_OWN_HP/AV_PLAYER_HP expose the modeled successor. DE preserved.
	push af
	push bc
	push hl
	ld a, l
	and $3f ; direct callers cannot enable reads beyond AV_CONTEXT_SIZE
	ad_address AV_BRANCH
	ld [hl], a
	pop hl
	ld a, h
	ad_address AV_REPLY
	ld [hl], a
	pop bc
	ad_address AV_KIND
	ld [hl], b
	ad_address AV_MOVE
	ld [hl], c
	pop af
	ad_address AV_SLOT
	ld [hl], a
	xor a
	ad_address AV_UNCERTAIN
	ld [hl], a
	ad_address AV_SLOT
	ld a, [hl]
	ld b, 1
	call BossAI_BuildOwnedDamageContext
.initial_facts
	call .ResetHPState
	call .SetWeight
	call .ItemUncertainty
	call .VolatileUncertainty
	ad_address AV_KIND
	ld a, [hl]
	and a
	jr z, .move_order
	cp AV_WAIT_ACTION
	jr z, .wait_reply
; Every entry takes hazards before anything else. A faint replacement gives
; the player no additional turn. An ordinary switch forfeits its own action.
	ld a, [wEnemyScreens]
	and SCREENS_SPIKES_MASK
	ld b, a
	call BossAI_ContextEntryDamage
	call .LoseOwnHP
	ad_address AV_KIND
	ld a, [hl]
	cp AV_REPLACEMENT_ACTION
	jp z, .score
.wait_reply
	ad_address AV_KIND
	ld a, [hl]
	cp AV_WAIT_ACTION
	call z, .OwnCanAct ; a failed forced move can still encounter confusion first
	call .Reply
	jp .score
.move_order
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jr z, .uncached_speeds
	bit AV_PREPARED_SPEED_UNKNOWN_F, [hl]
	jr z, .speed_known
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_ORDER_F, [hl]
	jr .speed_known
.uncached_speeds
	call BossAI_ContextSpeeds
	ld a, 0
	adc 0
	push af
	push hl
	av_store_word AV_OWN_SPEED
	pop bc
	av_store_word AV_PLAYER_SPEED
	pop af
	and a
	jr nz, .speed_known
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_ORDER_F, [hl]
.speed_known
	ad_address AD_PRIORITY
	ld a, [hl]
	ad_address AV_PRIORITY
	ld [hl], a
	ad_address AV_REPLY
	ld a, [hl]
	and a
	jr z, .own_first
	ld c, a
	call BossAI_PublicMovePriority
	ld a, b
	ad_address AV_PRIORITY
	cp [hl]
	jr c, .own_first
	jr nz, .reply_first
	ad_address AV_BRANCH
	bit 2, [hl]
	jr z, .compare_speed
	push hl
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_ORDER_F, [hl]
	pop hl
	bit 3, [hl]
	jr nz, .own_first
	jr .reply_first
.compare_speed
	ad_address AV_UNCERTAIN
	bit AV_UNKNOWN_ORDER_F, [hl]
	jr nz, .reply_first
	av_load_word AV_PLAYER_SPEED
	push bc
	av_load_word AV_OWN_SPEED
	pop hl
	ld a, l
	sub c
	ld a, h
	sbc b
	jr c, .own_first
; Ties are explicitly uncertain; use reply-first as the conservative branch.
	ld a, b
	cp h
	jr nz, .reply_first
	ld a, c
	cp l
	jr nz, .reply_first
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_ORDER_F, [hl]
.reply_first
	call .Reply
	call .OwnMove
	jp .score
.own_first
	call .OwnFirstMove
	call .Reply
	jp .score

.ResetHPState
	ad_address AV_OWN_DEFENSE
	ld b, 8
	xor a
.clear_defenses
	ld [hli], a
	dec b
	jr nz, .clear_defenses
	av_copy_word AD_ATTACKER_HP, AV_OWN_START
	av_store_word AV_OWN_HP
	av_copy_word AD_ATTACKER_MAXHP, AV_OWN_MAX
	av_copy_word AD_DEFENDER_HP, AV_PLAYER_START
	av_store_word AV_PLAYER_HP
	av_copy_word AD_DEFENDER_MAXHP, AV_PLAYER_MAX
	ret

.OwnFirstMove
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jp z, .OwnMove
	ad_address AV_PREPARED_DAMAGE
	bit AV_PREPARED_FIRST_F, [hl]
	jp z, .OwnMove
	ad_address AV_BRANCH
	ld a, [hl]
	ld c, 1 << AV_FIRST_MISS_F
	ld hl, AV_FIRST_MISS
	bit 0, a
	jr nz, .first_state
	ld hl, AV_FIRST_MIN
	ld c, 1 << AV_FIRST_MIN_F
	bit 4, a
	jr z, .first_state
	ld hl, AV_FIRST_MAX
	ld c, 1 << AV_FIRST_MAX_F
.first_state
	add hl, de
	push hl
	ad_address AV_PREPARED_DAMAGE
	ld a, [hl]
	and c
	pop hl
	jp nz, BossAI_PrepareFirstActionStates.load
; Save only this action's uncertainty contribution. Initial/order uncertainty
; belongs to the current reply and must never leak into another cached branch.
	push bc
	push hl
	ad_address AV_UNCERTAIN
	ld a, [hl]
	push af
	ld [hl], 0
	call .OwnMove
	pop af
	pop hl
	push af
	call BossAI_PrepareFirstActionStates.save
	pop af
	ad_address AV_UNCERTAIN
	or [hl]
	ld [hl], a
	pop bc
	ad_address AV_PREPARED_DAMAGE
	ld a, [hl]
	or c
	ld [hl], a
	ret

.DefenseAxis
; Only these self-targeted scripts have one defensive raise and no other effect.
	ad_address AD_MOVE
	ld a, [hl]
	ld bc, $0101
	cp HARDEN
	jr z, .defense_axis_found
	cp WITHDRAW
	jr z, .defense_axis_found
	inc b
	cp BARRIER
	jr z, .defense_axis_found
	cp ACID_ARMOR
	jr z, .defense_axis_found
	ld c, 4
	cp AMNESIA
	jr z, .defense_axis_found
	and a
	ret
.defense_axis_found
	scf
	ret

.DefenseBoost
	call .DefenseAxis
	ret nc
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ad_address AV_PLAYER_DEFENSE
	jr z, .defense_record
	ad_address AV_OWN_DEFENSE
.defense_record
	ld [hl], c
	inc hl
	push hl
	push de
	call .DefenseInputs
	call BossAI_ProjectRaisedDefense
	pop de
	pop hl
	ld [hli], a
	ld [hl], b
	inc hl
	ld [hl], c
	scf
	ret

.DefenseInputs
; B=steps, C=axis. Return A=stage, HL=raw, DE=effective, B=steps.
; Read defense before screen/item modifiers. No hidden player stats are read.
	push bc
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr nz, .owned_defense_inputs
	ld b, 0
	ld hl, wPlayerAtkLevel
	add hl, bc
	ld a, [hl]
	push af
	ld b, 1
	call BossAI_EstimatePlayerDamageStat
	push bc
	call .DefenseAxis
	ld b, 0
	call BossAI_EstimatePlayerDamageStat
	jr .defense_inputs_done
.owned_defense_inputs
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	ld a, BASE_STAT_LEVEL
	jr nz, .owned_defense_stage
	ld b, 0
	ld hl, wEnemyAtkLevel
	add hl, bc
	ld a, [hl]
.owned_defense_stage
	push af
	ld a, c
	add a
	ld c, a
	ld b, 0
	ld hl, wEnemyMonAttack
	add hl, bc
	add MON_ATK
	ld c, a
	call BossAI_BuildPublicDamageContext.OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	push bc
	call .DefenseAxis
	ld a, c
	add a
	ld c, a
	ld b, 0
	ld hl, wEnemyAttack
	add hl, bc
	add MON_ATK
	ld c, a
	call BossAI_BuildPublicDamageContext.OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
.defense_inputs_done
	ld h, b
	ld l, c
	pop de
	pop af
	pop bc
	ret

.ProjectedDefenseMatches
; Carry and HL=effective override word only for this defender/category.
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ld b, 1
	jr c, .projected_axis
	ld b, 4
.projected_axis
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ad_address AV_OWN_DEFENSE
	jr z, .projected_record
	ad_address AV_PLAYER_DEFENSE
.projected_record
	ld a, [hl]
	cp b
	jr nz, .no_projected_defense
	inc hl
	inc hl
	scf
	ret
.no_projected_defense
	and a
	ret

.ProjectedDefense
	call .ProjectedDefenseMatches
	ret nc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	av_store_word AD_DEFENSE
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ld a, [wPlayerScreens]
	jr nz, .projected_screen
	ld a, [wEnemyScreens]
.projected_screen
	call BossAI_BuildPublicDamageContext.screen
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ret nz
	jp BossAI_BuildPublicDamageContext.defender_stat_item

.SetWeight
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	jr nz, .slot_known
	ld a, [wCurOTMon]
.slot_known
	inc a
	ld b, a
	ld a, [wBossAIWinconMonIdx]
	cp b
	ld a, 128
	jr nz, .weight
	ld a, 192
.weight
	ad_address AV_WEIGHT
	ld [hl], a
	ret

.BuildOutgoing
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jr z, .uncached_outgoing
	call .LoadPreparedOutgoing
	jr .outgoing_hp
.uncached_outgoing
	ad_address AV_MOVE
	ld c, [hl]
	ld b, 1
	ad_address AV_SLOT
	ld a, [hl]
	call BossAI_BuildOwnedDamageContext
.outgoing_hp
	call .ProjectedDefense
	av_copy_word AV_OWN_HP, AD_ATTACKER_HP
	av_copy_word AV_PLAYER_HP, AD_DEFENDER_HP
	call BossAI_BuildPublicDamageContext.RefreshHPFlags
	jp .MoveReplyPursuit
.BuildIncoming
; C=reply. Reconstruct from public/owned facts without swapping live actors.
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jr z, .uncached_incoming
	call BossAI_PreparePublicReply.Matches
	jr nc, .uncached_incoming
	ad_address AV_PREPARED_IN
	call .load_template
	jr .incoming_hp
.uncached_incoming
	ld b, 0
	ad_address AV_SLOT
	ld a, [hl]
	call BossAI_BuildOwnedDamageContext
.incoming_hp
	call .ProjectedDefense
	av_copy_word AV_OWN_HP, AD_DEFENDER_HP
	av_copy_word AV_PLAYER_HP, AD_ATTACKER_HP
	call BossAI_BuildPublicDamageContext.RefreshHPFlags
.MoveReplyPursuit
; An explicit opposing move is not a voluntary switch. The separate switch
; path below rejects incoming Pursuit until outgoing-active HP is represented.
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_PURSUIT
	ret nz
	ad_address AD_POSTROLL
	ld a, [hl]
	ad_address AD_MAX_POSTROLL
	ld [hl], a
	ret

.LoadPreparedOutgoing
; Clone the immutable template. Incoming execution overwrites the AD prefix,
; so every owned execution restores it before refreshing projected HP/flags.
	ad_address AV_PREPARED_OUT
.load_template
	push de
	ld b, AD_CONTEXT_SIZE
.load_prepared_byte
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .load_prepared_byte
	pop de
	ret

.IncomingDamageRange
	call .ProjectedDefenseMatches
	jp c, .uncached_range
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jp z, .uncached_range
	ad_address AV_REPLY
	ld c, [hl]
	call BossAI_PreparePublicReply.Matches
	jp nc, .uncached_range
	ad_address AV_PREPARED_IN_DAMAGE
	bit 0, [hl]
	jp z, .uncached_range
	ad_address AD_FLAGS
	ld a, [hl]
	ad_address AV_PREPARED_IN + AD_FLAGS
	cp [hl]
	jp nz, .uncached_range
	jp .use_prepared_range

.OwnMove
	av_load_word AV_OWN_HP
	ld a, b
	or c
	ret z
	av_load_word AV_PLAYER_HP
	ld a, b
	or c
	ret z
	call .BuildOutgoing
	call .OwnCanAct
	ret nc
	call .DefenseBoost
	ret c
	call BossAI_ContextRecovery
	jr nc, .own_damage
	ld a, b
	or c
	ret z
	call .GainOwnHP
; Rest/status cleanup and subsequent action denial require successor status.
	ad_address AV_MOVE
	ld a, [hl]
	cp REST
	ret nz
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_TRANSITION_F, [hl]
	ret
.own_damage
	call .EffectUncertainty
	call .HitUncertainty
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SELFDESTRUCT
	jr nz, .own_hit
; Combat computes damage before selfdestruct, then faints the user before
; failuretext. Keep AD attacker HP for damage, but faint projected own HP now.
	ld bc, 0
	av_store_word AV_OWN_HP
.own_hit
	ad_address AV_BRANCH
	bit 0, [hl]
	ret nz
	ad_address AD_ACCURACY
	ld a, [hl]
	and a
	ret z
	call .OwnDamageRange
	push af
	call .RangeUncertainty
	pop af
	jr c, .own_amount
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_DAMAGE_F, [hl]
	ret
.own_amount
	push hl
	ad_address AV_BRANCH
	bit 4, [hl]
	pop hl
	jr z, .own_minimum
	ld b, h
	ld c, l
	av_store_word AV_DAMAGE
	av_copy_word AD_RAW_MAX, AV_RAW
	jr .own_selected
.own_minimum
	av_store_word AV_DAMAGE
	av_copy_word AD_RAW_MIN, AV_RAW
.own_selected
	av_load_word AV_DAMAGE
	ld a, b
	or c
	ret z ; immunity/failure ends the script before recoil and drain
	call .LosePlayerHP
	call .OwnAfterHitItem
	av_copy_word AV_OWN_HP, AD_ATTACKER_HP
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SELFDESTRUCT
	jr z, .selfdestruct
	cp EFFECT_RECOIL_HIT
	jr z, .recoil
	cp EFFECT_LEECH_HIT
	jr z, .drain
	cp EFFECT_DREAM_EATER
	jr z, .drain
	ret
.selfdestruct
	ld bc, 0
	av_store_word AV_OWN_HP
	ret
.recoil
	av_load_word AV_RAW
	call BossAI_ContextRecoil
	jp .LoseOwnHP
.drain
	av_load_word AV_RAW
	call BossAI_ContextDrain
	jp .GainOwnHP

.OwnDamageRange
; BC=min, HL=max, DE=context, carry=supported. Raw endpoints remain in AD.
	call .ProjectedDefenseMatches
	jr c, .uncached_range
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jr z, .uncached_range
	ad_address AV_PREPARED_DAMAGE
	bit 0, [hl]
	jr z, .uncached_range
	ad_address AD_FLAGS
	ld a, [hl]
	ad_address AV_PREPARED_OUT + AD_FLAGS
	cp [hl]
	jr nz, .uncached_range
.use_prepared_range
; The template raw amounts are independent of target HP for these single-hit
; effects, but each HP-loss endpoint must be capped at the projected target HP.
	av_load_word AD_RAW_MIN
	call .CapPublicTargetHP
	push bc
	av_load_word AD_RAW_MAX
	call .CapPublicTargetHP
	ld h, b
	ld l, c
	pop bc
	scf
	ret
.uncached_range
	push de
	call BossAI_PublicDamageRange
	ld h, d
	ld l, e
	pop de
	ret
.CapPublicTargetHP
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ld a, l
	sub c
	ld a, h
	sbc b
	ret nc
	ld b, h
	ld c, l
	ret

.Reply
	av_load_word AV_OWN_HP
	ld a, b
	or c
	ret z
	ad_address AV_REPLY
	ld a, [hl]
	and a
	ret z
	av_load_word AV_PLAYER_HP
	ld a, b
	or c
	ret z
	; A hit-branch finish interrupts even when a separate miss branch exists.
	ad_address AV_REPLY
	ld c, [hl]
	call .BuildIncoming
	call .PlayerCanAct
	ret nc
	ad_address AV_KIND
	ld a, [hl]
	cp AV_SWITCH_ACTION
	jr nz, .ordinary_reply
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_PURSUIT
	jp z, .TransitionUncertainty
.ordinary_reply
	call .DefenseBoost
	ret c
	call BossAI_ContextRecovery
	jr nc, .reply_damage
	ld a, b
	or c
	ret z
	call .GainPlayerHP
	ad_address AV_REPLY
	ld a, [hl]
	cp REST
	ret nz
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_TRANSITION_F, [hl]
	ret
.reply_damage
	call .EffectUncertainty
	call .HitUncertainty
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_SELFDESTRUCT
	jr nz, .reply_hit
	ld bc, 0
	av_store_word AV_PLAYER_HP
.reply_hit
	ad_address AV_BRANCH
	bit 1, [hl]
	ret nz
	ad_address AD_ACCURACY
	ld a, [hl]
	and a
	ret z
	call .IncomingDamageRange
	push af
	call .RangeUncertainty
	pop af
	jr c, .reply_amount
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_DAMAGE_F, [hl]
; Unknown damaging replies use the HP-loss upper bound, never zero risk.
	ad_address AD_POWER
	ld a, [hl]
	and a
	ret z
	av_load_word AV_OWN_HP
	jp .LoseOwnHP
.reply_amount
	push hl
	ad_address AV_BRANCH
	bit 5, [hl]
	pop hl
	jr z, .reply_maximum
	av_store_word AV_DAMAGE
	av_copy_word AD_RAW_MIN, AV_RAW
	jr .reply_selected
.reply_maximum
	ld b, h
	ld c, l
	av_store_word AV_DAMAGE
	av_copy_word AD_RAW_MAX, AV_RAW
.reply_selected
	av_load_word AV_DAMAGE
	ld a, b
	or c
	ret z
	call .LoseOwnHP
	call .ReplyAfterHitItem
	av_copy_word AV_PLAYER_HP, AD_ATTACKER_HP
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_RECOIL_HIT
	jr z, .reply_recoil
	cp EFFECT_LEECH_HIT
	jr z, .reply_drain
	cp EFFECT_DREAM_EATER
	ret nz
.reply_drain
	av_load_word AV_RAW
	call BossAI_ContextDrain
	jp .GainPlayerHP
.reply_recoil
	av_load_word AV_RAW
	call BossAI_ContextRecoil
	jp .LosePlayerHP

.OwnAfterHitItem
; Known own item, after successful damage but before the move's recoil/drain.
; Opponent's unknown held item is omitted by the public model. Multihit item
; interactions remain rejected by the damage adapter until both HPs advance.
	av_load_word AV_OWN_HP
	ld a, b
	or c
	ret z
	call BossAI_BuildPublicDamageContext.OwnItem
	cp LIFE_ORB
	jr z, .life_orb
	cp SHELL_BELL
	ret nz
	av_load_word AV_RAW
	ld a, 1
	ld h, 8
	call BossAI_DamageKernel.Scale
	push bc
	av_load_word AV_OWN_MAX
	push bc
	av_load_word AV_OWN_HP
	pop hl
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a ; missing HP
	pop bc
	ld a, c
	sub l
	ld a, b
	sbc h
	jr c, .shell_gain
	ld b, h
	ld c, l
.shell_gain
	jp .GainOwnHP
.life_orb
	av_load_word AV_OWN_MAX
	ld a, 1
	ld h, LIFE_ORB_RECOIL_DEN
	call BossAI_DamageKernel.Scale
	jp .LoseOwnHP
.ReplyAfterHitItem
; The known defender's Helmet hurts the public attacker on contact. It still
; triggers on a KO of its holder, but never through the holder's Substitute.
	call BossAI_BuildPublicDamageContext.OwnItem
	cp ROCKY_HELMET
	ret nz
	ad_address AD_FLAGS
	bit AD_SUBSTITUTE_F, [hl]
	ret nz
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
	ret z
	av_load_word AV_PLAYER_MAX
	ld a, 1
	ld h, ROCKY_HELMET_DEN
	call BossAI_DamageKernel.Scale
	jp .LosePlayerHP

.OwnCanAct
; Certain denial is not uncertainty. Counter-one sleep wake, thawing moves,
; confusion and paralysis need status/outcome branches beyond this HP kernel.
	ld hl, wEnemySubStatus4
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	bit SUBSTATUS_RECHARGE, a
	jr nz, .denied
	ld hl, wEnemySubStatus3
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	bit SUBSTATUS_FLINCHED, a
	jr nz, .denied
	bit SUBSTATUS_CONFUSED, a
	call nz, .TransitionUncertainty
	call BossAI_BuildPublicDamageContext.OwnStatus
	jr .status_can_act
.PlayerCanAct
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_RECHARGE, a
	jr nz, .denied
	ld a, [wPlayerSubStatus3]
	bit SUBSTATUS_FLINCHED, a
	jr nz, .denied
	bit SUBSTATUS_CONFUSED, a
	call nz, .TransitionUncertainty
	ld a, [wBattleMonStatus]
.status_can_act
	bit PAR, a
	call nz, .TransitionUncertainty
	push af
	and SLP_MASK
	jr z, .not_sleeping
	cp 1
	jr z, .sleep_wake
	ad_address AD_MOVE
	ld a, [hl]
	cp SNORE
	jr z, .status_pop_yes
	cp SLEEP_TALK
	jr z, .asleep_call
	pop af
.denied
	and a
	ret
.sleep_wake
	call .TransitionUncertainty
	ad_address AD_MOVE
	ld a, [hl]
	cp SNORE
	jr z, .sleep_denied
	cp SLEEP_TALK
	jr z, .sleep_denied
	jr .status_pop_yes
.asleep_call
	call .TransitionUncertainty
.status_pop_yes
	pop af
	scf
	ret
.sleep_denied
	pop af
	and a
	ret
.not_sleeping
	pop af
	bit FRZ, a
	jr z, .can_act
	ad_address AD_MOVE
	ld a, [hl]
	cp FLAME_WHEEL
	jr z, .thaw
	cp SACRED_FIRE
	jr nz, .denied
.thaw
	call .TransitionUncertainty
.can_act
	scf
	ret
.TransitionUncertainty
	push hl
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_TRANSITION_F, [hl]
	pop hl
	ret
.ItemUncertainty
; Item state/secondary effects beyond the modeled direct HP changes.
	call BossAI_BuildPublicDamageContext.OwnItem
	cp AIR_BALLOON
	jr z, .TransitionUncertainty
	cp QUICK_CLAW
	jr z, .OrderUncertainty
	cp KINGS_ROCK
	jr z, .TransitionUncertainty
	ret
.OrderUncertainty
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_ORDER_F, [hl]
	ret
.VolatileUncertainty
	ld hl, wEnemySubStatus1
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	and (1 << SUBSTATUS_PROTECT) | (1 << SUBSTATUS_ENDURE) | (1 << SUBSTATUS_IN_LOVE)
	call nz, .TransitionUncertainty
	ld hl, wEnemySubStatus5
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	bit SUBSTATUS_DESTINY_BOND, a
	call nz, .TransitionUncertainty
	ld a, [wPlayerSubStatus1]
	and (1 << SUBSTATUS_PROTECT) | (1 << SUBSTATUS_ENDURE) | (1 << SUBSTATUS_IN_LOVE)
	call nz, .TransitionUncertainty
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_DESTINY_BOND, a
	call nz, .TransitionUncertainty
	ret
.EffectUncertainty
; HP-only script families. Other supported damage effects may alter status,
; stages, traps, charging or flinch state even when damage endpoints coincide.
	ad_address AD_EFFECT
	ld a, [hl]
	push bc
	ld b, a
	ld hl, .HPOnlyEffects
.effect_loop
	ld a, [hli]
	cp -1
	jr z, .effect_unknown
	cp b
	jr nz, .effect_loop
	pop bc
; Poison's contact retaliation can change the attacker's status mid-exchange.
	ld a, POISON
	call BossAI_DamageKernel.DefenderContribution
	and a
	ret z
	push bc
	ad_address AD_MOVE
	ld a, [hl]
	dec a
	ld c, a
	ld b, 0
	ld hl, MoveContactFlags
	add hl, bc
	ld a, BANK(MoveContactFlags)
	call GetFarByte
	pop bc
	and a
	jp nz, .TransitionUncertainty
	ret
.effect_unknown
	pop bc
	jp .TransitionUncertainty
.HPOnlyEffects
	db EFFECT_NORMAL_HIT, EFFECT_ALWAYS_HIT, EFFECT_STATIC_DAMAGE
	db EFFECT_LEVEL_DAMAGE, EFFECT_SUPER_FANG, EFFECT_FALSE_SWIPE
	db EFFECT_SELFDESTRUCT, EFFECT_RECOIL_HIT, EFFECT_LEECH_HIT, EFFECT_DREAM_EATER
	db EFFECT_MULTI_HIT, EFFECT_DOUBLE_HIT, EFFECT_EARTHQUAKE, EFFECT_GUST
	db EFFECT_PURSUIT, EFFECT_PAY_DAY, EFFECT_PRIORITY_HIT
	db -1

.RangeUncertainty
; BC=min, HL=max, DE=context. Preserve both endpoints and the context pointer.
	ld a, b
	cp h
	jr nz, .range_varies
	ld a, c
	cp l
	jr nz, .range_varies
; Capped HP loss can be constant on overkill while raw recoil/drain varies.
	push bc
	push hl
	av_load_word AD_RAW_MIN
	push bc
	av_load_word AD_RAW_MAX
	pop hl
	ld a, b
	cp h
	jr nz, .raw_varies
	ld a, c
	cp l
	jr z, .raw_done
.raw_varies
	ad_address AV_UNCERTAIN
	set AV_AMOUNT_RANGE_F, [hl]
.raw_done
	pop hl
	pop bc
	ret
.range_varies
	push hl
	ad_address AV_UNCERTAIN
	set AV_AMOUNT_RANGE_F, [hl]
	pop hl
	ret

.HitUncertainty
	ad_address AD_ACCURACY
	ld a, [hl]
	and a
	ret z
	cp 255
	jr nz, .uncertain_hit
	ad_address AD_NEGATION_CHANCE
	ld a, [hli]
	or [hl]
	jr nz, .uncertain_hit
	ad_address AD_FLAGS
	bit AD_SUBSTITUTE_F, [hl]
	jr nz, .uncertain_hit
	ret
.uncertain_hit
	ad_address AV_UNCERTAIN
	set AV_UNKNOWN_HIT_F, [hl]
	ret

.LoseOwnHP
	ld hl, AV_OWN_HP
	jr .SubtractHP
.LosePlayerHP
	ld hl, AV_PLAYER_HP
.SubtractHP
; BC=loss, HL=context offset. Saturating subtract from a projected HP word.
	add hl, de
	push hl
	inc hl
	ld a, [hld]
	sub c
	ld c, a
	ld a, [hl]
	sbc b
	ld b, a
	jr nc, .store_hp
	ld bc, 0
.store_hp
	pop hl
	ld [hl], b
	inc hl
	ld [hl], c
	ret
.GainOwnHP
; Recovery helpers have already capped the gain at projected missing HP.
	ld hl, AV_OWN_HP
	jr .GainHP
.GainPlayerHP
	ld hl, AV_PLAYER_HP
.GainHP
	add hl, de
	inc hl
	ld a, [hl]
	add c
	ld [hld], a
	ld a, [hl]
	adc b
	ld [hl], a
	ret

.score
	ld bc, 1024
	av_store_word AV_VALUE
; Floor each state's HP fraction independently. Its delta telescopes across
; continuations and does not reward splitting one HP change into many events.
	av_load_word AV_OWN_START
	ad_address AV_OWN_HP
	ld a, [hli]
	cp b
	jr nz, .own_hp_value
	ld a, [hl]
	cp c
	jr z, .player_hp_value ; identical state fractions cancel exactly
.own_hp_value
	ad_address AV_WEIGHT
	ld a, [hl]
; Reload max HP after fetching the weight (address macro clobbers HL).
	push af
	push bc
	av_load_word AV_OWN_MAX
	ld h, b
	ld l, c
	pop bc
	pop af
	call .OwnHPFraction
	call .SubtractValue
	av_load_word AV_OWN_HP
	push bc
	ad_address AV_WEIGHT
	ld a, [hl]
	push af
	av_load_word AV_OWN_MAX
	ld h, b
	ld l, c
	pop af
	pop bc
	call .OwnHPFraction
	call .AddValue
.player_hp_value
	av_load_word AV_PLAYER_START
	ad_address AV_PLAYER_HP
	ld a, [hli]
	cp b
	jr nz, .changed_player_hp
	ld a, [hl]
	cp c
	jr z, .material_value
.changed_player_hp
	push bc
	av_load_word AV_PLAYER_MAX
	ld h, b
	ld l, c
	pop bc
	ld a, 128
	call .PlayerHPFraction
	call .AddValue
	av_load_word AV_PLAYER_HP
	push bc
	av_load_word AV_PLAYER_MAX
	ld h, b
	ld l, c
	pop bc
	ld a, 128
	call .PlayerHPFraction
	call .SubtractValue
.material_value
	av_load_word AV_OWN_START
	ld a, b
	or c
	jr z, .player_material
	av_load_word AV_OWN_HP
	ld a, b
	or c
	jr nz, .player_material
	ad_address AV_WEIGHT
	ld a, [hl]
	ld c, a
	ld b, 0
	sla c
	rl b
	call .SubtractValue
.player_material
	av_load_word AV_PLAYER_START
	ld a, b
	or c
	jr z, .value_done
	av_load_word AV_PLAYER_HP
	ld a, b
	or c
	jr nz, .value_done
	ld bc, 256
	call .AddValue
.value_done
	av_load_word AV_VALUE
	ad_address AV_UNCERTAIN
	ld a, [hl]
	and a
	ret nz
	scf
	ret
.AddValue
	ad_address AV_VALUE
	inc hl
	ld a, [hl]
	add c
	ld [hld], a
	ld a, [hl]
	adc b
	ld [hl], a
	ret
.SubtractValue
	ad_address AV_VALUE
	inc hl
	ld a, [hl]
	sub c
	ld [hld], a
	ld a, [hl]
	sbc b
	ld [hl], a
	ret
.OwnHPFraction
	push af
	ld a, HIGH(sBossAIOwnHPValues)
	jr .PreparedHPFraction
.PlayerHPFraction
	push af
	ld a, HIGH(sBossAIPlayerHPValues)
.PreparedHPFraction
; Table bases need not be page aligned. Keep the pointer separately from the
; caller's maxHP until the domain check has succeeded.
	push hl
	push af
	ad_address AV_BRANCH
	bit AV_PREPARED_F, [hl]
	jr z, .no_hp_table
	ad_address AV_PREPARED_DAMAGE
	bit AV_PREPARED_HP_F, [hl]
	jr z, .no_hp_table
	pop af
	pop hl
	push af
	ld a, l
	sub c
	ld a, h
	sbc b
	jr c, .hp_above_max
	pop af
	cp HIGH(sBossAIOwnHPValues)
	ld hl, sBossAIOwnHPValues
	jr z, .hp_table
	ld hl, sBossAIPlayerHPValues
.hp_table
	add hl, bc
	ld c, [hl]
	ld b, 0
	pop af
	ret
.no_hp_table
	pop af
	pop hl
	jr .hp_fallback
.hp_above_max
	pop af
.hp_fallback
	pop af
	jp .HPFraction
.HPFraction
; BC=HP, HL=max HP, A=weight; BC=floor(HP*weight/max), zero stays zero.
; A 16-bit denominator is needed for real max HP above 255.
	push de
	ld d, h
	ld e, l
	ldh [hMultiplier], a
	xor a
	ldh [hMultiplicand], a
	ld a, b
	ldh [hMultiplicand + 1], a
	ld a, c
	ldh [hMultiplicand + 2], a
	call BossAI_Multiply
	ld a, d
	or e
	jr z, .fraction_zero
; Legal HP is at most max HP, so the weighted quotient fits one byte.
; Test eight quotient bits instead of subtracting max HP up to 192 times.
; Retain the general path for malformed/diagnostic HP above max HP.
	ld a, b
	cp d
	jr c, .fraction_binary
	jr nz, .fraction_general
	ld a, c
	cp e
	jr c, .fraction_binary
	jr z, .fraction_binary
.fraction_general
	ldh a, [hProduct + 2]
	ld h, a
	ldh a, [hProduct + 3]
	ld l, a
	ld bc, 0
	ld a, d
	or e
	jr z, .fraction_done
.fraction_loop
	ld a, l
	sub e
	ld l, a
	ld a, h
	sbc d
	ld h, a
	ldh a, [hProduct + 1]
	sbc 0
	jr c, .fraction_done
	ldh [hProduct + 1], a
	inc bc
	jr .fraction_loop
.fraction_binary
; Divisor B:DE = max HP * 128; numerator stays in hProduct+1..3.
	ld b, 0
	ld c, 7
.fraction_align
	sla e
	rl d
	rl b
	dec c
	jr nz, .fraction_align
	ld a, 8
	ldh [hMultiplier], a
.fraction_bit
	sla c
	ldh a, [hProduct + 3]
	sub e
	ld l, a
	ldh a, [hProduct + 2]
	sbc d
	ld h, a
	ldh a, [hProduct + 1]
	sbc b
	jr c, .fraction_skip_bit
	ldh [hProduct + 1], a
	ld a, h
	ldh [hProduct + 2], a
	ld a, l
	ldh [hProduct + 3], a
	inc c
.fraction_skip_bit
	srl b
	rr d
	rr e
	ldh a, [hMultiplier]
	dec a
	ldh [hMultiplier], a
	jr nz, .fraction_bit
	ld b, 0
	jr .fraction_done
.fraction_zero
	ld bc, 0
.fraction_done
	pop de
	ret

; ai-layer: POLICY
BossAI_ProjectRaisedDefense::
; A=current stage (1..13), B=raise (1 or 2), HL=raw defense,
; DE=current effective defense before screens/items. A=new stage, BC=new stat.
; Pure combat RaiseStat/CalcBattleStats arithmetic; AF/BC/DE/HL clobbered.
	push hl
	push de
	cp MAX_STAT_LEVEL
	jr nc, .unchanged
	add b
	cp MAX_STAT_LEVEL + 1
	jr c, .stage_ready
	ld a, MAX_STAT_LEVEL
.stage_ready
	ld c, a
	ld a, d
	cp HIGH(MAX_STAT_VALUE)
	jr nz, .recalculate
	ld a, e
	cp LOW(MAX_STAT_VALUE)
	jr nz, .recalculate
; Combat rolls back exactly one stage, even after a two-stage request.
	ld a, c
	dec a
.unchanged
	pop bc
	pop hl
	ret
.recalculate
	ld a, c
	push af
	dec a
	add a
	ld e, a
	ld d, 0
	ld hl, StatLevelMultipliers
	add hl, de
	ld a, BANK(StatLevelMultipliers)
	call GetFarByte
	ld d, a
	inc hl
	ld a, BANK(StatLevelMultipliers)
	call GetFarByte
	ld h, a
	ld a, d
	pop de ; new stage in D
	pop bc ; discard old effective stat
	pop bc ; raw stat
	push de
	call BossAI_DamageKernel.Scale
	call BossAI_CapDamageStat
	pop af
	ret
