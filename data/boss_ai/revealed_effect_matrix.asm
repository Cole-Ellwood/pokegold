; ============================================================
; data/boss_ai/revealed_effect_matrix.asm
; P3 table consumed by BossAI_ApplyMoveModel.ApplyRevealedEffectMatrixBias.
;
; Row ABI:
;   db <revealed-key>, <candidate-key>, <rule-id>, <score-delta>
;
; Revealed keys are either exact active-player revealed move effects
; (checked through wPlayerUsedMoves) or BOSS_AI_REM_GROUP_* public keys.
; Candidate keys are exact boss candidate effects or BOSS_AI_REM_GROUP_*
; candidate classes derived from the candidate move currently in
; wEnemyMoveStruct. No row reads hidden player moves/items/private stats.
; ============================================================

BossAIRevealedEffectMatrix:
	; Revealed Protect punishes catastrophic boss commitment.
	db EFFECT_PROTECT, EFFECT_SELFDESTRUCT, BOSS_AI_REM_RULE_DISCOURAGE, 10
	db EFFECT_PROTECT, EFFECT_HYPER_BEAM, BOSS_AI_REM_RULE_DISCOURAGE, 4

	; Revealed recovery rewards denial lines that are useful on the public board.
	db BOSS_AI_REM_GROUP_RECOVERY, BOSS_AI_REM_GROUP_STATUS_DENIAL, BOSS_AI_REM_RULE_RECOVERY_STATUS_DENIAL, 4
	db BOSS_AI_REM_GROUP_RECOVERY, EFFECT_FORCE_SWITCH, BOSS_AI_REM_RULE_RECOVERY_UTILITY_DENIAL, 3

	; Revealed Encore changes whether commitment moves are safe.
	db EFFECT_ENCORE, BOSS_AI_REM_GROUP_COMMITMENT, BOSS_AI_REM_RULE_FAST_ENCORE_AVOIDANCE, 5
	db BOSS_AI_REM_GROUP_LAST_MOVE_ENCORE_TRAP, EFFECT_ENCORE, BOSS_AI_REM_RULE_LAST_MOVE_ENCORE_TRAP, 6

	; Revealed self-KO and sleep threats reward public preemption.
	db EFFECT_SELFDESTRUCT, EFFECT_PROTECT, BOSS_AI_REM_RULE_SELFDESTRUCT_PROTECT, 5
	db EFFECT_SLEEP, BOSS_AI_REM_GROUP_SLEEP_PREEMPT, BOSS_AI_REM_RULE_SLEEP_PREEMPT, 5

	; Revealed trade traps penalize unsafe KO/contact categories.
	db EFFECT_DESTINY_BOND, BOSS_AI_REM_GROUP_DAMAGING, BOSS_AI_REM_RULE_DESTINY_BOND_AVOIDANCE, 7
	db EFFECT_COUNTER, BOSS_AI_REM_GROUP_PHYSICAL_DAMAGE, BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE, 5
	db EFFECT_MIRROR_COAT, BOSS_AI_REM_GROUP_SPECIAL_DAMAGE, BOSS_AI_REM_RULE_COUNTERCOAT_AVOIDANCE, 5

	db -1
