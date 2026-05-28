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
BossAI_TrySwitch:
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_ResetTurnCaches
	call BossAI_SelectPlanIfNeeded
	call BossAI_ComputePlayerPlausibleTypeMask
	call BossAI_OracleHakiRead
	ret nz
	call BossAI_HakiReserveAceAction
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
	ret z
	call BossAI_RefineSwitchCandidateForPlausibleRisk
	ld a, [wEnemySwitchMonParam]
	and a
	ret z
	call BossAI_GetPrimaryThreatType
	jr nc, .candidate_answers_threat
	call BossAI_IsImmunityPivotOpportunity
	jr c, .candidate_answers_threat
	xor a
	ld [wEnemySwitchMonParam], a
	ret

.candidate_answers_threat

	ld a, [wEnemySwitchMonParam]
	and a
	ret z
	; LATE-tier categorical sack: dying low-speed non-wincon non-asleep mons
	; stay in to use their last turn instead of letting the player get a free
	; hit on the next mon. Soft +8 to threshold doesn't move the needle when
	; ComputeSwitchConfidence base alone is 65-90 + bonuses.
	call BossAI_ShouldSackHard
	jr nc, .no_hard_sack
	xor a
	ld [wEnemySwitchMonParam], a
	ret
.no_hard_sack
	; Bug B fix: block switching INTO a low-HP candidate unless it's an
	; immunity pivot. Without this, an AI seeing a "best-matchup" bench mon
	; switches into it even when it has 12/60 HP and will die before
	; contributing. The candidate's HP is otherwise never read.
	call BossAI_SwitchCandidateLowHPBlock
	jr nc, .no_low_hp_block
	xor a
	ld [wEnemySwitchMonParam], a
	ret
.no_low_hp_block
	push af
	call BossAI_ComputeSwitchConfidence
	ld [wBossAISwitchConfidence], a
IF DEF(BOSS_AI_TRACE)
	ld [wBossAITraceSwitchConfidence], a
ENDC
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
	; Reload confidence from WRAM. The .no_penalty / sack-bias / wincon-risk
	; helpers above all use `b` internally, so reading `b` here would compare
	; against helper scratch instead of the stored switch confidence.
	ld a, [wBossAISwitchConfidence]
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
	ret

; ai-layer: POLICY
BossAI_OracleHakiRead:
; Uniform Haki exception: once per battle, on the ace's first active turn,
; an eligible boss reads the player's already-locked move. If a bench mon
; is immune to that move type while the active is not, pivot to it; else
; pick the best move from normal scoring. This is the only normal Boss AI
; routine allowed to read current-turn input.
	call BossAI_HakiReadyCommon
	jr nc, .no
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
	call BossAI_HakiFindImmunitySwitch
	jp c, BossAI_CommitHakiOracleSwitch
	call BossAI_ChooseBestOracleMove
	jr nc, .no
	jp BossAI_CommitHakiOracleChoice

.no
	xor a
	ret

BossAI_OracleHakiAfterPlayerAction:
; Player-first Haki fires immediately before the enemy action. At this point
; a player move has resolved or a switch-in is already public on the field, so
; rebuild scores against the true current target before choosing.
	ld a, [wBossAITier]
	and a
	ret z
	call BossAI_HakiReadyCommon
	jr nc, .no
	ld a, [wBattlePlayerAction]
	cp BATTLEPLAYERACTION_SWITCH
	jr z, .switch_read
	and a ; BATTLEPLAYERACTION_USEMOVE?
	jr nz, .no
	ld a, [wCurPlayerMove]
	and a
	jr z, .no
	call BossAI_RebuildHakiMoveScores
	jr .choose

.switch_read
	call BossAI_RebuildHakiMoveScores

.choose
	call BossAI_ChooseBestOracleMove
	jr nc, .no
	jp BossAI_CommitHakiOracleChoice

.no
	xor a
	ret

BossAI_HakiReserveAceAction:
; If the ace is due to Haki on a player-first move turn, do not let normal
; switch/item logic consume the action before the post-player hook can fire.
	ld a, [wEnemyGoesFirst]
	and a
	jr nz, .no
	call BossAI_HakiReadyCommon
	jr nc, .no
	ld a, [wBattlePlayerAction]
	and a ; BATTLEPLAYERACTION_USEMOVE?
	jr nz, .no
	ld a, 1
	and a
	ret

.no
	xor a
	ret

BossAI_HakiReadyCommon:
	ld a, [wBossAITier]
	and a
	jr z, .no
	ld hl, wBossAIRevealedMovesBitmapSpare + 1
	bit BOSSAI_HAKI_SPENT_F, [hl]
	jr nz, .no
	bit BOSSAI_HAKI_ELIGIBLE_F, [hl]
	jr z, .no
	ld a, [wEnemySubStatus5]
	bit SUBSTATUS_ENCORED, a
	jr nz, .no
	callfar CheckEnemyLockedIn
	jr nz, .no
	scf
	ret

.no
	and a
	ret

BossAI_RebuildHakiMoveScores:
	ld a, 20
	ld hl, wEnemyAIMoveScores
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a

	ld a, [wEnemyDisabledMove]
	and a
	jr z, .check_pp
	ld b, a
	ld hl, wEnemyMonMoves
	ld c, 0
.disabled_loop
	ld a, [hli]
	cp b
	jr z, .score_disabled
	inc c
	ld a, c
	cp NUM_MOVES
	jr nz, .disabled_loop
	jr .check_pp

.score_disabled
	ld hl, wEnemyAIMoveScores
	ld b, 0
	add hl, bc
	ld [hl], 80

.check_pp
	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonPP
	ld c, NUM_MOVES
.pp_loop
	ld a, [de]
	and PP_MASK
	jr nz, .pp_next
	ld [hl], 80
.pp_next
	inc hl
	inc de
	dec c
	jr nz, .pp_loop

	call BossAI_ApplyMoveModel
	call BossAI_ApplyLookaheadToTopMoveCandidates
IF DEF(BOSS_AI_TRACE)
	farcall BossAI_TraceTopMoves
ENDC
	ret

BossAI_CommitHakiOracleChoice:
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

BossAI_CommitHakiOracleSwitch:
; Commit a Haki defensive switch. wBossAITemp holds the 0-based bench
; slot picked by BossAI_HakiFindImmunitySwitch; convert to 1-based for
; wEnemySwitchMonIndex, queue the per-leader taunt, mark Haki spent,
; and tail-call AI_TrySwitch. AI_Switch ends with `scf; ret`, and the
; carry survives through BossAI_TrySwitch's `ret nz` (the cp
; LINK_COLOSSEUM right before scf leaves NZ in non-link battles), so
; the core.asm caller sees `jr c, .switch_item` and routes through
; the switch handler.
	ld a, [wBossAITemp]
	inc a
	ld [wEnemySwitchMonIndex], a
	call BossAI_QueueHakiTaunt
	ld hl, wBossAIRevealedMovesBitmapSpare + 1
	set BOSSAI_HAKI_SPENT_F, [hl]
	res BOSSAI_HAKI_ELIGIBLE_F, [hl]
IF DEF(BOSS_AI_TRACE)
	ld a, [wBossAITraceRiskFlags]
	or 1 << BOSSAI_HAKI_TRACE_FIRED_F
	ld [wBossAITraceRiskFlags], a
ENDC
	jp AI_TrySwitch

BossAI_HakiFindImmunitySwitch:
; Search the bench for a mon immune (NO_EFFECT) to the locked move's
; type when the active is not already immune. Returns carry set with
; wBossAITemp = bench slot (0-based) if found, else carry clear.
;
; Reads:    wCurPlayerMove (non-zero), wEnemyMonSpecies, wOTPartyCount,
;           wCurOTMon, wOTPartySpecies, wOTPartyMon1HP.
; Clobbers: bc, de, hl; wBossAITemp (slot on success), wBossAITemp2/3
;           (scratch), wCurSpecies (restored), wBaseStats / wBaseType*
;           (left at whichever mon was last looked up; callers needing
;           active base data must reload via GetBaseData).
	ld a, [wCurPlayerMove]
	dec a
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr
	ld [wBossAITemp2], a

	ld a, [wCurSpecies]
	ld [wBossAITemp3], a

	ld a, [wEnemyMonSpecies]
	and a
	jr z, .none
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBossAITemp2]
	call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .none ; active is already immune

	ld a, [wOTPartyCount]
	and a
	jr z, .none
	ld d, a
	ld e, 0
	ld hl, wOTPartyMon1HP

.loop
	ld a, [wCurOTMon]
	cp e
	jr z, .next

	ld a, [hli]
	ld b, a
	ld a, [hl]
	dec hl
	or b
	jr z, .next ; fainted

	push hl
	push de
	ld hl, wOTPartySpecies
	ld d, 0
	add hl, de
	ld a, [hl]
	pop de
	pop hl
	and a
	jr z, .next
	cp $ff
	jr z, .next

	push hl
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBossAITemp2]
	call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem
	pop hl
	ld a, [wTypeMatchup]
	and a
	jr z, .found

.next
	push de
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	pop de
	inc e
	dec d
	jr nz, .loop

.none
	ld a, [wBossAITemp3]
	ld [wCurSpecies], a
	and a
	jr z, .none_skip_base
	call GetBaseData
.none_skip_base
	and a
	ret

.found
	ld a, e
	ld [wBossAITemp], a
	ld a, [wBossAITemp3]
	ld [wCurSpecies], a
	and a
	jr z, .found_skip_base
	call GetBaseData
.found_skip_base
	scf
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
; Concern: Tier threshold and loop-penalty gates
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
	call BossAI_GetPrimaryThreatType
	ret nc
	ld [wBossAITemp], a
	ld a, [wCurSpecies]
	push af

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
	ld a, [wBossAITemp]
	call BossAI_CheckPlayerMoveTypeMatchupVsBaseNoItem
	ld a, [wTypeMatchup]
	cp EFFECTIVE
	jr nc, .not_immune
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
	; Removed the prior `+10 if active is at quarter HP` bonus. It was
	; structurally backwards: it directly fought BossAI_ShouldSackInsteadOfSwitch's
	; +8 to threshold and won by 2, so low active HP slightly *increased* switch
	; likelihood instead of biasing toward sacking. Removed so the sack-bias
	; lever can actually move the decision when the active mon is dying.
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
	call BossAI_ApplyRolePackageSwitchBias
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
BossAI_ApplyRolePackageSwitchBias::
	ld a, [wBossAITier]
	cp AI_TIER_MID
	jr nc, .enabled
	ld a, b
	ret
.enabled
	push bc
	call BossAI_ClassifyActivePlayerRolePackage
	ld d, a
	pop bc
	ld a, d
	and a
	jr nz, .has_package
	ld a, b
	ret

.has_package
	ld c, 0
	bit BOSS_AI_ROLEPKG_TRAP_PERISH_F, d
	jr z, .no_trap_perish
	ld a, c
	add 10
	ld c, a
.no_trap_perish
	bit BOSS_AI_ROLEPKG_SETUP_SWEEPER_F, d
	jr z, .no_setup
	ld a, c
	add 8
	ld c, a
.no_setup
	bit BOSS_AI_ROLEPKG_PRIORITY_REVENGE_F, d
	jr z, .no_priority
	ld a, c
	add 6
	ld c, a
.no_priority
	bit BOSS_AI_ROLEPKG_WALLBREAKER_F, d
	jr z, .no_wallbreaker
	ld a, c
	add 6
	ld c, a
.no_wallbreaker
	bit BOSS_AI_ROLEPKG_STATUS_PRESSURE_F, d
	jr z, .no_status
	ld a, c
	add 4
	ld c, a
.no_status
	bit BOSS_AI_ROLEPKG_PHAZER_F, d
	jr z, .no_phazer
	ld a, c
	add 4
	ld c, a
.no_phazer
	bit BOSS_AI_ROLEPKG_RECOVERY_WALL_F, d
	jr z, .no_recovery
	ld a, c
	add 2
	ld c, a
.no_recovery
	bit BOSS_AI_ROLEPKG_SPINNER_F, d
	jr z, .cap_bonus
	ld a, c
	add 2
	ld c, a

.cap_bonus
	ld a, c
	cp BOSS_AI_ROLEPKG_SWITCH_BONUS_CAP + 1
	jr c, .bonus_ok
	ld a, BOSS_AI_ROLEPKG_SWITCH_BONUS_CAP
.bonus_ok
	add b
	cp 100
	ret c
	ld a, 99
	ret

; ai-layer: POLICY
BossAI_ClassifyActivePlayerRolePackage::
	ld a, [wBossAITier]
	cp AI_TIER_MID
	jr nc, .enabled
	xor a
	ret
.enabled
	ld a, [wBattleMonSpecies]
	and a
	ret z
	cp NUM_POKEMON + 1
	jr c, .valid_species
	xor a
	ret
.valid_species
	dec a
	ld e, a
	ld d, 0
	ld hl, BossAIRolePackageBySpecies
	add hl, de
	ld a, [hl]
	push af
	call BossAI_LastPlayerMoveRolePackageMask
	ld b, a
	pop af
	or b
	ret

; ai-layer: POLICY
BossAI_LastPlayerMoveRolePackageMask::
	ld a, [wLastPlayerMove]
	and a
	ret z
	cp STRUGGLE
	jr nz, .load_effect
	xor a
	ret
.load_effect
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	ld b, a
	ld c, 0
	cp EFFECT_RAPID_SPIN
	jr nz, .check_phazer
	set BOSS_AI_ROLEPKG_SPINNER_F, c
.check_phazer
	ld a, b
	cp EFFECT_FORCE_SWITCH
	jr nz, .check_setup
	set BOSS_AI_ROLEPKG_PHAZER_F, c
.check_setup
	ld a, b
	call BossAI_IsSetupEffect
	jr nc, .check_recovery
	set BOSS_AI_ROLEPKG_SETUP_SWEEPER_F, c
.check_recovery
	ld a, b
	cp EFFECT_HEAL
	jr z, .set_recovery
	cp EFFECT_MORNING_SUN
	jr z, .set_recovery
	cp EFFECT_SYNTHESIS
	jr z, .set_recovery
	cp EFFECT_MOONLIGHT
	jr nz, .check_priority
.set_recovery
	set BOSS_AI_ROLEPKG_RECOVERY_WALL_F, c
.check_priority
	ld a, b
	cp EFFECT_PRIORITY_HIT
	jr nz, .check_status
	set BOSS_AI_ROLEPKG_PRIORITY_REVENGE_F, c
.check_status
	ld a, b
	call BossAI_IsStatusEffect
	jr nc, .check_trap
	set BOSS_AI_ROLEPKG_STATUS_PRESSURE_F, c
.check_trap
	ld a, b
	cp EFFECT_TRAP_TARGET
	jr z, .set_trap
	cp EFFECT_PERISH_SONG
	jr z, .set_trap
	cp EFFECT_MEAN_LOOK
	jr nz, .check_wallbreaker
.set_trap
	set BOSS_AI_ROLEPKG_TRAP_PERISH_F, c
.check_wallbreaker
	call BossAI_LastPlayerMovePower
	cp 90
	jr c, .done
	set BOSS_AI_ROLEPKG_WALLBREAKER_F, c
.done
	ld a, c
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
BossAI_PickFaintReplacement::
; Pre-faint-replacement hook. When the boss's active mon faints and
; wEnemySwitchMonIndex is 0, score each healthy bench candidate and pick the
; best by (priority, hp%). This bypasses both the vanilla type-only scorer
; (which doesn't consider candidate HP or offensive coverage) and the prior
; "first alive above ¼ HP" hack (which picked by party-order accident, e.g.
; Morty's Misdreavus over Haunter 2 even though Haunter 2 has Ice Punch).
;
; Per-candidate priority:
;   2 = has real coverage AND resists at least one of active player's types
;   1 = has real coverage (any move where SE × BP >= 60 × relevant base stat >= 60)
;   0 = no real coverage
; "Real coverage" = a move with effectiveness >= 2x vs active player, BP >= 60,
; and candidate's base Atk (physical type) / SpA (special type) >= 60. The two
; >=60 thresholds filter tickle moves (Acid 40 BP) and weak attackers respectively.
;
; Hard skip (excluded entirely) if candidate is 2x-or-worse weak to either of
; the active player's types: don't suicide a bench mon into a STAB counter.
;
; Tiebreak within priority: highest HP% (computed inline 0..100).
;
; If all candidates are filtered out by the 2x-weakness gate, leave
; wEnemySwitchMonIndex at 0 — vanilla's type-only scorer handles "all my bench
; is bad" rather than us forcing a synthetic answer. Tier-gated: returns
; immediately for non-boss trainers.
	ld a, [wBossAITier]
	and a
	ret z
	ld a, [wEnemySwitchMonIndex]
	and a
	ret nz
	push bc
	push de
	push hl
	xor a
	ld [wBossAITemp], a   ; best priority so far
	ld [wBossAITemp2], a  ; best hp% so far
	ld [wBossAITemp3], a  ; best idx+1 so far (0 = none found)
	ld a, [wOTPartyCount]
	ld b, a
	ld c, 0
.scan
	ld a, b
	and a
	jr z, .done
	call BossAI_FaintRepl_EvalCandidate
	jr nc, .next
	; carry set: d = priority, e = hp%. Compare against running best.
	ld a, [wBossAITemp]
	cp d
	jr c, .update
	jr nz, .next
	ld a, [wBossAITemp2]
	cp e
	jr nc, .next
.update
	ld a, d
	ld [wBossAITemp], a
	ld a, e
	ld [wBossAITemp2], a
	ld a, c
	inc a
	ld [wBossAITemp3], a
.next
	inc c
	dec b
	jr .scan
.done
	ld a, [wBossAITemp3]
	and a
	jr z, .nothing
	ld [wEnemySwitchMonIndex], a
.nothing
	pop hl
	pop de
	pop bc
	ret

; ai-layer: POLICY
BossAI_FaintRepl_EvalCandidate:
; Score one candidate for faint-replacement selection.
;
; In:  c = candidate party idx (0-based)
; Out: carry SET   → d = priority (0/1/2), e = hp% (0..100)
;      carry CLEAR → exclude (active, fainted, ≤¼ HP, or 2x-weak to active STAB)
; Preserves: bc (loop state)
; Scratch: wBossAITemp4..5 (candidate types).
;
; Step order:
;   1) Active-mon check + HP gate (alive, >¼ HP); compute hp% in e.
;   2) Load candidate base data into wCurBaseData; stash types in temp4/5.
;   3) Coverage scan while wCurBaseData is candidate's (reads BASE_ATK/SAT).
;   4) Restore wCurSpecies + wCurBaseData to active mon.
;   5) 2x-weak + resist check via wBossAITemp4/5.
;   6) Compose priority from (has_cov, has_resist).
;
; Stack discipline: function prologue pushes bc + hl. Step 2 pushes hp%-de
; then active-species-af. Step 4 pops both in reverse. After step 4 the
; stack is back to the 2-push prologue state, so every exit path is
; `pop hl; pop bc; ret`.
	push bc
	push hl

	; (1a) Active-mon skip
	ld a, [wCurOTMon]
	cp c
	jp z, .skip

	; (1b) HP gate + hp%
	call BossAI_FaintRepl_HPGateAndPct
	jp nc, .skip
	; e = hp%; bc still = caller's (loop count, idx)

	; (2) Load candidate base data; stash types in temp4/5
	push de                       ; save hp% (e); d junk
	ld hl, wOTPartyMon1Species
	ld a, c
	call GetPartyLocation
	ld a, [hl]
	ld d, a                       ; candidate species
	ld a, [wCurSpecies]
	push af                       ; save active species
	ld a, d
	ld [wCurSpecies], a
	call GetBaseData              ; wCurBaseData ← candidate
	ld a, [wCurBaseData + BASE_TYPE_1]
	ld [wBossAITemp4], a
	ld a, [wCurBaseData + BASE_TYPE_2]
	ld [wBossAITemp5], a

	; (3) Coverage scan
	call BossAI_FaintRepl_CandidateHasRealCoverage
	; carry = has_cov. Convert to b = 0/1 (clobbers loop count, restored on exit).
	ld a, 0
	adc a
	ld b, a                       ; b = has_cov

	; (4) Restore active species; refresh wCurBaseData.
	; GetBaseData preserves bc/de/hl (see home/pokemon.asm:215), so b (has_cov)
	; and the pushed de (hp%) survive.
	pop af                        ; active species
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	pop de                        ; restore hp% to e (d junk)

	; (5) 2x-weak + resist check.
	;   Inputs:  wBattleMonType1/2 (player), wBossAITemp4/5 (candidate)
	;   Outputs: branch to .matchup_weak | .matchup_resists | .matchup_neutral
	; BossAI_CheckTypeMatchupNoItem preserves bc, so b=has_cov survives both calls.
	ld a, [wBattleMonType1]
	ld hl, wBossAITemp4
	call BossAI_CheckTypeMatchupNoItem
	ld a, [wTypeMatchup]
	ld d, a                       ; d = eff vs type1
	ld a, [wBattleMonType1]
	ld c, a
	ld a, [wBattleMonType2]
	cp c
	jr z, .single_type
	; Distinct second type: run matchup again.
	ld a, [wBattleMonType2]
	ld hl, wBossAITemp4
	call BossAI_CheckTypeMatchupNoItem
	ld a, [wTypeMatchup]
	ld c, a                       ; c = eff vs type2 (clobbers idx; not needed past here)
	; Weak if max(d, c) ≥ SUPER_EFFECTIVE.
	cp SUPER_EFFECTIVE
	jr nc, .matchup_weak
	ld a, d
	cp SUPER_EFFECTIVE
	jr nc, .matchup_weak
	; Resist if min(d, c) < EFFECTIVE.
	cp EFFECTIVE
	jr c, .matchup_resists
	ld a, c
	cp EFFECTIVE
	jr c, .matchup_resists
	jr .matchup_neutral
.single_type
	ld a, d
	cp SUPER_EFFECTIVE
	jr nc, .matchup_weak
	cp EFFECTIVE
	jr c, .matchup_resists
	jr .matchup_neutral

	; (6) Compose priority.
.matchup_weak
	jr .skip
.matchup_resists
	ld a, b                       ; has_cov
	and a
	jr z, .priority_zero
	ld d, 2
	jr .priority_done
.matchup_neutral
	ld a, b
	and a
	jr z, .priority_zero
	ld d, 1
	jr .priority_done
.priority_zero
	ld d, 0
.priority_done
	pop hl
	pop bc
	scf
	ret

.skip
	pop hl
	pop bc
	and a
	ret

; ai-layer: POLICY
BossAI_FaintRepl_HPGateAndPct:
; Read candidate's HP and maxHP from party WRAM, gate on alive + above ¼ HP,
; compute hp% = HP * 100 / maxHP using the HRAM math UNION.
;
; In:  c = candidate party idx (0-based)
; Out: carry SET  → e = hp% (0..100); HP gate passed
;      carry CLEAR → fainted, ≤¼ HP, or zero HP
; Preserves: bc; clobbers: a, d, e, hl, math UNION
	push bc
	ld hl, wOTPartyMon1HP
	ld a, c
	call GetPartyLocation
	ld a, [hli]
	ld b, a                       ; HP hi
	ld a, [hli]
	ld c, a                       ; HP lo (clobbers idx — restored via pop bc at exit)
	or b
	jr z, .fail
	ld a, [hli]
	ld d, a                       ; maxHP hi
	ld a, [hl]
	ld e, a                       ; maxHP lo
	; HP*4 > maxHP?
	ld h, b
	ld l, c
	add hl, hl
	add hl, hl                    ; hl = HP*4
	ld a, h
	cp d
	jr c, .fail
	jr nz, .pass_quarter
	ld a, l
	cp e
	jr c, .fail
	jr z, .fail                   ; equal counts as "at quarter" (≤ excluded)
.pass_quarter
	; hp% via HRAM math.
	xor a
	ldh [hMultiplicand + 0], a
	ld a, b
	ldh [hMultiplicand + 1], a
	ld a, c
	ldh [hMultiplicand + 2], a
	ld a, 100
	ldh [hMultiplier], a
	push de                       ; preserve maxHP
	call Multiply
	pop de
	; Scale maxHP (de) and hProduct in lockstep until maxHP fits in 1 byte.
	ld a, d
	and a
	jr z, .div_ready
.shift
	srl d
	rr e
	ldh a, [hProduct + 1]
	srl a
	ldh [hProduct + 1], a
	ldh a, [hProduct + 2]
	rra
	ldh [hProduct + 2], a
	ldh a, [hProduct + 3]
	rra
	ldh [hProduct + 3], a
	ld a, d
	and a
	jr nz, .shift
.div_ready
	ld a, e
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 3]
	cp 101
	jr c, .pct_ok
	ld a, 100
.pct_ok
	ld e, a
	pop bc
	scf
	ret
.fail
	pop bc
	and a
	ret

; ai-layer: POLICY
BossAI_FaintRepl_CandidateHasRealCoverage:
; Return carry if any of the candidate's 4 moves satisfies ALL of:
;   - raw BP ≥ 60                                       (filters Acid/Karate Chop)
;   - effectiveness vs active player's types ≥ 2×       (super effective)
;   - candidate's base stat for move category ≥ 60      (filters weak attackers)
;     PHYSICAL types → BASE_ATK; SPECIAL types → BASE_SAT.
;
; Preconditions:
;   wCurBaseData = candidate's base data (caller's responsibility)
;   wBattleMonType1/2 = active player's types
;
; In:  c = candidate party idx (0-based)
; Out: carry set if has real coverage; clear otherwise
; Preserves: bc
	push bc
	push de
	push hl
	ld hl, wOTPartyMon1Moves
	ld a, c
	call GetPartyLocation         ; hl = candidate's MON_MOVES (4 bytes)
	ld b, 4                       ; counter
.move_loop
	ld a, [hli]
	and a
	jr z, .next_move              ; empty slot
	push hl                       ; save hl across attribute lookups
	push bc                       ; save (counter b, idx c)
	dec a
	ld c, a                       ; c = move_id - 1 (clobbers idx; saved on stack)

	; BP gate (filters tickle moves)
	ld a, c
	ld hl, Moves + MOVE_POWER
	call BossAI_GetMoveAttr       ; preserves bc; a = BP
	cp 60
	jr c, .move_fail

	; Type lookup
	ld a, c
	ld hl, Moves + MOVE_TYPE
	call BossAI_GetMoveAttr       ; a = move type
	ld d, a

	; Effectiveness vs active player
	ld a, d
	ld hl, wBattleMonType1
	call BossAI_CheckTypeMatchupNoItem  ; preserves bc
	ld a, [wTypeMatchup]
	cp SUPER_EFFECTIVE
	jr c, .move_fail

	; Stat floor (uses wCurBaseData = candidate)
	ld a, d
	cp SPECIAL
	jr c, .use_atk
	ld a, [wCurBaseData + BASE_SAT]
	jr .check_stat
.use_atk
	ld a, [wCurBaseData + BASE_ATK]
.check_stat
	cp 60
	jr c, .move_fail

	; All gates pass: candidate has real coverage.
	pop bc
	pop hl
	pop hl                        ; prologue hl
	pop de                        ; prologue de
	pop bc                        ; prologue bc (restores outer counter+idx)
	scf
	ret

.move_fail
	pop bc
	pop hl
.next_move
	dec b
	jr nz, .move_loop
	pop hl
	pop de
	pop bc
	and a
	ret

; ai-layer: POLICY
BossAI_SwitchCandidateLowHPBlock:
; Returns carry (= block voluntary switch) when the proposed switch candidate
; in wEnemySwitchMonParam (low nibble = 0-based party idx) is at <= quarter HP
; AND lacks any type immunity vs the active player mon's types. The immunity
; exception preserves the Gen-2 "absorb a STAB hit with an immune mon" pivot
; per gameplay-lead intent.
;
; Reads: wEnemySwitchMonParam, wOTPartyMon1HP[N], wOTPartyMon1Species[N],
;        wBattleMonType1, wBattleMonType2
; Writes: wCurSpecies (saved/restored), wCurBaseData (saved/restored),
;         wBossAITemp4..5 (scratch for candidate type pair), wTypeMatchup
	ld a, [wEnemySwitchMonParam]
	and $f
	ld b, a
	push bc
	push de
	ld hl, wOTPartyMon1HP
	ld a, b
	call GetPartyLocation
	ld a, [hli]
	ld d, a
	ld a, [hl]
	ld e, a
	sla e
	rl d
	sla e
	rl d
	inc hl
	ld a, [hli]
	cp d
	jr c, .above_quarter
	jr nz, .at_quarter
	ld a, [hl]
	cp e
	jr c, .above_quarter
.at_quarter
	pop de
	pop bc
	call BossAI_CandidateImmuneToPlayerSTAB
	jr c, .has_immunity
	scf
	ret
.above_quarter
	pop de
	pop bc
.has_immunity
	and a
	ret

; ai-layer: POLICY
BossAI_CandidateImmuneToPlayerSTAB:
; Returns carry if the candidate (wEnemySwitchMonParam low nibble) has at
; least one type immunity (NO_EFFECT) vs either of the active player mon's
; types. Used by BossAI_SwitchCandidateLowHPBlock to permit a dying mon to
; switch in if it can absorb a STAB hit at 0x.
	push bc
	push de
	push hl
	ld a, [wEnemySwitchMonParam]
	and $f
	ld c, a
	ld hl, wOTPartyMon1Species
	ld a, c
	call GetPartyLocation
	ld a, [hl]
	ld c, a
	ld a, [wCurSpecies]
	push af
	ld a, c
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wCurBaseData + BASE_TYPE_1]
	ld d, a
	ld a, [wCurBaseData + BASE_TYPE_2]
	ld e, a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ld a, d
	ld [wBossAITemp4], a
	ld a, e
	ld [wBossAITemp5], a
	ld a, [wBattleMonType1]
	ld hl, wBossAITemp4
	call BossAI_CheckTypeMatchupNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .immune_yes
	ld a, [wBattleMonType1]
	ld c, a
	ld a, [wBattleMonType2]
	cp c
	jr z, .immune_no
	ld hl, wBossAITemp4
	call BossAI_CheckTypeMatchupNoItem
	ld a, [wTypeMatchup]
	and a
	jr z, .immune_yes
.immune_no
	pop hl
	pop de
	pop bc
	and a
	ret
.immune_yes
	pop hl
	pop de
	pop bc
	scf
	ret

; ai-layer: POLICY
BossAI_ShouldSackHard:
; LATE-tier categorical sack rule. Returns carry (= abort voluntary switch)
; when the active mon is in a "let it die in field" state per gameplay-lead
; intent: dying mons should spend their last turn productively instead of
; giving the player a free hit on the next mon. Two stay-and-don't-sack
; exceptions: fast frail mons (base speed >= 105) can outspeed and contribute
; a last action after a switch, so keeping them in to act before dying loses
; value; asleep mons should be switched out so the sleep-clause "slot" stays
; banked instead of being burned by an in-field KO.
;
; Conditions (all must hold for sack):
;   - wBossAITier == AI_TIER_LATE
;   - active HP <= quarter max
;   - active is NOT the boss's wincon mon
;   - active is NOT asleep
;   - active species base Speed < 105
	ld a, [wBossAITier]
	cp AI_TIER_LATE
	jr c, .no
	call AICheckEnemyQuarterHP_HL
	jr c, .no
	ld a, [wCurOTMon]
	inc a
	ld b, a
	ld a, [wBossAIWinconMonIdx]
	cp b
	jr z, .no
	ld a, [wEnemyMonStatus]
	and SLP_MASK
	jr nz, .no
	ld a, [wCurSpecies]
	push af
	ld a, [wEnemyMonSpecies]
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wCurBaseData + BASE_SPD]
	ld b, a
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ld a, b
	cp 105
	jr nc, .no
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

INCLUDE "data/boss_ai/role_package_classifier.asm"

endc
