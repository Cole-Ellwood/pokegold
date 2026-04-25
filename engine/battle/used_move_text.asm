BattleCommand_UsedMoveText:
	ld hl, UsedMoveText
	call PrintText
	jp WaitBGMap

UsedMoveText:
	text_far _ActorNameText
	text_asm

	ldh a, [hBattleTurn]
	and a
	jr nz, .start

	ld a, [wPlayerMoveStruct + MOVE_ANIM]
	call UpdateUsedMoves
	callfar BossAI_RecordRevealedPlayerMove

.start
	ld a, BATTLE_VARS_LAST_MOVE
	call GetBattleVarAddr
	ld d, h
	ld e, l

	ld a, BATTLE_VARS_LAST_COUNTER_MOVE
	call GetBattleVarAddr

	ld a, BATTLE_VARS_MOVE_ANIM
	call GetBattleVar
	ld [wMoveGrammar], a

	call CheckUserIsCharging
	jr nz, .grammar

	; update last move
	ld a, [wMoveGrammar]
	ld [hl], a
	ld [de], a
	call UpdateMetronomeTracker

.grammar
	call GetMoveGrammar ; convert move id to grammar index

; everything except 'CheckObedience' made redundant in localization

	; check obedience
	ld a, [wAlreadyDisobeyed]
	and a
	ld hl, UsedMove2Text
	ret nz

	; check move grammar
	ld a, [wMoveGrammar]
	cp $3
	ld hl, UsedMove2Text
	ret c
	ld hl, UsedMove1Text
	ret

UsedMove1Text:
	text_far _UsedMove1Text
	text_asm
	jr UsedMoveText_CheckObedience

UsedMove2Text:
	text_far _UsedMove2Text
	text_asm
UsedMoveText_CheckObedience:
; check obedience
	ld a, [wAlreadyDisobeyed]
	and a
	jr z, .GetMoveNameText
; print "instead,"
	ld hl, .UsedInsteadText
	ret

.UsedInsteadText:
	text_far _UsedInsteadText
	text_asm
.GetMoveNameText:
	ld hl, MoveNameText
	ret

MoveNameText:
	text_far _MoveNameText
	text_asm
; get start address
	ld hl, .endusedmovetexts

; get move id
	ld a, [wMoveGrammar]

; 2-byte pointer
	add a

; seek
	push bc
	ld b, 0
	ld c, a
	add hl, bc
	pop bc

; get pointer to usedmovetext ender
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

.endusedmovetexts
; entries correspond to MoveGrammar sets
	dw EndUsedMove1Text
	dw EndUsedMove2Text
	dw EndUsedMove3Text
	dw EndUsedMove4Text
	dw EndUsedMove5Text

EndUsedMove1Text:
	text_far _EndUsedMove1Text
	text_end

EndUsedMove2Text:
	text_far _EndUsedMove2Text
	text_end

EndUsedMove3Text:
	text_far _EndUsedMove3Text
	text_end

EndUsedMove4Text:
	text_far _EndUsedMove4Text
	text_end

EndUsedMove5Text:
	text_far _EndUsedMove5Text
	text_end

GetMoveGrammar:
; store move grammar type in wMoveGrammar

	push bc
; wMoveGrammar contains move id
	ld a, [wMoveGrammar]
	ld c, a ; move id
	ld b, 0 ; grammar index

; read grammar table
	ld hl, MoveGrammar
.loop
	ld a, [hli]
; end of table?
	cp -1
	jr z, .end
; match?
	cp c
	jr z, .end
; advance grammar type at 0
	and a
	jr nz, .loop
; next grammar type
	inc b
	jr .loop

.end
; wMoveGrammar now contains move grammar
	ld a, b
	ld [wMoveGrammar], a

; we're done
	pop bc
	ret

UpdateMetronomeTracker:
	push hl
	push de
	push bc
	call GetUserItem
	ld a, b
	cp HELD_METRONOME
	jr z, .holding_item
	call .Clear
	jr .done

.holding_item
	ld a, [wMoveGrammar]
	ld b, a
	call .IsDamagingMove
	jr c, .clear_and_done
	call .GetTrackerPointers
	ld a, [hl]
	cp b
	jr nz, .new_move
	ld a, [de]
	inc a
	ld [de], a
	jr .done

.new_move
	ld a, b
	ld [hl], a
	xor a
	ld [de], a
	jr .done

.clear_and_done
	call .Clear

.done
	pop bc
	pop de
	pop hl
	ret

.Clear
	call .GetTrackerPointers
	xor a
	ld [hl], a
	ld [de], a
	ret

.GetTrackerPointers
	ld hl, wPlayerMetronomeMove
	ld de, wPlayerMetronomeCount
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyMetronomeMove
	ld de, wEnemyMetronomeCount
	ret

.IsDamagingMove
; input b = move id
; carry set if status/non-damaging
	ld a, b
	cp SEISMIC_TOSS
	jr z, .damaging
	cp NIGHT_SHADE
	jr z, .damaging
	cp DRAGON_RAGE
	jr z, .damaging
	cp SONICBOOM
	jr z, .damaging
	cp PSYWAVE
	jr z, .damaging
	cp COUNTER
	jr z, .damaging
	cp BIDE
	jr z, .damaging
	dec a
	ld hl, Moves + MOVE_POWER
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	and a
	jr z, .blocked

.damaging
	and a
	ret

.blocked
	scf
	ret

INCLUDE "data/moves/grammar.asm"

CheckUserIsCharging:
	ldh a, [hBattleTurn]
	and a
	ld a, [wPlayerCharging] ; player
	jr z, .end
	ld a, [wEnemyCharging] ; enemy
.end
	and a
	ret

UpdateUsedMoves:
; append move a to wPlayerUsedMoves unless it has already been used

	push bc
; start of list
	ld hl, wPlayerUsedMoves
; get move id
	ld b, a
; next count
	ld c, NUM_MOVES

.loop
; get move from the list
	ld a, [hli]
; not used yet?
	and a
	jr z, .add
; already used?
	cp b
	jr z, .quit
; next byte
	dec c
	jr nz, .loop

; if the list is full and the move hasn't already been used
; shift the list back one byte, deleting the first move used
; this can occur with struggle or a new learned move
	ld hl, wPlayerUsedMoves + 1
; 1 = 2
	ld a, [hld]
	ld [hli], a
; 2 = 3
	inc hl
	ld a, [hld]
	ld [hli], a
; 3 = 4
	inc hl
	ld a, [hld]
	ld [hl], a
; 4 = new move
	ld a, b
	ld [wPlayerUsedMoves + 3], a
	jr .quit

.add
; go back to the byte we just inced from
	dec hl
; add the new move
	ld [hl], b

.quit
; list updated
	pop bc
	ret
