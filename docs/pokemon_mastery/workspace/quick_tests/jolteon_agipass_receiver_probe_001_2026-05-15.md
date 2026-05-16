# Jolteon AgiPass Receiver Probe 001 - 2026-05-15

Type: focused regression probe after `jolteon_agipass_receiver_transfer_001`.

Status: nonblind constructed drill. This checks whether the dry Baton Pass
lesson can be stated as concrete move choices without breaking information
tiering. It is not fresh replay proof and must not count as mastery progress.

Source basis:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/jolteon_agipass_receiver_review_001_2026-05-15.md`
- Smogon GSC OU Threatlist, Jolteon section:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC OU Speed Tiers:
  `https://www.smogon.com/resources/competitive/gs/gsc_speedtiers`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums GSC BP:
  `https://www.smogon.com/forums/threads/gsc-bp.3541165/`

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

Result: pass as regression only. The answers reopened boost and receiver
ledgers after dry Baton Pass, named defender answers, and did not anchor on
possible-only hidden receivers.

## Scenario 1 - Dry Pass Revealed, Next Jolteon Turn

Public state:
p1 Jolteon previously revealed Baton Pass by handing to Cloyster. Later p1
Jolteon faces p2 Zapdos. p1 has revealed Machamp in back. p2 has revealed
Tyranitar and Zapdos, with Snorlax possible but unrevealed.

Frozen answer:
Top action: Agility. Confidence: medium.

Ranked candidates:

1. Agility.
2. Baton Pass directly to Machamp if Tyranitar or Snorlax is clearly entering
   immediately.
3. Thunderbolt/Thunder if Zapdos is staying and the pass receiver does not
   improve the next two turns.

Reason:
The public Baton Pass reveal means Jolteon is a package, not only a pivot.
Agility converts if the opponent switches to a normal or Rock route owner and
sets up Machamp as the named receiver.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Boost Banked, Receiver Named

Public state:
p1 Jolteon has used Agility and is at +2 Speed. p2 switched Snorlax into the
turn and took Spikes. p1 has revealed Machamp. Snorlax has not revealed phaze
or Lovely Kiss.

Frozen answer:
Top action: Baton Pass to Machamp. Confidence: medium-high.

Ranked candidates:

1. Baton Pass to Machamp.
2. Thunderbolt/Thunder only if Snorlax is in range where the attack changes
   the route before Rest or Curse.
3. Switch to a defensive owner only if the receiver route is blocked by a
   revealed phaze or status line.

Reason:
The boost exists to change the receiver board. Passing to the revealed Fighting
breaker is the route-converting move; attacking Snorlax is generic unless it
creates a concrete threshold.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Machamp Into Tyranitar With Zapdos Receiver

Public state:
p1 Machamp faces p2 Tyranitar. p2 has already shown Zapdos and used it as the
clean Fighting receiver. Tyranitar has revealed Rock Slide and Thunderbolt,
not Earthquake. p1 has Jolteon healthy.

Frozen answer:
Top action: switch Jolteon. Confidence: medium.

Ranked candidates:

1. Switch Jolteon to punish the Zapdos receiver.
2. Cross Chop if Tyranitar staying removes a route piece immediately.
3. Rock Slide only if Zapdos staying in front of Machamp is the strongest
   public branch and the handoff is too expensive.

Reason:
The visible Machamp/Tyranitar matchup is not the whole board. Once Zapdos is
the named receiver, the positive move is the counter-handoff that meets it.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Defender Into Public Jolteon Pass With Revealed Phaze

Public state:
p2 Zapdos faces p1 Jolteon. Jolteon has revealed Baton Pass but not Agility
yet. p1 has revealed Machamp. p2 Zapdos has revealed Whirlwind, and p2 also
has Snorlax healthy and Tyranitar revealed.

Frozen answer:
Top action: Whirlwind. Confidence: high.

Ranked candidates:

1. Whirlwind.
2. Attack with Thunder if Jolteon is low enough that damage denies boost/pass.
3. Switch Snorlax only if it puts the revealed receiver into revenge range or
   beats the receiver board after pass.

Reason:
Once phaze is revealed, the defender can deny the package directly. If phaze
is only possible, it stays a high-risk read with attack or concrete receiver
damage as the fallback.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Hidden Receiver Discipline

Public state:
p1 Jolteon has revealed Baton Pass against p2 Zapdos, but no p1 teammates are
revealed except Cloyster. p2 expects a slow physical breaker but has no
Team Preview.

Frozen answer:
Top action: Agility or dry Baton Pass to the revealed/likely receiver class,
with exact receiver left unnamed. Confidence: medium.

Ranked candidates:

1. Agility/pass route by class: physical breaker, Snorlax-like owner, or
   support receiver depending on future reveals.
2. Electric attack if Zapdos stays and the attack improves the route.
3. Exact Machamp or Marowak call only as a high-risk read with the class
   fallback stated.

Reason:
The package is public, but the exact teammate is not. Positive selection names
the receiver class and fallback rather than anchoring on a hidden exact mon.

Grade: top. Tags: positive, route, branch.

## Scenario 6 - Lure Coverage Reclassifies After Reveal

Public state:
p2 Tyranitar entered into Jolteon/Cloyster routing and has now revealed
Thunderbolt into Cloyster. p1 later considers sending Cloyster into Tyranitar
again.

Frozen answer:
Top action: do not repeat the Cloyster handoff; route through the safer owner
or punish Tyranitar's receiver. Confidence: medium-high.

Ranked candidates:

1. Handoff to a safer Tyranitar owner or counter-switch to the expected
   receiver.
2. Attack Tyranitar if the active mon can convert before the lure coverage
   matters.
3. Cloyster only if it survives and still completes a concrete job such as
   Spikes, Explosion, or forced damage.

Reason:
Before reveal, Thunderbolt was not anchorable. After reveal, it is public role
information and must change the future receiver map.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh replay transfer. When Baton Pass
appears, freeze this sequence:

1. Is Baton Pass just a dry handoff, or has it made a package public?
2. Which boost, Substitute, coverage, or status follow-up becomes live next?
3. Which receiver is revealed, strong-prior, or possible-only?
4. What does the defender use to deny the receiver board?
5. Does the chosen move improve the route over two turns, or merely avoid an
   immediate blunder?
