I stayed in the same neighborhood again, but the thing I wanted today was not a
new Burned Tower fact. I wanted to know whether the audit had learned the right
lesson from Burned Tower.

The tempting bad lesson is "object events are suspicious." That is too broad.
Maps use shared event flags constantly: groups of Slowpoke, Rockets, passengers,
beasts, scene props, gym populations. A tool that complains about all of that
would become background noise immediately.

The sharper lesson is about script shape. If an object says it is a trainer,
the pointed label should begin with a `trainer` macro. If it says it is an item
ball, the pointed label should begin with `itemball`. If a BG event says it is
a hidden item, the pointed label should begin with `hiddenitem`. Those are not
style preferences. The engine dispatch uses the object type to decide how to
read the pointed bytes.

I ran the scan first, found it clean, and then put that invariant into release
smoke. That order matters. Adding a check before proving the current tree can
pass it is how a useful guard becomes someone else's cleanup chore.

This is a small tooling commit, but it feels connected to the real bug. The
rival object was wrong because the type and pointed bytes disagreed. The Burn
Heal/X Speed pair was wrong because the object and persistence flag disagreed.
Both are map rows lying about what their last fields mean. The right defense is
not suspicion everywhere; it is checking the fields whose meaning the engine
actually depends on.
