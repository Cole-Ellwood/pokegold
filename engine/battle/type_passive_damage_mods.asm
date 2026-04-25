TypePassive_ApplyDamageModifiers_Far:
; Apply locked Type Passive V1 damage modifiers.
	ld hl, wCurDamage
	ld a, [hli]
	or [hl]
	ret z

	ld a, [wTypeModifier]
	bit STAB_DAMAGE_F, a
	jr z, .after_normal
	call .GetCurrentMoveType
	cp NORMAL
	jr nz, .after_normal
	ld a, NORMAL
	call .GetUserTypeContribution
	and a
	jr z, .after_normal
	cp 2
	ld a, 31
	ld d, 30
	jr nz, .apply_normal
	ld a, 16
	ld d, 15
.apply_normal
	call .ApplyCurDamageFraction

.after_normal
	call .GetCurrentMoveType
	cp FIRE
	jr nz, .after_fire
	call .IsUserBelowOneThirdHP
	jr nc, .after_fire
	ld a, FIRE
	call .GetUserTypeContribution
	and a
	jr z, .after_fire
	cp 2
	ld a, 11
	ld d, 10
	jr nz, .apply_fire
	ld a, 6
	ld d, 5
.apply_fire
	call .ApplyCurDamageFraction

.after_fire
	call .GetOpponentStatus
	and a
	jr z, .after_ghost
	ld a, GHOST
	call .GetUserTypeContribution
	and a
	jr z, .after_ghost
	cp 2
	ld a, 21
	ld d, 20
	jr nz, .apply_ghost
	ld a, 11
	ld d, 10
.apply_ghost
	call .ApplyCurDamageFraction

.after_ghost
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .after_dragon
	ld a, DRAGON
	call .GetUserTypeContribution
	and a
	jr z, .after_dragon
	cp 2
	ld a, 21
	ld d, 20
	jr nz, .apply_dragon
	ld a, 11
	ld d, 10
.apply_dragon
	call .ApplyCurDamageFraction

.after_dragon
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	jr c, .after_ground
	ld a, GROUND
	call .GetOpponentTypeContribution
	and a
	jr z, .after_ground
	cp 2
	ld a, 19
	ld d, 20
	jr nz, .apply_ground
	ld a, 9
	ld d, 10
.apply_ground
	call .ApplyCurDamageFraction

.after_ground
	ld a, [wCriticalHit]
	and a
	jr z, .after_rock
	ld a, ROCK
	call .GetOpponentTypeContribution
	and a
	jr z, .after_rock
	cp 2
	ld a, 19
	ld d, 20
	jr nz, .apply_rock
	ld a, 9
	ld d, 10
.apply_rock
	call .ApplyCurDamageFraction

.after_rock
	call .GetCurrentMoveType
	cp SPECIAL
	jr nc, .after_bug
	ld a, BUG
	call .GetOpponentTypeContribution
	and a
	jr z, .after_bug
	cp 2
	ld a, 19
	ld d, 20
	jr nz, .apply_bug
	ld a, 9
	ld d, 10
.apply_bug
	call .ApplyCurDamageFraction

.after_bug
	call .GetCurrentMoveType
	cp SPECIAL
	jr c, .after_water
	ld a, WATER
	call .GetOpponentTypeContribution
	and a
	jr z, .after_water
	cp 2
	ld a, 39
	ld d, 40
	jr nz, .apply_water
	ld a, 19
	ld d, 20
.apply_water
	call .ApplyCurDamageFraction

.after_water
	call .IsOpponentAboveHalfHP
	jr nc, .after_ice
	ld a, ICE
	call .GetOpponentTypeContribution
	and a
	jr z, .after_ice
	cp 2
	ld a, 39
	ld d, 40
	jr nz, .apply_ice
	ld a, 19
	ld d, 20
.apply_ice
	call .ApplyCurDamageFraction

.after_ice
	ret

.GetCurrentMoveType:
	ld hl, wPlayerMoveStruct + MOVE_TYPE
	ldh a, [hBattleTurn]
	and a
	jr z, .got_type
	ld hl, wEnemyMoveStruct + MOVE_TYPE
.got_type
	ld a, [hl]
	ret

.GetOpponentStatus:
	ld hl, wEnemyMonStatus
	ldh a, [hBattleTurn]
	and a
	jr z, .got_status
	ld hl, wBattleMonStatus
.got_status
	ld a, [hl]
	ret

.GetTypeContributionFromHL:
; input: a = type constant, hl -> type1/type2
; output: a = 0 (none), 1 (dual half), 2 (monotype full)
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	ld a, c
	cp b
	jr z, .full
	xor a
	ret

.dual
	ld a, c
	cp b
	jr z, .half
	ld a, [hl]
	cp b
	jr z, .half
	xor a
	ret

.half
	ld a, 1
	ret

.full
	ld a, 2
	ret

.GetUserTypeContribution:
	ld b, a
	ld hl, wBattleMonType1
	ldh a, [hBattleTurn]
	and a
	jr z, .got_user_types
	ld hl, wEnemyMonType1
.got_user_types
	ld a, b
	jr .GetTypeContributionFromHL

.GetOpponentTypeContribution:
	ld b, a
	ld hl, wEnemyMonType1
	ldh a, [hBattleTurn]
	and a
	jr z, .got_opp_types
	ld hl, wBattleMonType1
.got_opp_types
	ld a, b
	jr .GetTypeContributionFromHL

.ApplyCurDamageFraction:
; Fixed-point style ratio (Q8.8-like): floor(damage * numerator / denominator), min 1.
; input: a = numerator, d = denominator
	ld b, a
	ld hl, wCurDamage
	ld a, [hli]
	or [hl]
	ret z

	xor a
	ldh [hMultiplicand + 0], a
	ld a, [wCurDamage]
	ldh [hMultiplicand + 1], a
	ld a, [wCurDamage + 1]
	ldh [hMultiplicand + 2], a
	ld a, b
	ldh [hMultiplier], a
	call Multiply

	ldh a, [hProduct + 0]
	ldh [hDividend + 0], a
	ldh a, [hProduct + 1]
	ldh [hDividend + 1], a
	ldh a, [hProduct + 2]
	ldh [hDividend + 2], a
	ldh a, [hProduct + 3]
	ldh [hDividend + 3], a

	ld a, d
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 2]
	ld [wCurDamage], a
	ld b, a
	ldh a, [hQuotient + 3]
	ld [wCurDamage + 1], a
	or b
	ret nz
	ld a, 1
	ld [wCurDamage + 1], a
	ret

.GetUserHPAndMax:
	ld hl, wBattleMonHP
	ld de, wBattleMonMaxHP
	ldh a, [hBattleTurn]
	and a
	jr z, .got_user_hp
	ld hl, wEnemyMonHP
	ld de, wEnemyMonMaxHP
.got_user_hp
	ld a, [hli]
	ld b, a
	ld a, [hl]
	ld c, a
	ld a, [de]
	ld d, a
	inc de
	ld a, [de]
	ld e, a
	ret

.GetOpponentHPAndMax:
	ld hl, wEnemyMonHP
	ld de, wEnemyMonMaxHP
	ldh a, [hBattleTurn]
	and a
	jr z, .got_opp_hp
	ld hl, wBattleMonHP
	ld de, wBattleMonMaxHP
.got_opp_hp
	ld a, [hli]
	ld b, a
	ld a, [hl]
	ld c, a
	ld a, [de]
	ld d, a
	inc de
	ld a, [de]
	ld e, a
	ret

.IsUserBelowOneThirdHP:
; carry set if current HP is strictly below one-third max HP.
	call .GetUserHPAndMax
	ld h, b
	ld l, c
	add hl, bc
	add hl, bc
	jr c, .not_below
	ld a, h
	cp d
	jr c, .below
	jr nz, .not_below
	ld a, l
	cp e
	jr c, .below

.not_below
	and a
	ret

.below
	scf
	ret

.IsOpponentAboveHalfHP:
; carry set if current HP is strictly above half max HP.
	call .GetOpponentHPAndMax
	ld h, d
	ld l, e
	srl h
	rr l
	ld a, b
	cp h
	jr c, .not_above
	jr nz, .above
	ld a, c
	cp l
	jr c, .not_above
	jr z, .not_above

.above
	scf
	ret

.not_above
	and a
	ret

TypePassive_GetTypeContributionFromHL_Far:
; input: a = type constant, hl -> type1/type2
; output: a = 0 (none), 1 (dual half), 2 (monotype full)
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	ld a, c
	cp b
	jr z, .full
	xor a
	ret

.dual
	ld a, c
	cp b
	jr z, .half
	ld a, [hl]
	cp b
	jr z, .half
	xor a
	ret

.half
	ld a, 1
	ret

.full
	ld a, 2
	ret

TypePassive_GetUserTypesAddr_Far:
	ld hl, wBattleMonType1
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyMonType1
	ret

TypePassive_GetOpponentTypesAddr_Far:
	ld hl, wEnemyMonType1
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wBattleMonType1
	ret

TypePassive_GetUserTypeContribution_Far:
	ld b, a
	call TypePassive_GetUserTypesAddr_Far
	ld a, b
	jp TypePassive_GetTypeContributionFromHL_Far

TypePassive_GetOpponentTypeContribution_Far:
	ld b, a
	call TypePassive_GetOpponentTypesAddr_Far
	ld a, b
	jp TypePassive_GetTypeContributionFromHL_Far

TypePassive_GetCurrentMoveType_Far:
	ld hl, wPlayerMoveStruct + MOVE_TYPE
	ldh a, [hBattleTurn]
	and a
	jr z, .got_type
	ld hl, wEnemyMoveStruct + MOVE_TYPE
.got_type
	ld a, [hl]
	ret

TypePassive_GetCurrentMovePower_Far:
	ld hl, wPlayerMoveStruct + MOVE_POWER
	ldh a, [hBattleTurn]
	and a
	jr z, .got_power
	ld hl, wEnemyMoveStruct + MOVE_POWER
.got_power
	ld a, [hl]
	ret

TypePassive_GetCurrentMoveEffect_Far:
	ld hl, wPlayerMoveStruct + MOVE_EFFECT
	ldh a, [hBattleTurn]
	and a
	jr z, .got_effect
	ld hl, wEnemyMoveStruct + MOVE_EFFECT
.got_effect
	ld a, [hl]
	ret

TypePassive_IsCurrentMoveStatus_Far:
; return z if current move has 0 power (status category in this engine)
	call TypePassive_GetCurrentMovePower_Far
	and a
	ret

TypePassive_IsCurrentMoveContact_Far:
; return carry if current move makes contact.
	ld a, BATTLE_VARS_MOVE_ANIM
	farcall GetBattleVar
	and a
	jr z, .not_contact
	cp NUM_ATTACKS + 1
	jr nc, .not_contact
	dec a
	ld c, a
	ld b, 0
	ld hl, MoveContactFlags
	add hl, bc
	ld a, [hl]
	and a
	jr z, .not_contact
	scf
	ret

.not_contact
	and a
	ret

TypePassive_GetOpponentStatus_Far:
	ld hl, wEnemyMonStatus
	ldh a, [hBattleTurn]
	and a
	jr z, .got_status
	ld hl, wBattleMonStatus
.got_status
	ld a, [hl]
	ret

TypePassive_GetUserStatusAddr_Far:
	ld hl, wBattleMonStatus
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyMonStatus
	ret

TypePassive_IsOpponentSafeguarded_Far:
	ld hl, wEnemyScreens
	ldh a, [hBattleTurn]
	and a
	jr z, .got_screens
	ld hl, wPlayerScreens
.got_screens
	bit SCREENS_SAFEGUARD, [hl]
	ret

TypePassive_IsUserSafeguarded_Far:
	ld hl, wPlayerScreens
	ldh a, [hBattleTurn]
	and a
	jr z, .got_screens
	ld hl, wEnemyScreens
.got_screens
	bit SCREENS_SAFEGUARD, [hl]
	ret

TypePassive_GetTypeContributionFromDE_Far:
; input: a = type constant, de -> type1/type2
; output: a = 0 (none), 1 (dual half), 2 (monotype full)
	ld b, a
	ld a, [de]
	ld c, a
	inc de
	ld a, [de]
	cp c
	jr nz, .dual
	ld a, c
	cp b
	jr z, .full
	xor a
	ret

.dual
	ld a, c
	cp b
	jr z, .half
	ld a, [de]
	cp b
	jr z, .half
	xor a
	ret

.half
	ld a, 1
	ret

.full
	ld a, 2
	ret

TypePassive_ApplyFractionToStatAtHL_Far:
; Fixed-point style (Q8.8-like ratio): floor(stat * numerator / denominator), min 1.
; input: hl -> high byte of stat, a = numerator, d = denominator
	push de
	ld e, a
	xor a
	ldh [hMultiplicand + 0], a
	ld a, [hli]
	ldh [hMultiplicand + 1], a
	ld a, [hl]
	ldh [hMultiplicand + 2], a
	ld a, e
	ldh [hMultiplier], a
	call Multiply

	ldh a, [hProduct + 0]
	ldh [hDividend + 0], a
	ldh a, [hProduct + 1]
	ldh [hDividend + 1], a
	ldh a, [hProduct + 2]
	ldh [hDividend + 2], a
	ldh a, [hProduct + 3]
	ldh [hDividend + 3], a

	pop de
	ld a, d
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
	ld a, b
	or c
	jr nz, .store
	inc c

.store
	dec hl
	ld a, b
	ld [hli], a
	ld a, c
	ld [hl], a
	dec hl
	ret

TypePassive_GetOpponentDarkShieldFlagAddr_Far:
	ld hl, wEnemyDarkShieldConsumed
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wPlayerDarkShieldConsumed
	ret

TypePassive_GetUserParalysisFailThreshold_Far:
; Baseline 25%, Fighting half 20%, Fighting full 15%.
	ld a, FIGHTING
	call TypePassive_GetUserTypeContribution_Far
	and a
	ld a, 25 percent
	ret z
	cp 2
	ld a, 20 percent
	ret nz
	ld a, 15 percent
	ret

ApplyPrzEffectOnSpeed_Far:
; Uses Battle Core convention for hBattleTurn in status recalcs:
; nonzero = player, zero = enemy.
	ldh a, [hBattleTurn]
	and a
	jr z, .enemy
	ld hl, wBattleMonSpeed
	ld de, wBattleMonType1
	ld a, [wBattleMonStatus]
	jr .got_side

.enemy
	ld hl, wEnemyMonSpeed
	ld de, wEnemyMonType1
	ld a, [wEnemyMonStatus]

.got_side
	ld b, a

	push bc
	push de
	ld a, ELECTRIC
	call TypePassive_GetTypeContributionFromDE_Far
	pop de
	and a
	jr z, .check_paralysis
	cp 2
	ld a, 41
	ld d, 40
	jr nz, .apply_electric
	ld a, 21
	ld d, 20
.apply_electric
	call TypePassive_ApplyFractionToStatAtHL_Far

.check_paralysis
	pop bc
	bit PAR, b
	ret z

	push de
	ld a, FIGHTING
	call TypePassive_GetTypeContributionFromDE_Far
	pop de
	and a
	jr z, .default_paralysis
	cp 2
	ld a, 3
	ld d, 8
	jr nz, .apply_paralysis
	ld a, 1
	ld d, 2
	jr .apply_paralysis

.default_paralysis
	ld a, 1
	ld d, 4

.apply_paralysis
	call TypePassive_ApplyFractionToStatAtHL_Far
	ret

ApplyBrnEffectOnAttack_Far:
; Uses Battle Core convention for hBattleTurn in status recalcs:
; nonzero = player, zero = enemy.
	ldh a, [hBattleTurn]
	and a
	jr z, .enemy
	ld a, [wBattleMonStatus]
	bit BRN, a
	ret z
	ld hl, wBattleMonAttack
	ld de, wBattleMonType1
	jr .got_side

.enemy
	ld a, [wEnemyMonStatus]
	bit BRN, a
	ret z
	ld hl, wEnemyMonAttack
	ld de, wEnemyMonType1

.got_side
	push de
	ld a, FIGHTING
	call TypePassive_GetTypeContributionFromDE_Far
	pop de
	and a
	jr z, .default_burn
	cp 2
	ld a, 5
	ld d, 8
	jr nz, .apply_burn
	ld a, 3
	ld d, 4
	jr .apply_burn

.default_burn
	ld a, 1
	ld d, 2

.apply_burn
	call TypePassive_ApplyFractionToStatAtHL_Far
	ret

TypePassive_ApplyFlyingAccuracyBonusToB_Far:
; Flying full: x1.08 (27/25), Flying half: x1.04 (26/25).
; input: b = final accuracy after regular modifiers
	ld a, b
	cp $ff
	ret z
	ld e, b
	ld a, FLYING
	call TypePassive_GetUserTypeContribution_Far
	and a
	jr nz, .has_flying
	ld b, e
	ret

.has_flying
	cp 2
	ld a, 26
	jr nz, .got_num
	ld a, 27
.got_num
	ld d, a
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, e
	ldh [hMultiplicand + 2], a
	ld a, d
	ldh [hMultiplier], a
	call Multiply

	ldh a, [hProduct + 0]
	ldh [hDividend + 0], a
	ldh a, [hProduct + 1]
	ldh [hDividend + 1], a
	ldh a, [hProduct + 2]
	ldh [hDividend + 2], a
	ldh a, [hProduct + 3]
	ldh [hDividend + 3], a
	ld a, 25
	ldh [hDivisor], a
	ld b, 4
	call Divide
	ldh a, [hQuotient + 2]
	and a
	jr z, .in_range
	ld b, $ff
	ret

.in_range
	ldh a, [hQuotient + 3]
	ld b, a
	and a
	ret nz
	ld b, 1
	ret

TypePassive_IsDarkShieldEligibleEffect_Far:
; return nz only for opponent-targeting non-damaging effects.
	call TypePassive_GetCurrentMoveEffect_Far
	cp EFFECT_SLEEP
	jr z, .yes
	cp EFFECT_TOXIC
	jr z, .yes
	cp EFFECT_POISON
	jr z, .yes
	cp EFFECT_PARALYZE
	jr z, .yes
	cp EFFECT_CONFUSE
	jr z, .yes
	cp EFFECT_LEECH_SEED
	jr z, .yes
	cp EFFECT_DISABLE
	jr z, .yes
	cp EFFECT_ENCORE
	jr z, .yes
	cp EFFECT_SPITE
	jr z, .yes
	cp EFFECT_ATTRACT
	jr z, .yes
	cp EFFECT_MEAN_LOOK
	jr z, .yes
	cp EFFECT_NIGHTMARE
	jr z, .yes
	cp EFFECT_FORCE_SWITCH
	jr z, .yes
	cp EFFECT_ATTACK_DOWN
	jr z, .yes
	cp EFFECT_DEFENSE_DOWN
	jr z, .yes
	cp EFFECT_SPEED_DOWN
	jr z, .yes
	cp EFFECT_SP_ATK_DOWN
	jr z, .yes
	cp EFFECT_SP_DEF_DOWN
	jr z, .yes
	cp EFFECT_ACCURACY_DOWN
	jr z, .yes
	cp EFFECT_EVASION_DOWN
	jr z, .yes
	cp EFFECT_ATTACK_DOWN_2
	jr z, .yes
	cp EFFECT_DEFENSE_DOWN_2
	jr z, .yes
	cp EFFECT_SPEED_DOWN_2
	jr z, .yes
	cp EFFECT_SP_ATK_DOWN_2
	jr z, .yes
	cp EFFECT_SP_DEF_DOWN_2
	jr z, .yes
	cp EFFECT_ACCURACY_DOWN_2
	jr z, .yes
	cp EFFECT_EVASION_DOWN_2
	jr z, .yes
	xor a
	ret

.yes
	ld a, 1
	and a
	ret

TypePassive_StatusMoveLikelyAffectsOpponent_Far:
; return nz if this status move is likely to have effect on target.
	ld a, BATTLE_VARS_SUBSTATUS4_OPP
	farcall GetBattleVar
	bit SUBSTATUS_SUBSTITUTE, a
	jr nz, .blocked

	farcall BattleCheckTypeMatchup
	ld a, [wTypeMatchup]
	and a
	ret z

	call TypePassive_GetCurrentMoveEffect_Far
	cp EFFECT_SLEEP
	jr z, .needs_clear_status
	cp EFFECT_TOXIC
	jr z, .needs_clear_status
	cp EFFECT_POISON
	jr z, .needs_clear_status
	cp EFFECT_PARALYZE
	jr z, .needs_clear_status
	ld a, 1
	and a
	ret

.needs_clear_status
	call TypePassive_IsOpponentSafeguarded_Far
	jr nz, .blocked
	call TypePassive_GetOpponentStatus_Far
	and a
	jr nz, .blocked
	ld a, 1
	and a
	ret

.blocked
	xor a
	ret

TypePassive_TryDarkStatusShield_Far:
; return carry if the Dark shield negates this status move.
	call TypePassive_IsCurrentMoveStatus_Far
	ret nz
	call TypePassive_IsDarkShieldEligibleEffect_Far
	ret z

	ld a, DARK
	call TypePassive_GetOpponentTypeContribution_Far
	and a
	ret z
	ld b, a

	call TypePassive_GetOpponentDarkShieldFlagAddr_Far
	ld a, [hl]
	and a
	ret nz

	call TypePassive_StatusMoveLikelyAffectsOpponent_Far
	ret z

	ld [hl], 1
	ld a, b
	cp 2
	jr z, .negate
	call BattleRandom
	cp 50 percent
	ret nc

.negate
	scf
	ret

TypePassive_TryMindShield_Far:
; Psychic passive: chance for defender to take 0 damage but still register a hit.
	ld hl, wCurDamage
	ld a, [hli]
	or [hl]
	ret z

	call TypePassive_IsCurrentMoveStatus_Far
	ret z

	ld a, PSYCHIC_TYPE
	call TypePassive_GetOpponentTypeContribution_Far
	and a
	ret z
	cp 2
	ld b, 6
	jr nz, .roll
	ld b, 13
.roll
	call BattleRandom
	cp b
	ret nc

	xor a
	ld [wCurDamage], a
	ld [wCurDamage + 1], a
	ret

TypePassive_MaybePoisonRetaliation_Far:
; Poison passive: on contact damaging hit, defender may poison attacker.
	ld hl, wCurDamage
	ld a, [hli]
	or [hl]
	ret z

	call TypePassive_IsCurrentMoveContact_Far
	ret nc

	call TypePassive_IsCurrentMoveStatus_Far
	ret z

	ld a, POISON
	call TypePassive_GetOpponentTypeContribution_Far
	and a
	ret z
	cp 2
	ld c, 10 percent
	jr nz, .got_proc_threshold
	ld c, 20 percent
.got_proc_threshold

	call TypePassive_GetUserStatusAddr_Far
	ld a, [hl]
	and a
	ret nz

	call TypePassive_GetUserTypesAddr_Far
	ld a, [hli]
	cp POISON
	ret z
	cp STEEL
	ret z
	ld a, [hl]
	cp POISON
	ret z
	cp STEEL
	ret z

	farcall GetUserItem
	ld a, b
	cp HELD_PREVENT_POISON
	ret z

	call TypePassive_IsUserSafeguarded_Far
	ret nz

	call BattleRandom
	cp c
	ret nc

	call TypePassive_GetUserStatusAddr_Far
	set PSN, [hl]
	call UpdateUserInParty
	call RefreshBattleHuds
	ret

TypePassive_AdjustRecoilBCForSteel_Far:
; input/output: bc recoil amount
	ld a, STEEL
	call TypePassive_GetUserTypeContribution_Far
	and a
	ret z
	cp 2
	jr z, .no_recoil
	srl b
	rr c
	ret

.no_recoil
	xor a
	ld b, a
	ld c, a
	ret

TypePassive_GetUserHPPointers_Far:
; output: hl -> current HP, de -> max HP for current user side
	ld hl, wBattleMonHP
	ld de, wBattleMonMaxHP
	ldh a, [hBattleTurn]
	and a
	ret z
	ld hl, wEnemyMonHP
	ld de, wEnemyMonMaxHP
	ret

HandleTypePassiveRegrowth_Far:
	ldh a, [hSerialConnectionStatus]
	cp USING_EXTERNAL_CLOCK
	jr z, .DoEnemyFirst
	call SetPlayerTurn
	call .do_it
	call SetEnemyTurn
	jp .do_it

.DoEnemyFirst:
	call SetEnemyTurn
	call .do_it
	call SetPlayerTurn

.do_it
	ld a, GRASS
	call TypePassive_GetUserTypeContribution_Far
	ld d, a
	and a
	ret z

	call TypePassive_GetUserStatusAddr_Far
	ld a, [hl]
	and a
	ret nz

	call TypePassive_GetUserHPPointers_Far
	ld a, [hli]
	ld b, a
	ld a, [hl]
	ld c, a
	ld a, [de]
	cp b
	jr nz, .heal
	inc de
	ld a, [de]
	cp c
	ret z

.heal
	farcall GetMaxHP
	ld a, d
	cp 2
	ld a, 6
	jr nz, .shift
	ld a, 5
.shift
	call .ShiftBCByA_MinOne
	farcall SwitchTurnCore
	farcall RestoreHP
	ret

.ShiftBCByA_MinOne:
	ld e, a
.shift_loop
	srl b
	rr c
	dec e
	jr nz, .shift_loop
	ld a, b
	or c
	ret nz
	inc c
	ret

GetFailureResultText_Far:
	ld hl, DoesntAffectText
	ld de, DoesntAffectText
	ld a, [wTypeModifier]
	and EFFECTIVENESS_MASK
	jr z, .got_text
	ld a, BATTLE_VARS_MOVE_EFFECT
	farcall GetBattleVar
	cp EFFECT_FUTURE_SIGHT
	ld hl, ButItFailedText
	ld de, ItFailedText
	jr z, .got_text
	ld hl, AttackMissedText
	ld de, AttackMissed2Text
	ld a, [wCriticalHit]
	cp -1
	jr nz, .got_text
	ld hl, UnaffectedText
.got_text
	call FailText_CheckOpponentProtect_Far
	xor a
	ld [wCriticalHit], a

	ld a, BATTLE_VARS_MOVE_EFFECT
	farcall GetBattleVar
	cp EFFECT_JUMP_KICK
	ret nz

	ld a, [wTypeModifier]
	and EFFECTIVENESS_MASK
	ret z

	ld hl, wCurDamage
	ld a, [hli]
	ld b, [hl]
rept 3
	srl a
	rr b
endr
	ld [hl], b
	dec hl
	ld [hli], a
	or b
	jr nz, .do_at_least_1_damage
	inc a
	ld [hl], a
.do_at_least_1_damage
	ld hl, CrashedText
	call StdBattleTextbox
	ld a, $1
	ld [wBattleAnimParam], a
	farcall LoadMoveAnim
	ld c, TRUE
	ldh a, [hBattleTurn]
	and a
	jr nz, .do_enemy
	farcall DoPlayerDamage
	ret

.do_enemy
	farcall DoEnemyDamage
	ret

FailText_CheckOpponentProtect_Far:
	ld a, BATTLE_VARS_SUBSTATUS1_OPP
	farcall GetBattleVar
	bit SUBSTATUS_PROTECT, a
	jr z, .not_protected
	ld h, d
	ld l, e
.not_protected
	jp StdBattleTextbox

INCLUDE "data/moves/contact_flags.asm"
