# Spin vs Damage Boundary Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_031` misses into compact paired
prompts that force the Starmie/Cloyster hazard-control boundary:

- direct damage into a phazer, spinner, or spinblocker;
- clean Rapid Spin when the Ghost branch is priced and a non-Ghost pivot is
  more likely;
- statusing a spinner even though Spin may still resolve;
- switching to a Ghost only when it actually enters the Spin turn and active
  pressure is weaker.

This is not final-exam evidence. These prompts were built after seeing the
replay miss, so the score is a regression result, not a fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_031_hazard_pressure_taxonomy_transfer_smogtours-gen2ou-866835_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/hazard_pressure_move_taxonomy_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Discussion Thread:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`
- Smogon GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`

Source note: the GSC Spikes guide says status can decide the Spikes war
against Cloyster and Starmie, and specifically describes baiting Starmie into
repeated spin/recovery conflicts. The Cloyster analysis says Surf pressures
some spinners and Explosion absorbers while Toxic pressures Starmie and
opposing Cloyster. GSC discussion and core material both reinforce that
Starmie is a real spinner and that Misdreavus can be chosen specifically to
block Starmie spins. The decision is therefore not "always Spin" or "always
attack"; it is whether the current turn's damage, status, Spin, or Ghost entry
changes the next route most.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: fresh replay transfer is still needed, because
scenario 2 is the exact `replay_turn_pause_031` overcorrection miss: after
learning "damage over premature Spin," I still need to choose clean Spin when
the board actually offers it.

## Scenario 1 - Damage The Phazer Before Spinning

Public state: vanilla GSC, spectator-public style. Our Starmie is active at
94%, poisoned, with Thunder / Surf revealed or strongly represented by prior
play. Spikes are on our side. Opposing Skarmory is active at 100% or high HP,
with Toxic revealed and likely phazing or Snorlax-checking duties. The
opponent has not revealed a Ghost yet. Our Snorlax route improves if Skarmory
is forced low; Starmie is healthy enough to spin later if it gets a cleaner
turn.

Frozen answer: use Thunder. Confidence: medium-high. The route is direct
damage as hazard control: Thunder can make Skarmory unable to keep absorbing
Snorlax and Starmie pressure, while Rapid Spin spends the turn but leaves the
phazer healthy and able to keep poisoning or checking the route. Serious
alternatives: Rapid Spin only if Starmie's future entries are collapsing or if
Skarmory is already too low to matter; switch only if Starmie must be preserved
and Toxic damage will decide the game. Worst branch: Thunder misses and
Skarmory lands Toxic or phazes later, but the missed hit still targeted the
piece that was converting the hazard war.

Policy key: direct damage beats Rapid Spin when the hit changes the opponent's
phaze/check map more than clearing our current layer.

Grade: complete.

## Scenario 2 - Spin Cleanly When The Non-Ghost Pivot Is Live

Public state: vanilla GSC, spectator-public style. Our Starmie is active at
94%, poisoned, with Surf / Thunder revealed. Spikes are on our side. Opposing
Cloyster is active at 99%, poisoned, with Rapid Spin / Spikes / Surf / Toxic
revealed. The opponent has Misdreavus revealed at about half HP, but Blissey is
also revealed and has strong incentive to enter Starmie to wall it, heal, or
later use Heal Bell. Our own Spikes are not currently up on the opponent's
side.

Frozen answer: use Rapid Spin. Confidence: medium. This is the clean Spin
boundary: Misdreavus is a real branch, but the support pivot is live and the
payoff of clearing our side is immediate. Serious alternatives: Surf only if
Misdreavus is much more likely than Blissey or if hitting Cloyster/Misdreavus
creates the next forced route; Recover only if poison damage makes Starmie lose
its future job. Worst branch: Misdreavus enters and blocks Spin, but that was
priced as a plausible branch, not treated as certainty.

Policy key: after a damage-over-Spin miss, do not overcorrect. Rapid Spin is
correct when it is clean often enough and the active damage line has no
stronger route endpoint.

Grade: complete.

## Scenario 3 - Status The Spinner Even If Spin Resolves

Public state: vanilla GSC, spectator-public style. Our Cloyster is active at
94%, poisoned, with Spikes / Toxic revealed. Opposing Cloyster is active at
94%, healthy, with Rapid Spin / Spikes / Toxic revealed. Spikes are on both
sides or our layer is newly set and likely to be spun. We do not have a Ghost
that can enter safely this turn. Our long route improves if opposing Cloyster's
future entries are put on a timer.

Frozen answer: use Toxic. Confidence: high. The route is future spinner
control: Toxic probably does not stop the current Rapid Spin, but it makes the
opposing Cloyster worse at resetting Spikes and answering later pressure.
Serious alternatives: Surf if damage pushes Cloyster into immediate KO or
Explosion range; Rapid Spin if our own grounded core cannot take another
entry. Worst branch: opposing Cloyster spins this turn and later receives
Heal Bell support, so Toxic becomes a temporary clock rather than permanent
control.

Policy key: status can be the correct hazard-control move even when it loses
the current layer, if it changes future spin/re-entry timing.

Grade: complete.

## Scenario 4 - Hit The Spinblocker Branch

Public state: vanilla GSC, spectator-public style. Our Starmie is active at
100%, poisoned, with Surf / Thunder revealed. Opposing Skarmory is low enough
that it may switch, and the opponent has revealed Misdreavus around half HP as
a Snorlax and Rapid Spin control piece. Spikes are on our side. If Starmie
spins into Misdreavus, the turn is wasted; if Starmie attacks, it pressures
both the Ghost entry and several support pivots.

Frozen answer: use Surf or Thunder according to the better damage profile;
default Surf when it reliably chunks Misdreavus and does not miss. Confidence:
medium-high. The route is to punish the spinblocker/pivot branch before trying
to clear. Serious alternatives: Rapid Spin only if Misdreavus is out of
position, too low to risk entry, or the opponent has stronger reason to go
Blissey; Recover if Starmie must preserve multiple future Spin attempts. Worst
branch: Blissey enters and absorbs the hit, but Starmie still avoided a wasted
Spin into Ghost.

Policy key: when the Ghost entry is the live punish, attack the Ghost branch
before spinning unless clearing now is still the route.

Grade: complete.

## Scenario 5 - Ghost Entry Is Real Only On The Spin Turn

Public state: vanilla GSC, player-side known team. Our Cloyster is active at
70%, with Spikes / Surf / Toxic / Explosion. Spikes are up on the opponent's
side and are required for our Machamp or Marowak cleanup. Opposing Starmie is
active at 78%, healthy, with Rapid Spin / Recover / Surf revealed. Our
Misdreavus is healthy and can enter Starmie's Rapid Spin; Cloyster's Toxic or
Surf does not meaningfully stop Starmie from spinning and Recovering later.

Frozen answer: switch Misdreavus. Confidence: high. The route is current
retention: the Ghost can actually enter the Spin turn, and active damage or
status does not solve the spinner before the layer is removed. Serious
alternatives: Toxic only if Misdreavus is too low to enter or if Starmie is
more likely to Recover than Spin; Explosion only if removing Starmie now opens
the final route and the absorber branch is priced. Worst branch: Starmie reads
the Ghost and attacks or pivots, but the layer-retention route at least forced
Starmie to respect the block.

Policy key: spinblock is correct when the Ghost enters the actual Spin turn
and the active pressure line is weaker.

Grade: complete.

## Scenario 6 - Damage The Spinner Instead Of Admiring The Ghost

Public state: vanilla GSC, spectator-public style. Our Cloyster is active at
100% with Surf / Spikes / Toxic revealed. Opposing Forretress is active at
88% with Rapid Spin / Spikes revealed and no Giga Drain shown. Our Ghost is
healthy on the bench, but Forretress is likely to stay or pivot to a standard
Explosion absorber. Surf threatens meaningful damage now, and Spikes are not
the only route because our Electric or Snorlax can exploit a damaged support
core.

Frozen answer: use Surf. Confidence: medium-high. The route is to punish the
spinner or its pivot directly; switching Ghost may block Spin, but it can also
give Forretress a free Toxic, Spikes, or pivot if the opponent does not spin.
Serious alternatives: Ghost switch if the current layer is the entire route
and Forretress spinning now is overwhelmingly likely; Toxic is poor if the
target is Forretress and not a spinner that cares about poison. Worst branch:
Forretress spins first and survives, but it no longer gets the support turn
for free.

Policy key: do not let "we have a Ghost" hide an active direct-damage punish.

Grade: complete.

## Resulting Rule

On Starmie/Cloyster hazard-control turns, ask these in order:

1. Does direct damage make the spinner, phazer, or spinblocker unable to keep
   answering the route?
2. Is Rapid Spin clean enough now, or is the Ghost branch actually the
   opponent's best route this turn?
3. Does status change future spin/re-entry timing even if the current Spin
   resolves?
4. Can the Ghost actually enter the Spin turn, and is blocking stronger than
   the active pressure move?

If the answer changes from one turn to the next, follow the new answer. The
taxonomy is a re-solve prompt, not a bias toward damage, Spin, or Ghost entry.

## Next Study Target

Run a fresh unseen replay segment with Starmie or Cloyster active and both
direct damage and Rapid Spin plausible. Score the chosen move class separately
from exact move agreement, and watch for overcorrection after the first miss.
