# Quick Test 002 - Replay Micro-Probe - 2026-05-14

Status: frozen-answer replay micro-probe.

Source: Smogon forum post in GSC OU Winter Seasonal #8 Round 4 linking
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912130`.

Contamination control:

- Raw replay log was downloaded to a temporary local file.
- A parser exposed only public state before turns 10, 20, 30, 40, and 50.
- The oracle file with p1's actual choices was generated separately and not
  opened before the answers below were written.
- This is not a sealed final exam. Actual replay moves are a weak oracle:
  players can choose suboptimal lines, and this prompt omits p1's unrevealed
  own moves even though a real player would know them.

## Frozen Answers

### Q1 - Before Turn 10

Public state: p1 Moltres 96% vs p2 Rhydon 94%. Both sides have Spikes. p1 has
seen Cloyster, Golem, sleeping Snorlax, Zapdos, and Moltres. p2 has shown
Cloyster, Meganium, Rhydon, Snorlax, and Zapdos.

Answer: switch to Cloyster.

Reason: Rhydon is the direct anti-Moltres answer and threatens Rock Slide, so
staying only makes sense if p1 knows Moltres has a Rhydon-punishing hidden move
such as Hidden Power Grass. With only public revealed moves, Cloyster is the
cleanest Rhydon answer and immediately threatens Surf or Toxic while preserving
Moltres as the Meganium breaker.

Alternatives: hidden HP Grass if p1's private moveset supports it; Golem only
if the plan is to trade or scout and Cloyster is too important.

Worst branch: Cloyster comes in as p2 doubles to Meganium or Snorlax, giving up
tempo and another Spikes hit later.

### Q2 - Before Turn 20

Public state: p1 Cloyster 94% vs p2 Snorlax 94%. Both sides have Spikes. p2
side also has Light Screen. p1 Exeggutor is down, p1 Snorlax is asleep, and p2
Snorlax has shown Lovely Kiss.

Answer: Toxic.

Reason: p2 Snorlax is the central long-game piece and Sleep Clause makes
Lovely Kiss less threatening while p1 Snorlax remains asleep. Toxic turns the
current free contact into a clock and helps Spikes matter.

Alternatives: Surf if p1 needs chip through Light Screen less than it needs the
poison clock; switch Golem only if expecting a passive Snorlax turn and needing
to threaten Explosion or Earthquake.

Worst branch: p2 switches the Snorlax into a status absorber or a better Toxic
target was needed later, but letting healthy Snorlax sit unclocked is worse.

### Q3 - Before Turn 30

Public state: p1 Zapdos 85% vs p2 Meganium 62%. Both sides have Spikes. p1
Moltres is still 96%, p1 Exeggutor is gone, p2 Zapdos is asleep at 31%, and p2
Meganium has shown Light Screen, Razor Leaf, and Synthesis.

Answer: switch to Moltres.

Reason: Meganium is a bad Zapdos damage target unless p1 privately knows Hidden
Power type gives reliable pressure. Moltres is the preserved converter against
Meganium and forces p2 to respect Fire Blast.

Alternatives: Hidden Power if p1 knows it is the correct type and p2's Rhydon
or Houndoom switch does not punish too hard; Thunder only if paralysis/chip
changes a concrete endgame.

Worst branch: p2 doubles to Rhydon or Houndoom as Moltres enters, but that is
still a priced branch and preserves Zapdos.

### Q4 - Before Turn 40

Public state: p1 Golem 18% vs p2 Rhydon 57%. p1 side has no Spikes; p2 side
has Spikes. p1 Cloyster is poisoned at 94%, p1 Zapdos is asleep at 100%, and
p2 Rhydon has shown Earthquake and Rock Slide.

Answer: switch to Cloyster unless p1 privately has Explosion and it KOs.

Reason: low-HP Golem does not beat Rhydon straight up, but it already cleared
p1's side and can be preserved as death-fodder or possible trade material.
Cloyster is the clean public Rhydon answer and threatens Surf.

Alternatives: Explosion if known and the damage converts; Earthquake only if
staying avoids a worse branch and p1 accepts losing Golem.

Worst branch: p2 doubles to Meganium or Snorlax on Cloyster, but Rhydon getting
a free hit into Golem is the more immediate route-losing branch.

### Q5 - Before Turn 50

Public state: p1 Snorlax 94% asleep vs p2 Rhydon 69% at +1 Attack, +1 Defense,
-1 Speed. Both sides have Spikes. p1 has only asleep Snorlax, asleep Zapdos
49%, and healthy Moltres 96% left; p1 Cloyster, Golem, and Exeggutor are down.

Answer: stay with Snorlax and attack Rhydon if p1 has Earthquake; otherwise
Curse.

Reason: the bench cannot take over this turn. Zapdos and Moltres are both bad
into +1 Rhydon with Spikes up, so Snorlax must be the emergency stabilizer.
If Earthquake exists, it pressures the setup threat immediately; if not, Curse
is the only way to avoid being overrun by a boosted Rhydon while waiting for a
wake.

Alternatives: switch Zapdos only on a desperate Earthquake read, but asleep
Zapdos at 49% plus Spikes is too fragile into Rock Slide. Moltres is not a
serious switch.

Worst branch: Snorlax stays asleep while Rhydon attacks or stacks another
Curse, leaving p1 with no stable Rhydon answer.

## Oracle And Scoring

Oracle after answer freeze:

| Question | My answer | p1 actual choice | Grade |
| --- | --- | --- | --- |
| Q1 | Switch Cloyster | Switch Exeggutor | Partial / prompt-flawed |
| Q2 | Toxic | Toxic | Match |
| Q3 | Switch Moltres, but HP if correct type | Hidden Power | Acceptable conditional match |
| Q4 | Switch Cloyster unless Explosion KOs | Earthquake | Miss |
| Q5 | Stay Snorlax; Earthquake if known, otherwise Curse | No move line; Snorlax stayed asleep | Unscored oracle failure |

Rough score: uncounted 82.0.

Why uncounted:

- The prompt omitted p1's unrevealed own team and own move choices. That is not
  the intended information model. A player-side advisor knows its own team and
  moves even without Team Preview.
- Actual replay moves are useful but not a perfect oracle. They show what a
  strong player did, not a proof that every alternative is wrong.
- Q5 has no action oracle because Pokemon Showdown logs only `cant` when the
  sleeping Pokemon fails to move.

Errors / lessons:

- Q1: not a reliable miss. Exeggutor was not included in the prompt even though
  p1 knew it existed. Future replay prompts must include the advised side's
  full known team and full own moves if available.
- Q2: good. Toxic into Snorlax remained correct even when p2 switched Cloyster;
  the move still punished a route-relevant support piece.
- Q3: good calibration. The correct line depended on Hidden Power type. The
  prompt hid the type, so the answer should preserve the conditional rather
  than pretend certainty.
- Q4: real decision miss. I overweighted the immediate Rhydon-vs-Golem
  matchup and underweighted p2's incentive to preserve Rhydon by pivoting a
  poisoned Cloyster into the obvious Ground move or Explosion slot. The useful
  lesson is: when a low-HP piece still threatens a high-value active with a
  forced-progress move, first price the opponent's preservation switch before
  choosing a defensive pivot.

Next measurement fix:

Build the next quick-test prompt from either fully specified local scenarios or
a replay parser that includes the advised side's known full team and own move
sets. Exclude asleep `cant` turns, forced replacement turns, and turns where the
oracle cannot recover the player's chosen action.
