DEF MOVE_REMINDER_MAX_MOVES EQU 30
DEF MOVE_REMINDER_PAGE_SIZE EQU 3
DEF MOVE_REMINDER_MENU_NEXT EQU $ff
DEF MOVE_REMINDER_MENU_CANCEL EQU $fe

MoveReminder:
	ld hl, .IntroText
	call PrintText
	call YesNoBox
	jr c, .declined

	ld hl, .AskMonText
	call PrintText
	farcall SelectMonFromParty
	jr c, .declined

	ld a, [wCurPartySpecies]
	cp EGG
	jr z, .egg

	call .BuildMoveList
	ld hl, wSwitchMonBuffer
	ld a, [hl]
	and a
	jr z, .no_moves

	ld hl, .AskMoveText
	call PrintText
	call .ChooseMoveFromList
	jr nc, .declined

	ld [wPutativeTMHMMove], a
	ld [wNamedObjectIndex], a
	call GetMoveName
	call CopyName1
	predef LearnMove
	ret

.egg
	ld hl, .EggText
	call PrintText
	ret

.no_moves
	ld hl, .NoMovesText
	call PrintText
	ret

.declined
	ld hl, .DeclinedText
	call PrintText
	ret

.BuildMoveList
	xor a
	ld hl, wSwitchMonBuffer
	ld [hl], a

	ld a, [wCurPartyMon]
	ld hl, wPartyMon1Level
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld a, [hl]
	ld [wCurPartyLevel], a

	ld a, [wCurPartySpecies]
	push af

.species_loop
	call .AddSpeciesMovesUpToLevel
	callfar GetPreEvolution
	jr c, .species_loop

	pop af
	ld [wCurPartySpecies], a
	ret

.AddSpeciesMovesUpToLevel
; input: wCurPartySpecies
	ld a, [wCurPartySpecies]
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord

.skip_evos
	call .ReadEvoByteInc
	and a
	jr nz, .skip_evos

.next_move
	call .ReadEvoByteInc
	and a
	ret z
	ld b, a
	ld a, [wCurPartyLevel]
	cp b
	jr c, .skip_move

	call .ReadEvoByteInc
	push hl
	call .TryAddReminderMove
	pop hl
	jr .next_move

.skip_move
	inc hl
	jr .next_move

.ReadEvoByteInc
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	inc hl
	ret

.TryAddReminderMove
; input: a = move id
	and a
	ret z
	push af
	call .PartyMonAlreadyKnowsMove
	pop af
	ret c
	push af
	call .ReminderListAlreadyHasMove
	pop af
	ret c

	ld d, a
	ld hl, wSwitchMonBuffer
	ld a, [hl]
	cp MOVE_REMINDER_MAX_MOVES
	ret nc
	ld c, a
	ld b, 0
	inc hl
	add hl, bc
	ld [hl], d
	ld hl, wSwitchMonBuffer
	inc [hl]
	ret

.PartyMonAlreadyKnowsMove
; input: a = move id
; output: carry if known
	ld d, a
	ld a, [wCurPartyMon]
	ld hl, wPartyMon1Moves
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld b, NUM_MOVES

.known_loop
	ld a, [hli]
	cp d
	jr z, .yes
	dec b
	jr nz, .known_loop
	and a
	ret

.yes
	scf
	ret

.ReminderListAlreadyHasMove
; input: a = move id
; output: carry if already listed
	ld d, a
	ld hl, wSwitchMonBuffer
	ld b, [hl]
	inc hl

.dup_loop
	ld a, b
	and a
	jr z, .no
	ld a, [hli]
	cp d
	jr z, .yes_dup
	dec b
	jr .dup_loop

.no
	and a
	ret

.yes_dup
	scf
	ret

.ChooseMoveFromList
	xor a
	ld [wMenuCursorPosition], a

.page_loop
	call .BuildReminderPageMenuData
	ld hl, .MoveMenuHeader
	call LoadMenuHeader
	call VerticalMenu
	push af
	call CloseWindow
	pop af
	jr c, .cancel

	ld a, [wMenuCursorY]
	dec a
	ld c, a
	ld b, 0
	ld hl, wMenuItemsList
	add hl, bc
	ld a, [hl]
	cp MOVE_REMINDER_MENU_NEXT
	jr z, .next_page
	cp MOVE_REMINDER_MENU_CANCEL
	jr z, .cancel

	ld c, a
	ld b, 0
	ld hl, wSwitchMonBuffer + 1
	add hl, bc
	ld a, [hl]
	scf
	ret

.next_page
	ld a, [wMenuCursorPosition]
	add MOVE_REMINDER_PAGE_SIZE
	ld [wMenuCursorPosition], a
	jr .page_loop

.cancel
	and a
	ret

.BuildReminderPageMenuData
	ld hl, wStringBuffer2
	ld a, STATICMENU_CURSOR | STATICMENU_NO_TOP_SPACING
	ld [hli], a
	xor a
	ld [hli], a ; count (filled later)
	ld [wMenuSelectionQuantity], a

; clamp page start
	ld a, [wSwitchMonBuffer]
	ld d, a
	ld a, [wMenuCursorPosition]
	cp d
	jr c, .start_ok
	xor a
	ld [wMenuCursorPosition], a
.start_ok

	ld a, d
	ld e, a ; total
	ld a, [wMenuCursorPosition]
	ld d, a ; start index
	ld a, e
	sub d
	ld b, a ; remaining
	ld a, b
	cp MOVE_REMINDER_PAGE_SIZE
	jr c, .got_page_count
	ld a, MOVE_REMINDER_PAGE_SIZE
.got_page_count
	ld b, a ; moves this page

	ld de, wMenuItemsList
	ld c, d ; current global move index

.move_loop
	ld a, b
	and a
	jr z, .after_moves

	ld a, c
	ld [de], a
	inc de
	ld a, [wMenuSelectionQuantity]
	inc a
	ld [wMenuSelectionQuantity], a

	push bc
	push de
	push hl
	ld b, 0
	ld hl, wSwitchMonBuffer + 1
	add hl, bc
	ld a, [hl]
	ld [wNamedObjectIndex], a
	call GetMoveName
	pop hl
	pop de
	pop bc

	push bc
	push de
	ld de, wStringBuffer1
	call .AppendMenuString
	pop de
	pop bc

	inc c
	dec b
	jr .move_loop

.after_moves
	ld a, c
	cp e
	jr nc, .append_cancel

	ld a, MOVE_REMINDER_MENU_NEXT
	ld [de], a
	inc de
	ld a, [wMenuSelectionQuantity]
	inc a
	ld [wMenuSelectionQuantity], a
	push de
	ld de, .NextText
	call .AppendMenuString
	pop de

.append_cancel
	ld a, MOVE_REMINDER_MENU_CANCEL
	ld [de], a
	inc de
	ld a, [wMenuSelectionQuantity]
	inc a
	ld [wMenuSelectionQuantity], a
	push de
	ld de, .CancelText
	call .AppendMenuString
	pop de

	ld a, [wMenuSelectionQuantity]
	ld [wStringBuffer2 + 1], a
	ret

.AppendMenuString
.copy
	ld a, [de]
	inc de
	ld [hli], a
	cp '@'
	jr nz, .copy
	ret

.MoveMenuHeader:
	db MENU_BACKUP_TILES ; flags
	menu_coords 1, 1, 18, 13
	dw wStringBuffer2
	db 1 ; default option

.NextText:
	db "NEXT@"

.CancelText:
	db "CANCEL@"

.IntroText:
	text "I can help your"
	line "#MON remember"
	cont "moves for free."

	para "Want me to help?"
	done

.AskMonText:
	text "Which #MON needs"
	line "a memory jog?"
	done

.AskMoveText:
	text "Which move should"
	line "it remember?"
	done

.NoMovesText:
	text "There are no moves"
	line "to remember right"
	cont "now."
	done

.EggText:
	text "An EGG won't"
	line "remember moves."
	done

.DeclinedText:
	text "All right."
	line "Come back anytime."
	done
