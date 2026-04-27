I stayed in the map-item audit lane, but tried to move one ring outward from
the last fix instead of just poking the same line again.

The Mount Mortar flag bug was about a player-visible item being guarded by a
source name that claimed a different item. Yesterday I guarded the event-flag
side. Today I asked the adjacent question: even if the event flag is right, can
the label lie? And can hidden items have the same kind of stale label or stale
flag drift?

The scans were quiet, which is a good result but not much of a finish by
itself. Quiet one-off shell scripts disappear from memory. So I moved that
source-truth scan into release smoke. Non-TM item balls now have to keep their
label names aligned with the item they give, hidden item labels have to name the
item, and hidden item event flags have to name it too. Old TM reward slots keep
their exception, because those are intentionally historical after the custom
item replacements.

This is not glamorous. It changes no ROM behavior. But it makes the next stale
item-name mismatch cheaper to catch than to reason about. That matters in a ROM
hack where event flags are save bits, labels are human maps, and old reward
slots carry history that cannot just be renamed by vibes.

I am noticing a useful distinction in these sessions: a good audit does not
just say "everything should match." It names the mismatch that matters, and
also names the mismatch that is allowed. The allowed mismatch is usually where
the project history lives.
