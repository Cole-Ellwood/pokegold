I started with the converted old-HM discs because the roadmap had left a little
hook there: the wording around TM51-TM57 still sounded like a place where a real
bug might hide. It did not turn into the bug I half-expected. The teach path
already says "Booted up a TM." unconditionally, the item names are TM51 through
TM57, the pocket name is TM POCKET, and release smoke has a surprisingly dense
net around the reward order and field-tool backfill.

The only concrete thing I found was smaller and more satisfying than dramatic:
two dead loads in the TM pocket renderer, one of them carrying the old comment
"why are we doing this?" The honest answer was: it is not doing anything. The
code pops the saved TM/quantity pair back into bc, immediately overwrites the
accumulator before printing the quantity, and no flags are involved. So I cut
the nonsense instead of trying to manufacture a text overhaul.

I like this kind of pass because it resists the fake productivity trap. There
was a tempting larger edit available: rename every surviving HM-ish symbol now
that the discs are displayed as TMs. But that would churn assembly constants,
map reward scripts, release smoke expectations, and historical event names for
almost no player-facing gain. The code still needs the old event names because
save compatibility is part of the shape of the problem. The dead `ld a` lines
were different: local, explainable, verifiable, and gone without changing the
concepts underneath.

One note for later: `engine/items/tmhm.asm` still has old vocabulary in labels
because the engine concept is really "the TM/HM table" even if the hack presents
the former HMs as late-numbered TMs. I would not rename that file or its broad
entrypoints unless a future change is already touching the whole item teaching
interface. The useful cleanup lives inside blocks like today's, where the reader
is forced to ask a small stupid question and the answer is "delete it."
