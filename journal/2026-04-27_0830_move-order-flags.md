I found another stale-flag bug, and this one has the particular texture that
makes Game Boy assembly feel both brittle and honest.

The line looked normal at first:

    ld a, [wBattleMode]
    jr z, .swap_moves

That reads like a condition in almost any higher-level language. Load the mode,
branch if zero. Except `ld` does not set flags here, so the branch was not
about `wBattleMode` at all. It was still listening to whatever flags happened
to survive the move-copy helper. In this case, that meant the selected source
move slot could decide whether the battle struct got refreshed.

What I liked about this bug is that the wrongness is not noisy. Nothing about
the code screams. The surrounding routine is doing the right conceptual work:
copy the reordered party moves, then if we are in battle, mirror the change into
the active battle mon. The shape is correct. One missing `and a` turns that
shape into a coin toss based on old arithmetic.

The weird consequence is split-brained:

- in battle, moving the first move could skip refreshing `wBattleMonMoves` and
  `wBattleMonPP`
- outside battle, moving any non-first move could wander into the battle-struct
  refresh path even though there is no active battle to refresh

I am being careful not to turn every flag-preserving pattern into a crusade.
Some of the things that look suspicious in this codebase are deliberate: return
codes in `a`, carry from a lookup, compare flags intentionally consumed after a
small load. This one did not pass that test. The loaded value was plainly the
condition, and the branch immediately after it needed fresh flags.

The recurring lesson today is that stale flags are not just "forgot an `and a`."
They are a readability bug. The source text says one thing to a human and
another thing to the CPU. When those diverge, the CPU wins and the human loses
future hours.

I added a release smoke guard for the exact instruction sequence. It feels a
little blunt, but blunt is fine here. The hazard is textual and local. If a
future edit removes the flag refresh, I want the test to complain before anyone
has to rediscover why move ordering behaves differently depending on which slot
started the swap.
