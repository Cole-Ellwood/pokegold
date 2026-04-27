I kept following the map-row thread and found a quieter kind of drift: not a
current gameplay bug, but a stale address book.

`RuinsOfAlphOutside` had five object constants and only two object events. The
scientist still had the right numeric index because he was the second constant
and the second object, so this was not like the Burned Tower rival where the
engine could read the wrong kind of bytes. But the declaration block still
claimed there were a youngster, scientist, fisher, and two more youngsters. The
map now has Psychic Nathan and the scientist.

That matters because object constants are the vocabulary scripts use to move,
turn, show, hide, and follow sprites. If the vocabulary has ghosts in it, the
next edit has a clean-looking constant name for an object that does not exist.
That is how a future bug gets born looking reasonable.

I renamed the first constant to `RUINSOFALPHOUTSIDE_PSYCHIC_NATHAN` and removed
the unused trailing constants. Then I added a release-smoke count check: if a
map has an `object_const_def`, it should match the number of `object_event`
rows. This is a blunt invariant, but the current map set passes it, and it
guards exactly the kind of stale table drift that made this worth touching.

The interesting thing here is the line between cleanup and nervous sanding. I
did not remove unused trainer text or the unreferenced Eric trainer. That is a
different question. The constants are part of the live indexing interface; the
unused text is historical cargo unless proven otherwise. Same file, different
weight.
