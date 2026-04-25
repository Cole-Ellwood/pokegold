BossAI_IncrementTurnsElapsed:
	ld a, [wBossAITier]
	and a
	ret z
	ld hl, wBossAITurnsElapsed
	inc [hl]
	ld hl, wBossAIPlanPhase
	inc [hl]
	ret

BossAI_RecordPlayerSwitch:
	ld a, [wBossAITier]
	and a
	ret z
	ld hl, wBossAIPlayerSwitchCount
	inc [hl]
	ret

BossAI_RecordPlayerSpecies:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBattleMonSpecies]
	and a
	ret z
	ld b, a

	ld a, [wBossAISeenPlayerSpeciesCount]
	ld c, a
	ld hl, wBossAISeenPlayerSpecies
	ld a, c
	and a
	jr z, .append

.check_seen
	ld a, [hli]
	cp b
	ret z
	dec c
	jr nz, .check_seen

.append
	ld a, [wBossAISeenPlayerSpeciesCount]
	cp PARTY_LENGTH
	ret nc
	ld c, a
	ld b, 0
	ld hl, wBossAISeenPlayerSpecies
	add hl, bc
	ld a, [wBattleMonSpecies]
	ld [hl], a
	ld hl, wBossAISeenPlayerSpeciesCount
	inc [hl]
	ret

MaybePickAdaptiveEnemyLead:
; Blind weighted opener for selected major trainers:
; prefer default lead, but allow two alternate alive options.
	ld a, [wLinkMode]
	and a
	ret nz

	ld a, [wBattleMode]
	cp TRAINER_BATTLE
	ret nz

	call .ShouldUseAdaptiveLeadForTrainer
	ret nc

	call .FindFirstAliveOTMon
	ret nc
	ld d, a ; lead

	push de
	ld a, d
	call .FindNextAliveOTMon
	pop de
	jr nc, .pick_lead_only
	ld e, a ; alt1

	push de
	ld a, e
	call .FindNextAliveOTMon
	pop de
	jr nc, .pick_two_options
	ld b, a ; alt2

	call BattleRandom
	cp TRAINER_LEAD_PRIMARY_CHANCE_3
	jr c, .pick_lead
	cp TRAINER_LEAD_SECONDARY_CHANCE_3
	jr c, .pick_alt1
	ld a, b
	jr .set_pick

.pick_two_options
	call BattleRandom
	cp TRAINER_LEAD_PRIMARY_CHANCE_2
	jr c, .pick_lead

.pick_alt1
	ld a, e
	jr .set_pick

.pick_lead_only
.pick_lead
	ld a, d

.set_pick
	inc a
	ld [wEnemySwitchMonIndex], a
	ret

.ShouldUseAdaptiveLeadForTrainer:
	callfar IsGymLeader
	ret nc

	ld a, [wOtherTrainerClass]
	cp FALKNER
	jr z, .disabled
	cp WHITNEY
	jr z, .disabled
	cp BUGSY
	jr z, .disabled
	cp MORTY
	jr z, .disabled
	cp RED
	jr z, .disabled
	scf
	ret

.disabled
	and a
	ret

.FindFirstAliveOTMon:
	ld a, [wOTPartyCount]
	and a
	jr z, .none_found

	ld b, a
	xor a
	ld c, a
	ld hl, wOTPartyMon1HP
	ld de, PARTYMON_STRUCT_LENGTH - 1
.first_loop
	ld a, [hli]
	or [hl]
	jr nz, .first_found
	add hl, de
	inc c
	dec b
	jr nz, .first_loop

.none_found
	and a
	ret

.first_found
	ld a, c
	scf
	ret

.FindNextAliveOTMon:
; Input: a = current party index. Output: a = next alive index, carry set if found.
	inc a
	ld c, a
	ld a, [wOTPartyCount]
	cp c
	jr z, .none_found
	jr c, .none_found

	ld hl, wOTPartyMon1HP
	push bc
	ld a, c
	call GetPartyLocation
	pop bc
	ld de, PARTYMON_STRUCT_LENGTH - 1

.next_scan
	ld a, [hli]
	or [hl]
	jr nz, .next_found
	add hl, de
	inc c
	ld a, [wOTPartyCount]
	cp c
	jr z, .none_found
	jr c, .none_found
	jr .next_scan

.next_found
	ld a, c
	scf
	ret

BossAI_RecordRevealedPlayerMove:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wPlayerMoveStruct + MOVE_ANIM]
	and a
	ret z
	dec a
	ld c, a
	ld b, 0

	ld hl, wBossAIRevealedMovesBitmap
	ld a, c
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	add hl, de

	ld a, c
	and %00000111
	ld e, a
	ld d, 1
.bit_loop
	ld a, e
	and a
	jr z, .set
	sla d
	dec e
	jr .bit_loop

.set
	ld a, [hl]
	or d
	ld [hl], a
	xor a
	ld [wBossAIPlausibleTypeMaskSpecies], a
	ret

BossAI_ApplyMoveModel:
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	ret z
	push bc
	push de
	push hl
	call .ScoreMove
	pop hl
	pop de
	pop bc
	inc hl
	inc de
	dec c
	jr nz, .loop
	ret

.ScoreMove
	ld a, h
	ld [wBossAIScorePtr], a
	ld a, l
	ld [wBossAIScorePtr + 1], a
	ld a, [de]
	call AIGetEnemyMove

	xor a
	ld [wBossAIMoveChoiceReady], a

	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .skip_ko
	push hl
	call AIDamageCalc
	pop hl
	ld a, [wCurDamage + 1]
	ld e, a
	ld a, [wCurDamage]
	ld d, a
	ld a, [wBattleMonHP + 1]
	cp e
	ld a, [wBattleMonHP]
	sbc d
	jr nc, .skip_ko
	ld c, 0
	call .EncourageByTierWeight

.skip_ko
	call .EnemyUnderPressure
	jr nc, .skip_denyko
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIDenyKOEffects
	ld de, 1
	call IsInArray
	jr nc, .skip_denyko
	ld c, 1
	call .EncourageByTierWeight

.skip_denyko
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .skip_tempo
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PRIORITY_HIT
	jr z, .tempo_bonus
	push hl
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	callfar BattleCheckTypeMatchup
	pop af
	ldh [hBattleTurn], a
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .skip_tempo
	call AICompareSpeed
	jr nc, .skip_tempo

.tempo_bonus
	ld c, 2
	call .EncourageByTierWeight

.skip_tempo
	call .IsSetupMove
	jr nc, .skip_setup
	call .EnemyUnderPressure
	jr c, .unsafe_setup
	ld c, 3
	call .EncourageByTierWeight
	jr .skip_setup

.unsafe_setup
	ld c, 3
	call .DiscourageByTierWeight

.skip_setup
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	jr nc, .skip_status
	ld a, [wBattleMonStatus]
	and a
	jr nz, .skip_status
	ld c, 4
	call .EncourageByTierWeight
	ld a, [wBossAITurnsElapsed]
	cp 5
	jr c, .skip_status
	ld c, 4
	call .DiscourageByTierWeight

.skip_status
	call .ApplySpikesLayerBias
	call .ApplyLegacyRoleBiasIfNeeded
	call BossAI_ApplyPlanMoveBias
	call BossAI_ApplyScoutMoveBias
	call BossAI_ApplyRepeatPenalty

	call .HasKOLine
	ret c

	ld a, [wEnemyMoveStruct + MOVE_ACC]
	cp 80 percent
	jr c, .risk
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIRiskyEffects
	ld de, 1
	call IsInArray
	ret nc

.risk
	ld c, 6
	call .DiscourageByTierWeight
	ret

.ApplySpikesLayerBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SPIKES
	ret nz

	ld a, [wPlayerScreens]
	and SCREENS_SPIKES_MASK
	and a
	jr z, .spikes_layer1
	cp 1
	jr z, .spikes_layer2
	cp 2
	jr z, .spikes_layer3

; Already at 3 layers: discourage.
	ld c, 5
	call .DiscourageByTierWeight
	ret

.spikes_layer1
; Good lead/pivot punishment baseline.
	ld a, [wBossAITurnsElapsed]
	and a
	jr z, .spikes_l1_high
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 40
	jr nc, .spikes_l1_high
	ld c, 4
	call .EncourageByTierWeight
	ret

.spikes_l1_high
	ld c, 5
	call .EncourageByTierWeight
	ret

.spikes_layer2
; Layer 2 gives limited immediate gain; only push if layer 3 looks reachable.
	call .EnemyUnderPressure
	jr c, .spikes_l2_danger
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 55
	jr nc, .spikes_l2_longterm
	ld c, 4
	call .DiscourageByTierWeight
	ret

.spikes_l2_longterm
	ld c, 2
	call .EncourageByTierWeight
	ret

.spikes_l2_danger
	ld c, 5
	call .DiscourageByTierWeight
	ret

.spikes_layer3
; Prioritize finishing the stack unless immediate danger.
	call .EnemyUnderPressure
	jr c, .spikes_l3_danger
	ld c, 5
	call .EncourageByTierWeight
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 40
	ret c
	ld c, 2
	call .EncourageByTierWeight
	ret

.spikes_l3_danger
	ld c, 3
	call .DiscourageByTierWeight
	ret

.ApplyLegacyRoleBiasIfNeeded
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ret z
	jr .ApplyRoleBias

.ApplyRoleBias
	ld a, [wTrainerClass]
	cp FALKNER
	jp z, .falkner
	cp RIVAL1
	jp z, .rival
	cp CHUCK
	jp z, .chuck
	cp JASMINE
	jp z, .jasmine
	cp PRYCE
	jp z, .pryce
	cp CLAIR
	jp z, .clair
	cp WILL
	jp z, .will
	cp BRUNO
	jp z, .bruno
	cp KAREN
	jp z, .karen
	cp KOGA
	jp z, .koga
	cp CHAMPION
	jp z, .champion
	ret

.rival
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	ld c, 5
	call .EncourageByTierWeight
	ret

.falkner
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SPEED_DOWN_HIT
	jr z, .falkner_bias
	cp EFFECT_ACCURACY_DOWN
	jr z, .falkner_bias
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	cp FLYING
	ret nz
.falkner_bias
	ld c, 5
	call .EncourageByTierWeight
	ret

.chuck
	ld a, FIGHTING
	call .EncourageIfType
	ld hl, BossAIChuckRoleEffects
	call .EncourageIfEffectInArray
	ret

.jasmine
	ld a, STEEL
	call .EncourageIfType
	ld a, ELECTRIC
	call .EncourageIfType
	ld a, GROUND
	call .EncourageIfType
	ld hl, BossAIJasmineRoleEffects
	call .EncourageIfEffectInArray
	ret

.pryce
	ld a, ICE
	call .EncourageIfType
	ld a, GROUND
	call .EncourageIfType
	ld hl, BossAIPryceRoleEffects
	call .EncourageIfEffectInArray
	ret

.clair
	ld a, DRAGON
	call .EncourageIfType
	ld hl, BossAIClairRoleEffects
	call .EncourageIfEffectInArray
	ret

.will
	ld a, PSYCHIC_TYPE
	call .EncourageIfType
	ld hl, BossAIWillRoleEffects
	call .EncourageIfEffectInArray
	ret

.bruno
	ld a, FIGHTING
	call .EncourageIfType
	ld hl, BossAIBrunoRoleEffects
	call .EncourageIfEffectInArray
	ret

.karen
	ld a, DARK
	call .EncourageIfType
	ld hl, BossAIKarenRoleEffects
	call .EncourageIfEffectInArray
	ret

.koga
	ld a, POISON
	call .EncourageIfType
	ld a, BUG
	call .EncourageIfType
	ld hl, BossAIKogaRoleEffects
	call .EncourageIfEffectInArray
	ret

.champion
	ld a, DRAGON
	call .EncourageIfType
	ld a, FLYING
	call .EncourageIfType
	ld hl, BossAIChampionRoleEffects
	call .EncourageIfEffectInArray
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_HYPER_BEAM
	ret nz
	call .HasKOLine
	ret c
	ld c, 5
	call .DiscourageByTierWeight
	ret

.EncourageIfType
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	cp b
	ret nz
	ld c, 5
	call .EncourageByTierWeight
	ret

.EncourageIfEffectInArray
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld de, 1
	call IsInArray
	ret nc
	ld c, 5
	call .EncourageByTierWeight
	ret

.EncourageByTierWeight
	call .GetTierWeight
	call BossAI_LoadScorePointer
	jr .EncourageScoreByA

.DiscourageByTierWeight
	call .GetTierWeight
	call BossAI_LoadScorePointer
	jr .DiscourageScoreByA

.GetTierWeight
	ld hl, BossAITierWeights
	ld a, [wBossAITier]
	dec a
	jr z, .got_tier
.tier_loop
	ld de, 7
	add hl, de
	dec a
	jr nz, .tier_loop
.got_tier
	ld a, c
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]
	ret

.EncourageScoreByA
	and a
	ret z
	ld e, a
.encourage_loop
	ld a, [hl]
	cp 1
	ret z
	dec [hl]
	dec e
	jr nz, .encourage_loop
	ret

.DiscourageScoreByA
	and a
	ret z
	ld e, a
.discourage_loop
	inc [hl]
	dec e
	jr nz, .discourage_loop
	ret

.EnemyUnderPressure
	call AICheckEnemyQuarterHP
	jr nc, .pressure_yes
	call CheckPlayerMoveTypeMatchups
	ld a, [wEnemyAISwitchScore]
	cp BASE_AI_SWITCH_SCORE
	jr c, .pressure_yes
	and a
	ret
.pressure_yes
	scf
	ret

.HasKOLine
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .hasko_no
	call AIDamageCalc
	ld a, [wCurDamage + 1]
	ld e, a
	ld a, [wCurDamage]
	ld d, a
	ld a, [wBattleMonHP + 1]
	cp e
	ld a, [wBattleMonHP]
	sbc d
	jr nc, .hasko_no
	scf
	ret
.hasko_no
	and a
	ret

.IsSetupMove
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_DRAGON_DANCE
	jr z, .setup_yes
	cp EFFECT_ATTACK_UP
	jr c, .setup_no
	cp EFFECT_EVASION_UP + 1
	jr c, .setup_yes
	cp EFFECT_ATTACK_UP_2
	jr c, .setup_no
	cp EFFECT_EVASION_UP_2 + 1
	jr c, .setup_yes
.setup_no
	and a
	ret
.setup_yes
	scf
	ret

BossAI_SelectMove:
	xor a
	ld [wBossAIMoveChoiceReady], a
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask
IF DEF(BOSS_AI_TRACE)
	xor a
	ld [wBossAITraceRiskFlags], a
ENDC
	call BossAI_ApplyLookaheadToTopMoveCandidates

IF DEF(BOSS_AI_TRACE)
	call BossAI_TraceTopMoves
ENDC

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld b, $ff ; best score
	ld c, $ff ; best index
	xor a ; current index
.first_pass
	cp NUM_MOVES
	jr nc, .first_done
	push af
	ld a, [de]
	and a
	jr z, .first_done_pop
	ld a, [hl]
	cp 80
	jr nc, .first_next
	cp b
	jr nc, .first_next
	ld b, a
	pop af
	ld c, a
	push af
.first_next
	pop af
	inc hl
	inc de
	inc a
	jr .first_pass

.first_done_pop
	pop af

.first_done
	ld a, c
	cp $ff
	ret z

	ld a, c ; best index
	ld [wBossAITemp], a
	ld a, b
	push af
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld b, $ff ; second score
	ld c, $ff ; second index
	xor a ; current index
.second_pass
	cp NUM_MOVES
	jr nc, .second_done
	push af
	ld a, [de]
	and a
	jr z, .second_done_pop
	pop af
	push af
	push hl
	ld hl, wBossAITemp
	cp [hl]
	pop hl
	jr z, .second_next
	ld a, [hl]
	cp 80
	jr nc, .second_next
	cp b
	jr nc, .second_next
	ld b, a
	pop af
	ld c, a
	push af
.second_next
	pop af
	inc hl
	inc de
	inc a
	jr .second_pass

.second_done_pop
	pop af

.second_done
	pop af
	ld e, a
	ld a, c
	cp $ff
	jr z, .choose_best

	ld a, b
	sub e
	cp 6
	ld a, 230
	jr nc, .roll
	ld a, b
	sub e
	cp 3
	ld a, 192
	jr nc, .roll
	ld a, 154

.roll
	call .AdjustBestMovePickChance
	ld b, a
	call Random
	cp b
	jr c, .choose_best
	jr .choose_second

.choose_best
	ld a, [wBossAITemp]
	jr .store_choice

.choose_second
	ld a, c

.store_choice
	ld [wCurEnemyMoveNum], a
	ld c, a
	ld b, 0
	ld hl, wEnemyMonMoves
	add hl, bc
	ld a, [hl]
	ld [wCurEnemyMove], a
	ld a, 1
	ld [wBossAIMoveChoiceReady], a
	call BossAI_UpdateRepeatTracker
	call BossAI_MarkScoutedIfScoutMove

IF DEF(BOSS_AI_TRACE)
	ld a, [wCurEnemyMove]
	ld [wBossAITraceChosenMove], a
ENDC
	ret

.AdjustBestMovePickChance
	push bc
	ld b, a
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr nz, .check_mid
	ld a, b
	add 32
	jr nc, .late_cap_check
	ld a, 252
	jr .done
.late_cap_check
	cp 252
	jr c, .done
	ld a, 252
	jr .done

.check_mid
	cp AI_TIER_MID
	jr nz, .early
	ld a, b
	add 20
	jr nc, .mid_cap_check
	ld a, 245
	jr .done
.mid_cap_check
	cp 245
	jr c, .done
	ld a, 245
	jr .done

.early
	ld a, b

.done
	pop bc
	ret

BossAI_SwitchOrTryItem:
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask

	call BossAI_HasAnyKOMove
	jr nc, .check_switch
	call BossAI_IsImminentKOPrevention
	jr c, .check_switch
	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .check_switch
	ret

.check_switch
	call BossAI_DecaySwitchCooldown
	callfar CheckAbleToSwitch
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

BossAI_DecaySwitchCooldown:
	ld a, [wBossAISwitchCooldown]
	and a
	ret z
	dec a
	ld [wBossAISwitchCooldown], a
	ret

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

BossAI_NeedsLoopPenalty:
	ld a, [wBossAISwitchCooldown]
	and a
	jr z, .no_penalty
	ld a, [wCurOTMon]
	inc a
	ld b, a
	ld a, [wBossAILastSwitchedOut]
	cp b
	jr nz, .no_penalty

	call BossAI_IsImminentKOPrevention
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

BossAI_IsImminentKOPrevention:
	call AICheckEnemyQuarterHP
	jr nc, .yes
	call CheckPlayerMoveTypeMatchups
	ld a, [wEnemyAISwitchScore]
	cp BASE_AI_SWITCH_SCORE
	jr c, .yes
	call BossAI_ShouldRespectPotentialPlayerRevenge
	jr c, .yes
	and a
	ret
.yes
	scf
	ret

BossAI_ShouldRespectPotentialPlayerRevenge:
; Carry if the player is likely to threaten a fast revenge KO line.
	call AICompareSpeed
	jr nc, .check_threat
	call BossAI_IsScarfSwingPossible
	jr nc, .no

.check_threat
	call BossAI_GetPrimaryThreatType
	jr nc, .no
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	cp 3
	jr c, .no

	call AICheckEnemyHalfHP
	jr nc, .yes
	call BossAI_HasRevealedSuperEffectiveMove
	jr c, .yes
	call BossAI_IsSuspiciousSwitchIn
	jr nc, .no
	call AICheckEnemyQuarterHP
	jr nc, .yes

.no
	and a
	ret

.yes
	scf
	ret

BossAI_IsScarfSwingPossible:
; Carry if player is currently slower but would be faster with a 1.5x speed boost.
	call AICompareSpeed
	jr nc, .no

	ld a, [wBattleMonSpeed]
	ld h, a
	ld b, a
	ld a, [wBattleMonSpeed + 1]
	ld l, a
	ld c, a
	add hl, bc
	add hl, bc
	ld b, h
	ld c, l
	srl b
	rr c

	ld a, [wEnemyMonSpeed]
	cp b
	jr c, .yes
	jr nz, .no
	ld a, [wEnemyMonSpeed + 1]
	cp c
	jr c, .yes

.no
	and a
	ret

.yes
	scf
	ret

BossAI_IsSuspiciousSwitchIn:
; Carry when the fresh switch-in looks like a coverage/pivot line instead of natural STAB pressure.
	ld a, [wBossAITurnsElapsed]
	and a
	jr z, .no
	ld a, [wPlayerTurnsTaken]
	and a
	jr nz, .no
	call AICompareSpeed
	jr nc, .no

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
	ld hl, wEnemyMonType1
	call CheckTypeMatchup
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr c, .nve
	and a
	ret
.nve
	scf
	ret

BossAI_IsImmunityPivotOpportunity:
	ld a, [wLastPlayerCounterMove]
	and a
	ret z
	push af
	dec a
	ld hl, Moves + MOVE_POWER
	call GetMoveAttr
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
	call GetMoveAttr
	inc hl
	call GetMoveByte
	ld hl, wBaseType
	call CheckTypeMatchup
	ld a, [wTypeMatchup]
	and a
	ret nz
	scf
	ret

.no
	pop af
	and a
	ret

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

	call AICheckEnemyHalfHP
	jr nc, .yes
	call AICheckPlayerHalfHP
	jr nc, .yes

.no
	and a
	ret

.yes
	scf
	ret

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
	call AICheckEnemyQuarterHP
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

BossAI_PredictPlayerSwitch:
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
	call AICheckPlayerQuarterHP
	jr c, .hp_done
	ld a, [wBossAITemp]
	add 20
	ld [wBossAITemp], a
.hp_done

	call CheckPlayerMoveTypeMatchups
	ld a, [wEnemyAISwitchScore]
	cp BASE_AI_SWITCH_SCORE + 1
	jr c, .done
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

BossAI_HasRevealedSuperEffectiveMove:
	ld hl, wBossAIRevealedMovesBitmap
	ld b, 1 ; move id

.byte_loop
	ld a, b
	cp NUM_ATTACKS + 1
	jr nc, .no
	ld a, [hli]
	ld d, a
	ld e, 8

.bit_loop
	ld a, b
	cp NUM_ATTACKS + 1
	jr nc, .no
	ld a, d
	and 1
	jr z, .next_bit

	push bc
	push de
	push hl
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call GetMoveAttr
	and a
	jr z, .restore
	inc hl
	call GetMoveByte
	ld hl, wEnemyMonType1
	call CheckTypeMatchup
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .restore
	pop hl
	pop de
	pop bc
	scf
	ret

.restore
	pop hl
	pop de
	pop bc

.next_bit
	ld a, d
	srl a
	ld d, a
	inc b
	dec e
	jr nz, .bit_loop
	jr .byte_loop

.no
	and a
	ret

BossAI_HasAnyKOMove:
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	jr z, .no
	push bc
	push de
	call AIGetEnemyMove
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .next
	call AIDamageCalc
	ld a, [wCurDamage + 1]
	ld e, a
	ld a, [wCurDamage]
	ld d, a
	ld a, [wBattleMonHP + 1]
	cp e
	ld a, [wBattleMonHP]
	sbc d
	jr nc, .next
	pop de
	pop bc
	scf
	ret
.next
	pop de
	pop bc
	inc de
	dec c
	jr nz, .loop
.no
	and a
	ret

BossAI_SeenSpeciesThreatScore:
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .none
	ld c, a
	ld hl, wBossAISeenPlayerSpecies
	ld b, 0
.loop
	ld a, [hli]
	and a
	jr z, .next
	ld [wCurSpecies], a
	call GetBaseData

	ld a, [wBaseType1]
	ld d, a
	ld hl, wEnemyMonType1
	call CheckTypeMatchup
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr nc, .favorable

	ld a, [wBaseType2]
	cp d
	jr z, .next
	ld hl, wEnemyMonType1
	call CheckTypeMatchup
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .next

.favorable
	inc b

.next
	dec c
	jr nz, .loop

	ld a, b
	and a
	jr z, .none
	add a
	add a
	add b
	add a
	ret

.none
	xor a
	ret

DEF BOSS_ROLE_SETUP EQU 0
DEF BOSS_ROLE_STATUS EQU 1
DEF BOSS_ROLE_DENIAL EQU 2

BossAI_SelectPlanIfNeeded:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBossAIPlanId]
	and a
	jr nz, .adapt
	call .ChooseInitialPlan
	jr .trace

.adapt
	call .AdaptPlan

.trace
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAIPlanId]
	ld [wBossAITracePlanId], a
	ld a, [wBossAIPlanPhase]
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
	call AIGetEnemyMove
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

BossAI_IsSetupEffect:
	cp EFFECT_DRAGON_DANCE
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

BossAI_IsStatusEffect:
	push hl
	push de
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	pop de
	pop hl
	ret

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

BossAI_ComputePlayerPlausibleTypeMask:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBattleMonSpecies]
	and a
	ret z
	ld b, a
	ld [wBossAITemp], a
	ld a, [wBossAIPlausibleTypeMaskSpecies]
	cp b
	ret z

	ld a, b
	ld [wBossAIPlausibleTypeMaskSpecies], a
	call BossAI_ClearPlausibleMask

	ld a, [wBattleMonType1]
	call BossAI_SetPlausibleMaskBit
	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	jr z, .skip_stab2
	ld a, c
	call BossAI_SetPlausibleMaskBit
.skip_stab2

	call BossAI_AddRevealedDamagingTypesToMask

	ld a, [wBossAITemp]
	ld [wCurSpecies], a
	call GetBaseData
	ld hl, wBaseTMHM
	ld b, 1
	ld c, 1
	ld d, NUM_TM_HM
.tm_loop
	ld a, d
	and a
	jr z, .add_learnset_moves
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

.add_learnset_moves
	ld a, [wBossAITemp]
	call BossAI_AddSpeciesLevelUpMovesToMask
	ld a, [wBossAITemp]
	call BossAI_AddSpeciesEggMovesToMask

.done
IF DEF(BOSS_AI_TRACE)
	ld hl, wBossAIPlausibleTypeMaskCache
	ld de, wBossAITracePlausibleMask
	ld bc, 4
	call CopyBytes
ENDC
	ret

BossAI_ClearPlausibleMask:
	ld hl, wBossAIPlausibleTypeMaskCache
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ret

BossAI_AddRevealedDamagingTypesToMask:
	ld hl, wBossAIRevealedMovesBitmap
	ld b, 1
.byte_loop
	ld a, b
	cp NUM_ATTACKS + 1
	ret nc
	ld a, [hli]
	ld d, a
	ld e, 8
.bit_loop
	ld a, b
	cp NUM_ATTACKS + 1
	ret nc
	ld a, d
	and 1
	jr z, .next_bit
	push bc
	push de
	push hl
	ld a, b
	call BossAI_AddRevealedMoveToPlausibleMask
	pop hl
	pop de
	pop bc
.next_bit
	ld a, d
	srl a
	ld d, a
	inc b
	dec e
	jr nz, .bit_loop
	jr .byte_loop

BossAI_AddRevealedMoveToPlausibleMask:
	ld b, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetPlausibleMaskBit
	ret

.check_power
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call GetMoveAttr
	and a
	ret z
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call GetMoveAttr
	call BossAI_SetPlausibleMaskBit
	ret

BossAI_AddMoveIdToPlausibleMask:
	and a
	ret z
	ld b, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetPlausibleMaskBit
	ret

.check_power
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call GetMoveAttr
	and a
	ret z
	cp BOSS_AI_PLAUSIBLE_MIN_POWER
	ret c
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call GetMoveAttr
	call BossAI_SetPlausibleMaskBit
	ret

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
	inc hl
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	call BossAI_AddMoveIdToPlausibleMask
	inc hl
	jr .move_loop

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
	call BossAI_AddMoveIdToPlausibleMask
	inc hl
	jr .loop

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

BossAI_ApplyPlanMoveBias:
	ld a, [wBossAIPlanId]
	and a
	ret z
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .check_status
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call BossAI_IsSetupEffect
	ret nc
	ld a, 2
	jp BossAI_EncourageScoreHL

.check_status
	cp BOSS_PLAN_STATUS_CHOKE
	jr nz, .check_break
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call BossAI_IsStatusEffect
	ret nc
	ld a, 2
	jp BossAI_EncourageScoreHL

.check_break
	cp BOSS_PLAN_WALLBREAK_THEN_CLEAN
	jr nz, .check_protect
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	cp 80
	ret c
	ld a, 2
	jp BossAI_EncourageScoreHL

.check_protect
	cp BOSS_PLAN_ENDGAME_PROTECT
	jr nz, .check_denial
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .protect_good
	cp EFFECT_SUBSTITUTE
	jr z, .protect_good
	cp EFFECT_HEAL
	jr z, .protect_good
	cp EFFECT_MORNING_SUN
	jr z, .protect_good
	cp EFFECT_SYNTHESIS
	jr z, .protect_good
	cp EFFECT_MOONLIGHT
	ret nz
.protect_good
	ld a, 2
	jp BossAI_EncourageScoreHL

.check_denial
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call BossAI_IsDenialEffect
	ret nc
	ld a, 2
	jp BossAI_EncourageScoreHL

BossAI_ApplyScoutMoveBias:
	push hl
	call BossAI_ShouldScout
	pop hl
	ret nc
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .scout_move
	cp EFFECT_SUBSTITUTE
	ret nz
.scout_move
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, 2
	jr c, .apply
	ld a, 3
.apply
	jp BossAI_EncourageScoreHL

BossAI_ApplyRepeatPenalty:
	ld a, [wBossAIRepeatCount]
	cp 2
	ret c
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	ld b, a
	ld a, [wBossAILastChosenMove]
	cp b
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .penalize
	push hl
	call AIDamageCalc
	pop hl
	ld a, [wCurDamage + 1]
	ld e, a
	ld a, [wCurDamage]
	ld d, a
	ld a, [wBattleMonHP + 1]
	cp e
	ld a, [wBattleMonHP]
	sbc d
	ret c
.penalize
	ld a, BOSS_AI_REPEAT_PENALTY
	jp BossAI_DiscourageScoreHL

BossAI_LoadScorePointer:
	push af
	ld a, [wBossAIScorePtr]
	ld h, a
	ld a, [wBossAIScorePtr + 1]
	ld l, a
	pop af
	ret

BossAI_EncourageScoreHL:
	call BossAI_LoadScorePointer
	and a
	ret z
	ld e, a
.enc_loop
	ld a, [hl]
	cp 1
	ret z
	dec [hl]
	dec e
	jr nz, .enc_loop
	ret

BossAI_DiscourageScoreHL:
	call BossAI_LoadScorePointer
	and a
	ret z
	ld e, a
.disc_loop
	ld a, [hl]
	cp 79
	jr nc, .disc_done
	inc [hl]
.disc_done
	dec e
	jr nz, .disc_loop
	ret

BossAI_ApplyLookaheadToTopMoveCandidates:
	ld a, [wBossAITier]
	cp BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN
	ret c

IF DEF(BOSS_AI_TRACE)
	xor a
	ld [wBossAITraceRiskFlags], a
	ld hl, wBossAITraceLookaheadBonusTop
	ld [hli], a
	ld [hli], a
	ld [hl], a
ENDC

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
	ld b, 79
.best_loop
	ld a, [de]
	and a
	jr z, .best_done
	ld a, [hl]
	cp 80
	jr nc, .best_next
	cp b
	jr nc, .best_next
	ld b, a
.best_next
	inc hl
	inc de
	dec c
	jr nz, .best_loop

.best_done
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
	ld a, b
	add 6
	push af
	ld b, 0
.eval_loop
	ld a, [de]
	and a
	jr z, .eval_done
	ld a, [hl]
	cp 80
	jr nc, .eval_next
	pop af
	push af
	cp [hl]
	jr c, .eval_next
	push hl
	push de
	ld a, [de]
	call BossAI_EvaluateActionLookahead
IF DEF(BOSS_AI_TRACE)
	ld [wTempByteValue], a
ENDC
	pop de
	pop hl
	push bc
	call BossAI_ApplySignedDeltaToScore
	pop bc
IF DEF(BOSS_AI_TRACE)
	push bc
	ld a, b
	cp 3
	jr nc, .after_trace
	ld c, a
	ld b, 0
	push de
	ld hl, wBossAITraceLookaheadBonusTop
	add hl, bc
	ld a, [wTempByteValue]
	ld [hl], a
	pop de
.after_trace
	pop bc
ENDC
	inc b
	ld a, b
	cp BOSS_AI_LOOKAHEAD_N
	jr nc, .eval_done
.eval_next
	inc hl
	inc de
	dec c
	jr nz, .eval_loop
	; fallthrough
.eval_done
	pop af
	ret

BossAI_ApplySignedDeltaToScore:
	bit 7, a
	jr z, .positive
	cpl
	inc a
	ld c, a
	ld a, [hl]
	sub c
	jr nc, .store
	ld a, 1
	jr .store

.positive
	ld c, a
	ld a, [hl]
	add c
	cp 80
	jr c, .store
	ld a, 79
.store
	ld [hl], a
	ret

BossAI_EvaluateActionLookahead:
	ld a, [wBossAITier]
	and a
	ret z
	cp BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN
	jr nc, .go
	xor a
	ret

.go
	push hl
	push de
	push bc
	call AIGetEnemyMove
	ld b, 0 ; upside
	ld c, 0 ; downside

	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .check_setup
	push bc
	call AIDamageCalc
	pop bc
	ld a, [wCurDamage + 1]
	ld e, a
	ld a, [wCurDamage]
	ld d, a
	ld a, [wBattleMonHP + 1]
	cp e
	ld a, [wBattleMonHP]
	sbc d
	jr nc, .not_ko
	ld b, BOSS_AI_LOOKAHEAD_BONUS_CAP
	jr .check_setup

.not_ko
	ld a, [wBattleMonHP + 1]
	ld e, a
	ld a, [wBattleMonHP]
	ld d, a
	srl d
	rr e
	ld a, [wCurDamage + 1]
	cp e
	ld a, [wCurDamage]
	sbc d
	jr c, .check_quarter
	ld a, b
	add 4
	ld b, a
	jr .check_setup

.check_quarter
	ld a, [wBattleMonHP + 1]
	ld e, a
	ld a, [wBattleMonHP]
	ld d, a
	srl d
	rr e
	srl d
	rr e
	ld a, [wCurDamage + 1]
	cp e
	ld a, [wCurDamage]
	sbc d
	jr c, .check_setup
	ld a, b
	add 2
	ld b, a

.check_setup
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call BossAI_IsSetupEffect
	jr nc, .check_scout
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .check_scout
	ld a, b
	add 3
	ld b, a

.check_scout
	push bc
	call BossAI_ShouldScout
	pop bc
	jr nc, .check_reply
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .scout_bonus
	cp EFFECT_SUBSTITUTE
	jr nz, .check_reply
.scout_bonus
	ld a, b
	add 2
	ld b, a

.check_reply
	push bc
	call BossAI_HasAnyKOMove
	pop bc
	jr c, .late_reply
	push bc
	call BossAI_GetPrimaryThreatType
	pop bc
	jr nc, .late_reply
	push bc
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop bc
	ld e, a
	ld a, c
	add e
	ld c, a

.late_reply
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr c, .delta
	push bc
	call BossAI_HasAnyKOMove
	pop bc
	jr nc, .delta
	ld a, c
	and a
	jr z, .delta
	dec c

.delta
	call BossAI_ApplyMultiTurnProjection
	ld a, c
	sub b
	call BossAI_ClampSignedLookaheadDelta
	pop bc
	pop de
	pop hl
	ret

BossAI_ApplyMultiTurnProjection:
; Adds a rolling, tier-based future projection onto upside/downside (b/c).
; This keeps lookahead reactive each turn while extending the planning horizon.
	call .GetProjectionDepth
	and a
	ret z

; Non-damaging moves lose tempo over longer horizons.
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr nz, .check_setup
	call .GetProjectionDepth
	call .AddDownsideByA

.check_setup
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	push bc
	call BossAI_IsSetupEffect
	pop bc
	jr nc, .check_scout
	call .IsUnderPressure
	jr c, .setup_risky
	call .GetProjectionDepth
	add a
	call .AddUpsideByA
	jr .check_scout

.setup_risky
	call .GetProjectionDepth
	add a
	call .AddDownsideByA

.check_scout
	push bc
	call BossAI_ShouldScout
	pop bc
	jr nc, .check_threat
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .scout_bonus
	cp EFFECT_SUBSTITUTE
	jr nz, .check_threat

.scout_bonus
	call .GetProjectionDepth
	call .AddUpsideByA

.check_threat
	push bc
	call BossAI_HasAnyKOMove
	pop bc
	jr c, .check_switch
	push bc
	call BossAI_GetPrimaryThreatType
	pop bc
	jr nc, .check_switch
	push bc
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop bc
	ld d, a
	ld a, d
	and a
	jr z, .check_switch
	ld a, d
	call .AddDownsideByA
	call .GetProjectionDepth
	cp 3
	jr c, .check_switch
	ld a, d
	call .AddDownsideByA

.check_switch
	push bc
	call BossAI_PredictPlayerSwitch
	pop bc
	cp 50
	jr c, .check_accuracy
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SPIKES
	jr z, .switch_bonus
	push bc
	call BossAI_IsSetupEffect
	pop bc
	jr nc, .check_accuracy

.switch_bonus
	call .GetProjectionDepth
	call .AddUpsideByA

.check_accuracy
	ld a, [wEnemyMoveStruct + MOVE_ACC]
	cp 80 percent
	ret nc
	call .GetProjectionDepth
	call .AddDownsideByA
	ret

.GetProjectionDepth
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, BOSS_AI_LOOKAHEAD_HORIZON_LATE - 1
	ret z
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ld a, BOSS_AI_LOOKAHEAD_HORIZON_MID - 1
	ret z
	xor a
	ret

.IsUnderPressure
	push bc
	call AICheckEnemyQuarterHP
	jr nc, .pressure_yes
	call CheckPlayerMoveTypeMatchups
	ld a, [wEnemyAISwitchScore]
	cp BASE_AI_SWITCH_SCORE
	jr c, .pressure_yes
	pop bc
	and a
	ret

.pressure_yes
	pop bc
	scf
	ret

.AddUpsideByA
	and a
	ret z
	ld d, a
	ld a, b
	add d
	ld b, a
	ret

.AddDownsideByA
	and a
	ret z
	ld d, a
	ld a, c
	add d
	ld c, a
	ret

BossAI_ClampSignedLookaheadDelta:
	bit 7, a
	jr z, .clamp_pos
	cpl
	inc a
	cp BOSS_AI_LOOKAHEAD_BONUS_CAP + 1
	jr c, .restore_neg
	ld a, BOSS_AI_LOOKAHEAD_BONUS_CAP
.restore_neg
	cpl
	inc a
	ret

.clamp_pos
	cp BOSS_AI_LOOKAHEAD_BONUS_CAP + 1
	ret c
	ld a, BOSS_AI_LOOKAHEAD_BONUS_CAP
	ret

BossAI_GetPrimaryThreatType:
	ld d, 0
	ld e, 0
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.r_loop
	ld a, c
	and a
	jr z, .fallback
	ld a, [hli]
	and a
	jr z, .fallback
	push hl
	push de
	push bc
	call BossAI_GetRevealedMoveThreatTypeAndSeverity
	push af
	ld a, b
	ld [wBossAITemp], a
	pop af
	pop bc
	pop de
	pop hl
	jr nc, .r_next
	cp d
	jr c, .r_next
	ld d, a
	ld a, [wBossAITemp]
	ld e, a
.r_next
	dec c
	jr nz, .r_loop

.fallback
	ld a, d
	and a
	jr z, .plausible
	ld a, e
	scf
	ret

.plausible
	ld hl, BossAI_PlausibleThreatTypes
	xor a
	ld d, a
	ld e, a
.p_loop
	ld a, [hli]
	cp -1
	jr z, .hp_fallback
	ld b, a
	push hl
	ld a, b
	call BossAI_TestPlausibleMaskBit
	pop hl
	jr nc, .p_loop
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	cp d
	jr c, .p_loop
	ld d, a
	ld a, b
	ld e, a
	jr .p_loop

.hp_fallback
	ld a, d
	and a
	jr nz, .done
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestPlausibleMaskBit
	jr nc, .none
	ld hl, BossAIHiddenPowerThreatTypes
.hp_loop
	ld a, [hli]
	cp -1
	jr z, .done
	ld b, a
	push hl
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop hl
	cp d
	jr c, .hp_loop
	ld d, a
	ld a, b
	ld e, a
	jr .hp_loop

.done
	ld a, d
	and a
	jr z, .none
	ld a, e
	scf
	ret

.none
	and a
	ret

BossAI_GetRevealedMoveThreatTypeAndSeverity:
	and a
	ret z
	ld c, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetPlausibleMaskBit
	and a
	ret

.check_power
	ld a, c
	dec a
	ld hl, Moves + MOVE_POWER
	call GetMoveAttr
	and a
	ret z
	ld a, c
	dec a
	ld hl, Moves + MOVE_TYPE
	call GetMoveAttr
	ld b, a
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	and a
	ret z
	scf
	ret

BossAI_GetTypeThreatSeverityVsEnemyMon:
	push hl
	ld hl, wEnemyMonType1
	predef CheckTypeMatchup
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 4
	ld a, 6
	ret nc
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 2
	ld a, 3
	ret nc
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	ld a, 1
	ret nc
	xor a
	ret

BossAI_GetTierPlausibleRiskWeight:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_LATE
	ret z
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ld a, BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_MID
	ret z
	ld a, BOSS_AI_PLAUSIBLE_RISK_WEIGHT_TIER_EARLY
	ret

BossAI_GetScoutRollThreshold:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, BOSS_AI_SCOUT_PROB_TIER_LATE
	ret z
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ld a, BOSS_AI_SCOUT_PROB_TIER_MID
	ret z
	ld a, BOSS_AI_SCOUT_PROB_TIER_EARLY
	ret

BossAI_GetActiveSpeciesSeenBit:
	call BossAI_GetActiveSpeciesSeenIndex
	and a
	ret z
	dec a
	ld e, a
	ld d, 1
.bit
	ld a, e
	and a
	jr z, .done
	sla d
	dec e
	jr .bit
.done
	ld a, d
	scf
	ret

BossAI_IsActiveSpeciesScouted:
	call BossAI_GetActiveSpeciesSeenBit
	ret nc
	ld b, a
	ld a, [wBossAIScoutedMask]
	and b
	jr z, .no
	scf
	ret
.no
	and a
	ret

BossAI_SetActiveSpeciesScouted:
	call BossAI_GetActiveSpeciesSeenBit
	ret nc
	ld b, a
	ld a, [wBossAIScoutedMask]
	or b
	ld [wBossAIScoutedMask], a
	ret

BossAI_ShouldScout:
	call BossAI_IsActiveSpeciesScouted
	jr c, .no
	call BossAI_GetPrimaryThreatType
	jr nc, .no
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	cp 3
	jr c, .no
	call BossAI_HasAnyKOMove
	jr c, .no
	call BossAI_GetScoutRollThreshold
	ld b, a
	call Random
	cp b
	jr nc, .no
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAITraceRiskFlags]
	or 1
	ld [wBossAITraceRiskFlags], a
ENDC
	scf
	ret
.no
	and a
	ret

BossAI_UpdateRepeatTracker:
	ld a, [wCurEnemyMove]
	ld b, a
	ld a, [wBossAILastChosenMove]
	cp b
	jr nz, .new_move
	ld a, [wBossAIRepeatCount]
	inc a
	ld [wBossAIRepeatCount], a
	ret

.new_move
	ld a, b
	ld [wBossAILastChosenMove], a
	ld a, 1
	ld [wBossAIRepeatCount], a
	ret

BossAI_MarkScoutedIfScoutMove:
	ld a, [wCurEnemyMove]
	and a
	ret z
	call AIGetEnemyMove
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .mark
	cp EFFECT_SUBSTITUTE
	ret nz
.mark
	call BossAI_SetActiveSpeciesScouted
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAITraceRiskFlags]
	or 2
	ld [wBossAITraceRiskFlags], a
ENDC
	ret

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
	ld h, a
	ld a, [wOTPartyCount]
	cp h
	jr z, .done
	jr c, .done
	ld a, [wBossAITemp5]
	cp BOSS_AI_SWITCH_CANDIDATE_CAP
	jr nc, .done
	ld a, [wCurOTMon]
	cp h
	jr z, .next

	ld hl, wOTPartyMon1HP
	ld a, h
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

BossAI_ComputeSwitchCandidateRisk:
	ld c, a
	dec c
	ld b, 0
	ld hl, wOTPartySpecies
	add hl, bc
	ld a, [hl]
	and a
	jr z, .hard_risk
	cp $ff
	jr z, .hard_risk
	ld [wCurSpecies], a
	call GetBaseData

	ld b, 0
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
.mask_loop
	ld a, [hli]
	cp -1
	jr z, .hp_risk
	ld c, a
	push hl
	ld a, c
	call BossAI_TestPlausibleMaskBit
	pop hl
	jr nc, .mask_loop
	ld a, c
	call .AddTypeRisk
	jr .mask_loop

.hp_risk
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestPlausibleMaskBit
	jr nc, .done
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

.done
	ld a, b
	cp 100
	ret c
	ld a, 99
	ret

.hard_risk
	ld a, 99
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
	ld hl, wBaseType1
	predef CheckTypeMatchup
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

BossAI_ShouldSackInsteadOfSwitch:
	call AICheckEnemyQuarterHP
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

BossAI_MaybeMarkScoutPivot:
	call BossAI_ShouldScout
	ret nc
	call BossAI_SetActiveSpeciesScouted
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAITraceRiskFlags]
	or 4
	ld [wBossAITraceRiskFlags], a
ENDC
	ret

BossAI_PlausibleThreatTypes:
	db NORMAL
	db FIGHTING
	db FLYING
	db POISON
	db GROUND
	db ROCK
	db BUG
	db GHOST
	db STEEL
	db FIRE
	db WATER
	db GRASS
	db ELECTRIC
	db PSYCHIC_TYPE
	db ICE
	db DRAGON
	db DARK
	db -1

BossAIHiddenPowerThreatTypes:
	db GROUND
	db ICE
	db GRASS
	db ELECTRIC
	db -1

IF DEF(BOSS_AI_TRACE)
BossAI_TraceTopMoves:
	ld a, [wBossAITier]
	and a
	ret z

	ld hl, wBossAITraceTopMoves
	xor a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ld hl, wBossAITraceTopScores
	ld a, $ff
	ld [hli], a
	ld [hli], a
	ld [hl], a

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	ret z
	ld b, a ; move id
	ld a, [hl]
	cp 80
	jr nc, .next
	call .InsertCandidate
.next
	inc hl
	inc de
	dec c
	jr nz, .loop
	ret

.InsertCandidate
	ld d, a ; candidate score
	ld a, [wBossAITraceTopScores]
	cp d
	jr c, .check_second
	jr z, .check_second
	ld a, [wBossAITraceTopScores + 1]
	ld [wBossAITraceTopScores + 2], a
	ld a, [wBossAITraceTopMoves + 1]
	ld [wBossAITraceTopMoves + 2], a
	ld a, [wBossAITraceTopScores]
	ld [wBossAITraceTopScores + 1], a
	ld a, [wBossAITraceTopMoves]
	ld [wBossAITraceTopMoves + 1], a
	ld a, d
	ld [wBossAITraceTopScores], a
	ld a, b
	ld [wBossAITraceTopMoves], a
	ret

.check_second
	ld a, [wBossAITraceTopScores + 1]
	cp d
	jr c, .check_third
	jr z, .check_third
	ld a, [wBossAITraceTopScores + 1]
	ld [wBossAITraceTopScores + 2], a
	ld a, [wBossAITraceTopMoves + 1]
	ld [wBossAITraceTopMoves + 2], a
	ld a, d
	ld [wBossAITraceTopScores + 1], a
	ld a, b
	ld [wBossAITraceTopMoves + 1], a
	ret

.check_third
	ld a, [wBossAITraceTopScores + 2]
	cp d
	ret c
	ret z
	ld a, d
	ld [wBossAITraceTopScores + 2], a
	ld a, b
	ld [wBossAITraceTopMoves + 2], a
	ret
ENDC

BossAITierWeights:
; ko, denyko, tempo, setup, status, role, risk
	db 4, 2, 1, 1, 1, 1, 2 ; early
	db 5, 3, 2, 2, 1, 1, 2 ; mid
	db 7, 4, 4, 2, 2, 3, 1 ; late

BossAIDenyKOEffects:
	db EFFECT_SLEEP
	db EFFECT_PARALYZE
	db EFFECT_CONFUSE
	db EFFECT_HEAL
	db EFFECT_MORNING_SUN
	db EFFECT_SYNTHESIS
	db EFFECT_MOONLIGHT
	db EFFECT_PROTECT
	db EFFECT_SUBSTITUTE
	db EFFECT_LEECH_SEED
	db EFFECT_REFLECT
	db EFFECT_LIGHT_SCREEN
	db EFFECT_FORCE_SWITCH
	db -1

BossAIStatusEffects:
	db EFFECT_SLEEP
	db EFFECT_PARALYZE
	db EFFECT_CONFUSE
	db EFFECT_POISON
	db EFFECT_TOXIC
	db EFFECT_LEECH_SEED
	db -1

BossAIChuckRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_LOCK_ON
	db EFFECT_PRIORITY_HIT
	db -1

BossAIJasmineRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_PROTECT
	db EFFECT_RAIN_DANCE
	db -1

BossAIPryceRoleEffects:
	db EFFECT_SPEED_DOWN_HIT
	db EFFECT_FORCE_SWITCH
	db EFFECT_HEAL
	db EFFECT_MORNING_SUN
	db EFFECT_SYNTHESIS
	db EFFECT_MOONLIGHT
	db -1

BossAIClairRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_SPEED_UP
	db EFFECT_SPEED_UP_2
	db EFFECT_RESET_STATS
	db EFFECT_RAIN_DANCE
	db -1

BossAIWillRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_REFLECT
	db EFFECT_LEECH_SEED
	db EFFECT_FUTURE_SIGHT
	db -1

BossAIBrunoRoleEffects:
	db EFFECT_PRIORITY_HIT
	db EFFECT_FORESIGHT
	db EFFECT_PROTECT
	db -1

BossAIKarenRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_CONFUSE
	db EFFECT_TOXIC
	db EFFECT_MEAN_LOOK
	db EFFECT_DESTINY_BOND
	db EFFECT_FORCE_SWITCH
	db -1

BossAIKogaRoleEffects:
	db EFFECT_TOXIC
	db EFFECT_SPIKES
	db EFFECT_PROTECT
	db EFFECT_BATON_PASS
	db EFFECT_CONFUSE
	db -1

BossAIChampionRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_RAIN_DANCE
	db EFFECT_SAFEGUARD
	db EFFECT_FORCE_SWITCH
	db -1

BossAIRiskyEffects:
	db EFFECT_SELFDESTRUCT
	db EFFECT_RECOIL_HIT
	db EFFECT_HYPER_BEAM
	db EFFECT_BELLY_DRUM
	db -1
