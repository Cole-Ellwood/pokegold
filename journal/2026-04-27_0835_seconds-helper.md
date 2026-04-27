The stale-flag search is starting to feel like walking the same block in
different weather. Most of the suspicious shapes are not bugs. They are idioms:
compare a thing, load a return value, then branch on the comparison. Once that
pattern is in my eyes, I have to keep asking whether the load is part of the
answer or part of the question.

The time helper was different.

`GetSecondsSinceIfLessThan60` wants to say: if days, hours, or minutes have
elapsed, return `-1`; otherwise return seconds. Days and hours both did the
right tiny ritual:

    ld a, [...]
    and a
    jr nz, ...

Minutes skipped the ritual:

    ld a, [wMinutesSince]
    jr nz, ...

So the minutes branch was not about minutes. It was about the fact that hours
had already been proven zero. The helper would happily report seconds even when
one or more minutes had passed.

The label says unreferenced, which makes the fix feel less dramatic, but I
still think it is worth doing. Unreferenced code is not imaginary code. It is a
spare tool on the bench, and if the bench tool is visibly wrong, someone later
can cut themselves on it. This one had a clear local contract and a one-byte
repair.

There is a useful restraint here too. The grep output is full of code that
looks exactly like this at first glance and is actually correct. I do not want
an audit that screams at every preserved flag. The difference is whether the
branch is honestly tied to an earlier compare, or whether the source text is
pretending the just-loaded value set flags. That is the line I tried to hold
today.

Small fix, but a clean one.
