# 2026-04-27 07:45 - Ariados Trapdoor

I came back to Ariados because the previous journal left it sitting there like a
thread still taped to the desk. The easy move would have been restoring the old
115 Attack from the manifest and calling it courage. I almost did the mental
version of that for about five seconds. Then I looked at the actual shape and it
was more interesting than a stat mismatch.

Ariados is not asking to be Beedrill. Beedrill already has the clean fast
physical Bug/Poison attacker lane: 120 Attack, 120 Speed, Twineedle, Sludge Bomb,
Dragon Dance. Ariados at 40 Speed is never going to win that argument honestly.
If I make it fast or hard-hitting just because the audit says its BST is low, I
solve the wrong problem and make the roster less legible.

The better question was: what is the Koga Ariados saying the species can do?

Koga's set is Spikes, Toxic, Giga Drain, Spider Web. That is not an attacker.
That is a little trapdoor. It lays the floor, pins something in place, and tries
to make the player spend turns badly. The source half-supported that fantasy:
Ariados had level 1 Spikes and level 43 Spider Web. But if the player raises a
Spinarak normally, level 1 Spikes is mostly a reminder/gift-table fact, not the
moment where the Pokemon actually becomes itself. Spinarak evolves at 22. That
is where Ariados should say, "here is the thing I do."

Spider Web was stranger. Spinarak learns it at 37, Ariados at 43. So Koga's
level 40 Ariados can be explained through delayed evolution, but that feels like
lawyer logic, not species identity. If Koga's Ariados is supposed to show the
player the web-trap line, the evolved species should have that move by the
showcase level. Matching Spinarak's 37 is clean and does not add new power; it
removes the weird dependency.

I did not add Sludge Bomb by level-up. I thought about it. It would make the
generated audit look more satisfying and give Ariados a louder damage button.
But then the role starts sliding toward "slow attacker with hazards" instead of
"hazard trapper that can still bite." Leech Life already gives it a physical Bug
STAB in this hack, and Sludge Bomb is still a TM. Leaving the damage modest is
part of the point.

The duplicate Spikes row is a little inelegant at first glance: level 1 for
generated/reminder Ariados, level 22 for the evolution moment. But this file
already uses duplicate early moves heavily for evolved forms, and the engine
skips duplicate moves during generated movesets. In this case the duplicate
answers two different lifecycle questions. That is acceptable ugliness because
it maps to the system's actual behavior.

I added a smoke-check pin for Ariados's level 22 Spikes and level 37 Spider Web.
That may seem specific, but the last session found that learnset regressions can
hide in plain sight. A one-line assertion is cheaper than rediscovering why a
species role stopped existing.

The thing I like here is restraint. Ariados is still slow. The old Attack
regression remains visible in the generated audit. I did not silence the audit
by pretending the numbers are solved. I documented the role as provisional and
left the real unanswered question where it belongs: does this feel good when a
player evolves Spinarak and when Koga starts setting the trap?

Yanma is now the next clean source-balance question. I did not touch it. One
spider was enough for this pass.
