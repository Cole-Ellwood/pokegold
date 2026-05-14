# Janine Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; local Weezing is
  Poison/Dark.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Qwilfish Spikes boundary example:
  `docs/pokemon_mastery/worked_examples/janine_qwilfish_spikes_arbitration.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Janine as adaptive first-three: Qwilfish / Tentacruel / Muk.
- Haze source: `engine/battle/effect_commands.asm`; it resets both sides' stat
  stages.
- Sleep Talk and Rest source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Quiver Dance, Sleep Powder, Explosion, Sludge Bomb, Fire Blast, Flamethrower,
  Thunderbolt, Psychic, Giga Drain, Surf, Earthquake, Ice Beam, and Rapid Spin
  are listed in `docs/agent_navigation/hack_mechanics_reference.md`.
- Rocky Helmet, Expert Belt, Wise Glasses, Mystic Water, and Leftovers behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Contact evidence for Rocky Helmet depends on `data/moves/contact_flags.asm`.
- Expert principle sources: Smogon GSC Spikes, Explosion, status, setup, and
  poison-team route control.

Boss roster:

```text
Lv60 Qwilfish @ Leftovers:
  Spikes / Sludge Bomb / Surf / Explosion

Lv61 Tentacruel @ Mystic Water:
  Rapid Spin / Surf / Sludge Bomb / Haze

Lv62 Muk @ Rocky Helmet:
  Flamethrower / Sludge Bomb / Sleep Talk / Rest

Lv62 Nidoking @ Expert Belt:
  Earthquake / Sludge Bomb / Ice Beam / Thunderbolt

Lv63 Weezing @ Leftovers:
  Sludge Bomb / Fire Blast / Thunderbolt / Explosion

Lv64 Venomoth @ Wise Glasses:
  Sleep Powder / Psychic / Giga Drain / Quiver Dance
```

Boss likely openings:

- Janine is source-listed as adaptive first-three, not fixed Qwilfish.
- Plan for Qwilfish / Tentacruel / Muk, with Qwilfish favored by the current
  weighted opener rule.
- The player may know this boss roster before the fight. Janine's ordinary boss
  AI still must not know the player's unrevealed team, hidden moves, hidden
  item, private stats, or current-turn input.

## Boss Routes

Qwilfish route:

- Goal: start Spikes, apply physical poison pressure with Sludge Bomb, threaten
  Surf coverage, then trade with Explosion when the hazard job is done.
- What it punishes: passive leads, hazard plans that ignore Janine's spinner,
  and sacrificing the only Nidoking/Venomoth answer to Explosion.
- Denial idea: pressure Qwilfish before Spikes plus Explosion becomes a route
  trade. If Qwilfish can boom on an irreplaceable piece, that branch must be
  priced before choosing slow progress.
- Hazard contract: if the player has a spinner, Janine has no Ghost on this
  roster to block Rapid Spin directly. Qwilfish must make the layer convert
  before removal, or punish the spinner with damage, status pressure from the
  rest of the team, or Explosion. Do not treat "no Rapid Spin revealed" as
  proof the player cannot remove the layer.

Tentacruel route:

- Goal: remove hazards with Rapid Spin, reset boosts with Haze, and threaten
  Surf / Sludge Bomb damage.
- What it punishes: setup plans that ignore Haze and hazard plans with no spin
  punish.
- Denial idea: if the player's route depends on hazards or boosts, Tentacruel
  must be pressured or forced into a bad reset turn. If not, preserve resources
  for Nidoking, Weezing, or Venomoth.

Muk route:

- Goal: sit on exchanges with RestTalk, punish contact with Rocky Helmet where
  applicable, and threaten Flamethrower / Sludge Bomb.
- What it punishes: contact-heavy physical plans, weak chip into Rest, and
  assuming a sleeping RestTalk Pokemon is harmless.
- Denial idea: force Rest only if the sleep turns can be converted. Otherwise,
  Muk may simply reset while Janine's other routes remain intact.

Nidoking route:

- Goal: break the player's pivot map with Earthquake, Sludge Bomb, Ice Beam,
  Thunderbolt, and Expert Belt.
- What it punishes: type-slogan switching and assuming the obvious Poison answer
  covers all four attacks.
- Denial idea: preserve the real Nidoking answer until local type/passive/damage
  evidence confirms the pivot. If Expert Belt applies, the route may flip.

Weezing route:

- Goal: use broad coverage and Explosion to remove the one piece that stops
  Janine's remaining route.
- What it punishes: switching an irreplaceable answer into coverage without
  pricing Explosion, and treating Poison/Dark typing like vanilla Weezing.
- Denial idea: ask what Weezing removes if it explodes. If that removal opens
  Venomoth or Nidoking, preservation may dominate immediate chip.

Venomoth route:

- Goal: use Sleep Powder or Quiver Dance to become a fast special route with
  Psychic and Giga Drain.
- What it punishes: giving it a free setup turn, letting Sleep Powder remove
  the anti-setup piece, or relying on a single revenge hit without checking
  Speed and damage after Quiver Dance.
- Denial idea: determine whether sleep or Quiver Dance is the immediate losing
  branch. If either lands, re-score; do not continue the old plan.

## Player Plan Template

Primary route:

- Janine wants to stack hazards, remove the player's hazard/setup state, then
  trade Explosion or coverage into the exact piece that stops Nidoking or
  Venomoth. The player should identify that piece before turn 1.
- Because the opener can be Qwilfish, Tentacruel, or Muk, the first player lead
  should not be chosen only to beat Qwilfish. It must also avoid giving
  Tentacruel a free Spin/Haze route or Muk a free RestTalk/contact-punish route.

Backup route:

- If Qwilfish gets Spikes or Tentacruel erases the player's setup/hazards,
  shorten the fight around immediate KOs, status, phazing/Haze, or preserving
  the Nidoking/Venomoth answer.

Best lead profile:

- A lead that pressures Qwilfish, does not donate free Haze/Rapid Spin value to
  Tentacruel, and does not rely on contact-heavy chip into Muk without pricing
  Rocky Helmet. It must not be the only answer to Nidoking or Venomoth.
- If the player has a Rapid Spin route, the lead or early pivot map should ask
  whether Spin can happen before Spikes convert, and what Janine gains if she
  Explodes or attacks the spinner.

Avoid as lead:

- A hazard lead if Tentacruel spins for free.
- A setup lead if Tentacruel can Haze before the boost converts.
- A contact-heavy route into Muk unless Rocky Helmet/contact evidence is priced.
- The only Venomoth answer if Qwilfish or Weezing can explode on it.

First-turn question:

```text
Which adaptive opener appeared?

Qwilfish: can we pressure Spikes / Explosion without spending the
Nidoking/Venomoth answer?

Tentacruel: is Rapid Spin, Surf damage, Sludge Bomb damage, or Haze the live
route, and does our lead give it a free reset?

Muk: are we donating contact chip into Rocky Helmet or weak progress into
RestTalk?
```

If Qwilfish sets Spikes:

- Re-score grounded player Pokemon, the player's Rapid Spin options, and
  whether Venomoth or Nidoking now needs less chip to clean.
- If the player has no spinner, treat the layer as a real route tax. If the
  player has an unrevealed or live spinner, decide whether Qwilfish can make
  the layer convert before removal or should cash out into the spinner route.

If Tentacruel opens or enters:

- Decide whether Rapid Spin or Haze is the live route. Do not keep setting
  hazards or boosts into a free reset.
- If the player is not relying on hazards or boosts, do not overchase
  Tentacruel; preserve the answer map for Nidoking, Weezing, and Venomoth.

If Muk opens, or uses Rest or Sleep Talk:

- Track Rest turns and Sleep Talk branches. A sleeping Muk may still attack;
  punish the Rest cycle only if the follow-up creates real progress.
- Avoid contact-heavy lines unless the damage or contact flag evidence says the
  Rocky Helmet branch is acceptable.

If Nidoking enters:

- Require local type/passive/damage evidence for the intended pivot. Expert
  Belt coverage can turn a comfortable-looking answer into a losing branch.

If Venomoth enters:

- Price Sleep Powder and Quiver Dance before every passive move. If the current
  Pokemon cannot deny either branch, pivot or sacrifice with a named follow-up.

Worst plausible branch:

- The player lets Qwilfish start Spikes, loses hazard or setup progress to
  Tentacruel, spends the Nidoking/Venomoth answer into Muk or Weezing, and then
  gets swept or broken after Sleep Powder, Quiver Dance, coverage, or Explosion.

Abandon conditions:

- The only Nidoking or Venomoth answer is asleep, exploded on, or below its
  required damage threshold.
- Tentacruel can spin or Haze without giving up decisive pressure.
- Muk's RestTalk cycle cannot be converted into progress.
- Venomoth has boosted and no immediate denial route remains.
- Weezing can Explode on an irreplaceable piece.
- Type-chart, passive, contact, item, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Janine is a role-preservation fight. The GSC transfer is to identify which
  piece is irreplaceable against the live breaker, then refuse trades that make
  Janine's later Nidoking or Venomoth route uncontestable.
