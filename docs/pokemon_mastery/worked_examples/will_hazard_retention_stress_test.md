# Worked Example: Will Hazard Retention Stress Test

Purpose: stress-test the hazard-control lesson from
`../reviews/2026-05-13_smogtours-gen4ou-878566.md` against Will's local boss
route. This is a route-arbitration drill, not a claim that hazards are always
the right plan.

Local evidence:

- Will route map: `../boss_route_maps/will_turn1_route_sheet.md`.
- Will pre-battle route sheet: `will_pre_battle_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Roster source: `data/trainers/parties.asm`.
- Generated mechanics reference:
  `../../agent_navigation/hack_mechanics_reference.md`.
- Mechanics overview:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.

Expert transfer source:

- DPP hazard-control review:
  `../reviews/2026-05-13_smogtours-gen4ou-878566.md`.
- Smogon GSC Spikes material:
  <https://www.smogon.com/gs/articles/gsc_spikes>.
- Smogon DPP entry-hazard material:
  <https://www.smogon.com/dp/articles/entry_hazards>.

## Pattern Being Tested

Bad shortcut:

```text
We got hazards up, so we are making progress.
```

Better policy:

```text
Hazards are a contract:
  set them;
  retain them or price removal;
  convert them before they disappear.
```

Against Will, this matters on both sides. Forretress can set Spikes, poison,
Protect, and Explode. Starmie can remove the player's hazards with Rapid Spin
while threatening Surf, Psychic, and Thunderbolt. A hazard turn that does not
change Starmie's spin incentives, Slowbro's Rest/Amnesia clock, or the
Alakazam/Houndoom/Xatu answer map may be only a decorative turn.

## Stress-Test State

Use this public-state prompt, then substitute the user's real team:

```text
Will active:
  Forretress or Starmie

Will bench:
  Slowbro, Alakazam, Houndoom, Xatu, and the other hazard-control piece still
  relevant unless fainted

Hazard state:
  player side Spikes layers:
  Will side Spikes layers:
  local max layers: 3
  Rapid Spin clears all layers

Player route:
  depends on forcing repeated grounded entries, phazing, Rest pressure,
  revenge thresholds, or a Starmie punish

Player concern:
  Starmie may spin before the layer converts; Forretress may turn its own layer
  into Toxic, Protect, Explosion, or safe entry for Will's special attackers
```

Do not decide from layer count alone. Decide from the set-retain-convert
contract.

## Required Questions

Before advising a hazard-related move, fill this:

```text
Set:
  who creates the layer, current layer count, target max, and opportunity cost

Retain:
  who blocks, punishes, traps, threatens, or removes Starmie / Forretress

Convert:
  what route improves before the layer is spun away or made irrelevant

Removal branch:
  what happens if Rapid Spin clears all layers next turn

Counter-hazard branch:
  what happens if Forretress sets Spikes on our side instead

Irreplaceable piece:
  which answer cannot take poison, Explosion, Spikes, or coverage chip

Answer flip:
  what evidence would make attacking, switching, spinning, or sacrificing
  better than another layer
```

## Move-Class Arbitration

Setting a layer rises when:

- Will's side is below three layers;
- the setter survives the worst plausible branch;
- Starmie cannot spin for free or the spin turn is punishable;
- the layer changes a switch, Rest, revenge, phazing, or KO threshold;
- the setter is not the only answer to Alakazam, Houndoom, or Slowbro.

Setting a layer falls when:

- Will's side is already at three layers;
- Starmie can immediately remove all layers without giving up a larger route;
- Forretress or Slowbro gets a free setup/status/recovery turn;
- the layer does not convert before Will's faster special route becomes live;
- the setter is needed later for spin, Explosion, phazing, or a defensive job.

Attacking or pressuring Starmie rises when:

- Starmie is the reason the hazard route is fake;
- damage forces Recover, removes the spin turn, or puts Starmie into revenge
  range;
- the attack also preserves the answer map for Slowbro, Alakazam, and Houndoom.

Removing Will's hazards rises when:

- grounded switch count is now the limiting clock;
- the player's Alakazam/Houndoom/Slowbro answer cannot afford another entry;
- removal does not hand Slowbro a free Amnesia/Rest route or Starmie a free
  attack.

Explosion, sacrifice, or one-time trade rises when:

- the trade removes Starmie, Forretress, or Slowbro as the piece blocking the
  current route;
- the traded Pokemon has no remaining irreplaceable job;
- the route after the trade survives Alakazam, Houndoom Pursuit, and Xatu
  Future Sight.

## Will-Specific Failure Signs

- "Set the third layer" while Starmie spins for free next turn.
- "Keep hazards up" without naming who retains them.
- "Forretress already did its job" while Explosion can still remove the only
  special answer.
- "Starmie only spun" when Rapid Spin erased the player's entire route and
  created tempo.
- "We can switch around" while Will's Spikes, Pursuit, and Future Sight make
  switching the losing clock.
- No one names what the layer changes before removal.

## Example Verdict Shape

```text
Recommendation:
  set layer / attack Starmie / remove hazards / switch / trade / shorten route

Why:
  The current hazard contract is [set / retain / convert]. The weak part is
  [retention / conversion / our own side's switch tax].

Worst plausible branch:
  if we choose the wrong class, Will gets [free Spin / Spikes / Toxic /
  Explosion / Amnesia / Pursuit / Future Sight landing] and our [answer] no
  longer performs its later role.

What changes the answer:
  Starmie HP, spin punish, Forretress Explosion state, current layer count,
  grounded switch count, Slowbro Rest timing, Houndoom Pursuit range, Xatu
  Future Sight counter, and local type/passive/damage evidence.
```

## Boss-Battle Transfer

This stress test generalizes to other hazard bosses:

- Karen: Gengar sets Spikes, Donphan spins and Roars, then Tyranitar or
  Houndoom converts the lost turns.
- Pryce: Cloyster sets, Dewgong spins, Piloswine turns layers into Roar value.
- Koga or Janine: Poison, trap, Haze, Spin, and layered hazards compete for the
  same turns.
- Brock or Bruno: hazards matter most when they tax the real setup or physical
  answers before those answers can act.

The action test is always:

```text
If the layer stays for only one turn, what route does it improve?
If the layer disappears immediately, what did we gain anyway?
If neither answer is concrete, the hazard turn is suspect.
```

## Extracted Lesson

The DPP hazard-control replay becomes a Will policy rule: do not call hazards
progress until the set-retain-convert contract is real. In the romhack, three
layers are powerful because the switch tax can become enormous, but Rapid Spin
clears all layers. Will punishes lazy hazard play by making the player answer
two questions at once: can the layer stay or convert, and which future answer
is being poisoned, exploded on, Pursuited, or forced through Future Sight while
the player spends the hazard turn?
