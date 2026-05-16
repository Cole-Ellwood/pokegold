# Spinblock Route Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression.

Purpose: convert the `replay_turn_pause_026` turn-8 miss into six compact
prompts that force the next hazard-control choice after Spikes are up:
Rapid Spin, spinblock, spinner punish, status pressure, or abandoning the
hazard subgame for a more urgent route.

This is not final-exam evidence. The prompts were built after studying the
policy and prior replay, so the score is a regression/checklist result, not a
fresh skill estimate.

Local docs checked:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_026_hazard_spinblock_transfer_smogtours-gen2ou-934842_2026-05-14.md`
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

Source note: GSC Spikes play is not just "set or spin." The source material
separates the route into setting, keeping, removing, and converting Spikes.
Misdreavus and Gengar are the only GSC spinblockers, but they do not cover the
same spinners equally. Gengar can be a strong partner for Forretress because it
blocks Cloyster and opposing Forretress, while Misdreavus is the sturdier
Starmie blocker. Cloyster and Forretress also compress support roles, so the
current support job can outrank immediate Spin or Explosion.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Branch-bundle hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Weakest remaining pressure: scenarios 2 and 4 need fresh replay transfer.
They are the closest to the `replay_turn_pause_026` miss: a spinner has an
obvious Rapid Spin button, but the opponent can either switch to a Ghost or use
a better non-Ghost hazard answer.

## Scenario 1 - Clean Spin Before The Layer Converts

Public state: vanilla GSC, player-side known team. Our Starmie is 88% with
Surf / Rapid Spin / Recover / Substitute. Spikes are on our side. Opposing
Cloyster is active at 42% with Spikes / Toxic / Surf revealed. The opponent's
Gengar is fainted, Misdreavus is not on the known team, and Cloyster's Toxic
does not stop Starmie from Recovering later. Our Zapdos and Snorlax both need
the layer removed to keep entering.

Frozen answer: use Rapid Spin. Confidence: high. The route is clean removal
before Spikes convert into repeated-entry damage. Serious alternatives:
Substitute if Toxic denial matters more, or Surf if Cloyster is in KO range and
removal can wait one turn. Worst branch: Cloyster lands Toxic and preserves
itself, but the layer is gone and Starmie can still Recover.

Policy key: Rapid Spin is a progress move when no effective blocker can enter
and the removed layer preserves real future entries.

Grade: complete.

## Scenario 2 - Gengar Is The Expected Spinblock

Public state: vanilla GSC, spectator-public style. Our Tentacruel is active at
91% against opposing Forretress at 100%. Forretress just set Spikes on our
side. The opponent has already revealed Gengar at full HP and Snorlax as the
special sponge. Our Snorlax is healthy and can enter Gengar's Thunderbolt
branch; our Tentacruel's Rapid Spin does no progress if Gengar enters.

Frozen answer: double-switch to Snorlax or attack the switch-in; do not rate
Rapid Spin as clean progress. Confidence: medium-high. The route is to punish
the expected spinblock branch before trying to remove hazards again. Serious
alternative: Rapid Spin is acceptable only if Forretress staying is much more
likely than Gengar, or if the cost of leaving Spikes up for one more turn is
route-ending. Worst branch: Forretress stays and Tentacruel gives up a direct
spin turn.

Policy key: before clicking Spin, ask whether a live Ghost can enter on the
actual removal turn; if yes, name the punish or accept that Spin may fail.

Grade: complete.

## Scenario 3 - Healthy Misdreavus Blocks Starmie

Public state: vanilla GSC, player-side known team. Our Cloyster has Spikes up
against opposing Starmie at 94%, which has Surf / Rapid Spin / Recover
revealed. Our Misdreavus is 86% and can take Starmie's current attacks; our
Tyranitar is healthy enough to punish a later Starmie or opposing Ghost pivot.
If Starmie spins now, our Marowak route loses its entry-tax support.

Frozen answer: switch Misdreavus to block Rapid Spin. Confidence: high. The
route is current retention: the blocker can enter the actual removal turn and
the layer is what makes Marowak pressure convert. Serious alternatives: Toxic
with Cloyster only if Starmie is unlikely to spin immediately; double to
Tyranitar only if Starmie is clearly avoiding Rapid Spin. Worst branch: Starmie
Surfs on the switch and starts wearing down Misdreavus, but the layer is still
retained.

Policy key: a spinblocker is real retention only if it can enter or act on the
removal turn.

Grade: complete.

## Scenario 4 - Gengar Does Not Reliably Block Starmie

Public state: vanilla GSC, player-side known team. Our Forretress has Spikes
up, and opposing Starmie is active at 100% with Surf / Rapid Spin / Recover
revealed. Our only Ghost is Gengar at 62%; it is needed later to threaten
Explosion and cannot safely absorb repeated Starmie attacks. Our Raikou is
healthy and forces Starmie out, while our Snorlax can punish Recover loops.

Frozen answer: switch Raikou or use the non-Ghost pressure plan; do not treat
Gengar as an automatic spinblock. Confidence: medium-high. The route is to
deny Starmie a cheap spin through offensive pressure, not to spend a fragile
Gengar into the wrong spinner matchup. Serious alternative: Gengar only if
blocking this exact Spin is worth risking its future role or if Starmie lacks
the attack to punish it. Worst branch: Starmie spins as Raikou enters, making
the move future pressure rather than current retention.

Policy key: "we have a Ghost" is not enough. Match the blocker to the spinner
and price the blocker's later job.

Grade: complete.

## Scenario 5 - Stop The Route Before Spinning

Public state: vanilla GSC, player-side known set. Our Forretress is 79% with
Spikes / Rapid Spin / Toxic / Explosion. Spikes are on both sides. Opposing
Snorlax is active at 100%, at `atk+1 def+1 spe-1`, and has Curse / Double-Edge
revealed. The opponent's Cloyster is the setter but is currently benched. Our
Skarmory is low, so Snorlax becomes hard to contain if it gets another free
boost.

Frozen answer: use Toxic, not Rapid Spin. Confidence: high. The route is
route-stopper first: Snorlax's setup branch is more urgent than the symmetric
hazard state, and Toxic starts the clock that later makes Spin or Explosion
meaningful. Serious alternatives: Explosion if Snorlax will otherwise win
immediately; Rapid Spin only if Snorlax is already contained. Worst branch:
Toxic misses and Snorlax attacks or boosts again.

Policy key: do not ask "Spikes or Rapid Spin?" before asking whether the
opponent's current route becomes permanent if unstopped.

Grade: complete.

## Scenario 6 - Accept Status To Remove The Layer

Public state: vanilla GSC, player-side known team. Our Starmie is 72% with
Rapid Spin / Surf / Recover / Thunder Wave. Spikes are on our side and our
team relies on repeated Snorlax and Raikou entries. Opposing Cloyster is active
at 100% with Spikes / Toxic / Surf / Explosion revealed. The opponent has no
Ghost and no Pursuit trapper revealed; Cloyster's Toxic is likely if Starmie
stays.

Frozen answer: use Rapid Spin. Confidence: medium-high. The route is to pay
the Toxic cost once to preserve repeated entries for the rest of the team.
Serious alternatives: Thunder Wave if paralyzing Cloyster prevents both
Explosion and future Spikes better; Recover if Starmie is about to lose the
long game. Worst branch: Cloyster lands Toxic and later Explodes, but the
current layer is removed and the team is no longer paying every switch.

Policy key: spinner status is a cost, not an automatic reason to delay Spin,
when removal keeps the team's live routes affordable.

Grade: complete.

## Resulting Rule

Before valuing Rapid Spin or a spinblock as progress, answer five questions:

1. What exact route does the current layer enable if it stays?
2. Can the spinner remove it this turn, and does removal preserve a named
   teammate or route?
3. Can a Ghost enter or act on the actual removal turn?
4. If a Ghost enters, what is the punish: attack, double-switch, Pursuit,
   status, phaze, or abandon the spin attempt?
5. Is a more urgent route-stopper, such as Toxic, phazing, Explosion, or
   direct pressure, more important than the hazard exchange this turn?

## Next Study Target

Run a fresh unseen replay segment with Spikes up, an active spinner, and a
plausible Gengar or Misdreavus. Score whether the spinblock branch is named
before clicking Rapid Spin or treating the layer as retained.
