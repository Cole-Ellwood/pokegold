# Named Pivot Coverage Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_041` turns 59-60 into a three-prompt
micro-drill: if a pivot is named as serious, the selected action must hit it,
double into it, or explicitly accept it. A move that only pressures the active
target fails branch coverage.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/quick_tests/branch_coverage_spin_phaze_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_041_branch_coverage_transfer_smogtours-gen2ou-931101_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Tyranitar:
  `https://www.smogon.com/forums/threads/gsc-ou-tyranitar.3676727/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Source note: the Tyranitar and sample-team material support the key coverage
point: Tyranitar's value comes from matching the coverage or utility move to
the expected target, such as Fire Blast into Steel-types, Pursuit/Roar for
Ghost and setup control, and Rock/Ground/Fighting coverage across different
switch trees. The probe below does not import team preview; each prompt only
uses revealed or explicitly supplied public branches.

## Score Summary

Scenarios: 3.

Action-policy hits: 3 / 3.

Named-pivot coverage hits: 3 / 3.

Route-job hits: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. The prompts are constructed from a known
failure class and should be followed by a fresh replay transfer.

## Scenario 1 - Starmie To Snorlax After Spin Block

Public state:

```text
Vanilla GSC. Our Gengar is active at 87% against poisoned Starmie at 87%.
Gengar has Thunderbolt revealed. Starmie has Rapid Spin / Recover / Substitute
/ Surf revealed and just had Rapid Spin blocked by Gengar. Opponent has
Snorlax at 67% and Raikou asleep in reserve. Spikes are on the opponent's
side. Our Tyranitar is healthy and has Dynamic Punch / Earthquake / Fire Blast
/ Rock Slide revealed.
```

Named serious branch: Starmie switches to Snorlax to preserve itself and
absorb Thunderbolt while keeping the spinner alive for later.

Tempting move: Gengar Thunderbolt.

Frozen answer: switch Tyranitar. Confidence: medium-high.

Branch coverage: Thunderbolt covers Starmie staying to Recover or Substitute,
but it does not cover the named Snorlax pivot. Tyranitar covers the pivot by
entering on Snorlax and threatening Dynamic Punch or Rock Slide while Spikes
tax the switch.

Score: pass.

## Scenario 2 - Snorlax To Misdreavus Into Fighting Coverage

Public state:

```text
Vanilla GSC. Our Tyranitar is active at 93% against opposing Snorlax at 60%.
Tyranitar has Dynamic Punch / Earthquake / Fire Blast / Rock Slide revealed.
Opponent has sleeping Misdreavus at 100% in reserve, already shown as a
Normal/Fighting immunity. Spikes are on the opponent's side. Snorlax is worth
preserving because it is the main special sponge.
```

Named serious branch: opponent switches Snorlax to Misdreavus, taking Spikes
but blanking Fighting coverage.

Tempting move: Dynamic Punch into Snorlax.

Frozen answer: use Earthquake as the coverage midground, or double only if the
post-double route is clearer. Confidence: medium.

Branch coverage: Dynamic Punch pressures Snorlax but fails the named
Misdreavus branch. In GSC, Misdreavus has no Levitate, so Earthquake still
hits it while also making progress if Snorlax stays. Rock Slide is another
damage line, but Earthquake is the cleaner named-branch cover here.

Score: pass.

## Scenario 3 - Steel Pivot Into Tyranitar Coverage

Public state:

```text
Vanilla GSC. Our Tyranitar is active at 88% against opposing Snorlax at 55%.
Tyranitar has Dynamic Punch / Earthquake / Fire Blast / Rock Slide revealed.
Opponent has Skarmory at 78% and Forretress at 35% in reserve. Both are public
Steel-type pivots that can enter on Fighting/Ground pressure, but both dislike
Fire Blast. Spikes are on the opponent's side. Snorlax is not yet in KO range
from ordinary damage.
```

Named serious branch: opponent preserves Snorlax by pivoting Skarmory or
Forretress into Tyranitar's Fighting/Ground move.

Tempting move: Dynamic Punch or Earthquake into Snorlax.

Frozen answer: use Fire Blast if the Steel pivot is the branch being covered.
Confidence: medium-high.

Branch coverage: Fire Blast is the move that affects the named Steel pivot.
Dynamic Punch is stronger into Snorlax but repeats the failure pattern: it
names a pivot and then does not punish that pivot. If the advisor thinks
Snorlax staying is overwhelmingly more likely, the Steel pivot should be
downgraded rather than kept in the serious-branch list.

Score: pass.

## Resulting Checklist

Before finalizing a move after naming a pivot:

1. Does the move hit the active target only, or does it also hit the named
   pivot?
2. If it fails the pivot, is there a midground that hits both?
3. If there is no midground, is a double switch better than an active-target
   attack?
4. If the active-target attack is still best, demote the pivot from "serious"
   or state why accepting it is worth the route loss.

## Next Study Target

Fresh replay transfer with this exact check in the turn table:

```text
Named pivot:
Selected action affects pivot? yes/no
If no, why is accepting it correct?
```
