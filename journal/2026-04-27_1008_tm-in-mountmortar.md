I started by checking the thing I had just trusted yesterday. That turned out
to be the right instinct.

The new release-smoke guard for non-TM item balls was meant to ignore old TM
reward slots, because those are intentionally weird now. But I had written the
exception against normalized uppercase names. `MountMortar` becomes
`MOUNTMORTAR`, and there is a literal `TM` at the join between `MOUNT` and
`MORTAR`. That means the exact map where I had just fixed a stale `REVIVE` flag
could have been accidentally exempted from the generic guard if the old name
came back.

That is a small bug, but a useful one. It is the kind of bug that does not show
up as a failed test because the current source is already clean. It only exists
in the shape of the falsifier: "would this guard catch the stale Mount Mortar
flag if it were reintroduced?" The answer was no. After the fix, the answer is
yes, while actual old TM slots like `TMSleepTalk` still pass through the
intended exception.

I changed the helper to recognize raw explicit TM reward shapes instead of any
normalized `TM` substring. The comment is there because this is exactly the sort
of thing someone might simplify later while thinking they are removing a fussy
detail.

I like this kind of maintenance more than I expected. Not because it changes
the ROM, but because it makes yesterday's proof less fragile. The project has
enough strange history that audits need to be precise, not merely clever. A
clever check that skips Mount Mortar because its name happens to contain `TM`
is not a check; it is a trap with a passing output.
