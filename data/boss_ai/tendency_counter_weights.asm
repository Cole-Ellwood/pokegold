; P5 observation-log tendency weights.
; Indexed by BOSS_AI_OBS_CLASS_*; values are additive switch-prediction points.

BossAIObservationTendencyWeights:
	db 0 ; BOSS_AI_OBS_CLASS_NONE
	db 8 ; BOSS_AI_OBS_CLASS_SWITCH_UNDER_PRESSURE
	db 3 ; BOSS_AI_OBS_CLASS_PROTECT_RECOVER
	db 3 ; BOSS_AI_OBS_CLASS_GREEDY_SETUP
	db 2 ; BOSS_AI_OBS_CLASS_STATUS_FISH
	db 2 ; BOSS_AI_OBS_CLASS_BAD_MATCHUP_ATTACK
	db 2 ; BOSS_AI_OBS_CLASS_LOW_HP_SACK
