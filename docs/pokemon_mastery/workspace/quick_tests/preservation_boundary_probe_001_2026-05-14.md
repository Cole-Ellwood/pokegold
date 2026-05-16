# Preservation Boundary Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks the replay 064
cash-out, sleep, and hazard-timing misses. It is not fresh replay-transfer
evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer before
treating this boundary as stable.

## Scenario 1 - Low RestTalk Zapdos Rest Before Cash-Out

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos is active at 21% against an
opposing Exeggutor at 65%. Spikes are on both sides. Zapdos has Hidden Power,
Rest, and Sleep Talk available from known set context. Exeggutor has revealed
Psychic and Thief. Hidden Power damages Exeggutor, but does not remove it from
the board. Rest will heal before Exeggutor's likely Psychic lands.
```

Tempting move: Hidden Power because Zapdos is low, hazards make future entry
hard, and Exeggutor is in range of meaningful chip.

Frozen answer: use Rest if Zapdos still has a route-defining job as a RestTalk
Electric and Hidden Power does not open a named converter. The branch-covering
question is not "can Zapdos get one more hit?" but "does cashing out remove a
blocker, or does Rest preserve the better long route?" Confidence: medium.

Classification: preserve low RestTalk route piece before cash-out.

Score: pass.

## Scenario 2 - Sleeping RestTalk Stays To Cover Ground Pivot

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos is active at 33% asleep with
Sleep Talk and Hidden Power revealed. Spikes are on both sides. Opposing
Exeggutor is at 31%, and the opponent has a hidden Ground-type pivot that would
like to enter on an Electric move or a passive switch. Snorlax can switch in for
you, but that gives the opponent a free board if they pivot.
```

Tempting move: switch Zapdos out because a sleeping Pokemon is often preserved
for Sleep Clause value instead of burning turns.

Frozen answer: stay and use Sleep Talk if that action covers both the low
Exeggutor and the likely Ground pivot. The sleep rule is a tendency, not a
script; RestTalk plus coverage can still perform the active job this turn.
Confidence: medium.

Classification: sleeping RestTalk route piece has an active branch-covering
job.

Score: pass.

## Scenario 3 - Non-RestTalk Sleeper Switches To Preserve Sleep Clause Value

Public state:

```text
Vanilla GSC spectator-public state. Your Exeggutor was put to sleep by Lovely
Kiss and has no revealed Sleep Talk. Sleep Clause is now active against your
team while Exeggutor remains asleep. Opposing Snorlax is healthy enough to
Curse or attack. You have Skarmory and Gengar available as live responses.
Exeggutor can stay to burn a sleep turn, but it does not threaten meaningful
damage, recovery denial, or setup denial this turn.
```

Tempting move: stay in to burn sleep turns because waking sooner sounds like
progress.

Frozen answer: switch out and save the sleeping Exeggutor unless it has a
specific active job. The preserved sleeper keeps Sleep Clause value and may
absorb or pivot later; staying only helps if it denies a named route that the
bench cannot cover. Confidence: medium-high.

Classification: switch sleeping non-RestTalk piece when burning turns has no
route job.

Score: pass.

## Scenario 4 - Forretress Sets Reciprocal Spikes Before Spinblock Timing

Public state:

```text
Vanilla GSC spectator-public state. Your Snorlax is active at 100% against an
opposing Forretress at 94%. Spikes are on the opponent's side only.
Forretress has just entered through Spikes and has not set its own layer yet.
You have Gengar available as a spinblocker. Snorlax can Earthquake, while
Gengar can enter on Rapid Spin but takes Spikes once they are up.
```

Tempting move: switch Gengar immediately because Forretress is a spinner and
your Spikes are already up.

Frozen answer: do not auto-spinblock before pricing Forretress's current job.
If your side has no Spikes yet, reciprocal Spikes is a major branch; staying
with Snorlax and using Earthquake can punish that support turn while preserving
Gengar for the later Spin or Explosion branch. Confidence: medium.

Classification: reciprocal layer before spinblock timing.

Score: pass.

## Resulting Checklist

When choosing preserve, cash-out, sleep stay, sleep switch, or spinblock:

1. Does the low piece still have a route-defining job after this turn?
2. Does the cash-out remove a named blocker or only create damage?
3. If asleep, does this Pokemon have Sleep Talk, coverage, or a denial job?
4. If asleep without an active job, what does switching preserve?
5. For Forretress, is the current job Spikes, Spin, Explosion, or pivot?
6. Does the spinblocker need to enter now, or after the support job is claimed?

## Next Transfer Check

Run a fresh no-keyword-screen replay packet focused on preservation boundaries.
For each turn, record the route job of the low or sleeping piece, the opponent's
best support branch, and why the chosen action beats preserve, cash-out,
spinblock, or handoff alternatives.
