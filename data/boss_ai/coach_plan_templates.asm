; P7 high-conviction LATE-only coach templates.
; Row shape:
;   class, trainer id, active species, plan id,
;   phase-0 move, phase-1 move, phase-2+ move, revealed-stop effect, confidence
;
; Public stop effects are checked against the active player's revealed moves.

BossAICoachPlanTemplates:
	db CHAMPION, LANCE, DRAGONITE, BOSS_PLAN_TEMPLATE_SETUP_ONCE_THEN_ATTACK, DRAGON_DANCE, OUTRAGE, OUTRAGE, EFFECT_FORCE_SWITCH, 92
	db KOGA, KOGA1, MUK, BOSS_PLAN_TEMPLATE_PRESSURE_RECOVER_THEN_LOCK, TOXIC, CURSE, REST, EFFECT_HEAL_BELL, 86
	db 0
