# Replay Turn-Pause 054 Hazard Loop Spin Window - smogtours-gen2ou-922676 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-922676`.

Mode: spectator-public vanilla GSC replay practice. Lead species were read
only from the public pre-turn-1 switch lines because this replay used custom
nicknames.

Selected measurable action: fresh transfer after
`snorlax_set_ambiguity_phaze_cashout_probe_001_2026-05-14.md`. The target was
Snorlax set ambiguity, support status before cash-out, and RestTalk inference.
The replay instead produced a higher-value hazard-loop transfer: preserve the
Electric answer, use Cloyster as the lower-value Snorlax absorber, and treat a
predicted Explosion absorber switch as a Rapid Spin window before cash-out.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- The selected replay was the next fresh metadata-only candidate:
  `smogtours-gen2ou-922676`, a 62-turn Gen 2 OU replay.
- Only public pre-turn-1 switch lines were inspected to map nicknames to lead
  species: p1 Cloyster and p2 Zapdos.
- Turns 1-10 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/snorlax_set_ambiguity_phaze_cashout_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, Is Snorlax Banworthy in GSC OU?:
  `https://www.smogon.com/forums/threads/is-snorlax-banworthy-in-gsc-ou.3541958/`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Steelix source reinforces Spikes plus Roar as a real support
conversion plan, and the Explosion source frames Explosion as a specific
offensive, defensive, or tactical trade rather than an automatic low-HP button.
This replay adds the Spin-window half: if the opponent covers Explosion by
switching a lower-value absorber, Rapid Spin can be the better cash-out punish.

## Score Summary

Scored decisions: 20 side decisions.

Top-match: 10 / 20.

Acceptable-match: 12 / 20.

Classification hits: 11 / 20.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 1 p1. I wanted immediate Spikes into Zapdos,
but the actual line preserved Cloyster and handed to Raikou.

Main improvement:

- Turn 7 transferred the prior lower-value absorber lesson: p1 preserved
  Raikou by switching Cloyster into Snorlax Double-Edge.
- Turn 4 and turn 6 correctly identified Spikes before cash-out and Snorlax as
  the Electric sponge.

Main errors:

- Turn 1 p1: overvalued immediate Spikes and underpriced preserving Cloyster
  against Zapdos lead pressure.
- Turn 2 p1: named the Snorlax pivot but chose Hidden Power instead of the
  actual Thunder, which had better payoff into the likely special sponge.
- Turn 3 p1: repeated the Electric-preservation miss before correcting it on
  turn 7.
- Turn 8 p1: overcalled Explosion. The actual line used the predicted Cloyster
  absorber switch as a clean Rapid Spin window.
- Turns 9-10: over-simplified the support mirror after Spin. The actual mirror
  reset Spikes, used Surf chip, then Toxic into the Raikou handoff.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | p1 Cloyster vs p2 Zapdos | p1 Spikes; p2 Thunder | p1 Raikou; p2 Thunder | p1 miss, p2 top | Preserve Cloyster when Zapdos lead pressure is too high. |
| 2 | Raikou vs Zapdos | p1 Hidden Power; p2 Snorlax | p2 Snorlax; p1 Thunder miss | p1 miss, p2 top | If Snorlax is the likely pivot, Thunder has the better payoff. |
| 3 | Raikou vs Snorlax | p1 Thunder; p2 Double-Edge | p1 Cloyster; p2 Double-Edge | p1 miss, p2 top | Use lower-value Cloyster to preserve Raikou. |
| 4 | Cloyster 72 vs Snorlax | p1 Spikes; p2 leave to pressure Cloyster | p2 Cloyster; p1 Spikes | p1 top, p2 acceptable | Spikes first, support mirror second. |
| 5 | Cloyster mirror | p1 Toxic/coverage, Raikou alternative; p2 Spikes | p1 Raikou; p2 Spikes | p1 acceptable, p2 top | Handoff after support can be immediate. |
| 6 | Raikou vs opposing Cloyster | p1 Thunder; p2 Snorlax | p2 Snorlax; p1 Thunder miss | both top | Electric pressure forces the special sponge. |
| 7 | Raikou 100 vs Snorlax 94 | p1 Cloyster; p2 Double-Edge | p1 Cloyster; p2 Double-Edge | both top | Prior miss transferred. |
| 8 | Cloyster 38 vs Snorlax 95 | p1 Explosion; p2 Cloyster absorber | p2 Cloyster; p1 Rapid Spin | p1 miss, p2 top | Predicted absorber switch made Spin cleaner than boom. |
| 9 | Cloyster mirror after Spin | p1 Raikou; p2 Spin/Toxic/Surf | p2 Spikes; p1 Surf | both miss | The mirror can reset layer plus chip before handoff. |
| 10 | Cloyster mirror after reset | p1 Rapid Spin; p2 Explosion/direct punish | p1 Raikou; p2 Toxic | both miss | Toxic into the handoff can beat repeating Spin or boom. |

## Reusable Lessons

Lead Cloyster into Zapdos is not automatically a Spikes turn. If Zapdos can
make the support piece lose too much value immediately, preserve Cloyster and
use the Electric answer first.

When the likely pivot is Snorlax rather than a Ground immune to Electric,
Thunder can be better than the generic Hidden Power midground. The branch gate
is not "can this move hit every pivot?" but "does this move punish the most
likely pivot enough?"

Predicted Explosion absorber switches create Rapid Spin windows. On turn 8,
Snorlax's side respected Cloyster Explosion and switched to its own Cloyster;
p1 used that lower-pressure turn to clear Spikes instead of cashing out.

After one Spin, the hazard loop is not solved. The opposing Cloyster can reset
Spikes, and the next support move may be Surf chip or Toxic into the Electric
handoff rather than another immediate Spin or Explosion.

## Source-To-Policy Extraction

Trigger:
  Cloyster has set Spikes, is low enough to threaten Explosion, and the
  opponent has a likely lower-value absorber for the cash-out.

Default:
  Before booming, ask whether the expected absorber switch creates a clean
  Rapid Spin, reset, Toxic, Surf, or handoff turn. If the route value is hazard
  control, Spin can be the cash-out punish.

Exceptions:
  Explosion is correct when the active target is the irreplaceable route
  blocker, no absorber is available or acceptable, the Spin does not matter, or
  the opponent can punish Spin with a Ghost, setup, or decisive damage.

Worst branch:
  The advisor calls Explosion because Cloyster is low, misses the clean Spin
  window, and then loses the hazard loop to a reset layer plus status.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  three-layer Spikes, Rapid Spin clearing all layers, Ghost immunity, and local
  support move timing.

Drill:
  Build a four-prompt regression: preserve Cloyster from Zapdos lead pressure,
  switch Cloyster into Snorlax to preserve Raikou, Spin on the predicted
  Explosion absorber switch, and re-solve after the opponent resets Spikes.

## Next Rep

Run a fresh replay transfer focused on hazard-loop Spin windows after
support-cash-out threats. The regression artifact is
`workspace/quick_tests/hazard_loop_spin_window_probe_001_2026-05-14.md`.
