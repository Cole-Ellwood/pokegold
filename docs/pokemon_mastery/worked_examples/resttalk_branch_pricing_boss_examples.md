# Worked Example: RestTalk Branch Pricing

Purpose: avoid treating Rest, Sleep Talk, or sleep turns as generic free time.

Expert sources:

- Smogon Introduction to Status in GSC:
  https://www.smogon.com/gs/articles/status
- Smogon GSC Mechanics:
  https://www.smogon.com/forums/threads/gsc-mechanics.3542417/
- Smogon Playing with Spikes in GSC:
  https://www.smogon.com/gs/articles/gsc_spikes
- Smogon Moving On - Competitive moves that were left behind:
  https://www.smogon.com/articles/moves-left-behind

Local evidence:

- `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- `engine/battle/move_effects/sleep_talk.asm`
- `engine/battle/effect_commands.asm`
- `constants/battle_constants.asm`

## Pattern

Public state:

```text
Rest user:
Has Sleep Talk:
Current HP:
Current status:
Rest / Sleep Talk PP:
Hazards:
Our converter:
Opponent punish during sleep turns:
Worst Sleep Talk branch:
Route after Rest resolves:
```

Decision:

```text
Punish Rest only if:
  the sleeping turns create forced progress;
  Sleep Talk branches are priced;
  and the converter survives the reset if Sleep Talk calls Rest.
```

## Replay Shape: smogtours-gen2ou-905952

Observed:

- A Real Jester's Snorlax used RestTalk Surf as the final stabilizer.
- underlying froze that Snorlax on turn 54, but later lost Snorlax to
  Exeggutor Explosion and had to finish with paralyzed Gengar alone.
- When Snorlax eventually used Rest on turn 75, the apparent freeze route
  became a Rest cycle. Gengar had to beat the full reset through paralysis.

Lesson:

- A temporary disable or low-HP state is not a route unless the converter is
  preserved until recovery is denied. If the target has RestTalk, the branch
  "Sleep Talk calls Rest" must be treated as legal progress denial, not as
  surprising bad luck.

## Red Shape

Boss anchor:

- Snorlax @ Leftovers:
  Curse / Sleep Talk / Rest / Body Slam

Bad advice:

- "Force Snorlax to Rest, then set up freely."

Better advice:

- Force Rest only if the next turns can deny the CurseLax route despite Sleep
  Talk. The follow-up must be phazing/Haze, strong damage, Explosion/sacrifice,
  PP pressure, or a setup line that still survives Body Slam or Sleep Talk
  branches.

Answer-changing information:

- Snorlax's current boosts.
- Whether Body Slam paralysis would break the converter.
- Whether the answer has enough HP/PP to continue after Sleep Talk calls Rest.
- Whether hazards or phazing make the Rest cycle worse for Red.

## Janine Shape

Boss anchor:

- Muk @ Rocky Helmet:
  Flamethrower / Sludge Bomb / Sleep Talk / Rest

Bad advice:

- "Muk is asleep, so contact attacks are safe."

Better advice:

- Price Sleep Talk into Sludge Bomb, Flamethrower, or Rest, plus Rocky Helmet on
  contact. If the player's physical route loses too much HP to contact plus a
  Sleep Talk attack, the correct line may be pivoting, special damage, phazing,
  Haze, or forcing Muk to spend Rest PP while preserving the physical answer.

Answer-changing information:

- Whether the player's attack makes contact.
- Whether poison or burn would break the intended route.
- Whether Muk is boosted by Curse in the current state.
- Whether the team can convert the two sleep turns before RestTalk resets.

## Rest-Only Anchor Shape

Examples:

- Misty Quagsire: Curse / Earthquake / Surf / Rest
- Will Slowbro: Amnesia / Surf / Psychic / Rest
- Sabrina Hypno: Seismic Toss / Rest / Thunder Wave / Psychic

Rule:

- Rest-only users have a more punishable sleep window than RestTalk users, but
  the window still needs a converter. If the sleeping turns are spent on weak
  chip, wrong setup, or switching that gives the boss a safe wake turn, forcing
  Rest did not actually convert.

Answer-changing information:

- Whether the Rest-only user can switch out.
- Whether the player has hazards, phazing, setup, or a forced KO before wake.
- Whether the boss can wake into Thunder Wave, Haze, phazing, or immediate KO.
- Whether local AI or roster structure gives the boss a safe pivot during Rest.

## Transfer Rule

Do not ask only:

```text
Can we force Rest?
```

Ask:

```text
After Rest, who owns the next two turns?
If Sleep Talk can act, what are its legal branches?
If the damage race resets to full HP, what concrete route remains?
```

For live boss advice, the recommended move should name the Rest-cycle payoff:

```text
force Rest -> set hazard / phaze / Haze / boost / explode / safe entry / PP win
```

If it cannot name the payoff, forcing Rest is probably just delaying the fight.
