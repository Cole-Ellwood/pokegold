# Item Removal And Revealed Package Review 001 - 2026-05-15

Study status: expert replay review and policy update source. This is not fresh
replay-transfer proof and does not count as progress by itself.

Parent miss:
`workspace/quick_tests/one_time_trade_setup_transfer_001_smogtours-gen2ou-935835_2026-05-15.md`

Current replay source:

- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935835`
- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935835.log`

Supporting local expert reviews:

- `reviews/2026-05-13_smogtours-gen2ou-891179.md`
- `reviews/2026-05-13_smogtours-gen2ou-902727.md`
- `reviews/2026-05-13_smogtours-gen2ou-917190.md`
- `reviews/2026-05-13_smogtours-gen2ou-935544.md`

## Review Question

The latest fresh transfer had 0 severe, hidden-info, state, and mechanics
errors, but only 8/30 top-match and 18/30 acceptable-match. The failure was
positive move selection:

- Turn 1: Jynx used `Thief`; I ranked generic sleep first.
- Turns 13-15: Starmie used `Substitute`, then `Nightmare`, then another
  `Substitute`; I kept ranking generic `Surf` pressure.

The question is whether these were isolated replay quirks or a repeated policy
gap.

## Evidence

Jynx and Thief:

- In `891179`, Jynx used `Thief` on Snorlax before applying sleep pressure.
  The review says item removal changed the long-term Snorlax route because
  passive recovery no longer erased Ice Beam, Spikes, and sleep-turn damage.
- In `902727`, Jynx and Gengar used `Thief` against reset hubs before the
  route converted through hazards, phazing, and Explosion.
- In the fresh `935835` miss, Jynx again faced an obvious bulky receiver and
  used `Thief` immediately. The line did not need sleep to hit first; it made
  future Snorlax turns more expensive even after Jynx was removed.

Starmie and revealed punishment packages:

- In `917190`, Starmie's `Substitute` / `Confuse Ray` / `Surf` / `Nightmare`
  package became an endgame route, but the review also warns that Substitute
  can become self-tax if the opponent breaks it cleanly.
- In `935544`, Starmie entered on sleeping Snorlax, used `Nightmare`, and
  turned the live sleep state into immediate pressure. The review separates the
  route pressure from the later crit outcome.
- In fresh `935835`, Starmie revealed `Substitute` as Snorlax used `Rest`,
  then revealed `Nightmare` while Snorlax slept. The set reveal changed the
  action ranking: the route was no longer "Surf the sleeping Snorlax"; it was
  "keep the sleep-state package live unless the opponent has a cleaner reset."

## Policy Update

Item-removal extension:

When a status-capable lead or special attacker faces an obvious bulky receiver,
rank `Thief` beside sleep and coverage before choosing the status move. Item
removal is top only if it changes a named route: recovery denial, hazard
clock, sleep-turn pressure, damage threshold, or reset-hub removal. It is not a
generic "click utility" script.

Revealed-package extension:

When a move reveal shows a coherent package, reclassify the whole route before
the next move. `Substitute` into a RestTalk target may be passive scouting, but
if `Nightmare`, confusion, Leech Seed, Growth, Baton Pass, or phazing support
is revealed or strongly implied, the follow-up move can be the route converter.
Rank the package follow-up above generic damage unless the opponent already
has a revealed reset, phaze, faster breaker, or low-cost switch that invalidates
the package.

## Next Transfer Gate

For every nontrivial fresh turn with a status-capable or package-revealing
Pokemon, freeze this mini-rank before selecting the move:

1. Item removal or revealed package follow-up.
2. Coverage into the named receiver or reset hub.
3. Counter-handoff or phaze.
4. Status.
5. Generic damage.

This ranking is not mandatory order; it is a checklist to prevent choosing the
visible safe move before pricing the route-converting move.
