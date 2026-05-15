# Statused Spinner Handoff Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_028` turn-7 miss into six compact
prompts that force the choice after a spinner or hazard support piece is
statused: continue the support mirror, Rapid Spin, hand off to pressure, phaze,
attack, or delay the reset.

This is not final-exam evidence. The prompts were built after seeing the miss,
so the score is a regression/checklist result, not a fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_027_spinblock_transfer_smogtours-gen2ou-934144_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_028_statused_spinner_handoff_smogtours-gen2ou-934149_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/spinblock_route_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`

Source note: status on a spinner or setter changes the hazard route only if it
creates a forced response: switch, recovery, bad re-entry, phaze cycle, KO
range, or a safer later reset. If the next click just repeats the support
mirror, the status may not have been converted.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 1 and 4 need fresh replay transfer
because they match the actual miss: both sides have hazards, a support piece is
statused, and the right line may be pressure or phazing instead of Spin.

## Scenario 1 - Handoff After Status And Layer

Public state: vanilla GSC, spectator-public style. Our Cloyster is active at
100% with Spikes and Toxic revealed. Opposing Cloyster is active at 100% and
badly poisoned. Spikes are up on both sides. Our Zapdos is healthy and can
force the poisoned Cloyster out or punish the Electric absorber. Our Raikou is
asleep but has RestTalk revealed and can absorb opposing Electric pressure.

Frozen answer: switch Zapdos. Confidence: high. The route is to convert Toxic
plus Spikes by forcing the poisoned support piece to leave, not to keep
clicking support into a mirror where both sides may spin later. Serious
alternatives: Rapid Spin if our grounded entries are already collapsing;
Explosion only if Cloyster's removal opens an immediate route. Worst branch:
the opponent doubles to Raikou or Snorlax as Zapdos enters.

Policy key: once status and the layer are delivered, handoff pressure can be
the conversion move.

Grade: complete.

## Scenario 2 - Set The First Layer Before Handoff

Public state: vanilla GSC, player-side known set. Our Cloyster is active at
100% with Spikes / Toxic / Surf / Explosion. Opposing Cloyster is badly
poisoned at 100%, but no Spikes are currently up on either side. Our Zapdos can
force Cloyster later, but without Spikes the forced switch has no entry tax.

Frozen answer: use Spikes first. Confidence: high. The route is status, then
field, then handoff. Immediate Zapdos pressure is serious only if Cloyster is
about to Explode or if our own Cloyster cannot survive another turn. Worst
branch: opposing Cloyster sets its own Spikes or Explodes before the handoff.

Policy key: pressure handoff is strongest after the layer exists; do not skip
the field job when the support piece can still safely deliver it.

Grade: complete.

## Scenario 3 - Spin Before The Handoff

Public state: vanilla GSC, player-side known team. Our Starmie is active at
76% with Rapid Spin / Surf / Recover / Thunder Wave. Our side has Spikes.
Opposing Forretress is badly poisoned at 54% and has Spikes / Toxic revealed.
The opponent has no Ghost revealed, and our Snorlax cannot keep entering with
Spikes up.

Frozen answer: use Rapid Spin. Confidence: high. The route is removal before
pressure: the statused setter is not the immediate problem if our own key
pieces are losing every entry. Serious alternatives: Surf if it KOs
Forretress or denies Explosion; Thunder Wave only if it prevents a worse
handoff. Worst branch: Forretress switches to an unrevealed Ghost or Explodes.

Policy key: statused-support handoff does not override a necessary clean spin.

Grade: complete.

## Scenario 4 - Phaze Converts The Statused Support

Public state: vanilla GSC, player-side known set. Our Tyranitar is active at
70% with Roar / Rock Slide / Curse / Rest. Spikes are up on the opponent's
side. Opposing Snorlax is at `atk+1 def+1`, and the opponent's poisoned
Cloyster is likely to re-enter as the support reset. Our Cloyster has already
set Spikes and Toxic.

Frozen answer: use Roar if Snorlax stays or the support reset enters.
Confidence: medium-high. The route is to convert the hazard/status state by
forcing repeated entries instead of returning to the Cloyster mirror. Serious
alternatives: Rock Slide if Snorlax is in KO range; switch if Earthquake damage
would make Tyranitar unusable. Worst branch: Roar fails because it moves before
the target or Tyranitar is too low after Earthquake.

Policy key: after support is delivered, a phazer may be the pressure piece
that turns status plus hazards into progress.

Grade: complete.

## Scenario 5 - Attack The Spinner Instead Of Resetting

Public state: vanilla GSC, player-side known set. Our Zapdos is active at 88%
with Thunder / Hidden Power Ice / Rest / Sleep Talk. Opposing Starmie is at
46%, poisoned, and has Rapid Spin / Recover / Surf revealed. Spikes are absent
on both sides because Starmie just removed them. Our Cloyster can set Spikes
later if Starmie is forced out.

Frozen answer: use Thunder. Confidence: high. The route is to punish the
poisoned spinner directly; resetting Spikes now would only invite Starmie to
Recover or spin again later. Serious alternatives: Rest if Zapdos is too low;
double to Cloyster only if Starmie is forced out. Worst branch: Thunder misses
and Starmie Recovers.

Policy key: when the spinner is already statused and in range, damage can be
the hazard-control move.

Grade: complete.

## Scenario 6 - Delay Reset Until The Support Leaves

Public state: vanilla GSC, player-side known team. Our Cloyster has Spikes and
Toxic revealed. Opposing Forretress is poisoned at 65%, and Spikes are up on
both sides. Our Snorlax is active against Forretress after a double-switch.
Forretress can Rapid Spin or switch, but it cannot threaten Snorlax much.

Frozen answer: attack or force with Snorlax first; reset hazards after
Forretress leaves or is forced low. Confidence: medium-high. The route is to
cash in the pressure turn before re-entering the support mirror. Serious
alternatives: switch Cloyster only if Forretress is clearly spinning and the
layer must be reset immediately. Worst branch: Forretress spins as Snorlax
attacks, making this future control rather than current retention.

Policy key: a delayed reset can be better than immediate support if the
pressure turn makes the next reset stick.

Grade: complete.

## Resulting Rule

After a spinner or setter is statused, ask in this order:

1. Has the field job already been delivered this cycle?
2. Is our own side's hazard problem urgent enough to Spin now?
3. Which pressure piece exploits the status: Electric, Snorlax, Tyranitar,
   phazer, trapper, direct attacker, or Explosion user?
4. Does that pressure force switch, recovery, KO range, phaze value, or a safer
   later hazard reset?
5. If we stay in the support mirror, what progress do we actually gain before
   the opponent spins, switches, Explodes, or Recovers?

## Next Study Target

Run a fresh unseen replay segment with a statused spinner / setter and score
whether this handoff checklist transfers without overcorrecting away from
necessary Rapid Spin or first-layer Spikes.
