; ============================================================
; engine/battle/ai/ko_band_oracle.asm - Boss AI KO-band helpers
; P2b consumer for data/boss_ai/matchup_tables.asm.
; Included with BOSSAI_EMIT_* guards from main.asm.
; ============================================================

if DEF(BOSSAI_EMIT_KO_BAND_ORACLE)

SECTION "Boss AI KO Oracle", ROMX

DEF BOSS_AI_MATCHUP_NUM_TYPES EQU 17
DEF BOSS_AI_MATCHUP_SLOT_BYTES EQU 1 + BOSS_AI_MATCHUP_NUM_TYPES + BOSS_AI_MATCHUP_NUM_TYPES
DEF BOSS_AI_MATCHUP_OFFENSIVE_OFFSET EQU 1 + BOSS_AI_MATCHUP_NUM_TYPES

; ai-layer: POLICY
BossAI_ApplyKOBandOraclePressure::
; Input: b = current exact pressure score; wTypeMatchup = exact current-move
; type matchup against the player's active mon.
; Output: b possibly +1 when the current move is super-effective and the
; P2a per-slot table confirms this enemy slot has public SE coverage against
; the player's active typing. This avoids giving one move credit for another
; move's coverage while still making confirmed KO-pressure lines sharper.
	ld a, [wBossAITier]
	cp AI_TIER_MID
	ret c
	ld a, [wTypeMatchup]
	cp EFFECTIVE * 2
	ret c
	push bc
	call BossAI_CurrentSlotOffensiveCoverageVsPlayer
	pop bc
	ret nc
	cp EFFECTIVE * 2
	ret c
	inc b
	ret

; ai-layer: POLICY
BossAI_CurrentSlotOffensiveCoverageVsPlayer:
; Output: carry if the P2a table has the active enemy slot; a = best coverage
; multiplier among the player's active type(s), using the slot's offensive
; vector (best of the slot's known four moves vs each defender type).
	ld a, [wBattleMonType1]
	call BossAI_CurrentSlotOffensiveCoverageVsType
	ret nc
	push af
	ld a, [wBattleMonType2]
	call BossAI_CurrentSlotOffensiveCoverageVsType
	jr nc, .use_first
	ld c, a
	pop af
	cp c
	jr nc, .done
	ld a, c
	scf
	ret

.use_first
	pop af
.done
	scf
	ret

; ai-layer: POLICY
BossAI_CurrentSlotOffensiveCoverageVsType:
; Input: a = raw type constant. Output: carry if lookup succeeds; a =
; multiplier byte from the current enemy slot's offensive vector.
	call BossAI_CanonicalTypeIndex
	ret nc
	add BOSS_AI_MATCHUP_OFFENSIVE_OFFSET
	push af
	call BossAI_GetCurrentEnemyMatchupSlot
	jr nc, .no_pop
	pop af
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]
	scf
	ret

.no_pop
	pop af
	and a
	ret

; ai-layer: POLICY
BossAI_GetCurrentEnemyMatchupSlot:
; Output: carry if found; hl = slot block for wTrainerClass/wOtherTrainerID
; and current wCurOTMon. Slot block layout: species, 17 defensive, 17 offensive.
	ld a, [wTrainerClass]
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a
	ld hl, BossAIMatchupTables

.row_loop
	ld a, [hli]
	and a
	jr z, .not_found
	cp b
	jr z, .class_match
	inc hl ; trainer id
	ld a, [hli] ; party count
	push bc
	call .SkipSlotsA
	pop bc
	jr .row_loop

.class_match
	ld a, [hli]
	cp c
	jr z, .matched
	ld a, [hli] ; party count
	push bc
	call .SkipSlotsA
	pop bc
	jr .row_loop

.matched
	ld a, [hli] ; party count
	ld b, a
	ld a, [wCurOTMon]
	cp b
	jr nc, .not_found
	and a
	jr z, .found
	ld b, a
.slot_loop
	ld de, BOSS_AI_MATCHUP_SLOT_BYTES
	add hl, de
	dec b
	jr nz, .slot_loop

.found
	scf
	ret

.not_found
	and a
	ret

.SkipSlotsA
	and a
	ret z
	ld b, a
.skip_loop
	ld de, BOSS_AI_MATCHUP_SLOT_BYTES
	add hl, de
	dec b
	jr nz, .skip_loop
	ret

; ai-layer: POLICY
BossAI_CanonicalTypeIndex:
; Input: a = raw type constant. Output: carry if in the 17-type P2a vector
; order; a = vector index 0..16. BIRD/unused types return nc.
	ld c, a
	ld hl, BossAIOracleCanonicalTypeOrder
	ld b, 0
.loop
	ld a, [hli]
	cp -1
	jr z, .no
	cp c
	jr z, .yes
	inc b
	jr .loop

.yes
	ld a, b
	scf
	ret

.no
	and a
	ret

BossAIOracleCanonicalTypeOrder:
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

; ai-layer: POLICY
BossAI_ApplyDamageDominanceBias::
	push bc
	push de
	push hl
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	and a
	jr z, .ret_regs
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	ld c, a
	call .CurrentMoveDamageRank
	and a
	jr z, .ret_regs
	ld [wBossAITemp2], a
	ld a, [wEnemyMoveStruct + MOVE_ANIM]
	ld [wBossAITemp3], a
	ld hl, wEnemyMonMoves
	ld b, NUM_MOVES

.loop
	ld a, [hli]
	and a
	jr z, .done
	ld c, a
	push hl
	push bc
	ld a, [wBossAITemp3]
	cp c
	jr z, .next
	call .MoveIdMatchupSTABRank
	ld d, a
	ld a, [wBossAITemp2]
	add 32
	jr c, .next
	cp d
	jr z, .dominated
	jr c, .dominated

.next
	pop bc
	pop hl
	dec b
	jr nz, .loop

.done
	jr .ret_regs

.ret_regs
	pop hl
	pop de
	pop bc
	ret

.dominated
	pop bc
	pop hl
	call .DiscourageCurrentScoreBy8
	jr .ret_regs

.CurrentMoveDamageRank
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld c, a
	ld a, [wTypeMatchup]
	call .ScalePowerByMatchup
	jr .ApplySTABToRank

.MoveIdMatchupSTABRank
	ld a, c
	and a
	ret z
	dec a
	ld hl, Moves + MOVE_POWER
	push bc
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	pop bc
	and a
	ret z
	ld b, a
	ld a, c
	dec a
	ld hl, Moves + MOVE_TYPE
	push bc
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	pop bc
	ld c, a
	; Scale by type matchup vs the active player defender so the comparison
	; ranks the same way .CurrentMoveDamageRank does for the current move.
	; Cross-bank note: this file lives in bank 0x11, but the boss-AI matchup
	; helpers live in bank 0x0e. A plain `call BossAI_CheckTypeMatchupNoItem`
	; jumped into the BossAIMatchupTables data table (broke the first 2026-05-25
	; build). The fix swaps the comparison move's type into
	; wEnemyMoveStruct + MOVE_TYPE and farcalls the *uncached* wrapper, which
	; reads MOVE_TYPE and sets hl internally, so the farcall hl-clobber is
	; harmless and the cached current-move matchup key/result are untouched.
	push bc
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	push af
	ld a, c
	ld [wEnemyMoveStruct + MOVE_TYPE], a
	farcall BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItemUncached
	pop af
	ld [wEnemyMoveStruct + MOVE_TYPE], a
	pop bc
	ld a, [wTypeMatchup]
	call .ScalePowerByMatchup
	jr .ApplySTABToRank

.ScalePowerByMatchup
	and a
	ret z
	cp EFFECTIVE
	jr c, .resisted
	cp SUPER_EFFECTIVE
	jr c, .after_type
	cp SUPER_EFFECTIVE * 2
	jr nc, .quad_effective
	ld a, b
	call .Double
	jr .store_type

.quad_effective
	ld a, b
	call .Double
	call .Double
	jr .store_type

.resisted
	ld a, b
	srl a
	jr .store_type

.after_type
	ld a, b

.store_type
	ret

.ApplySTABToRank
	ld [wBossAITemp4], a
	ld a, [wEnemyMonType1]
	cp c
	jr z, .stab
	ld a, [wEnemyMonType2]
	cp c
	jr nz, .rank_done

.stab
	ld a, [wBossAITemp4]
	call .AddHalf
	ld [wBossAITemp4], a

.rank_done
	ld a, [wBossAITemp4]
	ret

.Double
	add a
	ret nc
	ld a, $ff
	ret

.AddHalf
	ld d, a
	srl d
	add d
	ret nc
	ld a, $ff
	ret

.DiscourageCurrentScoreBy8
	ld a, [wBossAIScorePtr]
	ld h, a
	ld a, [wBossAIScorePtr + 1]
	ld l, a
	ld b, 8
.discourage_loop
	ld a, [hl]
	cp 79
	jr nc, .discourage_next
	inc [hl]
.discourage_next
	dec b
	jr nz, .discourage_loop
	ret

INCLUDE "data/boss_ai/matchup_tables.asm"

endc
