; ============================================================
; engine/battle/ai/boss_policy_move.asm - Boss AI move-policy guarded fragments
; Split out of boss.asm per docs/boss_ai_organization_plan.md section 3.
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; Included with BOSSAI_EMIT_* guards from main.asm to preserve ROM byte order.
; ============================================================

if DEF(BOSSAI_EMIT_MOVE_ADAPTIVE_LEAD)
; ============================================================
; Region: Adaptive lead
; Concern: Pre-battle weighted opener for selected trainers
; Layer: POLICY
; Original lines: 144
; ============================================================
; ai-layer: POLICY
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
	ld a, [wOtherTrainerClass]
	and a
	ret z
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a
	ld hl, AdaptiveLeadMap
.loop
	ld a, [hli]
	and a
	ret z
	cp b
	jr nz, .next
	ld a, [hli]
	cp c
	jr z, .enabled
	jr .loop
.next
	inc hl
	jr .loop

.enabled
	scf
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

endc

if DEF(BOSSAI_EMIT_MOVE_APPLY_MODEL)
; ============================================================
; Region: Move-scoring overlay
; Concern: BossAI_ApplyMoveModel gates and scoring heuristics
; Layer: POLICY
; Original lines: 1823
; ============================================================
; ai-layer: POLICY
BossAI_ApplyMoveModel:
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_ResetTurnCaches
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask
IF DEF(BOSS_AI_TRACE)
	call .ClearMoveModelTrace
ENDC

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	ret z
IF DEF(BOSS_AI_TRACE)
	call .TracePreModelScore
ENDC
	ld a, [hl]
	cp 80
	jr nc, .scored
	push bc
	push de
	push hl
	call .ScoreMove
	pop hl
	pop de
	pop bc
.scored
IF DEF(BOSS_AI_TRACE)
	call .TracePostModelScore
ENDC
.next
	inc hl
	inc de
	dec c
	jr nz, .loop
	ret

IF DEF(BOSS_AI_TRACE)
.ClearMoveModelTrace
	ld hl, wBossAITracePreModelScores
	ld c, NUM_MOVES * 2
	ld a, $ff
.clear_trace_loop
	ld [hli], a
	dec c
	jr nz, .clear_trace_loop
	ret

.TracePreModelScore
	push af
	push bc
	push de
	push hl
	ld d, [hl]
	ld a, NUM_MOVES
	sub c
	ld c, a
	ld b, 0
	ld hl, wBossAITracePreModelScores
	add hl, bc
	ld [hl], d
	pop hl
	pop de
	pop bc
	pop af
	ret

.TracePostModelScore
	push af
	push bc
	push de
	push hl
	ld d, [hl]
	ld a, NUM_MOVES
	sub c
	ld c, a
	ld b, 0
	ld hl, wBossAITracePostModelScores
	add hl, bc
	ld [hl], d
	pop hl
	pop de
	pop bc
	pop af
	ret
ENDC

.ScoreMove
	ld a, h
	ld [wBossAIScorePtr], a
	ld a, l
	ld [wBossAIScorePtr + 1], a
	ld a, [de]
	call AIGetEnemyMove_HL

	xor a
	ld [wBossAIMoveChoiceReady], a
	call .HeldItemMoveBlocked
	ret c
	call .DamagingMoveBlockedByTypeImmunity
	ret c
	call .GhostCurseBlockedPublicly
	ret c
	call .PainSplitBlockedPublicly
	ret c

	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .skip_ko
	push hl
	call BossAI_CurrentEnemyMoveHasKOPressure
	pop hl
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
	call .DenyKOMoveAnswersPublicThreat
	jr nc, .skip_denyko
	ld c, 1
	call .EncourageByTierWeight

.skip_denyko
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .skip_tempo
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PRIORITY_HIT
	jr nz, .check_type_tempo
	call BossAI_PublicEnemyFaster
	jr c, .skip_tempo
	jr .tempo_bonus

.check_type_tempo
	push hl
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .skip_tempo
	call BossAI_PublicEnemyFaster
	jr nc, .skip_tempo

.tempo_bonus
	ld c, 2
	call .EncourageByTierWeight

.skip_tempo
	call BossAI_IsCurrentEnemySetupMove
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
	call .ApplySetupDisciplineBias

	call .UtilityMoveWouldFailPublicly
	jr nc, .skip_utility_fail
	ld a, 24
	call BossAI_DiscourageScoreHL

.skip_utility_fail
	call .ApplyRecoveryTimingDiscipline
	call .early_stat_drop_discipline

	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	jr nc, .skip_status
	call .StatusMoveWouldFailPublicly
	jr nc, .status_ok
	ld a, 80
	call BossAI_SetScoreHL
	jr .skip_status
.status_ok
	ld c, 4
	call .EncourageByTierWeight
	call .ApplyStatusHardAnswerDiscipline

.skip_status
	call .ApplySetupPunishBias
	call .ApplySpikesLayerBias
	call .ApplyPhazingPlanBias
	call .ApplyRapidSpinBias
	call .ApplyBatonPassBias
	call .ApplyRevealedAntiSetupAvoidance
	call .ApplyRampMoveBias
	call BossAI_ApplyPlanMoveBias
	call .ApplyChargeMoveBias
	call .ApplyPoisonContactRiskBias
	call .ApplyDarkShieldChanceBias
	call .ApplyLifeOrbRecoilBias
	call .ApplyDestinyBondTradeBias
	call .ApplyCounterCoatTradeBias
	call .ApplyRevealedEffectMatrixBias
	call .ApplyChoiceFirstLockRegret
	call .ApplySelfKOTradeDiscipline
	call BossAI_ApplyScoutMoveBias
	call BossAI_ApplyRepeatPenalty
	push hl
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	farcall BossAI_ApplyDamageDominanceBias
	pop hl

	call .PureStatusHardBlockOnStrongDamage

	call .HasKOLine
	ret c

	call BossAI_CurrentEnemyMoveAccuracyRisky
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

.HeldItemMoveBlocked
	call BossAI_EnemyChoiceLockedMove
	jr nc, .check_assault_vest
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	cp b
	jr z, .check_assault_vest
	ld a, 80
	call BossAI_SetScoreHL
	scf
	ret

.check_assault_vest
	call BossAI_GetEnemyHeldEffect
	cp HELD_ASSAULT_VEST
	jr nz, .held_item_legal
	call .AssaultVestBlocksCurrentMove
	jr nc, .held_item_legal
	ld a, 80
	call BossAI_SetScoreHL
	scf
	ret

.held_item_legal
	and a
	ret

.DamagingMoveBlockedByTypeImmunity
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .damage_type_legal
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_HIDDEN_POWER
	jr z, .damage_type_legal
	push hl
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	pop hl
	ld a, [wTypeMatchup]
	and a
	jr nz, .damage_type_legal
	ld a, 80
	call BossAI_SetScoreHL
	scf
	ret
.damage_type_legal
	and a
	ret

.AssaultVestBlocksCurrentMove
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	and a
	jr z, .assault_vest_blocked
	cp $ff
	jr z, .assault_vest_blocked
	cp SEISMIC_TOSS
	jr z, .assault_vest_allowed
	cp NIGHT_SHADE
	jr z, .assault_vest_allowed
	cp DRAGON_RAGE
	jr z, .assault_vest_allowed
	cp SONICBOOM
	jr z, .assault_vest_allowed
	cp PSYWAVE
	jr z, .assault_vest_allowed
	cp COUNTER
	jr z, .assault_vest_allowed
	cp BIDE
	jr z, .assault_vest_allowed
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .assault_vest_blocked
.assault_vest_allowed
	and a
	ret
.assault_vest_blocked
	scf
	ret

.StatusMoveWouldFailPublicly
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call .DarkShieldBlocksStatusEffect
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_LEECH_SEED
	jp z, .check_leech
	cp EFFECT_PARALYZE
	jp z, .check_paralyze
	cp EFFECT_CONFUSE
	jp z, .check_confuse
	cp EFFECT_POISON
	jp z, .check_poison
	cp EFFECT_TOXIC
	jp z, .check_poison
	cp EFFECT_SLEEP
	jp z, .check_sleep
	and a
	ret

.UtilityMoveWouldFailPublicly
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call .DarkShieldBlocksUtilityEffect
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_LIGHT_SCREEN
	jr z, .check_light_screen
	cp EFFECT_REFLECT
	jr z, .check_reflect
	cp EFFECT_SAFEGUARD
	jr z, .check_safeguard
	cp EFFECT_SUBSTITUTE
	jr z, .check_substitute
	cp EFFECT_PROTECT
	jr z, .check_protect
	cp EFFECT_DISABLE
	jr z, .check_disable
	cp EFFECT_ENCORE
	jp z, .check_encore
	cp EFFECT_MEAN_LOOK
	jp z, .check_mean_look
	cp EFFECT_DREAM_EATER
	jp z, .check_dream_eater
	cp EFFECT_NIGHTMARE
	jp z, .check_nightmare
	cp EFFECT_RAIN_DANCE
	jp z, .check_rain_dance
	cp EFFECT_SUNNY_DAY
	jp z, .check_sunny_day
	cp EFFECT_HEAL
	jp z, .check_heal
	cp EFFECT_MORNING_SUN
	jp z, .check_heal
	cp EFFECT_SYNTHESIS
	jp z, .check_heal
	cp EFFECT_MOONLIGHT
	jp z, .check_heal
	and a
	ret

.check_light_screen
	ld a, [wEnemyScreens]
	bit SCREENS_LIGHT_SCREEN, a
	jp nz, .status_fail
	and a
	ret

.check_reflect
	ld a, [wEnemyScreens]
	bit SCREENS_REFLECT, a
	jp nz, .status_fail
	and a
	ret

.check_safeguard
	ld a, [wEnemyScreens]
	bit SCREENS_SAFEGUARD, a
	jp nz, .status_fail
	and a
	ret

.check_substitute
	ld a, [wEnemySubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	call AICheckEnemyQuarterHP_HL
	jp nc, .status_fail
	and a
	ret

.check_protect
	ld a, [wEnemySubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	and a
	ret

.check_disable
	ld a, [wPlayerDisableCount]
	and a
	jp nz, .status_fail
	ld a, [wLastPlayerCounterMove]
	and a
	jp z, .status_fail
	cp STRUGGLE
	jp z, .status_fail
	and a
	ret

.check_encore
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_ENCORED, a
	jp nz, .status_fail
	ld a, [wLastPlayerMove]
	and a
	jp z, .status_fail
	cp STRUGGLE
	jp z, .status_fail
	cp ENCORE
	jp z, .status_fail
	cp MIRROR_MOVE
	jp z, .status_fail
	and a
	ret

.check_mean_look
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_CANT_RUN, a
	jp nz, .status_fail
	and a
	ret

.check_dream_eater
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	ld a, [wBattleMonStatus]
	and SLP_MASK
	jp z, .status_fail
	and a
	ret

.check_nightmare
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	ld a, [wBattleMonStatus]
	and SLP_MASK
	jp z, .status_fail
	ld a, [wPlayerSubStatus1]
	bit SUBSTATUS_NIGHTMARE, a
	jp nz, .status_fail
	and a
	ret

.check_rain_dance
	ld a, [wBattleWeather]
	cp WEATHER_RAIN
	jp z, .status_fail
	and a
	ret

.check_sunny_day
	ld a, [wBattleWeather]
	cp WEATHER_SUN
	jp z, .status_fail
	and a
	ret

.DarkShieldBlocksStatusEffect
	cp EFFECT_SLEEP
	jr z, .dark_shield_candidate
	cp EFFECT_TOXIC
	jr z, .dark_shield_candidate
	cp EFFECT_POISON
	jr z, .dark_shield_candidate
	cp EFFECT_PARALYZE
	jr z, .dark_shield_candidate
	cp EFFECT_CONFUSE
	jr z, .dark_shield_candidate
	cp EFFECT_LEECH_SEED
	jr z, .dark_shield_candidate
	and a
	ret

.DarkShieldBlocksUtilityEffect
	cp EFFECT_DISABLE
	jr z, .dark_shield_candidate
	cp EFFECT_ENCORE
	jr z, .dark_shield_candidate
	cp EFFECT_SPITE
	jr z, .dark_shield_candidate
	cp EFFECT_ATTRACT
	jr z, .dark_shield_candidate
	cp EFFECT_MEAN_LOOK
	jr z, .dark_shield_candidate
	cp EFFECT_NIGHTMARE
	jr z, .dark_shield_candidate
	cp EFFECT_FORCE_SWITCH
	jr z, .dark_shield_candidate
	cp EFFECT_ATTACK_DOWN
	jr c, .dark_shield_no
	cp EFFECT_EVASION_DOWN + 1
	jr c, .dark_shield_candidate
	cp EFFECT_ATTACK_DOWN_2
	jr c, .dark_shield_no
	cp EFFECT_EVASION_DOWN_2 + 1
	jr c, .dark_shield_candidate
.dark_shield_no
	and a
	ret

.dark_shield_candidate
	ld a, [wPlayerDarkShieldConsumed]
	and a
	jr nz, .dark_shield_no
	ld a, [wBattleMonType1]
	cp DARK
	jr nz, .dark_shield_no
	ld a, [wBattleMonType2]
	cp DARK
	jr nz, .dark_shield_no
	scf
	ret

.check_heal
	call AICheckEnemyMaxHP_HL
	jp c, .status_fail
	and a
	ret

.check_primary_status
	call .PrimaryStatusBlocked
	ret

.check_sleep
	call .PrimaryStatusBlocked
	ret c
; This scorer only evaluates enemy moves, so enemy sleep clause state is the
; side that blocks another sleep attempt into the player's party.
	ld a, [wEnemySleepClauseSlot]
	and a
	jp nz, .status_fail
	ret

.check_paralyze
	call .PrimaryStatusBlocked
	ret c
	call .EnemyStatusMoveTypeMissesPlayer
	ret

.check_confuse
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	ld a, [wPlayerScreens]
	bit SCREENS_SAFEGUARD, a
	jp nz, .status_fail
	ld a, [wPlayerSubStatus3]
	bit SUBSTATUS_CONFUSED, a
	jp nz, .status_fail
	and a
	ret

.EnemyStatusMoveTypeMissesPlayer
; Status scripts that run through type matchup, such as Thunder Wave or Glare,
; fail only on real type-chart immunities. Dragon's Majesty is damage-only.
	push bc
	push de
	push hl
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld d, a
	ld a, [wBattleMonType1]
	ld b, a
	ld a, [wBattleMonType2]
	ld c, a
	ld hl, TypeMatchups

.status_type_loop
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	cp -1
	jr z, .status_type_ok
	cp -2
	jr nz, .status_type_match_move
	ld a, BATTLE_VARS_SUBSTATUS1_OPP
	call GetBattleVar
	bit SUBSTATUS_IDENTIFIED, a
	jr nz, .status_type_ok
	jr .status_type_loop

.status_type_match_move
	cp d
	jr nz, .status_type_skip
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	cp b
	jr z, .status_type_check_multiplier
	cp c
	jr z, .status_type_check_multiplier
	inc hl
	jr .status_type_loop

.status_type_skip
	inc hl
	inc hl
	jr .status_type_loop

.status_type_check_multiplier
	ld a, BANK(TypeMatchups)
	call GetFarByte
	inc hl
	and a
	jr z, .status_type_fail
	jr .status_type_loop

.status_type_ok
	pop af
	ldh [hBattleTurn], a
	pop hl
	pop de
	pop bc
	and a
	ret

.status_type_fail
	pop af
	ldh [hBattleTurn], a
	pop hl
	pop de
	pop bc
	scf
	ret

.check_poison
	call .PrimaryStatusBlocked
	ret c
	ld a, [wBattleMonType1]
	cp POISON
	jr z, .status_fail
	cp STEEL
	jr z, .status_fail
	ld a, [wBattleMonType2]
	cp POISON
	jr z, .status_fail
	cp STEEL
	jr z, .status_fail
	and a
	ret

.check_leech
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jr nz, .status_fail
	bit SUBSTATUS_LEECH_SEED, a
	jr nz, .status_fail
	ld a, [wBattleMonType1]
	cp GRASS
	jr z, .status_fail
	ld a, [wBattleMonType2]
	cp GRASS
	jr z, .status_fail
	and a
	ret

.PrimaryStatusBlocked
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jr nz, .status_fail
	ld a, [wBattleMonStatus]
	and a
	jr nz, .status_fail
	ld a, [wPlayerScreens]
	bit SCREENS_SAFEGUARD, a
	jr nz, .status_fail
	and a
	ret

.status_fail
	scf
	ret

.GhostCurseBlockedPublicly
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_CURSE
	jr nz, .ghost_curse_ok
	call BossAI_EnemyIsGhostType
	jr nc, .ghost_curse_ok
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jr nz, .ghost_curse_block
	ld a, [wPlayerSubStatus1]
	bit SUBSTATUS_CURSE, a
	jr nz, .ghost_curse_block
.ghost_curse_check_self_ko
	call AICheckEnemyHalfHP_HL
	jr c, .ghost_curse_ok
	call .PlayerCantActThisTurnPublicly
	jr c, .ghost_curse_block
	call .EnemyUnderPressure
	jr c, .ghost_curse_ok
.ghost_curse_block
	ld a, 80
	call BossAI_SetScoreHL
	scf
	ret
.ghost_curse_ok
	and a
	ret

.PainSplitBlockedPublicly
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PAIN_SPLIT
	jr nz, .pain_split_ok
	call BossAI_HasAnyKOMove
	jr c, .pain_split_block
	call .PainSplitHasLargePositiveGap
	jr c, .pain_split_ok
.pain_split_block
	ld a, 80
	call BossAI_SetScoreHL
	scf
	ret
.pain_split_ok
	and a
	ret

.PainSplitHasLargePositiveGap
; Return carry if player current HP is at least 2x enemy current HP.
	push hl
	push bc
	ld hl, wEnemyMonHP
	ld b, [hl]
	inc hl
	ld c, [hl]
	sla c
	rl b
	ld hl, wBattleMonHP + 1
	ld a, [hld]
	cp c
	ld a, [hl]
	sbc b
	pop bc
	pop hl
	jr c, .pain_split_gap_no
	scf
	ret
.pain_split_gap_no
	and a
	ret

.PlayerCantActThisTurnPublicly
	ld a, [wBattleMonStatus]
	and SLP_MASK
	jr nz, .player_cant_act
	ld a, [wBattleMonStatus]
	bit FRZ, a
	jr nz, .player_cant_act
	and a
	ret
.player_cant_act
	scf
	ret

.early_stat_drop_discipline
	ld a, [wBossAITier]
	cp AI_TIER_EARLY
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret nz
	call .stat_drop_index
	ret nc
	ld a, [wPlayerSubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jr nz, .early_stat_drop_public_fail
	bit SUBSTATUS_MIST, a
	jr nz, .early_stat_drop_public_fail
	ld b, 0
	ld hl, wPlayerStatLevels
	add hl, bc
	ld a, [hl]
	cp 2
	jr c, .early_stat_drop_public_fail
	ld a, [wEnemyTurnsTaken]
	and a
	jr z, .early_stat_drop_opening
	ld a, BOSS_AI_EARLY_STAT_DROP_AFTER_TURN_PENALTY
	jp BossAI_DiscourageScoreHL

.early_stat_drop_opening
	ld a, BOSS_AI_EARLY_STAT_DROP_OPENING_PENALTY
	jp BossAI_DiscourageScoreHL

.early_stat_drop_public_fail
	ld a, 24
	jp BossAI_DiscourageScoreHL

.stat_drop_index
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_ATTACK_DOWN
	jr c, .not_stat_down
	cp EFFECT_EVASION_DOWN + 1
	jr c, .single_stat_down
	cp EFFECT_ATTACK_DOWN_2
	jr c, .not_stat_down
	cp EFFECT_EVASION_DOWN_2 + 1
	jr nc, .not_stat_down
	sub EFFECT_ATTACK_DOWN_2
	ld c, a
	scf
	ret

.single_stat_down
	sub EFFECT_ATTACK_DOWN
	ld c, a
	scf
	ret

.not_stat_down
	and a
	ret

.ApplySetupPunishBias
	call .PlayerHasMajorSetupBoost
	ret nc
	call .HasKOLine
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_FORCE_SWITCH
	jr z, .setup_punish
	cp EFFECT_RESET_STATS
	jr z, .setup_punish
	cp EFFECT_ENCORE
	ret nz
.setup_punish
	ld a, 8
	jp BossAI_EncourageScoreHL

.ApplySetupDisciplineBias
	call BossAI_IsCurrentEnemySetupMove
	ret nc
	call BossAI_SetupBoostHasFurtherValue
	jr c, .setup_has_value
	ld a, 8
	jp BossAI_DiscourageScoreHL
.setup_has_value
	call BossAI_SetupTurnIsAffordable
	ret c
	ld a, 4
	jp BossAI_DiscourageScoreHL

.ApplyStatusHardAnswerDiscipline
	call BossAI_HasAnyKOMove
	ret nc
	ld a, 5
	jp BossAI_DiscourageScoreHL

.PureStatusHardBlockOnStrongDamage
; Backstop for the "AI picks Confuse Ray when Shadow Ball is 4x SE STAB"
; failure class. The pressure-score path that drives BossAI_HasAnyKOMove
; can miss on edge cases (Psychic-defender decrement, KO-band oracle
; coverage gaps, etc.). This gate is independent: any other move in the
; moveset with raw type matchup vs the active defender of 4x or higher
; hard-blocks pure primary-status moves on this turn.
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	ret nc
	call .HasStrongMatchupDamagingMove
	ret nc
	ld a, 80
	jp BossAI_SetScoreHL

.HasStrongMatchupDamagingMove
; Output: carry set if some OTHER move in our moveset is a damaging move
; with raw type matchup vs the active player defender of at least 4x
; (>= SUPER_EFFECTIVE * 2). Saves and restores wTypeMatchup so callers
; that read it post-call still see the current move's value.
	push bc
	push de
	push hl
	ld a, [wTypeMatchup]
	push af
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	ld d, a
	ld hl, wEnemyMonMoves
	ld c, NUM_MOVES
.hsmdm_loop
	ld a, [hli]
	and a
	jr z, .hsmdm_none
	cp d
	jr z, .hsmdm_skip
	push hl
	push bc
	push de
	call .ScanMoveForStrongMatchup
	pop de
	pop bc
	pop hl
	jr c, .hsmdm_yes
.hsmdm_skip
	dec c
	jr nz, .hsmdm_loop
.hsmdm_none
	pop af
	ld [wTypeMatchup], a
	and a
	pop hl
	pop de
	pop bc
	ret
.hsmdm_yes
	pop af
	ld [wTypeMatchup], a
	scf
	pop hl
	pop de
	pop bc
	ret

.ScanMoveForStrongMatchup
; Input: a = move id (1-indexed). Output: carry if this move is damaging
; (MOVE_POWER > 0) and has raw type matchup vs the active player defender
; >= SUPER_EFFECTIVE * 2 (4x). Clobbers wTypeMatchup (caller restores).
	push bc
	push de
	push hl
	ld d, a
	dec a
	ld hl, Moves + MOVE_POWER
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	and a
	jr z, .smfsm_no
	ld a, d
	dec a
	ld hl, Moves + MOVE_TYPE
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	ld e, a
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	ld a, e
	ld hl, wBattleMonType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	ld a, [wTypeMatchup]
	cp SUPER_EFFECTIVE * 2
	jr c, .smfsm_no
	scf
	jr .smfsm_done
.smfsm_no
	and a
.smfsm_done
	pop hl
	pop de
	pop bc
	ret

.ApplySelfKOTradeDiscipline
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SELFDESTRUCT
	ret nz
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .self_ko_active_immunity
	call .PlayerHasSeenAliveBenchGhost
	jr nc, .self_ko_check_ko
.self_ko_seen_ghost_branch
	ld a, 8
	call BossAI_DiscourageScoreHL
.self_ko_check_ko
	call .HasKOLine
	jr c, .self_ko_has_ko
	call AICheckEnemyQuarterHP_HL
	ret nc
	ld a, 16
	jp BossAI_DiscourageScoreHL
.self_ko_active_immunity
	ld a, 24
	jp BossAI_DiscourageScoreHL
.self_ko_has_ko
	call AICheckEnemyQuarterHP_HL
	jr nc, .self_ko_cashout_good
	call .EnemyUnderPressure
	ret nc
.self_ko_cashout_good
	ld a, 4
	jp BossAI_EncourageScoreHL

.ApplyRecoveryTimingDiscipline
	call .IsCurrentEnemyRecoveryMove
	ret nc
	call BossAI_HasAnyKOMove
	jr c, .discourage_recovery
	call AICheckEnemyHalfHP_HL
	ret nc
.discourage_recovery
	ld a, 6
	jp BossAI_DiscourageScoreHL

.IsCurrentEnemyRecoveryMove
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_HEAL
	jr z, .yes_recovery
	cp EFFECT_MORNING_SUN
	jr z, .yes_recovery
	cp EFFECT_SYNTHESIS
	jr z, .yes_recovery
	cp EFFECT_MOONLIGHT
	jr z, .yes_recovery
	and a
	ret
.yes_recovery
	scf
	ret

.ApplyPhazingPlanBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_FORCE_SWITCH
	ret nz
	call .HasKOLine
	ret c
	ld a, [wPlayerScreens]
	and SCREENS_SPIKES_MASK
	ret z
	call .PlayerHasMajorSetupBoost
	jr c, .phaze_good
	call .PlayerHasRepeatedSwitchPressure
	ret nc
.phaze_good
	ld a, 8
	jp BossAI_EncourageScoreHL

.ApplyRapidSpinBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_RAPID_SPIN
	ret nz
	ld a, [wEnemyScreens]
	and SCREENS_SPIKES_MASK
	ret z
	ld c, 5
	call .EncourageByTierWeight
	ret

.ApplyBatonPassBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_BATON_PASS
	ret nz
	push hl
	call BossAI_FindFirstAliveSwitchCandidate
	pop hl
	jr nc, .baton_bad
	call .EnemyHasBoostToPass
	jr c, .baton_good
.baton_bad
	ld a, 6
	call BossAI_DiscourageScoreHL
	ret
.baton_good
	ld c, 5
	call .EncourageByTierWeight
	ret

.ApplyRevealedAntiSetupAvoidance
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call .IsBoostSetupMove
	ret nc
	call .HasKOLine
	ret c
	call .PlayerHasRevealedAntiSetup
	ret nc
	ld a, 5
	jp BossAI_DiscourageScoreHL

.IsBoostSetupMove
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_DRAGON_DANCE
	jr z, .boost_setup_yes
	cp EFFECT_CALM_MIND
	jr z, .boost_setup_yes
	cp EFFECT_QUIVER_DANCE
	jr z, .boost_setup_yes
	cp EFFECT_CURSE
	jr z, .check_curse_boost
	cp EFFECT_ATTACK_UP
	jr c, .boost_setup_no
	cp EFFECT_EVASION_UP + 1
	jr c, .boost_setup_yes
	cp EFFECT_ATTACK_UP_2
	jr c, .boost_setup_no
	cp EFFECT_EVASION_UP_2 + 1
	jr c, .boost_setup_yes
	jr .boost_setup_no
.check_curse_boost
	call BossAI_EnemyIsGhostType
	jr c, .boost_setup_no
.boost_setup_yes
	scf
	ret
.boost_setup_no
	and a
	ret

.PlayerHasRevealedAntiSetup
	ld a, EFFECT_RESET_STATS
	call .PlayerHasRevealedEffectA
	ret c
	ld a, EFFECT_FORCE_SWITCH
	jp .PlayerHasRevealedEffectA

.PlayerHasRevealedEffectA
; a = target move effect. Checks only the active player's public used-move list.
	ld [wBossAITemp], a
	push hl
	push bc
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.revealed_effect_loop
	ld a, [hli]
	and a
	jr z, .revealed_effect_next
	push hl
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	ld b, a
	pop hl
	ld a, [wBossAITemp]
	cp b
	jr z, .revealed_effect_yes
.revealed_effect_next
	dec c
	jr nz, .revealed_effect_loop
	pop bc
	pop hl
	and a
	ret
.revealed_effect_yes
	pop bc
	pop hl
	scf
	ret

.ApplyRampMoveBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_ROLLOUT
	jr z, .ramp_move
	cp EFFECT_FURY_CUTTER
	ret nz
.ramp_move
	call .HasKOLine
	ret c
	push hl
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr c, .ramp_resisted
	call .EnemyUnderPressure
	jr c, .ramp_risky
	ld c, 3
	call .EncourageByTierWeight
	ret
.ramp_resisted
	ld a, 6
	call BossAI_DiscourageScoreHL
	ret
.ramp_risky
	ld a, 5
	call BossAI_DiscourageScoreHL
	ret

.ApplyChargeMoveBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SOLARBEAM
	ret nz
	ld a, [wBattleWeather]
	cp WEATHER_SUN
	ret z
	ld a, [wEnemySubStatus3]
	bit SUBSTATUS_CHARGED, a
	ret nz
	ld a, 8
	call BossAI_DiscourageScoreHL
	ret

.ApplyPoisonContactRiskBias
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call .EnemyMoveMakesContact
	ret nc
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	ret z
	call .HasKOLine
	ret c
	call .EnemyCanBePoisonedByRetaliation
	ret nc
	call .PlayerPoisonTypeContribution
	and a
	ret z
	cp 2
	jr z, .full_poison_contact_risk
	ld a, 2
	jp BossAI_DiscourageScoreHL
.full_poison_contact_risk
	ld a, 4
	jp BossAI_DiscourageScoreHL

.ApplyDarkShieldChanceBias
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret nz
	ld a, [wPlayerDarkShieldConsumed]
	and a
	ret nz
	call BossAI_CurrentMoveDarkShieldEligible
	ret z
	ld a, DARK
	call BossAI_PlayerTypeContribution
	cp 1
	ret nz
	ld a, 10
	jp BossAI_DiscourageScoreHL

.ApplyLifeOrbRecoilBias
	call BossAI_GetEnemyHeldEffect
	cp HELD_LIFE_ORB
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call .HasKOLine
	ret c
	call AICheckEnemyQuarterHP_HL
	ret c
	ld a, 6
	jp BossAI_DiscourageScoreHL

.ApplyDestinyBondTradeBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_DESTINY_BOND
	ret nz
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call AICheckEnemyQuarterHP_HL
	ret c
	; Bug: `.HasKOLine` checks the CURRENT scored move's KO pressure. Destiny
	; Bond has MOVE_POWER = 0, so .HasKOLine ALWAYS returns "no KO" and this
	; gate never fires — DB gets encouraged even when the boss has a normal
	; KO move available. Use BossAI_HasAnyKOMove (scans all 4 moveset slots).
	call BossAI_HasAnyKOMove
	ret c
	call BossAI_PlayerHasPublicThreatVsEnemy
	ret nc
	call BossAI_PublicEnemyFaster
	ret nc
	ld c, 1
	call .EncourageByTierWeight
	ld a, 3
	jp BossAI_EncourageScoreHL

.ApplyCounterCoatTradeBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_COUNTER
	jr z, .counter_coat_candidate
	cp EFFECT_MIRROR_COAT
	ret nz
.counter_coat_candidate
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	ret z
	call .HasKOLine
	ret c
	call BossAI_PublicEnemyFaster
	ret c
	call BossAI_PlayerHasPublicThreatVsEnemy
	ret nc
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld b, 0
	cp EFFECT_COUNTER
	jr z, .counter_coat_scan
	inc b
.counter_coat_scan
	push hl
	call .PlayerHasRevealedCounterCoatCategory
	pop hl
	ret nc
	ld c, 1
	call .EncourageByTierWeight
	ld a, 2
	jp BossAI_EncourageScoreHL

.PlayerHasRevealedCounterCoatCategory
; b = 0 for physical Counter bait, b = 1 for special Mirror Coat bait.
	push de
	push bc
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.counter_coat_loop
	ld a, [hli]
	and a
	jr z, .counter_coat_next
	push hl
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .counter_coat_pop_next
	inc hl
	call BossAI_GetMoveByte
	ld d, a
	pop hl
	ld a, b
	and a
	jr z, .counter_wants_physical
	ld a, d
	cp SPECIAL
	jr nc, .counter_coat_yes
	jr .counter_coat_next
.counter_wants_physical
	ld a, d
	cp SPECIAL
	jr c, .counter_coat_yes
	jr .counter_coat_next
.counter_coat_pop_next
	pop hl
.counter_coat_next
	dec c
	jr nz, .counter_coat_loop
	pop bc
	pop de
	and a
	ret
.counter_coat_yes
	pop bc
	pop de
	scf
	ret

.ApplyChoiceFirstLockRegret
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	ld a, [wEnemyChoiceLockedMove]
	and a
	ret nz
	call BossAI_GetEnemyHeldEffect
	call BossAI_IsChoiceHeldEffect
	ret nz
	call .HasKOLine
	ret c
	call .EnemyUnderPressure
	ret c
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 60
	ret c
	call .SeenSpeciesChoiceLockRisk
	and a
	ret z
	cp 2
	jr z, .choice_immune_risk
	ld a, 3
	jp BossAI_DiscourageScoreHL
.choice_immune_risk
	ld a, 6
	jp BossAI_DiscourageScoreHL

.SeenSpeciesChoiceLockRisk
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .no_choice_lock_risk
	ld c, a
	ld hl, wBossAISeenPlayerSpecies
	ld e, 0
	ld a, [wCurSpecies]
	push af
.choice_seen_loop
	ld a, [hli]
	and a
	jr z, .choice_next_seen
	push hl
	push bc
	push de
	ld [wCurSpecies], a
	call GetBaseData
	call .CandidateMoveMatchupVsBaseTypes
	pop de
	pop bc
	pop hl
	and a
	jr z, .choice_seen_immune
	cp EFFECTIVE
	jr nc, .choice_next_seen
	ld a, e
	cp 1
	jr nc, .choice_next_seen
	ld e, 1
.choice_next_seen
	dec c
	jr nz, .choice_seen_loop
	jr .choice_restore_species
.choice_seen_immune
	ld e, 2
.choice_restore_species
	ld a, e
	ld [wBossAITemp], a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ld a, [wBossAITemp]
	ret
.no_choice_lock_risk
	xor a
	ret

DEF BOSS_AI_REM_GROUP_RECOVERY EQU $e0
DEF BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP EQU $e1
DEF BOSS_AI_REM_GROUP_STATUS_DENIAL EQU $e2
DEF BOSS_AI_REM_GROUP_COMMITMENT EQU $e3
DEF BOSS_AI_REM_GROUP_SLEEP_PREEMPT EQU $e4
DEF BOSS_AI_REM_GROUP_DAMAGING EQU $e5
DEF BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE EQU $e6
DEF BOSS_AI_REM_GROUP_SPECIAL_DAMAGE EQU $e7

DEF BOSS_AI_REM_RULE_DISCOURAGE EQU 1
DEF BOSS_AI_REM_RULE_RECOVERY_STATUS_DENIAL EQU 2
DEF BOSS_AI_REM_RULE_RECOVERY_UTILITY_DENIAL EQU 3
DEF BOSS_AI_REM_RULE_FAST_ENCORE_AVOIDANCE EQU 4
DEF BOSS_AI_REM_RULE_LAST_MOVE_ENCORE_TRAP EQU 5
DEF BOSS_AI_REM_RULE_SELFDESTRUCT_PROTECT EQU 6
DEF BOSS_AI_REM_RULE_SLEEP_PREEMPT EQU 7
DEF BOSS_AI_REM_RULE_DESTINY_BOND_AVOIDANCE EQU 8
DEF BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE EQU 9

.ApplyRevealedEffectMatrixBias
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld hl, BossAIRevealedEffectMatrix
.matrix_loop
	ld a, [hli]
	cp -1
	ret z
	ld [wBossAITemp], a
	ld a, [hli]
	ld [wBossAITemp2], a
	ld a, [hli]
	push af ; rule id
	ld a, [hli]
	ld [wBossAITemp3], a
	push hl ; next row
	ld a, [wBossAITemp2]
	call .MatrixCandidateMatchesA
	jr nc, .matrix_next
	ld a, [wBossAITemp]
	call .MatrixRevealedKeyMatchesA
	jr nc, .matrix_next
	pop hl
	pop af
	push hl
	call .MatrixApplyRuleA
	pop hl
	jr .matrix_loop

.matrix_next
	pop hl
	pop af
	jr .matrix_loop

.MatrixCandidateMatchesA
	cp BOSS_AI_REM_GROUP_STATUS_DENIAL
	jr z, .candidate_status_denial
	cp BOSS_AI_REM_GROUP_COMMITMENT
	jr z, .candidate_commitment
	cp BOSS_AI_REM_GROUP_SLEEP_PREEMPT
	jr z, .candidate_sleep_preempt
	cp BOSS_AI_REM_GROUP_DAMAGING
	jr z, .candidate_damaging
	cp BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE
	jr z, .candidate_physical_damage
	cp BOSS_AI_REM_GROUP_SPECIAL_DAMAGE
	jr z, .candidate_special_damage
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp b
	jr z, .matrix_yes
	and a
	ret
.candidate_status_denial
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_TOXIC
	jr z, .matrix_yes
	cp EFFECT_LEECH_SEED
	jr z, .matrix_yes
	and a
	ret
.candidate_commitment
	jp .EncorePunishableCommitmentMove
.candidate_sleep_preempt
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SUBSTITUTE
	jr z, .matrix_yes
	cp EFFECT_SAFEGUARD
	jr z, .matrix_yes
	and a
	ret
.candidate_damaging
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	jr .matrix_yes
.candidate_physical_damage
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	jr c, .matrix_yes
	and a
	ret
.candidate_special_damage
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call BossAI_CurrentEnemyMoveCategory
	cp SPECIAL
	jr nc, .matrix_yes
	and a
	ret
.matrix_yes
	scf
	ret

.MatrixRevealedKeyMatchesA
	cp BOSS_AI_REM_GROUP_RECOVERY
	jp z, .PlayerHasRevealedRecovery
	cp BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP
	jp z, .LastPlayerMoveIsEncoreTrap
	jp .PlayerHasRevealedEffectA

.MatrixApplyRuleA
	cp BOSS_AI_REM_RULE_DISCOURAGE
	jp z, .MatrixDiscourageScore
	cp BOSS_AI_REM_RULE_RECOVERY_STATUS_DENIAL
	jr z, .MatrixRecoveryStatusDenial
	cp BOSS_AI_REM_RULE_RECOVERY_UTILITY_DENIAL
	jr z, .MatrixRecoveryUtilityDenial
	cp BOSS_AI_REM_RULE_FAST_ENCORE_AVOIDANCE
	jr z, .MatrixFastEncoreAvoidance
	cp BOSS_AI_REM_RULE_LAST_MOVE_ENCORE_TRAP
	jr z, .MatrixLastMoveEncoreTrap
	cp BOSS_AI_REM_RULE_SELFDESTRUCT_PROTECT
	jr z, .MatrixSelfdestructProtect
	cp BOSS_AI_REM_RULE_SLEEP_PREEMPT
	jr z, .MatrixSleepPreempt
	cp BOSS_AI_REM_RULE_DESTINY_BOND_AVOIDANCE
	jp z, .MatrixDestinyBondAvoidance
	cp BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE
	jp z, .MatrixCounterCoatAvoidance
	ret

.MatrixRecoveryStatusDenial
	call .MatrixRequireMidTier
	ret c
	call AICheckPlayerMaxHP_HL
	ret c
	call .HasKOLine
	ret c
	call .StatusMoveWouldFailPublicly
	ret c
	jp .MatrixEncourageScore

.MatrixRecoveryUtilityDenial
	call .MatrixRequireMidTier
	ret c
	call AICheckPlayerMaxHP_HL
	ret c
	call .HasKOLine
	ret c
	call .UtilityMoveWouldFailPublicly
	ret c
	jr .MatrixEncourageScore

.MatrixFastEncoreAvoidance
	call .MatrixRequireMidTier
	ret c
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_ENCORED, a
	ret nz
	call BossAI_PublicEnemyFaster
	ret c
	jr .MatrixDiscourageScore

.MatrixLastMoveEncoreTrap
	call .MatrixRequireMidTier
	ret c
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_ENCORED, a
	ret nz
	call .UtilityMoveWouldFailPublicly
	ret c
	call BossAI_PublicEnemyFaster
	ret nc
	jr .MatrixEncourageScore

.MatrixSelfdestructProtect
	call .MatrixRequireMidTier
	ret c
	call .UtilityMoveWouldFailPublicly
	ret c
	call AICheckPlayerHalfHP_HL
	ret c
	push hl
	call BossAI_HasAnyKOMove
	pop hl
	ret c
	jr .MatrixEncourageScore

.MatrixSleepPreempt
	call .MatrixRequireMidTier
	ret c
	ld a, [wEnemyMonStatus]
	and SLP_MASK
	ret nz
	call .UtilityMoveWouldFailPublicly
	ret c
	call BossAI_PublicEnemyFaster
	ret nc
	jr .MatrixEncourageScore

.MatrixDestinyBondAvoidance
	call .MatrixRequireMidTier
	ret c
	; See .ApplyDestinyBondTradeBias: .HasKOLine on a 0-power move (DB) always
	; returns "no KO", so this discouragement branch never fired. Switch to
	; BossAI_HasAnyKOMove so the rule actually triggers when the boss has a
	; conventional KO line available.
	call BossAI_HasAnyKOMove
	ret nc
	call AICheckPlayerQuarterHP_HL
	ret c
	call BossAI_PublicEnemyFaster
	ret c
	jr .MatrixDiscourageScore

.MatrixCounterCoatAvoidance
	call .MatrixRequireMidTier
	ret c
	call .HasKOLine
	ret c
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	ret z
	jr .MatrixDiscourageScore

.MatrixRequireMidTier
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret

.MatrixEncourageScore
	call .MatrixLoadScorePtrHL
	ld a, [wBossAITemp3]
	jp BossAI_EncourageScoreHL

.MatrixDiscourageScore
	call .MatrixLoadScorePtrHL
	ld a, [wBossAITemp3]
	jp BossAI_DiscourageScoreHL

.MatrixLoadScorePtrHL
	ld a, [wBossAIScorePtr]
	ld h, a
	ld a, [wBossAIScorePtr + 1]
	ld l, a
	ret

.PlayerHasRevealedRecovery
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.recovery_loop
	ld a, [hli]
	and a
	ret z
	push hl
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_HEAL
	jr z, .recovery_yes_pop
	cp EFFECT_MORNING_SUN
	jr z, .recovery_yes_pop
	cp EFFECT_SYNTHESIS
	jr z, .recovery_yes_pop
	cp EFFECT_MOONLIGHT
	jr z, .recovery_yes_pop
	pop hl
	dec c
	jr nz, .recovery_loop
	and a
	ret
.recovery_yes_pop
	pop hl
	scf
	ret

.EncorePunishableCommitmentMove
	call BossAI_IsCurrentEnemySetupMove
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .encore_commitment_yes
	cp EFFECT_SUBSTITUTE
	jr z, .encore_commitment_yes
	cp EFFECT_HEAL
	jr z, .encore_commitment_yes
	cp EFFECT_MORNING_SUN
	jr z, .encore_commitment_yes
	cp EFFECT_SYNTHESIS
	jr z, .encore_commitment_yes
	cp EFFECT_MOONLIGHT
	jr z, .encore_commitment_yes
	and a
	ret
.encore_commitment_yes
	scf
	ret

.LastPlayerMoveIsEncoreTrap
	ld a, [wLastPlayerMove]
	and a
	ret z
	cp STRUGGLE
	ret z
	cp ENCORE
	ret z
	cp MIRROR_MOVE
	ret z
	dec a
	push hl
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	pop hl
	cp EFFECT_PROTECT
	jr z, .encore_trap_yes
	cp EFFECT_HEAL
	jr z, .encore_trap_yes
	cp EFFECT_MORNING_SUN
	jr z, .encore_trap_yes
	cp EFFECT_SYNTHESIS
	jr z, .encore_trap_yes
	cp EFFECT_MOONLIGHT
	jr z, .encore_trap_yes
	and a
	ret
.encore_trap_yes
	scf
	ret

.CandidateMoveMatchupVsBaseTypes
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld hl, wBaseType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	ld a, [wTypeMatchup]
	ret

.EnemyMoveMakesContact
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	and a
	jr z, .no_contact
	cp NUM_ATTACKS + 1
	jr nc, .no_contact
	dec a
	ld c, a
	ld b, 0
	ld hl, MoveContactFlags
	add hl, bc
	ld a, BANK(MoveContactFlags)
	call GetFarByte
	and a
	jr z, .no_contact
	scf
	ret
.no_contact
	and a
	ret

.EnemyCanBePoisonedByRetaliation
	ld a, [wEnemyMonStatus]
	and a
	jr nz, .poison_retaliation_safe
	ld a, [wEnemyMonType1]
	cp POISON
	jr z, .poison_retaliation_safe
	cp STEEL
	jr z, .poison_retaliation_safe
	ld a, [wEnemyMonType2]
	cp POISON
	jr z, .poison_retaliation_safe
	cp STEEL
	jr z, .poison_retaliation_safe
	ld a, [wEnemyScreens]
	bit SCREENS_SAFEGUARD, a
	jr nz, .poison_retaliation_safe
	scf
	ret
.poison_retaliation_safe
	and a
	ret

.PlayerPoisonTypeContribution
	ld a, [wBattleMonType1]
	ld b, a
	ld a, [wBattleMonType2]
	cp b
	jr nz, .dual_type_poison_check
	ld a, b
	cp POISON
	jr z, .full_poison_type
	xor a
	ret
.dual_type_poison_check
	ld a, b
	cp POISON
	jr z, .half_poison_type
	ld a, [wBattleMonType2]
	cp POISON
	jr z, .half_poison_type
	xor a
	ret
.half_poison_type
	ld a, 1
	ret
.full_poison_type
	ld a, 2
	ret

.EnemyHasBoostToPass
	ld hl, wEnemyStatLevels
	ld b, NUM_LEVEL_STATS
.boost_loop
	ld a, [hli]
	cp BASE_STAT_LEVEL + 1
	jr nc, .boost_seen
	dec b
	jr nz, .boost_loop
	and a
	ret
.boost_seen
	scf
	ret

.PlayerHasMajorSetupBoost
	ld a, [wPlayerStatLevels + ATTACK]
	cp BASE_STAT_LEVEL + 2
	jr nc, .setup_seen
	ld a, [wPlayerStatLevels + SP_ATTACK]
	cp BASE_STAT_LEVEL + 2
	jr nc, .setup_seen
	ld a, [wPlayerStatLevels + SPEED]
	cp BASE_STAT_LEVEL + 2
	jr nc, .setup_seen
	ld a, [wPlayerStatLevels + EVASION]
	cp BASE_STAT_LEVEL + 2
	jr nc, .setup_seen
	and a
	ret
.setup_seen
	scf
	ret

.PlayerHasRepeatedSwitchPressure
	ld a, [wBossAITurnsElapsed]
	and a
	ret z
	ld c, a
	ld a, [wBossAIPlayerSwitchCount]
	and a
	ret z
	add a
	cp c
	jr c, .no_switch_pressure
	scf
	ret
.no_switch_pressure
	and a
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
	ld a, 24
	call BossAI_DiscourageScoreHL
	ret

.spikes_layer1
; Good lead/pivot punishment baseline.
	call .EnemyUnderPressure
	jr c, .spikes_l1_baseline
	ld a, [wBossAITurnsElapsed]
	cp 2
	jr c, .spikes_l1_high
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 40
	jr nc, .spikes_l1_high
.spikes_l1_baseline
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
	ld a, EFFECT_RAPID_SPIN
	call .PlayerHasRevealedEffectA
	jr nc, .spikes_l2_no_revealed_spin
	call .ApplyRevealedRapidSpinSpikesRisk
	ret c
.spikes_l2_no_revealed_spin
	call .ApplySpikesLayer2UnrevealedSpinRisk
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 55
	jr nc, .spikes_l2_longterm
	ret

.spikes_l2_longterm
	ld c, 2
	call .EncourageByTierWeight
	ret

.spikes_l2_danger
	ld a, 6
	call BossAI_DiscourageScoreHL
	ret

.spikes_layer3
; Prioritize finishing the stack unless immediate danger.
	call .EnemyUnderPressure
	jr c, .spikes_l3_danger
	ld a, EFFECT_RAPID_SPIN
	call .PlayerHasRevealedEffectA
	jr nc, .spikes_l3_no_revealed_spin
	call .ApplyRevealedRapidSpinSpikesRisk
	ret c
.spikes_l3_no_revealed_spin
	call .ApplySpikesLayer3UnrevealedSpinRisk
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
	ld a, 6
	call BossAI_DiscourageScoreHL
	ret

.ApplyRevealedRapidSpinSpikesRisk
; Active Rapid Spin is public. Panic only if it can currently clear Spikes.
	call .EnemyActiveBlocksRapidSpin
	jr nc, .revealed_spin_not_blocked
	ld a, EFFECT_FORESIGHT
	call .PlayerHasRevealedEffectA
	jr c, .revealed_spin_soft
	and a
	ret
.revealed_spin_not_blocked
	call .BossHasAvailableReserveGhost
	jr c, .revealed_spin_soft
	ld a, 10
	call BossAI_DiscourageScoreHL
	scf
	ret
.revealed_spin_soft
	ld a, 8
	call BossAI_DiscourageScoreHL
	and a
	ret

.ApplySpikesLayer2UnrevealedSpinRisk
.spikes_l2_soft_spin_risk
	ret

.ApplySpikesLayer3UnrevealedSpinRisk
	call .BossHasSpinblockAvailable
	ret c
	call .PlayerHasSeenBenchRevealedRapidSpin
	jr c, .spikes_l3_bench_spin_risk
	call .PlayerActiveLikelyCanRapidSpin
	jr c, .spikes_l3_soft_spin_risk
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ret c
.spikes_l3_soft_spin_risk
	ld a, 1
	jp BossAI_DiscourageScoreHL
.spikes_l3_bench_spin_risk
	ld a, 6
	jp BossAI_DiscourageScoreHL

.BossHasSpinblockAvailable
	call .EnemyActiveBlocksRapidSpin
	ret c
	jp .BossHasAvailableReserveGhost

.EnemyActiveBlocksRapidSpin
	call BossAI_EnemyIsGhostType
	ret nc
	ld a, [wEnemySubStatus1]
	bit SUBSTATUS_IDENTIFIED, a
	jr nz, .enemy_not_spinblocking
	scf
	ret
.enemy_not_spinblocking
	and a
	ret

.BossHasAvailableReserveGhost
	ld a, [wOTPartyCount]
	cp 2
	jr c, .reserve_ghost_no
	ld [wBossAITemp2], a
	ld a, [wCurSpecies]
	ld [wBossAITemp4], a
	ld a, [wCurPartySpecies]
	ld [wBossAITemp5], a
	ld de, wOTPartySpecies
	ld hl, wOTPartyMon1HP
	ld c, 0
.reserve_ghost_loop
	ld a, [wCurOTMon]
	cp c
	jr z, .reserve_ghost_next
	push hl
	push de
	push bc
	call .PartyMonAtLeastQuarterHP
	pop bc
	pop de
	pop hl
	jr nc, .reserve_ghost_next
	ld a, [de]
	and a
	jr z, .reserve_ghost_next
	push hl
	push de
	push bc
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	cp GHOST
	jr z, .reserve_ghost_yes_pop
	ld a, [wBaseType2]
	cp GHOST
	jr z, .reserve_ghost_yes_pop
	pop bc
	pop de
	pop hl
.reserve_ghost_next
	inc de
	push bc
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	inc c
	ld a, [wBossAITemp2]
	cp c
	jr nz, .reserve_ghost_loop
	jr .reserve_ghost_restore_no
.reserve_ghost_yes_pop
	pop bc
	pop de
	pop hl
	call .RestoreBossSpeciesBaseData
	scf
	ret
.reserve_ghost_restore_no
	call .RestoreBossSpeciesBaseData
.reserve_ghost_no
	and a
	ret

.RestoreBossSpeciesBaseData
	ld a, [wBossAITemp5]
	ld [wCurPartySpecies], a
	ld a, [wBossAITemp4]
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ret

.PartyMonAtLeastQuarterHP
; hl = party-mon HP. Return carry if current HP is at least one quarter max HP.
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	or b
	jr z, .party_hp_low
	sla c
	rl b
	sla c
	rl b
	ld a, [hli]
	ld d, a
	ld a, [hl]
	ld e, a
	ld a, b
	cp d
	jr c, .party_hp_low
	jr nz, .party_hp_ok
	ld a, c
	cp e
	jr c, .party_hp_low
.party_hp_ok
	scf
	ret
.party_hp_low
	and a
	ret

.PlayerHasSeenBenchRevealedRapidSpin
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .bench_spin_no
	ld c, a
	ld a, [wBossAISeenPlayerAliveMask]
	ld [wBossAITemp5], a
	ld hl, wBossAISeenPlayerSpecies
	ld b, 0
.bench_spin_loop
	ld a, [hli]
	and a
	jr z, .bench_spin_next
	ld e, a
	ld a, [wBossAITemp5]
	bit 0, a
	jr z, .bench_spin_next
	ld a, [wBattleMonSpecies]
	cp e
	jr z, .bench_spin_next
	push hl
	push bc
	ld a, b
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, wBossAISpeciesUsedMoves
	add hl, de
	ld c, NUM_MOVES
.bench_spin_moves
	ld a, [hli]
	and a
	jr z, .bench_spin_move_next
	push hl
	push bc
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_RAPID_SPIN
	pop bc
	pop hl
	jr z, .bench_spin_yes_pop
.bench_spin_move_next
	dec c
	jr nz, .bench_spin_moves
	pop bc
	pop hl
.bench_spin_next
	ld a, [wBossAITemp5]
	srl a
	ld [wBossAITemp5], a
	inc b
	dec c
	jr nz, .bench_spin_loop
.bench_spin_no
	and a
	ret
.bench_spin_yes_pop
	pop bc
	pop hl
	scf
	ret

.PlayerHasSeenAliveBenchGhost
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .bench_ghost_no
	ld c, a
	ld a, [wBossAISeenPlayerAliveMask]
	ld [wBossAITemp5], a
	ld a, [wCurSpecies]
	push af
	ld hl, wBossAISeenPlayerSpecies
.bench_ghost_loop
	ld a, [hli]
	and a
	jr z, .bench_ghost_next
	ld e, a
	ld a, [wBossAITemp5]
	bit 0, a
	jr z, .bench_ghost_next
	ld a, [wBattleMonSpecies]
	cp e
	jr z, .bench_ghost_next
	push hl
	push bc
	ld a, e
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	cp GHOST
	jr z, .bench_ghost_yes_pop
	ld a, [wBaseType2]
	cp GHOST
	jr z, .bench_ghost_yes_pop
	pop bc
	pop hl
.bench_ghost_next
	ld a, [wBossAITemp5]
	srl a
	ld [wBossAITemp5], a
	dec c
	jr nz, .bench_ghost_loop
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
.bench_ghost_no
	and a
	ret
.bench_ghost_yes_pop
	pop bc
	pop hl
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	scf
	ret

.PlayerActiveLikelyCanRapidSpin
	call BossAI_PlayerActiveFourMoveSaturated
	jr c, .active_spin_no
	ld a, [wBattleMonSpecies]
	and a
	jr z, .active_spin_no
	ld [wBossAITemp4], a
	ld a, [wCurSpecies]
	push af
	ld a, [wCurPartySpecies]
	push af
	xor a
	ld [wBossAITemp2], a
	ld a, [wBossAITemp4]
	ld [wCurPartySpecies], a
.active_spin_source_loop
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wCurPartySpecies]
	call .SpeciesLevelUpHasRapidSpin
	jr c, .active_spin_yes
	callfar GetPreEvolution
	jr nc, .active_spin_restore_no
	ld a, 1
	ld [wBossAITemp2], a
	jr .active_spin_source_loop
.active_spin_yes
	pop af
	ld [wCurPartySpecies], a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	scf
	ret
.active_spin_restore_no
	pop af
	ld [wCurPartySpecies], a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
.active_spin_no
	and a
	ret

.SpeciesLevelUpHasRapidSpin
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
.species_spin_skip_evos
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .species_spin_moves
	cp EVOLVE_STAT
	jr z, .species_spin_skip_stat_evo
	inc hl
	inc hl
	inc hl
	jr .species_spin_skip_evos
.species_spin_skip_stat_evo
	inc hl
	inc hl
	inc hl
	inc hl
	jr .species_spin_skip_evos
.species_spin_moves
	inc hl
.species_spin_move_loop
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .species_spin_no
	ld b, a
	ld a, [wBattleMonLevel]
	cp b
	jr c, .species_spin_skip_move
	inc hl
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	cp RAPID_SPIN
	jr z, .species_spin_yes
	inc hl
	jr .species_spin_move_loop
.species_spin_skip_move
	inc hl
	inc hl
	jr .species_spin_move_loop
.species_spin_yes
	scf
	ret
.species_spin_no
	and a
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
	ld a, [wBossAITierWeightRow]
	and a
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
; Saturate at 79 to mirror BossAI_DiscourageScoreHL: scores 80+ mean "blocked"
; in BossAI_SelectMove (cp 80 in the first-pass scan), so an unsaturated
; discourage chain on a high score could either flip a candidate from "scored"
; to "blocked" mid-chain or wrap past 255 and look highly preferred.
	and a
	ret z
	ld e, a
.discourage_loop
	ld a, [hl]
	cp 79
	jr nc, .discourage_done
	inc [hl]
.discourage_done
	dec e
	jr nz, .discourage_loop
	ret

.EnemyUnderPressure
	call AICheckEnemyQuarterHP_HL
	jr nc, .pressure_yes
	call BossAI_PlayerHasRevealedPriorityThreat
	jr c, .pressure_yes
	call BossAI_PlayerHasPublicThreatVsEnemy
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
	call BossAI_CurrentEnemyMoveHasKOPressure
	jr nc, .hasko_no
	scf
	ret
.hasko_no
	and a
	ret

.DenyKOMoveAnswersPublicThreat
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_REFLECT
	jr z, .denyko_reflect
	cp EFFECT_LIGHT_SCREEN
	jr z, .denyko_light_screen
	scf
	ret

.denyko_reflect
	call .PlayerPublicThreatCategory
	ret nc
	and a
	jr z, .denyko_yes
	jr .screen_mismatch

.denyko_light_screen
	call .PlayerPublicThreatCategory
	ret nc
	cp 1
	jr z, .denyko_yes
	jr .screen_mismatch

.denyko_yes
	scf
	ret

.screen_mismatch
	ld a, 4
	call BossAI_DiscourageScoreHL
	and a
	ret

.PlayerPublicThreatCategory
; Return carry with a = 0 for physical or 1 for special when an active
; public STAB type threatens the enemy.
	ld a, [wBattleMonType1]
	call .PublicThreatCategoryForType
	ret c
	ld a, [wBattleMonType2]
	call .PublicThreatCategoryForType
	ret c

.public_threat_category_no
	and a
	ret

.PublicThreatCategoryForType
	ld [wBossAITemp5], a
	ld c, a
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	ret nc
	ld a, [wBossAITemp5]
	cp SPECIAL
	jr c, .public_threat_physical
	ld a, 1
	scf
	ret

.public_threat_physical
	xor a
	scf
	ret

; ============================================================
endc
if DEF(BOSSAI_EMIT_MOVE_GHOST_HELPER)
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

endc

if DEF(BOSSAI_EMIT_MOVE_SELECT)
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
; Gap <  3: 60% best (154/256), with no tier bump so true near-ties mix.
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
	cp 192
	jr nc, .tier_adjust
	ld a, b
	jr .done

.tier_adjust
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

endc

if DEF(BOSSAI_EMIT_MOVE_ACTIVE_THREAT_CACHES)
; ============================================================
; Region: Threat caches (active)
; Concern: Public-threat and revealed-priority cache wrappers
; Layer: POLICY
; Original lines: 165
; ============================================================
; ai-layer: POLICY
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

; ai-layer: POLICY
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
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	jr c, .yes_pop_hl

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
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	jr c, .yes
.unknown_second_type
	ld a, [wBattleMonType2]
	ld c, a
	ld a, [wBattleMonType1]
	cp c
	jr z, .no
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	jr c, .yes
	jr .no

; ai-layer: POLICY
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

; ai-layer: POLICY
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
	ld c, a
	call BossAI_PlayerThreatTypeHitsEnemy
	jr nc, .next
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

endc

if DEF(BOSSAI_EMIT_MOVE_PRESSURE_SCORING)
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
	jr .ko_band_oracle

.resisted
	ld a, b
	and a
	jr z, .done
	dec b

.ko_band_oracle
	farcall BossAI_ApplyKOBandOraclePressure

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
	call BossAI_ConsultKOBandCalibration
	and a
	jr z, .cap
	ld a, b
	add 1
	ld b, a

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
	ld a, [wCurSpecies]
	push af

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
	jr .restore_species_base_data

.clamp_max
	ld a, 255
	jr .restore_species_base_data

.div_zero
	ld a, c
	; fallthrough

.restore_species_base_data
	ld [wBossAITemp], a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ld a, [wBossAITemp]
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
; Coarse AI pressure model for selected Type Passive V1 modifiers.
; Damage ground truth lives in TypePassive_ApplyDamageModifiers_Far
; (engine/battle/type_passive_damage_mods.asm); omissions are policy choices.
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

endc

if DEF(BOSSAI_EMIT_MOVE_ACCURACY_RISK)
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

; ai-layer: POLICY
endc

if DEF(BOSSAI_EMIT_MOVE_PUBLIC_FASTER)
; ============================================================
; Region: Public-faster (speed)
; Concern: Public speed predicate with known Choice Scarf handling
; Layer: POLICY
; Original lines: 63
; ============================================================
; ai-layer: POLICY
BossAI_PublicEnemyFaster:
; Per-tick cache wrapper. The uncached body does two GetBaseData calls
; (heaviest single op in ScoreMove). Inputs (player species, enemy species,
; enemy item) are stable within one AI tick; cached result is reused across
; all moves and lookahead candidates in the same turn.
	ld a, [wBossAIPublicEnemyFasterCache]
	inc a
	jr z, .miss
	dec a
	rrca
	ret
.miss
	call BossAI_PublicEnemyFasterUncached
	push af
	sbc a, a
	and 1
	ld [wBossAIPublicEnemyFasterCache], a
	pop af
	ret

BossAI_PublicEnemyFasterUncached:
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
endc

if DEF(BOSSAI_EMIT_MOVE_PREDICT_AND_REVEALED_SE)
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
	call BossAI_ConsultTendencyCounters
	and a
	jr z, .skip_tendency
	ld b, a
	ld a, [wBossAITemp]
	add b
	ld [wBossAITemp], a
.skip_tendency

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
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	pop hl
	jr nc, .type_loop
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
	call BossAI_PlayerThreatTypeSuperEffectiveVsEnemy
	pop hl
	jr nc, .hp_loop
	scf
	ret

.no
	and a
	ret

endc

if DEF(BOSSAI_EMIT_MOVE_BENCH_THREAT_SCORE)
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

endc

if DEF(BOSSAI_EMIT_MOVE_PLAN_SELECTION)
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
	call BossAI_TryCoachPlanTemplate
	ret c

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
	call BossAI_CurrentPlanIsCoachTemplate
	jr c, .check_coach_valid
	call BossAI_TryCoachPlanTemplate
	ret c
	jr .coach_valid

.check_coach_valid
	call BossAI_CoachPlanStillValid
	jr c, .coach_valid
	call .DropCoachPlanToGeneric
	ret

.coach_valid
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

.DropCoachPlanToGeneric
	ld a, BOSS_PLAN_TEMPO_PRESSURE
	ld [wBossAIPlanId], a
	ld a, 40
	ld [wBossAIPlanConfidence], a
	xor a
	ld [wBossAIPlanPhase], a
	ld a, [wCurOTMon]
	inc a
	ld [wBossAIWinconMonIdx], a
	call BossAI_GetActiveSpeciesSeenIndex
	ld [wBossAITargetMonIdx], a
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

; ai-layer: POLICY
BossAI_TryCoachPlanTemplate:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr nc, .late
	and a
	ret
.late
	call BossAI_FindCoachPlanTemplate
	ret nc
	push hl
	call BossAI_CoachTemplateStopConditionClear
	pop hl
	ret nc
	ld a, [hli]
	ld [wBossAIPlanId], a
	ld de, 4
	add hl, de
	ld b, [hl]
	xor a
	ld [wBossAIPlanPhase], a
	ld a, [wCurOTMon]
	inc a
	ld [wBossAIWinconMonIdx], a
	push bc
	call BossAI_GetActiveSpeciesSeenIndex
	ld [wBossAITargetMonIdx], a
	pop bc
	ld a, b
	ld [wBossAIPlanConfidence], a
	scf
	ret

; ai-layer: POLICY
BossAI_CoachPlanStillValid:
	call BossAI_CurrentPlanIsCoachTemplate
	jr c, .coach
	scf
	ret
.coach
	call BossAI_FindCoachPlanTemplate
	ret nc
	jp BossAI_CoachTemplateStopConditionClear

; ai-layer: POLICY
BossAI_CurrentPlanIsCoachTemplate:
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_TEMPLATE_SETUP_ONCE_THEN_ATTACK
	jr z, .yes
	cp BOSS_PLAN_TEMPLATE_PRESSURE_RECOVER_THEN_LOCK
	jr z, .yes
	and a
	ret
.yes
	scf
	ret

; ai-layer: POLICY
BossAI_FindCoachPlanTemplate:
	ld a, [wTrainerClass]
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a
	ld hl, BossAICoachPlanTemplates
.row_loop
	ld a, [hli]
	and a
	jr z, .not_found
	cp b
	jr nz, .skip_after_class
	ld a, [hli]
	cp c
	jr nz, .skip_after_id
	ld a, [hli]
	ld e, a
	ld a, [wEnemyMonSpecies]
	cp e
	jr nz, .skip_after_species
	scf
	ret

.skip_after_class
	ld de, BOSS_AI_COACH_TEMPLATE_ROW_SIZE - 1
	add hl, de
	jr .row_loop

.skip_after_id
	ld de, BOSS_AI_COACH_TEMPLATE_ROW_SIZE - 2
	add hl, de
	jr .row_loop

.skip_after_species
	ld de, BOSS_AI_COACH_TEMPLATE_ROW_SIZE - 3
	add hl, de
	jr .row_loop

.not_found
	and a
	ret

; ai-layer: POLICY
BossAI_CoachTemplateStopConditionClear:
; hl = row plan-id field. Stop if the player has shown a hard public answer:
; revealed super-effective pressure, the row's explicit stop effect, or a
; resisted damaging lock move after the setup phase.
	push hl
	call BossAI_HasRevealedSuperEffectiveMove
	pop hl
	jr c, .blocked

	push hl
	ld de, 4
	add hl, de
	ld a, [hl]
	pop hl
	and a
	jr z, .check_resist
	push hl
	call BossAI_PlayerHasRevealedEffectA_Coach
	pop hl
	jr c, .blocked

.check_resist
	push hl
	call BossAI_CoachExpectedMoveResistedByPlayer
	pop hl
	jr c, .blocked
	scf
	ret

.blocked
	and a
	ret

; ai-layer: POLICY
BossAI_CoachTemplateExpectedMoveFromHL:
; hl = row plan-id field. Output: carry and a = expected move for this phase.
	ld a, [wBossAIPlanPhase]
	and $7f
	and a
	jr z, .phase0
	cp 1
	jr z, .phase1
	ld de, 3
	jr .load
.phase0
	ld de, 1
	jr .load
.phase1
	ld de, 2
.load
	add hl, de
	ld a, [hl]
	and a
	ret z
	scf
	ret

; ai-layer: POLICY
BossAI_CoachExpectedMoveResistedByPlayer:
	ld a, [wBossAIPlanPhase]
	and $7f
	and a
	jr z, .no
	call BossAI_CoachTemplateExpectedMoveFromHL
	ret nc
	ld b, a
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	jr z, .no
	ld a, b
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	ld c, a
	ldh a, [hBattleTurn]
	push af
	ld a, 1
	ldh [hBattleTurn], a
	ld a, c
	ld hl, wBaseType1
	call BossAI_CheckTypeMatchupNoItem
	pop af
	ldh [hBattleTurn], a
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr c, .yes
.no
	and a
	ret
.yes
	scf
	ret

; ai-layer: POLICY
BossAI_PlayerHasRevealedEffectA_Coach:
	ld [wBossAITemp], a
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.loop
	ld a, [hli]
	and a
	jr z, .next
	push hl
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	ld b, a
	pop hl
	ld a, [wBossAITemp]
	cp b
	jr z, .yes
.next
	dec c
	jr nz, .loop
	and a
	ret
.yes
	scf
	ret

INCLUDE "data/boss_ai/coach_plan_templates.asm"

endc

if DEF(BOSSAI_EMIT_MOVE_PARTY_BY_ROLE)
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

endc

if DEF(BOSSAI_EMIT_MOVE_EFFECT_CLASSIFIERS)
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
; Approved exact-speed exception: if the enemy already outspeeds the active
; player mon, an Agility / Speed boost flips no race. Stop encouraging.
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

endc

if DEF(BOSSAI_EMIT_MOVE_MASK_CONSTRUCTION_OPEN)
; ============================================================
; Region: Plausible / likely type-mask construction
; Concern: Plausible and likely move-type mask construction and tests
; Layer: POLICY
; Original lines: 500
; ============================================================
; ai-layer: POLICY
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
	call BossAI_PlayerActiveFourMoveSaturated
	jr c, .done
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

; ai-layer: POLICY
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

; ai-layer: POLICY
BossAI_PlayerActiveFourMoveSaturated:
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_TRANSFORMED, a
	jr nz, .no
	call BossAI_ActiveSpeciesRevealTainted
	jr c, .no
	ld hl, wPlayerUsedMoves
	ld c, NUM_MOVES
.loop
	ld a, [hli]
	and a
	jr z, .no
	push bc
	push hl
	call BossAI_MoveTaintsFourMoveReveal
	pop hl
	pop bc
	jr c, .no
	dec c
	jr nz, .loop
	scf
	ret
.no
	and a
	ret

; ai-layer: POLICY
endc

if DEF(BOSSAI_EMIT_MOVE_MASK_REVEALED_AND_MOVE_ADDS)
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

; ai-layer: POLICY
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

; ai-layer: POLICY
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

; ai-layer: POLICY
endc

if DEF(BOSSAI_EMIT_MOVE_MASK_SPECIES_SOURCES)
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

; ai-layer: POLICY
BossAI_LoadPublicThreatSourceSpecies:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ret

; ai-layer: POLICY
BossAI_AddCurrentSpeciesSpeculativeMoveThreats:
	call BossAI_AddBaseTMHMMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesEggMovesToMask
	ret

; ai-layer: POLICY
BossAI_AddCurrentSpeciesLikelyMoveThreats:
	ld a, [wBossAITemp2]
	and a
	ret nz
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToLikelyMask
	ret

; ai-layer: POLICY
BossAI_AdvanceToPreEvolutionThreatSource:
	callfar GetPreEvolution
	ret nc
	ld a, 1
	ld [wBossAITemp2], a
	scf
	ret

; ai-layer: POLICY
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

; ai-layer: POLICY
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

; ai-layer: POLICY
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

; ai-layer: POLICY
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

; ai-layer: POLICY
endc

if DEF(BOSSAI_EMIT_MOVE_PLAN_MOVE_BIAS)
; Region: Plan move bias
; Concern: Plan-driven move-score adjustments
; Layer: POLICY
; Original lines: 55
; ============================================================
; ai-layer: POLICY
BossAI_ApplyPlanMoveBias:
	ld a, [wBossAIPlanId]
	and a
	ret z
	call BossAI_ApplyCoachPlanMoveBias
	ret c
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .check_status
	call BossAI_IsCurrentEnemySetupMove
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
	cp BOSS_PLAN_ANTI_SETUP_DENIAL
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	call BossAI_IsDenialEffect
	ret nc
	ld a, 2
	jp BossAI_EncourageScoreHL

; ai-layer: POLICY
BossAI_ApplyCoachPlanMoveBias:
	call BossAI_CurrentPlanIsCoachTemplate
	ret nc
	call BossAI_FindCoachPlanTemplate
	ret nc
	push hl
	call BossAI_CoachTemplateStopConditionClear
	pop hl
	ret nc
	call BossAI_CoachTemplateExpectedMoveFromHL
	ret nc
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	cp b
	jr z, .encourage
	and a
	ret
.encourage
	ld a, BOSS_AI_COACH_TEMPLATE_MOVE_BONUS
	call BossAI_EncourageScoreHL
	scf
	ret

endc

if DEF(BOSSAI_EMIT_MOVE_SCOUT_REPEAT_BIASES)
; ============================================================
; Region: Scout / repeat biases
; Concern: Scout-pivot bias and same-move repeat penalty
; Layer: POLICY
; Original lines: 38
; ============================================================
; ai-layer: POLICY
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

; ai-layer: POLICY
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
	call BossAI_CurrentEnemyMoveHasKOPressure
	pop hl
	ret c
.penalize
	ld a, BOSS_AI_REPEAT_PENALTY
	jp BossAI_DiscourageScoreHL

endc

if DEF(BOSSAI_EMIT_MOVE_LOOKAHEAD_TOP_CANDIDATES)
; ============================================================
; Region: Lookahead orchestration
; Concern: Top-move candidate lookahead and score delta application
; Layer: POLICY
; Original lines: 117
; ============================================================
; ai-layer: POLICY
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
	add BOSS_AI_LOOKAHEAD_BONUS_CAP
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
	push hl
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
	pop hl
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

; ai-layer: POLICY
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

endc

if DEF(BOSSAI_EMIT_MOVE_LOOKAHEAD_BODY)
; ============================================================
; Region: Lookahead body + multi-turn projection
; Concern: Action lookahead body and future-turn projection helpers
; Layer: POLICY
; Original lines: 294
; ============================================================
; ai-layer: POLICY
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
	call AIGetEnemyMove_HL
	ld b, 0 ; upside
	ld c, 0 ; downside

	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .check_setup
	call BossAI_CurrentEnemyMovePressureScore
	ld d, a
	call AICheckPlayerQuarterHP_HL
	jr nc, .low_hp
	call AICheckPlayerHalfHP_HL
	jr nc, .half_hp
	ld a, d
	cp 4
	jr c, .not_ko
	ld b, BOSS_AI_LOOKAHEAD_BONUS_CAP
	jr .check_setup

.low_hp
	ld a, d
	cp 1
	jr c, .not_ko
	ld b, BOSS_AI_LOOKAHEAD_BONUS_CAP
	jr .check_setup

.half_hp
	ld a, d
	cp 3
	jr c, .not_ko
	ld b, BOSS_AI_LOOKAHEAD_BONUS_CAP
	jr .check_setup

.not_ko
	ld a, d
	cp 3
	jr c, .check_quarter
	ld a, b
	add 4
	ld b, a
	jr .check_setup

.check_quarter
	ld a, d
	cp 2
	jr c, .check_setup
	ld a, b
	add 2
	ld b, a

.check_setup
	call BossAI_IsCurrentEnemySetupMove
	jr nc, .check_scout
	ld a, [wBossAIPlanId]
	cp BOSS_PLAN_SETUP_SWEEP
	jr nz, .check_scout
; Stop encouraging more boosts once a KO is already available — extra setup
; just wastes turns and burn/sandstorm chip while the player free-hits.
	push bc
	call BossAI_HasAnyKOMove
	pop bc
	jr c, .check_scout
; Stop encouraging the move when the targeted stat is already at MAX_STAT_LEVEL.
; Without this the AI loops Agility/Swords Dance to +6 and then keeps trying.
	push bc
	call BossAI_SetupBoostHasFurtherValue
	pop bc
	jr nc, .check_scout
; Spamming setup past turn 0 means sitting in damage range while the player
; free-hits. Showdown bot literature converges on "use a boosting move
; *once*". Allow turn-0 setup unconditionally (no info yet, mon is fresh),
; allow turn-1 setup only at full HP (player whiffed / switched / chipped
; trivially), and refuse setup encouragement from turn 2 onward.
	push bc
	call BossAI_SetupTurnIsAffordable
	pop bc
	jr nc, .check_scout
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

; ai-layer: POLICY
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
	push bc
	call BossAI_IsCurrentEnemySetupMove
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
	jr z, .switch_candidate
	push bc
	call BossAI_IsCurrentEnemySetupMove
	pop bc
	jr nc, .check_accuracy

.switch_candidate
	call .IsUnderPressure
	jr c, .check_accuracy

.switch_bonus
	call .GetProjectionDepth
	call .AddUpsideByA

.check_accuracy
	call BossAI_CurrentEnemyMoveAccuracyRisky
	ret nc
	call .GetProjectionDepth
	call .AddDownsideByA
	ret

.GetProjectionDepth
; Per-tick cached projection depth. Inputs (wBossAITier) are stable within
; one AI tick; called 8x per ApplyMultiTurnProjection × up to 4 candidates
; per turn. First call computes and stores; later calls in the same turn
; (across all candidates) hit the cache.
	ld a, [wBossAILookaheadDepthCache]
	inc a
	jr z, .compute_depth
	dec a
	ret
.compute_depth
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, BOSS_AI_LOOKAHEAD_HORIZON_LATE - 1
	jr z, .store_depth
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ld a, BOSS_AI_LOOKAHEAD_HORIZON_MID - 1
	jr z, .store_depth
	xor a
.store_depth
	ld [wBossAILookaheadDepthCache], a
	ret

.IsUnderPressure
	push bc
	call AICheckEnemyQuarterHP_HL
	jr nc, .pressure_yes
	call BossAI_PlayerHasRevealedPriorityThreat
	jr c, .pressure_yes
	call BossAI_PlayerHasPublicThreatVsEnemy
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

endc

if DEF(BOSSAI_EMIT_MOVE_LOOKAHEAD_CLAMP)
; ============================================================
; Region: Signed-delta clamp
; Concern: Signed lookahead delta clamp
; Layer: POLICY
; Original lines: 18
; ============================================================
; ai-layer: POLICY
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

endc

if DEF(BOSSAI_EMIT_MOVE_PRIMARY_THREAT_TYPE)
; ============================================================
; Region: Primary threat type
; Concern: Cached primary threat type resolution
; Layer: POLICY
; Original lines: 154
; ============================================================
; ai-layer: POLICY
BossAI_GetPrimaryThreatType:
; Cache encoding: $ff = uncomputed; $20+ = no threat; 0..$1f = found type id.
; Real type ids cap at DARK ($1b), so $20 is a safe "no threat" sentinel.
	ld a, [wBossAIPrimaryThreatCache]
	cp $ff
	jr z, .miss
	cp $20
	ret nc
	scf
	ret
.miss
	call BossAI_GetPrimaryThreatTypeUncached
	jr c, .miss_yes
	ld a, $20
	ld [wBossAIPrimaryThreatCache], a
	xor a
	ret
.miss_yes
	ld [wBossAIPrimaryThreatCache], a
	scf
	ret

; ai-layer: POLICY
BossAI_GetPrimaryThreatTypeUncached:
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
.likely_loop
	ld a, [hli]
	cp -1
	jr z, .possible
	ld b, a
	push hl
	push de
	ld a, b
	call BossAI_TestLikelyMaskBit
	pop de
	pop hl
	jr nc, .likely_loop
	push bc
	push de
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop de
	pop bc
	cp d
	jr c, .likely_loop
	ld d, a
	ld a, b
	ld e, a
	jr .likely_loop

.possible
	ld hl, BossAI_PlausibleThreatTypes
.possible_loop
	ld a, [hli]
	cp -1
	jr z, .hp_fallback
	ld b, a
	push hl
	push de
	ld a, b
	call BossAI_TestPlausibleMaskBit
	pop de
	pop hl
	jr nc, .possible_loop
	push hl
	push de
	ld a, b
	call BossAI_TestLikelyMaskBit
	pop de
	pop hl
	jr c, .possible_loop
	push bc
	push de
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop de
	pop bc
	cp 3
	jr c, .possible_loop
	cp d
	jr c, .possible_loop
	ld d, a
	ld a, b
	ld e, a
	jr .possible_loop

.hp_fallback
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	push de
	call BossAI_TestLikelyMaskBit
	pop de
	jr c, .scan_hidden_power
	ld a, d
	and a
	jr nz, .done
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	push de
	call BossAI_TestPlausibleMaskBit
	pop de
	jr nc, .none
.scan_hidden_power
	ld hl, BossAIHiddenPowerThreatTypes
.hp_loop
	ld a, [hli]
	cp -1
	jr z, .done
	ld b, a
	push hl
	push bc
	push de
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop de
	pop bc
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

endc

if DEF(BOSSAI_EMIT_MOVE_THREAT_SEVERITY)
; ============================================================
; Region: Threat severity + item nullifies
; Concern: Threat severity scoring and known defensive item nullification
; Layer: POLICY
; Original lines: 136
; ============================================================
; ai-layer: POLICY
BossAI_GetRevealedMoveThreatTypeAndSeverity:
	and a
	ret z
	ld c, a
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_SetPlausibleAndLikelyMaskBit
	and a
	ret

.check_power
	ld a, c
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	ret z
	ld a, c
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	ld b, a
	push bc
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	pop bc
	and a
	ret z
	scf
	ret

; ai-layer: POLICY
BossAI_GetTypeThreatSeverityVsEnemyMon:
	push hl
	ld c, a
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	pop hl
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 4
	ld a, 6
	jr nc, .adjust
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 2
	ld a, 3
	jr nc, .adjust
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	ld a, 1
	jr nc, .adjust
	xor a
	ret

.adjust
	ld b, a
	push hl
	call BossAI_AdjustThreatSeverityForEnemyKnownDefense
	pop hl
	ret

; ai-layer: POLICY
BossAI_AdjustThreatSeverityForEnemyKnownDefense:
; input: c = public threat type, b = severity. output: a = adjusted severity.
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr nc, .dragon
	xor a
	ret

.dragon
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr nc, .assault_vest
	ld a, DRAGON
	call BossAI_EnemyTypeContribution
	and a
	jr z, .assault_vest
	call BossAI_DecThreatSeverityB

.assault_vest
	call BossAI_GetEnemyHeldEffect
	ld e, a
	cp HELD_ASSAULT_VEST
	jr nz, .eviolite
	ld a, c
	cp SPECIAL
	jr c, .eviolite
	call BossAI_DecThreatSeverityB

.eviolite
	ld a, e
	cp HELD_EVOLITE
	jr nz, .done
	call BossAI_EnemySpeciesCanEvolve
	jr nc, .done
	call BossAI_DecThreatSeverityB

.done
	ld a, b
	ret

; ai-layer: POLICY
BossAI_PlayerThreatTypeSuperEffectiveVsEnemy:
; input: c = public threat type. output: carry if super-effective and not nullified.
	call BossAI_PlayerThreatTypeHitsEnemy
	jr nc, .no
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .no
	scf
	ret

.no
	and a
	ret

; ai-layer: POLICY
BossAI_PlayerThreatTypeHitsEnemy:
; input: c = public threat type. output: carry if it can hit and is not nullified.
	ld a, c
	call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .no
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr c, .no
	scf
	ret

.no
	and a
	ret

; ai-layer: POLICY
BossAI_EnemyKnownItemNullifiesThreatType:
	cp GROUND
	jr nz, .no
	call BossAI_GetEnemyHeldEffect
	cp HELD_AIR_BALLOON
	jr nz, .no
	scf
	ret

.no
	and a
	ret

; ai-layer: POLICY
BossAI_DecThreatSeverityB:
	ld a, b
	and a
	ret z
	dec b
	ret

; ai-layer: POLICY
BossAI_EnemySpeciesCanEvolve:
	ld a, [wEnemyMonSpecies]
	and a
	ret z
	push hl
	push bc
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .no
	pop bc
	pop hl
	scf
	ret

.no
	pop bc
	pop hl
	and a
	ret

endc

if DEF(BOSSAI_EMIT_MOVE_TIER_ROLL_THRESHOLDS)
; ============================================================
; Region: Tier-roll thresholds
; Concern: Tier-weighted plausible, speculative, and scout thresholds
; Layer: POLICY
; Original lines: 31
; ============================================================
; ai-layer: POLICY
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

; ai-layer: POLICY
BossAI_GetSpeculativePlausibleRiskWeight:
	call BossAI_GetTierPlausibleRiskWeight
	srl a
	ret nz
	inc a
	ret

; ai-layer: POLICY
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

endc

if DEF(BOSSAI_EMIT_MOVE_SCOUT_DECISION)
BossAI_ShouldScout:
; Per-tick cache for the prereq chain only. The five prereq helpers
; (IsActiveSpeciesScouted / GetPrimaryThreatType /
; GetTypeThreatSeverityVsEnemyMon / HasAnyKOMove / GetScoutRollThreshold)
; have turn-stable outputs. The Random roll varies per call and stays
; inside this function so RNG consumption is preserved. We also capture
; wTypeMatchup at end of prereqs and restore it on every cache hit so any
; downstream reader sees the same byte the original chain would have left.
	ld a, [wBossAIShouldScoutPrereqCache]
	inc a
	jr z, .compute_prereqs
	dec a
	jr z, .no
	; cached "prereqs passed" -- restore the side-effect wTypeMatchup write
	; the original prereq chain would have left, then roll random.
	ld a, [wBossAIShouldScoutMatchupValue]
	ld [wTypeMatchup], a
	ld a, [wBossAIShouldScoutThresholdCache]
	ld b, a
	call Random
	cp b
	jr nc, .no
	jr .yes

.compute_prereqs
	call BossAI_IsActiveSpeciesScouted
	jr c, .prereqs_failed
	call BossAI_GetPrimaryThreatType
	jr nc, .prereqs_failed
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	cp 3
	jr c, .prereqs_failed
	call BossAI_HasAnyKOMove
	jr c, .prereqs_failed
	call BossAI_GetScoutRollThreshold
	ld [wBossAIShouldScoutThresholdCache], a
	; capture wTypeMatchup as the original chain left it, so cached calls
	; can restore it. Random and GetScoutRollThreshold don't touch
	; wTypeMatchup; capturing here matches the byte the unwrapped function
	; would have left at end of prereqs.
	ld a, [wTypeMatchup]
	ld [wBossAIShouldScoutMatchupValue], a
	ld a, 1
	ld [wBossAIShouldScoutPrereqCache], a
	ld a, [wBossAIShouldScoutThresholdCache]
	ld b, a
	call Random
	cp b
	jr nc, .no

.yes
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAITraceRiskFlags]
	or 1
	ld [wBossAITraceRiskFlags], a
ENDC
	scf
	ret

.prereqs_failed
	xor a
	ld [wBossAIShouldScoutPrereqCache], a
.no
	and a
	ret

endc

if DEF(BOSSAI_EMIT_MOVE_MARK_SCOUTED_IF_SCOUT_MOVE)
BossAI_MarkScoutedIfScoutMove:
	ld a, [wCurEnemyMove]
	and a
	ret z
	call AIGetEnemyMove_HL
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

endc

if DEF(BOSSAI_EMIT_MOVE_MARK_SCOUT_PIVOT)
; ============================================================
; Region: Mark scout pivot
; Concern: Scout-pivot marking after switch execution
; Layer: POLICY
; Original lines: 10
; ============================================================
; ai-layer: POLICY
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

endc

if DEF(BOSSAI_EMIT_MOVE_BIAS_SUPPORT_TABLES)
BossAITierWeights:
; ko, denyko, tempo, setup, status, role, risk
; rows 0..2 mirror AI_TIER_EARLY/MID/LATE; rows 3..4 are sub-tier bumps used by
; BossAITierRampMap to ramp specific early-tier trainers toward MID without
; flipping the tier value (which would also enable MID-only feature gates).
	db 4, 2, 1, 1, 1, 1, 2 ; row 0: early
	db 5, 3, 2, 2, 1, 1, 2 ; row 1: mid
	db 7, 4, 4, 2, 2, 3, 1 ; row 2: late
	db 5, 2, 1, 1, 1, 1, 2 ; row 3: early +25% (one delta column raised toward mid)
	db 5, 3, 1, 1, 1, 1, 2 ; row 4: early +50% (two delta columns raised toward mid)

; ai-layer: POLICY
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

; ai-layer: POLICY
BossAIStatusEffects:
	db EFFECT_SLEEP
	db EFFECT_PARALYZE
	db EFFECT_CONFUSE
	db EFFECT_POISON
	db EFFECT_TOXIC
	db EFFECT_LEECH_SEED
	db -1

; ai-layer: POLICY
BossAIRiskyEffects:
	db EFFECT_SELFDESTRUCT
	db EFFECT_RECOIL_HIT
	db EFFECT_HYPER_BEAM
	db EFFECT_BELLY_DRUM
	db -1

INCLUDE "data/boss_ai/revealed_effect_matrix.asm"

; ============================================================
endc
