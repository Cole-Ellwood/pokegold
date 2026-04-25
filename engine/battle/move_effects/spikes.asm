BattleCommand_Spikes:
	ld hl, wEnemyScreens
	ldh a, [hBattleTurn]
	and a
	jr z, .got_screens
	ld hl, wPlayerScreens
.got_screens

; Fails only if three layers are already down.

	ld a, [hl]
	and SCREENS_SPIKES_MASK
	cp 3
	jr nc, .failed

; Animate based on current layer count (0, 1, 2), then increment to 1..3 layers.
	ld [wBattleAnimParam], a
	inc a
	ld b, a

	ld a, [hl]
	and SCREENS_NON_SPIKES_MASK
	or b
	ld [hl], a

	call AnimateCurrentMove

	ld hl, SpikesText
	jp StdBattleTextbox

.failed
	jp FailMove
