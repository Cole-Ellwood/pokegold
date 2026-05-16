# Spin vs Setup Handoff Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_029` turn-19 miss into six compact
prompts that force the choice when a spinner can remove Spikes, but the active
pressure piece may prefer setup, attack, Rest, phaze, or sacrifice over
spinblocking.

This is not final-exam evidence. The prompts were built after seeing the miss,
so the score is a regression/checklist result, not a fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_029_spin_vs_setup_handoff_smogtours-gen2ou-935409_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Playing with Spikes in GSC forum thread:
  `https://www.smogon.com/forums/threads/playing-with-spikes-in-gsc-qc-2-2-gp-2-2-done.3475184/post-4501581`
- Smogon GSC Donphan:
  `https://www.smogon.com/forums/threads/gsc-donphan-done.3733724/post-9920297`
- Smogon GSC Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

Source note: GSC hazard control is a route trade, not a one-move checklist.
The Spikes source emphasizes forcing sequences after hazards, Donphan is a
spinner that still has anti-Curse tools such as Growl or Roar, and Snorlax
sources frame Curse as route pressure that forces phazing or real containment.
Therefore, the spin turn must be priced against the route the active Pokemon
starts if it stays in.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 1 and 2 need fresh replay transfer
because they are the exact boundary: do we let Rapid Spin resolve to start a
setup route, or block Spin because the layer is the route?

## Scenario 1 - Let Spin Resolve For Curse

Public state: vanilla GSC, spectator-public style. Our Snorlax is active at
94% against opposing Donphan at 94%. Spikes are up on both sides. Our Gengar is
healthy and could enter to block Rapid Spin, but our Snorlax has Curse
revealed and Donphan has no anti-Curse move revealed. Opposing Forretress is
low and their Zapdos is chipped.

Frozen answer: use Curse, accepting Rapid Spin if Donphan uses it. Confidence:
medium-high. The route is to trade current hazard retention for immediate
Snorlax setup pressure. Serious alternative: switch Gengar only if the layer is
the primary route and Donphan has no way to punish the Ghost. Worst branch:
Donphan reveals Roar or Growl, or Spin removes the layer and Snorlax cannot
convert before Toxic/phazing arrives.

Policy key: if the spin turn gives a pressure piece a route-changing setup,
blocking Spin may be too small.

Grade: complete.

## Scenario 2 - Block Spin Because The Layer Is The Route

Public state: vanilla GSC, player-side known team. Our Spikes are up on the
opponent's side. Opposing Donphan is active at 91% and will likely use Rapid
Spin. Our Gengar is 88% and can enter Donphan safely enough. Our Snorlax is
asleep, poisoned, or otherwise unable to turn the free turn into pressure, and
our only win route is forcing the opponent's Zapdos and Snorlax through Spikes
range.

Frozen answer: switch Gengar to block Rapid Spin. Confidence: high. The route
is current retention: without the layer, the known endgame clock disappears
and no active pressure piece compensates. Serious alternatives: attack Donphan
only if it KOs or denies the next Spin. Worst branch: Donphan predicts Gengar
with coverage or switches, but the layer remains protected against the main
removal line.

Policy key: the overcorrection boundary has two sides; block Spin when the
layer is the route and no stronger handoff exists.

Grade: complete.

## Scenario 3 - Attack The Spinner

Public state: vanilla GSC, player-side known set. Our Snorlax is active at
82%, with Double-Edge / Earthquake / Rest / Curse. Opposing Donphan is active
at 42%, Spikes are up on the opponent's side, and Donphan has Rapid Spin /
Earthquake revealed. Our Gengar is healthy, but Donphan is in range of
Double-Edge plus recoil/hazard follow-up, and Snorlax does not need another
Curse to force progress.

Frozen answer: use Double-Edge. Confidence: high. The route is to punish the
spinner directly; blocking Spin risks giving Donphan or a switch a safer reset.
Serious alternatives: Curse only if Donphan is unlikely to Spin or can survive
comfortably; Gengar only if the layer matters more than removing Donphan.
Worst branch: Donphan survives, spins, and Snorlax takes too much return
damage.

Policy key: damage into the spinner can be the hazard-control move when it
removes or cripples the remover.

Grade: complete.

## Scenario 4 - Rest While The Spinner Spins

Public state: vanilla GSC, player-side known team. Our Snorlax is active at
46%, badly poisoned, at `atk+2 def+2`, with Rest available. Opposing Donphan is
active and can Rapid Spin. Spikes are up on the opponent's side, but Snorlax is
the only piece that can still pressure their defensive core if healed. Our
Gengar can block Spin, but switching it in lets Snorlax lose its setup and
poison position.

Frozen answer: use Rest. Confidence: medium-high. The route is to preserve the
setup converter; losing current Spikes is acceptable if Snorlax keeps the
route alive. Serious alternatives: attack if it KOs Donphan before Spin;
Gengar only if Snorlax cannot convert even after Rest. Worst branch: Donphan
spins, then phazes or hands off while Snorlax sleeps.

Policy key: the active converter's HP/status can outrank immediate hazard
retention.

Grade: complete.

## Scenario 5 - Phaze Over Spinblock

Public state: vanilla GSC, player-side known set. Our Steelix is active at
76%, with Roar / Earthquake / Curse / Rest. Opposing Donphan is active at 88%
and can Rapid Spin. Spikes are up on the opponent's side. The opponent's
Snorlax, Zapdos, and Starmie are all chipped enough that one forced entry
meaningfully changes the endgame, and Donphan is unlikely to threaten Steelix
immediately.

Frozen answer: use Roar. Confidence: medium. The route is to convert the layer
now rather than only preserve it. Serious alternatives: Gengar if Donphan
spinning is uniquely bad; Earthquake if Donphan is in range. Worst branch:
Donphan spins before Roar value matters, or Steelix takes a coverage hit that
makes later phazing impossible.

Policy key: when the active phazer can convert the layer immediately, phazing
can outrank a spinblock switch.

Grade: complete.

## Scenario 6 - Sacrifice To Keep The Route

Public state: vanilla GSC, player-side known team. Our Cloyster is active at
31%, with Explosion / Surf / Spikes / Toxic. Opposing Starmie is active at 58%,
poisoned, and has Rapid Spin / Recover / Surf revealed. Spikes are up on the
opponent's side and are required for our Marowak cleanup. Our Ghost is too low
to block Starmie, and if Starmie spins and Recovers the cleanup route is gone.

Frozen answer: use Explosion or the strongest immediate damage if Explosion is
not legal on this set. Confidence: medium-high. The route is to spend the
support piece to remove the spinner before it resets the endgame. Serious
alternatives: switch only if a real blocker can enter; Spikes is no progress if
Starmie spins this turn. Worst branch: Starmie switches to a low-value absorber
or survives and spins later.

Policy key: sacrifice is justified when the spinner must be removed and no
setup, phaze, Rest, or spinblock route covers the current turn.

Grade: complete.

## Resulting Rule

When a spinner enters and a spinblocker is available, ask in this order:

1. If Spin resolves, what route do we start this turn?
2. Is that route stronger than preserving the current layer?
3. Can the active Pokemon attack, set up, Rest, phaze, status, or sacrifice in
   a way that compensates for losing the layer?
4. What contains the pressure route after the handoff: Roar, Growl, Toxic,
   Rest, Defense Curl, Explosion, Recover, or a pivot?
5. If none of those routes compensates, block or punish Spin.

## Next Study Target

Run a fresh unseen replay segment with an active spinner and a live pressure
piece. Score whether the branch bundle prices both spinblock and pressure
handoff without overcorrecting in either direction.
