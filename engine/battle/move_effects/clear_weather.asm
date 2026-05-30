BattleCommand_ClearWeather:
; Rider effect on Gust, Whirlwind, and Haze: blows away any active weather.
; Skips on a missed move so a whiffed Gust/Whirlwind leaves the sky intact,
; and is a silent no-op when there is no weather, so it never makes its host
; move report a failure of its own.
	ld a, [wAttackMissed]
	and a
	ret nz

	ld a, [wBattleWeather]
	and a ; WEATHER_NONE
	ret z

	dec a ; WEATHER_RAIN/SUN/SANDSTORM -> 0/1/2
	ld c, a
	ld b, 0
	ld hl, .EndedMessages
	add hl, bc
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a

	xor a
	ld [wBattleWeather], a
	jp StdBattleTextbox

.EndedMessages:
; entries correspond to WEATHER_* constants past WEATHER_NONE
	dw BattleText_TheRainStopped
	dw BattleText_TheSunlightFaded
	dw BattleText_TheSandstormSubsided
