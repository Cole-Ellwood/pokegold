# 2026-04-27 08:03 - Old Bugs On A Leash

The obvious bug hunt was quiet again. The triage helper found no duplicate
battle-script command weirdness, no held-effect compare shape, no base-data
restore lead, no TM Tutor item leak. That can feel like a dead end, but I do
not trust "quiet" as a conclusion. Quiet is a direction change.

I went to `docs/bugs_and_glitches.md` because it is one of those files that can
quietly become decorative. It lists the old Gold/Silver bugs, and the source
currently has the fixes. Coin Case text ends cleanly. Hall of Fame wipes the
previous save path if the player has never saved. Lucky Number checks all boxes.
Present uses the shorter failure text. Surf checks for a facing object.
Cerulean Gym has no fishing group. Route 15 is uppercase.

None of that was broken today.

The missing piece was that these checks were living in a human-readable doc and
an old ledger note, not in the release smoke. That is the annoying middle state:
the project knows something, but the machine does not. Future edits can regress
one of those fixes and still pass the main confidence command. Not likely, but
also not imaginary. Map data and text are exactly the kind of source that gets
brushed by unrelated edits.

So I put the old bugs on a leash. `check_release_smoke.py` now has one compact
section for the documented Gold/Silver bug fixes. It is not clever. It asks:
does the Coin Case text terminate safely, does Hall of Fame preserve the
first-save guard, does Lucky Number use `NUM_BOXES`, does Present use the safe
line, does Surf check facing objects, does Cerulean Gym block fishing, and does
Route 15 shout like every other route sign?

I like this as a maintenance move because it does not pretend to be new design.
It just closes a small gap between "we know this matters" and "the repo will
catch it next time." That is often better than another speculative feature.

One thing I did not do: add a separate audit note. The smoke checker itself is
the durable artifact here, and the roadmap/playbook now point at it. Adding a
third prose file would mostly make future sessions read more to learn the same
fact.
