; Boolean checks
DEF FALSE EQU 0
DEF TRUE  EQU 1

; genders
DEF MALE   EQU 0
DEF FEMALE EQU 1

; input
DEF NO_INPUT EQU %00000000

; FlagAction arguments (see home/flag.asm)
	const_def
	const RESET_FLAG
	const SET_FLAG
	const CHECK_FLAG

; G/S version ID: 0 = Gold, 1 = Silver (used by checkver)
IF DEF(_GOLD)
DEF GS_VERSION EQU 0
ELIF DEF(_SILVER)
DEF GS_VERSION EQU 1
ENDC

; save file corruption check values
DEF SAVE_CHECK_VALUE_1 EQU 99
DEF SAVE_CHECK_VALUE_2 EQU 127

; Save layout version. Bump when any field under wPlayerData*/wPokemonData/
; wCurMapData/wOptions is added/removed/resized/reordered, or when the Save/
; Backup Save N SRAM sections are reorganized. $FF means "legacy save predating
; this marker" and is accepted only by v1 to absorb existing dev/playtest saves
; on first deploy. v2+ must NOT keep the $FF accept path; only the current
; version and explicitly-migrated previous versions are valid.
DEF SAVE_FORMAT_VERSION EQU 2

; RTC halted check value
DEF RTC_HALT_VALUE EQU $1234

; time of day boundaries
DEF MORN_HOUR EQU 4  ; 4 AM
DEF DAY_HOUR  EQU 10 ; 10 AM
DEF NITE_HOUR EQU 18 ; 6 PM
DEF NOON_HOUR EQU 12 ; 12 PM
DEF MAX_HOUR  EQU 24 ; 12 AM

; significant money values
DEF START_MONEY EQU 3000
DEF MOM_MONEY   EQU 2300
DEF MAX_MONEY   EQU 999999
DEF MAX_COINS   EQU 9999

; link record
DEF MAX_LINK_RECORD EQU 9999

; day-care
DEF MAX_DAY_CARE_EXP EQU $500000

; hall of fame
DEF HOF_MASTER_COUNT EQU 200

; card flip
DEF CARDFLIP_DECK_SIZE EQU 4 * 6

; SGB command MLT_REQ can be used to detect SGB hardware
DEF JOYP_SGB_MLT_REQ EQU %00000011
