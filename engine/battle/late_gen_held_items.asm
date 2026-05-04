ApplyLateGenDamageStatsItemMods_Far::
; Reach via ROM0 thunk ApplyLateGenDamageStatsItemMods — direct callfar
; would clobber hl (the input/output attack stat) with this function's address.
;
; push/pop de preserves caller's d = move BP across the boost helpers, which
; clobber d via `ld d, *_DEN` to set up the denominator parameter for
; .ApplyFractionToHL/BC. PlayerAttackDamage / EnemyAttackDamage carry d=BP
; through .done into this chain and damagecalc consumes it; without the
; preservation, Choice Band / Choice Specs / Assault Vest / Eviolite holders
; propagate d=2 (the *_DEN value) into damagecalc, dealing roughly 1/30 of
; intended damage. Latent since 80c2d5c6, masked previously by GetUserItem's
; own d-clobber (fixed 44ca3b29).
	push af
	push de
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
	jr nc, .special
	call .ApplyChoiceBandBoost
	call .ApplyEvioliteDefenseBoost
	jr .done

.special
	call .ApplyChoiceSpecsBoost
	call .ApplyAssaultVestBoostToDefense
	call .ApplyEvioliteSpDefBoost

.done
	pop de
	pop af
	ret

.ApplyChoiceBandBoost:
	ld a, HELD_CHOICE_BAND
	call _CheckUserItemEquals
	ret nz
	ld a, CHOICE_STAT_NUM
	ld d, CHOICE_STAT_DEN
	jp .ApplyFractionToHL

.ApplyChoiceSpecsBoost:
	ld a, HELD_CHOICE_SPECS
	call _CheckUserItemEquals
	ret nz
	ld a, CHOICE_STAT_NUM
	ld d, CHOICE_STAT_DEN
	jp .ApplyFractionToHL

.ApplyAssaultVestBoostToDefense:
	ld a, HELD_ASSAULT_VEST
	call _CheckOpponentItemEquals
	ret nz
	ld a, ASSAULT_VEST_SPD_NUM
	ld d, ASSAULT_VEST_SPD_DEN
	jp .ApplyFractionToBC

.ApplyEvioliteDefenseBoost:
	ld a, HELD_EVOLITE
	call _CheckOpponentItemEquals
	ret nz
	call .GetOpponentSpecies
	call .SpeciesCanEvolve
	ret z
	ld a, EVOLITE_DEF_NUM
	ld d, EVOLITE_DEF_DEN
	jp .ApplyFractionToBC

.ApplyEvioliteSpDefBoost:
	ld a, HELD_EVOLITE
	call _CheckOpponentItemEquals
	ret nz
	call .GetOpponentSpecies
	call .SpeciesCanEvolve
	ret z
	ld a, EVOLITE_SPD_NUM
	ld d, EVOLITE_SPD_DEN
	jp .ApplyFractionToBC

.GetOpponentSpecies:
	ldh a, [hBattleTurn]
	and a
	ld a, [wEnemyMonSpecies]
	ret z
	ld a, [wBattleMonSpecies]
	ret

.SpeciesCanEvolve:
	and a
	ret z
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	ret

.ApplyFractionToHL:
	push bc
	ld b, h
	ld c, l
	call .ApplyFractionToBC
	ld h, b
	ld l, c
	pop bc
	ret

.ApplyFractionToBC:
; a = numerator, d = denominator, bc = value
	push hl
	push de
	ld e, a
	xor a
	ldh [hMultiplicand + 0], a
	ld a, b
	ldh [hMultiplicand + 1], a
	ld a, c
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
	pop hl
	ret

ApplyLateGenDamageMultipliers_Far:
	callfar GetUserItem
	ld a, b
	and a
	ret z

	cp HELD_MUSCLE_BAND
	jr z, .muscle_band
	cp HELD_WISE_GLASSES
	jr z, .wise_glasses
	cp HELD_EXPERT_BELT
	jr z, .expert_belt
	cp HELD_METRONOME
	jr z, .metronome
	cp HELD_LIFE_ORB
	jr z, .life_orb
	ret

.muscle_band
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
	ret nc
	ld a, MUSCLE_BAND_NUM
	ld d, MUSCLE_BAND_DEN
	jp .ApplyDamageQuotientMultiplier

.wise_glasses
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
	ret c
	ld a, WISE_GLASSES_NUM
	ld d, WISE_GLASSES_DEN
	jp .ApplyDamageQuotientMultiplier

.expert_belt
	push bc
	push de
	ldh a, [hQuotient + 0]
	ld b, a
	ldh a, [hQuotient + 1]
	ld c, a
	ldh a, [hQuotient + 2]
	ld d, a
	ldh a, [hQuotient + 3]
	ld e, a
	push bc
	push de
	callfar BattleCheckTypeMatchup
	pop de
	pop bc
	ld a, b
	ldh [hQuotient + 0], a
	ld a, c
	ldh [hQuotient + 1], a
	ld a, d
	ldh [hQuotient + 2], a
	ld a, e
	ldh [hQuotient + 3], a
	pop de
	pop bc
	ld a, [wTypeMatchup]
	cp EFFECTIVE + 1
	ret c
	ld a, EXPERT_BELT_NUM
	ld d, EXPERT_BELT_DEN
	jp .ApplyDamageQuotientMultiplier

.metronome
	call .GetUserMetronomeCount
	add a
	add METRONOME_STEP_DEN
	cp METRONOME_MAX_MULT_NUM + 1
	jr c, .metronome_num_ok
	ld a, METRONOME_MAX_MULT_NUM
.metronome_num_ok
	ld d, METRONOME_MAX_MULT_DEN
	jp .ApplyDamageQuotientMultiplier

.life_orb
	ld a, LIFE_ORB_DAMAGE_NUM
	ld d, LIFE_ORB_DAMAGE_DEN
	jp .ApplyDamageQuotientMultiplier

.GetUserMetronomeCount:
	ld hl, wPlayerMetronomeCount
	ld de, wEnemyMetronomeCount
	call _GetSidedHL
	ld a, [hl]
	ret

.ApplyDamageQuotientMultiplier:
; a = numerator, d = denominator
	push de
	ldh [hMultiplier], a
	xor a
	ldh [hMultiplicand + 0], a
	ldh a, [hQuotient + 2]
	ldh [hMultiplicand + 1], a
	ldh a, [hQuotient + 3]
	ldh [hMultiplicand + 2], a
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
	ret

HandleLateGenAfterHitEffects_Far:
	ld hl, wCurDamage
	ld a, [hli]
	or [hl]
	ret z

	call FocusPunch_TryBreak_Far
	call .MaybePopAirBalloon
	call .MaybeApplyRockyHelmetRecoil

	call .UserStillAlive
	ret z

	call .MaybeApplyShellBellHeal
	call .UserStillAlive
	ret z
	call .MaybeApplyLifeOrbRecoil
	ret

.MaybePopAirBalloon:
	ld a, HELD_AIR_BALLOON
	call _CheckOpponentItemEquals
	ret nz
	call .ClearOpponentHeldItem
	ld hl, BattleText_AirBalloonPopped
	jp StdBattleTextbox

.MaybeApplyRockyHelmetRecoil:
; Skip if the contact landed on the holder's Substitute — the Sub absorbed
; the hit, the attacker never touched the Helmet.
	ld a, HELD_ROCKY_HELMET
	call _CheckOpponentItemEquals
	ret nz
	call TypePassive_IsCurrentMoveContact_Far
	ret nc
	ld a, BATTLE_VARS_SUBSTATUS4_OPP
	farcall GetBattleVar
	bit SUBSTATUS_SUBSTITUTE, a
	ret nz
	ld a, ROCKY_HELMET_DEN
	call .GetUserMaxHPDividedByA
	ld a, b
	or c
	jr nz, .recoil_ready
	inc c
.recoil_ready
	callfar SubtractHPFromUser
	ld hl, BattleText_RockyHelmetHurt
	jp StdBattleTextbox

.MaybeApplyShellBellHeal:
	ld a, HELD_SHELL_BELL
	call _CheckUserItemEquals
	ret nz
	ld hl, wCurDamage
	ld b, [hl]
	inc hl
	ld c, [hl]
	srl b
	rr c
	srl b
	rr c
	srl b
	rr c
	ld a, b
	or c
	jr nz, .heal_ready
	inc c
.heal_ready
	call .HealUserByBC
	ret

.MaybeApplyLifeOrbRecoil:
	ld a, HELD_LIFE_ORB
	call _CheckUserItemEquals
	ret nz
	ld a, LIFE_ORB_RECOIL_DEN
	call .GetUserMaxHPDividedByA
	ld a, b
	or c
	jr nz, .do_recoil
	inc c
.do_recoil
	callfar SubtractHPFromUser
	ld a, LIFE_ORB
	ld [wNamedObjectIndex], a
	call GetItemName
	ld hl, BattleText_UsersHurtByStringBuffer1
	jp StdBattleTextbox

.UserStillAlive:
	ld hl, wBattleMonHP
	ld de, wEnemyMonHP
	call _GetSidedHL
	ld a, [hli]
	or [hl]
	ret

.GetUserMaxHPDividedByA:
; a = denominator, returns bc = floor(maxhp / denominator)
	push af
	callfar GetMaxHP
	pop af
	jp .DivideBCByA

.DivideBCByA:
; a = denominator, bc = value, returns bc = floor(value / a)
	push de
	ld d, a
	xor a
	ldh [hDividend + 0], a
	ld a, b
	ldh [hDividend + 1], a
	ld a, c
	ldh [hDividend + 2], a
	ld a, d
	ldh [hDivisor], a
	ld b, 3
	call Divide
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
	pop de
	ret

.HealUserByBC:
	callfar BattleCommand_SwitchTurn
	callfar RestoreHP
	callfar BattleCommand_SwitchTurn
	ret

.ClearOpponentHeldItem:
	push hl
	push bc
	push de
	ldh a, [hBattleTurn]
	and a
	ld hl, wEnemyMonItem
	ld de, wOTPartyMon1Item
	ld a, [wCurOTMon]
	jr z, .got_side
	ld hl, wBattleMonItem
	ld de, wPartyMon1Item
	ld a, [wCurBattleMon]
.got_side
	ld c, a
	xor a
	ld [hl], a
	ld h, d
	ld l, e
	ld a, c
	call GetPartyLocation
	ldh a, [hBattleTurn]
	and a
	jr nz, .clear_party_item
	ld a, [wBattleMode]
	dec a
	jr z, .done
.clear_party_item
	xor a
	ld [hl], a
.done
	pop de
	pop bc
	pop hl
	ret

FocusPunch_TryBreak_Far:
	ld a, [wAttackMissed]
	and a
	ret nz
	ld a, [wCurDamage]
	ld b, a
	ld a, [wCurDamage + 1]
	or b
	ret z
	ldh a, [hBattleTurn]
	and a
	jr z, .player_attacking
	ld a, [wCurPlayerMove]
	jr .got_target_move

.player_attacking
	ld a, [wCurEnemyMove]

.got_target_move
	cp FOCUS_PUNCH
	ret nz
	ld a, BATTLE_VARS_SUBSTATUS2_OPP
	call GetBattleVarAddr
	set SUBSTATUS_FOCUS_PUNCH, [hl]
	ret

FocusPunch_CheckLostFocus_Far:
	ld a, BATTLE_VARS_SUBSTATUS2
	call GetBattleVarAddr
	bit SUBSTATUS_FOCUS_PUNCH, [hl]
	ret z
	res SUBSTATUS_FOCUS_PUNCH, [hl]
	ld a, TRUE
	ld [wAttackMissed], a
	ld hl, LostFocusText
	call StdBattleTextbox
	ld a, [wBattleScriptBufferAddress]
	ld l, a
	ld a, [wBattleScriptBufferAddress + 1]
	ld h, a
	ld a, endmove_command
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ret

DittoMetalPowder_Far:
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
	ret nc
	ld a, MON_SPECIES
	call BattlePartyAttr
	ldh a, [hBattleTurn]
	and a
	ld a, [hl]
	jr nz, .got_species
	ld a, [wTempEnemyMonSpecies]

.got_species
	cp DITTO
	ret nz

	push bc
	callfar GetOpponentItem
	ld a, [hl]
	cp METAL_POWDER
	pop bc
	ret nz

	ld h, b
	ld l, c
	srl b
	rr c
	add hl, bc
	ld b, h
	ld c, l

	ld a, HIGH(MAX_STAT_VALUE)
	cp b
	jr c, .cap
	ret nz
	ld a, LOW(MAX_STAT_VALUE)
	cp c
	ret nc

.cap
	ld bc, MAX_STAT_VALUE
	ret

SpeciesItemBoost_Far::
; Return in hl the stat value at hl.
; If the attacking monster is species b or c and
; it's holding item d, double it.
; Reach via ROM0 thunk SpeciesItemBoost — direct callfar would clobber hl.
	ld a, [hli]
	ld l, [hl]
	ld h, a

	push hl
	ld a, MON_SPECIES
	call BattlePartyAttr

	ldh a, [hBattleTurn]
	and a
	ld a, [hl]
	jr z, .CompareSpecies
	ld a, [wTempEnemyMonSpecies]
.CompareSpecies:
	pop hl

	cp b
	jr z, .GetItemHeldEffect
	cp c
	ret nz

.GetItemHeldEffect:
	push hl
	callfar GetUserItem
	ld a, [hl]
	pop hl
	cp d
	ret nz

	sla l
	rl h

	ld a, HIGH(MAX_STAT_VALUE)
	cp h
	jr c, .cap
	ret nz
	ld a, LOW(MAX_STAT_VALUE)
	cp l
	ret nc

.cap
	ld hl, MAX_STAT_VALUE
	ret

EnemyHPPercentage:
	ld hl, wEnemyMonMaxHP
	ld a, [hli]
	ld b, [hl]
	ld c, 100
	and a
	jr z, .shift_done
.shift
	rra
	rr b
	srl c
	and a
	jr nz, .shift
.shift_done
	ld a, c
	ldh [hMultiplier], a
	call Multiply
	ld a, b
	ld b, 4
	ldh [hDivisor], a
	jp Divide

CheckDamageStatsCritical_Far:
; Return carry if boosted stats should be used in damage calculations.
; Unboosted stats should be used if the attack is a critical hit,
;  and the stage of the opponent's defense is higher than the user's attack.
	ld a, [wCriticalHit]
	and a
	scf
	ret z

	push bc
	ldh a, [hBattleTurn]
	and a
	jr nz, .enemy
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
; special
	ld a, [wPlayerSAtkLevel]
	ld b, a
	ld a, [wEnemySDefLevel]
	jr nc, .end
; physical
	ld a, [wPlayerAtkLevel]
	ld b, a
	ld a, [wEnemyDefLevel]
	jr .end

.enemy
	call TypePassive_GetEffectiveMoveCategory_Far
	cp SPECIAL
; special
	ld a, [wEnemySAtkLevel]
	ld b, a
	ld a, [wPlayerSDefLevel]
	jr nc, .end
; physical
	ld a, [wEnemyAtkLevel]
	ld b, a
	ld a, [wPlayerDefLevel]
.end
	cp b
	pop bc
	ret

EnforceEnemyHeldMoveRestrictions_Far:
	ld a, [wCurEnemyMove]
	cp $ff
	ret z
	and a
	ret z
	cp STRUGGLE
	ret z
	ld a, [wEnemyMonItem]
	ld b, a
	callfar GetItemHeldEffect
	ld e, b

	ld a, e
	call IsChoiceHeldEffect_Far
	jr z, .choice_item
	xor a
	ld [wEnemyChoiceLockedMove], a
	jr .assault_vest

.choice_item
	ld a, [wEnemyChoiceLockedMove]
	and a
	jr nz, .force_choice_move
	ld a, [wCurEnemyMove]
	ld [wEnemyChoiceLockedMove], a
	jr .assault_vest

.force_choice_move
	ld [wCurEnemyMove], a
	call .SyncEnemyMoveIndex
	jr c, .force_choice_struggle
	call .IsCurrentEnemyMoveUsable
	jr nc, .assault_vest
.force_choice_struggle
	ld a, STRUGGLE
	ld [wCurEnemyMove], a
	xor a
	ld [wCurEnemyMoveNum], a

.assault_vest
	ld a, e
	cp HELD_ASSAULT_VEST
	ret nz
	ld a, [wCurEnemyMove]
	call IsMoveBlockedByAssaultVest_Far
	ret nc
	call .FindEnemyUsableDamagingMove
	ret nc
	ld a, STRUGGLE
	ld [wCurEnemyMove], a
	xor a
	ld [wCurEnemyMoveNum], a
	ret

.SyncEnemyMoveIndex:
	ld hl, wEnemyMonMoves
	ld c, 0
	ld a, [wCurEnemyMove]
	ld d, a
.sync_loop
	ld a, [hli]
	cp d
	jr z, .sync_found
	inc c
	ld a, c
	cp NUM_MOVES
	jr nz, .sync_loop
	scf
	ret

.sync_found
	ld a, c
	ld [wCurEnemyMoveNum], a
	and a
	ret

.IsCurrentEnemyMoveUsable:
	ld a, [wCurEnemyMove]
	and a
	jr z, .choice_unusable
	cp $ff
	jr z, .choice_unusable
	ld b, a
	ld a, [wEnemyDisabledMove]
	cp b
	jr z, .choice_unusable
	ld a, [wCurEnemyMoveNum]
	ld c, a
	ld b, 0
	ld hl, wEnemyMonPP
	add hl, bc
	ld a, [hl]
	and PP_MASK
	jr z, .choice_unusable
	and a
	ret

.choice_unusable
	scf
	ret

.FindEnemyUsableDamagingMove:
	ld hl, wEnemyMonMoves
	ld de, wEnemyMonPP
	ld c, 0
.find_loop
	ld a, [hl]
	and a
	jr z, .find_next
	ld b, a
	ld a, [wEnemyDisabledMove]
	cp b
	jr z, .find_next
	ld a, [de]
	and PP_MASK
	jr z, .find_next
	ld a, b
	call IsMoveBlockedByAssaultVest_Far
	jr c, .find_next
	ld a, b
	ld [wCurEnemyMove], a
	ld a, c
	ld [wCurEnemyMoveNum], a
	and a
	ret

.find_next
	inc hl
	inc de
	inc c
	ld a, c
	cp NUM_MOVES
	jr nz, .find_loop
	scf
	ret

IsChoiceHeldEffect_Far:
	cp HELD_CHOICE_BAND
	ret z
	cp HELD_CHOICE_SPECS
	ret z
	cp HELD_CHOICE_SCARF
	ret

IsMoveBlockedByAssaultVest_Far:
	and a
	jr z, .blocked
	cp $ff
	jr z, .blocked
	cp SEISMIC_TOSS
	jr z, .allowed
	cp NIGHT_SHADE
	jr z, .allowed
	cp DRAGON_RAGE
	jr z, .allowed
	cp SONICBOOM
	jr z, .allowed
	cp PSYWAVE
	jr z, .allowed
	cp COUNTER
	jr z, .allowed
	cp BIDE
	jr z, .allowed
	dec a
	ld hl, Moves + MOVE_POWER
	ld bc, MOVE_LENGTH
	call AddNTimes
	ld a, BANK(Moves)
	call GetFarByte
	and a
	jr z, .blocked

.allowed
	and a
	ret

.blocked
	scf
	ret

GetSixthMaxHP_Far:
; output: bc
	push de
	callfar GetMaxHP
	ld a, 6
	ld d, a
	xor a
	ldh [hDividend + 0], a
	ld a, b
	ldh [hDividend + 1], a
	ld a, c
	ldh [hDividend + 2], a
	ld a, d
	ldh [hDivisor], a
	ld b, 3
	call Divide
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
	pop de
	ld a, b
	or c
	jr nz, .end
	inc c
.end
	ret

_CheckUserItemEquals:
; Input:  a = item-effect constant to check
; Output: zf set if user holds an item with that effect, nz otherwise
; Preserves hl, bc; clobbers a (still equals input on return)
	push hl
	push bc
	push af
	callfar GetUserItem
	jr _CheckItemEquals_finish

_CheckOpponentItemEquals:
; Input:  a = item-effect constant to check
; Output: zf set if opponent holds an item with that effect, nz otherwise
; Preserves hl, bc; clobbers a (still equals input on return)
	push hl
	push bc
	push af
	callfar GetOpponentItem
_CheckItemEquals_finish:
	pop af
	cp b
	pop bc
	pop hl
	ret
