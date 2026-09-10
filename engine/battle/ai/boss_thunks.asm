; ============================================================
; engine/battle/ai/boss_thunks.asm — HL-preserving cross-bank thunks into the AI Scoring bank
; Split out of boss.asm per docs/boss_ai_organization_plan.md §3
; Option C. SECTION: Enemy Trainers (bank 0e), shared with the other
; boss_*.asm files and items.asm + read_trainer_attributes.asm.
; ============================================================

; Region: Cross-bank _HL thunks
; Concern: HL-preserving farcall thunks into the AI Scoring bank
; Layer: THUNK
; Original lines: 59
; ============================================================
; The AI Scoring helpers (scoring.asm) sit in the floating "AI Scoring"
; section, a different ROMX bank from the boss policy files here in bank
; 0x0e ("Enemy Trainers"), so a plain `call AIxxx` from a boss_*.asm file
; would resolve inside bank 0x0e (garbage). `farcall` clobbers `hl` before
; the target runs (asm guide 3.2), and many boss callers need `hl`
; preserved across the call (e.g. `jp BossAI_*ScoreHL`).
;
; These thunks share bank 0x0e with the boss files, so a plain
; `call AIxxx_HL` reaches them. Each wraps `farcall` with `push hl` /
; `pop hl` so the caller's hl is preserved end-to-end. AIGetEnemyMove_HL
; also preserves bc and passes the move id through c because farcall
; consumes a for the target bank. ROM0 was too tight for these.
;
; Rationale: `tools/audit/check_cross_bank_call.py` flagged 39 plain-call
; sites in the boss policy code targeting scoring.asm; this is the same
; class as the May 2026 cross-bank softlock (commit 2593278d).

; ai-layer: THUNK
AIGetEnemyMove_HL:
	push hl
	push bc
	ld c, a
	farcall AIGetEnemyMoveFromC
	pop bc
	pop hl
	ret

; ai-layer: THUNK
AICheckEnemyQuarterHP_HL:
	push hl
	farcall AICheckEnemyQuarterHP
	pop hl
	ret

; ai-layer: THUNK
AICheckEnemyHalfHP_HL:
	push hl
	farcall AICheckEnemyHalfHP
	pop hl
	ret

; ai-layer: THUNK
AICheckEnemyMaxHP_HL:
	push hl
	farcall AICheckEnemyMaxHP
	pop hl
	ret

; ai-layer: THUNK
AICheckPlayerQuarterHP_HL:
; The player-HP targets use the "hl" macro variant, which clobbers bc;
; preserve it like the enemy-HP thunks so every thunk has the same contract.
	push hl
	push bc
	farcall AICheckPlayerQuarterHP
	pop bc
	pop hl
	ret

; ai-layer: THUNK
AICheckPlayerHalfHP_HL:
	push hl
	push bc
	farcall AICheckPlayerHalfHP
	pop bc
	pop hl
	ret

; ai-layer: THUNK
AICheckPlayerMaxHP_HL:
	push hl
	farcall AICheckPlayerMaxHP
	pop hl
	ret
