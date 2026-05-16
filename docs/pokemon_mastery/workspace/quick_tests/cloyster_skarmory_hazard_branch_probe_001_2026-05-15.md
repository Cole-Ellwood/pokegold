# Cloyster/Skarmory Hazard Branch Probe 001 - 2026-05-15

Type: focused regression probe after
`cloyster_skarmory_hazard_branch_transfer_001`.

Status: nonblind constructed drill. This protects the new policy boundary, but
it is not fresh replay proof and must not be counted as mastery progress.

Source basis:

- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `reviews/cloyster_skarmory_hazard_branch_review_001_2026-05-15.md`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`

## Score Summary

Scenarios: 5.
Top-match: 5 / 5.
Acceptable-match: 5 / 5.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 5 / 5.
Route-converting move chosen: 5 / 5.
Branch-punish chosen: 5 / 5.

Result: pass as a regression check only. The answers obeyed side ownership,
missing-layer, next-owner, and branch-conversion ordering, but the prompt set
was authored from the known miss.

## Scenario 1 - Missing Layer First

Public state:
p1 Cloyster is active at 91% against p2 Skarmory at 100%. p1 side has Spikes;
p2 side has no Spikes. p1 Cloyster has revealed Surf and Spikes. p2 Skarmory
has revealed Toxic only. p2 has no revealed spinner, no revealed Electric, and
no active setup threat.

Frozen answer:
Top action: Spikes. Confidence: medium-high.

Ranked candidates:

1. Spikes.
2. Surf into Skarmory or an opposing Cloyster branch.
3. Switch to Electric pressure if Skarmory reveals Whirlwind or an Electric
   receiver enters.

Reason:
The opponent's side is unspiked and Cloyster is already active. No public
branch makes immediate Surf or Spin more converting than placing the missing
layer. If p2 switches to Cloyster, Surf becomes the next turn's branch punish,
not the first action.

Grade: top. Tags: positive, route, branch.

## Scenario 2 - Surf Beats Reflex Spin

Public state:
Both sides have Spikes. p1 Cloyster is active at 88% poisoned against p2
Skarmory at 100%. p1 Cloyster has revealed Surf, Spikes, and Rapid Spin. p2
Skarmory has revealed Toxic. p2 Cloyster is revealed at 70% and is the only
revealed p2 hazard owner; p2 Zapdos is also revealed but does not want repeated
Surf chip. p1 has a healthy Electric in back.

Frozen answer:
Top action: Surf. Confidence: medium.

Ranked candidates:

1. Surf.
2. Rapid Spin.
3. Switch to the Electric if Zapdos or Skarmory pressure is named.

Reason:
Own-side Spikes make Rapid Spin real, but the named branch is p2 preserving
Skarmory and re-entering Cloyster to keep the hazard cycle alive. Surf hits
that owner and can put it into removal or Explosion range. Spin is the fallback
if p2 stays passive or lacks the reset owner.

Grade: top. Tags: positive, route, branch.

## Scenario 3 - Spin Is The Route Move

Public state:
Both sides have Spikes. p1 Cloyster is active at 72% against p2 Skarmory at
100%. p2 Cloyster is fainted. p2 Starmie is revealed at 31% paralyzed and
cannot safely enter Surf plus Spikes. p2 Skarmory has revealed Toxic and
Whirlwind but has not revealed Drill Peck. p1's next converter is a grounded
Snorlax that cannot afford another entry tax.

Frozen answer:
Top action: Rapid Spin. Confidence: high.

Ranked candidates:

1. Rapid Spin.
2. Surf.
3. Switch to Electric pressure after clearing.

Reason:
p1's own side is taxed, the opponent's side is already spiked, and the revealed
setter is gone. The remaining spinner cannot reset or remove safely. Clearing
the entry tax preserves the grounded Snorlax route more than Surf chip into a
passive Skarmory.

Grade: top. Tags: positive, route, branch.

## Scenario 4 - Counter-Handoff Beats Field Job

Public state:
p1 Cloyster is active at 94% against p2 Skarmory at 100%. Both sides have
Spikes. p2 Zapdos is revealed at 82% and has repeatedly entered on Cloyster to
avoid Spikes and force it out. p1 Raikou is revealed at 90% and is the team's
Zapdos owner. p1 Cloyster has revealed Surf, Spikes, and Rapid Spin.

Frozen answer:
Top action: switch to Raikou. Confidence: medium.

Ranked candidates:

1. Raikou handoff.
2. Surf if p2 stays Skarmory or goes Cloyster.
3. Rapid Spin if p2 cannot keep Zapdos pressure.

Reason:
The named owner is Zapdos, not the field state. Surf chip is acceptable, and
Spin can matter later, but the immediate branch-converting move is the handoff
that meets Zapdos without letting it freely force Cloyster out.

Grade: top. Tags: positive, route, branch.

## Scenario 5 - Toxic Into The Spinner Branch

Public state:
p1 Cloyster is active at 86% against p2 Skarmory at 100%. p2 side has Spikes;
p1 side is clean. p1 Cloyster has revealed Surf, Spikes, and Toxic. p2 Starmie
is revealed at 100% with Rapid Spin and Recover. p2 Skarmory cannot be poisoned
but has been leaving Cloyster for Starmie whenever hazards are up.

Frozen answer:
Top action: Toxic. Confidence: medium.

Ranked candidates:

1. Toxic into Starmie.
2. Surf.
3. Switch to Electric pressure.

Reason:
Rapid Spin is impossible progress because p1's side is clean. Spikes already
tax p2. The named branch is Starmie entering to clear; Toxic changes the
Recover/Spin loop and is the branch punish. If Skarmory stays, the move fails,
but the fallback remains Surf or Electric handoff on the next board.

Grade: top. Tags: positive, route, branch.

## Next Use

The next countable action should be a fresh unseen replay transfer with this
checklist active:

1. Whose side has Spikes?
2. Is a missing layer available now?
3. Who is the opponent's next owner: setter, spinner, flyer, Electric, Ghost,
   phazer, or setup threat?
4. Which action beats that owner before defaulting to Spikes or Rapid Spin?
