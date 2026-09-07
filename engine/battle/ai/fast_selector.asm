; Native replacement orchestration; ordinary decisions currently restart
; through the complete compatibility adapter. This is not the timing gate.
DEF FS_NATIVE_SLOT EQU FS_CONTROL + 2
DEF FS_NATIVE_LEFT EQU FS_CONTROL + 3

BossAI_ComparePublicActionsFastPrototype::
; DE=472-byte context, A=decision0/2, B=scan0..15, SRAM closed. Same full
; record ABI/finalizer as the compatibility adapter. Native replacement
; computes entry HP potentials directly; all other paths return status2.
	ld c, a
	push bc
	call BossAI_FastPreparePublicInputs
	pop bc
	jp nc, .reference
	ld a, c
	cp AV_REPLACEMENT_ACTION
	jp nz, .reference
	xor a
	call OpenSRAM
	call BossAI_FastClearResults
	ad_address FS_LEGAL_MASK
	xor a
	ld [hli], a
	ld [hl], a
	ad_address FS_SCAN
	bit 0, [hl]
	ld a, 0
	jr z, .first
	ld a, PARTY_LENGTH - 1
.first
	ad_address FS_NATIVE_SLOT
	ld [hli], a
	ld [hl], PARTY_LENGTH
.candidate
	ad_address FS_NATIVE_SLOT
	ld c, [hl]
	ld b, 0
	ld hl, .SlotBits
	add hl, bc
	ld a, [hl]
	ad_address FS_ACTIONS + AC_SWITCH_MASK
	and [hl]
	jp z, .next
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	ad_address AV_SLOT
	ld [hl], a
	farcall BossAI_FastPrepareReplacementFacts
	ld a, [FSA_MAX_HP]
	ld b, a
	ld a, [FSA_MAX_HP + 1]
	ld c, a
	ld a, [FSA_START_HP]
	cp b
	jr c, .valid_hp
	jp nz, .restart
	ld a, [FSA_START_HP + 1]
	cp c
	jr c, .valid_hp
	jp nz, .restart
.valid_hp
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastBuildHPTable
	jp nc, .restart
	ld [FSA_HP_MODE], a
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	call .Potential
	ld a, b
	ld [FSA_START_PHI], a
	ld a, c
	ld [FSA_START_PHI + 1], a
	ld a, [FSB_ENTRY_LOSS]
	ld b, a
	ld a, [FSB_ENTRY_LOSS + 1]
	ld c, a
	ld hl, FSA_ENTRY_HP
	call BossAI_FastLoseHP
	ld a, [FSA_ENTRY_HP]
	ld b, a
	ld a, [FSA_ENTRY_HP + 1]
	ld c, a
	call .Potential
	ld a, b
	ld [FSA_ENTRY_PHI], a
	ld a, c
	ld [FSA_ENTRY_PHI + 1], a
	ld hl, 1024
	add hl, bc
	ld a, [FSA_START_PHI + 1]
	ld c, a
	ld a, l
	sub c
	ld c, a
	ld a, [FSA_START_PHI]
	ld b, a
	ld a, h
	sbc b
	ld b, a
	call .StoreRecord
.next
	ad_address FS_NATIVE_LEFT
	dec [hl]
	jr z, .done
	ad_address FS_SCAN
	bit 0, [hl]
	ad_address FS_NATIVE_SLOT
	jr nz, .previous
	inc [hl]
	jp .candidate
.previous
	dec [hl]
	jp .candidate
.done
	ad_address FS_BACKEND
	ld [hl], 0
	jp BossAI_FastFinalizeResults
.restart
	call CloseSRAM ; discard native state before the old JC lifetime begins
	ad_address FS_KIND
	ld c, [hl]
	inc hl
	ld b, [hl]
.reference
	farcall BossAI_FastReferenceRestartFromC
	ret
.Potential
	push de
	ld a, [FSA_HP_MODE]
	ld d, a
	ld a, [FSA_WEIGHT]
	ld hl, $a000
	call BossAI_FastHPPotential
	pop de
	ret
.StoreRecord
; BC=1024+entryPhi-startPhi. One absent reply/order has M=2 and T=score*2*65536.
	push bc
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	add 4
	add a
	ld c, a
	add a
	add a
	add c
	ld c, a
	ld b, 0
	ld hl, FS_RESULTS
	add hl, bc
	pop bc
	xor a
	ld [hli], a
	sla c
	rl b
	ld [hl], b
	inc hl
	ld [hl], c
	inc hl
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld a, 2
	ld [hli], a
	xor a
	ld [hli], a
	ld [hli], a
	ld a, [FSB_SETUP_FLAGS]
	ld [hl], a
	ad_address FS_NATIVE_SLOT
	ld a, [hl]
	add a
	ld c, a
	ld b, 0
	ld hl, .ResultBits
	add hl, bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address FS_LEGAL_MASK
	ld a, [hl]
	or b
	ld [hli], a
	ld a, [hl]
	or c
	ld [hl], a
	ret
.SlotBits
	db 1, 2, 4, 8, 16, 32
.ResultBits
	bigdw 1 << 4, 1 << 5, 1 << 6, 1 << 7, 1 << 8, 1 << 9
