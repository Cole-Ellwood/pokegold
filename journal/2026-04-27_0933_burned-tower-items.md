The Burned Tower map kept giving.

After the rival object fix, I did not want to assume the rest of that object
block was fine just because the first bug was done. The two item balls at the
bottom looked ordinary until the names were read against the event flags:
`BurnedTower1FBurnHeal` was guarded by `EVENT_BURNED_TOWER_1F_X_SPEED`, and
`BurnedTower1FXSpeed` was guarded by `EVENT_BURNED_TOWER_1F_BURN_HEAL`.

This is the kind of bug that is easy to wave away as "just names" until the
script path is traced. `OBJECTTYPE_ITEMBALL` copies the item data, then
`FindItemInBallScript` gives the item and calls `disappear LAST_TALKED`.
`disappear` sets the current object's event flag. So the names are not cosmetic:
pick up one ball and the other flag gets set.

I ran a broader cross-swap scan afterward because one local fix can hide a
pattern. The scan turned up no remaining two-item swap candidates after the
edit. There are still source-truth oddities like old TM-named event flags now
guarding held-item replacements, and one Mount Mortar Guard Spec guarded by a
Revive-named flag. I left those alone because they are not the same bug. A stale
flag name is ugly; a cross-wired pair changes play.

What I want to remember is how close this was to yesterday's kind of bug:
nothing crashes, no build complains, and a normal player might only notice that
a pickup disappeared or reappeared in a way they cannot reproduce cleanly. Map
metadata has these little trapdoors. It is worth reading the last fields, not
just the scripts.
