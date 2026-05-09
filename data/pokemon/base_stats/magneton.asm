	db MAGNETON ; 082

	db  80, 100, 110,  80, 120,  50
	;   hp  atk  def  spd  sat  sdf

	db ELECTRIC, STEEL ; type
	db 60 ; catch rate
	db 161 ; base exp
	db NO_ITEM, METAL_COAT ; items
	db GENDER_UNKNOWN ; gender ratio
	db 100 ; unknown 1
	db 20 ; step cycles to hatch
	db 5 ; unknown 2
IF DEF(_GOLD)
	INCBIN "gfx/pokemon/magneton/front_gold.dimensions"
ELIF DEF(_SILVER)
	INCBIN "gfx/pokemon/magneton/front_silver.dimensions"
ENDC
	dw NULL, NULL ; unused (beta front/back pics)
	db GROWTH_MEDIUM_FAST ; growth rate
	dn EGG_MINERAL, EGG_MINERAL ; egg groups

	; tm/hm learnset
	tmhm CURSE, ROLLOUT, TOXIC, ZAP_CANNON, HIDDEN_POWER, HYPER_BEAM, PROTECT, RAIN_DANCE, ENDURE, FRUSTRATION, DRAGONBREATH, THUNDER, RETURN, DOUBLE_TEAM, SWAGGER, SLEEP_TALK, REST, FLASH
	; end
