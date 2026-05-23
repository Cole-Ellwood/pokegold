; ============================================================
; engine/battle/ai/observation_log.asm - Boss AI public observation log
; P5 WRAMX-2 substrate for recent public player tendencies.
; Included with BOSSAI_EMIT_* guards from main.asm.
; ============================================================

if DEF(BOSSAI_EMIT_OBSERVATION_LOG)

; ai-layer: PLATFORM
BossAI_ClearObservationLog::
	ldh a, [hWRAMBank]
	push af
	ld a, 2
	call SetWRAMBank
	ld hl, wBossAIWramx2Buffer
	ld bc, wBossAIWramx2BufferEnd - wBossAIWramx2Buffer
	xor a
	call ByteFill
	pop af
	call SetWRAMBank
	ret

; ai-layer: PLATFORM
BossAI_AppendObservationLog::
; Called at the next-turn boundary before pending player switches are folded
; into the aggregate count. The entry is public: pending switch marker,
; last displayed player move, public matchup severity, and visible move order.
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	call BossAI_ClassifyCurrentObservation
	ld d, a
	call BossAI_CurrentObservationDamageBand
	ld e, a
	call BossAI_CurrentObservationSpeedRelation
	push af
	call BossAI_ObservationWindowLimit
	ld h, a
	push af
	ld a, [wBossAITurnsElapsed]
	ld c, a
	ldh a, [hWRAMBank]
	ld b, a
	ld a, 2
	call SetWRAMBank

	ld a, [wBossAIObsWriteIndex]
	cp h
	jr c, .index_ok
	xor a
.index_ok
	ld h, a
	add a
	add a
	add LOW(wBossAIObsEntries)
	ld l, a
	ld a, HIGH(wBossAIObsEntries)
	adc 0
	ld h, a
	ld a, c
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, e
	ld [hli], a
	pop af ; window limit
	ld c, a
	pop af ; speed relation
	ld [hli], a

	ld a, [wBossAIObsWriteIndex]
	inc a
	cp c
	jr c, .store_index
	xor a
.store_index
	ld [wBossAIObsWriteIndex], a

	ld a, [wBossAIObsCount]
	cp c
	jr c, .inc_count
	ld a, c
	jr .store_count
.inc_count
	inc a
	cp c
	jr c, .store_count
	ld a, c
.store_count
	ld [wBossAIObsCount], a

	ld a, b
	call SetWRAMBank
	ret

; ai-layer: PLATFORM
BossAI_ClassifyCurrentObservation:
	ld a, [wBossAIPendingPlayerSwitchCount]
	and a
	jr nz, .switch
	ld a, [wLastPlayerMove]
	and a
	jr z, .none
	cp STRUGGLE
	jr z, .bad_matchup_attack
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	ld b, a
	cp EFFECT_HIDDEN_POWER
	jr z, .none
	cp EFFECT_PROTECT
	jr z, .protect_recover
	cp EFFECT_HEAL
	jr z, .protect_recover
	cp EFFECT_MORNING_SUN
	jr z, .protect_recover
	cp EFFECT_SYNTHESIS
	jr z, .protect_recover
	cp EFFECT_MOONLIGHT
	jr z, .protect_recover
	call BossAI_IsSetupEffect
	jr c, .setup
	ld a, b
	call BossAI_IsStatusEffect
	jr c, .status
	call BossAI_LastPlayerMovePower
	and a
	jr z, .none
	call AICheckPlayerQuarterHP_HL
	jr nc, .low_hp_sack
	ld a, [wLastPlayerMove]
	call BossAI_GetRevealedMoveThreatTypeAndSeverity
	jr c, .none
.bad_matchup_attack
	ld a, BOSS_AI_OBS_CLASS_BAD_MATCHUP_ATTACK
	ret
.switch
	ld a, BOSS_AI_OBS_CLASS_SWITCH_UNDER_PRESSURE
	ret
.protect_recover
	ld a, BOSS_AI_OBS_CLASS_PROTECT_RECOVER
	ret
.setup
	ld a, BOSS_AI_OBS_CLASS_GREEDY_SETUP
	ret
.status
	ld a, BOSS_AI_OBS_CLASS_STATUS_FISH
	ret
.low_hp_sack
	ld a, BOSS_AI_OBS_CLASS_LOW_HP_SACK
	ret
.none
	xor a
	ret

; ai-layer: PLATFORM
BossAI_CurrentObservationDamageBand:
	call BossAI_LastPlayerMovePower
	and a
	jr z, .unknown
	call BossAI_LastPlayerMoveEffect
	cp EFFECT_HIDDEN_POWER
	jr z, .unknown
	ld a, [wLastPlayerMove]
	call BossAI_GetRevealedMoveThreatTypeAndSeverity
	jr nc, .light
	and a
	jr z, .light
	cp 6
	jr nc, .ko_pressure
	cp 3
	jr nc, .heavy
	ld a, BOSS_AI_OBS_DAMAGE_SOLID
	ret
.ko_pressure
	ld a, BOSS_AI_OBS_DAMAGE_KO_PRESSURE
	ret
.heavy
	ld a, BOSS_AI_OBS_DAMAGE_HEAVY
	ret
.light
	ld a, BOSS_AI_OBS_DAMAGE_LIGHT
	ret
.unknown
	xor a
	ret

; ai-layer: PLATFORM
BossAI_LastPlayerMovePower:
	ld a, [wLastPlayerMove]
	and a
	ret z
	cp STRUGGLE
	jr z, .struggle
	dec a
	ld hl, Moves + MOVE_POWER
	jp BossAI_GetMoveAttr
.struggle
	ld a, 50
	ret

; ai-layer: PLATFORM
BossAI_LastPlayerMoveEffect:
	ld a, [wLastPlayerMove]
	and a
	ret z
	cp STRUGGLE
	jr z, .struggle
	dec a
	ld hl, Moves + MOVE_EFFECT
	jp BossAI_GetMoveAttr
.struggle
	xor a
	ret

; ai-layer: PLATFORM
BossAI_CurrentObservationSpeedRelation:
	ld a, [wEnemyGoesFirst]
	and a
	jr z, .player_first
	ld a, BOSS_AI_OBS_SPEED_ENEMY_FIRST
	ret
.player_first
	ld a, BOSS_AI_OBS_SPEED_PLAYER_FIRST
	ret

; ai-layer: PLATFORM
BossAI_ObservationWindowLimit:
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	ld a, BOSS_AI_OBS_MAX_TURNS
	ret nc
	ld a, BOSS_AI_OBS_MID_TURNS
	ret

; ai-layer: POLICY
BossAI_ConsultTendencyCounters::
; Output: a = additive switch-prediction bonus. EARLY returns zero; MID scans
; the three-slot window; LATE scans the six-slot window.
	ld a, [wBossAITier]
	cp AI_TIER_MID
	jr nc, .enabled
	xor a
	ret
.enabled
	push bc
	push de
	push hl
	call BossAI_ObservationWindowLimit
	ld c, a
	ldh a, [hWRAMBank]
	push af
	ld a, 2
	call SetWRAMBank
	ld a, [wBossAIObsCount]
	cp c
	jr c, .count_ok
	ld a, c
.count_ok
	ld d, a
	ld e, 0
	ld hl, wBossAIObsEntries + 1
.loop
	ld a, d
	and a
	jr z, .done
	ld a, [hl]
	push hl
	call BossAI_ObservationWeightForClass
	pop hl
	add e
	cp BOSS_AI_OBS_TENDENCY_BONUS_CAP + 1
	jr c, .store_bonus
	ld a, BOSS_AI_OBS_TENDENCY_BONUS_CAP
.store_bonus
	ld e, a
	ld a, l
	add BOSS_AI_OBS_ENTRY_SIZE
	ld l, a
	jr nc, .next
	inc h
.next
	dec d
	jr .loop
.done
	pop af
	call SetWRAMBank
	ld a, e
	pop hl
	pop de
	pop bc
	ret

; ai-layer: POLICY
BossAI_ConsultKOBandCalibration::
; Output: a = 1 when LATE-tier public observations say the boss has recently
; moved first while the player has not shown heavy/KO-pressure damage.
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr nc, .enabled
	xor a
	ret
.enabled
	push bc
	push de
	push hl
	ldh a, [hWRAMBank]
	push af
	ld a, 2
	call SetWRAMBank
	ld a, [wBossAIObsCount]
	ld d, a
	ld e, 0
	ld hl, wBossAIObsEntries + 2
.loop
	ld a, d
	and a
	jr z, .done
	ld a, [hli]
	cp BOSS_AI_OBS_DAMAGE_HEAVY
	jr nc, .blocked
	ld a, [hl]
	cp BOSS_AI_OBS_SPEED_ENEMY_FIRST
	jr nz, .advance
	ld e, 1
	jr .advance
.blocked
	ld e, 0
	jr .done
.advance
	ld a, l
	add BOSS_AI_OBS_ENTRY_SIZE - 1
	ld l, a
	jr nc, .next
	inc h
.next
	dec d
	jr .loop
.done
	pop af
	call SetWRAMBank
	ld a, e
	pop hl
	pop de
	pop bc
	ret

; ai-layer: POLICY
BossAI_ObservationWeightForClass:
	cp BOSS_AI_OBS_CLASS_COUNT
	jr c, .valid
	xor a
	ret
.valid
	push de
	ld e, a
	ld d, 0
	ld hl, BossAIObservationTendencyWeights
	add hl, de
	ld a, [hl]
	pop de
	ret

INCLUDE "data/boss_ai/tendency_counter_weights.asm"

endc
