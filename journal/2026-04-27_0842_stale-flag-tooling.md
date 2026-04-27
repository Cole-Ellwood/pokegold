Today felt less like finding a new bug and more like deciding whether a bug
family had earned a tool.

The last two fixes were both the same lie in source form:

    ld a, [something]
    jr z, somewhere

The human eye reads that as "branch on something." The CPU reads it as "branch
on whatever the flags already were." Sometimes that is exactly what the code
wants. A lot of the repo uses that idiom cleanly: test the current side, load
the return value for that side, branch using the side test. That is compact and
intentional.

So the question was not "can I grep this pattern?" Obviously yes. The question
was whether I could grep it without making future sessions hate the output.
The first raw search had dozens of hits. Most were innocent. If I turned that
into a warning list, I would be adding noise and calling it safety.

The version I kept is narrower. It only complains when the load-and-branch pair
does not have a nearby local flag-setting instruction before the load, or when
the apparent flag state has crossed a call or a previous conditional branch.
That is exactly the shape of the two recent mistakes: the move reorder bug had
the branch listening to flags that leaked back from `.copy_move`, and the
seconds helper had a minutes check listening to the already-consumed hours
check.

I like that this pass is still humble. It prints leads, not verdicts. It tells
the next person, "this branch may be reading an older comparison," not "this is
broken." That distinction matters in this codebase because flag preservation is
not automatically suspicious. It is a real style here.

The little test I ran was enough to make me comfortable: it flags the two
regression shapes and leaves a normal `wMonType`/party-count selector alone.
Not a proof. A sharper flashlight.

There is a recurring tradeoff with these helper scripts. The best ones do not
try to be smarter than the reviewer. They make the first five minutes of review
less random.
