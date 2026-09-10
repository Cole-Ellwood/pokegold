; Common-sum allocation after the pair total: $a578..$a58f.
DEF FSC_INCOMING EQU $a57d ; signed32 sum of weight*reply moment, current defender
DEF FSC_MASS EQU $a581 ; M=2*W_R for the whole decision
DEF FSC_ENTRY_DELTA EQU $a583 ; signed16 entry potential change, zero when active
DEF FSC_BASELINE EQU $a585 ; 2*65536*(1024+entry delta): the unary standalone baseline
DEF FSC_TEMP EQU $a58a ; five-byte accumulation temporary
ASSERT FPK_TOTAL + 5 == FSC_INCOMING
ASSERT FSC_TEMP + 5 == FSC_FAULT
ASSERT FSC_FAULT < $a590

; Main-bank far entries for the fallback evaluators (Boss AI Fast Fallback
; section): the compact executors at the shared continuation and the
; standalone delta. Inputs come from the pair control bytes, not registers.
BossAI_FastFallbackOwnAction::
	call BossAI_FastNormalizedPair.Context
	ld hl, FSE_CONT_HIT
	ld a, [FPK_INDEX]
	ld c, a
	ld a, [FPK_FIRST_EVENT]
	jp BossAI_FastExecuteOwnedPlan
BossAI_FastFallbackReplyAction::
	call BossAI_FastNormalizedPair.Context
	ld hl, FSE_CONT_HIT
	ld a, [FPK_SECOND_EVENT]
	jp BossAI_FastExecuteReplyPlan
BossAI_FastFallbackDelta::
; BC=V(final)-V(initial) of the shared continuation.
	jp BossAI_FastBuildOwnedStandalone.Delta
