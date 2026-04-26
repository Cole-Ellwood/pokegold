RepelWoreOffScript::
	opentext
	writetext .RepelWoreOffText
	checkflag ENGINE_BUG_CONTEST_TIMER
	iftrue .NoRenewal
	checkitem MAX_REPEL
	iftrue .OfferMaxRepel
	checkitem SUPER_REPEL
	iftrue .OfferSuperRepel
	checkitem REPEL
	iftrue .OfferRepel
	waitbutton
	closetext
	end

.NoRenewal:
	waitbutton
	closetext
	end

.OfferMaxRepel:
	promptbutton
	writetext .UseAnotherRepelText
	yesorno
	iffalse .Done
	takeitem MAX_REPEL
	iffalse .Done
	setval 250
	writemem wRepelEffect
	writetext .UsedMaxRepelText
	waitbutton
	closetext
	end

.OfferSuperRepel:
	promptbutton
	writetext .UseAnotherRepelText
	yesorno
	iffalse .Done
	takeitem SUPER_REPEL
	iffalse .Done
	setval 200
	writemem wRepelEffect
	writetext .UsedSuperRepelText
	waitbutton
	closetext
	end

.OfferRepel:
	promptbutton
	writetext .UseAnotherRepelText
	yesorno
	iffalse .Done
	takeitem REPEL
	iffalse .Done
	setval 100
	writemem wRepelEffect
	writetext .UsedRepelText
	waitbutton
	closetext
	end

.Done:
	closetext
	end

.RepelWoreOffText:
	text_far _RepelWoreOffText
	text_end

.UseAnotherRepelText:
	text "Use another"
	line "REPEL now?"
	done

.UsedMaxRepelText:
	text "Used MAX REPEL."
	done

.UsedSuperRepelText:
	text "Used SUPER REPEL."
	done

.UsedRepelText:
	text "Used REPEL."
	done
