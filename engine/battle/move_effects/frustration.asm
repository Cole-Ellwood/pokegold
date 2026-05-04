BattleCommand_FrustrationPower:
; push de preserves caller's e (= attacker level set by damagestats). The move
; script runs damagestats → frustrationpower → damagecalc, and damagecalc reads
; e as level. `ld de, wEnemyMonHappiness` and `_GetSidedHL` would otherwise
; leave e = LOW($D0FB) = $FB, propagating wrong level into damagecalc (~5x
; damage at level 50). LoadHappinessPower's `ld d, a` re-sets d=BP, so the d
; half of the saved value is intentionally discarded after the pop.
	push bc
	push de
	ld hl, wBattleMonHappiness
	ld de, wEnemyMonHappiness
	call _GetSidedHL
	ld a, $ff
	sub [hl]
	ldh [hMultiplicand + 2], a
	xor a
	ldh [hMultiplicand + 0], a
	ldh [hMultiplicand + 1], a
	ld a, 10
	ldh [hMultiplier], a
	call Multiply
	ld a, 25
	ldh [hDivisor], a
	ld b, 4
	call Divide

LoadHappinessPower:
	ldh a, [hQuotient + 3]
	and a
	jr nz, .done
	inc a
.done
	pop de
	ld d, a
	pop bc
	ret
