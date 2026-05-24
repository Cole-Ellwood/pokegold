DEF SAVE_FORMAT_VERSION_V2 EQU 2

DEF SAVEFILE_CURRENT_PRIMARY EQU $1
DEF SAVEFILE_CURRENT_BACKUP  EQU $2
DEF SAVEFILE_V2_PRIMARY      EQU $3
DEF SAVEFILE_V2_BACKUP       EQU $4

DEF V2_PLAYER_DATA1_SIZE EQU $0226
DEF V2_PLAYER_DATA2_SIZE EQU $01aa
DEF V2_PLAYER_DATA3_SIZE EQU $047d
DEF V2_CUR_MAP_DATA_SIZE EQU $0034
DEF V2_POKEMON_DATA_SIZE EQU $04df
DEF V2_GAME_DATA_SIZE    EQU $0d60

DEF V2_WPLAYERDATA1_OFF EQU $0000
DEF V2_WPLAYERDATA2_OFF EQU $0226
DEF V2_WGAMETIMECAP_OFF EQU $0049
DEF V2_WCURDAY_OFF EQU $0051
DEF V2_WOBJECTFOLLOW_LEADER_OFF EQU $0053
DEF V2_WCMDQUEUE_OFF EQU $0264
DEF V2_WMAPOBJECTS_OFF EQU $02a4
DEF V2_WUNUSEDREANCHORBGMAPFLAGS_OFF EQU $03c4
DEF V2_WTIMEOFDAYPAL_OFF EQU $03c7
DEF V2_WTIMEOFDAYPALFLAGS_OFF EQU $03cc
DEF V2_WPLAYERDATA3_OFF EQU $03d0
DEF V2_WWHICHREGISTEREDITEM_OFF EQU $04df
DEF V2_WTRADEFLAGS_OFF EQU $04e4
DEF V2_WMOOMOOBERRIES_OFF EQU $0506
DEF V2_WPOKECENTER2FSCENEID_OFF EQU $0516
DEF V2_WBOSSAITIER_OFF EQU $058a
DEF V2_WJOYPADDISABLE_OFF EQU $0719
DEF V2_WCURBOX_OFF EQU $071b
DEF V2_WBOXNAMES_OFF EQU $071e
DEF V2_WBIKEFLAGS_OFF EQU $079e
DEF V2_WCURMAPSCENESCRIPTPOINTER_OFF EQU $07a0
DEF V2_WDECOBED_OFF EQU $07b8
DEF V2_WTIMEREVENTSTARTDAY_OFF EQU $07cc
DEF V2_WFRUITTREEFLAGS_OFF EQU $07d0
DEF V2_WLUCKYNUMBERDAYTIMER_OFF EQU $07d6
DEF V2_WSPECIALPHONECALLID_OFF EQU $07da
DEF V2_WBUGCONTESTSTARTTIME_OFF EQU $07de
DEF V2_WSTEPCOUNT_OFF EQU $081c
DEF V2_WHAPPINESSSTEPCOUNT_OFF EQU $0820
DEF V2_WPARKBALLSREMAINING_OFF EQU $0822
DEF V2_WLUCKYNUMBERSHOWFLAG_OFF EQU $0846
DEF V2_WLUCKYIDNUMBER_OFF EQU $0848
DEF V2_WCURMAPDATA_OFF EQU $084d
DEF V2_WLASTSPAWNMAPGROUP_OFF EQU $085a
DEF V2_WWARPNUMBER_OFF EQU $085e
DEF V2_WPOKEMONDATA_OFF EQU $0881
DEF V2_WPOKEDEXCAUGHT_OFF EQU $0a43

DEF V2_BOX_NAMES_IN_PLAYERDATA3 EQU V2_WBOXNAMES_OFF - V2_WPLAYERDATA3_OFF

MACRO copy_v2_save_chunk
	ld hl, \1 + \2
	ld de, \3
	ld bc, \4 - \3
	call CopyBytes
ENDM

MACRO copy_v2_playerdata1_chunks
	copy_v2_save_chunk \1, V2_WPLAYERDATA1_OFF, wPlayerData1, wGameTimeCap
	copy_v2_save_chunk \1, V2_WGAMETIMECAP_OFF, wGameTimeCap, wCurDay
	copy_v2_save_chunk \1, V2_WCURDAY_OFF, wCurDay, wObjectFollow_Leader
	copy_v2_save_chunk \1, V2_WOBJECTFOLLOW_LEADER_OFF, wObjectFollow_Leader, wPlayerData1End
ENDM

MACRO copy_v2_playerdata2_chunks
	copy_v2_save_chunk \1, V2_WPLAYERDATA2_OFF, wPlayerData2, wCmdQueue
	copy_v2_save_chunk \1, V2_WCMDQUEUE_OFF, wCmdQueue, wMapObjects
	copy_v2_save_chunk \1, V2_WMAPOBJECTS_OFF, wMapObjects, wUnusedReanchorBGMapFlags
	copy_v2_save_chunk \1, V2_WUNUSEDREANCHORBGMAPFLAGS_OFF, wUnusedReanchorBGMapFlags, wTimeOfDayPal
	copy_v2_save_chunk \1, V2_WTIMEOFDAYPAL_OFF, wTimeOfDayPal, wTimeOfDayPalFlags
	copy_v2_save_chunk \1, V2_WTIMEOFDAYPALFLAGS_OFF, wTimeOfDayPalFlags, wPlayerData2End
ENDM

MACRO copy_v2_playerdata3_chunks
	copy_v2_save_chunk \1, V2_WPLAYERDATA3_OFF, wPlayerData3, wWhichRegisteredItem
	copy_v2_save_chunk \1, V2_WWHICHREGISTEREDITEM_OFF, wWhichRegisteredItem, wTradeFlags
	copy_v2_save_chunk \1, V2_WTRADEFLAGS_OFF, wTradeFlags, wMooMooBerries
	copy_v2_save_chunk \1, V2_WMOOMOOBERRIES_OFF, wMooMooBerries, wPokecenter2FSceneID
	copy_v2_save_chunk \1, V2_WPOKECENTER2FSCENEID_OFF, wPokecenter2FSceneID, wBossAITier
	copy_v2_save_chunk \1, V2_WBOSSAITIER_OFF, wBossAITier, wJoypadDisable
	copy_v2_save_chunk \1, V2_WJOYPADDISABLE_OFF, wJoypadDisable, wCurBox
	copy_v2_save_chunk \1, V2_WCURBOX_OFF, wCurBox, wCurBox + 1
	copy_v2_save_chunk \1, V2_WBIKEFLAGS_OFF, wBikeFlags, wCurMapSceneScriptPointer
	copy_v2_save_chunk \1, V2_WCURMAPSCENESCRIPTPOINTER_OFF, wCurMapSceneScriptPointer, wDecoBed
	copy_v2_save_chunk \1, V2_WDECOBED_OFF, wDecoBed, wTimerEventStartDay
	copy_v2_save_chunk \1, V2_WTIMEREVENTSTARTDAY_OFF, wTimerEventStartDay, wFruitTreeFlags
	copy_v2_save_chunk \1, V2_WFRUITTREEFLAGS_OFF, wFruitTreeFlags, wLuckyNumberDayTimer
	copy_v2_save_chunk \1, V2_WLUCKYNUMBERDAYTIMER_OFF, wLuckyNumberDayTimer, wSpecialPhoneCallID
	copy_v2_save_chunk \1, V2_WSPECIALPHONECALLID_OFF, wSpecialPhoneCallID, wBugContestStartTime
	copy_v2_save_chunk \1, V2_WBUGCONTESTSTARTTIME_OFF, wBugContestStartTime, wStepCount
	copy_v2_save_chunk \1, V2_WSTEPCOUNT_OFF, wStepCount, wHappinessStepCount
	copy_v2_save_chunk \1, V2_WHAPPINESSSTEPCOUNT_OFF, wHappinessStepCount, wParkBallsRemaining
	copy_v2_save_chunk \1, V2_WPARKBALLSREMAINING_OFF, wParkBallsRemaining, wLuckyNumberShowFlag
	copy_v2_save_chunk \1, V2_WLUCKYNUMBERSHOWFLAG_OFF, wLuckyNumberShowFlag, wLuckyIDNumber
	copy_v2_save_chunk \1, V2_WLUCKYIDNUMBER_OFF, wLuckyIDNumber, wPlayerData3End
ENDM

MACRO copy_v2_curmap_chunks
	copy_v2_save_chunk \1, V2_WCURMAPDATA_OFF, wCurMapData, wLastSpawnMapGroup
	copy_v2_save_chunk \1, V2_WLASTSPAWNMAPGROUP_OFF, wLastSpawnMapGroup, wWarpNumber
	copy_v2_save_chunk \1, V2_WWARPNUMBER_OFF, wWarpNumber, wCurMapDataEnd
ENDM

MACRO copy_v2_pokemon_chunks
	copy_v2_save_chunk \1, V2_WPOKEMONDATA_OFF, wPokemonData, wPokedexCaught
	copy_v2_save_chunk \1, V2_WPOKEDEXCAUGHT_OFF, wPokedexCaught, wPokemonDataEnd
ENDM

SaveMenu:
	call LoadStandardMenuHeader
	lb de, 4, 0
	farcall DisplayNormalContinueData
	call SpeechTextbox
	call UpdateSprites
	farcall SaveMenu_CopyTilemapAtOnce
	ld hl, WouldYouLikeToSaveTheGameText
	call SaveTheGame_yesorno
	jr nz, .refused
	call AskOverwriteSaveFile
	jr c, .refused
	call PauseGameLogic
	call SavingDontTurnOffThePower
	call ResumeGameLogic
	call ExitMenu
	and a
	ret

.refused
	call ExitMenu
	call ReloadPalettes
	farcall SaveMenu_CopyTilemapAtOnce
	scf
	ret

SaveAfterLinkTrade:
	call PauseGameLogic
	farcall StageRTCTimeForSave
	call SavePokemonData
	call SaveChecksum
	call SaveBackupPokemonData
	call SaveBackupChecksum
	farcall BackupPartyMonMail
	farcall SaveRTC
	call ResumeGameLogic
	ret

ChangeBoxSaveGame:
	push de
	ld hl, ChangeBoxSaveText
	call MenuTextbox
	call YesNoBox
	call ExitMenu
	jr c, .refused
	call AskOverwriteSaveFile
	jr c, .refused
	call PauseGameLogic
	call SaveBox
	pop de
	ld a, e
	ld [wCurBox], a
	call LoadBox
	call SavingDontTurnOffThePower
	call ResumeGameLogic
	and a
	ret
.refused
	pop de
	ret

Link_SaveGame:
	call AskOverwriteSaveFile
	jr c, .refused
	call PauseGameLogic
	call SavingDontTurnOffThePower
	call ResumeGameLogic
	and a

.refused
	ret

MoveMonWOMail_SaveGame:
	call PauseGameLogic
	push de
	call SaveBox
	pop de
	ld a, e
	ld [wCurBox], a
	call LoadBox
	call ResumeGameLogic
	ret

MoveMonWOMail_InsertMon_SaveGame:
	call PauseGameLogic
	push de
	call SaveBox
	pop de
	ld a, e
	ld [wCurBox], a
	ld a, SAVEFILE_CURRENT_PRIMARY
	ld [wSaveFileExists], a
	farcall StageRTCTimeForSave
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SaveChecksum
	call ValidateBackupSave
	call SaveBackupOptions
	call SaveBackupPlayerData
	call SaveBackupPokemonData
	call SaveBackupChecksum
	farcall BackupPartyMonMail
	farcall SaveRTC
	call LoadBox
	call ResumeGameLogic
	ld de, SFX_SAVE
	call PlaySFX
	ld c, 24
	call DelayFrames
	ret

StartMoveMonWOMail_SaveGame:
	ld hl, MoveMonWOMailSaveText
	call MenuTextbox
	call YesNoBox
	call ExitMenu
	jr c, .refused
	call AskOverwriteSaveFile
	jr c, .refused
	call PauseGameLogic
	call SavingDontTurnOffThePower
	call ResumeGameLogic
	and a
	ret

.refused
	scf
	ret

PauseGameLogic:
	ld a, TRUE
	ld [wGameLogicPaused], a
	ret

ResumeGameLogic:
	xor a ; FALSE
	ld [wGameLogicPaused], a
	ret

AddHallOfFameEntry:
	ld a, BANK(sHallOfFame)
	call OpenSRAM
	ld hl, sHallOfFame + HOF_LENGTH * (NUM_HOF_TEAMS - 1) - 1
	ld de, sHallOfFame + HOF_LENGTH * NUM_HOF_TEAMS - 1
	ld bc, HOF_LENGTH * (NUM_HOF_TEAMS - 1)
.loop
	ld a, [hld]
	ld [de], a
	dec de
	dec bc
	ld a, c
	or b
	jr nz, .loop
	ld hl, wHallOfFamePokemonList
	ld de, sHallOfFame
	ld bc, wHallOfFamePokemonListEnd - wHallOfFamePokemonList + 1
	call CopyBytes
	call CloseSRAM
	ret

SaveGameData:
	call _SaveGameData
	ret

AskOverwriteSaveFile:
	ld a, [wSaveFileExists]
	and a
	jr z, .erase
	call CompareLoadedAndSavedPlayerID
	jr z, .yoursavefile
	ld hl, AnotherSaveFileText
	call SaveTheGame_yesorno
	jr nz, .refused
	jr .erase

.yoursavefile
	ld hl, AlreadyASaveFileText
	call SaveTheGame_yesorno
	jr nz, .refused
	jr .ok

.erase
	call ErasePreviousSave

.ok
	and a
	ret

.refused
	scf
	ret

SaveTheGame_yesorno:
	ld b, BANK(WouldYouLikeToSaveTheGameText)
	call MapTextbox
	call LoadMenuTextbox
	lb bc, 0, 7
	call PlaceYesNoBox
	ld a, [wMenuCursorY]
	dec a
	call CloseWindow
	push af
	call ReloadPalettes
	pop af
	and a
	ret

CompareLoadedAndSavedPlayerID:
	ld a, BANK(sPlayerData)
	call OpenSRAM
	ld hl, sPlayerData + (wPlayerID - wPlayerData)
	ld a, [hli]
	ld c, [hl]
	ld b, a
	call CloseSRAM
	ld a, [wPlayerID]
	cp b
	ret nz
	ld a, [wPlayerID + 1]
	cp c
	ret

SavingDontTurnOffThePower:
	; Prevent joypad interrupts
	xor a
	ldh [hJoypadReleased], a
	ldh [hJoypadPressed], a
	ldh [hJoypadSum], a
	ldh [hJoypadDown], a
	; Save the text speed setting to the stack
	ld a, [wOptions]
	push af
	; Set the text speed to medium
	ld a, TEXT_DELAY_MED
	ld [wOptions], a
	; SAVING... DON'T TURN OFF THE POWER.
	ld hl, SavingDontTurnOffThePowerText
	call PrintText
	; Restore the text speed setting
	pop af
	ld [wOptions], a
	; Wait for 16 frames
	ld c, 16
	call DelayFrames
	call _SaveGameData
	; wait 32 frames
	ld c, 32
	call DelayFrames
	; copy the original text speed setting to the stack
	ld a, [wOptions]
	push af
	; set text speed to medium
	ld a, TEXT_DELAY_MED
	ld [wOptions], a
	; <PLAYER> saved the game!
	ld hl, SavedTheGameText
	call PrintText
	; restore the original text speed setting
	pop af
	ld [wOptions], a
	ld de, SFX_SAVE
	call WaitPlaySFX
	call WaitSFX
	; wait 30 frames
	ld c, 30
	call DelayFrames
	ret

_SaveGameData:
	ld a, TRUE
	ld [wSaveFileExists], a
	farcall StageRTCTimeForSave
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SaveBox
	call SaveChecksum
	call ValidateBackupSave
	call SaveBackupOptions
	call SaveBackupPlayerData
	call SaveBackupPokemonData
	call SaveBackupChecksum
	call UpdateStackTop
	farcall BackupPartyMonMail
	farcall SaveRTC
	ret

UpdateStackTop:
; sStackTop appears to be unused.
; It could have been used to debug stack overflow during saving.
	call FindStackTop
	ld a, BANK(sStackTop)
	call OpenSRAM
	ld a, [sStackTop + 0]
	ld e, a
	ld a, [sStackTop + 1]
	ld d, a
	or e
	jr z, .update
	ld a, e
	sub l
	ld a, d
	sbc h
	jr c, .done

.update
	ld a, l
	ld [sStackTop + 0], a
	ld a, h
	ld [sStackTop + 1], a

.done
	call CloseSRAM
	ret

FindStackTop:
; Find the furthest point that sp has traversed to.
; This is distinct from the current value of sp.
	ld hl, wStackBottom
.loop
	ld a, [hl]
	or a
	ret nz
	inc hl
	jr .loop

ErasePreviousSave:
	call EraseBoxes
	call EraseHallOfFame
	call EraseLinkBattleStats
	ld a, BANK(sStackTop)
	call OpenSRAM
	xor a
	ld [sStackTop + 0], a
	ld [sStackTop + 1], a
	call CloseSRAM
	ld a, $1
	ld [wSavedAtLeastOnce], a
	ret

EraseLinkBattleStats:
	ld a, BANK(sLinkBattleStats)
	call OpenSRAM
	ld hl, sLinkBattleStats
	ld bc, sLinkBattleStatsEnd - sLinkBattleStats
	xor a
	call ByteFill
	jp CloseSRAM

EraseHallOfFame:
	ld a, BANK(sHallOfFame)
	call OpenSRAM
	ld hl, sHallOfFame
	ld bc, sHallOfFameEnd - sHallOfFame
	xor a
	call ByteFill
	jp CloseSRAM

ValidateSave:
	ld a, BANK(sCheckValue1) ; aka BANK(sCheckValue2), BANK(sSaveFormatVersion)
	call OpenSRAM
	ld a, SAVE_CHECK_VALUE_1
	ld [sCheckValue1], a
	ld a, SAVE_CHECK_VALUE_2
	ld [sCheckValue2], a
	ld a, SAVE_FORMAT_VERSION
	ld [sSaveFormatVersion], a
	jp CloseSRAM

SaveOptions:
	ld a, BANK(sOptions)
	call OpenSRAM
	ld hl, wOptions
	ld de, sOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	ld a, [wOptions]
	and ~(1 << NO_TEXT_SCROLL)
	ld [sOptions], a
	jp CloseSRAM

SavePlayerData:
	ld a, BANK(sPlayerData)
	call OpenSRAM
	ld hl, wPlayerData
	ld de, sPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	call CopyBytes
	ld hl, wCurMapData
	ld de, sCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call CopyBytes
	jp CloseSRAM

SavePokemonData:
	ld a, BANK(sPokemonData)
	call OpenSRAM
	ld hl, wPokemonData
	ld de, sPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call CopyBytes
	call CloseSRAM
	ret

SaveBox:
	call GetBoxAddress
	call SaveBoxAddress
	ret

SaveChecksum:
	ld hl, sGameData
	ld bc, sGameDataEnd - sGameData
	ld a, BANK(sGameData)
	call OpenSRAM
	call Checksum
	ld a, e
	ld [sChecksum + 0], a
	ld a, d
	ld [sChecksum + 1], a
	call CloseSRAM
	ret

ValidateBackupSave:
	ld a, BANK(sBackupCheckValue1) ; aka BANK(sBackupCheckValue2), BANK(sBackupSaveFormatVersion)
	call OpenSRAM
	ld a, SAVE_CHECK_VALUE_1
	ld [sBackupCheckValue1], a
	ld a, SAVE_CHECK_VALUE_2
	ld [sBackupCheckValue2], a
	ld a, SAVE_FORMAT_VERSION
	ld [sBackupSaveFormatVersion], a
	call CloseSRAM
	ret

SaveBackupOptions:
	ld a, BANK(sBackupOptions)
	call OpenSRAM
	ld hl, wOptions
	ld de, sBackupOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call CloseSRAM
	ret

SaveBackupPlayerData:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld hl, wPlayerData3
	ld de, sBackupPlayerData3
	ld bc, wPlayerData3End - wPlayerData3
	call CopyBytes
	ld a, BANK(sBackupPlayerData1)
	call OpenSRAM
	ld hl, wPlayerData1
	ld de, sBackupPlayerData1
	ld bc, wPlayerData1End - wPlayerData1
	call CopyBytes
	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	ld hl, wPlayerData2
	ld de, sBackupPlayerData2
	ld bc, wPlayerData2End - wPlayerData2
	call CopyBytes
	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	ld hl, wCurMapData
	ld de, sBackupCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call CopyBytes
	call CloseSRAM
	jp SaveBackupBoxNames

SaveBackupPokemonData:
	ld a, BANK(sBackupPokemonData)
	call OpenSRAM
	ld hl, wPokemonData
	ld de, sBackupPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call CopyBytes
	call CloseSRAM
	ret

SaveBackupChecksum:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld hl, sBackupPlayerData3
	ld bc, wPlayerData3End - wPlayerData3
	call Checksum
	push de
	ld hl, sBackupPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call Checksum
	pop hl
	add hl, de
	ld a, BANK(sBackupPlayerData1)
	call OpenSRAM
	push hl
	ld hl, sBackupPlayerData1
	ld bc, wPlayerData1End - wPlayerData1
	call Checksum
	pop hl
	add hl, de
	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	push hl
	ld hl, sBackupPlayerData2
	ld bc, wPlayerData2End - wPlayerData2
	call Checksum
	pop hl
	add hl, de
	push hl
	ld hl, sBackupBoxNames
	ld bc, BOX_NAME_LENGTH * NUM_BOXES
	call Checksum
	pop hl
	add hl, de
	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	push hl
	ld hl, sBackupCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call Checksum
	pop hl
	add hl, de
	ld a, l
	ld [sBackupChecksum + 0], a
	ld a, h
	ld [sBackupChecksum + 1], a
	call CloseSRAM
	ret

TryLoadSaveFile:
	ld a, [wSaveFileExists]
	cp SAVEFILE_V2_PRIMARY
	jr z, .primary_v2
	call VerifyChecksum
	jr nz, .backup
	call LoadPlayerData
	call LoadPokemonData
	call LoadBox
	farcall RestorePartyMonMail
	call ValidateBackupSave
	call SaveBackupOptions
	call SaveBackupPlayerData
	call SaveBackupPokemonData
	call SaveBackupChecksum
	and a
	ret

.primary_v2
	call VerifyChecksumV2
	jr nz, .backup
	; sBoxNames lands inside the old v2 PokemonData SRAM range, so copy the
	; old PokemonData out before LoadPlayerDataV2 migrates box names there.
	call LoadPokemonDataV2
	call LoadPlayerDataV2
	call LoadBox
	farcall RestorePartyMonMail
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SaveChecksum
	call ValidateBackupSave
	call SaveBackupOptions
	call SaveBackupPlayerData
	call SaveBackupPokemonData
	call SaveBackupChecksum
	and a
	ret

.backup
	xor a
	ld [wSaveFileExists], a
	call CheckBackupSaveFile
	ld a, [wSaveFileExists]
	and a
	jr z, .corrupt
	cp SAVEFILE_V2_BACKUP
	jr z, .backup_v2
	call VerifyBackupChecksum
	jr nz, .corrupt
	call LoadBackupPlayerData
	call LoadBackupPokemonData
	call LoadBox
	farcall RestorePartyMonMail
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SaveChecksum
	and a
	ret

.backup_v2
	call VerifyBackupChecksumV2
	jr nz, .corrupt
	call LoadBackupPlayerDataV2
	call LoadBackupPokemonDataV2
	call LoadBox
	farcall RestorePartyMonMail
	call ValidateSave
	call SaveOptions
	call SavePlayerData
	call SavePokemonData
	call SaveChecksum
	and a
	ret

.corrupt
	ld a, [wOptions]
	push af
	set NO_TEXT_SCROLL, a
	ld [wOptions], a
	ld hl, SaveFileCorruptedText
	call PrintText
	pop af
	ld [wOptions], a
	scf
	ret

TryLoadSaveData:
	xor a ; FALSE
	ld [wSaveFileExists], a
	call CheckPrimarySaveFile
	ld a, [wSaveFileExists]
	and a
	jr z, .backup

	ld a, BANK(sPlayerData)
	call OpenSRAM
	ld hl, sPlayerData + wStartDay - wPlayerData
	ld de, wStartDay
	ld bc, 14
	call CopyBytes
	call CloseSRAM
	ret

.backup
	call CheckBackupSaveFile
	ld a, [wSaveFileExists]
	and a
	jr z, .corrupt
	cp SAVEFILE_V2_BACKUP
	jr z, .backup_v2

	ld a, BANK(sBackupPlayerData1)
	call OpenSRAM
	ld hl, sBackupPlayerData1 + wStartDay - wPlayerData
	ld de, wStartDay
	ld bc, 14
	call CopyBytes
	call CloseSRAM
	ret

.backup_v2
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld hl, sBackupPlayerData3 + V2_PLAYER_DATA3_SIZE + V2_POKEMON_DATA_SIZE + wStartDay - wPlayerData
	ld de, wStartDay
	ld bc, 14
	call CopyBytes
	call CloseSRAM
	ret

.corrupt
	ld hl, DefaultOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call ClearClock
	ret

INCLUDE "data/default_options.asm"

CheckPrimarySaveFile:
	ld a, BANK(sCheckValue1) ; aka BANK(sCheckValue2), BANK(sSaveFormatVersion)
	call OpenSRAM
	ld a, [sCheckValue1]
	cp SAVE_CHECK_VALUE_1
	jr nz, .nope
	ld a, [sCheckValue2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .try_v2
	ld a, [sSaveFormatVersion]
	cp SAVE_FORMAT_VERSION
	jr z, .current_version
.try_v2
	ld a, [sGameData + V2_GAME_DATA_SIZE + 2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .nope
	ld a, [sGameData + V2_GAME_DATA_SIZE + 3]
	cp SAVE_FORMAT_VERSION_V2
	jr z, .v2_version
	jr nz, .nope
.v2_version
	ld hl, sOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call CloseSRAM
	call CheckTextDelay
	ld a, SAVEFILE_V2_PRIMARY
	ld [wSaveFileExists], a
	ret

.current_version
	ld hl, sOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call CloseSRAM
	call CheckTextDelay
	ld a, TRUE
	ld [wSaveFileExists], a
	ret

.nope
	call CloseSRAM
	ret

CheckBackupSaveFile:
	ld a, BANK(sBackupCheckValue1) ; aka BANK(sBackupCheckValue2), BANK(sBackupSaveFormatVersion)
	call OpenSRAM
	ld a, [sBackupCheckValue1]
	cp SAVE_CHECK_VALUE_1
	jr nz, .nope
	ld a, [sBackupCheckValue2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .try_v2
	ld a, [sBackupSaveFormatVersion]
	cp SAVE_FORMAT_VERSION
	jr z, .current_version
.try_v2
	ld a, [sBackupCurMapData + V2_CUR_MAP_DATA_SIZE + 2]
	cp SAVE_CHECK_VALUE_2
	jr nz, .nope
	ld a, [sBackupCurMapData + V2_CUR_MAP_DATA_SIZE + 3]
	cp SAVE_FORMAT_VERSION_V2
	jr z, .v2_version
	jr nz, .nope
.v2_version
	ld hl, sBackupOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call CheckTextDelay
	ld a, SAVEFILE_V2_BACKUP
	ld [wSaveFileExists], a
	call CloseSRAM
	ret

.current_version
	ld hl, sBackupOptions
	ld de, wOptions
	ld bc, wOptionsEnd - wOptions
	call CopyBytes
	call CheckTextDelay
	ld a, SAVEFILE_CURRENT_BACKUP
	ld [wSaveFileExists], a
	call CloseSRAM
	ret

.nope
	call CloseSRAM
	ret

CheckTextDelay:
; Fix options if text delay is invalid
	ld hl, wTextboxFlags
	res TEXT_DELAY_F, [hl]
	ld a, [wOptions]
	and TEXT_DELAY_MASK
	cp TEXT_DELAY_FAST
	ret z
	cp TEXT_DELAY_MED
	ret z
	cp TEXT_DELAY_SLOW
	ret z
	ld a, [wOptions]
	and ~TEXT_DELAY_MASK
	or (1 << FAST_TEXT_DELAY_F) | (1 << TEXT_DELAY_F)
	ld [wOptions], a
	ret

LoadPlayerData:
	ld a, BANK(sPlayerData)
	call OpenSRAM
	ld hl, sPlayerData
	ld de, wPlayerData
	ld bc, wPlayerDataEnd - wPlayerData
	call CopyBytes
	ld hl, sCurMapData
	ld de, wCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call CopyBytes
	call CloseSRAM
	ret

LoadPokemonData:
	ld a, BANK(sPokemonData)
	call OpenSRAM
	ld hl, sPokemonData
	ld de, wPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call CopyBytes
	call CloseSRAM
	ret

LoadBox:
	call GetBoxAddress
	call LoadBoxAddress
	ret

VerifyChecksum:
	ld hl, sGameData
	ld bc, sGameDataEnd - sGameData
	ld a, BANK(sGameData)
	call OpenSRAM
	call Checksum
	ld a, [sChecksum + 0]
	cp e
	jr nz, .fail
	ld a, [sChecksum + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

VerifyChecksumV2:
	ld hl, sGameData
	ld bc, V2_GAME_DATA_SIZE
	ld a, BANK(sGameData)
	call OpenSRAM
	call Checksum
	ld a, [sGameData + V2_GAME_DATA_SIZE + 0]
	cp e
	jr nz, .fail
	ld a, [sGameData + V2_GAME_DATA_SIZE + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

LoadPlayerDataV2:
	ld a, BANK(sGameData)
	call OpenSRAM
	copy_v2_playerdata1_chunks sGameData
	copy_v2_playerdata2_chunks sGameData
	copy_v2_playerdata3_chunks sGameData
	copy_v2_curmap_chunks sGameData
	ld hl, sGameData + V2_WBOXNAMES_OFF
	ld de, sBoxNames
	ld bc, BOX_NAME_LENGTH * NUM_BOXES
	call CopyBytes
	call CloseSRAM
	ret

LoadPokemonDataV2:
	ld a, BANK(sGameData)
	call OpenSRAM
	copy_v2_pokemon_chunks sGameData
	call CloseSRAM
	ret

LoadBackupPlayerDataV2:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	copy_v2_playerdata3_chunks (sBackupPlayerData3 - V2_WPLAYERDATA3_OFF)
	copy_v2_playerdata1_chunks (sBackupPlayerData3 + V2_PLAYER_DATA3_SIZE + V2_POKEMON_DATA_SIZE - V2_WPLAYERDATA1_OFF)
	call CloseSRAM

	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	copy_v2_playerdata2_chunks (sBackupPlayerData2 - V2_WPLAYERDATA2_OFF)
	call CloseSRAM

	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	copy_v2_curmap_chunks (sBackupCurMapData - V2_WCURMAPDATA_OFF)
	call CloseSRAM
	jp LoadBackupBoxNamesV2

LoadBackupPokemonDataV2:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	copy_v2_pokemon_chunks (sBackupPlayerData3 + V2_PLAYER_DATA3_SIZE - V2_WPOKEMONDATA_OFF)
	call CloseSRAM
	ret

LoadBackupBoxNamesV2:
	ld c, 0
.loop
	ld a, c
	push bc
	ld hl, sBackupPlayerData3 + V2_BOX_NAMES_IN_PLAYERDATA3
	ld bc, BOX_NAME_LENGTH
	call AddNTimes
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld de, wBoxNameBuffer
	ld bc, BOX_NAME_LENGTH
	call CopyBytes
	pop bc
	ld a, c
	push bc
	ld hl, sBoxNames
	ld bc, BOX_NAME_LENGTH
	call AddNTimes
	ld d, h
	ld e, l
	ld a, BANK(sBoxNames)
	call OpenSRAM
	ld hl, wBoxNameBuffer
	ld bc, BOX_NAME_LENGTH
	call CopyBytes
	pop bc
	inc c
	ld a, c
	cp NUM_BOXES
	jr c, .loop
	call CloseSRAM
	ret

VerifyBackupChecksumV2:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld hl, sBackupPlayerData3
	ld bc, V2_PLAYER_DATA3_SIZE
	call Checksum
	push de
	ld hl, sBackupPlayerData3 + V2_PLAYER_DATA3_SIZE
	ld bc, V2_POKEMON_DATA_SIZE
	call Checksum
	pop hl
	add hl, de
	push hl
	ld hl, sBackupPlayerData3 + V2_PLAYER_DATA3_SIZE + V2_POKEMON_DATA_SIZE
	ld bc, V2_PLAYER_DATA1_SIZE
	call Checksum
	pop hl
	add hl, de

	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	push hl
	ld hl, sBackupPlayerData2
	ld bc, V2_PLAYER_DATA2_SIZE
	call Checksum
	pop hl
	add hl, de

	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	push hl
	ld hl, sBackupCurMapData
	ld bc, V2_CUR_MAP_DATA_SIZE
	call Checksum
	pop hl
	add hl, de
	ld d, h
	ld e, l
	ld a, [sBackupCurMapData + V2_CUR_MAP_DATA_SIZE + 0]
	cp e
	jr nz, .fail
	ld a, [sBackupCurMapData + V2_CUR_MAP_DATA_SIZE + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

LoadBackupPlayerData:
	ld a, BANK(sBackupPlayerData3)
	call OpenSRAM
	ld hl, sBackupPlayerData3
	ld de, wPlayerData3
	ld bc, wPlayerData3End - wPlayerData3
	call CopyBytes

	ld a, BANK(sBackupPlayerData1)
	call OpenSRAM
	ld hl, sBackupPlayerData1
	ld de, wPlayerData1
	ld bc, wPlayerData1End - wPlayerData1
	call CopyBytes

	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	ld hl, sBackupPlayerData2
	ld de, wPlayerData2
	ld bc, wPlayerData2End - wPlayerData2
	call CopyBytes

	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	ld hl, sBackupCurMapData
	ld de, wCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call CopyBytes
	call CloseSRAM
	jp LoadBackupBoxNames

LoadBackupPokemonData:
	ld a, BANK(sBackupPokemonData)
	call OpenSRAM
	ld hl, sBackupPokemonData
	ld de, wPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call CopyBytes
	call CloseSRAM
	ret

SaveBackupBoxNames:
	assert BANK(sBoxNames) == BANK(sBackupBoxNames)
	ld a, BANK(sBoxNames)
	call OpenSRAM
	ld hl, sBoxNames
	ld de, sBackupBoxNames
	ld bc, BOX_NAME_LENGTH * NUM_BOXES
	call CopyBytes
	call CloseSRAM
	ret

LoadBackupBoxNames:
	assert BANK(sBoxNames) == BANK(sBackupBoxNames)
	ld a, BANK(sBoxNames)
	call OpenSRAM
	ld hl, sBackupBoxNames
	ld de, sBoxNames
	ld bc, BOX_NAME_LENGTH * NUM_BOXES
	call CopyBytes
	call CloseSRAM
	ret

VerifyBackupChecksum:
	ld a, BANK(sBackupPokemonData)
	call OpenSRAM
	ld hl, sBackupPokemonData
	ld bc, wPokemonDataEnd - wPokemonData
	call Checksum
	push de

	ld hl, sBackupPlayerData3
	ld bc, wPlayerData3End - wPlayerData3
	call Checksum
	pop hl
	add hl, de

	ld a, BANK(sBackupPlayerData1)
	call OpenSRAM
	push hl
	ld hl, sBackupPlayerData1
	ld bc, wPlayerData1End - wPlayerData1
	call Checksum
	pop hl
	add hl, de

	ld a, BANK(sBackupPlayerData2)
	call OpenSRAM
	push hl
	ld hl, sBackupPlayerData2
	ld bc, wPlayerData2End - wPlayerData2
	call Checksum
	pop hl
	add hl, de
	push hl
	ld hl, sBackupBoxNames
	ld bc, BOX_NAME_LENGTH * NUM_BOXES
	call Checksum
	pop hl
	add hl, de

	ld a, BANK(sBackupCurMapData)
	call OpenSRAM
	push hl
	ld hl, sBackupCurMapData
	ld bc, wCurMapDataEnd - wCurMapData
	call Checksum
	pop hl
	add hl, de
	ld d, h
	ld e, l
	ld a, [sBackupChecksum + 0]
	cp e
	jr nz, .fail
	ld a, [sBackupChecksum + 1]
	cp d
.fail
	push af
	call CloseSRAM
	pop af
	ret

GetBoxAddress:
	ld a, [wCurBox]
	cp NUM_BOXES
	jr c, .ok
	xor a
	ld [wCurBox], a

.ok
	ld e, a
	ld d, 0
	ld hl, BoxAddresses
rept 5
	add hl, de
endr
	ld a, [hli]
	push af
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop af
	ret

SaveBoxAddress:
; Save box via wBoxPartialData.
; We do this in three steps because the size of wBoxPartialData is less than
; the size of sBox.
	push hl
; Load the first part of the active box.
	push af
	push de
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, sBox
	ld de, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	pop de
	pop af
; Save it to the target box.
	push af
	push de
	call OpenSRAM
	ld hl, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM

; Load the second part of the active box.
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, sBox + (wBoxPartialDataEnd - wBoxPartialData)
	ld de, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	pop de
	pop af

	ld hl, (wBoxPartialDataEnd - wBoxPartialData)
	add hl, de
	ld e, l
	ld d, h
; Save it to the next part of the target box.
	push af
	push de
	call OpenSRAM
	ld hl, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM

; Load the third and final part of the active box.
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2
	ld de, wBoxPartialData
	ld bc, sBoxEnd - (sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2) ; $8e
	call CopyBytes
	call CloseSRAM
	pop de
	pop af

	ld hl, (wBoxPartialDataEnd - wBoxPartialData)
	add hl, de
	ld e, l
	ld d, h
; Save it to the final part of the target box.
	call OpenSRAM
	ld hl, wBoxPartialData
	ld bc, sBoxEnd - (sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2) ; $8e
	call CopyBytes
	call CloseSRAM

	pop hl
	ret

LoadBoxAddress:
; Load box via wBoxPartialData.
; We do this in three steps because the size of wBoxPartialData is less than
; the size of sBox.
	push hl
	ld l, e
	ld h, d
; Load part 1
	push af
	push hl
	call OpenSRAM
	ld de, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, wBoxPartialData
	ld de, sBox
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	pop hl
	pop af

	ld de, (wBoxPartialDataEnd - wBoxPartialData)
	add hl, de
; Load part 2
	push af
	push hl
	call OpenSRAM
	ld de, wBoxPartialData
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, wBoxPartialData
	ld de, sBox + (wBoxPartialDataEnd - wBoxPartialData)
	ld bc, (wBoxPartialDataEnd - wBoxPartialData)
	call CopyBytes
	call CloseSRAM
	pop hl
	pop af
; Load part 3
	ld de, (wBoxPartialDataEnd - wBoxPartialData)
	add hl, de
	call OpenSRAM
	ld de, wBoxPartialData
	ld bc, sBoxEnd - (sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2) ; $8e
	call CopyBytes
	call CloseSRAM
	ld a, BANK(sBox)
	call OpenSRAM
	ld hl, wBoxPartialData
	ld de, sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2
	ld bc, sBoxEnd - (sBox + (wBoxPartialDataEnd - wBoxPartialData) * 2) ; $8e
	call CopyBytes
	call CloseSRAM

	pop hl
	ret

EraseBoxes:
	ld hl, BoxAddresses
	ld c, NUM_BOXES
.next
	push bc
	ld a, [hli]
	call OpenSRAM
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	xor a
	ld [de], a
	inc de
	ld a, -1
	ld [de], a
	inc de
	ld bc, sBoxEnd - (sBox + 2)
.clear
	xor a
	ld [de], a
	inc de
	dec bc
	ld a, b
	or c
	jr nz, .clear
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	ld a, -1
	ld [de], a
	inc de
	xor a
	ld [de], a
	call CloseSRAM
	pop bc
	dec c
	jr nz, .next
	ret

BoxAddresses:
	table_width 5
for n, 1, NUM_BOXES + 1
	db BANK(sBox{d:n}) ; aka BANK(sBox{d:n}End)
	dw sBox{d:n}, sBox{d:n}End
endr
	assert_table_length NUM_BOXES

Checksum:
	ld de, 0
.loop
	ld a, [hli]
	add e
	ld e, a
	ld a, 0
	adc d
	ld d, a
	dec bc
	ld a, b
	or c
	jr nz, .loop
	ret

WouldYouLikeToSaveTheGameText:
	text_far _WouldYouLikeToSaveTheGameText
	text_end

SavingDontTurnOffThePowerText:
	text_far _SavingDontTurnOffThePowerText
	text_end

SavedTheGameText:
	text_far _SavedTheGameText
	text_end

AlreadyASaveFileText:
	text_far _AlreadyASaveFileText
	text_end

AnotherSaveFileText:
	text_far _AnotherSaveFileText
	text_end

SaveFileCorruptedText:
	text_far _SaveFileCorruptedText
	text_end

ChangeBoxSaveText:
	text_far _ChangeBoxSaveText
	text_end

MoveMonWOMailSaveText:
	text_far _MoveMonWOMailSaveText
	text_end
