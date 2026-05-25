; Boss AI Haki taunt text.
; Must live in BANK(BattleText): BossAI_FlushPendingHakiTaunt jumps to
; StdBattleTextbox, which switches to BANK(BattleText) before calling
; PrintText. Pointer table (BossAIHakiTauntPointers) stays alongside the
; queue code in the Boss AI bank; only the text data lives here.

BossAIHakiTauntMortyText:
	text "Morty's grin"
	line "twitches."
	prompt

BossAIHakiTauntChuckText:
	text "Chuck steadies"
	line "his stance."
	prompt

BossAIHakiTauntJasmineText:
	text "Jasmine's eyes"
	line "harden."
	prompt

BossAIHakiTauntPryceText:
	text "Pryce breathes"
	line "slowly."
	prompt

BossAIHakiTauntClairText:
	text "Clair's glare"
	line "sharpens."
	prompt

BossAIHakiTauntSilverText:
	text "Silver's glare"
	line "burns."
	prompt

BossAIHakiTauntExecutiveText:
	text "The EXECUTIVE"
	line "goes still."
	prompt

BossAIHakiTauntWillText:
	text "Will lifts a"
	line "hand."
	prompt

BossAIHakiTauntBrunoText:
	text "Bruno plants"
	line "his feet."
	prompt

BossAIHakiTauntKogaText:
	text "Koga vanishes"
	line "for a blink."
	prompt

BossAIHakiTauntKarenText:
	text "Karen smiles"
	line "slowly."
	prompt

BossAIHakiTauntLanceText:
	text "Lance's eyes"
	line "narrow."
	prompt

BossAIHakiTauntBlueText:
	text "Blue's smirk"
	line "fades."
	prompt

BossAIHakiTauntRedText:
	text "…"
	prompt
