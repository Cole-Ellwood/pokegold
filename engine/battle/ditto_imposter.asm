TryActivateDittoImposter:
	ld hl, wBattleMonHP
	ld de, wBattleMonSpecies
	ldh a, [hBattleTurn]
	and a
	jr z, .check_hp
	ld hl, wEnemyMonHP
	ld de, wEnemyMonSpecies
.check_hp
	ld a, [hli]
	or [hl]
	ret z

	ld a, [de]
	cp DITTO
	ret nz

	ld a, BATTLE_VARS_SUBSTATUS5_OPP
	callfar GetBattleVarAddr
	bit SUBSTATUS_TRANSFORMED, [hl]
	ret nz
	callfar CheckHiddenOpponent
	ret nz

	ld hl, DittoImposterActivatedText
	call StdBattleTextbox
	callfar BattleCommand_Transform
	ret
