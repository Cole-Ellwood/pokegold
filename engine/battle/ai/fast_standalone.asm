; Standalone original-event successors and exact signed probability moments.
DEF FSO_INDEX EQU $a548
DEF FSO_EVENT EQU $a549
DEF FSO_DELTA EQU $a54a
ASSERT FSE_MASK < FSO_INDEX
ASSERT FSO_DELTA + 2 <= $a560
ASSERT FSE_MODE == FSO_DELTA + 1 ; action execution and Delta are sequential

BossAI_FastBuildOwnedStandalone::
; C=compiled owned plan0..3; imported actors and HP tables already live.
; DE/SP preserved, SRAM0 open. Same fixed-context preconditions as executor.
; Carry=complete. Invalid index/fallback opcode returns clear without writes.
; Writes plan32..48, both continuations, executor and arithmetic workspaces.
; mu = p*delta_hit + (256-p)*delta_miss; accuracy255 decodes to256.
	ld a, c
	cp 4
	jp nc, .reject
	push bc
	ld b, 0
	rept 6
	sla c
	rl b
	endr
	ld hl, FSP_BASE + FSP_OPCODE
	add hl, bc
	ld a, [hl]
	and a
	jp z, .reject_pop
	cp FSP_SELFDESTRUCT + 1
	jp nc, .reject_pop
	pop bc
	ld a, c
	ld [FSO_INDEX], a
	push de
	xor a
	ld [FSO_EVENT], a
.event
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
	ld a, [FSO_INDEX]
	ld c, a
	ld a, [FSO_EVENT]
	call BossAI_FastExecuteOwnedPlan
	ld a, [FSO_EVENT]
	add a
	add a
	add FSP_HIT_HP
	call BossAI_FastExecuteOwnedPlan.PlanAddress
	push hl
	call BossAI_FastExecuteOwnedPlan.Continuation
	pop de
	ld b, 4
.copy_hp
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_hp
	call BossAI_FastExecuteOwnedPlan.Continuation
	ld bc, 16
	add hl, bc
	ld a, [hl]
	push af
	ld a, [FSO_EVENT]
	add FSP_STANDALONE_HIT_FLAGS
	call BossAI_FastExecuteOwnedPlan.PlanAddress
	pop af
	ld [hl], a
	call .Delta
	push bc
	ld a, [FSO_EVENT]
	add a
	add FSP_HIT_DELTA
	call BossAI_FastExecuteOwnedPlan.PlanAddress
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	ld hl, FSO_EVENT
	inc [hl]
	ld a, [hl]
	cp 2
	jp c, .event
	call .Moment
	pop de
	scf
	ret
.reject_pop
	pop bc
.reject
	and a
	ret
.Delta
; Own phi difference minus player's, signed16, no HP averaging.
	call BossAI_FastExecuteOwnedPlan.Continuation
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_HP_MODE]
	ld d, a
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastHPPotential
	ld a, [FSA_START_PHI + 1]
	ld l, a
	ld a, c
	sub l
	ld [FSO_DELTA + 1], a
	ld a, [FSA_START_PHI]
	ld h, a
	ld a, b
	sbc h
	ld [FSO_DELTA], a
	call BossAI_FastExecuteOwnedPlan.Continuation
	inc hl
	inc hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, [FSA_PLAYER + 37]
	ld d, a
	ld a, 128
	ld hl, $a180
	call BossAI_FastHPPotential
	ld a, [FSA_PLAYER + 5]
	ld l, a
	ld a, c
	sub l
	ld c, a
	ld a, [FSA_PLAYER + 4]
	ld h, a
	ld a, b
	sbc h
	ld b, a
	ld a, [FSO_DELTA + 1]
	sub c
	ld c, a
	ld a, [FSO_DELTA]
	sbc b
	ld b, a
	ret
.Moment
; 256*miss + p*(hit-miss). Multiply sign-extended difference in the existing
; 40-bit arithmetic workspace, then add its low24 bits to the signed24 base.
	ld a, FSP_MISS_DELTA
	call BossAI_FastExecuteOwnedPlan.PlanWord
	push bc
	ld a, FSP_MOMENT
	call BossAI_FastExecuteOwnedPlan.PlanAddress
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	ld [hl], 0
	push bc
	ld a, FSP_HIT_DELTA
	call BossAI_FastExecuteOwnedPlan.PlanWord
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
	ld a, FSP_ACCURACY
	call BossAI_FastExecuteOwnedPlan.PlanAddress
	ld a, [hl]
	cp 255
	jr nz, .probability
	ld a, 1
	ld [FS_MULTIPLIER + 1], a
	xor a
.probability
	ld [FS_MULTIPLIER + 2], a
	call BossAI_FastMultiply40By24
	ld a, FSP_MOMENT + 2
	call BossAI_FastExecuteOwnedPlan.PlanAddress
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
