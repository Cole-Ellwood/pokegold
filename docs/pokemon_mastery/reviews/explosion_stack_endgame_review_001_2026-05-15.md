# Explosion Stack Endgame Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_031_gen2ou-2586481735_p1_2026-05-15.md`

## Diagnosis

Packet 031 did not repeat the packet-030 severe wake/action miss. The helper's
critical ledger worked well enough to keep severe, hidden-info, and mechanics
errors clean. The new failure class was endgame trade valuation:

- T15: Gengar had a live Explosion into a chipped/paralyzed Raikou, a named
  blocker for the remaining special pressure. Preserving Gengar was acceptable,
  but boom was a real route converter.
- T17: Steelix faced Zapdos after Hidden Power had revealed the anti-Steelix
  pressure. Explosion converted the Steelix job before Steelix became a worse
  future piece.
- T29: Gengar should have exploded into sleeping Heracross. Removing the last
  breaker simplified the remaining Snorlax/Smeargle endgame more than Ice
  Punch chip did.

There was also an opening ledger miss: after Smeargle got Spikes, Heracross
was not a passive sleep target. Its Speed and Megahorn made Steelix or Zapdos
the route-preserving owner before more Smeargle status.

## Source Check

Current GSC sources support the correction:

- Smogon's GSC Explosion guide describes Gengar as an offensive Exploder that
  targets Raikou and other special walls, but also warns that Raikou must be
  weakened or paralyzed so Rest does not undo the trade.
- The same guide frames Explosion as a way to punish predictable play, force
  trades, and create the free-entry sequence that lets the next owner convert.
- Smogon's GSC threatlist describes Steelix as both an Electric immunity /
  physical wall and one of the best Explosion users, especially when it cannot
  safely phaze or wall the current threat.
- The current GSC sample-team breakdown treats Gengar Explosion as a way to
  pressure special walls for offensive partners and notes that Golem/Steelix
  often need Explosion to threaten Zapdos.
- Smogon's Spikes article says Smeargle can set Spikes with Spore support but
  has nearly no bulk, and that Spikes offense needs added status/trades rather
  than passive hazard presence alone.
- Smogon's Heracross discussion centers Megahorn as broad pressure and treats
  Rest/Sleep Talk Heracross as a durable tank, so it must be priced as a real
  route piece rather than only as sleep fodder.

Sources:

- https://www.smogon.com/gs/articles/guide_to_explosion
- https://www.smogon.com/gs/articles/gsc_threats
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- https://www.smogon.com/gs/articles/gsc_spikes
- https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/

## Policy Compression

Compress the lesson into three live rules:

1. In mapped endgames, preserve an Explosion user only for a named remaining
   job. Generic insurance is not enough once the target, lost job, and
   post-trade owner are known.
2. Explosion-stack offense should trade down when removing the named blocker
   leaves a clear closer or free-entry owner, even if the exploder normally has
   defensive value.
3. After Spikes + sleep/status support, re-run the opponent's absorber ledger.
   A faster Heracross or similar breaker can be the owner of the next board,
   not just a target to status again.

## Drill Target

Create one small nonblind regression drill with four positions:

- Gengar boom into chipped/paralyzed Raikou when Raikou blocks the named route.
- Steelix boom into Zapdos after Hidden Power reveals that Steelix cannot keep
  its defensive job safely.
- Gengar boom into sleeping Heracross when the remaining material is mapped.
- Smeargle after Spikes versus Heracross: preserve route by leaving before
  faster Megahorn pressure removes the support piece for free.

The drill is repair scaffolding only. It does not prove progress; only fresh
unseen replay packets can do that.
