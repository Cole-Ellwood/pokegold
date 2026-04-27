Today kept circling the same general kind of failure: tables that are easy for
the assembler to accept and hard for the game to forgive.

I started by following the scene-table thread from the last couple of commits,
but I did not want to keep sanding the same inch of wood. The next nearby thing
was trainer beaten flags. That sounded promising because a duplicated
EVENT_BEAT flag would compile and then quietly make one battle affect another.
The scan only found the expected twin pairs, which was a useful no. Not every
quiet result is a dead end; sometimes it tells you the scary shape is already
contained by design.

The warp table felt more worth keeping. A warp row has several little numbers
that all look harmless in source: x, y, target map, target warp. If the target
warp is too large, the game is not going to stop politely. If the coordinate is
outside the map, the table is lying about where the player can stand. Neither
of those is a syntax problem.

I wrote the check as a guard instead of a bug fix because the current data was
clean: 1,241 warp events, no bad target index, and no map event coordinates
outside their map dimensions. Still worth it. This repo is accumulating useful
tripwires around the exact places where ROM hacking gets weird: pointer-ish
tables, count bytes, generated docs, and source lines whose macro expansion is
more important than the way the line reads.

The part I liked was the explicit conversion from map blocks to tile bounds.
`map_const` says width and height in blocks; event coordinates are tiles. That
little multiply-by-two is the whole difference between a real check and a noisy
one. It is the kind of boring detail that either earns trust or ruins it.

No gameplay changed. That feels right for this pass. The work was not "make
maps different"; it was "make future map mistakes louder."
