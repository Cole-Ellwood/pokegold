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
	call LoadBossAIPersonalityKernel
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

; LoadBossAIPersonalityKernel
; Called after LoadBossAITier finishes tier/ramp resolution. Walks
; BossAIPersonalityKernelMap looking for trainer_class + trainer_id match;
; if none, falls back to the tier-default kernel. Copies 8 bytes into
; wBossAIKernel. On wBossAITier == 0 (non-boss), returns without writing.
;
; Inputs:  wBossAITier, wTrainerClass, wOtherTrainerID must be set first.
; Outputs: wBossAIKernel filled with BOSS_AI_KERNEL_SIZE bytes.
; Clobbers: a, b, c, d, e, h, l.
LoadBossAIPersonalityKernel:
	ld a, [wBossAITier]
	and a
	ret z ; non-boss trainer; scoring paths gated on wBossAITier anyway

	ld a, [wTrainerClass]
	ld b, a
	ld a, [wOtherTrainerID]
	ld c, a

	ld hl, BossAIPersonalityKernelMap
.map_loop
	ld a, [hl]
	and a
	jr z, .use_tier_default ; sentinel = end of per-leader entries
	cp b
	jr nz, .map_next
	inc hl
	ld a, [hli]
	cp c
	jr nz, .map_skip
	; HL now points at the 8-byte kernel record; copy to wBossAIKernel.
	ld de, wBossAIKernel
	ld b, BOSS_AI_KERNEL_SIZE
.copy_kernel
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_kernel
	ret

.map_skip
	; mid-entry mismatch on trainer_id; skip the 8 kernel bytes
	ld de, BOSS_AI_KERNEL_SIZE
	add hl, de
	jr .map_loop

.map_next
	; first byte didn't match trainer_class; skip class + id + 8 kernel bytes = 10
	ld de, 10
	add hl, de
	jr .map_loop

.use_tier_default
	; index into BossAITierDefaultKernels by (tier - 1) * BOSS_AI_KERNEL_SIZE
	ld a, [wBossAITier]
	dec a ; AI_TIER_EARLY (1) -> offset 0
	ld b, 0
	; multiply a by BOSS_AI_KERNEL_SIZE (8): shift left 3
	add a, a
	add a, a
	add a, a
	ld c, a
	ld hl, BossAITierDefaultKernels
	add hl, bc
	ld de, wBossAIKernel
	ld b, BOSS_AI_KERNEL_SIZE
.copy_default
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .copy_default
	ret

INCLUDE "data/trainers/ai_tiers.asm"
INCLUDE "data/boss_ai/personality_kernels.asm"
