HiddenPowerDamage:
; Override Hidden Power's type and power based on the user's DVs.

	ld hl, wBattleMonSpecies
	ld de, wEnemyMonSpecies
	call _GetSidedHL
	ld a, [hl]
	cp UNOWN
	jr nz, .regular_hidden_power

	call UnownHiddenPowerType
	ld d, 100
	jr .done

.regular_hidden_power
	ld hl, wBattleMonDVs
	ld de, wEnemyMonDVs
	call _GetSidedHL

; Power:
	ld d, 60

; Type:

	; Def & 3
	ld a, [hl]
	and %0011
	ld b, a

	; + (Atk & 3) << 2
	ld a, [hl]
	and %0011 << 4
	swap a
	sla a
	sla a
	or b

; Skip Normal
	inc a

; Skip Bird
	cp BIRD
	jr c, .done
	inc a

; Skip unused types
	cp UNUSED_TYPES
	jr c, .done
	add UNUSED_TYPES_END - UNUSED_TYPES

.done

; Overwrite the current move type.
	push af
	ld a, BATTLE_VARS_MOVE_TYPE
	call GetBattleVarAddr
	pop af
	ld [hl], a

; Get the rest of the damage formula variables
; based on the new type, but keep base power.
	ld a, d
	push af
	farcall BattleCommand_DamageStats ; damagestats
	pop af
	ld d, a
	ret

UnownHiddenPowerType:
	call CountUnownHiddenPowerWeaknesses
	ld a, b
	and a
	jr z, .fallback
	ld c, a

.random_weakness
	call BattleRandom
	and $f
	cp c
	jr nc, .random_weakness
	ld b, a

	ld hl, UnownHiddenPowerTypes
.pick_loop
	ld a, [hli]
	cp -1
	jr z, .fallback
	push hl
	push bc
	call CheckUnownHiddenPowerType
	cp SUPER_EFFECTIVE
	pop bc
	pop hl
	jr c, .pick_loop
	ld a, b
	and a
	jr z, .pick
	dec b
	jr .pick_loop

.pick
	dec hl
	ld a, [hl]
	ret

.fallback
	ld a, PSYCHIC_TYPE
	ret

CountUnownHiddenPowerWeaknesses:
	ld hl, UnownHiddenPowerTypes
	ld b, 0
.loop
	ld a, [hli]
	cp -1
	ret z
	push hl
	push bc
	call CheckUnownHiddenPowerType
	cp SUPER_EFFECTIVE
	pop bc
	pop hl
	jr c, .loop
	inc b
	jr .loop

CheckUnownHiddenPowerType:
	push af
	ld a, BATTLE_VARS_MOVE_TYPE
	call GetBattleVarAddr
	pop af
	ld [hl], a
	farcall BattleCheckTypeMatchup
	ld a, [wTypeMatchup]
	ret

UnownHiddenPowerTypes:
	db FIGHTING
	db FLYING
	db POISON
	db GROUND
	db ROCK
	db BUG
	db GHOST
	db STEEL
	db FIRE
	db WATER
	db GRASS
	db ELECTRIC
	db PSYCHIC_TYPE
	db ICE
	db DRAGON
	db DARK
	db -1
