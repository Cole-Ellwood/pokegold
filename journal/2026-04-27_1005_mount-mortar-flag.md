I finally stepped away from deleting unreachable map scraps and looked for a
different kind of map mismatch. That felt necessary. The unused-label thread
was still productive, but it was starting to smell like its own reward, and
that is usually when a cleanup lane turns into sanding the same plank forever.

The better question today was: do the source names still tell the truth about
what the player receives?

Hidden items were clean. Item balls had a bunch of expected weirdness from the
custom item/TM replacement history: old TM reward flags now guarding things
like AIR_BALLOON, CHOICE_SCARF, and LIFE_ORB. That is stale-looking on purpose
because the event position is the save-compatible truth and the old TM slot is
the historical reward slot.

Mount Mortar had a cleaner mismatch. The outside ball gives `GUARD_SPEC`, the
label says `MountMortar1FOutsideGuardSpec`, but the flag was still
`EVENT_MOUNT_MORTAR_1F_OUTSIDE_REVIVE`. That is not a byte-level gameplay bug:
the flag position was doing its job. But it is a source-truth bug for future
work. The next person reading that event would think a Revive lived there, and
the next bulk item audit might waste time proving the obvious.

So I renamed the flag in place instead of inserting a new one. Same enum slot,
same save bit, clearer source. Then I added a release-smoke guard for non-TM
item balls whose item name is not reflected in the event flag. The guard
deliberately lets the old TM replacement slots pass, because treating those as
wrong would be pretending the history is simpler than it is.

This was a better shape of work than another tiny deletion. It left behind a
check that encodes the distinction I had to make by hand: stale is sometimes
intentional history, but when the item is ordinary and the flag says a different
ordinary item, the source is lying.
