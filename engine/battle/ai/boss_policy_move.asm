; ============================================================
; engine/battle/ai/boss_policy_move.asm — Move-pick, switch entry, threat-cache, pressure, type, and speed policy block
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================

; Region: Ghost helper
; Concern: Enemy Ghost typing probe for setup and Curse logic
; Layer: POLICY
; Original lines: 12
; ============================================================
; ai-layer: POLICY
BossAI_EnemyIsGhostType:
	ld a, [wEnemyMonType1]
	cp GHOST
	jr z, .yes
	ld a, [wEnemyMonType2]
	cp GHOST
	jr z, .yes
	and a
	ret
.yes
	scf
	ret

; ============================================================
; Region: Move pick
; Concern: Two-pass best/second-best selection and tier dice
; Layer: POLICY
; Original lines: 191
; ============================================================
; ai-layer: POLICY
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
	farcall BossAI_TraceTopMoves
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

; Pick best vs. second-best move based on score gap.
; Gap >= 6: 90% best (230/256)
; Gap >= 3: 75% best (192/256)
; Gap <  3: 60% best (154/256)
; Keeps boss decisions weighted but non-deterministic.
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
	push bc
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	inc e
	dec d
	jr nz, .loop

.none
	and a
	ret

; ============================================================
; Region: Threat caches (active)
; Concern: Public-threat and revealed-priority cache wrappers
; Layer: PLATFORM
; Original lines: 165
; ============================================================
; ai-layer: PLATFORM
BossAI_PlayerHasPublicThreatVsEnemy:
	ld a, [wBossAIPublicThreatCache]
	inc a
	jr z, .miss
	dec a
	rrca
	ret
.miss
	call BossAI_PlayerHasPublicThreatVsEnemyUncached
	push af
	sbc a, a
	and 1
	ld [wBossAIPublicThreatCache], a
	pop af
	ret

; ai-layer: PLATFORM
BossAI_PlayerHasPublicThreatVsEnemyUncached:
	call BossAI_HasRevealedSuperEffectiveMove
	jr c, .yes

	ld hl, wPlayerUsedMoves
	ld a, [hl]
	and a
	jr z, .public_type_fallback
	ld d, NUM_MOVES

.used_move_loop
	ld a, [hli]
	and a
	jr z, .public_type_fallback
	push hl
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .next_used_move
	inc hl
	call BossAI_GetMoveByte
	ld c, a
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .next_used_move
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr nc, .yes_pop_hl

.next_used_move
	pop hl
	dec d
	jr nz, .used_move_loop
	jr .public_type_fallback

.no
	and a
	ret

.yes_pop_hl
	pop hl
.yes
	scf
	ret

.public_type_fallback
	ld a, [wBattleMonType1]
	ld c, a
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .unknown_second_type
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr nc, .yes
.unknown_second_type
	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	jr z, .no
	ld a, c
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .no
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr nc, .yes
	jr .no

; ai-layer: PLATFORM
BossAI_PlayerHasRevealedPriorityThreat:
	ld a, [wBossAIRevealedPriorityCache]
	inc a
	jr z, .miss
	dec a
	rrca
	ret
.miss
	call BossAI_PlayerHasRevealedPriorityThreatUncached
	push af
	sbc a, a
	and 1
	ld [wBossAIRevealedPriorityCache], a
	pop af
	ret

; ai-layer: PLATFORM
BossAI_PlayerHasRevealedPriorityThreatUncached:
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.loop
	ld a, [hli]
	and a
	jr z, .no
	push hl
	push bc
	ld b, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_PRIORITY_HIT
	jr nz, .next
	ld a, b
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .next
	ld d, a
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	ld e, a
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .next
	ld a, e
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr c, .next
	call AICheckEnemyQuarterHP_HL
	jr nc, .yes_pop
	call AICheckEnemyHalfHP_HL
	jr c, .next
	ld a, d
	cp 80
	jr nc, .yes_pop
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr nc, .yes_pop

.next
	pop bc
	pop hl
	dec c
	jr nz, .loop

.no
	and a
	ret

.yes_pop
	pop bc
	pop hl
	scf
	ret

; ============================================================
; Region: Type-matchup (no item)
; Concern: No-item type-matchup wrappers and Dragon's Majesty overlay
; Layer: PLATFORM
; Original lines: 150
; ============================================================
; ai-layer: PLATFORM
BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem:
	push bc
	ld c, a
	ldh a, [hBattleTurn]
	push af
	xor a
	ldh [hBattleTurn], a
	ld a, c
	ld hl, wEnemyMonType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	pop bc
	ret

; ai-layer: PLATFORM
BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem:
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
	ret

; ai-layer: PLATFORM
BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem:
	push bc
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld hl, wBattleMonType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	pop bc
	ret

; ai-layer: PLATFORM
BossAI_CheckTypeMatchupNoItem:
	push hl
	push de
	push bc
	ld d, a
	ld b, [hl]
	inc hl
	ld c, [hl]
	ld a, EFFECTIVE
	ld [wTypeMatchup], a
	ld hl, TypeMatchups

.types_loop
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	cp -1
	jr z, .end
	cp -2
	jr nz, .next
	ld a, BATTLE_VARS_SUBSTATUS1_OPP
	call GetBattleVar
	bit SUBSTATUS_IDENTIFIED, a
	jr nz, .end
	jr .types_loop

.next
	cp d
	jr nz, .nope
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	cp b
	jr z, .yup
	cp c
	jr z, .yup
	inc hl
	jr .types_loop

.nope
	inc hl
	inc hl
	jr .types_loop

.yup
	push hl
	xor a
	ldh [hDividend + 0], a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	call BossAI_ApplyDragonsMajestyNoItem
	ldh [hMultiplicand + 2], a
	ld a, [wTypeMatchup]
	ldh [hMultiplier], a
	call Multiply
	ld a, 10
	ldh [hDivisor], a
	push bc
	ld b, 4
	call Divide
	pop bc
	ldh a, [hQuotient + 3]
	ld [wTypeMatchup], a
	pop hl
	jr .types_loop

.end
	pop bc
	pop de
	pop hl
	ret

; ai-layer: PLATFORM
BossAI_ApplyDragonsMajestyNoItem:
; Mirror Dragon's Majesty for boss type-only heuristics. These callers model
; damaging type pressure without peeking at held items, so a Dragon attacker
; treats a type-chart immunity as a resistance just like real damage does.
	and a
	ret nz
	push hl
	ldh a, [hBattleTurn]
	and a
	jr z, .player_user
	ld hl, wEnemyMonType1
	jr .got_user_types

.player_user
	ld hl, wBattleMonType1

.got_user_types
	ld a, [hli]
	cp DRAGON
	jr z, .has_dragon
	ld a, [hl]
	cp DRAGON
	jr z, .has_dragon
	pop hl
	xor a
	ret

.has_dragon
	pop hl
	ld a, NOT_VERY_EFFECTIVE
	ret

; ============================================================
; Region: Pressure scoring
; Concern: KO pressure, scored power, and known modifier stack
; Layer: POLICY
; Original lines: 352
; ============================================================
; ai-layer: POLICY
BossAI_CurrentEnemyMoveHasKOPressure:
	call BossAI_CurrentEnemyMovePressureScore
	ld d, a
	and a
	jr z, .no
	call AICheckPlayerQuarterHP_HL
	jr nc, .low_hp
	call AICheckPlayerHalfHP_HL
	jr nc, .half_hp
	ld a, d
	cp 4
	jr nc, .yes
	jr .no

.low_hp
	ld a, d
	cp 1
	jr nc, .yes
	jr .no

.half_hp
	ld a, d
	cp 3
	jr nc, .yes

.no
	and a
	ret

.yes
	scf
	ret

; ai-layer: POLICY
BossAI_CurrentEnemyMovePressureScore:
	call BossAI_CurrentEnemyMoveScoredPower
	and a
	jr z, .none
	ld b, 0
	cp 100
	jr c, .check_mid_power
	ld b, 2
	jr .type_matchup

.check_mid_power
	cp 70
	jr c, .type_matchup
	ld b, 1

.type_matchup
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .none
	cp EFFECTIVE
	jr c, .resisted
	cp EFFECTIVE * 4
	jr nc, .plus_two
	cp EFFECTIVE * 2
	jr nc, .plus_one
	jr .stab

.plus_two
	inc b
.plus_one
	inc b

.stab
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld c, a
	ld a, [wEnemyMonType1]
	cp c
	jr z, .stab_bonus
	ld a, [wEnemyMonType2]
	cp c
	jr nz, .imperial_scales

.stab_bonus
	inc b
	jr .imperial_scales

.resisted
	ld a, b
	and a
	jr z, .done
	dec b
	jr .imperial_scales

.imperial_scales
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr nc, .apply_modifiers
	ld a, [wBattleMonType1]
	cp DRAGON
	jr z, .dragon_defender
	ld a, [wBattleMonType2]
	cp DRAGON
	jr nz, .apply_modifiers

.dragon_defender
	ld a, b
	and a
	jr z, .done
	dec b

.apply_modifiers
	call BossAI_ApplyEnemyKnownPressureModifiers

.cap
	ld a, b
	cp 5
	ret c
	ld a, 4
	ret

.done
	ld a, b
	ret

.none
	xor a
	ret

; ai-layer: POLICY
BossAI_CurrentEnemyMoveScoredPower:
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SOLARBEAM
	jr z, .solar_power
	cp EFFECT_REVERSAL
	jr z, .reversal_power
	jr .raw_power

.solar_power
	ld a, [wBattleWeather]
	cp WEATHER_SUN
	jr z, .raw_power
	ld a, [wEnemySubStatus3]
	bit SUBSTATUS_CHARGED, a
	jr nz, .raw_power
	xor a
	ret

.reversal_power
	call AICheckEnemyQuarterHP_HL
	jr nc, .reversal_high
	call AICheckEnemyHalfHP_HL
	jr nc, .reversal_mid
	jr .raw_power

.reversal_high
	ld a, 100
	jr .scale

.reversal_mid
	ld a, 70
	jr .scale

.raw_power
	ld a, [wEnemyMoveStruct + MOVE_POWER]
.scale
	jp BossAI_ScaleMovePowerByBaseStatRatio

BossAI_ScaleMovePowerByBaseStatRatio:
; Scale raw move power by attacker_base/defender_base ratio on the
; relevant stat axis. PHYSICAL uses Atk/Def; SPECIAL uses SpA/SpD.
; Both sides use base stats only (public info — no player IV/EV reads).
; Stage and held-item multipliers are NOT applied here yet; that layer
; lands in a follow-up using computed stats (stat modifiers multiply
; the COMPUTED stat including the +5 floor and IV/EV term, so they
; must be applied in computed-stat space, not via base × multiplier).
;
; Input:  a = raw power (0 means status — returned as-is)
; Output: a = stat-scaled power, clamped to 0..255
; Clobbers: bc, de, hl, HRAM math UNION
	and a
	ret z
	ld c, a

	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL  ; carry set if PHYSICAL, clear if SPECIAL
	push af

	ld a, [wEnemyMonSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	pop af
	push af
	ld a, [wCurBaseData + BASE_ATK]
	jr c, .got_atk
	ld a, [wCurBaseData + BASE_SAT]
.got_atk
	ld d, a

	ld a, [wBattleMonSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	pop af
	ld a, [wCurBaseData + BASE_DEF]
	jr c, .got_def
	ld a, [wCurBaseData + BASE_SDF]
.got_def
	and a
	jr z, .div_zero
	ld b, a

	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, d
	ldh [hMultiplicand + 2], a
	ld a, c
	ldh [hMultiplier], a
	call Multiply

	ld a, b
	ldh [hDivisor], a
	ld b, 4
	call Divide

	ldh a, [hQuotient + 0]
	or a
	jr nz, .clamp_max
	ldh a, [hQuotient + 1]
	or a
	jr nz, .clamp_max
	ldh a, [hQuotient + 2]
	or a
	jr nz, .clamp_max
	ldh a, [hQuotient + 3]
	ret

.clamp_max
	ld a, 255
	ret

.div_zero
	ld a, c
	ret

; ai-layer: POLICY
BossAI_ApplyEnemyKnownPressureModifiers:
	call BossAI_ApplyEnemyHeldItemPressure
	call BossAI_ApplyEnemyOffensivePassivePressure
	call BossAI_ApplyPlayerDefensivePassivePressure
	ret

; ai-layer: POLICY
BossAI_ApplyEnemyHeldItemPressure:
	call BossAI_GetEnemyHeldEffect
	cp HELD_LIFE_ORB
	jr z, .boost_one
	cp HELD_CHOICE_BAND
	jr z, .choice_band
	cp HELD_CHOICE_SPECS
	jr z, .choice_specs
	cp HELD_EXPERT_BELT
	jr z, .expert_belt
	cp HELD_MUSCLE_BAND
	jr z, .muscle_band
	cp HELD_WISE_GLASSES
	jr z, .wise_glasses
	cp HELD_METRONOME
	jr z, .metronome
	ret

.choice_band
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	ret nc
	jr .boost_one

.choice_specs
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	ret c
	jr .boost_one

.expert_belt
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	ret c
	jr .boost_one

.muscle_band
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	ret nc
	jr .boost_one

.wise_glasses
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	ret c
	jr .boost_one

.metronome
	ld a, [wEnemyMetronomeCount]
	and a
	ret z
	inc b
	cp 4
	ret c
	jr .boost_one

.boost_one
	inc b
	ret

; ai-layer: POLICY
BossAI_ApplyEnemyOffensivePassivePressure:
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	cp NORMAL
	jr nz, .fire
	ld a, NORMAL
	call BossAI_EnemyTypeContribution
	and a
	jr z, .fire
	inc b

.fire
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	cp FIRE
	jr nz, .ghost
	call BossAI_EnemyBelowOneThirdHP
	jr nc, .ghost
	ld a, FIRE
	call BossAI_EnemyTypeContribution
	and a
	jr z, .ghost
	inc b

.ghost
	ld a, [wBattleMonStatus]
	and a
	ret z
	ld a, GHOST
	call BossAI_EnemyTypeContribution
	and a
	ret z
	inc b
	ret

; ai-layer: POLICY
BossAI_ApplyPlayerDefensivePassivePressure:
	ld a, PSYCHIC_TYPE
	call BossAI_PlayerTypeContribution
	and a
	jr z, .ground
	call BossAI_DecPressureB

.ground
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .bug
	ld a, GROUND
	call BossAI_PlayerTypeContribution
	and a
	jr z, .bug
	call BossAI_DecPressureB

.bug
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	jr nc, .water
	ld a, BUG
	call BossAI_PlayerTypeContribution
	and a
	jr z, .ice
	call BossAI_DecPressureB
	jr .ice

.water
	ld a, WATER
	call BossAI_PlayerTypeContribution
	and a
	jr z, .ice
	call BossAI_DecPressureB

.ice
	push bc
	call AICheckPlayerHalfHP_HL
	pop bc
	ret nc
	ld a, ICE
	call BossAI_PlayerTypeContribution
	and a
	ret z
	call BossAI_DecPressureB
	ret

; ai-layer: POLICY
BossAI_DecPressureB:
	ld a, b
	and a
	ret z
	dec b
	ret

; ai-layer: POLICY
BossAI_EnemyBelowOneThirdHP:
	push hl
	push de
	push bc
	ld hl, wEnemyMonHP
	ld b, [hl]
	inc hl
	ld c, [hl]
	ld hl, wEnemyMonMaxHP
	ld d, [hl]
	inc hl
	ld e, [hl]
	ld h, b
	ld l, c
	add hl, bc
	add hl, bc
	jr c, .not_below
	ld a, h
	cp d
	jr c, .below
	jr nz, .not_below
	ld a, l
	cp e
	jr c, .below

.not_below
	pop bc
	pop de
	pop hl
	and a
	ret

.below
	pop bc
	pop de
	pop hl
	scf
	ret

; ============================================================
; Region: Move category + type contribution
; Concern: Move category, accuracy risk, and type-contribution helpers
; Layer: PLATFORM
; Original lines: 103
; ============================================================
; ai-layer: PLATFORM
BossAI_CurrentEnemyMoveCategory:
	push hl
	push de
	push bc
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	callfar TypePassive_GetEffectiveMoveCategory_Far
	ld e, a
	pop af
	ldh [hBattleTurn], a
	ld a, e
	pop bc
	pop de
	pop hl
	ret

; ai-layer: PLATFORM
BossAI_CurrentEnemyMoveAccuracyRisky:
	push bc
	ld a, [wEnemyMoveStruct + MOVE_ACC]
	cp 80 percent
	jr nc, .not_risky
	ld b, a
	ld a, FLYING
	call BossAI_EnemyTypeContribution
	and a
	jr z, .risky
	ld a, b
	cp 75 percent
	jr nc, .not_risky

.risky
	pop bc
	scf
	ret

.not_risky
	pop bc
	and a
	ret

; ai-layer: PLATFORM
BossAI_CurrentMoveDarkShieldEligible:
	push hl
	push de
	push bc
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	callfar TypePassive_IsDarkShieldEligibleEffect_Far
	ld e, a
	pop af
	ldh [hBattleTurn], a
	ld a, e
	pop bc
	pop de
	pop hl
	and a
	ret

; ai-layer: PLATFORM
BossAI_PlayerTypeContribution:
	ld hl, wBattleMonType1
	jr BossAI_TypeContributionAtHL

; ai-layer: PLATFORM
BossAI_EnemyTypeContribution:
	ld hl, wEnemyMonType1

; ai-layer: PLATFORM
BossAI_TypeContributionAtHL:
	push bc
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	ld a, c
	cp b
	jr z, .full
	xor a
	pop bc
	ret

.dual
	ld a, c
	cp b
	jr z, .half
	ld a, [hl]
	cp b
	jr z, .half
	xor a
	pop bc
	ret

.half
	ld a, 1
	pop bc
	ret

.full
	ld a, 2
	pop bc
	ret

; ============================================================
; Region: Public-faster (speed)
; Concern: Public speed predicate with known Choice Scarf handling
; Layer: POLICY
; Original lines: 63
; ============================================================
; ai-layer: POLICY
BossAI_PublicEnemyFaster:
	push hl
	push de
	push bc
	ld a, [wCurSpecies]
	push af
	ld a, [wBattleMonSpecies]
	and a
	jr z, .enemy_not_faster
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseSpeed]
	ld b, a
	ld a, [wEnemyMonSpecies]
	and a
	jr nz, .got_enemy_species
	ld a, [wTempEnemyMonSpecies]

.got_enemy_species
	and a
	jr z, .enemy_not_faster
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseSpeed]
	ld c, a
	cp b
	jr c, .check_choice_scarf
	jr z, .check_choice_scarf

.enemy_faster
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	pop bc
	pop de
	pop hl
	scf
	ret

.check_choice_scarf
	call BossAI_GetEnemyHeldEffect
	cp HELD_CHOICE_SCARF
	jr nz, .enemy_not_faster
	ld a, c
	srl a
	add c
	jr c, .enemy_faster
	cp b
	jr c, .enemy_not_faster
	jr z, .enemy_not_faster
	jr .enemy_faster

.enemy_not_faster
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	pop bc
	pop de
	pop hl
	and a
	ret

; ============================================================
