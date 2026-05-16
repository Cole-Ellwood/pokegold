# CurseLax Receiver/Coverage Probe 001 - 2026-05-15

Type: focused regression probe after
`curselax_receiver_coverage_transfer_001`.

Status: nonblind constructed drill. This checks whether the CurseLax receiver
lesson can be stated as concrete move choices without breaking no-Team-Preview
or hidden-move discipline. It is not fresh replay proof and must not count as
mastery progress.

Source basis:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/curselax_receiver_coverage_review_001_2026-05-15.md`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Gengar:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon Forums, GSC OU Threat List:
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

Result: pass as regression only. The answers separated revealed/side-known
coverage from strong-prior and possible-only coverage, and they chose the move
that improved through the named receiver instead of defaulting to safe setup.

## Scenario 1 - Side-Known Earthquake Into Receiver

Public state:
p1 Snorlax is +1 from Curse at 100% against p2 sleeping Snorlax at 100%. p2 has
Spikes on its side. The side-known p1 set is Curse, Rest, Double-Edge, and
Earthquake. p2 has revealed a healthy Gengar and may have a physical wall or
phazer unrevealed.

Frozen answer:
Top action: Earthquake. Confidence: medium-high.

Ranked candidates:

1. Earthquake.
2. Curse again if the opponent stays asleep and no receiver enters.
3. Rest only if status or damage changes the timer.

Reason:
The named branch is a receiver, not only the sleeping Snorlax. Earthquake hits
Gengar and many Rock/Steel branches and still pressures a physical wall after
Spikes. Because the move is side-known, this is not hidden-info anchoring.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Spectator Public Strong Prior With Fallback

Public state:
p1 Snorlax is +1 from Curse at 100% against p2 sleeping Snorlax at 100%. p1 has
revealed only Curse. No team sheet is available. p2 has revealed Gengar and can
also have a hidden physical wall or phazer.

Frozen answer:
Top action: coverage attack if Earthquake is in the public/side-known set;
otherwise Curse is the fallback. Confidence: medium-low.

Ranked candidates:

1. Earthquake by class only if revealed or side-known; state the fallback.
2. Curse again if coverage is not available or the receiver cannot reset.
3. Double-Edge/Body Slam only if the receiver branch is unlikely or coverage is
   absent.

Reason:
Curse makes Earthquake a strong-prior branch, but spectator-public mode cannot
turn it into fact. The positive selection is the information-tiered answer:
name the coverage branch and fallback instead of either pretending Earthquake
is revealed or ignoring it.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Revealed Coverage Over Generic STAB

Public state:
p1 Snorlax is +1 at 88% against p2 Gengar at 93%. p1 Snorlax has revealed
Curse and Earthquake. p2 Gengar is healthy and may use Explosion, Hypnosis, or
switch to a physical wall.

Frozen answer:
Top action: Earthquake. Confidence: high.

Ranked candidates:

1. Earthquake.
2. switch if preserving Snorlax is more important than removing Gengar pressure.
3. Curse only if Gengar cannot punish this turn.

Reason:
Once Earthquake is public, generic Normal STAB and more setup are below the
coverage that hits the named Ghost branch.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Coverage Absent, Setup Is The Route

Public state:
p1 Snorlax is +1 at 100% against p2 sleeping Snorlax at 100%. p1 Snorlax has
revealed all four moves: Curse, Rest, Body Slam, and Sleep Talk. p2 has a
healthy Gengar revealed.

Frozen answer:
Top action: Curse or handoff, not Earthquake. Confidence: high.

Ranked candidates:

1. Curse if p2 cannot immediately phaze or explode.
2. switch to the Ghost/special owner if Gengar enters and Snorlax cannot touch
   it.
3. Body Slam only if the opponent stays asleep or paralysis changes the route.

Reason:
Four revealed moves remove the hidden coverage branch. This is the opposite
boundary: do not keep pricing Earthquake after the public set excludes it.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Defending With The Physical Owner Class

Public state:
p2 Snorlax is asleep at 100% against p1 +1 Snorlax. p1 has revealed Curse but
not coverage. p2 has revealed Gengar, and has an unrevealed Cloyster-like
physical wall available in side-known mode. Spikes are on p2's side.

Frozen answer:
Top action: switch the physical wall/boom owner if side-known, with Gengar as
the fallback if no better owner is available. Confidence: medium.

Ranked candidates:

1. Cloyster/physical wall owner.
2. Gengar guard if Earthquake is not revealed or if preserving the physical
   wall is more important.
3. stay asleep only if the switch gives up more route equity than it saves.

Reason:
The defender should leave the sleeping Snorlax, but the owner class matters.
Gengar guards Normal/Explosion; Cloyster-like owners answer boosted physical
pressure and can threaten their own support or cash-out route.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Possible-Only Coverage Cannot Become Fact

Public state:
p1 Snorlax is +1 at 100% against p2 sleeping Snorlax. p1 has revealed Curse,
Double-Edge, Rest, and Sleep Talk. p2 has a revealed Gengar. No team sheet is
available.

Frozen answer:
Top action: Curse or switch according to the Gengar branch; do not recommend
Earthquake. Confidence: high.

Ranked candidates:

1. switch to the Gengar answer if Gengar enters.
2. Curse if p2 stays asleep and no phazer/reset branch is live.
3. Double-Edge only if the active sleeping Snorlax stays and damage matters.

Reason:
Earthquake is impossible after four revealed moves. Hidden-info discipline means
the receiver map changes immediately once public facts remove the coverage.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. On every CurseLax
or boosted-physical turn, freeze this receiver check:

1. Which receiver owns the next board?
2. Which coverage/status/setup/rest/handoff action beats that receiver?
3. Is the coverage revealed, side-known, strong prior, possible-only, or
   impossible after four revealed moves?
4. What is the fallback if the coverage branch is absent?
