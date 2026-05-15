# Poison Clock Spin Loop Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert `replay_turn_pause_032` turns 30-34 into a compact Starmie vs
poisoned Cloyster drill. The targeted mistake is choosing from a static
"Rapid Spin or Surf" preference instead of re-scoring after each poison tick,
Spikes reset, and damage threshold.

This is not final-exam evidence. The prompts were built after seeing the replay
outcome, so the score is a regression/checklist result.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/replay_turn_pause_032_spin_vs_damage_boundary_transfer_smogtours-gen2ou-852072_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/spin_vs_damage_boundary_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/training_cycle.md`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon GSC OU Discussion Thread:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/`

Source note: Smogon Spikes material emphasizes that Starmie can be pressured
into spin/recovery conflicts, and that Toxic can wear down Starmie because GSC
has no Natural Cure. The Cloyster source explicitly points to Toxic pressuring
Starmie and opposing Cloyster, while Surf keeps some spinners and Explosion
absorbers honest. The replay-specific threshold below is not a universal damage
table; it is a route drill for recognizing when poison is already doing enough
and when damage finally becomes the route-converting move.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: this is a known-answer regression. The next useful
test is a fresh replay or semi-blind quick probe where the Cloyster HP bands
and poison stage are not labeled.

## Scenario 1 - Clear Side, Damage First

Public state: vanilla GSC, replay-derived band. Our Starmie is active at 63%,
badly poisoned, with Rapid Spin and Surf revealed. Our side is clear. Opposing
Cloyster is active at 78%, poisoned, and its side has Spikes. Cloyster has
Spikes / Surf / Toxic revealed, has no recovery beyond Leftovers, and can reset
our side if it gets another layer turn.

Frozen answer: use Surf. Confidence: high. Since our side is already clear,
Rapid Spin gains nothing this turn; Surf advances the poison clock and pushes
Cloyster toward the removal threshold. Serious alternatives: Recover only if
Starmie must preserve multiple future entries and Cloyster cannot reset Spikes
profitably; switch only if Raikou or another punish is forced. Worst branch:
Cloyster uses Spikes, so the next turn becomes a spin-loop decision instead of
a clean damage turn.

Policy key: if our side is clear, do not spend a no-value Spin. Damage the
setter/spinner or preserve Starmie.

Grade: complete.

## Scenario 2 - First Reset, Spin Before Damage

Public state: vanilla GSC, replay-derived band. Our Starmie is active at 63%,
badly poisoned, with Rapid Spin and Surf revealed. Both sides have Spikes.
Opposing Cloyster is poisoned at 45%. Surf will damage Cloyster but will not
remove it before it can set another layer or keep the loop going. Poison is
already ticking Cloyster down.

Frozen answer: use Rapid Spin. Confidence: high. The route is to clear our
side while poison and prior damage continue to solve Cloyster. Surf is tempting,
but if it does not remove Cloyster, it leaves our side Spiked while Starmie
takes poison. Serious alternatives: Surf only if a calc or observed roll makes
the KO likely; Recover only if Starmie survives the loop only by healing now.
Worst branch: Cloyster uses Spikes again, but that means the next decision is
another re-score with Cloyster lower.

Policy key: when damage does not remove the setter, Spin can be the progress
move because poison is the real removal clock.

Grade: complete.

## Scenario 3 - Second Reset, Do Not Attack Too Early

Public state: vanilla GSC, replay-derived band. Our Starmie is active at 57%,
badly poisoned. Both sides have Spikes. Opposing Cloyster is poisoned at 36%.
Surf will leave Cloyster alive in this observed band, while Rapid Spin clears
our side before Cloyster can reset.

Frozen answer: use Rapid Spin. Confidence: medium-high. This is the turn that
punished my replay answer: I wanted Surf too early. The route is still to keep
our side clear and let poison move Cloyster into the actual KO band. Serious
alternatives: Surf only if damage variation, prior chip, or a revealed item
state makes the KO real; switch only if Starmie is about to lose its remaining
spinner job. Worst branch: Cloyster resets Spikes again, but it is now close
enough that the next direct hit may remove it.

Policy key: "Cloyster is low" is not enough. Damage must actually remove the
reset piece or force a decisive branch.

Grade: complete.

## Scenario 4 - KO Band, Damage Becomes The Route

Public state: vanilla GSC, replay-derived band. Our Starmie is active at 44%,
badly poisoned. Both sides have Spikes. Opposing Cloyster is poisoned at 27%.
In the observed replay sequence, Surf KOs before Cloyster can act; Rapid Spin
would clear our side but let the setter/spinner remain if the KO is missed.

Frozen answer: use Surf. Confidence: high if the KO is observed or confirmed,
medium if it is a range. The route flips because damage now removes the reset
piece before another Spikes turn. Serious alternatives: Rapid Spin only if Surf
is not a KO and Starmie cannot afford the hazard on future entries; Recover is
too slow if Cloyster can keep resetting. Worst branch: Surf damage is short of
KO, so we have repeated the turn-33 error in the opposite direction.

Policy key: once damage removes the setter/spinner before it acts, damage
outranks another Spin.

Grade: complete.

## Scenario 5 - Cloyster Side Statuses The Spinner

Public state: vanilla GSC, reverse side. Our Cloyster is active at 88%,
poisoned, with Spikes / Surf / Toxic revealed. Opposing Starmie is active at
57%, healthy, with Rapid Spin revealed. Both sides have Spikes. If Starmie is
left healthy, it can spin repeatedly and recover later; if it is poisoned, its
future spin loop becomes finite.

Frozen answer: use Toxic. Confidence: medium-high. The route is future spinner
control, even though Starmie may spin immediately. Serious alternatives: Surf
if it puts Starmie into a forced KO range or catches a switch; Rapid Spin if
our own side's Spikes are the immediate losing route. Worst branch: Toxic
misses or Starmie has a cure route, leaving us behind in both status and
hazard tempo.

Policy key: poisoning Starmie can be hazard control because it changes the
future number of safe Spin turns.

Grade: complete.

## Scenario 6 - Exit The Loop When Starmie Is The Resource

Public state: vanilla GSC, replay-derived but adjusted. Our Starmie is active
at 31%, badly poisoned, with Rapid Spin / Surf / Recover revealed. Both sides
have Spikes. Opposing Cloyster is poisoned at 36%, so Surf is not a KO. If
Starmie spins and Cloyster resets Spikes, Starmie may lose the ability to clear
later or check the opponent's remaining threats.

Frozen answer: Recover or switch, depending on the opponent's best punish;
do not autopilot Rapid Spin. Confidence: medium. The route is resource
preservation: if Starmie cannot survive the loop, clearing once may not matter.
Serious alternatives: Rapid Spin if this is Starmie's last necessary job and
the next teammate converts immediately; Surf if it unexpectedly KOs or forces
Cloyster out. Worst branch: Recover gives Cloyster another Spikes turn and the
position becomes worse unless the extra Starmie HP is actually needed.

Policy key: the spin loop is correct only while Starmie remains a live resource
after the exchange.

Grade: complete.

## Resulting Rule

For poisoned Starmie vs poisoned Cloyster hazard loops:

1. If our side is clear, do not Spin; damage, recover, or pivot.
2. If both sides have Spikes and damage does not remove Cloyster, Spin can be
   correct while poison handles the setter.
3. Re-score after every poison tick and every Spikes reset.
4. When damage removes Cloyster before another reset, attack.
5. If Starmie is too low to survive the loop, preserve or cash it out instead
   of spinning by reflex.

## Next Study Target

Run a fresh replay or quick probe where the Starmie/Cloyster HP bands are
unlabeled and one scenario includes a false KO range. Score whether the answer
names the threshold check before choosing Surf or Rapid Spin.
