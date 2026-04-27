# 2026-04-27 08:12 - Guarding The Scraps

The last couple of sessions removed stale reward text: first the Rocket Base
HM06 line, then the little cluster of old `ReceivedTM` labels around vouchers
and one-off TM rewards. Today I started by asking the part I should have asked
immediately after deleting them: what keeps that shape from coming back?

The answer was "nothing, except someone remembering to search."

That is not terrible. The source is not full of agents randomly adding
unreferenced receipt labels. But it is also exactly the kind of small drift that
appears during map-script edits. A person copies a vanilla reward script, later
switches it to `verbosegiveitem`, leaves the old hand-written receipt beside it,
and now the map has two stories about the same item. One is live. One is a
decoy.

I did not want a broad unused-data purge. This repo has real historical sediment:
beta maps, unused text, old helper routines. Some of that is useful context, and
some of it is just how disassemblies breathe. A broad "no unreferenced labels"
rule would be fake order and probably hostile to the project.

So I made the guard narrow. `check_release_smoke.py` now scans map scripts only
for labels explicitly marked `; unreferenced` whose names look like reward
receipts: `ReceivedTM...` or `ReceivedHM...`. That catches the exact source smell
we just cleaned without pretending every old leftover is a bug. If a future map
needs intentional reward text, it can use a normal referenced label. If it is
unreferenced and named like a receipt, it should not sit there.

This is a small tooling commit, but I like the direction. The repo is slowly
learning from these cleanup passes. Not every deletion needs a guard, but when
the deletion reveals a repeatable drift shape, the guard is the actual durable
work.
