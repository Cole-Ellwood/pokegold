; Standalone incoming successors, deltas and signed probability moment.
BossAI_FastBuildReplyStandalone::
; DE=context with compiled reply399..446. Imported actors/HP tables live,
; SRAM0 open. DE/SP preserved. Reject opcode0 or >9 without writes.
; Writes only reply28..42, both continuations, executor/arithmetic scratch.
; Original event flags remain in their continuations, not in a plan union.
; Fixed public-context preconditions match the incoming plan executor.
	ad_address FSR_BASE + FSR_OPCODE
	ld a, [hl]
	and a
	jp z, .reject
	cp FSR_BOOST + 1
	jp nc, .reject
	push de
	xor a
	ld [FSO_EVENT], a
.event
	push de ; restore context before the next incoming executor
	ld hl, $a448
	ld a, [FSO_EVENT]
	and a
	jr z, .continuation
	ld hl, $a460
.continuation
	push hl
	ld b, 24
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	pop hl
	push hl
	ld a, [FSA_START_HP]
	ld [hli], a
	ld a, [FSA_START_HP + 1]
	ld [hli], a
	ld a, [FSA_PLAYER]
	ld [hli], a
	ld a, [FSA_PLAYER + 1]
	ld [hl], a
	pop hl
	ld a, [FSO_EVENT]
	call BossAI_FastExecuteReplyPlan
	ld a, [FSO_EVENT]
	add a
	add a
	add FSR_HIT_HP
	call BossAI_FastExecuteReplyPlan.PlanAddress
	push hl
	call BossAI_FastExecuteReplyPlan.Continuation
	pop de
	ld b, 4
.copy_hp
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_hp
; a successor equal to the start state (a miss, or a hit that cannot land)
; leaves both potentials where the import put them: delta zero
	call BossAI_FastExecuteReplyPlan.Continuation
	ld a, [FSA_START_HP]
	cp [hl]
	jr nz, .delta
	inc hl
	ld a, [FSA_START_HP + 1]
	cp [hl]
	jr nz, .delta
	inc hl
	ld a, [FSA_PLAYER]
	cp [hl]
	jr nz, .delta
	inc hl
	ld a, [FSA_PLAYER + 1]
	cp [hl]
	ld bc, 0
	jr z, .delta_ready
.delta
	call BossAI_FastBuildOwnedStandalone.Delta
.delta_ready
	push bc
	ld a, [FSO_EVENT]
	add a
	add FSR_HIT_DELTA
	call BossAI_FastExecuteReplyPlan.PlanAddress
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	pop de
	ld hl, FSO_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .event
	call .Moment
	pop de
	scf
	ret
.reject
	and a
	ret

.Moment
; 256*miss + p*(hit-miss). Multiply sign-extended difference in the existing
; 40-bit arithmetic workspace, then add its low24 bits to the signed24 base.
	ld a, FSR_MISS_DELTA
	call BossAI_FastExecuteReplyPlan.PlanWord
	push bc
	ld a, FSR_MOMENT
	call BossAI_FastExecuteReplyPlan.PlanAddress
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	ld [hl], 0
	push bc
	ld a, FSR_HIT_DELTA
	call BossAI_FastExecuteReplyPlan.PlanWord
	pop hl
	ld a, c
	sub l
	ld c, a
	ld a, b
	sbc h
	ld b, a
	ld [FS_MULTIPLICAND + 3], a
	ld a, c
	ld [FS_MULTIPLICAND + 4], a
	ld a, b
	add a
	sbc a
	ld [FS_MULTIPLICAND], a
	ld [FS_MULTIPLICAND + 1], a
	ld [FS_MULTIPLICAND + 2], a
	xor a
	ld [FS_MULTIPLIER], a
	ld [FS_MULTIPLIER + 1], a
	ld a, FSR_ACCURACY
	call BossAI_FastExecuteReplyPlan.PlanAddress
	ld a, [hl]
	cp 255
	jr nz, .probability
	ld a, 1
	ld [FS_MULTIPLIER + 1], a
	xor a
.probability
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
	ld a, FSR_MOMENT + 2
	call BossAI_FastExecuteReplyPlan.PlanAddress
	ld de, FS_PRODUCT + 4
	ld b, 3
	and a
.add
	ld a, [de]
	adc [hl]
	ld [hld], a
	dec de
	dec b
	jr nz, .add
	ret
