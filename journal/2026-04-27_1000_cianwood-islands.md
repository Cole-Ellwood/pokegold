I kept the unused-map-label thread alive for one more session, but I can feel
the diminishing returns starting to press on it. That is not a reason to stop
immediately, but it is a reason to be more strict about each deletion.

Today's tiny case was Cianwood. The unused script was simple:
`CianwoodCityUnusedScript` only jumped to `CianwoodCityUnusedText`, a bit of
flavor about the islands between Cianwood and Olivine and a mythical sea
creature. The living map has three ordinary town NPCs, Chuck's wife, six smash
rocks, signs, hidden items, and no object or background event that points to
that script. The text was real compiled content, but not reachable content.

This one felt less romantic than the Entei script. There was no alternate
encounter ghost, no weird half-battle shape. Just a conversational line that
used to have a speaker and does not now. In a hack trying to feel unknown and
dangerous, unused flavor text can look like something worth preserving, but
preserving unreachable flavor inside the ROM is not the same as preserving the
world. If it has no mouth, the player cannot hear it.

The build and generated index put a number on it: 106 ROMX bytes out of Map
Scripts 7. Again, small. Again, real.

I do not want the next session to blindly continue down the unused-label list.
There are still obvious-looking entries there, but some are no-op scene labels,
old bookshelf/sign remnants, local branch labels, beta blocks, or scraps whose
source-history value may be higher than their ROM cost. The worthwhile pattern
is narrower: a standalone script plus private text, with no incoming event edge
and no table-position risk. Anything outside that shape deserves slower thought
or a different reason.
