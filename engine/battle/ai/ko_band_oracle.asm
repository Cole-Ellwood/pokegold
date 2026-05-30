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
	; Save current move's matchup to wBossAITemp5 BEFORE any rank computation
	; runs. `.MoveIdMatchupSTABRank` (called in the loop) farcalls the
	; matchup helper, which overwrites wTypeMatchup. The "coverage trumps
	; STAB" rule below needs the original to compare both moves' SE-ness.
	ld a, [wTypeMatchup]
	ld [wBossAITemp5], a
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
	; Tier-aware dominance. The +32 rank buffer is tolerance between moves of
	; the SAME effectiveness tier; it must not shelter a move from a strictly
	; better-tier alternative. At equal base power a neutral STAB move and a
	; resisted STAB move rank close enough to tie inside the buffer (the Falkner
	; Pidgeotto Tackle-vs-Gust coin flip), so when the comparison move lands a
	; strictly better matchup tier than the current move, drop the buffer and
	; dominate on real (rich-model) rank alone. Tier only selects the comparison
	; method; the comparison itself is on damage rank, so a strong resisted move
	; still survives a weak neutral one.
	ld a, [wBossAITemp5]      ; current move's matchup tier
	ld e, a
	ld a, [wTypeMatchup]      ; comparison move's matchup tier
	cp e
	jr c, .standard_buffer    ; comparison worse tier -> buffered tolerance
	jr z, .standard_buffer    ; same tier -> buffered tolerance
	; comparison is a strictly better tier -> strict-less rank dominance (equal
	; rank does not dominate, so two equal-rank moves don't discourage each
	; other).
	ld a, [wBossAITemp2]
	cp d
	jr c, .dominated
	jr .next
.standard_buffer
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
	; Rich-model damage rank for the current move: stat-ratio scored power (base
	; offense/defense on the move's category axis) then type matchup then STAB.
	; BossAI_ScaleMovePowerByBaseStatRatio lives in bank 0x0e (reach it by
	; farcall) and derives the category from wEnemyMoveStruct + MOVE_TYPE, which
	; already holds the current move's type. It stashes its result in wBossAITemp
	; and clobbers a/bc/de/hl, so we read wBossAITemp — the farcall a-return is
	; the target's exit c, not a (asm guide 3.3). The current move's matchup is
	; the pre-loop cache in wBossAITemp5, taken before any farcall could
	; overwrite wTypeMatchup.
	ld a, [wEnemyMoveStruct + MOVE_POWER]
	farcall BossAI_ScaleMovePowerByBaseStatRatio
	ld a, [wBossAITemp]
	ld b, a
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	ld c, a
	ld a, [wBossAITemp5]
	call .ScalePowerByMatchup
	jp .ApplySTABToRank      ; jp not jr: .MoveIdMatchupSTABRank below pushes the target out of jr range

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
	; Swap the comparison move's effect into the move struct so the shared
	; scorer (multi-hit EV, fixed-damage) reads THIS move's effect, not the
	; current move's. Saved current effect is restored alongside the type at
	; the end. Read by id now, while c still holds the move id — the type read
	; below overwrites c.
	ld a, [wEnemyMoveStruct + MOVE_EFFECT]
	push af                                ; [stack bottom] current move effect
	ld a, c
	dec a
	ld hl, Moves + MOVE_EFFECT
	push bc
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	pop bc
	ld [wEnemyMoveStruct + MOVE_EFFECT], a  ; comparison effect into the struct
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
	; Rank the comparison move the same way .CurrentMoveDamageRank ranks the
	; current move: stat-ratio scored power then type matchup then STAB.
	; Cross-bank note: this file lives in bank 0x11, but the boss-AI matchup and
	; scoring helpers live in bank 0x0e. A plain `call BossAI_CheckTypeMatchupNoItem`
	; jumped into the BossAIMatchupTables data table (broke the first 2026-05-25
	; build), so both bank-0x0e helpers are reached by farcall. We swap the
	; comparison move's type into wEnemyMoveStruct + MOVE_TYPE so BOTH the matchup
	; helper AND the stat-ratio category derivation (which read MOVE_TYPE) see the
	; comparison move, then restore the current move's type. BossAI_ScaleMovePower-
	; ByBaseStatRatio stashes its result in wBossAITemp (the farcall a-return is the
	; target's exit c, not a) and preserves wTypeMatchup, so the comparison matchup
	; survives for the matchup scaling below and for the loop's tier check.
	ld a, [wEnemyMoveStruct + MOVE_TYPE]
	push af                                ; current move type (restored last)
	ld a, c
	ld [wEnemyMoveStruct + MOVE_TYPE], a   ; comparison type into the move struct
	push bc                                ; preserve raw power (b) + type (c)
	farcall BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItemUncached
	pop bc
	push bc
	ld a, b                                ; raw comparison power
	farcall BossAI_ScaleMovePowerByBaseStatRatio
	pop bc                                 ; b = raw power, c = comparison type
	pop af
	ld [wEnemyMoveStruct + MOVE_TYPE], a   ; restore current move type
	pop af
	ld [wEnemyMoveStruct + MOVE_EFFECT], a ; restore current move effect
	ld a, [wBossAITemp]
	ld b, a                                ; b = stat-scaled comparison power
	ld a, [wTypeMatchup]                   ; comparison matchup (preserved)
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
