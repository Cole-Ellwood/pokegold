IF DEF(BOSSAI_EMIT_LOCAL_PRIORITIES)
BossAI_FastMoveEffectPriorities: ; in-bank mirror for the offline AI reference
ELSE
MoveEffectPriorities:
ENDC
	db EFFECT_PROTECT,      3
	db EFFECT_ENDURE,       3
	db EFFECT_PRIORITY_HIT, 2
	db EFFECT_FORCE_SWITCH, 0
	db EFFECT_COUNTER,      0
	db EFFECT_MIRROR_COAT,  0
	db EFFECT_FOCUS_PUNCH,  0
	db -1
