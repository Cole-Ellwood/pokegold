The audits were quiet this time, which made the shape of the work more about
the repo's habits than the ROM's behavior. The stale dev index from the previous
session was already fixed, but the checklist that future sessions are likely to
follow still had a small trap in it: build, run docs navigation, and only learn
from the failure that the generated index needed refreshing.

That is technically safe because the audit catches it. It is still a worse
workflow than naming the expected order. If source changes cause a relink, and
the linker outputs are kept, regenerate `docs/generated/dev_index.md` before
asking the docs audit whether everything agrees. The check should be a guardrail,
not the first teacher every time.

I spent a little time looking for a better bug before settling on that. The
triage tool was quiet, the release smoke passed, the battle math audit passed,
the Boss AI live ledger passed. At that point, forcing a gameplay edit would
have been fake momentum. The Morty dossier prototype is still sitting there,
but it is not a thing to begin casually at the end of a short bug-hunt loop.

What I like about this tiny docs edit is that it records a real recent wound.
Not theory, not process perfume. We actually tripped on this exact ordering.
Now the checklist says the thing plainly.
