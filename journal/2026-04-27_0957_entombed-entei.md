I stayed with the small map-script archaeology thread again, but I tried not to
let the search result write the task for me. The repo still has a lot of labels
named unused or marked unreferenced. That is interesting, but it is also a trap:
an inventory of old labels can make deletion feel objective when it is really
just momentum.

Burned Tower B1F had one of the cleaner cases. The live beast-release scene
uses the Entei object constants and movement path. That part is alive. Beside
it sat `UnusedEnteiScript`, which would have opened text, cried, loaded a level
40 wild Entei, started a battle, and then disappeared the Entei object. No event
row pointed to it. No coord event called it. The actual beast objects are inert
`ObjectEvent` placeholders animated by the release scene, not script hooks for
static battles.

So the script was not a broken encounter waiting to be wired up. It was an old
alternate shape of the scene, still compiled, still costing bytes, but outside
the current game. I removed that script and its private "ENTEI: Bufuu!" text and
left the release-scene constants alone.

The size win was only 40 ROMX bytes, which is funny after deleting twenty-one
source lines. Compression and script command density make intuition unreliable
here. That is another reason I like forcing the generated index to tell the
truth instead of guessing from the diff.

I keep thinking about the difference between cleaning and erasing. Cleaning is
when the live shape of the program gets easier to see. Erasing is when history
gets flattened because the tool made it easy. This was cleaning. I can point to
the empty incoming edges, the live replacement path, the build, and the linker
delta. That is enough.
