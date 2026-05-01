BossAI_IncrementTurnsElapsed:
	ld a, [wBossAITier]
	and a
	ret z
	ld hl, wBossAITurnsElapsed
	inc [hl]
	ld hl, wBossAIPlanPhase
	res 7, [hl]
	inc [hl]
	ld a, [wBossAIPendingPlayerSwitchCount]
	and a
	jr z, .no_pending_switch
	ld b, a
	xor a
	ld [wBossAIPendingPlayerSwitchCount], a
	ld a, [wBossAIPlayerSwitchCount]
	add b
	jr nc, .store_switch_count
	ld a, $ff
.store_switch_count
	ld [wBossAIPlayerSwitchCount], a
.no_pending_switch
	call BossAI_DecaySwitchCooldown
	ret

BossAI_RecordPlayerSwitch:
	ld a, [wBossAITier]
	and a
	ret z
	ld hl, wBossAIPendingPlayerSwitchCount
	ld a, [hl]
	cp $ff
	ret z
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
	ld e, 0
	ld a, c
	and a
	jr z, .append

.check_seen
	ld a, [hli]
	cp b
	jr z, .mark_alive
	inc e
	dec c
	jr nz, .check_seen
	jr .append

.mark_alive
	ld c, e
	call BossAI_SetSeenPlayerAliveBit
	ret

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
	call BossAI_SetSeenPlayerAliveBit
	ld hl, wBossAISeenPlayerSpeciesCount
	inc [hl]
	ret

BossAI_RecordPlayerFaint:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wBattleMonSpecies]
	and a
	ret z
	ld b, a

	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	ret z
	ld c, a
	ld e, 0
	ld hl, wBossAISeenPlayerSpecies
.loop
	ld a, [hli]
	cp b
	jr z, .clear_alive
	inc e
	dec c
	jr nz, .loop
	ret

.clear_alive
	ld c, e
	call BossAI_ClearSeenPlayerAliveBit
	ret

BossAI_SetSeenPlayerAliveBit:
	push bc
	call BossAI_SeenPlayerSpeciesBitFromC
	ld hl, wBossAISeenPlayerAliveMask
	or [hl]
	ld [hl], a
	pop bc
	ret

BossAI_ClearSeenPlayerAliveBit:
	push bc
	call BossAI_SeenPlayerSpeciesBitFromC
	cpl
	ld hl, wBossAISeenPlayerAliveMask
	and [hl]
	ld [hl], a
	pop bc
	ret

BossAI_SeenPlayerSpeciesBitFromC:
	ld a, c
	and a
	ld a, 1
	ret z
	ld b, c
.loop
	add a
	dec b
	jr nz, .loop
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

BossAI_RecordRevealedPlayerMove:
	ld a, [wBossAITier]
	and a
	ret z

	ld a, [wPlayerMoveStruct + MOVE_ANIM]
	and a
	ret z
	ld b, a

	push bc
	call BossAI_GetActiveSpeciesRevealedMaskPointer
	pop bc
	ret nc
	ld a, b
	call BossAI_AddRevealedMoveToSpeciesMask
	call BossAI_MirrorPlayerUsedMovesToSpeciesSlot
	xor a
	ld [wBossAIPlausibleTypeMaskSpecies], a
	ld [wBossAIPlausibleTypeMaskLevel], a
	ret

BossAI_GetActiveSpeciesRevealedMaskPointer:
	call BossAI_GetActiveSpeciesSeenIndex
	and a
	jr z, .no_species
	dec a
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, wBossAIRevealedMovesBitmap
	add hl, de
	scf
	ret

.no_species
	and a
	ret

BossAI_LoadPlayerUsedMovesForActiveSpecies:
; Replace NewBattleMonStatus's blanket clear of wPlayerUsedMoves: keep boss AI
; memory of moves the entering active mon has used earlier this fight, so
; switching out and back in does not erase that memory. Falls back to the
; original zero behavior for non-boss fights and first-time encounters.
	xor a
	ld hl, wPlayerUsedMoves
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_GetActiveSpeciesUsedMovesPointer
	ret nc
	ld de, wPlayerUsedMoves
	ld c, NUM_MOVES
.copy_loop
	ld a, [hli]
	ld [de], a
	inc de
	dec c
	jr nz, .copy_loop
	ret

BossAI_MirrorPlayerUsedMovesToSpeciesSlot:
	push bc
	call BossAI_GetActiveSpeciesUsedMovesPointer
	pop bc
	ret nc
	ld de, wPlayerUsedMoves
	ld c, NUM_MOVES
.copy_loop
	ld a, [de]
	ld [hli], a
	inc de
	dec c
	jr nz, .copy_loop
	ret

BossAI_GetActiveSpeciesUsedMovesPointer:
; Scan-only (no auto-append) lookup for the active mon's slot in
; wBossAISpeciesUsedMoves. CF set with hl pointing at the slot; CF clear with
; hl unchanged when the species is not (yet) in the seen list.
	ld a, [wBattleMonSpecies]
	and a
	jr z, .no_species
	ld b, a
	ld a, [wBossAISeenPlayerSpeciesCount]
	and a
	jr z, .no_species
	ld c, a
	ld hl, wBossAISeenPlayerSpecies
	ld e, 0
.find_loop
	ld a, [hli]
	cp b
	jr z, .found
	inc e
	dec c
	jr nz, .find_loop
.no_species
	and a
	ret
.found
	ld a, e
	add a
	add a
	ld c, a
	ld b, 0
	ld hl, wBossAISpeciesUsedMoves
	add hl, bc
	scf
	ret

BossAI_GetMoveAttr:
	push bc
	ld bc, MOVE_LENGTH
	call AddNTimes
	call BossAI_GetMoveByte
	pop bc
	ret

BossAI_GetMoveByte:
	ld a, BANK(Moves)
	jp GetFarByte

BossAI_AddRevealedMoveToSpeciesMask:
	and a
	ret z
	ld [wBossAITemp], a
	ld a, l
	ld [wBossAITemp2], a
	ld a, h
	ld [wBossAITemp3], a

	ld a, [wBossAITemp]
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_HIDDEN_POWER
	jr nz, .check_power
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	jr BossAI_SetRevealedSpeciesMaskBit

.check_power
	ld a, [wBossAITemp]
	dec a
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr
	and a
	ret z
	ld a, [wBossAITemp]
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr

BossAI_SetRevealedSpeciesMaskBit:
	ld c, a
	and %11111000
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld a, [wBossAITemp2]
	ld l, a
	ld a, [wBossAITemp3]
	ld h, a
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
	ld a, [hl]
	cp 80
	jr nc, .next
	push bc
	push de
	push hl
	call .ScoreMove
	pop hl
	pop de
	pop bc
.next
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
	call .HeldItemMoveBlocked
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
	call .UtilityMoveWouldFailPublicly
	jr nc, .skip_utility_fail
	ld a, 24
	call BossAI_DiscourageScoreHL

.skip_utility_fail
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	jr nc, .skip_status
	call .StatusMoveWouldFailPublicly
	jr nc, .status_ok
	ld a, 24
	call BossAI_DiscourageScoreHL
	jr .skip_status
.status_ok
	ld c, 4
	call .EncourageByTierWeight

.skip_status
	call .ApplySetupPunishBias
	call .ApplySpikesLayerBias
	call .ApplyPhazingPlanBias
	call .ApplyRapidSpinBias
	call .ApplyBatonPassBias
	call .ApplyRevealedAntiSetupAvoidance
	call .ApplyRampMoveBias
	call .ApplyLegacyRoleBiasIfNeeded
	call BossAI_ApplyPlanMoveBias
	call .ApplyChargeMoveBias
	call .ApplyPoisonContactRiskBias
	call .ApplyDarkShieldChanceBias
	call .ApplyLifeOrbRecoilBias
	call .ApplyShellBellSustainBias
	call .ApplyGrassRegrowthBias
	call .ApplyDestinyBondTradeBias
	call .ApplyRevealedDestinyBondAvoidance
	call .ApplyCounterCoatTradeBias
	call .ApplyRevealedCounterCoatAvoidance
	call .ApplyMercyRefusalBias
	call .ApplyChoiceFirstLockRegret
	call .ApplyRevealedProtectCommitmentRisk
	call .ApplyRevealedRecoveryDenialBias
	call .ApplyRevealedFastEncoreAvoidance
	call .ApplyLastMoveEncoreTrapBias
	call .ApplyRevealedSelfdestructProtectBias
	call .ApplyRevealedSleepPreemptBias
	call BossAI_ApplyScoutMoveBias
	call BossAI_ApplyRepeatPenalty

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
	jp z, .check_primary_status
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
	cp EFFECT_SUBSTITUTE
	jr z, .check_substitute
	cp EFFECT_PROTECT
	jr z, .check_protect
	cp EFFECT_DISABLE
	jr z, .check_disable
	cp EFFECT_ENCORE
	jr z, .check_encore
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

.check_substitute
	ld a, [wEnemySubStatus4]
	bit SUBSTATUS_SUBSTITUTE, a
	jp nz, .status_fail
	call AICheckEnemyQuarterHP
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
	call AICheckEnemyMaxHP
	jp c, .status_fail
	and a
	ret

.check_primary_status
	call .PrimaryStatusBlocked
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
	call .EnemyUnderPressure
	jr c, .ramp_risky
	ld c, 3
	call .EncourageByTierWeight
	ret
.ramp_risky
	call .HasKOLine
	ret c
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
	call AICheckEnemyQuarterHP
	ret c
	ld a, 6
	jp BossAI_DiscourageScoreHL

.ApplyShellBellSustainBias
	call BossAI_GetEnemyHeldEffect
	cp HELD_SHELL_BELL
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	ret z
	call AICheckEnemyMaxHP
	ret c
	ld a, 2
	jp BossAI_EncourageScoreHL

.ApplyGrassRegrowthBias
	ld a, GRASS
	call BossAI_EnemyTypeContribution
	and a
	ret z
	ld a, [wEnemyMonStatus]
	and a
	ret nz
	call AICheckEnemyMaxHP
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	jr z, .regrowth_good
	cp EFFECT_SUBSTITUTE
	jr z, .regrowth_good
	cp EFFECT_HEAL
	jr z, .regrowth_good
	cp EFFECT_MORNING_SUN
	jr z, .regrowth_good
	cp EFFECT_SYNTHESIS
	jr z, .regrowth_good
	cp EFFECT_MOONLIGHT
	ret nz
.regrowth_good
	ld a, 2
	jp BossAI_EncourageScoreHL

.ApplyDestinyBondTradeBias
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_DESTINY_BOND
	ret nz
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call AICheckEnemyQuarterHP
	ret c
	call .HasKOLine
	ret c
	call BossAI_PlayerHasPublicThreatVsEnemy
	ret nc
	call BossAI_PublicEnemyFaster
	ret nc
	ld c, 1
	call .EncourageByTierWeight
	ld a, 3
	jp BossAI_EncourageScoreHL

.ApplyRevealedDestinyBondAvoidance
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call .HasKOLine
	ret nc
	call AICheckPlayerQuarterHP
	ret c
	ld a, EFFECT_DESTINY_BOND
	call .PlayerHasRevealedEffectA
	ret nc
	call BossAI_PublicEnemyFaster
	ret c
	ld a, 7
	jp BossAI_DiscourageScoreHL

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

.ApplyRevealedCounterCoatAvoidance
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret z
	call .HasKOLine
	ret c
	call BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem
	ld a, [wTypeMatchup]
	and a
	ret z
	call BossAI_CurrentEnemyMoveCategory
	ld b, 0
	cp SPECIAL
	jr c, .counter_coat_avoid_scan
	inc b
.counter_coat_avoid_scan
	call .PlayerHasRevealedCounterCoatTrap
	ret nc
	ld a, 5
	jp BossAI_DiscourageScoreHL

.PlayerHasRevealedCounterCoatTrap
; b = 0 checks revealed Counter; b = 1 checks revealed Mirror Coat.
	ld a, b
	and a
	ld a, EFFECT_COUNTER
	jr z, .counter_coat_trap_scan
	ld a, EFFECT_MIRROR_COAT
.counter_coat_trap_scan
	jp .PlayerHasRevealedEffectA

.ApplyMercyRefusalBias
; Prediction-driven non-damaging pick when a KO is available against a low-HP
; player. Fires only when BossAI_PredictPlayerSwitch is high enough that a
; setup/Spikes/status play actually beats the KO; the encourage magnitude is
; capped so the KO still wins roughly 9 times out of 10 even when this fires.
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ret c
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	ret nz
	call .MercyRefusalCandidate
	ret nc
	call AICheckPlayerQuarterHP
	ret c
	call .EnemyUnderPressure
	ret c
	push hl
	call BossAI_HasAnyKOMove
	pop hl
	ret nc
	push hl
	call BossAI_PredictPlayerSwitch
	pop hl
	cp 60
	ret c
	ld a, 2
	jp BossAI_EncourageScoreHL

.MercyRefusalCandidate
	call .UtilityMoveWouldFailPublicly
	jr c, .mercy_no
	call .IsSetupMove
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SPIKES
	jr z, .mercy_spikes
	ld hl, BossAIStatusEffects
	ld de, 1
	call IsInArray
	jr nc, .mercy_no
	call .StatusMoveWouldFailPublicly
	jr c, .mercy_no
	scf
	ret
.mercy_spikes
	ld a, [wPlayerScreens]
	and SCREENS_SPIKES_MASK
	cp 3
	jr nc, .mercy_no
	scf
	ret
.mercy_no
	and a
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
	cp 40
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

.ApplyRevealedProtectCommitmentRisk
	call .PlayerHasRevealedProtect
	ret nc
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SELFDESTRUCT
	jr z, .protect_hard_punish
	cp EFFECT_HYPER_BEAM
	ret nz
	ld a, 4
	jp BossAI_DiscourageScoreHL
.protect_hard_punish
	ld a, 10
	jp BossAI_DiscourageScoreHL

.PlayerHasRevealedProtect
	ld a, EFFECT_PROTECT
	jp .PlayerHasRevealedEffectA

.ApplyRevealedRecoveryDenialBias
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call .PlayerHasRevealedRecovery
	ret nc
	call AICheckPlayerMaxHP
	ret c
	call .HasKOLine
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_TOXIC
	jr z, .recovery_status
	cp EFFECT_LEECH_SEED
	jr z, .recovery_status
	cp EFFECT_FORCE_SWITCH
	ret nz
	call .UtilityMoveWouldFailPublicly
	ret c
	ld a, 3
	jp BossAI_EncourageScoreHL

.recovery_status
	call .StatusMoveWouldFailPublicly
	ret c
	ld a, 4
	jp BossAI_EncourageScoreHL

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

.ApplyRevealedFastEncoreAvoidance
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_ENCORED, a
	ret nz
	call .EncorePunishableCommitmentMove
	ret nc
	ld a, EFFECT_ENCORE
	call .PlayerHasRevealedEffectA
	ret nc
	call BossAI_PublicEnemyFaster
	ret c
	ld a, 5
	jp BossAI_DiscourageScoreHL

.EncorePunishableCommitmentMove
	call .IsSetupMove
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

.ApplyLastMoveEncoreTrapBias
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_ENCORE
	ret nz
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_ENCORED, a
	ret nz
	call .UtilityMoveWouldFailPublicly
	ret c
	call BossAI_PublicEnemyFaster
	ret nc
	call .LastPlayerMoveIsEncoreTrap
	ret nc
	ld a, 6
	jp BossAI_EncourageScoreHL

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

.ApplyRevealedSelfdestructProtectBias
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_PROTECT
	ret nz
	call .UtilityMoveWouldFailPublicly
	ret c
	call AICheckPlayerHalfHP
	ret c
	push hl
	call BossAI_HasAnyKOMove
	pop hl
	ret c
	call .PlayerHasRevealedSelfdestruct
	ret nc
	ld a, 5
	jp BossAI_EncourageScoreHL

.PlayerHasRevealedSelfdestruct
	ld a, EFFECT_SELFDESTRUCT
	jp .PlayerHasRevealedEffectA

.ApplyRevealedSleepPreemptBias
; Encourage Substitute / Safeguard when the player has revealed a sleep move
; AND the boss is publicly faster — both Sub and Safeguard need to resolve
; before the sleep move to actually preempt it. From a slower boss they fizzle
; (the sleep lands first, so the boss is asleep before the utility move runs).
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wEnemyMonStatus]
	and SLP_MASK
	ret nz
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	cp EFFECT_SUBSTITUTE
	jr z, .candidate
	cp EFFECT_SAFEGUARD
	ret nz
.candidate
	call .UtilityMoveWouldFailPublicly
	ret c
	ld a, EFFECT_SLEEP
	call .PlayerHasRevealedEffectA
	ret nc
	call BossAI_PublicEnemyFaster
	ret nc
	ld a, 5
	jp BossAI_EncourageScoreHL

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
	ld c, 5
	call .DiscourageByTierWeight
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

.IsSetupMove
	jp BossAI_IsCurrentEnemySetupMove

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

BossAI_SwitchOrTryItem:
	ld a, [wBossAITier]
	and a
	ret z
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

BossAI_CheckAbleToSwitchSafe:
	xor a
	ld [wEnemySwitchMonParam], a
	call BossAI_FindFirstAliveSwitchCandidate
	ret nc
	call BossAI_PlayerHasPublicThreatVsEnemy
	jr c, .high_confidence
	call AICheckEnemyQuarterHP
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

BossAI_PlayerHasPublicThreatVsEnemy:
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

BossAI_PlayerHasRevealedPriorityThreat:
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
	call AICheckEnemyQuarterHP
	jr nc, .yes_pop
	call AICheckEnemyHalfHP
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

BossAI_CurrentEnemyMoveHasKOPressure:
	call BossAI_CurrentEnemyMovePressureScore
	ld d, a
	and a
	jr z, .no
	call AICheckPlayerQuarterHP
	jr nc, .low_hp
	call AICheckPlayerHalfHP
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
	call AICheckEnemyQuarterHP
	jr nc, .reversal_high
	call AICheckEnemyHalfHP
	jr nc, .reversal_mid
	jr .raw_power

.reversal_high
	ld a, 100
	ret

.reversal_mid
	ld a, 70
	ret

.raw_power
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	ret

BossAI_ApplyEnemyKnownPressureModifiers:
	call BossAI_ApplyEnemyHeldItemPressure
	call BossAI_ApplyEnemyOffensivePassivePressure
	call BossAI_ApplyPlayerDefensivePassivePressure
	ret

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
	call AICheckPlayerHalfHP
	pop bc
	ret nc
	ld a, ICE
	call BossAI_PlayerTypeContribution
	and a
	ret z
	call BossAI_DecPressureB
	ret

BossAI_DecPressureB:
	ld a, b
	and a
	ret z
	dec b
	ret

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

BossAI_PlayerTypeContribution:
	ld hl, wBattleMonType1
	jr BossAI_TypeContributionAtHL

BossAI_EnemyTypeContribution:
	ld hl, wEnemyMonType1

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
	call AICheckEnemyQuarterHP
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

BossAI_IsImminentKOPrevention:
	call AICheckEnemyQuarterHP
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

	call AICheckEnemyHalfHP
	jr nc, .yes
	call BossAI_HasRevealedSuperEffectiveMove
	jr c, .yes
	call BossAI_IsSuspiciousSwitchIn
	jr nc, .no
	call AICheckEnemyQuarterHP
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
	call AICheckEnemyHalfHP
	jr nc, .seen_yes
.seen_no
	and a
	ret
.seen_yes
	scf
	ret

BossAI_IsScarfSwingPossible:
; Do not infer unrevealed player Choice Scarf from private speed values.
	and a
	ret

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

BossAI_HasAnyKOMove:
	call BossAI_SaveEnemyMoveStruct
	call BossAI_EnemyChoiceLockedMove
	jr nc, .scan_all_moves
	call AIGetEnemyMove
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
	call AIGetEnemyMove
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

BossAI_GetEnemyHeldEffect:
	push bc
	ld a, [wEnemyMonItem]
	ld b, a
	callfar GetItemHeldEffect
	ld a, b
	pop bc
	ret

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

BossAI_IsChoiceHeldEffect:
	cp HELD_CHOICE_BAND
	ret z
	cp HELD_CHOICE_SPECS
	ret z
	cp HELD_CHOICE_SCARF
	ret

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

BossAI_SetPlausibleAndLikelyMaskBit:
	push af
	call BossAI_SetPlausibleMaskBit
	pop af
	call BossAI_SetLikelyMaskBit
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

BossAI_LoadPublicThreatSourceSpecies:
	ld a, [wCurPartySpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ret

BossAI_AddCurrentSpeciesSpeculativeMoveThreats:
	call BossAI_AddBaseTMHMMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToMask
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesEggMovesToMask
	ret

BossAI_AddCurrentSpeciesLikelyMoveThreats:
	ld a, [wBossAITemp2]
	and a
	ret nz
	ld a, [wCurPartySpecies]
	call BossAI_AddSpeciesLevelUpMovesToLikelyMask
	ret

BossAI_AdvanceToPreEvolutionThreatSource:
	callfar GetPreEvolution
	ret nc
	ld a, 1
	ld [wBossAITemp2], a
	scf
	ret

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

BossAI_ApplyPlanMoveBias:
	ld a, [wBossAIPlanId]
	and a
	ret z
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
	call BossAI_CurrentEnemyMoveHasKOPressure
	pop hl
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

BossAI_SetScoreHL:
	call BossAI_LoadScorePointer
	ld [hl], a
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
	call BossAI_CurrentEnemyMovePressureScore
	ld d, a
	call AICheckPlayerQuarterHP
	jr nc, .low_hp
	call AICheckPlayerHalfHP
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
.likely_loop
	ld a, [hli]
	cp -1
	jr z, .possible
	ld b, a
	push hl
	ld a, b
	call BossAI_TestLikelyMaskBit
	pop hl
	jr nc, .likely_loop
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
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
	ld a, b
	call BossAI_TestPlausibleMaskBit
	pop hl
	jr nc, .possible_loop
	push hl
	ld a, b
	call BossAI_TestLikelyMaskBit
	pop hl
	jr c, .possible_loop
	ld a, b
	call BossAI_GetTypeThreatSeverityVsEnemyMon
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
	call BossAI_TestLikelyMaskBit
	jr c, .scan_hidden_power
	ld a, d
	and a
	jr nz, .done
	ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT
	call BossAI_TestPlausibleMaskBit
	jr nc, .none
.scan_hidden_power
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
	call BossAI_GetTypeThreatSeverityVsEnemyMon
	and a
	ret z
	scf
	ret

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

BossAI_AdjustThreatSeverityForEnemyKnownDefense:
; input: c = public threat type, b = severity. output: a = adjusted severity.
	ld a, c
	call BossAI_EnemyKnownItemNullifiesThreatType
	jr nc, .assault_vest
	xor a
	ret

.assault_vest
	call BossAI_GetEnemyHeldEffect
	cp HELD_ASSAULT_VEST
	jr nz, .eviolite
	ld a, c
	cp SPECIAL
	jr c, .eviolite
	call BossAI_DecThreatSeverityB

.eviolite
	call BossAI_GetEnemyHeldEffect
	cp HELD_EVOLITE
	jr nz, .done
	call BossAI_EnemySpeciesCanEvolve
	jr nc, .done
	call BossAI_DecThreatSeverityB

.done
	ld a, b
	ret

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

BossAI_DecThreatSeverityB:
	ld a, b
	and a
	ret z
	dec b
	ret

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

BossAI_GetSpeculativePlausibleRiskWeight:
	call BossAI_GetTierPlausibleRiskWeight
	srl a
	ret nz
	inc a
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
	push de
	call .InsertCandidate
	pop de
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
; rows 0..2 mirror AI_TIER_EARLY/MID/LATE; rows 3..4 are sub-tier bumps used by
; BossAITierRampMap to ramp specific early-tier trainers toward MID without
; flipping the tier value (which would also enable MID-only feature gates).
	db 4, 2, 1, 1, 1, 1, 2 ; row 0: early
	db 5, 3, 2, 2, 1, 1, 2 ; row 1: mid
	db 7, 4, 4, 2, 2, 3, 1 ; row 2: late
	db 5, 2, 1, 1, 1, 1, 2 ; row 3: early +25% (one delta column raised toward mid)
	db 5, 3, 1, 1, 1, 1, 2 ; row 4: early +50% (two delta columns raised toward mid)

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
