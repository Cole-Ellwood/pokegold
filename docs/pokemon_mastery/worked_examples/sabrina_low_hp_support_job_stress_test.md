# Worked Example: Sabrina Low-HP Support Job Stress Test

Purpose: stress-test the ADV replay lesson from
`smogtours_gen3ou_805152_late_support_job.md` against a local Sabrina route.
This is not a solved turn. It is a decision pattern for recognizing when a
low-HP support Pokemon still has one route-changing job left.

Local evidence:

- Sabrina route map: `../boss_route_maps/sabrina_turn1_route_sheet.md`.
- Sabrina pre-battle route sheet: `sabrina_pre_battle_route_sheet.md`.
- Sabrina 30-turn drill: `sabrina_30_turn_ledger_drill.md`.
- Roster source: `data/trainers/parties.asm`.
- Screens: `engine/battle/effect_commands.asm` and `engine/battle/core.asm`.
- Encore: `engine/battle/move_effects/encore.asm`.
- Baton Pass: `engine/battle/move_effects/baton_pass.asm`.
- Choice Specs and Morning Sun:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.

Expert transfer source:

- ADV replay review: `../reviews/2026-05-13_smogtours-gen3ou-805152.md`.
- Smogon ADV Baton Pass material:
  <https://www.smogon.com/rs/articles/baton_pass>.
- Smogon DPP Baton Pass material:
  <https://www.smogon.com/dp/articles/baton_pass_chains>.
- Smogon move-restriction material:
  <https://www.smogon.com/dp/articles/move_restrictions>.

## Pattern Being Tested

Bad shortcut:

```text
The support Pokemon is low, so it is basically spent.
```

Better policy:

```text
The support Pokemon's broad role may be gone, but one remaining action can
still decide the next route. Name that job before calling it expendable.
```

Against Sabrina, the boss-side version is especially dangerous. Low HP does not
make Mr. Mime harmless if it can still set the missing screen or Encore a setup,
recovery, status, or other low-value move. Low HP does not make Espeon harmless
if Baton Pass can reset position. Low HP does not make Hypno harmless if
Thunder Wave or Rest changes the endgame.

## Stress-Test State

Use this as a public-state prompt, then substitute the user's real team when
available:

```text
Sabrina active:
  Mr. Mime at low HP
  known moves: Light Screen / Reflect / Encore / Psychic

Sabrina bench:
  Jynx, Espeon, Alakazam, Hypno still alive

Board:
  one screen may already be active or recently expired
  the player's active Pokemon can either attack, setup, recover, status, or
  switch

Player concern:
  Alakazam, Jynx, or Hypno still has a live route if given protected entry
```

Do not decide from HP alone. Decide from the remaining support job.

## Required Questions

Before advising a move, fill this:

```text
Support piece:
  Mr. Mime / Espeon / Hypno / player support piece

Original broad role:
  screen setter / Baton Pass pivot / bulky status anchor / player support

Current narrow job:
  last screen / Encore trap / Baton Pass escape / Thunder Wave / Rest reset /
  one safe entry / one final status or weather move

Beneficiary:
  which Sabrina or player Pokemon improves if the job happens

Trigger:
  what has to be true for the job to matter this turn

Can it still act:
  yes / no / only if Speed, priority, accuracy, or damage cooperates

Route opened:
  what becomes easier after the job

Route lost if ignored:
  what wins for the opponent if the support piece survives one more turn
```

## Move-Class Arbitration

Attack to remove the support piece rises when:

- the support piece can still use a job that protects or delivers a stronger
  route;
- damage actually removes it before the job happens;
- the attacking piece does not expose an irreplaceable answer afterward;
- the next Sabrina route is worse than the cost of attacking now.

Switch rises when:

- the current active cannot stop the support job and staying only gives the
  boss a better clock;
- the switch-in preserves the answer to the beneficiary, not just to the
  current low-HP support Pokemon;
- the switch does not hand Encore, screen turns, sleep, or Choice-lock pressure
  a better target.

Setup, recovery, hazards, or status fall when:

- Mr. Mime can Encore the move;
- a missing screen would let Alakazam, Jynx, Espeon, or Hypno enter safely;
- the move does not stop the narrow support job;
- the active support clock expires in Sabrina's favor.

Sacrifice rises only when:

- the sacrificed Pokemon has no remaining job;
- the sacrifice creates safe entry to the piece that denies the beneficiary;
- the support piece's last job is either already blocked or no longer matters.

## Example Verdict Shape

```text
Recommendation:
  attack / switch / support / setup / sacrifice

Why:
  Mr. Mime is low, but its remaining job is [Light Screen / Reflect / Encore].
  That job benefits [Jynx / Espeon / Alakazam / Hypno] by [route].

Worst plausible branch:
  if we do not deny the job, Sabrina gets [screen / lock / pass / status] and
  our [answer] no longer performs its later role.

What changes the answer:
  exact KO range, Speed order, current screen turns, Encore legality, player
  active's last move, and whether the beneficiary is still alive.
```

## Sabrina-Specific Failure Signs

- "Mr. Mime is almost dead, so set up."
- "Encore is annoying but not decisive."
- "A screen is only defensive, so we can ignore it."
- "Espeon is low, so Baton Pass is harmless."
- "Hypno is slow, so Thunder Wave does not matter."
- No one names which Sabrina Pokemon receives the benefit.

## Boss-Battle Transfer

This stress test generalizes to other bosses:

- Bugsy: low-HP Ledian may still have one Reflect, Encore, or Baton Pass job.
- Misty: low-HP Politoed or Lapras may still reset rain for the next Water
  route.
- Erika or Red: low-HP sun support may still change SolarBeam, Synthesis, or
  Fire damage timing.
- Will, Koga, Janine, or Pryce: low-HP spinner, spinblocker, phazer, or
  Explosion user may still decide one final hazard or entry route.

The action test is always the same: if the support Pokemon acts once more, what
route becomes better, and can we afford that route?

## Extracted Lesson

The ADV replay lesson becomes a Sabrina policy rule: do not mark support as
spent by HP. Mark it spent only after its last meaningful job is impossible,
blocked, or no longer connected to a live route. If that last job still enables
Jynx sleep pressure, Espeon position reset, Choice Specs Alakazam entry, or
Hypno paralysis/Rest control, it must be denied or explicitly priced.
