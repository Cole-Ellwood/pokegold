; ============================================================
; engine/battle/ai/boss_data.asm — Late policy, lookahead, threat, scout, switch refinement, and data tail
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================

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

; ============================================================
; Region: Score read/write
; Concern: Score pointer, set, encourage, and discourage helpers
; Layer: PLATFORM
; Original lines: 42
; ============================================================
; ai-layer: PLATFORM
BossAI_LoadScorePointer:
	push af
	ld a, [wBossAIScorePtr]
	ld h, a
	ld a, [wBossAIScorePtr + 1]
	ld l, a
	pop af
	ret

; ai-layer: PLATFORM
BossAI_SetScoreHL:
	call BossAI_LoadScorePointer
	ld [hl], a
	ret

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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
	call BossAI_GetTypeThreatSeverityVsEnemyMon
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

; ============================================================
; Region: Scouted bitmap
; Concern: Active-species scouted bitmap and scout decision
; Layer: PLATFORM
; Original lines: 67
; ============================================================
; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
BossAI_SetActiveSpeciesScouted:
	call BossAI_GetActiveSpeciesSeenBit
	ret nc
	ld b, a
	ld a, [wBossAIScoutedMask]
	or b
	ld [wBossAIScoutedMask], a
	ret

; ai-layer: PLATFORM
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

; ============================================================
; Region: Repeat tracker
; Concern: Same-move repeat tracker and scout marking hook
; Layer: PLATFORM
; Original lines: 36
; ============================================================
; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ============================================================
; Region: Static data tables
; Concern: Plausible threats, tier weights, status/role/risky effect tables
; Layer: DATA
; Original lines: 139
; ============================================================
; ai-layer: DATA
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

; ai-layer: DATA
BossAIHiddenPowerThreatTypes:
	db GROUND
	db ICE
	db GRASS
	db ELECTRIC
	db -1

; BossAI_TraceTopMoves moved to engine/battle/ai/boss_trace_topmoves.asm
; (own SECTION) so the trace build doesn't push the "Enemy Trainers" bank
; over its 16 KB ceiling. Caller below uses farcall.

; ai-layer: DATA
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

; ai-layer: DATA
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

; ai-layer: DATA
BossAIStatusEffects:
	db EFFECT_SLEEP
	db EFFECT_PARALYZE
	db EFFECT_CONFUSE
	db EFFECT_POISON
	db EFFECT_TOXIC
	db EFFECT_LEECH_SEED
	db -1

; ai-layer: DATA
BossAIChuckRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_LOCK_ON
	db EFFECT_PRIORITY_HIT
	db -1

; ai-layer: DATA
BossAIJasmineRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_PROTECT
	db EFFECT_RAIN_DANCE
	db -1

; ai-layer: DATA
BossAIPryceRoleEffects:
	db EFFECT_SPEED_DOWN_HIT
	db EFFECT_FORCE_SWITCH
	db EFFECT_HEAL
	db EFFECT_MORNING_SUN
	db EFFECT_SYNTHESIS
	db EFFECT_MOONLIGHT
	db -1

; ai-layer: DATA
BossAIClairRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_SPEED_UP
	db EFFECT_SPEED_UP_2
	db EFFECT_RESET_STATS
	db EFFECT_RAIN_DANCE
	db -1

; ai-layer: DATA
BossAIWillRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_REFLECT
	db EFFECT_LEECH_SEED
	db EFFECT_FUTURE_SIGHT
	db -1

; ai-layer: DATA
BossAIBrunoRoleEffects:
	db EFFECT_PRIORITY_HIT
	db EFFECT_FORESIGHT
	db EFFECT_PROTECT
	db -1

; ai-layer: DATA
BossAIKarenRoleEffects:
	db EFFECT_SLEEP
	db EFFECT_CONFUSE
	db EFFECT_TOXIC
	db EFFECT_MEAN_LOOK
	db EFFECT_DESTINY_BOND
	db EFFECT_FORCE_SWITCH
	db -1

; ai-layer: DATA
BossAIKogaRoleEffects:
	db EFFECT_TOXIC
	db EFFECT_SPIKES
	db EFFECT_PROTECT
	db EFFECT_BATON_PASS
	db EFFECT_CONFUSE
	db -1

; ai-layer: DATA
BossAIChampionRoleEffects:
	db EFFECT_PARALYZE
	db EFFECT_RAIN_DANCE
	db EFFECT_SAFEGUARD
	db EFFECT_FORCE_SWITCH
	db -1

; ai-layer: DATA
BossAIRiskyEffects:
	db EFFECT_SELFDESTRUCT
	db EFFECT_RECOIL_HIT
	db EFFECT_HYPER_BEAM
	db EFFECT_BELLY_DRUM
	db -1

; ============================================================
