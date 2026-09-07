IF DEF(BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS)
BossAI_TypeMatchups:
ELSE
TypeMatchups:
ENDC
; Optional row-group anchors for the local AI copy; combat bytes are unchanged.
MACRO bossai_type_group
IF DEF(BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS)
.\1:
ENDC
ENDM
	;  attacker,     defender,     *=
	bossai_type_group NORMAL
	db NORMAL,       ROCK,         NOT_VERY_EFFECTIVE
	db NORMAL,       STEEL,        NOT_VERY_EFFECTIVE
	db NORMAL,       PSYCHIC_TYPE, NOT_VERY_EFFECTIVE
	bossai_type_group FIRE
	db FIRE,         FIRE,         NOT_VERY_EFFECTIVE
	db FIRE,         WATER,        NOT_VERY_EFFECTIVE
	db FIRE,         GRASS,        SUPER_EFFECTIVE
	db FIRE,         ICE,          SUPER_EFFECTIVE
	db FIRE,         BUG,          SUPER_EFFECTIVE
	db FIRE,         ROCK,         NOT_VERY_EFFECTIVE
	db FIRE,         DRAGON,       NOT_VERY_EFFECTIVE
	db FIRE,         STEEL,        SUPER_EFFECTIVE
	bossai_type_group WATER
	db WATER,        FIRE,         SUPER_EFFECTIVE
	db WATER,        WATER,        NOT_VERY_EFFECTIVE
	db WATER,        GRASS,        NOT_VERY_EFFECTIVE
	db WATER,        GROUND,       SUPER_EFFECTIVE
	db WATER,        ROCK,         SUPER_EFFECTIVE
	db WATER,        DRAGON,       NOT_VERY_EFFECTIVE
	db WATER,        ICE,          NOT_VERY_EFFECTIVE
	bossai_type_group ELECTRIC
	db ELECTRIC,     WATER,        SUPER_EFFECTIVE
	db ELECTRIC,     ELECTRIC,     NOT_VERY_EFFECTIVE
	db ELECTRIC,     GRASS,        NOT_VERY_EFFECTIVE
	db ELECTRIC,     GROUND,       NO_EFFECT
	db ELECTRIC,     FLYING,       SUPER_EFFECTIVE
	db ELECTRIC,     DRAGON,       NOT_VERY_EFFECTIVE
	bossai_type_group GRASS
	db GRASS,        FIRE,         NOT_VERY_EFFECTIVE
	db GRASS,        WATER,        SUPER_EFFECTIVE
	db GRASS,        GRASS,        NOT_VERY_EFFECTIVE
	db GRASS,        POISON,       NOT_VERY_EFFECTIVE
	db GRASS,        GROUND,       SUPER_EFFECTIVE
	db GRASS,        BUG,          NOT_VERY_EFFECTIVE
	db GRASS,        ROCK,         SUPER_EFFECTIVE
	db GRASS,        DRAGON,       NOT_VERY_EFFECTIVE
	db GRASS,        STEEL,        NOT_VERY_EFFECTIVE
	bossai_type_group ICE
	db ICE,          WATER,        NOT_VERY_EFFECTIVE
	db ICE,          GRASS,        SUPER_EFFECTIVE
	db ICE,          ICE,          NOT_VERY_EFFECTIVE
	db ICE,          GROUND,       SUPER_EFFECTIVE
	db ICE,          FLYING,       SUPER_EFFECTIVE
	db ICE,          DRAGON,       SUPER_EFFECTIVE
	db ICE,          STEEL,        NOT_VERY_EFFECTIVE
	db ICE,          FIRE,         NOT_VERY_EFFECTIVE
	bossai_type_group FIGHTING
	db FIGHTING,     NORMAL,       SUPER_EFFECTIVE
	db FIGHTING,     ICE,          SUPER_EFFECTIVE
	db FIGHTING,     FLYING,       NOT_VERY_EFFECTIVE
	db FIGHTING,     PSYCHIC_TYPE, NOT_VERY_EFFECTIVE
	db FIGHTING,     ROCK,         SUPER_EFFECTIVE
	db FIGHTING,     DARK,         SUPER_EFFECTIVE
	db FIGHTING,     STEEL,        SUPER_EFFECTIVE
	bossai_type_group POISON
	db POISON,       GRASS,        SUPER_EFFECTIVE
	db POISON,       POISON,       NOT_VERY_EFFECTIVE
	db POISON,       GROUND,       NOT_VERY_EFFECTIVE
	db POISON,       ROCK,         NOT_VERY_EFFECTIVE
	db POISON,       GHOST,        NOT_VERY_EFFECTIVE
	db POISON,       STEEL,        NO_EFFECT
	db POISON,       NORMAL,       SUPER_EFFECTIVE
	bossai_type_group GROUND
	db GROUND,       ELECTRIC,     SUPER_EFFECTIVE
	db GROUND,       GRASS,        NOT_VERY_EFFECTIVE
	db GROUND,       POISON,       SUPER_EFFECTIVE
	db GROUND,       FLYING,       NO_EFFECT
	db GROUND,       BUG,          NOT_VERY_EFFECTIVE
	db GROUND,       ROCK,         SUPER_EFFECTIVE
	db GROUND,       STEEL,        SUPER_EFFECTIVE
	db GROUND,       GHOST,        NO_EFFECT
	bossai_type_group FLYING
	db FLYING,       ELECTRIC,     NOT_VERY_EFFECTIVE
	db FLYING,       GRASS,        SUPER_EFFECTIVE
	db FLYING,       FIGHTING,     SUPER_EFFECTIVE
	db FLYING,       BUG,          SUPER_EFFECTIVE
	db FLYING,       ROCK,         NOT_VERY_EFFECTIVE
	db FLYING,       STEEL,        NOT_VERY_EFFECTIVE
	bossai_type_group PSYCHIC_TYPE
	db PSYCHIC_TYPE, FIGHTING,     SUPER_EFFECTIVE
	db PSYCHIC_TYPE, PSYCHIC_TYPE, NOT_VERY_EFFECTIVE
	db PSYCHIC_TYPE, DARK,         NO_EFFECT
	db PSYCHIC_TYPE, STEEL,        NOT_VERY_EFFECTIVE
	bossai_type_group BUG
	db BUG,          FIRE,         NOT_VERY_EFFECTIVE
	db BUG,          GRASS,        SUPER_EFFECTIVE
	db BUG,          FIGHTING,     NOT_VERY_EFFECTIVE
	db BUG,          POISON,       NOT_VERY_EFFECTIVE
	db BUG,          FLYING,       NOT_VERY_EFFECTIVE
	db BUG,          PSYCHIC_TYPE, SUPER_EFFECTIVE
	db BUG,          GHOST,        NOT_VERY_EFFECTIVE
	db BUG,          DARK,         SUPER_EFFECTIVE
	db BUG,          STEEL,        NOT_VERY_EFFECTIVE
	bossai_type_group ROCK
	db ROCK,         FIRE,         SUPER_EFFECTIVE
	db ROCK,         ICE,          SUPER_EFFECTIVE
	db ROCK,         FIGHTING,     NOT_VERY_EFFECTIVE
	db ROCK,         GROUND,       NOT_VERY_EFFECTIVE
	db ROCK,         FLYING,       SUPER_EFFECTIVE
	db ROCK,         BUG,          SUPER_EFFECTIVE
	db ROCK,         STEEL,        NOT_VERY_EFFECTIVE
	db ROCK,         PSYCHIC_TYPE, NOT_VERY_EFFECTIVE
	bossai_type_group GHOST
	db GHOST,        NORMAL,       NO_EFFECT
	db GHOST,        PSYCHIC_TYPE, SUPER_EFFECTIVE
	db GHOST,        DARK,         NOT_VERY_EFFECTIVE
	db GHOST,        STEEL,        NO_EFFECT
	db GHOST,        GHOST,        SUPER_EFFECTIVE
	db GHOST,        FIGHTING,     SUPER_EFFECTIVE
	bossai_type_group DRAGON
	db DRAGON,       DRAGON,       SUPER_EFFECTIVE
	db DRAGON,       STEEL,        NOT_VERY_EFFECTIVE
	bossai_type_group DARK
	db DARK,         FIGHTING,     NOT_VERY_EFFECTIVE
	db DARK,         PSYCHIC_TYPE, SUPER_EFFECTIVE
	db DARK,         GHOST,        SUPER_EFFECTIVE
	db DARK,         DARK,         NOT_VERY_EFFECTIVE
	bossai_type_group STEEL
	db STEEL,        FIRE,         NOT_VERY_EFFECTIVE
	db STEEL,        WATER,        NOT_VERY_EFFECTIVE
	db STEEL,        ICE,          SUPER_EFFECTIVE
	db STEEL,        ROCK,         SUPER_EFFECTIVE
	db STEEL,        STEEL,        NOT_VERY_EFFECTIVE
	db STEEL,        FIGHTING,     NOT_VERY_EFFECTIVE

	db -2 ; end (with Foresight)

; Foresight removes Ghost's immunities.
	bossai_type_group NORMAL_FORESIGHT
	db NORMAL,       GHOST,        NO_EFFECT
	bossai_type_group FIGHTING_FORESIGHT
	db FIGHTING,     GHOST,        NO_EFFECT

	bossai_type_group END
	db -1 ; end
PURGE bossai_type_group
