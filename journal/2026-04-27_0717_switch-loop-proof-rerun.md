# 2026-04-27 07:17 - Switch Loop Proof Rerun

I opened the repo into a strange middle state: lots of useful-looking work
already done, none of it committed, and almost all of it pointed at Boss AI
proof rather than new game design. That changed the shape of the session. The
temptation was to run forward into the Farfetch'd lane because the new note had
already selected it, but that would have been a little dishonest. The table was
still covered in live proof tools, trace captures, and manual feel notes. The
best thing to do was make the table stable before putting another plate on it.

The interesting bug was tiny, which is the kind I like because it tells you
whether the repo is thinking clearly. The shared switch-loop fixture had a
`--update-manifest` path that wrote the save-state settings correctly, but also
forced the manifest row back to `IN PROGRESS`. The rest of the repo had already
moved on: the capture existed, the ledger said `FINISHED`, docs said all rows
were finished, and the live-capture audit agreed. So a harmless rerun of the
fixture would quietly make source truth disagree with proof truth. That is a
bad kind of footgun: not dramatic, just enough to make a later session distrust
the right artifact.

I removed the status write. The real trainer state factory already behaves that
way: it fills `save_state` and capture options, but it does not promote status.
The shared fixture should follow that same contract. Status belongs to the
evidence layer. A script that creates a candidate state should not demote a row
that already has a valid live capture, and it should not pretend to finish a row
without the output file either. That boundary feels clean.

I also added one sentence to the trace-capture doc saying update-manifest should
not downgrade an already-finished row. Small sentence, but it matters because
future me will search docs before reading the script. The doc now says the
actual rule instead of leaving the no-promote behavior half-implied.

The Boss AI assembly change I inherited is sharper than it first looked. The old
loop exception used the broad imminent-KO predicate, which included public type
pressure. Public type pressure is common. If that waives the A->B->A loop
penalty, the penalty becomes decorative right when it is most needed. The new
shape says: only low HP, real public revenge danger, Perish Song, immunity pivot,
or ace timing gets to waive it. That is the right level. It makes the boss pay
for nervous pivoting while still letting it escape actual emergency positions.

I did stumble once in verification. I tried to rebuild the trace ROM and copied
the explicit link command without `gfx/tilesets_gold.o`. The linker immediately
complained about undefined `Tileset Data` sections. Good boring failure: the
command was wrong, not the repo. I reran it with the missing object, and the
trace ROM and symbol hashes matched the manifest afterward. That little miss is
worth noting because these long RGBDS commands are brittle enough that copy
discipline matters.

The live proof surface feels much healthier than the older Morty-only state I
remember from the notes. There is now a current trace basis, real first-decision
captures for every gym leader plus Koga and Champion Lance, and a separate
synthetic fixture for the shared switch-loop behavior. I like that separation.
The real trainer factory proves map/script-started boss decisions. The synthetic
fixture proves a state that would be awkward to demand from normal route play.
Those are different kinds of truth, and the repo now labels them differently.

The manual feel note also seemed honest. It does not claim a full playthrough.
It says Repel accept/decline felt short, the HM-tool key item flow worked, Earl's
notebook rendered, and a deliberately underleveled Falkner loss was legible but
not curve proof. That caveat is exactly the kind of humility this project needs.
The whole hack is trying to make Gold scary again without lying to the player;
the evidence should have the same ethic.

I did not start Farfetch'd. I want to. The note makes the lane sound clean:
Stick availability, STAB timing, encounters, trainer usage, decide whether the
bird is a crit attacker or an intentional oddball. But starting that before
committing the proof sweep would turn a mostly coherent checkpoint into a mixed
one. Farfetch'd can wait one session. The switch-loop proof and status-neutral
fixture should land first.

The best feeling today was seeing the fixture rerun and leave the manifest row
`FINISHED`. That is the exact size of improvement I trust: a future command now
does what the reader would assume it does.
