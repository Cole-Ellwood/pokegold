DefaultOptions:
; wOptions: fast text speed, forced Set battle style
	db TEXT_DELAY_FAST | (1 << BATTLE_SHIFT)
; wSaveFileExists: no
	db FALSE
; wTextboxFrame: frame 1
	db FRAME_1
; wTextboxFlags: use text speed
	db 1 << FAST_TEXT_DELAY_F
; wGBPrinterBrightness: GB Printer subsystem removed; reserved slot
	db 0
; wOptions2: menu account on
	db 1 << MENU_ACCOUNT

	db $00
	db $00
.End
	assert DefaultOptions.End - DefaultOptions == wOptionsEnd - wOptions
