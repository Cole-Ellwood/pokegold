TreeMons:
; entries correspond to TREEMON_SET_* constants
	table_width 2
	dw TreeMonSet_None
	dw TreeMonSet_Forest
	dw TreeMonSet_Canyon
	dw TreeMonSet_Rock
	dw TreeMonSet_Unused
	dw TreeMonSet_City
	assert_table_length NUM_TREEMON_SETS

; Two tables each (common, rare).
; Structure:
;	db  %, species, level

TreeMonSet_None:
TreeMonSet_Unused:
TreeMonSet_City:
	db -1
	db -1

TreeMonSet_Forest:

IF DEF(_GOLD)
; common
	db 50, CATERPIE,   10
	db 15, CATERPIE,   10
	db 15, METAPOD,    10
	db 10, EXEGGCUTE,  10
	db  5, EXEGGCUTE,  10
	db  5, METAPOD,    10
	db -1
; rare
	db 50, CATERPIE,   10
	db 15, PINECO,     10
	db 15, PINECO,     10
	db 10, EXEGGCUTE,  10
	db  5, EXEGGCUTE,  10
	db  5, METAPOD,    10
	db -1

ELIF DEF(_SILVER)
; common
	db 50, WEEDLE,     10
	db 15, WEEDLE,     10
	db 15, KAKUNA,     10
	db 10, EXEGGCUTE,  10
	db  5, EXEGGCUTE,  10
	db  5, KAKUNA,     10
	db -1
; rare
	db 50, WEEDLE,     10
	db 15, PINECO,     10
	db 15, PINECO,     10
	db 10, EXEGGCUTE,  10
	db  5, EXEGGCUTE,  10
	db  5, KAKUNA,     10
	db -1
ENDC

TreeMonSet_Canyon:
; common
	db 50, SPEAROW,    10
	db 15, SPEAROW,    10
	db 15, SPEAROW,    10
	db 10, AIPOM,      10
	db  5, AIPOM,      10
	db  5, AIPOM,      10
	db -1
; rare
	db 50, SPEAROW,    10
	db 15, HERACROSS,  10
	db 15, HERACROSS,  10
	db 10, AIPOM,      10
	db  5, AIPOM,      10
	db  5, AIPOM,      10
	db -1

TreeMonSet_Rock:
	db 90, KRABBY,     15
	db 10, SHUCKLE,    15
	db -1
