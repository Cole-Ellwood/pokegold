# Romhack Context: Snorlax

Status: source-checked from local docs/data. Not a full matchup table.

Use carefully. Snorlax is tier-defining in vanilla GSC, so expert material will
discuss it constantly. That does not mean Snorlax appears constantly in Gym
Leader Lab. Study those sources for transferable principles about bulky setup
anchors, Rest cycles, answer preservation, and route denial, then apply the
principle to the boss's actual Pokemon.

Scope: Pokemon Gold romhack / Gym Leader Lab. Use this to keep vanilla GSC
Snorlax principles from being transferred blindly.

## Vanilla GSC Strategic Baseline

Expert GSC sources agree on the strategic shape:

- Snorlax is central because it combines special bulk, strong Normal STAB,
  setup, recovery, coverage, sleep, and Selfdestruct/Self-Destruct pressure.
- No single answer covers every relevant Snorlax set. Practical answers are
  overlapping packages: Normal-resistant phazers, Ghosts, Growl/Charm users,
  Fighting pressure, Explosion trades, status plus hazards, and one's own
  Snorlax.
- The correct question is not "what counters Snorlax?" The correct question is
  "which Snorlax set hypotheses are still live, and which remaining pieces
  answer each one from this HP/status/hazard/PP state?"

## Romhack Facts

Sources:

- `docs/agent_navigation/hack_mechanics_reference.md`
- `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- `data/pokemon/base_stats/snorlax.asm`
- `data/trainers/parties.asm`

Verified facts:

- Snorlax's local base stats are HP 160 / Atk 110 / Def 65 / Spe 30 / SpA 65 /
  SpD 110.
- Snorlax is pure Normal.
- Snorlax's held item entries are `LEFTOVERS`, `LEFTOVERS`.
- Snorlax's TM/HM list includes classic route-relevant moves such as Curse,
  Toxic, Thunder, Earthquake, Psychic, Shadow Ball, Sleep Talk, Fire Blast,
  Double-Edge, Rest, Fire Punch, ThunderPunch, Surf, and Strength.
- The local type chart changes Poison into Normal from neutral to super
  effective. Local docs explicitly describe Poison -> Normal as a Snorlax
  answer.
- Red's current trainer-data Snorlax is:

```text
Level 75 Snorlax @ Leftovers
Curse / Sleep Talk / Rest / Body Slam
```

## Transfer Implications

- Preserve the general concept: a bulky anchor can be a wall, status absorber,
  Rest-cycle anchor, setup win condition, or endgame cleaner.
- Do not preserve every vanilla conclusion. In this hack, Poison attacks can be
  part of the Snorlax answer map, and three-layer Spikes make repeated grounded
  re-entry much harsher than vanilla GSC.
- Do not assume vanilla mixed Snorlax damage without a local calc. Snorlax has
  65 SpA in local data, but it still has broad special TM access.
- Do not assume Red's Snorlax can explode or use coverage. Current source data
  gives it Curse / Sleep Talk / Rest / Body Slam.
- Do not assume all boss Snorlax encounters share Red's set. Check the trainer
  roster or public battle state before advising.

## Advice Checklist

When Snorlax matters, ask:

1. Which side owns the Snorlax route?
2. What moves are confirmed, and what fourth-move hypotheses remain legal?
3. Is it a Curse route, RestTalk anchor, coverage lure, sleep/status absorber,
   or immediate damage trade?
4. Which of our pieces answer each live hypothesis?
5. Which answer is irreplaceable after current HP, status, Spikes layers, PP,
   and speed are considered?
6. Can Poison pressure, phazing, Explosion, sleep, paralysis, or three-layer
   Spikes force Snorlax into a losing Rest cycle?
7. If we sacrifice a Snorlax answer, what concrete route removes or neutralizes
   Snorlax before it converts?

## Remaining Verification

- Build matchup-specific damage checks for local Poison attackers into Snorlax.
- Build damage checks for Snorlax's special coverage in this hack before
  treating Fire Blast / Surf / Thunder as major coverage routes.
- Check trainer rosters for every boss Snorlax set before making boss-specific
  advice.
