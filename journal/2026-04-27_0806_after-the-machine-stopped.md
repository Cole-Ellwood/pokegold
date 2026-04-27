# 2026-04-27 08:06 - After The Machine Stopped

This was another quiet bug-hunt start, but it was a useful quiet. The triage
helper found nothing. Release smoke passed. Docs navigation passed. Boss AI
tiers, boss items, boss moves, no-cheat, gating, trace invariants, memory budget,
battle math, and cheap difficulty all passed. That kind of green wall is not a
reason to declare the repo perfect. It is a reason to stop swinging at ghosts.

I read the completion todo and decided not to touch the Morty scout dossier. It
is the only obvious `TODO`, but it is not a "while wandering" change. It wants a
prototype, a fairness read, source wiring, and probably some awkward thought
about what counts as public evidence. Starting that just to have something big
to commit would be exactly the wrong kind of motion.

So I went looking for small stale leftovers near recent work. The HM-tool pass
keeps leaving little edges worth checking because it changed a concept, not just
a line of code: HMs became field tools plus TM51-TM57 discs. In Team Rocket Base
B2F, Lance's reward path now uses `verbosegiveitem WHIRL_KIT`, then
`verbosegiveitem HM_WHIRLPOOL`, then explains the Whirl Kit. Right below that
was an old `RocketBaseReceivedHM06Text` label, already marked unreferenced,
still saying the player received TM56.

That text was not hurting runtime behavior. It was unreachable. But it was dead
old-language sitting right next to the current reward. The sort of thing a later
reader could notice and wonder whether a script path was missing, or whether
the HM conversion had not fully settled. It did not deserve a whole redesign.
It deserved deletion.

I like deletions like this when they are backed by a search. One less stale
sentence, one less false trail, a few fewer bytes in that map-script bank. Not a
grand improvement. Just the code saying slightly less that is no longer true.

The larger thought: after enough feature work, maintenance is often not adding
guards or systems. Sometimes it is walking behind the work and picking up the
wrapper it left on the floor.
