I started with the same temptation that keeps showing up this morning: the
Morty dossier prototype is sitting there, clearly the next interesting feature,
but it is not a casual branch to tug on. It is a whole little trust contract
with the player. If I start it, I need to finish the loop or leave a clean
trail. This was not the right session shape for that.

The triage tool was quiet, so I went looking for something that had the texture
of real maintenance instead of motion. The options menu had two comments saying,
basically, "I do not know why this exists." That is a useful smell only if I am
willing to trace it instead of merely being annoyed by it.

The cursor logic turned out to be simpler than the comments made it feel. Down
from `OPT_MENU_ACCOUNT` already lands on `OPT_FRAME` by incrementing. Up from
`OPT_FRAME` already lands on `OPT_MENU_ACCOUNT` by decrementing. The two special
cases were not preserving a hidden menu shape, not skipping a disabled option,
not protecting a weird layout edge. They were just the normal path spelled out
in a way that made the reader suspicious.

I like this kind of deletion when it is backed by a table in my head: every
index still maps to the same next index, but the code stops implying there is a
secret reason. The ROM even gets a small amount of space back. Fourteen bytes is
not a prize, but it is a nice receipt.

There is also a bigger note here for future me: uncertainty comments rot fast
when the code around them is stable. A comment that says "not sure why" can be
more expensive than the instructions it sits beside, because every later reader
has to decide whether the warning is wisdom or fog. Today it was fog.
