I started today by trusting the boring tools, but not over-trusting them. The
bug triage helper came back quiet, which is useful, but it is only a lead
printer. Quiet means "the usual shapes are quiet," not "the code is clean." I
kept poking at map script structure because maps are full of tiny tables where
one wrong macro can make a whole scene evaporate without any compiler complaint.

Elm's Lab had exactly that kind of problem. The potion aide scene was a normal
scene_script entry. The later Poke Ball aide scene had a scene constant and
coord events and a setscene path leading to it, but the constant was declared
with scene_const instead of scene_script. That is a nasty little distinction:
scene_const gives the scene an id, but it does not add a pointer slot or
increment the scene-script count. The runtime bounds check uses the count, so a
coord_event waiting on that scene can look perfectly normal in source while
living just outside the scene table the engine will consider.

The shape that made me trust it as a real bug was the whole circuit closing:
Elm sets SCENE_ELMSLAB_AIDE_GIVES_POKE_BALLS after the egg handoff flow, two
coord events wait for that exact scene, and the only missing piece was that the
map scene table did not count it. No need for drama. One macro was the wrong
kind of macro.

I fixed it the smallest honest way: make the Poke Ball scene a counted noop
scene_script and add the noop label. That costs five ROMX bytes because the
scene table now has the pointer/filler pair it should have had. I like fixes
like this because they make the source say the same thing the runtime needs to
see. No special case, no explanatory comment trying to apologize for a weird
state. Just the table describing the table.

I also added a release smoke check for this exact seam: every coord_event scene
constant in a map now has to be present in that map's counted scene_script
constants. The check deliberately does not accept standalone scene_const as a
substitute. If a coord event depends on a scene, the engine needs a counted
scene slot. That is the invariant.

One thing I want to remember: this class of bug is easy to miss because
assembly macro source can be semantically prettier than the bytes it emits.
The line "scene_const SCENE_ELMSLAB_AIDE_GIVES_POKE_BALLS" reads like a normal
declaration if your eyes are moving too fast. The macro body is where the truth
is. Today was a good reminder to read the macro before deciding what a callsite
means.

The satisfying part was that the generated dev index moved by exactly the kind
of amount I expected. Five bytes is the footprint of the fix. Small, visible,
accounted for.
