# Lead Sleep/Handoff Probe 001 - 2026-05-15

Type: focused regression probe after `lead_sleep_handoff_transfer_001`.

Status: nonblind constructed drill. This checks whether the lead sleep handoff
lesson can be stated as concrete move choices without breaking information
tiering. It is not fresh replay proof and must not count as mastery progress.

Source basis:

- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/lead_sleep_handoff_review_001_2026-05-15.md`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Nidoking Revamp:
  `https://www.smogon.com/forums/threads/nidoking-revamp-qc-3-2-gp-2-2.3481273/`
- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`

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

Result: pass as regression only. The answers preserved the sleep absorber when
its job was complete, used Sleep Talk only when public or strongly supported
with fallback, and did not anchor on possible-only coverage.

## Scenario 1 - Repeat Sleep Before Spikes Follow-Up

Public state:
p1 Nidoking faces p2 Cloyster turn 2. Nidoking revealed Lovely Kiss and missed.
Cloyster revealed Spikes, and p1 now has Spikes on its side. No Pokemon is
asleep. Nidoking has not revealed coverage.

Frozen answer:
Top action: Lovely Kiss. Confidence: medium-high.

Ranked candidates:

1. Lovely Kiss.
2. Thunder/electric coverage if revealed or side-known.
3. Earthquake or double-switch only if the incoming absorber is already named.

Reason:
Sleep is still live and public. Coverage is useful, but unrevealed coverage
cannot outrank the immediate sleep route unless side-known.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Absorber Did Its Job

Public state:
p2 Heracross switched into Nidoking's Lovely Kiss and is now asleep. Nidoking
has revealed only Lovely Kiss. Heracross has not revealed Sleep Talk. p1 has a
healthy Zapdos that threatens Heracross and pressures Snorlax; p2 has a likely
Snorlax owner.

Frozen answer:
Top action: switch Zapdos. Confidence: medium.

Ranked candidates:

1. Zapdos handoff.
2. coverage only if Fire Blast or equivalent is revealed or side-known.
3. Nidoking attack if the opponent is forced to burn sleep turns.

Reason:
Heracross's public job was absorbing sleep. Without revealed Sleep Talk or
revealed coverage, the next board is the handoff, not damage into a sleeping
target.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Revealed Sleep Talk Can Stay

Public state:
p2 Heracross is asleep against p1 Nidoking. Heracross has revealed Sleep Talk,
Megahorn, and Rest. Nidoking has revealed Lovely Kiss and Earthquake, but no
Fire coverage. Switching Snorlax in gives Nidoking a free double.

Frozen answer:
Top action: Sleep Talk. Confidence: medium.

Ranked candidates:

1. Sleep Talk.
2. switch Snorlax if Nidoking's next owner is Zapdos or another special route.
3. switch Cloyster only if it preserves more than Heracross's active roll.

Reason:
Once Sleep Talk is public, staying can convert. This is the opposite boundary
from guessing Sleep Talk before reveal.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Possible-Only Fire Coverage Cannot Anchor

Public state:
p1 Nidoking is active against sleeping p2 Heracross. Nidoking has revealed
Lovely Kiss and Earthquake only. Fire Blast is legal but unshown. p1 has Zapdos
available, and p2 has shown Cloyster plus a likely Snorlax owner.

Frozen answer:
Top action: switch Zapdos. Confidence: medium.

Ranked candidates:

1. Zapdos handoff.
2. Ice Beam/Thunder if revealed or side-known and it changes the receiver map.
3. Fire Blast only as a high-risk read with the handoff fallback.

Reason:
Possible-only Fire coverage cannot be the main line. The public route is to
move the pressure owner while the sleeping absorber is preserved or switched.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Zapdos Into Snorlax Without Opposing Spikes

Public state:
p1 Zapdos is active at full against p2 Snorlax at full. Spikes are on p1's
side, not p2's. p1 has Cloyster available. p2 Snorlax has not revealed moves
but can Curse or attack.

Frozen answer:
Top action: switch Cloyster. Confidence: medium.

Ranked candidates:

1. Cloyster handoff.
2. Thunder if p2 Snorlax is already chipped, paralyzed, or p2 has Spikes.
3. status/support only if it hits the Snorlax route before Rest or Curse.

Reason:
Zapdos pressure is much less converting when Snorlax is not taking Spikes.
Cloyster owns the Curse/physical board and can threaten Spikes, Toxic, Surf, or
Explosion later.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Snorlax Setup Into Expected Handoff

Public state:
p2 Snorlax is active at full against p1 Zapdos. p1 has already shown a likely
Cloyster handoff. p2 Snorlax has not revealed moves. No status is on Snorlax.

Frozen answer:
Top action: Curse. Confidence: medium.

Ranked candidates:

1. Curse.
2. Body Slam/Double-Edge if Zapdos is staying and damage/paralysis changes the
   route immediately.
3. Lovely Kiss only if p1 has not already spent sleep or lacks a good absorber.

Reason:
Curse improves through Zapdos leaving and through many physical receivers. It
is the positive branch-punish when the opponent is likely to hand off rather
than stay for raw Thunder.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. On lead sleep
turns, freeze this sequence:

1. Is sleep still live for this side?
2. Did the absorber's job finish when sleep landed?
3. Is Sleep Talk revealed, strong-prior with fallback, or only possible?
4. Who owns the next board if the sleeper switches out?
5. Does active pressure convert without opponent-side Spikes, or is a handoff
   needed?

