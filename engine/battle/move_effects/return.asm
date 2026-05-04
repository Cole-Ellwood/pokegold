BattleCommand_HappinessPower:
; push de preserves caller's e (= attacker level set by damagestats); see
; BattleCommand_FrustrationPower header for the full mechanism. Stack discipline
; must match LoadHappinessPower's pop de / pop bc exit.
	push bc
	push de
	ld hl, wBattleMonHappiness
	ld de, wEnemyMonHappiness
	call _GetSidedHL
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, [hl]
	ldh [hMultiplicand + 2], a
	ld a, 10
	ldh [hMultiplier], a
	call Multiply
	ld a, 25
	ldh [hDivisor], a
	ld b, 4
	call Divide
	jp LoadHappinessPower
