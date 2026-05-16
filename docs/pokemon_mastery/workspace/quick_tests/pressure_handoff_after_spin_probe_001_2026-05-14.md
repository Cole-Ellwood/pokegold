# Pressure Handoff After Spin Probe 001 - 2026-05-14

Mode: constructed policy regression. This is not a fresh replay score, not a
holdout, and not final-exam evidence. It exists to harden the errors from
`replay_turn_pause_033_pressure_handoff_after_spin_smogtours-gen2ou-934324_2026-05-14.md`.

Purpose: test six branches after Starmie, Cloyster, Zapdos, Gengar, Snorlax,
and Spikes create a hazard-control fork:

- allow Rapid Spin when the pressure handoff is stronger than the layer;
- block Rapid Spin when the layer is the immediate route;
- reset Spikes on a Resting or sleeping Snorlax;
- cash out a spent Cloyster with Explosion;
- preserve Cloyster when it still has a real support job;
- carry the weather and sleep clock instead of assuming the last attack repeats.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_033_pressure_handoff_after_spin_smogtours-gen2ou-934324_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/poison_clock_spin_loop_unlabeled_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Discussion Thread:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`

Source note: the Spikes article frames Starmie, Cloyster, Toxic, Ghosts,
Pursuit, and offensive pressure as one connected hazard subgame. The Cloyster
source reinforces why Spikes, Toxic, Surf, and Explosion all have to be priced
as route tools. This probe does not add a new policy; it tests STP-053's
post-Spin pressure boundary.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-information errors: 0.

Measurement status: guided regression only. Count it as policy coverage, not
fresh transfer improvement.

## Scenario 1 - Allow Spin Into Zapdos Pressure

Public state:

```text
Vanilla GSC. Our Machamp is active at 94% and badly poisoned. Opposing Starmie
is active at 64%, has Rapid Spin revealed, and is taking Spikes damage on
entry. Both sides have Spikes. Our Zapdos is 100% in back, Gengar is 100% in
back, and Cloyster is 47% with Spikes and Explosion revealed. Opposing Snorlax
is asleep at 79% and has Rest/Sleep Talk revealed.
```

Recommendation: switch Zapdos, allowing Rapid Spin if Starmie chooses it.

Route reason: Gengar can block Spin, but Zapdos creates the better next board:
Starmie must answer Thunder or switch to sleeping Snorlax, and that Snorlax
branch can give Cloyster a later Spikes reset.

Serious alternatives: Gengar if the layer is the immediate win condition;
Machamp attack only if Starmie is already in a confirmed KO or unrecoverable
range.

Worst branch: Starmie attacks Zapdos on the switch and keeps itself healthy
enough to spin again later.

Score: pass.

## Scenario 2 - Block Spin When The Layer Is The Route

Public state:

```text
Vanilla GSC. Opposing Starmie is active at 58%, with Rapid Spin, Recover, Surf,
and Thunder Wave revealed. Its side has Spikes; our side is clear. Our Gengar
is 92% and has Thunderbolt revealed. Our Zapdos is 28%, asleep, and cannot
force Starmie out. Opposing Snorlax is 44% and will be in Machamp range only
if it takes one more Spikes entry.
```

Recommendation: switch Gengar to block Rapid Spin, confidence medium-high.

Route reason: here the layer is the route. Letting Spin resolve removes the
Snorlax endgame threshold, and the available pressure handoff is too weak.

Serious alternatives: stay in and attack only if Starmie cannot safely Spin or
Recover; preserve Gengar if Starmie has already revealed Psychic.

Worst branch: Starmie predicts Gengar and attacks, but its public set does not
currently show the move that makes Gengar entry unacceptable.

Score: pass.

## Scenario 3 - Reset Spikes On Resting Snorlax

Public state:

```text
Vanilla GSC. Our Zapdos is active at 100%. Opposing Snorlax is active at 54%,
asleep, and has Rest/Sleep Talk revealed. Opponent's side is clear because
Starmie spun earlier. Our Cloyster is 47% in back with Spikes and Explosion
revealed. Opposing Starmie is 70% in back.
```

Recommendation: switch Cloyster, confidence medium.

Route reason: Zapdos Thunder is active, but Snorlax's likely wake, Rest, or
Sleep Talk turn gives Cloyster the cleaner hazard reset. If Snorlax Rests,
Spikes returns before Starmie can immediately remove it.

Serious alternatives: keep Thunder if Snorlax is near a KO threshold or if
Cloyster cannot survive the entry and one attack.

Worst branch: Snorlax wakes and attacks Cloyster hard, turning the reset into a
support-for-damage trade.

Score: pass.

## Scenario 4 - Cash Out A Spent Cloyster

Public state:

```text
Vanilla GSC. Our Cloyster is active at 15% after setting Spikes. Opposing
Snorlax is active at 100% asleep with Rest/Sleep Talk revealed. Opposing
Moltres is asleep at 62% in back and threatens Sunny Day Fire Blast if it gets
in cleanly. Our Gengar and Zapdos can pressure Starmie after Cloyster faints.
```

Recommendation: Explosion, confidence medium.

Route reason: Cloyster has completed the reset and is too low to preserve as a
future support piece. Explosion prices the likely Moltres pressure switch and
is still acceptable into Snorlax if the trade opens Gengar/Zapdos pressure.

Serious alternatives: switch Gengar if preserving Cloyster's death fodder is
material; Spikes is no longer needed this turn because the layer is already up.

Worst branch: a Ghost or Rock enters, or Snorlax stays asleep and the Explosion
target is not valuable enough.

Score: pass.

## Scenario 5 - Preserve Cloyster With A Future Job

Public state:

```text
Vanilla GSC. Our Cloyster is active at 62%, has Spikes, Toxic, Surf, and
Explosion revealed, and the opponent's side currently has no Spikes. Opposing
Snorlax is asleep at 72%, but opposing Starmie is 85% in back with Rapid Spin
revealed. Our Gengar is fainted, and Cloyster is the only way to reset Spikes
or trade into Starmie later.
```

Recommendation: do not explode yet; use Spikes if safe, otherwise switch to
the Snorlax answer while preserving Cloyster.

Route reason: Explosion is a route trade only after Cloyster's future job is
priced. Here the job is still live: reset the layer after Starmie clears it or
trade into the spinner once the route is ready.

Serious alternatives: Explosion if Snorlax is the last route blocker and
Starmie no longer matters; Surf if Snorlax is already in a damage threshold.

Worst branch: over-preserving Cloyster lets Snorlax wake and pressure without
paying the intended trade cost.

Score: pass.

## Scenario 6 - Carry The Weather And Sleep Clock

Public state:

```text
Vanilla GSC. Opposing Moltres is active at 56% and has Sunny Day, Fire Blast,
and Rest revealed. Sun was set four turns ago and will expire after this turn.
Our Snorlax is active at 99% asleep with Rest, Sleep Talk, Double-Edge, and
Earthquake revealed. Both sides have Spikes. Our Cloyster is 47% in back.
```

Recommendation: for Snorlax, Sleep Talk. For Moltres, renewing Sunny Day is a
serious top action before another Fire Blast.

Route reason: do not assume the last attack repeats. The sun clock changes the
damage route, and Snorlax's Sleep Talk branch can punish either Fire Blast or
Sunny Day with Double-Edge.

Serious alternatives: Snorlax switch only if another Fire Blast is a forced KO
and the replacement has a better sun matchup; Moltres Fire Blast if the current
sun turn already secures the route.

Worst branch: Sleep Talk rolls Earthquake into Moltres immunity while Moltres
renews sun, creating another high-damage cycle.

Score: pass.

## Extracted Checklist

Before choosing the hazard-control response after Starmie appears:

1. If Rapid Spin resolves, what pressure piece enters next?
2. If Rapid Spin is blocked, can the spinblocker survive the real punish?
3. Is the layer the current win condition, or can it be rebuilt on a Rest,
   Sleep Talk, forced switch, or low-pressure turn?
4. Does Cloyster still have a support job, or has it become Explosion material?
5. Are sleep turns, wake turns, weather, Rest, and Sleep Talk branches changing
   the timing?
6. What exact route is improved by the move, rather than merely defending the
   previous plan?

## Next Rep

Run another fresh replay transfer with a Starmie hazard-control turn, but do
not pre-label it as spinblock, pressure handoff, or Cloyster reset. Score the
first five hazard decisions after Starmie or Cloyster is revealed.
