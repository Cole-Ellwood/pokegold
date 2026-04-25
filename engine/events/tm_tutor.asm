TMTutorTeachAnyTM:
; Output wScriptVar:
; 0 = canceled, 1 = taught successfully, 2 = attempted but no move learned.
	ld hl, wTMsHMs
	ld de, wTMTutorTMHMBackup
	ld bc, NUM_TMS + NUM_HMS
	call CopyBytes

	ld hl, wTMsHMs
	ld b, NUM_TMS
	ld a, 1
.fill_tms
	ld [hli], a
	dec b
	jr nz, .fill_tms

	xor a
	ld b, NUM_HMS
.fill_hms
	ld [hli], a
	dec b
	jr nz, .fill_hms

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
	ld b, a
	ld a, HM01
	ld [wCurItem], a
	farcall TeachTMHM
	ld a, b
	ld [wCurItem], a
	jr c, .taught

	ld a, 2
	ld [wScriptVar], a
	ret

.taught
	ld a, 1
	ld [wScriptVar], a
	ret

.canceled
	xor a
	ld [wScriptVar], a
	ret
