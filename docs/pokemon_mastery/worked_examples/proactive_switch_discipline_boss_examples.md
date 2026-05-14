# Worked Example: Proactive Switch Discipline

Purpose: distinguish a route-improving proactive switch from a vague momentum
play.

Source basis:

- Smogon Introduction to Prediction:
  https://www.smogon.com/smog/issue1/introduction_to_prediction
- Smogon Introduction to Competitive GSC:
  https://www.smogon.com/smog/issue28/gsc
- Smogon double-switch discussion:
  https://www.smogon.com/forums/threads/fundamental-tactic-the-double-switch.3495451/

## Pattern

Public state:

```text
Current active matchup:
Why opponent may switch or pivot:
Most likely incoming route piece:
Our proactive switch:
What it gains if right:
Wrong branch if opponent stays:
Wrong branch if opponent chooses a different pivot:
Irreplaceable piece risked:
Next move if it works:
```

Decision:

```text
Proactive switch is legal only if:
  the opponent's switch/pivot is strongly incentivized by public state;
  the incoming piece is identifiable enough to punish;
  the new active improves a named route immediately;
  and the wrong branch does not lose an irreplaceable answer.
```

## Will Shape: Houndoom And Pursuit Pressure

Boss route:

- Will can use Houndoom to punish Psychic- or Ghost-leaning pivots with Crunch,
  Flamethrower, Sunny Day, and Pursuit.

Bad proactive-switch logic:

- "Houndoom is in, so switch the Psychic answer out." This can walk directly
  into Pursuit or give Sunny Day / Flamethrower a free route.

Better question:

- Is Houndoom threatening the stay line, the switch line, or both? If staying
  gets KOed but switching gets trapped by Pursuit, the correct play may be a
  controlled sack, direct damage, status, or a pivot that does not lose to both
  branches.

Legal proactive switch:

- Switching rises only when the incoming piece clearly survives the stay branch
  and the Pursuit branch, then immediately forces Houndoom out or removes its
  sun route.

Answer-changing information:

- Whether Pursuit is revealed or source-known.
- Whether Sunny Day is active or Houndoom can safely set it.
- Whether the current active is still needed for Alakazam, Slowbro, or Xatu.
- Whether the proposed pivot survives Charcoal Flamethrower or Crunch by local
  damage evidence.

## Erika Shape: Jumpluff Encore And Victreebel

Boss route:

- Jumpluff can turn passive moves into Encore traps, while Victreebel can punish
  the wrong preserved answer with sleep or Explosion pressure.

Bad proactive-switch logic:

- "She will switch to Victreebel, so bring the Victreebel answer now." If
  Jumpluff stays and Encores, sleeps, or pivots differently, the answer may be
  crippled before Victreebel appears.

Legal proactive switch:

- It becomes reasonable only if public state makes Jumpluff staying low-value:
  it is in KO range, cannot safely click Encore, or the boss route clearly
  needs Victreebel now. The switch-in must also handle the stay branch.

Answer-changing information:

- Jumpluff HP, Encore target, and sleep/status state.
- Whether Victreebel's sleep or Explosion route is still live.
- Whether the proposed pivot is the only answer to another Erika piece.
- Local Grass/Flying and passive evidence if the switch depends on damage
  typing.

## Human-Ladder Transfer Rule

Competitive double-switching teaches this abstract principle:

```text
When the opponent is strongly incentivized to enter a specific answer, you may
skip the obvious attack and enter the piece that beats that answer.
```

For Gym Leader Lab, translate it like this:

```text
Do not outguess the boss for style. Use roster, public state, route necessity,
and validated AI traces to decide whether the boss is likely to change state.
If that evidence is weak, cover the worst plausible branch instead.
```
