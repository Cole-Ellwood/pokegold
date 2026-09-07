; Same-bank bridges reuse authoritative public-model flag producers. Each
; stage is exported separately; the native executor decides whether execution
; reaches it before accumulating uncertainty. SRAM bank0 must be open.
DEF FSB_CAN_ACT EQU $a478
DEF FSB_CHECK_FLAGS EQU FSB_CAN_ACT + 1
DEF FSB_EFFECT_FLAGS EQU FSB_CHECK_FLAGS + 1
DEF FSB_HIT_FLAGS EQU FSB_EFFECT_FLAGS + 1
DEF FSB_SETUP_FLAGS EQU FSB_HIT_FLAGS + 1
DEF FSB_RANGE_FLAGS EQU FSB_SETUP_FLAGS + 1
DEF FSB_RANGE_SUPPORT EQU FSB_RANGE_FLAGS + 1
DEF FSB_LOSS_MIN EQU FSB_RANGE_SUPPORT + 1
DEF FSB_LOSS_MAX EQU FSB_LOSS_MIN + 2
DEF FSB_RAW_MIN EQU FSB_LOSS_MAX + 2
DEF FSB_RAW_MAX EQU FSB_RAW_MIN + 2
DEF FSB_ENTRY_LOSS EQU FSB_RAW_MAX + 2
DEF FSA_OWN EQU $a3f8
DEF FSA_START_HP EQU FSA_OWN
DEF FSA_MAX_HP EQU FSA_OWN + 2
DEF FSA_START_PHI EQU FSA_OWN + 4
DEF FSA_ENTRY_HP EQU FSA_OWN + 6
DEF FSA_ENTRY_PHI EQU FSA_OWN + 8
DEF FSA_WEIGHT EQU FSA_OWN + 34
DEF FSA_HP_MODE EQU FSA_OWN + 37
ASSERT FSB_ENTRY_LOSS + 2 <= $a4f8
ASSERT FSA_OWN + 40 == $a420

; Transient action-prefix export in the final 64 bytes of the producer bridge.
; This is input to plan construction, not a complete executable plan. The
; context/status readsets must match the continuation when these facts are used.
DEF FSB_PREFIX EQU $a4b8
DEF FSB_PREFIX_MOVE EQU FSB_PREFIX
DEF FSB_PREFIX_EFFECT EQU FSB_PREFIX + 1
DEF FSB_PREFIX_POWER EQU FSB_PREFIX + 2
DEF FSB_PREFIX_ACCURACY EQU FSB_PREFIX + 3
DEF FSB_PREFIX_PRIORITY EQU FSB_PREFIX + 4
DEF FSB_PREFIX_SLOT EQU FSB_PREFIX + 5
DEF FSB_PREFIX_KIND EQU FSB_PREFIX + 6
DEF FSB_PREFIX_DIRECTION EQU FSB_PREFIX + 7 ; 0owned,1player
DEF FSB_PREFIX_CAN_ACT EQU FSB_PREFIX + 8
DEF FSB_PREFIX_CHECK EQU FSB_PREFIX + 9
DEF FSB_PREFIX_EFFECT_FLAGS EQU FSB_PREFIX + 10
DEF FSB_PREFIX_HIT_FLAGS EQU FSB_PREFIX + 11
DEF FSB_PREFIX_RECOVERY EQU FSB_PREFIX + 12 ; recognized, even when quota0
DEF FSB_PREFIX_QUOTA EQU FSB_PREFIX + 13 ; BE uncapped recovery
ASSERT FSB_PREFIX + 64 == $a4f8

BossAI_FastExportActionPrefix::
; DE=public AD/AV context, C=0owned/1player, SRAM bank0 open.
; Preserve context and DE/SP. Output existing action flags a478..a47b and
; prefix a4b8..a4f7 (unused bytes zero). Carry=accepted; reject direction>=2
; without writes. No range/HP transition and no uncertainty is committed.
; Neither a can-act verdict nor recovery recognition bypasses executor gates:
; both living, nonzero reply, switch-Pursuit, and boost dispatch still apply.
	ld a, c
	cp 2
	jr nc, .reject
	ld hl, FSB_PREFIX
	ld b, 64
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ld a, c
	ld [FSB_PREFIX_DIRECTION], a
	call BossAI_FastExportActionFlags
	ld hl, FSB_CAN_ACT
	ld bc, FSB_PREFIX_CAN_ACT
	push de
	ld d, b
	ld e, c
	ld b, 4
.flags
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .flags
	pop de
	ad_address AD_MOVE
	ld a, [hl]
	ld [FSB_PREFIX_MOVE], a
	ad_address AD_EFFECT
	ld a, [hl]
	ld [FSB_PREFIX_EFFECT], a
	ad_address AD_POWER
	ld a, [hl]
	ld [FSB_PREFIX_POWER], a
	ad_address AD_ACCURACY
	ld a, [hli]
	ld [FSB_PREFIX_ACCURACY], a
	ld a, [hl]
	ld [FSB_PREFIX_PRIORITY], a
	ad_address AD_OWN_SLOT
	ld a, [hl]
	ld [FSB_PREFIX_SLOT], a
	ad_address AV_KIND
	ld a, [hl]
	ld [FSB_PREFIX_KIND], a
	farcall BossAI_FastRecoveryQuota
	ld a, 0
	adc 0
	ld [FSB_PREFIX_RECOVERY], a
	ld a, b
	ld [FSB_PREFIX_QUOTA], a
	ld a, c
	ld [FSB_PREFIX_QUOTA + 1], a
	scf
	ret
.reject
	and a
	ret

BossAI_FastExportActionFlags::
; DE=valid public context in the AV prefix, C=0owned/1player.
; DE/SP and all context bytes preserved. AF/BC/HL scratch; carry=accepted.
; Output only a478..a47b. Invalid direction rejects without mutation.
; Can-act flags are retained even on denial; effect/hit flags are metadata,
; not an assertion that a recovery/boost/miss/denied action reaches damage.
	ld a, c
	cp 2
	jr nc, .reject
	ad_address AV_UNCERTAIN
	ld a, [hl]
	push af
	ld [hl], 0
	ld a, c
	and a
	jr nz, .player
	call BossAI_ValuePublicExchange.OwnCanAct
	jr .can_act
.player
	call BossAI_ValuePublicExchange.PlayerCanAct
.can_act
	ld a, 0
	adc 0
	ld [FSB_CAN_ACT], a
	call .TakeFlags
	ld [FSB_CHECK_FLAGS], a
	call BossAI_ValuePublicExchange.EffectUncertainty
	call .TakeFlags
	ld [FSB_EFFECT_FLAGS], a
	call BossAI_ValuePublicExchange.HitUncertainty
	call .TakeFlags
	ld [FSB_HIT_FLAGS], a
	pop af
	ad_address AV_UNCERTAIN
	ld [hl], a
	scf
	ret
.reject
	and a
	ret
.TakeFlags
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ld [hl], 0
	ret

BossAI_FastExportSetupFlags::
; DE=owned actor's public context with correct AD_OWN_SLOT. Preserve context
; and DE/SP; output a47c only. Item/volatile flags apply at actor setup.
	ad_address AV_UNCERTAIN
	ld a, [hl]
	push af
	ld [hl], 0
	call BossAI_ValuePublicExchange.ItemUncertainty
	call BossAI_ValuePublicExchange.VolatileUncertainty
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ld [FSB_SETUP_FLAGS], a
	pop af
	ld [hl], a
	ret

ASSERT BANK(BossAI_FastExportActionFlags) == BANK(BossAI_ValuePublicExchange)

BossAI_FastExportDamageRange::
; DE=fully prepared public context for this particular HP/defense regime.
; Produces range flags/support, capped endpoints and raw endpoints separately.
; Restores AV_UNCERTAIN, preserves DE/SP. AD prefix is producer scratch;
; MoveReplyPursuit normalizes the explicit opposing-move postroll first.
; A captured range/flags certificate is only valid for this supplied context.
	ad_address AV_UNCERTAIN
	ld a, [hl]
	push af
	ld [hl], 0
	call BossAI_ValuePublicExchange.MoveReplyPursuit
	push de
	call BossAI_PublicDamageRange
	ld h, d
	ld l, e
	pop de
	push af
	call BossAI_ValuePublicExchange.RangeUncertainty
	ld a, b
	ld [FSB_LOSS_MIN], a
	ld a, c
	ld [FSB_LOSS_MIN + 1], a
	ld a, h
	ld [FSB_LOSS_MAX], a
	ld a, l
	ld [FSB_LOSS_MAX + 1], a
	pop af
	ld a, 0
	adc 0
	ld [FSB_RANGE_SUPPORT], a
	ad_address AD_RAW_MIN
	ld a, [hli]
	ld [FSB_RAW_MIN], a
	ld a, [hli]
	ld [FSB_RAW_MIN + 1], a
	ld a, [hli]
	ld [FSB_RAW_MAX], a
	ld a, [hl]
	ld [FSB_RAW_MAX + 1], a
	ad_address AV_UNCERTAIN
	ld a, [hl]
	ld [FSB_RANGE_FLAGS], a
	pop af
	ld [hl], a
	ret

BossAI_FastPrepareReplacementFacts::
; DE=producer context, AV_SLOT=legal bench slot. Native replacement uses
; the authoritative public actor, owned weight, setup flags and entry quota.
; No speeds, replies, ordinary action or HP tables are prepared here.
; Output own actor40 bytes (only HP/max/weight populated), entry-loss bridge,
; setup flags; AD/AV producer prefix is scratch. DE/SP preserved.
	ad_address AV_SLOT
	ld a, [hl]
	ld b, 1
	ld c, STRUGGLE
	call BossAI_BuildOwnedDamageContext
	call BossAI_ValuePublicExchange.ResetHPState
	call BossAI_ValuePublicExchange.SetWeight
	call BossAI_FastExportSetupFlags
	ld hl, FSA_OWN
	ld b, 40
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ad_address AV_OWN_START
	ld a, [hli]
	ld [FSA_START_HP], a
	ld [FSA_ENTRY_HP], a
	ld a, [hl]
	ld [FSA_START_HP + 1], a
	ld [FSA_ENTRY_HP + 1], a
	ad_address AV_OWN_MAX
	ld a, [hli]
	ld [FSA_MAX_HP], a
	ld a, [hl]
	ld [FSA_MAX_HP + 1], a
	ad_address AV_WEIGHT
	ld a, [hl]
	ld [FSA_WEIGHT], a
	ld a, [wEnemyScreens]
	and SCREENS_SPIKES_MASK
	ld b, a
	call BossAI_ContextEntryDamage
	ld a, b
	ld [FSB_ENTRY_LOSS], a
	ld a, c
	ld [FSB_ENTRY_LOSS + 1], a
	ret

; Orchestration bridges: the ordinary selector lives in another bank and marshals
; every input through DE/BC or the context. Each bridge leaves the producer
; prefix in the state the next same-bank helper reads.
DEF FSB_QUICK_CLAW EQU $a48f ; 1 when the active owned actor holds Quick Claw
DEF FSB_REPLY_REGIMES EQU $a490 ; regime mask compiled for the current reply
ASSERT FSB_REPLY_REGIMES < FSB_PREFIX

BossAI_FastPrepareOwnedCandidate::
; DE=context with AV_SLOT/KIND/MOVE/BRANCH supplied, C=plan slot0..3. Prepares
; the candidate epoch (speeds, outgoing template, incoming actor), restores the
; owned outgoing context and compiles the compact plan. Carry=represented; clear
; leaves an explicit fallback plan whose header (accuracy/priority) is valid.
; Live AD is the owned context (direction 1) on return. DE/SP preserved.
	push bc
	call BossAI_PreparePublicAction
	call BossAI_ValuePublicExchange.LoadPreparedOutgoing
	pop bc
	jp BossAI_FastCompileOwnedPlan

BossAI_FastPrepareActiveFacts::
; DE=context. Establishes the active defender's preparation epoch with a
; Struggle carrier of wait kind: speeds and speed mode in AV, incoming actor
; template, AV_WEIGHT, setup flags (a47c), the wait candidate's action-check
; flags (prefix) and the Quick Claw class. The live AD is left as the owned
; Struggle context (direction 1) for actor import. DE/SP preserved.
	ad_address AV_SLOT
	ld [hl], $ff
	ad_address AV_KIND
	ld [hl], AV_WAIT_ACTION
	ad_address AV_MOVE
	ld [hl], STRUGGLE
	ad_address AV_BRANCH
	ld [hl], 0
	call BossAI_PreparePublicAction
	call BossAI_ValuePublicExchange.LoadPreparedOutgoing
	call BossAI_ValuePublicExchange.SetWeight
	call BossAI_FastExportSetupFlags
	ld c, 0
	call BossAI_FastExportActionPrefix
	call BossAI_BuildPublicDamageContext.OwnItem
	cp QUICK_CLAW
	ld a, 0
	jr nz, .item_class
	inc a
.item_class
	ld [FSB_QUICK_CLAW], a
	ret

BossAI_FastPrepareReply::
; DE=context with AV_SLOT/AV_KIND/AV_REPLY (nonzero) set inside the defender's
; prepared epoch; C=mask of HP regimes this reply can reach (bit r). Builds
; the incoming context for the reply directly in the live AD, without the
; prepared-range call or template copy that the prepared evaluator needed,
; then compiles the compact incoming plan for the masked regimes only.
; Carry=represented; clear leaves opcode0 with a valid move/accuracy header.
	push bc
	ad_address AV_REPLY
	ld c, [hl]
	call BossAI_BuildPreparedIncoming
	call BossAI_ValuePublicExchange.MoveReplyPursuit
	pop bc
	jp BossAI_FastCompileReplyPlan.Masked
