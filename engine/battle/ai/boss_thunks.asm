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
; AI Scoring helpers live in bank 0x0b ("AI Scoring"). boss.asm itself
; lives in bank 0x0e ("Enemy Trainers"), so a plain `call AIxxx` from
; boss.asm to a scoring helper resolves at offset $7xxx in bank 0x0e
; (garbage). `farcall` would clobber `hl` before the target runs (per
; CLAUDE.md), and many boss.asm callers need `hl` preserved across the
; call (e.g., `jp BossAI_*ScoreHL`).
;
; These intra-bank thunks live alongside boss.asm in bank 0x0e, so plain
; `call AIxxx_HL` from boss.asm reaches them. Most thunks wrap `farcall`
; to the bank-0x0b target with `push hl` / `pop hl` so caller's hl is
; preserved end-to-end. AIGetEnemyMove_HL also preserves bc and passes
; the move id through c because farcall consumes a for the target bank.
; ROM0 was too tight for these (Home section had 13 bytes free; the
; 229 ROM0-free is fragmented across rst-handler gaps).
;
; Rationale: `tools/audit/check_cross_bank_call.py` flagged 39 plain-call
; sites in boss.asm targeting scoring.asm; this is the same class as
; the May 2026 cross-bank softlock (commit 2593278d).

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
	push hl
	farcall AICheckPlayerQuarterHP
	pop hl
	ret

; ai-layer: THUNK
AICheckPlayerHalfHP_HL:
	push hl
	farcall AICheckPlayerHalfHP
	pop hl
	ret

; ai-layer: THUNK
AICheckPlayerMaxHP_HL:
	push hl
	farcall AICheckPlayerMaxHP
	pop hl
	ret
