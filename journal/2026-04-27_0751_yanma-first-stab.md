# 2026-04-27 07:51 - Yanma First STAB

Yanma was the last medium-priority weak-Pokemon queue item after Farfetch'd and
Ariados. I did the obvious first checks: current stats, level-up curve, Route 35
availability, Schoolboy Alan usage, and the generated audit row. The suspicious
part was not that Yanma had no tools at all. It has real numbers. The current
source is 85/110/60/95/50/80, which is much less extreme than the older manifest
snapshot with 125 Attack and 140 Speed, but still not a joke.

The question was whether restoring the old fast glass-cannon statline was the
right move. I do not think it is. A level 12 Route 35 Yanma with 140 Speed and
125 Attack would be a very loud answer in the Whitney neighborhood. Maybe that
can be made fair, but it is not the smallest honest fix.

The actual gap was timing. Wild Yanma appears at level 12. Alan has one at level
17, then another at level 25. Before this pass, Yanma learned Leech Life at 19
and Wing Attack at 25. That means the first trainer showcase had no STAB at all:
Tackle, Foresight, Quick Attack, Double Team. This is the kind of thing that
makes a Pokemon look like it has a role in docs but feel like an old weak
Pokemon when the player meets it.

So I moved Leech Life from 19 to 17.

I like that exact number because it answers the trainer-showcase problem without
overfeeding the wild encounter. A level 12 catch still starts modestly. It gets
Double Team at 13, then has to grow into Leech Life. Alan's level 17 Yanma now
has the Bug move immediately. The level 25 rematch still introduces Wing Attack.
That makes the curve legible: quick nuisance first, Bug bite next, Flying STAB
later.

I did not add Baton Pass, Agility, or a new late move. I thought about it for a
minute because Yanma has that "fast bug that should do something clever" energy.
But Sleep Powder is already there at 31, Double Team is already there early, and
Wing Attack already gives the physical Flying half. Adding another system hook
would be designing a new Pokemon instead of tightening the one in source.

The generated audit still flags Yanma as lower than the older snapshot. That is
fine. The audit should not be bribed into silence. It is allowed to remember
that there was once a sharper concept. What matters today is that the current
concept is documented and the most obvious early failure has been removed.

The medium-priority queue is empty now. That does not mean balance is done. It
means the named, source-actionable trio got source-plus-intent treatment. The
lower watchlist still has real questions, but those should be opened one at a
time with source truth, not dragged into a broad stat cleanup just because the
table looks quiet.
