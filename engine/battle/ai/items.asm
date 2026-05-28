AI_SwitchOrTryItem:
	and a

	ld a, [wBattleMode]
	dec a
	ret z

	ld a, [wLinkMode]
	and a
	ret nz

	farcall CheckEnemyLockedIn
	ret nz

	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_CANT_RUN, a
	jr nz, DontSwitch

	ld a, [wEnemyWrapCount]
	and a
	jr nz, DontSwitch

	ld a, [wBossAITier]
	and a
	jp nz, BossAI_TrySwitch

	ld a, [wTrainerClass]
	dec a
	ld hl, TrainerClassAttributes + TRNATTR_AI_ITEM_SWITCH
	ld bc, NUM_TRAINER_ATTRIBUTES
	call AddNTimes

	bit SWITCH_OFTEN_F, [hl]
	jp nz, SwitchOften
	bit SWITCH_RARELY_F, [hl]
	jp nz, SwitchRarely
	bit SWITCH_SOMETIMES_F, [hl]
	jp nz, SwitchSometimes
	; fallthrough

DontSwitch:
; Trainers in this hack don't use bag items. The vanilla "try item on stay"
; branch was deleted along with the AI item dispatcher in the boss-ai cleanup
; pass; this label remains as the shared "stay" landing for the switch helpers.
	ret

AI_CheckAbleToSwitchPreserveCurSpecies:
	ld a, [wCurSpecies]
	push af
	callfar CheckAbleToSwitch
	pop af
	ld [wCurSpecies], a
	and a
	call nz, GetBaseData
	ret

SwitchOften:
	call AI_CheckAbleToSwitchPreserveCurSpecies
	ld a, [wEnemySwitchMonParam]
	and $f0
	jp z, DontSwitch

	cp $10
	jr nz, .not_10
	call Random
	cp 50 percent + 1
	jr c, .switch
	jp DontSwitch
.not_10

	cp $20
	jr nz, .not_20
	call Random
	cp 79 percent - 1
	jr c, .switch
	jp DontSwitch
.not_20

	; $30
	call Random
	cp 4 percent
	jp c, DontSwitch

.switch
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	; In register 'a' is the number (1-6) of the mon to switch to
	ld [wEnemySwitchMonIndex], a
	jp AI_TrySwitch

SwitchRarely:
	call AI_CheckAbleToSwitchPreserveCurSpecies
	ld a, [wEnemySwitchMonParam]
	and $f0
	jp z, DontSwitch

	cp $10
	jr nz, .not_10
	call Random
	cp 8 percent
	jr c, .switch
	jp DontSwitch
.not_10

	cp $20
	jr nz, .not_20
	call Random
	cp 12 percent
	jr c, .switch
	jp DontSwitch
.not_20

	; $30
	call Random
	cp 79 percent - 1
	jp c, DontSwitch

.switch
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld [wEnemySwitchMonIndex], a
	jp AI_TrySwitch

SwitchSometimes:
	call AI_CheckAbleToSwitchPreserveCurSpecies
	ld a, [wEnemySwitchMonParam]
	and $f0
	jp z, DontSwitch

	cp $10
	jr nz, .not_10
	call Random
	cp 20 percent - 1
	jr c, .switch
	jp DontSwitch
.not_10

	cp $20
	jr nz, .not_20
	call Random
	cp 50 percent + 1
	jr c, .switch
	jp DontSwitch
.not_20

	; $30
	call Random
	cp 20 percent - 1
	jp c, DontSwitch

.switch
	ld a, [wEnemySwitchMonParam]
	and $f
	inc a
	ld [wEnemySwitchMonIndex], a
	jp AI_TrySwitch

AI_TrySwitch:
; Determine whether the AI can switch based on how many Pokemon are still alive.
; If it can switch, it will.
	ld a, [wOTPartyCount]
	ld c, a
	ld hl, wOTPartyMon1HP
	ld d, 0
.SwitchLoop:
	ld a, [hli]
	ld b, a
	ld a, [hld]
	or b
	jr z, .fainted
	inc d
.fainted
	push bc
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	dec c
	jr nz, .SwitchLoop

	ld a, d
	cp 2
	jp nc, AI_Switch
	and a
	ret

AI_Switch:
	callfar BossAI_OnSwitchExecuted
	ld a, $1
	ld [wEnemyIsSwitching], a
	ld [wEnemyGoesFirst], a
	ld hl, wEnemySubStatus4
	res SUBSTATUS_RAGE, [hl]
	xor a
	ldh [hBattleTurn], a
	callfar PursuitSwitch

	push af
	ld a, [wCurOTMon]
	ld hl, wOTPartyMon1Status
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	ld d, h
	ld e, l
	ld hl, wEnemyMonStatus
	ld bc, MON_MAXHP - MON_STATUS
	call CopyBytes
	pop af

	jr c, .skiptext
	ld hl, EnemyWithdrewText
	call PrintText

.skiptext
	ld a, 1
	ld [wBattleHasJustStarted], a
	callfar NewEnemyMonStatus
	callfar ResetEnemyStatLevels
	ld hl, wPlayerSubStatus1
	res SUBSTATUS_IN_LOVE, [hl]
	farcall EnemySwitch
	farcall ResetBattleParticipants
	xor a
	ld [wBattleHasJustStarted], a
	ld a, [wLinkMode]
	cp LINK_COLOSSEUM
	ret z
	scf
	ret

EnemyWithdrewText:
	text_far _EnemyWithdrewText
	text_end
