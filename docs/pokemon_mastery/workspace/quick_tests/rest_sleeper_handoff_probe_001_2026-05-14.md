# Rest Sleeper Handoff Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether the replay
058 lessons are now stated as usable decision boundaries. It is not fresh
replay evidence and should not be counted as proof of broad improvement.

## Score Summary

Scenarios: 3.

Action policy hits: 3 / 3.

Classification hits: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Voluntary Electric Entry Into Tyranitar

Prompt:

Vanilla GSC spectator-public state. Your Raikou is active at 73% against an
opposing Tyranitar at 100%. The opponent has Spikes on their side. Tyranitar
has revealed Fire Blast and Rock Slide. Raikou entered last turn on Rock Slide,
taking heavy damage. Your other revealed pieces are Zapdos healthy, Forretress
healthy with Spikes, and a damaged Snorlax. Raikou's moves are not revealed.

Question: what is the recommended move class, and what branch must be priced?

Frozen answer:

Use the coverage or cash-out line that justified Raikou's entry, with Hidden
Power Water as the default if available. Price Tyranitar's Earthquake as the
best immediate punish. Do not choose a generic stabilizing move like Reflect
unless it clearly changes the Earthquake branch or preserves a more important
route than the Tyranitar damage.

Answer key:

Hit. The voluntary entry is information. Raikou entering Tyranitar should raise
the prior on Hidden Power Water, lure value, or a planned cash-out. The line
fails if Tyranitar Earthquakes and Raikou did not take the damage it entered to
claim.

## Scenario 2 - Gengar Threatens Tyranitar Without Auto-Explosion

Prompt:

Vanilla GSC spectator-public state. Your Gengar is active at 100% against an
opposing Tyranitar at 55%. The opponent has Spikes on their side. Tyranitar has
revealed Fire Blast, Rock Slide, and Earthquake. Your Raikou just fainted after
damaging Tyranitar. Your Zapdos is still a possible converter, but Tyranitar is
not yet removed. Gengar has not revealed Explosion.

Question: should Gengar immediately explode?

Frozen answer:

No by default. Use non-Explosion pressure first, such as Dynamic Punch if that
is the set's Tyranitar punish, unless removing Tyranitar immediately opens a
named converter and the opponent's switch-to-absorb branch is covered. Gengar's
Normal immunity, spin or Explosion deterrence, and later trade value are still
real resources.

Answer key:

Hit. Explosion is the opposite boundary only when the converter opens now and
the likely switch branch does not waste the trade. Here, threatening Tyranitar
without spending Gengar keeps more live routes.

## Scenario 3 - Rested Zapdos Handoff

Prompt:

Vanilla GSC spectator-public state. Your Zapdos is active at 100% asleep after
using Rest. Thunder and Rest are revealed. The opposing Exeggutor is at 54% and
has revealed Psychic and Stun Spore. The opponent also has Snorlax at high HP
and Tyranitar damaged, with Spikes on their side. Your Gengar is healthy.

Question: should Zapdos stay in and burn sleep turns?

Frozen answer:

Not automatically. First name the next board. If Exeggutor is likely to stay
and Zapdos has confirmed Sleep Talk that pressures it, staying can be correct.
If the opponent's best counter-pivot is Snorlax exploiting the sleeping Zapdos,
switch to Gengar and save Zapdos for later. Rest preserved Zapdos; it did not
force Zapdos to stay active.

Answer key:

Hit. The route is the handoff, not the sleep turn itself. Sleeping Zapdos can
be an active RestTalk pressure piece, but it can also be switched out and saved
when another piece covers the opponent's counter-pivot.

## Reusable Boundary

Do not turn a replay lesson into a one-line script. Voluntary entry, Explosion,
and Rest sleep are all signals to re-price the next board. They are not
commands to always attack, always boom, or always burn sleep turns.

## Next Transfer Check

Use a fresh replay packet with no keyword screen if possible. Target positions
where a player voluntarily enters a bad-looking matchup, threatens Explosion
without spending it, or switches a sleeping route piece out after Rest.
