BossAIHakiTauntMap:
; class, trainer id. Pointer rows below must stay in the same order.
	db MORTY, MORTY1
	db CHUCK, CHUCK1
	db JASMINE, JASMINE1
	db PRYCE, PRYCE1
	db CLAIR, CLAIR1

	db RIVAL1, RIVAL1_3_CHIKORITA
	db RIVAL1, RIVAL1_3_CYNDAQUIL
	db RIVAL1, RIVAL1_3_TOTODILE
	db RIVAL1, RIVAL1_4_CHIKORITA
	db RIVAL1, RIVAL1_4_CYNDAQUIL
	db RIVAL1, RIVAL1_4_TOTODILE
	db RIVAL1, RIVAL1_5_CHIKORITA
	db RIVAL1, RIVAL1_5_CYNDAQUIL
	db RIVAL1, RIVAL1_5_TOTODILE
	db RIVAL2, RIVAL2_1_CHIKORITA
	db RIVAL2, RIVAL2_1_CYNDAQUIL
	db RIVAL2, RIVAL2_1_TOTODILE
	db RIVAL2, RIVAL2_2_CHIKORITA
	db RIVAL2, RIVAL2_2_CYNDAQUIL
	db RIVAL2, RIVAL2_2_TOTODILE

	db EXECUTIVEM, EXECUTIVEM_1
	db EXECUTIVEM, EXECUTIVEM_2
	db EXECUTIVEM, EXECUTIVEM_3
	db EXECUTIVEM, EXECUTIVEM_4
	db EXECUTIVEF, EXECUTIVEF_1
	db EXECUTIVEF, EXECUTIVEF_2

	db WILL, WILL1
	db BRUNO, BRUNO1
	db KOGA, KOGA1
	db KAREN, KAREN1
	db CHAMPION, LANCE
	db BLUE, BLUE1
	db RED, RED1
	db 0 ; end

BossAIHakiTauntPointers:
	dw BossAIHakiTauntMortyText
	dw BossAIHakiTauntChuckText
	dw BossAIHakiTauntJasmineText
	dw BossAIHakiTauntPryceText
	dw BossAIHakiTauntClairText

	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText
	dw BossAIHakiTauntSilverText

	dw BossAIHakiTauntExecutiveText
	dw BossAIHakiTauntExecutiveText
	dw BossAIHakiTauntExecutiveText
	dw BossAIHakiTauntExecutiveText
	dw BossAIHakiTauntExecutiveText
	dw BossAIHakiTauntExecutiveText

	dw BossAIHakiTauntWillText
	dw BossAIHakiTauntBrunoText
	dw BossAIHakiTauntKogaText
	dw BossAIHakiTauntKarenText
	dw BossAIHakiTauntLanceText
	dw BossAIHakiTauntBlueText
	dw BossAIHakiTauntRedText

; Taunt text labels live in BANK(BattleText) (data/text/boss_ai_haki_taunts.asm)
; because StdBattleTextbox hardcodes that bank before calling PrintText.
