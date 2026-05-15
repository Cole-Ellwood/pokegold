# Hazard Ownership Review 001 - gen2ou-2544443857 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2544443857-5tvdxa7m0m3feng39gb3a5lo7368kwypw`

Parent transfer:
`quick_tests/three_check_transfer_001_gen2ou-2544443857_2026-05-14.md`

Mode: targeted expert replay review after reveal. This is not a fresh score.

Selected action:
Review turns 10-13 because the fresh packet's main miss was hazard ownership:
Golem Rapid Spin as progress, p2 Cloyster resetting Spikes, and p2 Zapdos
using coverage into the named Raikou receiver.

## Turn 10 - Golem Rapid Spin Was Progress

Public state:
p1 Golem was at 94% against p2 Snorlax at 79%. Spikes were on both sides. p1
had revealed Cloyster with Spikes and Toxic; p2 had a poisoned Cloyster with
Spikes. Golem had not yet revealed Rapid Spin.

Actual:
p2 switched Cloyster. p1 Golem used Rapid Spin, clearing p1's Spikes.

Review:
I treated Golem as only an Earthquake/Rock Slide/Explosion piece. That missed
the board shape: p1 had already landed Toxic on p2 Cloyster, so clearing p1's
Spikes while p2's side stayed spiked improved the whole entry map. Even though
Rapid Spin was unrevealed, the correct recommendation should have named "clear
our Spikes if Golem has Spin" before generic attacking.

Reusable rule:
When the active is a plausible spinner and only our side is suffering from the
next switch tax, price Spin as a route-converting move before attacking.

## Turn 11 - Spin Does Not Lock The Hazard Loop

Public state:
p1 Golem had just cleared p1's Spikes. p2 Cloyster was poisoned at 78% and was
active. p1 switched back to Cloyster.

Actual:
p2 Cloyster used Spikes, restoring hazards on p1's side.

Review:
I tunnelled on Rapid Spin because p2 had a poisoned Cloyster and Spikes on its
own side. But after p1 cleared hazards, p2's immediate route job was simpler:
reset Spikes while Cloyster still had the entry and HP to do it. The poisoned
setter was not done yet.

Reusable rule:
After Spin succeeds, immediately ask whether the opposing setter is active,
alive, and free to reset Spikes. If yes, resetting hazards may beat spinning,
Surfing, or preserving.

## Turn 12 - Zapdos As Surf Receiver

Public state:
Both sides had Spikes again. p1 Cloyster was healthy and p2 Cloyster was
poisoned at 72%.

Actual:
p2 switched Zapdos into Surf, taking chip but preserving poisoned Cloyster.

Review:
I stayed inside the Cloyster mirror and did not name the aerial special owner.
Zapdos did not care about Spikes on entry and could pressure Cloyster next
turn. The switch was not a perfect answer, but it preserved the poisoned
spinner/setter and changed the next board.

Reusable rule:
In Cloyster mirrors, name non-grounded receivers before assuming the next move
is Spin, Surf, or Explosion. A flyer that avoids Spikes can be the next-board
owner even if it takes Surf chip.

## Turn 13 - Coverage Into Named Receiver

Public state:
p1 Cloyster was at 99% against p2 Zapdos at 63%. p1 had a paralyzed Raikou at
80% and a Golem at 99%. Zapdos had revealed Hidden Power.

Actual:
p1 switched Raikou. p2 Zapdos used Hidden Power and heavily chipped Raikou.

Review:
I named Raikou as the obvious Zapdos owner but still made Thunder the top
choice for Zapdos. That repeated the branch-action problem: after naming the
receiver, choose the action that hits the receiver. Hidden Power was already
revealed and was the move that improved through the expected Raikou handoff.

Reusable rule:
When the expected receiver is already named and revealed coverage hits that
receiver, coverage must compete for top action even if the active target is
weak to the STAB move.

## Review Decision

No constructed probe is needed yet. The next countable rep should be another
fresh replay transfer with the hazard ownership check active:

1. If a plausible spinner is active, ask what side's Spikes it can clear now.
2. After Spin succeeds, ask whether the opposing setter can immediately reset.
3. In Cloyster mirrors, name flyer/special receivers before assuming mirror
   support repeats.
4. If the receiver is named and coverage is revealed, choose coverage when it
   improves through that receiver.
