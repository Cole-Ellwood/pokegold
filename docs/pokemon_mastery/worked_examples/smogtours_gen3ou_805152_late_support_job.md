# Worked Example: Late Support Job Preservation

Source review: `../reviews/2026-05-13_smogtours-gen3ou-805152.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen3ou-805152

Source context:
https://www.smogon.com/forums/threads/adv-swiss-i-top-8.3754448/

Format: ADV OU. This is a transfer artifact from expert play, not a romhack
mechanics claim.

## Source Lesson

In the replay, the opening support route fails: Agility is passed from Zapdos
to Celebi, but Celebi is removed by Salamence. The decisive support move comes
much later. Vaporeon is low, triggers Salac Berry, and Baton Passes the Speed
boost to Metagross for the final KO.

The transferable idea is that a support Pokemon's job can narrow over time.
When the broad role is gone, do not automatically call the piece expendable.
Ask whether it still owns one route-changing action.

## Position Pattern

```text
Support piece:
  low HP or no longer able to perform its original broad role

Remaining job:
  one pass, screen, weather reset, spinblock, status absorption, Encore,
  sacrifice entry, speed control, or final pivot

Beneficiary:
  the converter that immediately improves if the support job happens

Opponent route:
  the punish that wins if the support piece is thrown away too early
```

## Candidate Move Classes

Best when available:

- Preserve the support piece if its one remaining job creates the next forced
  route.
- Spend a different piece if that creates the support piece's final entry.
- Use the support move immediately when the trigger and receiver are both live.

Acceptable:

- Sacrifice the support piece only if the beneficiary can already convert
  without it, or if the support job is blocked by public state.
- Switch away from the support piece when the current turn would waste the job
  into a no-effect branch.

Wrong:

- Treating low HP as the same thing as no job.
- Using the support move without naming the receiver and route.
- Preserving the support piece after the receiver is gone or the trigger can no
  longer happen.

## Boss-Battle Transfer

Use this form during Gym Leader Lab advice:

```text
Original role:
Current narrow job:
Receiver / beneficiary:
Trigger needed:
Can it still act?:
Route opened:
Route lost if sacrificed:
Opponent punish if preserved:
Verdict:
```

Example boss-facing translations:

- A low-HP weather setter may be worth preserving if it can reset sun or rain
  for the final attacker.
- A damaged screen setter may still be worth saving if one screen lets the true
  answer survive setup damage.
- A nearly spent spinner or spinblocker may still decide a hazard endgame if
  one layer or one Spin changes all entry math.
- A Baton Pass or Encore user is not "support done" until the receiver map says
  no live teammate benefits from the last support action.

## Failure Signs

- "It is low, so sack it."
- "It is a support Pokemon, so use support now."
- "It already did its job."
- No receiver, trigger, or route is named.
- The support piece is preserved after its beneficiary has fainted.

## Rule

Low HP changes a support Pokemon's job from broad to narrow. It does not decide
expendability by itself.

Before sacrificing it, prove:

```text
no live receiver benefits;
or the trigger cannot happen;
or the opponent punish is worse than the support route;
or a different route has already become forced.
```

If none of those are true, keep the piece's last job in the route ledger.
