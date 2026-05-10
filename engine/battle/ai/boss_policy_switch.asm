; ============================================================
; engine/battle/ai/boss_policy_switch.asm — Switch predicates, confidence, prediction, held-item, plan, and mask block
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================

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

	ld a, c
	cp 20
	jr c, .done

.done
	ld a, [wBossAISwitchConfidence]
	ld b, a
	call BossAI_ApplyPlausibleRiskToSwitchConfidence
	ld b, a
	call BossAI_ApplyPlanSwitchBias
	ld b, a
	ld a, b
	cp 100
	ret c
	ld a, 99
	ret

; ============================================================
; Region: Predict-player-switch + revealed-SE-move
; Concern: Player switch prediction and revealed super-effective probe
; Layer: POLICY
; Original lines: 114
; ============================================================
; ai-layer: POLICY
BossAI_PredictPlayerSwitch:
; Not separately memoized: its two heavy internal calls
; (PlayerHasPublicThreatVsEnemy, HasRevealedSuperEffectiveMove via the cached
; public threat helper) hit the per-tick cache, so this routine's per-call
; cost is already collapsed.
	ld a, 10
	ld [wBossAITemp], a

	ld a, [wBossAITurnsElapsed]
	and a
	jr z, .switch_rate_done
	ld c, a
	ld a, [wBossAIPlayerSwitchCount]
	and a
	jr z, .switch_rate_done
	add a
	cp c
	jr c, .small_rate
	ld a, [wBossAITemp]
	add 20
	ld [wBossAITemp], a
	jr .switch_rate_done

.small_rate
	ld a, [wBossAITemp]
	add 10
	ld [wBossAITemp], a

.switch_rate_done
	call AICheckPlayerQuarterHP_HL
	jr c, .hp_done
	ld a, [wBossAITemp]
	add 20
	ld [wBossAITemp], a
.hp_done

	call BossAI_PlayerHasPublicThreatVsEnemy
	jr nc, .done
	ld a, [wBossAITemp]
	add 15
	ld [wBossAITemp], a

	call BossAI_HasRevealedSuperEffectiveMove
	jr nc, .done
	ld a, [wBossAITemp]
	sub 10
	jr nc, .set_switch_rate
	xor a
.set_switch_rate
	ld [wBossAITemp], a

.done
	ld a, [wBossAITemp]
	cp 80
	ret c
	ld a, 80
	ret

; ai-layer: POLICY
BossAI_HasRevealedSuperEffectiveMove:
	call BossAI_GetActiveSpeciesRevealedMaskPointer
	jr nc, .no
	ld a, l
	ld [wBossAITemp4], a
	ld a, h
	ld [wBossAITemp5], a

	ld hl, BossAI_PlausibleThreatTypes
.type_loop
	ld a, [hli]
	cp -1
	jr z, .hidden_power
	ld c, a
	push hl
	call BossAI_TestRevealedSpeciesMaskBit
	pop hl
	jr nc, .type_loop
	push hl
	ld a, c
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .type_loop
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr c, .type_loop
	scf
	ret

.hidden_power
	ld c, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestRevealedSpeciesMaskBit
	jr nc, .no
	ld hl, BossAIHiddenPowerThreatTypes
.hp_loop
	ld a, [hli]
	cp -1
	jr z, .no
	ld c, a
	push hl
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .hp_loop
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr c, .hp_loop
	scf
	ret

.no
	and a
	ret

; ============================================================
; Region: Cache misses (passive)
; Concern: Revealed-species bit test and uncached KO-move probe
; Layer: PLATFORM
; Original lines: 94
; ============================================================
; ai-layer: PLATFORM
BossAI_TestRevealedSpeciesMaskBit:
	ld a, c
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld a, [wBossAITemp4]
	ld l, a
	ld a, [wBossAITemp5]
	ld h, a
	add hl, de
	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.test_loop
	ld a, e
	and a
	jr z, .test
	sla d
	dec e
	jr .test_loop
.test
	ld a, [hl]
	and d
	jr z, .not_set
	scf
	ret
.not_set
	and a
	ret

; ai-layer: PLATFORM
BossAI_HasAnyKOMove:
	ld a, [wBossAIHasKOMoveCache]
	inc a
	jr z, .miss
	dec a
	rrca
	ret
.miss
	call BossAI_HasAnyKOMoveUncached
	push af
	sbc a, a
	and 1
	ld [wBossAIHasKOMoveCache], a
	pop af
	ret

; ai-layer: PLATFORM
BossAI_HasAnyKOMoveUncached:
	call BossAI_SaveEnemyMoveStruct
	call BossAI_EnemyChoiceLockedMove
	jr nc, .scan_all_moves
	call AIGetEnemyMove_HL
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .no
	call BossAI_CurrentEnemyMoveHasKOPressure
	jr nc, .no
	call BossAI_RestoreEnemyMoveStruct
	scf
	ret
.scan_all_moves
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	jr z, .no
	push bc
	push de
	call AIGetEnemyMove_HL
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .next
	call BossAI_CurrentEnemyMoveHasKOPressure
	jr nc, .next
	pop de
	pop bc
	call BossAI_RestoreEnemyMoveStruct
	scf
	ret
.next
	pop de
	pop bc
	inc de
	dec c
	jr nz, .loop
.no
	call BossAI_RestoreEnemyMoveStruct
	and a
	ret

; ============================================================
; Region: Held-item helpers
; Concern: Held-effect reads, Choice-lock probes, and move-struct save/restore
; Layer: PLATFORM
; Original lines: 57
; ============================================================
; ai-layer: PLATFORM
BossAI_GetEnemyHeldEffect:
	push bc
	ld a, [wEnemyMonItem]
	ld b, a
	callfar GetItemHeldEffect
	ld a, b
	pop bc
	ret

; ai-layer: PLATFORM
BossAI_EnemyChoiceLockedMove:
	ld a, [wEnemyChoiceLockedMove]
	and a
	ret z
	ld e, a
	call BossAI_GetEnemyHeldEffect
	call BossAI_IsChoiceHeldEffect
	jr nz, .not_choice_locked
	ld a, e
	scf
	ret
.not_choice_locked
	and a
	ret

; ai-layer: PLATFORM
BossAI_IsChoiceHeldEffect:
	cp HELD_CHOICE_BAND
	ret z
	cp HELD_CHOICE_SPECS
	ret z
	cp HELD_CHOICE_SCARF
	ret

; ai-layer: PLATFORM
BossAI_SaveEnemyMoveStruct:
	push hl
	push de
	push bc
	ld hl, wEnemyMoveStruct
	ld de, wBossAISavedEnemyMoveStruct
	ld bc, MOVE_LENGTH
	call CopyBytes
	pop bc
	pop de
	pop hl
	ret

; ai-layer: PLATFORM
BossAI_RestoreEnemyMoveStruct:
	push hl
	push de
	push bc
	ld hl, wBossAISavedEnemyMoveStruct
	ld de, wEnemyMoveStruct
	ld bc, MOVE_LENGTH
	call CopyBytes
	pop bc
	pop de
	pop hl
	ret

; ============================================================
; Region: Bench threat score
; Concern: Seen bench threat scoring
; Layer: POLICY
; Original lines: 81
; ============================================================
; ai-layer: POLICY
BossAI_SeenBenchThreatScore:
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .none
	ld c, a
	ld a, [wCurSpecies]
	push af
	ld a, [wBossAISeenPlayerAliveMask]
	ld [wBossAITemp5], a
	ld hl, wBossAISeenPlayerSpecies
	ld b, 0
.loop
	ld a, [hli]
	and a
	jr z, .next
	ld e, a
	ld a, [wBossAITemp5]
	bit 0, a
	jr z, .next
	ld a, [wBattleMonSpecies]
	cp e
	jr z, .next
	ld a, e
	ld [wCurSpecies], a
	call GetBaseData

	ld a, [wBaseType1]
	ld d, a
	push hl
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr nc, .favorable

	ld a, [wBaseType2]
	cp d
	jr z, .next
	push hl
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .next

.favorable
	inc b

.next
	ld a, [wBossAITemp5]
	srl a
	ld [wBossAITemp5], a
	dec c
	jr nz, .loop

	ld a, b
	and a
	jr z, .restore_return
	add a
	add a
	add b
	add a
	jr .restore_return

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

.none
	xor a
	ret

; ============================================================
; Region: Plan selection
; Concern: Initial/adaptive plan selection and decay
; Layer: POLICY
; Original lines: 178
; ============================================================
DEF BOSS_ROLE_SETUP EQU 0
DEF BOSS_ROLE_STATUS EQU 1
DEF BOSS_ROLE_DENIAL EQU 2

; ai-layer: POLICY
BossAI_SelectPlanIfNeeded:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBossAIPlanId]
	and a
	jr nz, .adapt
	call .ChooseInitialPlan
	ld hl, wBossAIPlanPhase
	set 7, [hl]
	jr .trace

.adapt
	ld hl, wBossAIPlanPhase
	bit 7, [hl]
	jr nz, .trace
	call .AdaptPlan
	ld hl, wBossAIPlanPhase
	set 7, [hl]

.trace
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAIPlanId]
	ld [wBossAITracePlanId], a
	ld a, [wBossAIPlanPhase]
	and $7f
	ld [wBossAITracePlanPhase], a
	ld a, [wBossAIPlanConfidence]
	ld [wBossAITracePlanConfidence], a
ENDC
	ret

.ChooseInitialPlan
	ld a, BOSS_PLAN_TEMPO_PRESSURE
	ld [wBossAIPlanId], a
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, 64
	jr c, .base_conf
	ld a, 80
.base_conf
	ld [wBossAIPlanConfidence], a
	xor a
	ld [wBossAIPlanPhase], a
	ld a, [wCurOTMon]
	inc a
	ld [wBossAIWinconMonIdx], a
	xor a
	ld [wBossAITargetMonIdx], a

	ld a, BOSS_ROLE_SETUP
	call BossAI_FindPartyMonByRole
	jr nc, .check_status_role
	ld [wBossAIWinconMonIdx], a
	ld a, BOSS_PLAN_SETUP_SWEEP
	ld [wBossAIPlanId], a
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, 76
	jr c, .store_conf
	ld a, 88
	jr .store_conf

.check_status_role
	ld a, BOSS_ROLE_STATUS
	call BossAI_FindPartyMonByRole
	jr nc, .check_denial_role
	ld [wBossAIWinconMonIdx], a
	ld a, BOSS_PLAN_STATUS_CHOKE
	ld [wBossAIPlanId], a
	ld a, 72
	jr .store_conf

.check_denial_role
	ld a, BOSS_ROLE_DENIAL
	call BossAI_FindPartyMonByRole
	jr nc, .late_default
	ld [wBossAIWinconMonIdx], a
	ld a, BOSS_PLAN_ANTI_SETUP_DENIAL
	ld [wBossAIPlanId], a
	ld a, 74
	jr .store_conf

.late_default
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr c, .store_conf
	ld a, BOSS_PLAN_WALLBREAK_THEN_CLEAN
	ld [wBossAIPlanId], a
	ld a, 84

.store_conf
	ld [wBossAIPlanConfidence], a
	call BossAI_GetActiveSpeciesSeenIndex
	ld [wBossAITargetMonIdx], a
	ret

.AdaptPlan
	call .IsWinconCompromised
	jr nc, .check_revealed
	ld a, BOSS_PLAN_ENDGAME_PROTECT
	ld [wBossAIPlanId], a
	ld a, 48
	ld [wBossAIPlanConfidence], a
	ret

.check_revealed
	call BossAI_HasRevealedSuperEffectiveMove
	jr nc, .check_decay
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .drop_confidence
	ld a, BOSS_PLAN_WALLBREAK_THEN_CLEAN
	ld [wBossAIPlanId], a
.drop_confidence
	ld a, [wBossAIPlanConfidence]
	sub 8
	jr nc, .store_drop
	ld a, 32
.store_drop
	ld [wBossAIPlanConfidence], a
	ret

.check_decay
	ld a, [wBossAIPlanPhase]
	cp BOSS_AI_PARANOIA_DECAY_TURNS
	ret c
	ld a, [wBossAIPlanConfidence]
	cp 95
	ret nc
	add 2
	ld [wBossAIPlanConfidence], a
	ret

.IsWinconCompromised
	ld a, [wBossAIWinconMonIdx]
	and a
	ret z
	dec a
	ld e, a

	ld hl, wOTPartyMon1Status
	ld a, e
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld a, [hl]
	and a
	jr nz, .yes

	ld hl, wOTPartyMon1HP
	ld a, e
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld b, [hl]
	inc hl
	ld c, [hl]
	sla c
	rl b
	sla c
	rl b
	inc hl
	inc hl
	ld a, [hld]
	cp c
	ld a, [hl]
	sbc b
	jr nc, .yes
	and a
	ret

.yes
	scf
	ret

; ============================================================
; Region: Party-by-role
; Concern: Find party mon by role tag
; Layer: POLICY
; Original lines: 83
; ============================================================
; ai-layer: POLICY
BossAI_FindPartyMonByRole:
	ld [wTempByteValue], a
	ld a, [wOTPartyCount]
	ld d, a
	ld e, 0
.mon_loop
	ld a, d
	and a
	jr z, .not_found
	ld a, e
	ld c, a
	ld b, 0
	ld hl, wOTPartySpecies
	add hl, bc
	ld a, [hl]
	and a
	jr z, .next_mon
	cp $ff
	jr z, .next_mon

	ld hl, wOTPartyMon1Moves
	ld a, e
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld b, NUM_MOVES
.move_loop
	ld a, [hli]
	and a
	jr z, .next_mon
	push hl
	push de
	push bc
	call AIGetEnemyMove_HL
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld c, a
	ld a, [wTempByteValue]
	cp BOSS_ROLE_SETUP
	jr nz, .check_status
	ld a, c
	call BossAI_IsSetupEffect
	jr c, .found
	jr .restore_move

.check_status
	cp BOSS_ROLE_STATUS
	jr nz, .check_denial
	ld a, c
	call BossAI_IsStatusEffect
	jr c, .found
	jr .restore_move

.check_denial
	ld a, c
	call BossAI_IsDenialEffect
	jr c, .found

.restore_move
	pop bc
	pop de
	pop hl
	dec b
	jr nz, .move_loop
	jr .next_mon

.found
	pop bc
	pop de
	pop hl
	ld a, e
	inc a
	scf
	ret

.next_mon
	inc e
	dec d
	jr .mon_loop

.not_found
	xor a
	and a
	ret

; ============================================================
; Region: Setup / status / denial classifiers
; Concern: Setup, status, denial, and affordability classifiers
; Layer: POLICY
; Original lines: 246
; ============================================================
; ai-layer: POLICY
BossAI_IsSetupEffect:
	cp EFFECT_DRAGON_DANCE
	jr z, .yes
	cp EFFECT_CALM_MIND
	jr z, .yes
	cp EFFECT_QUIVER_DANCE
	jr z, .yes
	cp EFFECT_RAIN_DANCE
	jr z, .yes
	cp EFFECT_SUNNY_DAY
	jr z, .yes
	cp EFFECT_ATTACK_UP
	jr c, .no
	cp EFFECT_EVASION_UP + 1
	jr c, .yes
	cp EFFECT_ATTACK_UP_2
	jr c, .no
	cp EFFECT_EVASION_UP_2 + 1
	jr c, .yes
.no
	and a
	ret
.yes
	scf
	ret

; ai-layer: POLICY
BossAI_IsCurrentEnemySetupMove:
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_CURSE
	jr z, .curse
	jp BossAI_IsSetupEffect

.curse
	call BossAI_EnemyIsGhostType
	jr c, .no
	scf
	ret

.no
	and a
	ret

; ai-layer: POLICY
BossAI_SetupBoostHasFurtherValue:
; Returns carry if the targeted stat for the current setup move is below
; MAX_STAT_LEVEL on the active enemy mon (i.e., further boosting is still
; useful). Multi-stat boosts return carry if ANY of the relevant stats can
; still rise. Weather (Rain Dance / Sunny Day) and Focus Energy always
; return carry. Used to gate SETUP_SWEEP plan setup encouragement.
	push hl
	push bc
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]

	cp EFFECT_RAIN_DANCE
	jp z, .yes
	cp EFFECT_SUNNY_DAY
	jp z, .yes
	cp EFFECT_FOCUS_ENERGY
	jp z, .yes
	cp EFFECT_DRAGON_DANCE
	jp z, .check_atk_or_spd
	cp EFFECT_CALM_MIND
	jp z, .check_satk_or_sdef
	cp EFFECT_QUIVER_DANCE
	jp z, .check_quiver_dance
	cp EFFECT_CURSE
	jp z, .check_curse

; Speed boosts get a tighter rule than other stats. Speed is binary in effect
; — once you outspeed the player by a safe margin, more Speed buys nothing —
; and three stages (~2.5x) is enough to catch even very slow setup mons up
; against very fast players. So cap encouragement at +3 stage and stop early
; if we already outspeed.
	cp EFFECT_SPEED_UP
	jr z, .check_speed
	cp EFFECT_SPEED_UP_2
	jr z, .check_speed

; Single-stat _UP_2 variants come first because their range is higher
; than the _UP range and we want to catch them before the consecutive _UP
; comparisons.
	cp EFFECT_ATTACK_UP_2
	jr c, .check_single_up
	cp EFFECT_EVASION_UP_2 + 1
	jr c, .single_up_2

.check_single_up
	cp EFFECT_ATTACK_UP
	jp c, .no
	cp EFFECT_EVASION_UP + 1
	jr c, .single_up
	jp .no

.single_up
	sub EFFECT_ATTACK_UP
	jr .index_stat

.single_up_2
	sub EFFECT_ATTACK_UP_2

.index_stat
	ld c, a
	ld b, 0
	ld hl, wEnemyAtkLevel
	add hl, bc
	ld a, [hl]
	cp MAX_STAT_LEVEL
	jr c, .yes
	jr .no

.check_speed
; Tier the cap by base Speed. The only Speed-only boost in this hack is
; AGILITY (+2 stages), so caps +1 and +2 both yield 1 Agility max in
; practice; the differentiation is mostly slow vs. fast. See CLAUDE.md
; "Stat math" gotcha for the multiplier table and reasoning.
;   base >= 90  -> cap +1  (one Agility max)
;   base 60..89 -> cap +2  (one Agility max)
;   base <= 59  -> cap +3  (two Agilities max — first lands at +2 < cap,
;                           second pushes to +4 which trips the cap)
; Stat-level encoding is base 7 (BASE_STAT_LEVEL), so cap stage N
; corresponds to byte BASE_STAT_LEVEL + N. wEnemyMonBaseStats is the
; current enemy mon's base-stat snapshot loaded at send-out; offset 3
; (STAT_SPD - 1) is base Speed.
	push de
	ld a, [wEnemyMonBaseStats + STAT_SPD - 1]
	cp 90
	ld d, BASE_STAT_LEVEL + 1
	jr nc, .have_speed_cap
	cp 60
	ld d, BASE_STAT_LEVEL + 2
	jr nc, .have_speed_cap
	ld d, BASE_STAT_LEVEL + 3
.have_speed_cap
	ld a, [wEnemySpdLevel]
	cp d
	pop de
	jr nc, .no
; If the enemy already outspeeds the active player mon, an Agility / Speed
; boost flips no race. Stop encouraging.
; AICompareSpeed lives in the AI Scoring section now (separate bank); cross
; via farcall. Safe because the helper takes no hl input.
	farcall AICompareSpeed
	jr c, .no
	jr .yes

.check_atk_or_spd
	ld a, [wEnemyAtkLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	ld a, [wEnemySpdLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	jr .no

.check_satk_or_sdef
	ld a, [wEnemySAtkLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	ld a, [wEnemySDefLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	jr .no

.check_quiver_dance
	ld a, [wEnemySAtkLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	ld a, [wEnemySDefLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	ld a, [wEnemySpdLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	jr .no

.check_curse
; Non-Ghost Curse boosts Atk and Def (and lowers Spd, which we ignore here
; — we just want to know if the boost still has stat-cap headroom).
	ld a, [wEnemyAtkLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	ld a, [wEnemyDefLevel]
	cp MAX_STAT_LEVEL
	jr c, .yes
	jr .no

.yes
	pop bc
	pop hl
	scf
	ret

.no
	pop bc
	pop hl
	and a
	ret

; ai-layer: POLICY
BossAI_SetupTurnIsAffordable:
; Returns carry if spending another turn on setup is affordable based on
; turns this mon has already spent on the field and current HP.
;   turn 0:        always affordable (mon just entered, no damage yet)
;   turn 1, full HP: affordable (player turn was wasted / trivial)
;   turn 1, < full:  not affordable (took a real hit, attack instead)
;   turn 2+:        never affordable (too many free turns spent setting up)
; Applies uniformly to all setup effects, including Speed boosts: if you
; haven't flipped the matchup in two turns, more setup just bleeds you out.
	ld a, [wEnemyTurnsTaken]
	and a
	jr z, .yes
	cp 2
	jr nc, .no
	call AICheckEnemyMaxHP_HL
	jr c, .yes
	jr .no

.yes
	scf
	ret

.no
	and a
	ret

; ai-layer: POLICY
BossAI_IsStatusEffect:
	push hl
	push de
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	pop de
	pop hl
	ret

; ai-layer: POLICY
BossAI_IsDenialEffect:
	cp EFFECT_FORCE_SWITCH
	jr z, .yes
	cp EFFECT_RESET_STATS
	jr z, .yes
	cp EFFECT_ENCORE
	jr z, .yes
	and a
	ret
.yes
	scf
	ret

; ============================================================
; Region: Seen-species index
; Concern: Active species to seen-species slot lookup
; Layer: PLATFORM
; Original lines: 43
; ============================================================
; ai-layer: PLATFORM
BossAI_GetActiveSpeciesSeenIndex:
	ld a, [wBattleMonSpecies]
	and a
	jr z, .none
	ld b, a
	ld a, [wBossAISeenPlayerSpeciesCount]
	ld c, a
	ld hl, wBossAISeenPlayerSpecies
	ld d, 1
.loop
	ld a, c
	and a
	jr z, .append
	ld a, [hli]
	cp b
	jr z, .found
	inc d
	dec c
	jr .loop

.append
	ld a, [wBossAISeenPlayerSpeciesCount]
	cp PARTY_LENGTH
	jr nc, .none
	ld c, a
	ld b, 0
	ld hl, wBossAISeenPlayerSpecies
	add hl, bc
	ld a, [wBattleMonSpecies]
	ld [hl], a
	ld hl, wBossAISeenPlayerSpeciesCount
	inc [hl]
	ld a, c
	inc a
	ret

.found
	ld a, d
	ret

.none
	xor a
	ret

; ============================================================
; Region: Plausible / likely type-mask construction
; Concern: Plausible and likely move-type mask construction and tests
; Layer: MIXED
; Original lines: 500
; ============================================================
; ai-layer: MIXED
BossAI_ComputePlayerPlausibleTypeMask:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBattleMonSpecies]
	and a
	ret z
	ld b, a
	ld [wBossAITemp], a
	ld a, [wBattleMonLevel]
	ld c, a
	ld a, [wBossAIPlausibleTypeMaskSpecies]
	cp b
	jr nz, .recompute
	ld a, [wBossAIPlausibleTypeMaskLevel]
	cp c
	ret z

.recompute
	ld a, b
	ld [wBossAIPlausibleTypeMaskSpecies], a
	ld a, c
	ld [wBossAIPlausibleTypeMaskLevel], a
	call BossAI_ClearPlausibleMask

	call BossAI_AddPublicSTABThreatsToMask
	call BossAI_AddRevealedDamagingTypesToMask
	ld a, [wBossAITemp]
	call BossAI_AddSpeciesAndPreEvolutionMovesToMask

.done
IF DEF(BOSS_AI_TRACE)
	ld hl, wBossAIPlausibleTypeMaskCache
	ld de, wBossAITracePlausibleMask
	ld bc, 4
	call CopyBytes
ENDC
	ret

; ai-layer: MIXED
BossAI_AddPublicSTABThreatsToMask:
	ld a, [wBattleMonType1]
	call BossAI_SetPlausibleAndLikelyMaskBit
	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	ret z
	ld a, c
	call BossAI_SetPlausibleAndLikelyMaskBit
	ret

; ai-layer: MIXED
BossAI_ClearPlausibleMask:
	ld hl, wBossAIPlausibleTypeMaskCache
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld hl, wBossAILikelyTypeMaskCache
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ret

; ai-layer: MIXED
BossAI_AddRevealedDamagingTypesToMask:
	call BossAI_GetActiveSpeciesRevealedMaskPointer
	ret nc
	push hl
	ld de, wBossAIPlausibleTypeMaskCache
	ld b, 4
.copy_possible_loop
	ld a, [de]
	or [hl]
	ld [de], a
	inc hl
	inc de
	dec b
	jr nz, .copy_possible_loop
	pop hl
	ld de, wBossAILikelyTypeMaskCache
	ld b, 4
.copy_likely_loop
	ld a, [de]
	or [hl]
	ld [de], a
	inc hl
	inc de
	dec b
	jr nz, .copy_likely_loop
	ret

; ai-layer: MIXED
BossAI_AddMoveIdToPlausibleMask:
	and a
	ret z
	ld b, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetPlausibleMaskBit
	ret

.check_power
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	ret z
	cp BOSS_AI_PLAUSIBLE_MIN_POWER
	ret c
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	call BossAI_SetPlausibleMaskBit
	ret

; ai-layer: MIXED
BossAI_AddMoveIdToLikelyMask:
	and a
	ret z
	ld b, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetLikelyMaskBit
	ret

.check_power
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	ret z
	cp BOSS_AI_PLAUSIBLE_MIN_POWER
	ret c
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	call BossAI_SetLikelyMaskBit
	ret

; ai-layer: MIXED
BossAI_SetPlausibleAndLikelyMaskBit:
	push af
	call BossAI_SetPlausibleMaskBit
	pop af
	call BossAI_SetLikelyMaskBit
	ret

; ai-layer: MIXED
BossAI_SetPlausibleMaskBit:
	ld c, a
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, wBossAIPlausibleTypeMaskCache
	add hl, de
	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.mask_loop
	ld a, e
	and a
	jr z, .set
	sla d
	dec e
	jr .mask_loop
.set
	ld a, [hl]
	or d
	ld [hl], a
	ret

; ai-layer: MIXED
BossAI_SetLikelyMaskBit:
	ld c, a
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, wBossAILikelyTypeMaskCache
	add hl, de
	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.mask_loop
	ld a, e
	and a
	jr z, .set
	sla d
	dec e
	jr .mask_loop
.set
	ld a, [hl]
	or d
	ld [hl], a
	ret

; ai-layer: MIXED
BossAI_AddSpeciesAndPreEvolutionMovesToMask:
	and a
	ret z
	ld [wBossAITemp4], a
	ld a, [wCurSpecies]
	push af
	ld a, [wCurPartySpecies]
	ld [wBossAITemp5], a
	ld a, [wBossAITemp4]
	ld [wCurPartySpecies], a
	xor a
	ld [wBossAITemp2], a

.loop
	call BossAI_LoadPublicThreatSourceSpecies
	call BossAI_AddCurrentSpeciesSpeculativeMoveThreats
	call BossAI_AddCurrentSpeciesLikelyMoveThreats
	call BossAI_AdvanceToPreEvolutionThreatSource
	jr c, .loop

.restore
	ld a, [wBossAITemp5]
	ld [wCurPartySpecies], a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ret

; ai-layer: MIXED
BossAI_LoadPublicThreatSourceSpecies:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ret

; ai-layer: MIXED
BossAI_AddCurrentSpeciesSpeculativeMoveThreats:
	call BossAI_AddBaseTMHMMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesEggMovesToMask
	ret

; ai-layer: MIXED
BossAI_AddCurrentSpeciesLikelyMoveThreats:
	ld a, [wBossAITemp2]
	and a
	ret nz
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToLikelyMask
	ret

; ai-layer: MIXED
BossAI_AdvanceToPreEvolutionThreatSource:
	callfar GetPreEvolution
	ret nc
	ld a, 1
	ld [wBossAITemp2], a
	scf
	ret

; ai-layer: MIXED
BossAI_AddBaseTMHMMovesToMask:
	ld hl, wBaseTMHM
	ld b, 1
	ld c, 1
	ld d, NUM_TM_HM
.tm_loop
	ld a, d
	and a
	ret z
	ld a, [hl]
	and b
	jr z, .next_tm
	push bc
	push de
	push hl
	ld a, c
	ld [wTempTMHM], a
	predef GetTMHMMove
	ld a, [wTempTMHM]
	call BossAI_AddMoveIdToPlausibleMask
	pop hl
	pop de
	pop bc
.next_tm
	inc c
	sla b
	jr nz, .bit_ok
	ld b, 1
	inc hl
.bit_ok
	dec d
	jr .tm_loop

; ai-layer: MIXED
BossAI_AddSpeciesLevelUpMovesToMask:
	and a
	ret z
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord

.skip_evos
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .moves
	cp EVOLVE_STAT
	jr z, .skip_stat_evo
	inc hl
	inc hl
	inc hl
	jr .skip_evos

.skip_stat_evo
	inc hl
	inc hl
	inc hl
	inc hl
	jr .skip_evos

.moves
	inc hl ; skip the no-more-evolutions marker
.move_loop
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	ret z
	ld b, a
	ld a, [wBattleMonLevel]
	cp b
	jr c, .skip_move
	inc hl
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	push hl
	call BossAI_AddMoveIdToPlausibleMask
	pop hl
	inc hl
	jr .move_loop

.skip_move
	inc hl
	inc hl
	jr .move_loop

; ai-layer: MIXED
BossAI_AddSpeciesLevelUpMovesToLikelyMask:
	and a
	ret z
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord

.skip_evos
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .moves
	cp EVOLVE_STAT
	jr z, .skip_stat_evo
	inc hl
	inc hl
	inc hl
	jr .skip_evos

.skip_stat_evo
	inc hl
	inc hl
	inc hl
	inc hl
	jr .skip_evos

.moves
	inc hl ; skip the no-more-evolutions marker
.move_loop
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	ret z
	ld b, a
	ld a, [wBattleMonLevel]
	cp b
	jr c, .skip_move
	inc hl
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	push hl
	call BossAI_AddMoveIdToLikelyMask
	pop hl
	inc hl
	jr .move_loop

.skip_move
	inc hl
	inc hl
	jr .move_loop

; ai-layer: MIXED
BossAI_AddSpeciesEggMovesToMask:
	and a
	ret z
	dec a
	ld c, a
	ld b, 0
	ld hl, EggMovePointers
	add hl, bc
	add hl, bc
	ld a, BANK(EggMovePointers)
	call GetFarWord

.loop
	ld a, BANK("Egg Moves")
	call GetFarByte
	cp -1
	ret z
	push hl
	call BossAI_AddMoveIdToPlausibleMask
	pop hl
	inc hl
	jr .loop

; ai-layer: MIXED
BossAI_TestPlausibleMaskBit:
	ld c, a
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, wBossAIPlausibleTypeMaskCache
	add hl, de
	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.test_loop
	ld a, e
	and a
	jr z, .test
	sla d
	dec e
	jr .test_loop
.test
	ld a, [hl]
	and d
	jr z, .not_set
	scf
	ret
.not_set
	and a
	ret

; ai-layer: MIXED
BossAI_TestLikelyMaskBit:
	ld c, a
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, wBossAILikelyTypeMaskCache
	add hl, de
	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.test_loop
	ld a, e
	and a
	jr z, .test
	sla d
	dec e
	jr .test_loop
.test
	ld a, [hl]
	and d
	jr z, .not_set
	scf
	ret
.not_set
	and a
	ret

; ============================================================
