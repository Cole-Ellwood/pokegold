# Worked Example: Red Late Weather Support Job Stress Test

Purpose: apply the late-support-job lesson from
`smogtours_gen3ou_805152_late_support_job.md` to Red's final-boss weather
routes. This is a preservation drill, not a claim that weather control is
always the correct Red plan.

Local evidence:

- Red route map: `../boss_route_maps/red_turn1_route_sheet.md`.
- Red pre-battle route sheet: `red_pre_battle_route_sheet.md`.
- Red sequential converter drill:
  `red_sequential_converter_pressure_stress_test.md`.
- Red 30-turn ledger drill: `red_30_turn_final_boss_ledger_drill.md`.
- Roster source: `data/trainers/parties.asm`, `RedGroup`.
- Weather, Morning Sun / Synthesis, SolarBeam, priority, Rest / Sleep Talk,
  Light Ball, and Mirror Coat references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert transfer source:

- Late support job review:
  `../reviews/2026-05-13_smogtours-gen3ou-805152.md`.
- Smogon DPP Sunny Day material:
  <https://www.smogon.com/dp/articles/sunny_day_guide>.
- Smogon DPP Rain Offense material:
  <https://www.smogon.com/dp/articles/rain_offense>.

## Pattern Being Tested

Bad shortcut:

```text
This support Pokemon is low or already did its broad job, so sacrifice it.
```

Better policy:

```text
Low HP narrows a support Pokemon's job. It does not erase the last job until
the receiver, trigger, and route are all gone.
```

Against Red, the last support job may be a weather reset, a weather denial, a
screen turn, a phaze/Haze turn, a safe-entry sacrifice, a priority-range buffer,
or one final status / damage action that lets the real answer survive Venusaur,
Charizard, Snorlax, Espeon, Blastoise, or surviving Pikachu.

Weather sources are useful because manual weather is a finite clock. The exact
later-generation ability details are not portable, but the planning principle
is: a setter or replenisher matters only when the next five turns have a named
beneficiary and a path to conversion.

## Stress-Test State

Use this public-state prompt, then substitute the user's real team:

```text
Red route just appeared or is about to appear:
  Venusaur Sunny Day / Synthesis / SolarBeam
  Charizard Sunny Day / Flamethrower / SolarBeam
  Espeon Reflect / Morning Sun / Calm Mind
  Snorlax Curse / Rest / Sleep Talk
  Blastoise Mirror Coat / mixed coverage
  Pikachu ExtremeSpeed if still alive

Our low-HP or nearly spent support piece:
  current HP:
  status:
  remaining PP:
  can enter again after hazards / weather / priority:
  original broad role:
  possible final narrow job:

Receiver or beneficiary:
  piece that improves if the support job happens

Trigger:
  sun reset / sun denial / screen / phaze / Haze / sacrifice entry / status /
  forced recovery / priority buffer / Mirror Coat avoidance

Question:
  Is this support piece truly expendable, or does one remaining job decide the
  next Red route?
```

## Required Questions

Before sacrificing, preserving, or spending a low-HP support piece, fill this:

```text
Original role:
  what broad job did this Pokemon once have?

Current narrow job:
  what exactly can it still do once?

Receiver:
  which teammate or route benefits immediately?

Boss route denied:
  which Red route becomes worse if this job happens?

Boss route opened:
  which Red route becomes better if this piece is sacrificed too early?

Trigger timing:
  can the support move happen before Red's payoff move?

Entry proof:
  can the support piece still enter or act after hazards, status, priority, and
  active weather?

Weather proof:
  if the job involves sun, what changes in Fire damage, Water damage,
  SolarBeam, Synthesis, or Morning Sun?

Answer flip:
  what evidence would make preserving, spending now, or sacrificing correct?
```

## Move-Class Arbitration

Preserving the support piece rises when:

- it can reset, deny, or burn Red's sun window at the exact turn Venusaur or
  Charizard would convert;
- it can set a screen, phaze, Haze, or status once before Espeon or Snorlax
  becomes unmanageable;
- it creates safe entry for the actual Snorlax, Espeon, sun, Blastoise, or
  Pikachu-priority answer;
- its receiver is alive and the support action immediately improves a concrete
  route;
- sacrificing it only gains chip that does not change a threshold.

Spending the support action now rises when:

- the trigger and receiver are both live this turn;
- waiting loses the entry because of hazards, poison, priority, weather,
  screen turns, or Red's next forced attack;
- Red's next move would make the support job impossible;
- the support move converts immediately rather than merely looking tidy.

Sacrificing the support piece rises when:

- the receiver is gone or no longer needs the job;
- the support action is blocked by public state;
- the support piece cannot enter or act before fainting;
- the sacrifice creates a clean entry for a more important answer;
- the remaining answer map still covers every live Red route.

Preserving falls when:

- the player preserves the piece after the beneficiary is dead;
- the support job requires weather, screen, or status mechanics that are not
  locally true;
- Red gets a free Calm Mind, Curse, Sunny Day, Mirror Coat punish, or
  ExtremeSpeed endgame while the player waits for a perfect support turn.

## Red-Specific Cases

### Low-HP Weather Denier Into Venusaur Or Charizard

If the user's Water, Rock, Fire-resistant, or Grass-resistant answer works only
in clear weather, a low-HP support piece may still matter if it can prevent or
stall the sun turn. The question is not "can it beat Charizard or Venusaur?"
The question is whether one action keeps the real answer valid.

Failure sign:

- The advice sacks the weather denier because it cannot win the matchup alone,
  then the Water answer loses to sun-boosted Fire pressure or one-turn
  SolarBeam.

Correct pressure:

- Preserve it only if the denial action happens before Sunny Day converts and
  the real answer can use the resulting turn.

### Low-HP Weather Setter For A Final Attacker

If the user's team has its own weather route, the setter may be low but not
spent. It is useful only if the next five turns have a named receiver and Red
cannot take the setup turn to start a stronger route.

Failure sign:

- The advice uses weather because "weather helps us" without naming the
  receiver, Red's immediate punish, or the exact damage / recovery / charge-turn
  change.

Correct pressure:

- Set weather when it creates an immediate KO threshold, protects the receiver
  from Red's weather, or changes SolarBeam / recovery / Fire / Water math in a
  way the receiver can cash out before Red's next converter enters.

### Low-HP Screen Or Control Support Into Espeon / Snorlax

Reflect, Haze, phazing, status, Encore-style control, or one safe-entry
sacrifice can still be decisive if Espeon or Snorlax is about to inherit the
board. The support piece is expendable only after those routes are covered by
someone else or no longer live.

Failure sign:

- The advice spends a low-HP controller on damage, then Espeon gets Calm Mind
  or Snorlax gets Curse / RestTalk with the real answer already exposed.

Correct pressure:

- Use or preserve the final control turn if it denies the route before the
  bulky setup piece becomes self-sustaining.

### Low-HP Pivot Into Blastoise

Blastoise punishes special-only stabilization with Mirror Coat. A low-HP pivot
may still be valuable if it creates entry for physical or mixed pressure, or if
its sacrifice prevents the important special attacker from eating Mirror Coat.

Failure sign:

- The advice calls the pivot "dead weight" and then uses the real special
  attacker into Mirror Coat risk.

Correct pressure:

- Spend the pivot if it creates the correct damage category, safe entry, or
  Mirror Coat avoidance for the actual Blastoise answer.

### Any Low-HP Piece Into Surviving Pikachu

Pikachu's ExtremeSpeed is not boosted by Light Ball locally, but priority still
decides endgames. A low-HP support piece may be needed to keep the cleaner out
of priority range or to remove Pikachu before the final route begins.

Failure sign:

- The advice says the final route is won without checking whether the receiver
  ends below ExtremeSpeed range.

Correct pressure:

- Preserve or spend the support piece according to whether it changes the final
  priority threshold.

## Example Verdict Shape

```text
Recommendation:
  preserve support / spend support now / sacrifice support / abandon support
  route

Why:
  The piece's original role was [old job], but its current narrow job is
  [one action]. That action benefits [receiver] by denying or improving [route].

Worst plausible branch:
  if we sacrifice or preserve incorrectly, Red gets [Sunny Day / Calm Mind /
  Curse / Mirror Coat / ExtremeSpeed] and our [answer] no longer performs its
  job.

What changes the answer:
  support HP and entry proof, sun turns, Reflect turns, Snorlax boosts and Rest
  state, Espeon boosts, Blastoise Mirror Coat branch, Pikachu survival, receiver
  HP, and local type/passive/weather/damage evidence.
```

## Boss-Battle Transfer

This stress test generalizes to other bosses:

- Misty: low-HP rain support may still reset or deny the last Water route.
- Blaine and Karen: one weather-denial or weather-reset action can decide
  whether a Fire or Houndoom route converts.
- Sabrina and Bugsy: a nearly spent screen / Encore / Baton Pass support piece
  may still deliver one receiver.
- Will, Koga, Janine, Pryce, or Brock: a low-HP spinner, phazer, or Explosion
  user may still own the final support job.

The action test is always:

```text
If this support piece acts one more time, what route becomes better?
If it dies now, which Red route gets easier?
Can the receiver convert before Red's next route inherits the board?
```

## Extracted Lesson

The late-support-job lesson becomes Red policy: do not decide expendability
from HP, old role, or whether the support Pokemon can win a matchup by itself.
Decide from the last remaining job, its receiver, and the Red route it denies.
In a final-boss fight with sun, screens, RestTalk, Mirror Coat, and priority,
one narrow support action can be the difference between a clean conversion and
the next Red route taking over.
