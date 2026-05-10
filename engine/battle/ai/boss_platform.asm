; ============================================================
; engine/battle/ai/boss_platform.asm — Opening state/public-info platform and first move-policy block, kept byte-ordered
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================

; ============================================================
; Region: State tracking
; Concern: Turn counter, switch counter, seen-species bitmap, alive bitmap
; Layer: PLATFORM
; Original lines: 143
; ============================================================
; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
BossAI_SetSeenPlayerAliveBit:
	push bc
	call BossAI_SeenPlayerSpeciesBitFromC
	ld hl, wBossAISeenPlayerAliveMask
	or [hl]
	ld [hl], a
	pop bc
	ret

; ai-layer: PLATFORM
BossAI_ClearSeenPlayerAliveBit:
	push bc
	call BossAI_SeenPlayerSpeciesBitFromC
	cpl
	ld hl, wBossAISeenPlayerAliveMask
	and [hl]
	ld [hl], a
	pop bc
	ret

; ai-layer: PLATFORM
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

; ============================================================
; Region: Public-info plumbing
; Concern: Revealed-moves bitmap, used-moves mirror, move-attribute reads
; Layer: PLATFORM
; Original lines: 189
; ============================================================
; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
BossAI_GetMoveAttr:
	push bc
	ld bc, MOVE_LENGTH
	call AddNTimes
	call BossAI_GetMoveByte
	pop bc
	ret

; ai-layer: PLATFORM
BossAI_GetMoveByte:
	ld a, BANK(Moves)
	jp GetFarByte

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ============================================================
; Region: Per-tick cache reset
; Concern: Sentinel writes to per-tick Boss AI cache bytes
; Layer: PLATFORM
; Original lines: 14
; ============================================================
; ai-layer: PLATFORM
BossAI_ResetTurnCaches:
; Clear the per-AI-tick memo caches consumed by the cached helpers
; (HasAnyKOMove / PlayerHasPublicThreatVsEnemy / PlayerHasRevealedPriorityThreat
; / PredictPlayerSwitch / GetPrimaryThreatType). Inputs to each are stable
; within one tick; first call computes, the rest read from cache. Saves
; ~50 type-chart walks per LATE-tier move-pick. Sentinel is $ff for all
; five — the GetPrimaryThreatType wrapper distinguishes "no threat" via a
; separate $20+ band since real type ids cap at $1b.
	ld a, $ff
	ld [wBossAIHasKOMoveCache], a
	ld [wBossAIPublicThreatCache], a
	ld [wBossAIRevealedPriorityCache], a
	ld [wBossAIPrimaryThreatCache], a
	ret

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
	call AIGetEnemyMove_HL

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
	call .ApplyRoleBias
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
	call AICheckEnemyQuarterHP_HL
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
	call AICheckEnemyMaxHP_HL
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
	call AICheckEnemyMaxHP_HL
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
	call AICheckEnemyQuarterHP_HL
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
	call AICheckPlayerQuarterHP_HL
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
	call AICheckPlayerMaxHP_HL
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
	call AICheckPlayerHalfHP_HL
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

; ============================================================
