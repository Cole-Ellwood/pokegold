; Private selector input and result boundaries. These helpers are not a
; complete selector: no gameplay caller exists until native evaluation passes.
DEF FS_ACTIONS EQU AV_PREPARED_CONTEXT_SIZE
DEF FS_REPLIES EQU FS_ACTIONS + AC_CONTEXT_SIZE
DEF FS_REPLY EQU FS_REPLIES + PR_CONTEXT_SIZE
DEF FS_CONTROL EQU FS_REPLY + 48
DEF FS_KIND EQU FS_CONTROL
DEF FS_SCAN EQU FS_CONTROL + 1
DEF FS_LEGAL_MASK EQU FS_CONTROL + 20
DEF FS_REPLY_WEIGHT EQU FS_CONTROL + 22
DEF FS_BACKEND EQU FS_CONTROL + 24
DEF FS_CONTEXT_SIZE EQU FS_CONTROL + 25
DEF FS_RESULTS EQU $a280
DEF FS_RECORD_SIZE EQU 10
DEF FS_RESULT_COUNT EQU 12
DEF FS_RECORD_BYTES EQU FS_RECORD_SIZE * FS_RESULT_COUNT
DEF FS_OUT_INDEX EQU FS_RECORD_BYTES
DEF FS_OUT_UNCERTAINTY EQU FS_OUT_INDEX + 1
DEF FS_OUT_SCORE EQU FS_OUT_INDEX + 2
DEF FS_OUT_LEGAL EQU FS_OUT_INDEX + 4
DEF FS_OUT_STATUS EQU FS_OUT_INDEX + 6
DEF FS_OUT_VERSION EQU FS_OUT_INDEX + 7
; Finalization owns all arithmetic scratch after producers are dead.
DEF FS_RESULT_PTR EQU FS_MATH + 24
DEF FS_RESULT_INDEX EQU FS_MATH + 26
DEF FS_REMAINING_MASK EQU FS_MATH + 27
DEF FS_BEST_INDEX EQU FS_MATH + 29
DEF FS_BEST_SCORE EQU FS_MATH + 30
ASSERT FS_ACTIONS == 324
ASSERT FS_REPLIES == 332
ASSERT FS_CONTROL == 447
ASSERT FS_CONTEXT_SIZE == 472
ASSERT FS_CONTEXT_SIZE <= wBattle - wBattleAnimTileDict
ASSERT FS_RESULTS + FS_RECORD_BYTES == $a2f8

BossAI_FastPreparePublicInputs::
; DE=472-byte owned context, A=decision0/2, B=traversal0..15. SRAM closed.
; DE preserved, carry=accepted. No selected index or complete vector yet.
; Invalid inputs are rejected before mutation. Actor/producer prefix is dead
; except that the legacy SRAM-table flag is explicitly invalidated.
	cp AV_REPLACEMENT_ACTION
	jr z, .kind_ok
	and a
	jr nz, .reject
.kind_ok
	ld c, a
	ld a, b
	and $f0
	jr nz, .reject
	push bc
	ad_address FS_ACTIONS
	ld b, FS_CONTEXT_SIZE - FS_ACTIONS
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ad_address AV_PREPARED_DAMAGE
	ld [hl], a
	pop bc
	ad_address FS_KIND
	ld [hl], c
	inc hl
	ld [hl], b
	ad_address FS_BACKEND
	ld [hl], $ff ; no completed evaluation until an evaluator commits its status
	push de
	ad_address FS_ACTIONS
	ld d, h
	ld e, l
	farcall BossAI_EnumeratePublicActionsFromC
	pop de
	ad_address FS_KIND
	ld a, [hl]
	cp AV_REPLACEMENT_ACTION
	jr z, .replacement
	push de
	ad_address FS_REPLIES
	ld d, h
	ld e, l
	farcall BossAI_BuildPublicReplySet
	pop de
	scf
	ret
.replacement
; Replacement has one absent reply and no open-moveset prior.
	ad_address FS_REPLY_WEIGHT + 1
	ld [hl], 1
	scf
	ret
.reject
	ld bc, 0
	and a
	ret

BossAI_FastClearResults::
; Bank0 SRAM must be open. DE preserved. Canonical invalid records.
	ld hl, FS_RESULTS
	ld b, FS_RESULT_COUNT
.record
	ld c, 7
	xor a
.zero
	ld [hli], a
	dec c
	jr nz, .zero
	ld a, $ff
	ld [hli], a
	ld [hli], a
	ld [hli], a
	dec b
	jr nz, .record
	ret

BossAI_FastFinalizeResults::
; DE=472-byte context, bank0 SRAM open, all producers/evaluation finished.
; Complete T/M/uncertainty records and explicit legality mask are inputs.
; Backend status0..2 is required. Normalize ALL legal records, choose highest
; integer score then lowest original index, export128bytes, close SRAM.
; DE/SP preserved; BC=best score, carry=legal. AF exceptcarry/HL are scratch.
; Invalid status/mass/numerator rejects the entire vector, never partial output.
	push de
	ad_address FS_BACKEND
	ld a, [hl]
	cp 3
	jp nc, .reject
	ad_address FS_LEGAL_MASK
	ld a, [hli]
	ld [FS_REMAINING_MASK], a
	and $f0
	jp nz, .reject
	ld a, [hl]
	ld [FS_REMAINING_MASK + 1], a
	xor a
	ld [FS_RESULT_INDEX], a
	ld [FS_BEST_SCORE], a
	ld [FS_BEST_SCORE + 1], a
	dec a
	ld [FS_BEST_INDEX], a
	ld a, HIGH(FS_RESULTS)
	ld [FS_RESULT_PTR], a
	ld a, LOW(FS_RESULTS)
	ld [FS_RESULT_PTR + 1], a
.record
	ld hl, FS_REMAINING_MASK
	srl [hl]
	inc hl
	rr [hl]
	call .RecordPointer ; loads preserve carry
	jr nc, .invalid_record
	ld a, [hli]
	ld [FS_DIVIDEND], a
	ld a, [hli]
	ld [FS_DIVIDEND + 1], a
	ld a, [hli]
	ld [FS_DIVIDEND + 2], a
	inc hl
	inc hl ; discard only final fractional bytes, retaining full T in record
	ld a, [hli]
	ld b, a
	ld [FS_DIVISOR], a
	ld a, [hli]
	ld c, a
	ld [FS_DIVISOR + 1], a
	or b
	jp z, .reject
	ld a, b
	cp HIGH(565)
	jp c, .mass_ok
	jp nz, .reject
	ld a, c
	cp LOW(565)
	jp nc, .reject
.mass_ok
	push hl
	call BossAI_FastDivide24By16
	pop hl
	ld a, [FS_DIVIDEND]
	and a
	jp nz, .reject
	ld a, [FS_DIVIDEND + 1]
	ld b, a
	cp HIGH(2048)
	jr c, .score_low
	jp nz, .reject
	ld a, [FS_DIVIDEND + 2]
	and a
	jp nz, .reject
.score_low
	ld a, [FS_DIVIDEND + 2]
	ld c, a
	ld [hl], b
	inc hl
	ld [hl], c
	ld a, [FS_BEST_INDEX]
	cp $ff
	jr z, .better
	ld a, [FS_BEST_SCORE]
	cp b
	jr c, .better
	jr nz, .next
	ld a, [FS_BEST_SCORE + 1]
	cp c
	jr nc, .next ; includes equal integer score: keep earlier original index
.better
	ld a, b
	ld [FS_BEST_SCORE], a
	ld a, c
	ld [FS_BEST_SCORE + 1], a
	ld a, [FS_RESULT_INDEX]
	ld [FS_BEST_INDEX], a
	jr .next
.invalid_record
	ld b, 7
	xor a
.invalid_zero
	ld [hli], a
	dec b
	jr nz, .invalid_zero
	dec a
	ld [hli], a
	ld [hli], a
	ld [hl], a
.next
	ld hl, FS_RESULT_PTR + 1
	ld a, [hl]
	add FS_RECORD_SIZE
	ld [hld], a
	jr nc, .pointer_ready
	inc [hl]
.pointer_ready
	ld hl, FS_RESULT_INDEX
	inc [hl]
	ld a, [hl]
	cp FS_RESULT_COUNT
	jp c, .record
	jr .export
.reject
	call BossAI_FastClearResults
	xor a
	ad_address FS_LEGAL_MASK
	ld [hli], a
	ld [hl], a
	ld [FS_BEST_SCORE], a
	ld [FS_BEST_SCORE + 1], a
	dec a
	ld [FS_BEST_INDEX], a
	ad_address FS_BACKEND
	ld [hl], a
.export
	push de
	ld hl, FS_RESULTS
	ld bc, FS_RECORD_BYTES
	call CopyBytes
	pop de
	ld a, [FS_BEST_INDEX]
	ad_address FS_OUT_INDEX
	ld [hli], a
	ld [hl], a ; invalid best also sets invalid uncertainty
	cp $ff
	jr z, .summary
	ld c, a
	add a
	add a
	add c
	add a ; 10*original index
	ld c, a
	ld b, 0
	ld hl, FS_RESULTS + 9
	add hl, bc
	ld a, [hl]
	ad_address FS_OUT_UNCERTAINTY
	ld [hl], a
.summary
	av_copy_word FS_LEGAL_MASK, FS_OUT_LEGAL
	ad_address FS_BACKEND
	ld a, [hl]
	ad_address FS_OUT_STATUS
	ld [hli], a
	ld [hl], 1
	ld a, [FS_BEST_SCORE]
	ld b, a
	ld a, [FS_BEST_SCORE + 1]
	ld c, a
	av_store_word FS_OUT_SCORE
	ld a, [FS_BEST_INDEX]
	cp $ff
	pop de
	jp CloseSRAM ; carry iff best index<255; preserves BC/carry
.RecordPointer
	ld a, [FS_RESULT_PTR]
	ld h, a
	ld a, [FS_RESULT_PTR + 1]
	ld l, a
	ret
