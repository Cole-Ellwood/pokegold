GetTrainerClassName:
	ld hl, wRivalName
	ld a, c
	cp RIVAL1
	jr z, .rival

	ld [wCurSpecies], a
	ld a, TRAINER_NAME
	ld [wNamedObjectType], a
	call GetName
	ld de, wStringBuffer1
	ret

.rival
	ld de, wStringBuffer1
	push de
	ld bc, TRAINER_CLASS_NAME_LENGTH
	call CopyBytes
	pop de
	ret

GetOTName:
	ld hl, wOTPlayerName
	ld a, [wLinkMode]
	and a
	jr nz, .ok

	ld hl, wRivalName
	ld a, c
	cp RIVAL1
	jr z, .ok

	ld [wCurSpecies], a
	ld a, TRAINER_NAME
	ld [wNamedObjectType], a
	call GetName
	ld hl, wStringBuffer1

.ok
	ld bc, TRAINER_CLASS_NAME_LENGTH
	ld de, wOTClassName
	push de
	call CopyBytes
	pop de
	ret

GetTrainerAttributes:
	ld a, [wTrainerClass]
	ld c, a
	call GetOTName
	ld a, [wTrainerClass]
	dec a
	ld hl, TrainerClassAttributes + TRNATTR_ITEM1
	ld bc, NUM_TRAINER_ATTRIBUTES
	call AddNTimes
	ld de, wEnemyTrainerItem1
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	ld a, [hl]
	ld [wEnemyTrainerBaseReward], a
	call LoadBossAITier
	ret

INCLUDE "data/trainers/attributes.asm"

LoadBossAITier:
	call ClearBossAIState
	xor a
	ld [wBossAITier], a
	ld [wBossAITierWeightRow], a

	ld a, [wTrainerClass]
	and a
	ret z
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a

	ld hl, BossAITierMap
.loop
	ld a, [hli]
	and a
	jr z, .tier_done
	cp b
	jr nz, .next

	ld a, [hli]
	cp c
	jr nz, .skip_tier

	ld a, [hli]
	ld [wBossAITier], a
	; default weight row = tier - 1 (EARLY=0, MID=1, LATE=2); ramp map may override.
	dec a
	ld [wBossAITierWeightRow], a
	jr .tier_done

.skip_tier
	inc hl
	jr .loop

.next
	inc hl
	inc hl
	jr .loop

.tier_done
	ld a, [wBossAITier]
	and a
	ret z
	; b/c still hold class/id from tier lookup.
	ld hl, BossAITierRampMap
.ramp_loop
	ld a, [hli]
	and a
	ret z
	cp b
	jr nz, .ramp_next
	ld a, [hli]
	cp c
	jr nz, .ramp_skip
	ld a, [hl]
	ld [wBossAITierWeightRow], a
	ret

.ramp_skip
	inc hl
	jr .ramp_loop

.ramp_next
	inc hl
	inc hl
	jr .ramp_loop

ClearBossAIState:
	ld hl, wBossAITier
	ld bc, wBossAIStateEnd - wBossAITier
	xor a
	call ByteFill
	ret

INCLUDE "data/trainers/ai_tiers.asm"
INCLUDE "data/trainers/ai_haki_excluded.asm"
