	object_const_def
	const LAKEOFRAGEMAGIKARPHOUSE_FISHING_GURU

LakeOfRageMagikarpHouse_MapScripts:
	def_scene_scripts

	def_callbacks

MagikarpLengthRaterScript:
; The Magikarp size sidequest is repurposed: the Fishing Guru now studies the
; one gold MAGIKARP that survived the Rockets' forced-evolution attempt at the
; lake. The vanilla state machine survives - EXPLAINED_WEIRD_MAGIKARP gates
; history->menInBlack, ASKED_FOR_MAGIKARP gates "already rewarded,"
; ELIXIR_ON_STANDBY holds the ETHER if the player's bag is full. The gate for
; the reward is EVENT_LAKE_OF_RAGE_RED_GYARADOS (set when the lake event ends)
; plus MAGIKARP in party: caught the survivor, didn't KO it.
	faceplayer
	opentext
	checkevent EVENT_LAKE_OF_RAGE_ASKED_FOR_MAGIKARP
	iftrue .AlreadyRewarded
	checkevent EVENT_LAKE_OF_RAGE_ELIXIR_ON_STANDBY
	iftrue .StandbyReward
	checkevent EVENT_LAKE_OF_RAGE_RED_GYARADOS
	iftrue .AskForSurvivor
	checkevent EVENT_LAKE_OF_RAGE_EXPLAINED_WEIRD_MAGIKARP
	iftrue .MidState
	writetext MagikarpLengthRaterText_LakeOfRageHistory
	waitbutton
	closetext
	setevent EVENT_LAKE_OF_RAGE_EXPLAINED_WEIRD_MAGIKARP
	end

.MidState:
	writetext MagikarpLengthRaterText_MenInBlack
	waitbutton
	closetext
	end

.AskForSurvivor:
	setval MAGIKARP
	special FindPartyMonThatSpecies
	iffalse .NoSurvivor
	writetext MagikarpLengthRaterText_ShowMeTheSurvivor
	yesorno
	iffalse .RefusedToShow
	writetext MagikarpLengthRaterText_YesThatsTheOne
	promptbutton
	verbosegiveitem ETHER
	iffalse .StoredReward
	setevent EVENT_LAKE_OF_RAGE_ASKED_FOR_MAGIKARP
	closetext
	end

.StoredReward:
	setevent EVENT_LAKE_OF_RAGE_ELIXIR_ON_STANDBY
	closetext
	end

.StandbyReward:
	writetext MagikarpLengthRaterText_HereIsYourEther
	promptbutton
	verbosegiveitem ETHER
	iffalse .StoredReward
	clearevent EVENT_LAKE_OF_RAGE_ELIXIR_ON_STANDBY
	setevent EVENT_LAKE_OF_RAGE_ASKED_FOR_MAGIKARP
	closetext
	end

.NoSurvivor:
	writetext MagikarpLengthRaterText_NoSurvivor
	waitbutton
	closetext
	end

.RefusedToShow:
	writetext MagikarpLengthRaterText_RefusedToShow
	waitbutton
	closetext
	end

.AlreadyRewarded:
	writetext MagikarpLengthRaterText_PostReward
	waitbutton
	closetext
	end

LakeOfRageMagikarpHouseUnusedRecordSign: ; unreferenced
	jumptext LakeOfRageMagikarpHouseUnusedRecordText

MagikarpHouseBookshelf:
	jumpstd DifficultBookshelfScript

MagikarpLengthRaterText_LakeOfRageHistory:
	text "LAKE OF RAGE is a"
	line "crater made by a"
	cont "single rampaging"

	para "GYARADOS."

	para "That's what the"
	line "old stories say."

	para "I can't imagine"
	line "the strength to"
	cont "carve a lake."

	para "We haven't seen"
	line "anything like it"
	cont "since."

	para "The MAGIKARP that"
	line "used to fill the"
	cont "water -- gone."

	para "I don't understand"
	line "what's happening."
	done

MagikarpLengthRaterText_MenInBlack:
	text "The LAKE has been"
	line "quiet since those"
	cont "men in black came."

	para "Too quiet."

	para "Even the MAGIKARP"
	line "are gone."
	done

MagikarpLengthRaterText_ShowMeTheSurvivor:
	text "They tell me there"
	line "was a survivor."

	para "A gold MAGIKARP."

	para "Could I see it?"
	line "Just once, with my"
	cont "own eyes."

	para "Would you show me?"
	done

MagikarpLengthRaterText_YesThatsTheOne:
	text "Yes."

	para "That's the one."

	para "Look at that."
	line "Gold, just like"
	cont "they said."

	para "So this is what"
	line "they tried to make"
	cont "a dragon out of."

	para "Take this -- you"
	line "earned it."
	done

MagikarpLengthRaterText_HereIsYourEther:
	text "You came back."

	para "Here -- this is"
	line "what I owed you."
	done

MagikarpLengthRaterText_NoSurvivor:
	text "You don't have it"
	line "with you?"

	para "The MAGIKARP from"
	line "the LAKE -- that's"
	cont "the one I want."
	done

MagikarpLengthRaterText_RefusedToShow:
	text "Hm. Maybe later,"
	line "then."
	done

MagikarpLengthRaterText_PostReward:
	text "I keep thinking"
	line "about that gold"
	cont "MAGIKARP."

	para "What a strange"
	line "world this is."
	done

LakeOfRageMagikarpHouseUnusedRecordText:
	text "CURRENT RECORD"

	para "@"
	text_ram wStringBuffer3
	text " caught by"
	line "@"
	text_ram wStringBuffer4
	text_end

LakeOfRageMagikarpHouseUnusedDummyText: ; unreferenced
	text_end

LakeOfRageMagikarpHouse_MapEvents:
	db 0, 0 ; filler

	def_warp_events
	warp_event  2,  7, LAKE_OF_RAGE, 2
	warp_event  3,  7, LAKE_OF_RAGE, 2

	def_coord_events

	def_bg_events
	bg_event  0,  1, BGEVENT_READ, MagikarpHouseBookshelf
	bg_event  1,  1, BGEVENT_READ, MagikarpHouseBookshelf

	def_object_events
	object_event  2,  3, SPRITE_FISHING_GURU, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, -1, 0, OBJECTTYPE_SCRIPT, 0, MagikarpLengthRaterScript, -1
