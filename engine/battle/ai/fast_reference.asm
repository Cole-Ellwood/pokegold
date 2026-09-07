; Full-numerator compatibility restart. This entry owns the OLD JC workspace;
; no native plans, producer bridge records, or FS control fields are live.
; It reuses the exhaustive per-candidate evaluator without legacy HP tables.
; The result reservation alone is live in SRAM while JC producers run.

BossAI_FastReferenceRestartFromC::
; Marshal decision kind across the real farcall into the direct ABI.
	ld a, c
	jp BossAI_ComparePublicActionsFastReferenceRestart

BossAI_ComparePublicActionsFastReferenceRestart::
; Same direct ABI as the proposed native entry: A=decision0/2, B=scan0..15,
; DE=472-byte context, SRAM closed on entry. Full records/status2 are exported
; via the common finalizer; DE/SP/BC/carry and closure follow that boundary.
; This is the slow compatibility adapter, not the two-second native selector.
	ld c, a
	push bc
	xor a
	call OpenSRAM
	farcall BossAI_FastClearResults
	pop bc
	ld a, b
	and $f0
	jr nz, .reject
	ld a, c
	cp AV_REPLACEMENT_ACTION
	jr z, .valid
	and a
	jr nz, .reject
.valid
	push bc
	ad_address JC_ACTIONS
	ld b, JC_CONTEXT_SIZE - JC_ACTIONS
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ad_address AV_PREPARED_DAMAGE
	ld [hl], a ; old fixed SRAM aliases must never become live
	pop bc
	ad_address JC_KIND
	ld [hl], c
	inc hl
	ld [hl], b
	push de
	ad_address JC_ACTIONS
	ld d, h
	ld e, l
	call BossAI_EnumeratePublicActionsFromC
	pop de
	push de
	ad_address JC_REPLIES
	ld d, h
	ld e, l
	call BossAI_BuildPublicReplySet
	pop de
	ad_address JC_SCAN
	bit 0, [hl]
	ld a, 0
	jr z, .start
	ld a, JC_NUM_ACTIONS - 1
.start
	ad_address JC_INDEX
	ld [hli], a
	ld [hl], JC_NUM_ACTIONS
.action
	call BossAI_ComparePublicActions.Candidate
	jr nc, .next
	call BossAI_ComparePublicActions.ValueCandidate
	call .CopyRecord
.next
	ad_address JC_LEFT
	dec [hl]
	jr z, .finished
	ad_address JC_SCAN
	bit 0, [hl]
	ad_address JC_INDEX
	jr nz, .previous
	inc [hl]
	jr .action
.previous
	dec [hl]
	jr .action
.reject
	ad_address FS_BACKEND
	ld [hl], $ff
	farcall BossAI_FastFinalizeResults
	ret
.finished
; JC lifetime ends here. Explicitly copied legal score records differ from
; the canonical $ffff invalid marker; build the mask before FS control writes.
	push de
	ld hl, FS_RESULTS + (JC_NUM_ACTIONS - 1) * FS_RECORD_SIZE + 7
	ld bc, 0
	ld d, JC_NUM_ACTIONS
.mask
	sla c
	rl b
	ld a, [hl]
	cp $ff
	jr z, .invalid
	set 0, c
.invalid
	ld a, l
	sub FS_RECORD_SIZE
	ld l, a
	ld a, h
	sbc 0
	ld h, a
	dec d
	jr nz, .mask
	pop de
	ad_address FS_LEGAL_MASK
	ld [hl], b
	inc hl
	ld [hl], c
	ad_address FS_BACKEND
	ld [hl], 2
	farcall BossAI_FastFinalizeResults
	ret
.CopyRecord
; The exhaustive mean leaves JC_TOTAL and JC_MASS intact. Copy all seven
; bytes before another candidate clears them; never reconstruct T from score.
	push bc
	ad_address JC_UNCERTAIN
	ld a, [hl]
	push af
	push de
	ad_address JC_INDEX
	ld a, [hl]
	add a
	ld c, a
	add a
	add a
	add c
	ld c, a
	ld b, 0
	ld hl, FS_RESULTS
	add hl, bc
	push hl
	ad_address JC_TOTAL
	pop bc
	ld d, b
	ld e, c
	ld b, 7
.copy
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy
	pop hl ; original context, not a source pointer into the result reservation
	pop af
	inc de
	inc de
	ld [de], a
	dec de
	dec de
	pop bc
	ld a, b
	ld [de], a
	inc de
	ld a, c
	ld [de], a
	ld d, h
	ld e, l
	ret

ASSERT BANK(BossAI_ComparePublicActionsFastReferenceRestart) == BANK(BossAI_ComparePublicActions)
