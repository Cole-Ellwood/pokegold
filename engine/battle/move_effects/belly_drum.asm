BattleCommand_BellyDrum:
	callfar GetHalfMaxHP
	callfar CheckUserHasEnoughHP
	jr nc, .failed

	push bc
	call BattleCommand_AttackUp2
	ld a, [wAttackMissed]
	and a
	jr nz, .failed_pop

	call AnimateCurrentMove
	pop bc
	callfar SubtractHPFromUser
	call UpdateUserInParty

rept MAX_STAT_LEVEL - BASE_STAT_LEVEL - 1
	call BattleCommand_AttackUp2
endr

	ld hl, BellyDrumText
	jp StdBattleTextbox

.failed_pop
	pop bc
.failed
	call AnimateFailedMove
	jp PrintButItFailed
