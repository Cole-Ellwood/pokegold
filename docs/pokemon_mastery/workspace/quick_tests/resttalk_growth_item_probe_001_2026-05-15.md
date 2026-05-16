# RestTalk/Growth/Item Probe 001 - 2026-05-15

Type: focused regression probe after `resttalk_growth_item_transfer_001`.

Status: nonblind constructed drill. This checks whether the item-first,
Growth-package, and CurseLax/RestTalk timing lessons can be stated as concrete
move choices without breaking information tiering. It is not fresh replay proof
and must not count as mastery progress.

Source basis:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/resttalk_growth_item_review_001_2026-05-15.md`
- Smogon Forums GSC Exeggutor OU Revamp:
  `https://www.smogon.com/forums/threads/exeggutor-ou-revamp-gp-0-2.3622650/`
- Smogon Forums GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`
- Smogon Forums GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2-2.3477110/`

## Score Summary

Scenarios: 6.
Top-match: 6 / 6.
Acceptable-match: 6 / 6.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 6 / 6.
Route-converting move chosen: 6 / 6.
Branch-punish chosen: 6 / 6.

Result: pass as regression only. The answers separated item-denial from
generic status, active removal from over-handoff, Espeon package denial,
revealed coverage reclassification, public-versus-side-known RestTalk, and
CurseLax Rest-clock timing.

## Scenario 1 - Thief Before Generic Status

Public state:
p1 no-item Exeggutor has side-known Thief, Sleep Powder, Psychic, and
Explosion. It faces a bulky special receiver class that usually relies on
Leftovers and will be pressured by Spikes later. The opponent's side has not
yet been slept.

Frozen answer:
Top action: Thief. Confidence: medium.

Ranked candidates:

1. Thief.
2. Sleep Powder if sleep value beats item removal or the receiver lacks
   Leftovers value.
3. Psychic/Explosion only if immediate damage or trade opens a named route.

Reason:
The route is to remove the receiver's Leftovers before Spikes and Zapdos/Snorlax
pressure. Sleep remains strong, but it is not automatic when item denial is the
converter.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Active Removal Beats Over-Handoff

Public state:
p1 Zapdos at healthy HP faces p2 Cloyster at 60%. p2 has an Electric receiver
available by class, but Cloyster is the only revealed Spikes setter and is in
range of Thunder. p1 side can survive a receiver entry.

Frozen answer:
Top action: Thunder. Confidence: medium-high.

Ranked candidates:

1. Thunder.
2. Counter-handoff only if the Electric receiver gains more than Cloyster loses.
3. Rest or preserve only if Zapdos cannot afford the exchange.

Reason:
The active move converts through the expected switch because it removes or
cripples the support piece before the receiver gets a stable board.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Espeon Growth Package

Public state:
p1 Tyranitar with Crunch and Pursuit faces p2 Espeon. Espeon has revealed
Morning Sun and just used Growth. Hidden Power coverage is not public. Espeon
is low enough that Crunch KOs if it stays.

Frozen answer:
Top action: Crunch. Confidence: high.

Ranked candidates:

1. Crunch.
2. Pursuit only if leaving is the strongest branch and Crunch fails to deny the
   package.
3. Switch only if revealed coverage makes Tyranitar unable to deny Growth.

Reason:
Once Growth is public, remove the package before it gets another recovery,
coverage, or pass turn. Pursuit is only top if the flee branch dominates.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Revealed Espeon Coverage Reclassification

Public state:
p2 Espeon has revealed Growth, Morning Sun, and Hidden Power Water into
Tyranitar. p1 Tyranitar survived but can no longer safely absorb a second hit.
p1 has a healthy Snorlax and a phazer class unrevealed by exact identity.

Frozen answer:
Top action: hand off to the public package answer, preferably Snorlax or the
phazer class if it enters safely. Confidence: medium.

Ranked candidates:

1. Snorlax/phazer handoff.
2. Crunch only if it KOs before Espeon heals or attacks.
3. Pursuit only if Espeon must flee and Tyranitar survives the revealed hit.

Reason:
After coverage reveal, Tyranitar is no longer a generic Espeon owner. Reclassify
the branch around revealed coverage and preserve the trapper only if it still
does the job.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - RestTalk Tiering Discipline

Public state:
p1 Zapdos has just used Rest in front of p2 Raikou. Sleep Talk has not been
publicly revealed. In side-known mode Zapdos has Sleep Talk; in spectator-public
mode it is only a strong prior. p1 also has Snorlax and Nidoking as public
handoff classes.

Frozen answer:
Top action: split by information tier. In side-known mode, Sleep Talk. In
spectator-public mode, name Sleep Talk as a strong-prior branch and keep
Snorlax/Nidoking handoff as the fallback. Confidence: medium.

Ranked candidates:

1. Sleep Talk only if revealed or side-known.
2. Snorlax/Nidoking handoff as public fallback.
3. Stay asleep without Sleep Talk only if it burns a safe turn and preserves the
   better owner.

Reason:
RestTalk is common and route-relevant, but pre-reveal public advice must not
pretend the move is fact.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - CurseLax Rest-Clock Timing

Public state:
p1 Snorlax at +2 and 55% has Double-Edge, Curse, and Rest revealed. It faces
p2 Raikou at full HP with RestTalk and Thunder revealed. Raikou wakes this turn
or can Sleep Talk Thunder; p1 side has Spikes down.

Frozen answer:
Top action: Rest. Confidence: high.

Ranked candidates:

1. Rest.
2. Double-Edge only if it creates an immediate KO or forces an irreversible
   route before Thunder.
3. More Curse only if the next Thunder cannot put Snorlax below the route's
   survival threshold.

Reason:
The boost is already banked. The next route-converting move is spending Rest
before Thunder removes the boosted Snorlax.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer only after starting
from `active_context.md`. When item utility, Growth/Morning Sun, or RestTalk
boost timing appears, freeze this sequence:

1. Is a no-item or item-denial move the converter before status?
2. Does the active hit remove a support piece through the expected receiver?
3. Has a Growth/recovery/Baton Pass package become public?
4. Is Sleep Talk revealed, side-known, strong-prior, or possible-only?
5. Does the boosted route need attack, Rest, another setup turn, or handoff in
   the next two turns?
