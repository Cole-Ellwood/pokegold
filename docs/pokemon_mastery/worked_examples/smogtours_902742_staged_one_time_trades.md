# Worked Example: Staged One-Time Trades

Source:

- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-902742.log
- Review: `../reviews/2026-05-13_smogtours-gen2ou-902742.md`
- GSC Explosion guide:
  https://www.smogon.com/gs/articles/guide_to_explosion
- GSC Thief discussion:
  https://www.smogon.com/forums/threads/thief.3543261/

## Pattern

Public state:

```text
One-time trade user:
Target:
Route opened by trade:
Route closed by losing user:
Blockers to trade:
Support job still live:
Follow-up after trade:
```

Decision:

```text
Spend the one-time trade only when:
  the target blocks a named route;
  the user has finished its higher-value support job;
  the immunity / protection / phaze / survival branch is priced;
  and the next Pokemon can convert the trade.
```

## Replay Shape

Position:

```text
Misdreavus is the Ghost and has already lost Leftovers.
Misdreavus is later removed by Exeggutor.
Skarmory is removed by Raikou.
Cloyster is low and can Explode on Forretress.
Exeggutor still has Explosion for sleeping Snorlax.
```

Bad advice:

```text
Cloyster is low, so use Explosion as soon as a bulky target appears.
```

Better posture:

```text
Keep the one-time trade until the blocker map is clear. Misdreavus must be
removed or disabled, the phazer/support pieces must be priced, and the target
must be the piece whose removal lets the remaining route finish.
```

Follow-up:

```text
Remove Misdreavus -> remove Skarmory -> Cloyster Explosion on Forretress ->
Exeggutor Explosion on Snorlax.
```

Why the order matters:

- If Explosion is spent before the Ghost problem is solved, the route can fail
  outright or hit the wrong target.
- If Cloyster trades before its hazard/status job is spent, the team may lose a
  needed support resource.
- If Exeggutor trades before Misdreavus is gone, the endgame can collapse into
  an avoidable immunity branch.

## Boss Transfer

Use this pattern when a boss fight includes Explosion, Self-Destruct, Destiny
Bond, Focus Band, Perish Song, or a planned controlled sack.

Ask:

```text
What blocks the trade?
What does the user still do if preserved?
What route opens after the trade?
Which Pokemon converts next?
What local mechanic could make the trade fail?
```

Local transfer limits:

```text
Normal/Ghost immunity, Protect, Substitute, Endure, Focus Band, passive type
abilities, priority, and move execution order must be checked in the romhack
before treating a one-time trade as guaranteed.
```

## Failure Signs

- The answer says "boom because low HP."
- The target is valuable but not the actual blocker.
- A Ghost, protection state, survival item, or faster KO branch is still live
  and unpriced.
- The user still has a spin, phaze, status, sleep, hazard, or defensive job
  that the team cannot replace.
- The follow-up after the trade is "pressure" instead of a concrete converter
  or forced line.

## Extracted Rule

```text
A one-time trade is an endgame route only after its blockers, lost roles, and
converter follow-up are all named.
```
