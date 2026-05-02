; Trace-only top-3 move snapshot, used by tools/trace/* to capture the boss
; decision surface. Lifted out of engine/battle/ai/boss.asm and placed in its
; own SECTION (see main.asm) because the in-bank "Enemy Trainers" budget can
; no longer hold both the trace block and the per-tick cache wrappers.
;
; Called via farcall from BossAI_SelectMove (also gated by IF DEF(BOSS_AI_TRACE)).

IF DEF(BOSS_AI_TRACE)

BossAI_TraceTopMoves::
	ld a, [wBossAITier]
	and a
	ret z

	ld hl, wBossAITraceTopMoves
	xor a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ld hl, wBossAITraceTopScores
	ld a, $ff
	ld [hli], a
	ld [hli], a
	ld [hl], a

	ld hl, wEnemyAIMoveScores
	ld de, wEnemyMonMoves
	ld c, NUM_MOVES
.loop
	ld a, [de]
	and a
	ret z
	ld b, a ; move id
	ld a, [hl]
	cp 80
	jr nc, .next
	push de
	call .InsertCandidate
	pop de
.next
	inc hl
	inc de
	dec c
	jr nz, .loop
	ret

.InsertCandidate
	ld d, a ; candidate score
	ld a, [wBossAITraceTopScores]
	cp d
	jr c, .check_second
	jr z, .check_second
	ld a, [wBossAITraceTopScores + 1]
	ld [wBossAITraceTopScores + 2], a
	ld a, [wBossAITraceTopMoves + 1]
	ld [wBossAITraceTopMoves + 2], a
	ld a, [wBossAITraceTopScores]
	ld [wBossAITraceTopScores + 1], a
	ld a, [wBossAITraceTopMoves]
	ld [wBossAITraceTopMoves + 1], a
	ld a, d
	ld [wBossAITraceTopScores], a
	ld a, b
	ld [wBossAITraceTopMoves], a
	ret

.check_second
	ld a, [wBossAITraceTopScores + 1]
	cp d
	jr c, .check_third
	jr z, .check_third
	ld a, [wBossAITraceTopScores + 1]
	ld [wBossAITraceTopScores + 2], a
	ld a, [wBossAITraceTopMoves + 1]
	ld [wBossAITraceTopMoves + 2], a
	ld a, d
	ld [wBossAITraceTopScores + 1], a
	ld a, b
	ld [wBossAITraceTopMoves + 1], a
	ret

.check_third
	ld a, [wBossAITraceTopScores + 2]
	cp d
	ret c
	ret z
	ld a, d
	ld [wBossAITraceTopScores + 2], a
	ld a, b
	ld [wBossAITraceTopMoves + 2], a
	ret

ENDC
