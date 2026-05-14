# Worked Example: Status Reset Map In Boss Fights

Source basis:

- Smogon's GSC status article treats Heal Bell and Rest as major modifiers to
  status value. Status is not just "landed" or "missed"; it can force a cure,
  create a window, or be wasted into a reset.
- Smogon's GSC Spikes article frames poison and paralysis as strongest when
  paired with switching pressure, phazing, forced Rest, or setup conversion.
- Local boss data adds concrete reset/prevention routes: Full Heal, Full
  Restore, Safeguard, Rest, Recover, Moonlight, Morning Sun, Synthesis, and
  Milk Drink appear in `data/trainers/attributes.asm` and
  `data/trainers/parties.asm`.

## Recipe Used

Before relying on status, answer two questions:

1. What resets or prevents this status?
2. What do we gain if the boss uses that reset?

If the second answer is blank, the status may only be feeding the boss a
low-cost cure turn.

## Expert-Play Anchor: Jolteon Reset Route

Review:

- `../reviews/2026-05-13_smogtours-gen2ou-933547.md`

In that 239-turn GSC game, Jolteon took paralysis on turn 18 and poison on turn
179, but neither status ended the route because Jolteon still had Rest and the
team could cover the sleep turns. The status was real pressure, but it did not
become decisive because the reset map was intact. The lesson for boss advice is
not "status does not matter." It is "status matters only through the route it
actually changes after cures, Rest, Sleep Talk, switch cost, and team support
are priced."

## Misty: Full Heal Against Status Pressure

Local evidence:

- Misty has `FULL_HEAL` in `data/trainers/attributes.asm`.
- Misty's route includes Politoed Hypnosis, Starmie Recover, Quagsire Rest, and
  Lanturn Thunder Wave in `data/trainers/parties.asm`.

Bad default:

- "Paralyze or poison Starmie because status is good into Recover."

Why that fails:

- If the status only triggers Full Heal while Starmie remains healthy, the user
  spent a turn and a finite status move without changing the Recover route.
  The status was not progress; it was an item prompt.

Better policy:

- Status rises when it forces Full Heal on a turn where the user also gains a
  threshold, safe entry, setup turn, or weather denial.
- Direct damage rises when it puts Starmie or Lanturn into a range where Full
  Heal does not solve the HP problem.
- Preserve status when Quagsire or Lanturn is the target whose cure turn will
  actually open the route.

Answer-changing information:

- Full Heal already spent makes later status much stronger.
- Rain active makes spending a turn to bait Full Heal more expensive.
- A player team with no safe Starmie threshold may need status despite the
  item, but only with a named follow-up.

## Koga And Champion: Full Restore As HP Plus Status Reset

Local evidence:

- Koga and Champion have `FULL_RESTORE` in `data/trainers/attributes.asm`.
- Koga has Muk with Rest, Umbreon with Moonlight and Toxic, and Crobat with
  Toxic pressure in `data/trainers/parties.asm`.

Bad default:

- "Toxic the bulky piece and wait."

Why that fails:

- Full Restore can remove both the poison and the damage that made poison
  meaningful. If the user cannot punish the item turn or force it early, Toxic
  may only spend tempo while Koga builds the trap, Haze, Moonlight, or setup
  map.

Better policy:

- Use Toxic when it forces Full Restore before the boss's main converter is
  ready, or when the item turn gives a clean switch, setup, phaze, or KO.
- Attack or force a threshold when Full Restore is likely and the poisoned
  target has not yet been made expensive enough to cure.
- Track the item as a one-time resource. After Full Restore is gone, a second
  status route may become decisive.

Answer-changing information:

- Full Restore already spent flips many Toxic clocks from bait to progress.
- A phazer or Haze user alive can punish the bulky route after the item.
- If the status user is also the only answer to Nidoking, Crobat, or Lance's
  next route, spending it to bait an item may be too expensive.

## Karen And Blaine: Safeguard Prevention Window

Local evidence:

- Karen Crobat has Safeguard in `data/trainers/parties.asm`.
- Blaine Ninetales has Safeguard in `data/trainers/parties.asm`.
- Blaine also has `FULL_HEAL` in `data/trainers/attributes.asm`.

Bad default:

- "Use Thunder Wave, Toxic, or sleep because the target is dangerous."

Why that fails:

- Once Safeguard is active, repeated status attempts do not improve the route.
  Worse, they can hand Karen or Blaine the exact turns needed for Dragon Dance,
  sun, Spikes, Agility, or priority cleanup.

Better policy:

- If status is the route, use it before Safeguard or force the Safeguard user
  to choose between prevention and taking major damage.
- If Safeguard is already up, count the prevention turns and use direct
  pressure, hazards, phazing, setup, or item denial instead.
- If the boss is likely to use Safeguard because the player revealed sleep or
  status, exploit that expected non-damaging turn with a converter entry.

Answer-changing information:

- Safeguard already expired or never set makes status live again.
- A direct KO on the Safeguard user may be better than preserving status.
- If the boss has Full Heal behind Safeguard, status needs two layers of
  justification: prevention window and cure item.

## Rest Users: Status As A Forced-Timing Tool

Local evidence:

- Koga Muk, Misty Quagsire, Sabrina Hypno, Will Slowbro, Pryce Slowking, and
  Red Snorlax all use Rest in local route sheets or trainer data.

Bad default:

- "Status the Rest user and then wait."

Why that fails:

- Rest removes the status and restores HP. Status is good only if it forces Rest
  at a time the user can convert: setup, phaze, PP pressure, safe entry, or a
  KO before wake/Sleep Talk stabilizes.

Better policy:

- Use status to force Rest only when the sleep turns are exploitable.
- If the Rest user has Sleep Talk, price the branches where it attacks,
  phazes, boosts, or calls Rest again.
- If the player cannot punish Rest, direct pressure or preserving a later
  status move may be better than starting a clock the boss resets for free.

Answer-changing information:

- Sleep Talk present lowers the value of "forced Rest" as a free turn.
- Low Rest PP or hazard re-entry tax makes forcing Rest more valuable.
- A setup user or breaker with clean entry turns Rest from reset into an
  opening.

## Extracted Lesson

Status progress is not the same as status landing. In boss fights, the useful
unit is the reset map: what can cure or prevent the status, whether that reset
is punishable, and whether the status creates route value before it disappears.
