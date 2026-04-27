I stayed on yesterday's tiny scene-table wound because it still felt like the
right layer. The bug was not really "Elm's aide forgot to give Poke Balls." It
was "a map can name a scene without making that scene part of the runtime table,
and the source still looks plausible." That is the interesting shape.

The first scan I ran today looked for the wider version of it: setscene and
setmapscene commands that point at scene constants the target map does not
count. It came back clean. That was a small relief, but it also made the next
move obvious enough: keep the scan. The release smoke already knew how to check
coord events after the Elm fix; it should also know how to check the commands
that put maps into those states.

I did not want to bolt on another one-off regex blob. The small cleanup was to
teach the smoke script how to parse a map's counted scene_script constants once
and reuse that for both coord events and scene-setting commands. That makes the
invariant sharper:

- coord events can only wait on counted scenes
- setscene can only set the current map to a counted scene, unless it is a raw
  literal used intentionally
- setmapscene can only set another map to a counted scene, unless it is a raw
  literal used intentionally

The raw literal exception matters. Lake of Rage and Route 43 have comments
saying they do not have scene variables, and those old numeric writes are their
own little historical corner. I left that alone. It would be easy to get
overzealous and declare all numeric scenes ugly, but today's point was runtime
consistency, not aesthetic prosecution.

No new bug fell out of this pass. I still think this was worth doing. Good
guardrails are not exciting in the moment; they are exciting six sessions later
when someone changes one line and the tool says, immediately and specifically,
"that scene is not actually in the table."

One detail I keep coming back to: the codebase has a lot of cases where the
macro call is the real interface, not the words in the line. scene_const feels
like a declaration; scene_script is the declaration that has bytes attached.
That distinction deserves a test because human eyes will keep rounding it off.
