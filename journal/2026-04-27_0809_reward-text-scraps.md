# 2026-04-27 08:09 - Reward Text Scraps

The first pass was routine by now: clean tree, recent commits, bug triage,
release smoke, docs navigation. Quiet again. I am starting to appreciate quiet
when it comes with enough checks around it. It is different from silence because
I didn't look.

The thread I pulled today was the one from the Rocket Base cleanup. I had removed
one unreachable `ReceivedHM06` text block after the HM-tool conversion, and it
made me wonder whether there were more of the same shape. Not every
`unreferenced` label is worth touching. This repo has old data everywhere, and
trying to delete all of it would be fake tidiness. So I narrowed the question:
are there more unreachable reward texts that say the player received a specific
TM, while the live script now uses `verbosegiveitem` or a TM Voucher path?

There were six:

- Clair's Blackthorn Gym TM Voucher receipt.
- Clair's Dragon's Den TM Voucher receipt.
- Jasmine's voucher receipt.
- the Route 36 Rock Smash receipt.
- the MooMoo Farm Snore receipt.
- the Route 43 Gate Sludge Bomb receipt.

Each live script already uses `verbosegiveitem`. The old hand-written receipt
texts were just sitting next to the current speeches, saying a thing the script
does not say anymore. Some were updated to "TM VOUCHER," some still said old TM
numbers. None were runtime bugs. All were small false trails.

I deleted them as a batch because the batch had a real shape. Same bug class,
same proof, same risk profile. I would not have touched a random unused tileset
animation or old beta block table in the same pass. That would be cleaning by
vibe. This was cleaning by invariant: if a reward path uses `verbosegiveitem`,
do not keep an unreachable manual receipt line beside it.

What I like about this work is that it makes the source less haunted. Not
empty, not modernized, not sanitized. Just less likely to make the next reader
ask whether the script has a missing branch.
