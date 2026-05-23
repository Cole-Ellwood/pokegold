; ============================================================
; engine/battle/ai/haki_taunt_queue.asm - Uniform Haki taunt queue
; Included with BOSSAI_EMIT_* guards from main.asm.
; ============================================================

if DEF(BOSSAI_EMIT_HAKI_TAUNT_QUEUE)
; ai-layer: PLATFORM
BossAI_QueueHakiTaunt::
; Store a one-byte 1-based taunt index. Byte 2 of
; wBossAIRevealedMovesBitmapSpare is unused by revealed-move masks and is
; cleared by ClearBossAIState with the rest of the Boss AI state.
	ld a, [wTrainerClass]
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a
	ld hl, BossAIHakiTauntMap
	ld d, 1
.loop
	ld a, [hli]
	and a
	jr z, .missing
	cp b
	jr nz, .skip_id
	ld a, [hli]
	cp c
	jr z, .found
	inc d
	jr .loop

.skip_id
	inc hl
	inc d
	jr .loop

.found
	ld a, d
	ld [wBossAIRevealedMovesBitmapSpare + 2], a
	ret

.missing
	xor a
	ld [wBossAIRevealedMovesBitmapSpare + 2], a
	ret

; ai-layer: PLATFORM
BossAI_FlushPendingHakiTaunt::
	ld a, [wBossAIRevealedMovesBitmapSpare + 2]
	and a
	ret z
	ld b, a
	xor a
	ld [wBossAIRevealedMovesBitmapSpare + 2], a
	ld a, b
	dec a
	add a
	ld c, a
	ld b, 0
	ld hl, BossAIHakiTauntPointers
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jp StdBattleTextbox

INCLUDE "data/boss_ai/haki_taunts.asm"

endc
