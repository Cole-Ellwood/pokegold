# Worked Example: Karen Hazard Retention Stress Test

Purpose: stress-test the hazard-control lesson from
`../reviews/2026-05-13_smogtours-gen4ou-878566.md` against Karen's local boss
route. This is a route-arbitration drill, not a claim that hazards should be
the default Karen plan.

Local evidence:

- Karen route map: `../boss_route_maps/karen_turn1_route_sheet.md`.
- Karen pre-battle route sheet: `karen_pre_battle_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Roster source: `data/trainers/parties.asm`, `KarenGroup`.
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
We set hazards, so we are making progress.
```

Better policy:

```text
Hazards are a contract:
  set them;
  retain them or price removal;
  convert them before the opponent's next route inherits the turn.
```

Against Karen, the contract has an extra condition:

```text
Do all of that while keeping the Tyranitar and Houndoom answers awake,
unpoisoned, untrapped, and not Roared out of position.
```

Gengar can combine Spikes with Hypnosis. Donphan can clear all player Spikes
with Rapid Spin or break a setup line with Roar. Crobat can make status routes
pause under Safeguard or start a poison/confusion clock. Murkrow and Houndoom
can punish forced switches with Pursuit or special pressure. Tyranitar and
Houndoom are the likely converters after the hazard turns have been spent.

## Stress-Test State

Use this public-state prompt, then substitute the user's real team:

```text
Karen active:
  Gengar or Donphan

Karen bench:
  Murkrow, Tyranitar, Crobat, Houndoom, and the other hazard-control piece
  still relevant unless fainted

Hazard state:
  player side Spikes layers:
  Karen side Spikes layers:
  local max layers: 3
  Rapid Spin clears all layers
  Flying-type Pokemon ignore Spikes in the local source

Sleep and disruption state:
  sleep clause status:
  Gengar Hypnosis branch:
  sleeping Pokemon's remaining job:
  Crobat Safeguard turns:

Player route:
  depends on forcing grounded entries, preserving Tyranitar/Houndoom answers,
  denying Dragon Dance, denying Sunny Day, or converting chip into a KO

Player concern:
  the hazard turn may let Gengar disable an answer, Donphan erase all layers,
  Crobat block status, Tyranitar boost, or Houndoom set sun
```

Do not decide from layer count alone. Decide from the set-retain-convert-answer
contract.

## Required Questions

Before advising a hazard-related move, fill this:

```text
Set:
  who creates the layer, current layer count, target max, and opportunity cost

Retain:
  how Donphan's Rapid Spin is denied, punished, or made irrelevant

Convert:
  what route improves before Donphan spins, Roars, or another Karen route starts

Sleep branch:
  what happens if Gengar uses Hypnosis or the current answer is already asleep

Spin branch:
  what happens if Donphan clears all layers next turn

Roar branch:
  what happens if Donphan removes the setup user or chosen pivot from the field

Converter branch:
  what happens if Tyranitar uses Dragon Dance or Houndoom uses Sunny Day while
  we spend the hazard turn

Irreplaceable answer:
  which Tyranitar or Houndoom answer cannot be slept, poisoned, trapped,
  chipped through Spikes, or forced out

Answer flip:
  what evidence would make attacking, switching, spinning, phazing, or
  sacrificing better than another layer
```

## Move-Class Arbitration

Setting a layer rises when:

- Karen's side is below three layers;
- the next layer changes a KO, revenge, Rest, phazing, or switch threshold;
- Donphan cannot spin for free or the spin turn gives the player a better
  route than the layer cost;
- the setter does not expose the only Tyranitar or Houndoom answer to Hypnosis,
  Pursuit, Toxic, Dragon Dance, or Sunny Day;
- the player can convert before Crobat Safeguard, Donphan Roar, or Karen's next
  cleaner takes over.

Setting a layer falls when:

- Karen's side is already at three layers;
- Donphan can immediately remove all layers without giving up a larger route;
- Gengar can sleep the only converter answer;
- the layer only creates future value while Tyranitar or Houndoom has an
  immediate conversion turn;
- Crobat's Safeguard blocks the status route that was supposed to exploit the
  hazard damage.

Pressuring Gengar rises when:

- Hypnosis can disable the only Tyranitar or Houndoom answer;
- Spikes on the player's side would make the required defensive cycle fail;
- Gengar's Dream Eater branch becomes real because the current target is
  sleeping;
- removing Gengar also frees a later sleep/status route.

Pressuring Donphan rises when:

- Donphan is the reason the player's hazard route is fake;
- damage forces Donphan to attack or Rest instead of spinning or Roaring;
- the player's route needs setup to stay in place and Roar would erase it;
- Donphan is the only remaining piece that can remove the player's layers.

Removing Karen's hazards rises when:

- grounded switch count is now the limiting clock;
- the Tyranitar or Houndoom answer needs multiple entries to work;
- removal does not give Tyranitar Dragon Dance, Houndoom Sunny Day, or Crobat
  Safeguard for free.

Sacrifice or one-time trade rises when:

- the trade removes Gengar, Donphan, Tyranitar, or Houndoom as the current
  route blocker;
- the sacrificed Pokemon has no remaining irreplaceable job;
- the post-trade route still covers the next Karen converter.

Status falls when:

- Crobat's Safeguard is active;
- the target is already statused;
- the status miss branch lets Tyranitar or Houndoom convert;
- Gengar sleep pressure makes a slower status plan too expensive.

## Karen-Specific Failure Signs

- "Gengar only set Spikes" when Hypnosis can decide which answer is disabled
  next.
- "Donphan only spun" when Rapid Spin erased all layers and bought Karen the
  next route.
- "Donphan only Roared" when Roar removed the setup or pivot that made the
  hazard route meaningful.
- "Set another layer" while Tyranitar gets Dragon Dance or Houndoom gets Sunny
  Day.
- "Use status to punish" while Crobat Safeguard is active.
- "Switch out safely" without pricing Pursuit.
- "We can ignore hazards" while the grounded Tyranitar or Houndoom answer is
  being taxed below its required threshold.
- "Gengar spinblocks Donphan" without local Rapid Spin/type evidence for this
  exact interaction.

## Example Verdict Shape

```text
Recommendation:
  set layer / pressure Gengar / pressure Donphan / remove hazards / switch /
  phaze / trade / shorten route

Why:
  The current hazard contract is [set / retain / convert / keep answer map
  intact]. The weak part is [sleep / spin / Roar / conversion / own-side
  switch tax].

Worst plausible branch:
  if we choose the wrong class, Karen gets [Hypnosis / free Spin / Roar /
  Safeguard / Pursuit / Dragon Dance / Sunny Day] and our [answer] no longer
  performs its later role.

What changes the answer:
  current layer count, Donphan HP and speed, Gengar sleep branch, sleep clause,
  Crobat Safeguard turns, Pursuit range, Tyranitar boost state, Houndoom sun
  turns, grounded switch count, and local type/passive/damage evidence.
```

## Boss-Battle Transfer

This stress test generalizes to other route-disruption bosses:

- Will: hazards fail if Starmie spins or Forretress converts the hazard turn
  into Toxic, Protect, Explosion, or safe entry.
- Koga and Janine: Spikes, Rapid Spin, Haze, Toxic, trap, Rest, and Explosion
  compete for the same turns.
- Pryce: Cloyster sets hazards, Dewgong removes them, Piloswine turns them into
  Roar value, and Sneasel inherits the endgame if answers are spent.
- Lance and Red: the important question is what setup or weather route inherits
  the board after the first hazard/control sequence.

The action test is always:

```text
If the layer stays for only one turn, what route does it improve?
If Donphan removes it immediately, what did we gain anyway?
If the hazard turn gives Karen a converter turn, which answer survives?
```

## Extracted Lesson

Karen hazard retention is not just set, retain, convert. It is set, retain,
convert, and keep the Tyranitar/Houndoom answer map intact through sleep,
Pursuit, Roar, Safeguard, and weather pressure. A layer only matters if the
player can either keep it, cash it out, or make the removal turn cost Karen
more than the player spent.
