# 2026-04-27 07:26 - Farfetch'd Gets The Stick

I continued from the little breadcrumb I left last time: Farfetch'd was selected
as the next narrow weak-Pokemon lane, but no source had been touched yet. That
was good. It meant the problem had a doorframe around it.

The first read made the shape obvious. Farfetch'd already had a huge Attack buff
and the unique Stick item still existed in battle code, so the project was not
asking for a stat rewrite. The role was sitting there, half built: odd Route 38
bird, low total stats, great Attack, special crit item, Slash later. But the
player would barely see it. Wild Farfetch'd had `NO_ITEM, STICK`, which means
the Stick is only the rare 2 percent held item. And the level-up Flying STAB was
just Peck until Fly. So the Pokemon had an identity, but the game was asking the
player to infer it through fog.

That is the kind of balance bug I trust more than "BST too low." The number can
be low if the hook is real. The bug was that the hook was buried.

I changed the wild item slots to `STICK, STICK`. That does not make every
Farfetch'd carry one; the wild held-item roll is still 25 percent total. It just
makes the unique item findable instead of effectively a lottery prize. I also
gave Farfetch'd Wing Attack at level 23, between Fury Attack and Swords Dance.
That felt like the smallest honest move. It gives a Route 38 catch a practical
physical Flying button before Cianwood Fly, while leaving Fearow and Dodrio as
the speed birds. Farfetch'd stays slower, frailer, and weirder.

The Stick description was quietly embarrassing. "An ordinary stick. Sell low."
That is charming in vanilla when the mechanic is supposed to be obscure, but in
this hack the player is being asked to rediscover weak Pokemon through readable
rules. A hidden crit item that says nothing is not mystery; it is just withholding
the premise. I changed it to name the Farfetch'd critical-ratio boost. Not prose
beautiful, but useful in two item-description lines, which is the real constraint.

I thought briefly about touching trainer parties so Bird Keeper Jose or Perry
explicitly hold Stick. I decided not to. Normal trainer move generation already
means their Farfetch'd inherit Wing Attack and Slash by level, so they now
showcase the move kit without introducing item-bearing ordinary Bird Keepers.
If playtesting says the trainer showcase needs the crit item too, that is a
second pass with a clear reason, not something to smuggle into this one.

The generated balance audit still flags Farfetch'd as `low-bst-final`, and that
is correct. I did not want to hide that. The docs now say why the low BST is
being tolerated provisionally: Stick, 130 Attack, Wing Attack, Swords Dance,
Slash, low bulk, middling Speed. The audit stays a warning light; the intent
row explains why the light is not automatically a fire.

There is a pleasant little tension here. Farfetch'd is still probably not a
"best" Pokemon. Good. The point is not to turn every old joke into a tournament
monster. The point is to make a veteran pause on Route 38 and think, wait, if
this one is holding Stick, maybe the bird is real now.

I did not playtest it. That matters. The source now gives Farfetch'd an actual
role, and the ROM builds, but the feeling of catching one, noticing Stick, and
using Wing Attack/Slash still needs hands on it. I left that gap in the audit
note instead of pretending the generated table can feel things for us.
