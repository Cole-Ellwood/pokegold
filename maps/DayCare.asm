object_const_def
	const DAYCARE_GRAMPS
	const DAYCARE_GRANNY
	const DAYCARE_TM_TUTOR
	const DAYCARE_MOVE_REMINDER

DEF DAYCARE_TM_TUTOR_UNLOCK_FEE EQU 1000

DayCare_MapScripts:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, DayCareEggCheckCallback

DayCareEggCheckCallback:
	checkflag ENGINE_DAY_CARE_MAN_HAS_EGG
	iftrue .PutDayCareManOutside
	clearevent EVENT_DAY_CARE_MAN_IN_DAY_CARE
	setevent EVENT_DAY_CARE_MAN_ON_ROUTE_34
	endcallback

.PutDayCareManOutside:
	setevent EVENT_DAY_CARE_MAN_IN_DAY_CARE
	clearevent EVENT_DAY_CARE_MAN_ON_ROUTE_34
	endcallback

DayCareManScript_Inside:
	faceplayer
	opentext
	special DayCareMan
	waitbutton
	closetext
	end

DayCareLadyScript:
	faceplayer
	opentext
	checkflag ENGINE_DAY_CARE_MAN_HAS_EGG
	iftrue .HusbandWasLookingForYou
	special DayCareLady
	waitbutton
	closetext
	end

.HusbandWasLookingForYou:
	writetext Text_GrampsLookingForYou
	waitbutton
	closetext
	end

DayCareTMTutorScript:
	faceplayer
	opentext
	checkevent EVENT_TM_TUTOR_UNLOCKED
	iftrue .Unlocked
	writetext DayCareTMTutorLockedIntroText
	yesorno
	iffalse .DeclinedUnlock
	checkmoney YOUR_MONEY, DAYCARE_TM_TUTOR_UNLOCK_FEE
	ifequal HAVE_LESS, .NotEnoughMoney
	takemoney YOUR_MONEY, DAYCARE_TM_TUTOR_UNLOCK_FEE
	special PlaceMoneyTopRight
	setevent EVENT_TM_TUTOR_UNLOCKED
	writetext DayCareTMTutorUnlockedText
	promptbutton

.Unlocked:
	readmem wTMTutorCredits
	ifgreater 0, .ShowCredits
	sjump .TryRedeemWhenEmpty

.ShowCredits:
	getnum STRING_BUFFER_3
	writetext DayCareTMTutorCreditsRemainingText
	promptbutton
	sjump .OfferLesson

.TryRedeemWhenEmpty:
	checkitem TM_VOUCHER
	iftrue .OfferRedeemVoucher
	writetext DayCareTMTutorNoCreditsText
	waitbutton
	closetext
	end

.OfferRedeemVoucher:
	writetext DayCareTMTutorRedeemVoucherText
	yesorno
	iffalse .Done
	takeitem TM_VOUCHER
	readmem wTMTutorCredits
	addval 3
	ifgreater 99, .ClampCredits
	writemem wTMTutorCredits
	sjump .ShowRedeemedCredits

.ClampCredits:
	setval 99
	writemem wTMTutorCredits

.ShowRedeemedCredits:
	readmem wTMTutorCredits
	getnum STRING_BUFFER_3
	writetext DayCareTMTutorVoucherRedeemedText
	promptbutton
	sjump .ShowCredits

.OfferLesson:
	writetext DayCareTMTutorOfferLessonText
	yesorno
	iffalse .Done

.LessonLoop:
	special TMTutorTeachAnyTM
	ifequal 0, .Done
	ifequal 1, .SuccessfulLesson
	sjump .AfterAttempt

.SuccessfulLesson:
	readmem wTMTutorCredits
	addval -1
	writemem wTMTutorCredits
	readmem wTMTutorCredits
	ifgreater 0, .ShowUpdatedCredits
	writetext DayCareTMTutorOutOfCreditsText
	promptbutton
	sjump .TryRedeemWhenEmpty

.ShowUpdatedCredits:
	getnum STRING_BUFFER_3
	writetext DayCareTMTutorCreditsRemainingText
	promptbutton

.AfterAttempt:
	readmem wTMTutorCredits
	ifgreater 0, .AskAnother
	sjump .TryRedeemWhenEmpty

.AskAnother:
	writetext DayCareTMTutorAnotherLessonText
	yesorno
	iftrue .LessonLoop

.Done:
	writetext DayCareTMTutorGoodbyeText
	waitbutton
	closetext
	end

.DeclinedUnlock:
	writetext DayCareTMTutorDeclineUnlockText
	waitbutton
	closetext
	end

.NotEnoughMoney:
	writetext DayCareTMTutorNotEnoughMoneyText
	waitbutton
	closetext
	end

DayCareMoveReminderScript:
	faceplayer
	opentext
	special MoveReminder
	waitbutton
	closetext
	end

DayCareBookshelf:
	jumptext DayCareServicePamphletText

Text_GrampsLookingForYou:
	text "Gramps was looking"
	line "for you."
	done

DayCareServicePamphletText:
	text "DAY-CARE SERVICES"
	line "TM TUTOR redeems"
	cont "VOUCHERS for"
	cont "lessons."

	para "MOVE REMINDER:"
	line "free old moves."
	done

DayCareTMTutorLockedIntroText:
	text "I'm the TM TUTOR."
	line "I can teach any TM"
	cont "move."

	para "Bring me TM"
	line "VOUCHERS and I'll"
	cont "redeem each one for"
	cont "three lessons."

	para "One-time setup fee:"
	line "¥1000."

	para "Unlock lessons now?"
	done

DayCareTMTutorUnlockedText:
	text "Great."

	para "Come back anytime"
	line "with TM VOUCHERS."
	cont "Each one is worth"
	cont "three lessons."
	done

DayCareTMTutorCreditsRemainingText:
	text "You have "
	text_ram wStringBuffer3
	line " lesson(s) left."
	done

DayCareTMTutorNoCreditsText:
	text "No lessons left."

	para "Bring me a TM"
	line "VOUCHER and I'll"
	cont "convert it into"
	cont "three lessons."
	done

DayCareTMTutorOfferLessonText:
	text "Want a TM lesson?"
	done

DayCareTMTutorRedeemVoucherText:
	text "Redeem 1 TM"
	line "VOUCHER for three"
	cont "lesson credits?"
	done

DayCareTMTutorVoucherRedeemedText:
	text "Voucher redeemed."

	para "You now have "
	text_ram wStringBuffer3
	line " lesson(s)."
	done

DayCareTMTutorAnotherLessonText:
	text "Teach another move?"
	done

DayCareTMTutorGoodbyeText:
	text "Come back whenever"
	line "you want more"
	cont "training."
	done

DayCareTMTutorDeclineUnlockText:
	text "No problem."
	line "I'll be here when"
	cont "you're ready."
	done

DayCareTMTutorNotEnoughMoneyText:
	text "You're short on"
	line "cash for setup."
	done

DayCareTMTutorOutOfCreditsText:
	text "That used your last"
	line "lesson credit."

	para "If you have a TM"
	line "VOUCHER, I can"
	cont "redeem it now."
	done

DayCare_MapEvents:
	db 0, 0 ; filler

	def_warp_events
	warp_event  0,  5, ROUTE_34, 3
	warp_event  0,  6, ROUTE_34, 4
	warp_event  2,  7, ROUTE_34, 5
	warp_event  3,  7, ROUTE_34, 5

	def_coord_events

	def_bg_events
	bg_event  0,  1, BGEVENT_READ, DayCareBookshelf
	bg_event  1,  1, BGEVENT_READ, DayCareBookshelf

	def_object_events
	object_event  2,  3, SPRITE_GRAMPS, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, DayCareManScript_Inside, EVENT_DAY_CARE_MAN_IN_DAY_CARE
	object_event  5,  3, SPRITE_GRANNY, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, DayCareLadyScript, -1
	object_event  8,  4, SPRITE_SUPER_NERD, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, DayCareTMTutorScript, -1
	object_event  7,  4, SPRITE_POKEFAN_M, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, DayCareMoveReminderScript, -1
