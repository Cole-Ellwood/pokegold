; ============================================================
; engine/battle/ai/boss_platform.asm - Boss AI platform-owned guarded fragments
; Split out of boss.asm per docs/boss_ai_organization_plan.md section 3.
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; Included with BOSSAI_EMIT_* guards from main.asm to preserve ROM byte order.
; ============================================================

IF !DEF(BOSSAI_HAKI_SPENT_F)
DEF BOSSAI_HAKI_SPENT_F EQU 0
DEF BOSSAI_HAKI_ACE_SEEN_F EQU 1
DEF BOSSAI_HAKI_ELIGIBLE_F EQU 2
DEF BOSSAI_HAKI_TRACE_FIRED_F EQU 3
ENDC

if DEF(BOSSAI_EMIT_PLATFORM_STATE_TRACKING)
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
	call BossAI_UpdateHakiAceWindow
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
BossAI_UpdateHakiAceWindow:
; Byte 1 of wBossAIRevealedMovesBitmapSpare stores quarantined Haki bits.
; Morty's Gengar prototype only: mark a one-turn window when the ace first
; starts a battle turn active, so player switch/item turns cannot defer Haki.
	ld hl, wBossAIRevealedMovesBitmapSpare + 1
	res BOSSAI_HAKI_ELIGIBLE_F, [hl]
	bit BOSSAI_HAKI_SPENT_F, [hl]
	ret nz
	bit BOSSAI_HAKI_ACE_SEEN_F, [hl]
	ret nz
	ld a, [wTrainerClass]
	cp MORTY
	ret nz
	ld a, [wOtherTrainerID]
	cp MORTY1
	ret nz
	ld a, [wEnemyMonSpecies]
	cp GENGAR
	ret nz
	set BOSSAI_HAKI_ACE_SEEN_F, [hl]
	set BOSSAI_HAKI_ELIGIBLE_F, [hl]
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_PUBLIC_INFO)
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
	push hl
	ld a, b
	call BossAI_MoveTaintsFourMoveReveal
	pop hl
	jr nc, .reveal_not_tainted
	push hl
	push bc
	call BossAI_TaintActiveSpeciesReveal
	pop bc
	pop hl

.reveal_not_tainted
	ld a, b
	call BossAI_AddRevealedMoveToSpeciesMask
	call BossAI_MirrorPlayerUsedMovesToSpeciesSlot
	xor a
	ld [wBossAIPlausibleTypeMaskSpecies], a
	ld [wBossAIPlausibleTypeMaskLevel], a
	ret

; ai-layer: PLATFORM
BossAI_MoveTaintsFourMoveReveal:
; Returns carry if move a can reveal copied/temporary moves, making the active
; species unsafe for four-revealed-move plausible-mask saturation this battle.
	and a
	jr z, .no
	cp STRUGGLE
	jr z, .yes
	dec a
	ld hl, Moves + MOVE_EFFECT
	call BossAI_GetMoveAttr
	cp EFFECT_MIRROR_MOVE
	jr z, .yes
	cp EFFECT_TRANSFORM
	jr z, .yes
	cp EFFECT_MIMIC
	jr z, .yes
	cp EFFECT_METRONOME
	jr z, .yes
	cp EFFECT_SKETCH
	jr z, .yes
	cp EFFECT_SLEEP_TALK
	jr z, .yes
.no
	and a
	ret
.yes
	scf
	ret

; ai-layer: PLATFORM
BossAI_TaintActiveSpeciesReveal:
	call BossAI_GetActiveSpeciesSeenIndex
	and a
	ret z
	dec a
	ld c, a
	call BossAI_SeenPlayerSpeciesBitFromC
	ld hl, wBossAIRevealedMovesBitmapSpare
	or [hl]
	ld [hl], a
	ret

; ai-layer: PLATFORM
BossAI_ActiveSpeciesRevealTainted:
	call BossAI_GetActiveSpeciesSeenIndex
	and a
	jr z, .no
	dec a
	ld c, a
	call BossAI_SeenPlayerSpeciesBitFromC
	ld hl, wBossAIRevealedMovesBitmapSpare
	and [hl]
	jr z, .no
	scf
	ret
.no
	and a
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_TURN_CACHE_RESET)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_TYPE_MATCHUP_NO_ITEM)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_MOVE_CATEGORY_WRAPPER)
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
endc
if DEF(BOSSAI_EMIT_PLATFORM_DARK_SHIELD_AND_TYPES)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_PASSIVE_CACHES)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_HELD_ITEM_HELPERS)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_SEEN_SPECIES_INDEX)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_CLEAR_PLAUSIBLE_MASK)
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

; ai-layer: PLATFORM
endc

if DEF(BOSSAI_EMIT_PLATFORM_MASK_SET_BITS)
BossAI_SetPlausibleAndLikelyMaskBit:
	push af
	call BossAI_SetPlausibleMaskBit
	pop af
	call BossAI_SetLikelyMaskBit
	ret

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
endc

if DEF(BOSSAI_EMIT_PLATFORM_MASK_TEST_BITS)
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

; ai-layer: PLATFORM
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
endc

if DEF(BOSSAI_EMIT_PLATFORM_SCORE_IO)
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

endc

if DEF(BOSSAI_EMIT_PLATFORM_SCOUTED_BITMAP_IO)
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
endc

if DEF(BOSSAI_EMIT_PLATFORM_REPEAT_TRACKER)
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
endc

if DEF(BOSSAI_EMIT_PLATFORM_NO_CHEAT_TABLES)
; ============================================================
; Region: Static data tables
; Concern: Plausible threats, tier weights, status/role/risky effect tables
; Layer: PLATFORM
; Original lines: 139
; ============================================================
; ai-layer: PLATFORM
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

; ai-layer: PLATFORM
BossAIHiddenPowerThreatTypes:
	db GROUND
	db ICE
	db GRASS
	db ELECTRIC
	db -1

; BossAI_TraceTopMoves moved to engine/battle/ai/boss_trace_topmoves.asm
; (own SECTION) so the trace build doesn't push the "Enemy Trainers" bank
; over its 16 KB ceiling. Caller below uses farcall.

; ai-layer: PLATFORM
endc
