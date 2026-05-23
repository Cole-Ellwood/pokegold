; ============================================================
; engine/battle/ai/boss_policy_switch.asm - Boss AI switch-policy guarded fragments
; Split out of boss.asm per docs/boss_ai_organization_plan.md section 3.
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; Included with BOSSAI_EMIT_* guards from main.asm to preserve ROM byte order.
; ============================================================

if DEF(BOSSAI_EMIT_SWITCH_DISPATCH)
; ============================================================
; Region: Switch dispatch
; Concern: Boss switch/item dispatch, candidate scan, confidence dice
; Layer: POLICY
; Original lines: 168
; ============================================================
; ai-layer: POLICY
BossAI_SwitchOrTryItem:
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_ResetTurnCaches
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask
	call BossAI_OracleHakiRead
	ret nz

	call BossAI_EnemyPerishEscapeUrgent
	jr c, .check_switch
	call BossAI_HasAnyKOMove
	jr nc, .check_switch
	call BossAI_IsImminentKOPrevention
	jr c, .check_switch
	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .check_switch
	ret

.check_switch
	call BossAI_CheckAbleToSwitchSafe
	ld a, [wEnemySwitchMonParam]
	and a
	jp z, AI_TryItem
	call BossAI_RefineSwitchCandidateForPlausibleRisk
	ld a, [wEnemySwitchMonParam]
	and a
	jp z, AI_TryItem

	push af
	call BossAI_ComputeSwitchConfidence
	ld [wBossAISwitchConfidence], a
IF DEF(BOSS_AI_TRACE)
	ld [wBossAITraceSwitchConfidence], a
ENDC
	ld b, a ; confidence
	call BossAI_GetSwitchThreshold
	ld c, a ; threshold
	call BossAI_NeedsLoopPenalty
	jr nc, .no_penalty
	ld a, c
	add AI_SWITCH_ANTI_LOOP_PENALTY
	ld c, a
.no_penalty
	call BossAI_ShouldSackInsteadOfSwitch
	jr nc, .no_sack_bias
	ld a, c
	add 8
	ld c, a
.no_sack_bias
	call BossAI_IsSwitchingIntoWinconRisk
	jr nc, .no_wincon_bias
	ld a, c
	add 10
	ld c, a
.no_wincon_bias
	ld a, b
	cp c
	jr c, .stay

; Switch probability based on confidence margin (b - c).
; Margin >= 20: 90% switch (230/256)
; Margin >= 10: 75% switch (192/256)
; Margin <  10: 55% switch (141/256)
	sub c
	ld d, a
	cp 20
	ld a, 230
	jr nc, .switch_roll
	ld a, d
	cp 10
	ld a, 192
	jr nc, .switch_roll
	ld a, 141

.switch_roll
	ld b, a
	call Random
	cp b
	jr nc, .stay

	pop af
	and $f
	inc a
	ld [wEnemySwitchMonIndex], a
	call BossAI_MaybeMarkScoutPivot
	jp AI_TrySwitch

.stay
	pop af
	jp AI_TryItem

; ai-layer: POLICY
BossAI_OracleHakiRead:
; Uniform Haki exception: once per battle, on the ace's first active turn,
; an eligible boss may re-score deterministically against the player's
; already-locked move. This is the only normal Boss AI routine allowed to
; read current-turn input.
	ld hl, wBossAIRevealedMovesBitmapSpare + 1
	bit BOSSAI_HAKI_SPENT_F, [hl]
	jr nz, .no
	bit BOSSAI_HAKI_ELIGIBLE_F, [hl]
	jr z, .no
	ld a, [wEnemyGoesFirst]
	and a
	jr z, .no
	ld a, [wBattlePlayerAction]
	and a
	jr nz, .no
	ld a, [wEnemySubStatus5]
	bit SUBSTATUS_ENCORED, a
	jr nz, .no
	ld a, [wCurPlayerMove]
	and a
	jr z, .no
	call BossAI_ApplyKnownPlayerActionOracleBias
	call BossAI_ChooseBestOracleMove
	jr nc, .no
	callfar EnforceEnemyHeldMoveRestrictions_Far
	callfar UpdateMoveData
	call BossAI_UpdateRepeatTracker
	call BossAI_MarkScoutedIfScoutMove
	call BossAI_QueueHakiTaunt
	ld hl, wBossAIRevealedMovesBitmapSpare + 1
	set BOSSAI_HAKI_SPENT_F, [hl]
	res BOSSAI_HAKI_ELIGIBLE_F, [hl]
IF DEF(BOSS_AI_TRACE)
	ld a, [wCurEnemyMove]
	ld [wBossAITraceChosenMove], a
	ld a, [wBossAITraceRiskFlags]
	or 1 << BOSSAI_HAKI_TRACE_FIRED_F
	ld [wBossAITraceRiskFlags], a
ENDC
	ld a, 1
	and a
	ret

.no
	xor a
	ret

BossAI_ApplyKnownPlayerActionOracleBias:
; Keep the base score model intact, then force only generic emergency
; defensive effects when the locked player move is a strong public threat.
	call BossAI_HakiPlayerSelectedStrongSuperEffectiveAttack
	ret nc
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.bias_loop
	ld a, [de]
	and a
	ret z
	ld a, [hl]
	cp 80
	jr nc, .bias_next
	push hl
	push de
	push bc
	ld a, [de]
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	ld b, a
	pop bc
	pop de
	pop hl
	ld a, b
	cp EFFECT_DESTINY_BOND
	jr z, .force_best
	cp EFFECT_PROTECT
	jr z, .force_best
	cp EFFECT_ENDURE
	jr nz, .bias_next
.force_best
	xor a
	ld [hl], a
.bias_next
	inc hl
	inc de
	dec c
	jr nz, .bias_loop
	ret

BossAI_ChooseBestOracleMove:
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld b, $ff ; best score
	ld c, $ff ; best index
	xor a ; current index
.best_loop
	cp NUM_MOVES
	jr nc, .best_done
	push af
	ld a, [de]
	and a
	jr z, .best_done_pop
	ld a, [hl]
	cp 80
	jr nc, .best_next
	cp b
	jr nc, .best_next
	ld b, a
	pop af
	ld c, a
	push af
.best_next
	pop af
	inc hl
	inc de
	inc a
	jr .best_loop

.best_done_pop
	pop af

.best_done
	ld a, c
	cp $ff
	jr z, .no_best
	ld [wCurEnemyMoveNum], a
	ld c, a
	ld b, 0
	ld hl, wEnemyMonMoves
	add hl, bc
	ld a, [hl]
	ld [wCurEnemyMove], a
	ld a, 1
	ld [wBossAIMoveChoiceReady], a
	scf
	ret
.no_best
	and a
	ret

BossAI_HakiPlayerSelectedStrongSuperEffectiveAttack:
	ld a, [wCurPlayerMove]
	and a
	jr z, .selected_no
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	cp 60
	jr c, .selected_no
	ld a, [wCurPlayerMove]
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	ld c, a
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	ret
.selected_no
	and a
	ret

; ai-layer: POLICY
BossAI_OnSwitchExecuted:
	ld a, [wBossAITier]
	and a
	ret z
	ld a, [wCurOTMon]
	inc a
	ld [wBossAILastSwitchedOut], a
	ld a, AI_SWITCH_COOLDOWN_TURNS
	ld [wBossAISwitchCooldown], a
	xor a
	ld [wBossAIRepeatCount], a
	ld [wBossAILastChosenMove], a
	ret

; ai-layer: POLICY
BossAI_DecaySwitchCooldown:
	ld a, [wBossAISwitchCooldown]
	and a
	ret z
	dec a
	ld [wBossAISwitchCooldown], a
	ret

; ai-layer: POLICY
BossAI_CheckAbleToSwitchSafe:
	xor a
	ld [wEnemySwitchMonParam], a
	call BossAI_FindFirstAliveSwitchCandidate
	ret nc
	call BossAI_PlayerHasPublicThreatVsEnemy
	jr c, .high_confidence
	call AICheckEnemyQuarterHP_HL
	ret c
	ld b, $20
	jr .store

.high_confidence
	ld b, $30

.store
	ld a, [wBossAITemp]
	or b
	ld [wEnemySwitchMonParam], a
	ret

; ai-layer: POLICY
BossAI_FindFirstAliveSwitchCandidate:
; output: carry and wBossAITemp if a living bench candidate exists; clobbers bc, de, hl.
	ld a, [wOTPartyCount]
	cp 2
	jr c, .none
	ld d, a
	ld e, 0
	ld hl, wOTPartyMon1HP

.loop
	ld a, [wCurOTMon]
	cp e
	jr z, .next
	push hl
	ld a, [hli]
	or [hl]
	pop hl
	jr z, .next
	ld a, e
	ld [wBossAITemp], a
	scf
	ret

.next
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	inc e
	dec d
	jr nz, .loop

.none
	and a
	ret

endc
if DEF(BOSSAI_EMIT_SWITCH_THRESHOLD_AND_LOOP)
; Region: Switch threshold + loop penalty
; Concern: Tier threshold, per-class deltas, and loop-penalty gates
; Layer: POLICY
; Original lines: 117
; ============================================================
; ai-layer: POLICY
BossAI_GetSwitchThreshold:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, AI_SWITCH_THRESHOLD_LATE
	jr z, .base_done
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ld a, AI_SWITCH_THRESHOLD_MID
	jr z, .base_done
	ld a, AI_SWITCH_THRESHOLD_EARLY
 
.base_done
	call .ApplyClassSwitchThresholdMod
	ret

.ApplyClassSwitchThresholdMod
	ld b, a
	ld a, [wTrainerClass]
	cp CHAMPION
	jr z, .minus_10
	cp KOGA
	jr z, .minus_8
	cp CLAIR
	jr z, .minus_6
	cp KAREN
	jr z, .minus_4
	cp BRUNO
	jr z, .minus_4
	cp JASMINE
	jr z, .plus_4
	cp CHUCK
	jr z, .plus_2
	ld a, b
	ret

.minus_10
	ld a, b
	sub 10
	ret nc
	xor a
	ret

.minus_8
	ld a, b
	sub 8
	ret nc
	xor a
	ret

.minus_6
	ld a, b
	sub 6
	ret nc
	xor a
	ret

.minus_4
	ld a, b
	sub 4
	ret nc
	xor a
	ret

.plus_4
	ld a, b
	add 4
	cp 96
	ret c
	ld a, 95
	ret

.plus_2
	ld a, b
	add 2
	cp 96
	ret c
	ld a, 95
	ret

; ai-layer: POLICY
BossAI_NeedsLoopPenalty:
	ld a, [wBossAISwitchCooldown]
	and a
	jr z, .no_penalty
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld b, a
	ld a, [wBossAILastSwitchedOut]
	cp b
	jr z, .check_exceptions
	ld a, [wCurOTMon]
	inc a
	ld b, a
	ld a, [wBossAILastSwitchedOut]
	cp b
	jr nz, .no_penalty

.check_exceptions
; Public threat creates many normal switch candidates. Only a real emergency
; should waive the anti-loop penalty, or A->B->A pivots never pay the cost.
	call AICheckEnemyQuarterHP_HL
	jr nc, .no_penalty
	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .no_penalty
	call BossAI_EnemyPerishEscapeUrgent
	jr c, .no_penalty
	call BossAI_IsImmunityPivotOpportunity
	jr c, .no_penalty
	call BossAI_AceTimingHook
	jr c, .no_penalty

	scf
	ret

.no_penalty
	and a
	ret

endc

if DEF(BOSSAI_EMIT_SWITCH_REASON_PREDICATES)
; ============================================================
; Region: Switch reason predicates
; Concern: KO-prevention, Perish escape, and revenge-respect predicates
; Layer: POLICY
; Original lines: 81
; ============================================================
; ai-layer: POLICY
BossAI_IsImminentKOPrevention:
	call AICheckEnemyQuarterHP_HL
	jr nc, .yes
	call BossAI_PlayerHasPublicThreatVsEnemy
	jr c, .yes
	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .yes
	and a
	ret
.yes
	scf
	ret

; ai-layer: POLICY
BossAI_EnemyPerishEscapeUrgent:
	ld a, [wEnemySubStatus1]
	bit SUBSTATUS_PERISH, a
	jr z, .no
	ld a, [wEnemyPerishCount]
	cp 3
	jr nc, .no
	and a
	jr z, .no
	scf
	ret
.no
	and a
	ret

; ai-layer: POLICY
BossAI_ShouldRespectPotentialPlayerRevenge:
; Carry if the player is likely to threaten a fast revenge KO line.
	call BossAI_PublicEnemyFaster
	jr nc, .check_threat
	call BossAI_PlayerHasRevealedPriorityThreat
	jr c, .yes
	jr .check_seen_revenge

.check_threat
	call BossAI_GetPrimaryThreatType
	jr nc, .check_seen_revenge
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	cp 3
	jr c, .check_seen_revenge

	call AICheckEnemyHalfHP_HL
	jr nc, .yes
	call BossAI_HasRevealedSuperEffectiveMove
	jr c, .yes
	call BossAI_IsSuspiciousSwitchIn
	jr nc, .no
	call AICheckEnemyQuarterHP_HL
	jr nc, .yes

.check_seen_revenge
	call .KnownSeenRevengeThreat
	jr c, .yes

.no
	and a
	ret

.yes
	scf
	ret

.KnownSeenRevengeThreat
	ld a, [wBossAITier]
	cp AI_TIER_MID
	jr c, .seen_no
	call BossAI_SeenBenchThreatScore
	cp 20
	jr nc, .seen_yes
	cp 10
	jr c, .seen_no
	call AICheckEnemyHalfHP_HL
	jr nc, .seen_yes
.seen_no
	and a
	ret
.seen_yes
	scf
	ret

endc

if DEF(BOSSAI_EMIT_SWITCH_IN_CLASSIFIERS)
; ============================================================
; Region: Switch-in classifiers
; Concern: Scarf-swing stub, suspicious switch-in, immunity-pivot checks
; Layer: POLICY
; Original lines: 107
; ============================================================
; ai-layer: POLICY
BossAI_IsScarfSwingPossible:
; Do not infer unrevealed player Choice Scarf from private speed values.
	and a
	ret

; ai-layer: POLICY
BossAI_IsSuspiciousSwitchIn:
; Carry when the fresh switch-in looks like a coverage/pivot line instead of natural STAB pressure.
	ld a, [wBossAITurnsElapsed]
	and a
	jr z, .no
	ld a, [wPlayerTurnsTaken]
	and a
	jr nz, .no

	ld a, [wBattleMonType1]
	call .IsTypeNotVeryEffective
	jr nc, .no

	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	jr z, .yes
	ld a, c
	call .IsTypeNotVeryEffective
	jr nc, .no

.yes
	scf
	ret

.no
	and a
	ret

.IsTypeNotVeryEffective
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr c, .nve
	and a
	ret
.nve
	scf
	ret

; ai-layer: POLICY
BossAI_IsImmunityPivotOpportunity:
	ld a, [wLastPlayerCounterMove]
	and a
	ret z
	ld b, a
	ld a, [wCurSpecies]
	push af
	ld a, b
	push af
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .no

	ld a, [wEnemySwitchMonParam]
	and $f
	ld c, a
	ld b, 0
	ld hl, wOTPartySpecies
	add hl, bc
	ld a, [hl]
	and a
	jr z, .no
	cp $ff
	jr z, .no
	ld [wCurSpecies], a
	call GetBaseData
	pop af
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	inc hl
	call BossAI_GetMoveByte
	call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem
	ld a, [wTypeMatchup]
	and a
	jr nz, .not_immune
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	scf
	ret

.not_immune
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	and a
	ret

.no
	pop af
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	and a
	ret

endc

if DEF(BOSSAI_EMIT_SWITCH_ACE_AND_CONFIDENCE)
; ============================================================
; Region: Ace timing + switch confidence
; Concern: Ace timing hook and switch-confidence calculation
; Layer: POLICY
; Original lines: 117
; ============================================================
; ai-layer: POLICY
BossAI_AceTimingHook:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr nz, .no

	ld a, [wTrainerClass]
	cp CLAIR
	jr z, .check_slot
	cp WILL
	jr z, .check_slot
	cp BRUNO
	jr z, .check_slot
	cp KAREN
	jr z, .check_slot
	cp KOGA
	jr z, .check_slot
	cp CHAMPION
	jr nz, .no

.check_slot
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	jr nz, .no

	ld a, [wBossAITurnsElapsed]
	cp 5
	jr nc, .yes

	call AICheckEnemyHalfHP_HL
	jr nc, .yes
	call AICheckPlayerHalfHP_HL
	jr nc, .yes

.no
	and a
	ret

.yes
	scf
	ret

; ai-layer: POLICY
BossAI_ComputeSwitchConfidence:
	ld a, [wEnemySwitchMonParam]
	and $f0
	cp $30
	ld a, 90
	jr z, .base_done
	ld a, [wEnemySwitchMonParam]
	and $f0
	cp $20
	ld a, 78
	jr z, .base_done
	ld a, 65

.base_done
	ld [wBossAISwitchConfidence], a
	call BossAI_HasAnyKOMove
	jr nc, .no_ko_discount
	ld a, [wBossAISwitchConfidence]
	sub 18
	jr nc, .store_ko_discount
	xor a
.store_ko_discount
	ld [wBossAISwitchConfidence], a
.no_ko_discount
	call AICheckEnemyQuarterHP_HL
	jr c, .no_hp_bonus
	ld a, [wBossAISwitchConfidence]
	add 10
	ld [wBossAISwitchConfidence], a
.no_hp_bonus
	call BossAI_AceTimingHook
	jr nc, .no_ace_bonus
	ld a, [wBossAISwitchConfidence]
	add 12
	ld [wBossAISwitchConfidence], a
.no_ace_bonus
	call BossAI_EnemyPerishEscapeUrgent
	jr nc, .no_perish_bonus
	ld a, [wBossAISwitchConfidence]
	add 40
	cp 100
	jr c, .store_perish_bonus
	ld a, 99
.store_perish_bonus
	ld [wBossAISwitchConfidence], a
.no_perish_bonus

	call BossAI_PredictPlayerSwitch
	ld c, a ; player switch chance
	srl a
	srl a
	ld d, a
	ld a, [wBossAISwitchConfidence]
	add d
	ld [wBossAISwitchConfidence], a

	ld a, [wBossAISwitchConfidence]
	ld b, a
	call BossAI_ApplyPlausibleRiskToSwitchConfidence
	ld b, a
	call BossAI_ApplyPlanSwitchBias
	ld b, a
	call BossAI_ApplyPreservationSwitchBias
	ld b, a
	ld a, b
	cp 100
	ret c
	ld a, 99
	ret

endc

if DEF(BOSSAI_EMIT_SWITCH_CANDIDATE_RISK_REFINEMENT)
; ============================================================
; Region: Switch-candidate risk refinement
; Concern: Candidate risk scoring and plausible-risk tie-breaks
; Layer: POLICY
; Original lines: 372
; ============================================================
; ai-layer: POLICY
BossAI_RefineSwitchCandidateForPlausibleRisk:
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld [wBossAITemp], a
	call BossAI_ComputeSwitchCandidateRisk
	ld [wBossAITemp2], a
	ld [wBossAITemp4], a
	ld a, [wBossAITemp]
	ld [wBossAITemp3], a

	xor a
	ld [wBossAITargetMonIdx], a
	ld [wBossAITemp5], a
.scan_loop
	ld a, [wBossAITargetMonIdx]
	ld c, a
	ld a, [wOTPartyCount]
	cp c
	jr z, .done
	jr c, .done
	ld a, [wBossAITemp5]
	cp BOSS_AI_SWITCH_CANDIDATE_CAP
	jr nc, .done
	ld a, [wCurOTMon]
	cp c
	jr z, .next

	ld hl, wOTPartyMon1HP
	ld a, c
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld a, [hli]
	or [hl]
	jr z, .next

	ld a, [wBossAITemp5]
	inc a
	ld [wBossAITemp5], a

	ld a, [wBossAITargetMonIdx]
	inc a
	call BossAI_ComputeSwitchCandidateRisk
	ld c, a
	ld a, [wBossAITemp4]
	cp c
	jr c, .next
	jr z, .next
	ld a, c
	ld [wBossAITemp4], a
	ld a, [wBossAITargetMonIdx]
	inc a
	ld [wBossAITemp3], a

.next
	ld a, [wBossAITargetMonIdx]
	inc a
	ld [wBossAITargetMonIdx], a
	jr .scan_loop

.done
	ld a, [wBossAITemp3]
	ld b, a
	ld a, [wBossAITemp]
	cp b
	ret z
	ld a, [wBossAITemp4]
	add 2
	ld b, a
	ld a, [wBossAITemp2]
	cp b
	ret c
	ret z
	ld a, [wEnemySwitchMonParam]
	and $f0
	ld b, a
	ld a, [wBossAITemp3]
	dec a
	or b
	ld [wEnemySwitchMonParam], a
	ret

; ai-layer: POLICY
BossAI_ComputeSwitchCandidateRisk:
	ld c, a
	ld a, [wCurSpecies]
	push af
	dec c
	ld b, 0
	ld hl, wOTPartySpecies
	add hl, bc
	ld a, [hl]
	and a
	jp z, .hard_risk
	cp $ff
	jp z, .hard_risk
	ld [wCurSpecies], a
	push bc
	call GetBaseData
	pop de

	ld b, 0
	call .ApplyRevealedPrioritySwitchInRisk
	ld a, [wBattleMonType1]
	ld d, 4
	call .AddTypeRisk
	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	jr z, .mask_risk
	ld a, c
	ld d, 4
	call .AddTypeRisk

.mask_risk
	call BossAI_GetTierPlausibleRiskWeight
	ld d, a
	ld hl, BossAI_PlausibleThreatTypes
.likely_mask_loop
	ld a, [hli]
	cp -1
	jr z, .possible_mask_risk
	ld c, a
	push hl
	ld a, c
	call BossAI_TestLikelyMaskBit
	pop hl
	jr nc, .likely_mask_loop
	ld a, c
	call .AddTypeRisk
	jr .likely_mask_loop

.possible_mask_risk
	call BossAI_GetSpeculativePlausibleRiskWeight
	ld d, a
	ld hl, BossAI_PlausibleThreatTypes
.possible_mask_loop
	ld a, [hli]
	cp -1
	jr z, .hp_risk
	ld c, a
	push hl
	ld a, c
	call BossAI_TestPlausibleMaskBit
	pop hl
	jr nc, .possible_mask_loop
	push hl
	ld a, c
	call BossAI_TestLikelyMaskBit
	pop hl
	jr c, .possible_mask_loop
	ld a, c
	call .AddTypeRisk
	jr .possible_mask_loop

.hp_risk
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestLikelyMaskBit
	jr nc, .possible_hp_risk
	call BossAI_GetTierPlausibleRiskWeight
	ld d, a
	call .AddHiddenPowerTypeRisk

.possible_hp_risk
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestLikelyMaskBit
	jr c, .immunity_tiebreak
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestPlausibleMaskBit
	jr nc, .immunity_tiebreak
	call BossAI_GetSpeculativePlausibleRiskWeight
	ld d, a
	call .AddHiddenPowerTypeRisk
	jr .immunity_tiebreak

.AddHiddenPowerTypeRisk
	ld hl, BossAIHiddenPowerThreatTypes
	ld e, 0
.hp_loop
	ld a, [hli]
	cp -1
	jr z, .hp_done
	push hl
	push de
	call .GetTypeRiskPoints
	pop de
	pop hl
	cp e
	jr c, .hp_loop
	ld e, a
	jr .hp_loop
.hp_done
	ld a, b
	add e
	ld b, a
	ret

.immunity_tiebreak
	call .ApplyPrimaryThreatImmunityTieBreak

.done
	ld a, b
	cp 100
	jr c, .restore_return
	ld a, 99
	jr .restore_return

.hard_risk
	ld a, 99
.restore_return
	ld b, a
	pop af
	ld [wCurSpecies], a
	and a
	jr z, .restored
	push bc
	call GetBaseData
	pop bc
.restored
	ld a, b
	ret

.ApplyPrimaryThreatImmunityTieBreak
	ld a, [wBossAITemp]
	push af
	push bc
	call BossAI_GetPrimaryThreatType
	jr nc, .restore_no_penalty
	ld c, a
	ldh a, [hBattleTurn]
	push af
	xor a
	ldh [hBattleTurn], a
	ld a, c
	ld hl, wBaseType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	ld a, [wTypeMatchup]
	and a
	jr z, .restore_no_penalty
	pop bc
	ld a, b
	add 3
	ld b, a
	pop af
	ld [wBossAITemp], a
	ret

.restore_no_penalty
	pop bc
	pop af
	ld [wBossAITemp], a
	ret

.ApplyRevealedPrioritySwitchInRisk
; e = zero-based switch candidate index, b = accumulated candidate risk.
	call .CandidateAtHalfHP
	ret c
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.priority_loop
	ld a, [hli]
	and a
	ret z
	push hl
	push bc
	ld e, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_PRIORITY_HIT
	jr nz, .priority_next
	ld a, e
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .priority_next
	ld a, e
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr c, .priority_next
	pop bc
	pop hl
	ld a, b
	add 3
	ld b, a
	ret

.priority_next
	pop bc
	pop hl
	dec c
	jr nz, .priority_loop
	ret

.CandidateAtHalfHP
	push hl
	push de
	push bc
	ld hl, wOTPartyMon1HP
	ld d, 0
	ld a, e
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld b, [hl]
	inc hl
	ld c, [hl]
	sla c
	rl b
	inc hl
	inc hl
	ld a, [hld]
	cp c
	ld a, [hl]
	sbc b
	pop bc
	pop de
	pop hl
	ret

.AddTypeRisk
	call .GetTypeRiskPoints
	ld e, a
	ld a, b
	add e
	ld b, a
	ret

.GetTypeRiskPoints
	push hl
	push bc
	ld c, a
	ldh a, [hBattleTurn]
	push af
	xor a
	ldh [hBattleTurn], a
	ld a, c
	ld hl, wBaseType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	pop bc
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 4
	jr nc, .quad
	cp EFFECTIVE * 2
	jr nc, .double
	and a
	jr z, .immune
	xor a
	ret

.quad
	ld a, d
	add d
	ret

.double
	ld a, d
	ret

.immune
	xor a
	ret

endc

if DEF(BOSSAI_EMIT_SWITCH_CONFIDENCE_FINALIZATION)
; ============================================================
; Region: Switch-confidence finalization
; Concern: Plausible-risk confidence, plan switch bias, sack/wincon gates
; Layer: POLICY
; Original lines: 131
; ============================================================
; ai-layer: POLICY
BossAI_ApplyPlausibleRiskToSwitchConfidence:
	ld a, b
	ld [wBossAISwitchConfidence], a
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	call BossAI_ComputeSwitchCandidateRisk
	ld [wBossAITemp2], a
	srl a
	ld [wBossAITemp3], a

	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .apply_penalty
	call BossAI_IsSuspiciousSwitchIn
	jr c, .medium_penalty
	call BossAI_HasRevealedSuperEffectiveMove
	jr c, .medium_penalty
	ld a, [wBossAITemp3]
	srl a
	ld [wBossAITemp3], a
	jr .apply_penalty

.medium_penalty
	ld a, [wBossAITemp3]
	srl a
	ld c, a
	ld a, [wBossAITemp3]
	sub c
	ld [wBossAITemp3], a

.apply_penalty
	ld a, [wBossAITemp3]
	ld c, a
	ld a, [wBossAISwitchConfidence]
	sub c
	jr nc, .safe_bonus
	xor a
.safe_bonus
	ld c, a
	ld a, [wBossAITemp2]
	cp 3
	jr nc, .store
	ld a, c
	add 6
	ld c, a
.store
	ld a, c
	cp 100
	ret c
	ld a, 99
	ret

; ai-layer: POLICY
BossAI_ApplyPlanSwitchBias:
	ld a, [wBossAIPlanId]
	and a
	jr z, .base
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld c, a
	ld a, [wBossAIWinconMonIdx]
	cp c
	jr nz, .not_wincon
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .plan_protect
	ld a, b
	add 6
	jr .cap
.plan_protect
	cp BOSS_PLAN_ENDGAME_PROTECT
	jr nz, .base
	ld a, b
	sub 6
	jr nc, .cap
	xor a
	jr .cap
.not_wincon
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_ENDGAME_PROTECT
	jr nz, .base
	ld a, b
	add 4
	jr .cap
.base
	ld a, b
.cap
	cp 100
	ret c
	ld a, 99
	ret

; ai-layer: POLICY
BossAI_ApplyPreservationSwitchBias:
	ld a, [wCurOTMon]
	inc a
	ld c, a
	ld a, [wBossAIWinconMonIdx]
	cp c
	jr nz, .base
	call BossAI_HasAnyKOMove
	jr c, .base
	call BossAI_PlayerHasPublicThreatVsEnemy
	jr nc, .base
	ld a, b
	add 10
	jr .cap
.base
	ld a, b
.cap
	cp 100
	ret c
	ld a, 99
	ret

; ai-layer: POLICY
BossAI_ShouldSackInsteadOfSwitch:
	call AICheckEnemyQuarterHP_HL
	jr c, .no
	call BossAI_HasAnyKOMove
	jr c, .no
	ld a, [wCurOTMon]
	inc a
	ld b, a
	ld a, [wBossAIWinconMonIdx]
	cp b
	jr z, .no
	scf
	ret
.no
	and a
	ret

; ai-layer: POLICY
BossAI_IsSwitchingIntoWinconRisk:
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld b, a
	ld a, [wBossAIWinconMonIdx]
	cp b
	jr nz, .no
	ld a, b
	call BossAI_ComputeSwitchCandidateRisk
	ld b, a
	call BossAI_GetTierPlausibleRiskWeight
	add 2
	cp b
	jr c, .yes
	jr z, .yes
.no
	and a
	ret
.yes
	scf
	ret

endc
