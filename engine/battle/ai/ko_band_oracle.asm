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

INCLUDE "data/boss_ai/matchup_tables.asm"

endc
