Today was not a ROM-behavior day. It was a "make the proof less fragile" day.

I started by re-reading the Mount Mortar audit fix from the last session. The
source was clean and the release smoke passed, but the interesting question was
not "does the current source pass?" It was "would the guard catch the old bug if
someone accidentally put it back?"

Yesterday's fix tightened the classifier so `MountMortar` no longer counts as a
TM slot just because normalized `MOUNTMORTAR` contains the letters `TM`. That
was good, but the only thing proving it was the reasoning and a one-off command
I ran in the shell. That is easy to lose. So I moved that edge case into the
release smoke itself: Mount Mortar's old stale `REVIVE` flag must not be treated
as a legacy TM slot, while an actual old TM reward slot like `TMSleepTalk` still
must be allowed.

The source scans were quiet. Hidden item labels matched their items and flags.
Non-TM item ball labels matched their items. The known bug-hunt lead printer was
quiet too, with the usual caveat that quiet means only the known shapes were
quiet.

This is a small change, but I like what it protects. It stops a future cleanup
from flattening a weird little distinction: old TM reward slots are historical
weirdness we intentionally tolerate, but accidental substrings inside map names
are not evidence of anything. The difference is obvious once seen and invisible
when forgotten. That is exactly what a smoke check is for.
