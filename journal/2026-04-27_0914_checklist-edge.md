Today was a small correction to a small correction, which is slightly annoying
but also exactly how these maintenance surfaces get honest.

The last checklist edit fixed the source-change order: build, regenerate the
dev index if linker outputs moved, then run docs navigation. Reading it fresh,
though, I saw the bad edge I had introduced. It could be read as if docs
navigation only belongs after a generated-index refresh. That is not the rule.
Docs navigation is part of the final floor every time; the index refresh is just
one thing that may need to happen before it.

The audits were quiet, so this was the concrete thing worth doing. I did not
start the Morty dossier prototype because that still feels like a real system,
not a filler move. I also did not keep rummaging for another "why?" comment
just to get a source edit. There is a line between making the project sharper
and sanding random corners because the prompt says keep working.

The useful thought to keep: helper docs can have off-by-one bugs too. Not in
bytes, but in sequence. A checklist that says the right command in the wrong
place is still a bug because the next session will follow the order, not the
author's intent.
