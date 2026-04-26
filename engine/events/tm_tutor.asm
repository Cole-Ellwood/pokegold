TMTutorTeachAnyTM:
; Output wScriptVar:
; 0 = canceled, 1 = taught successfully, 2 = attempted but no move learned.
	ld hl, wTMsHMs
	ld de, wTMTutorTMHMBackup
	ld bc, NUM_TMS + NUM_HMS
	call CopyBytes

	ld hl, wTMsHMs
	ld b, NUM_TMS + NUM_HMS
	ld a, 1
.fill_tms
	ld [hli], a
	dec b
	jr nz, .fill_tms

	xor a
	ld [wTMHMPocketScrollPosition], a
	ld [wTMHMPocketCursor], a
	farcall TMHMPocket

	push af
	ld hl, wTMTutorTMHMBackup
	ld de, wTMsHMs
	ld bc, NUM_TMS + NUM_HMS
	call CopyBytes
	pop af

	jr c, .tm_selected
	xor a
	ld [wScriptVar], a
	ret

.tm_selected
	ld a, [wCurItem]
	ld c, a
	callfar GetTMHMNumber
	ld a, c
	ld [wTempTMHM], a
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld [wPutativeTMHMMove], a
	call GetMoveName
	call CopyName1

	farcall ChooseMonToLearnTMHM
	jr c, .canceled

	ld a, [wCurItem]
	push af
	ld a, NO_ITEM
	ld [wCurItem], a
	farcall TeachTMHM
	jr c, .taught_restore_cur_item

	pop af
	ld [wCurItem], a
	ld a, 2
	ld [wScriptVar], a
	ret

.taught_restore_cur_item
	pop af
	ld [wCurItem], a
.taught
	ld a, 1
	ld [wScriptVar], a
	ret

.canceled
	xor a
	ld [wScriptVar], a
	ret
