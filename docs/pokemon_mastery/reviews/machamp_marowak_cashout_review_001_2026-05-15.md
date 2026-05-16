# Machamp / Marowak / Cash-Out Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_029_gen2ou-2585784320_p1_2026-05-15.md`

## Miss Pattern

Packet 029 did not fail through hidden-team abuse or a severe throw. It failed
through endgame resource valuation:

- T16: after Tyranitar revealed DynamicPunch, I still wanted Machamp instead of
  the typed absorber. That risked the future Fighting owner into the coverage
  it needed to solve later.
- T27: I attacked +2 Marowak with Machamp instead of preserving Machamp through
  Snorlax sack -> Cloyster Ice Beam. The attack probably worked if Rock Slide
  hit and no critical hit occurred, but it spent the cleaner route piece.
- T29: after Cloyster beat Marowak, I switched to Machamp rather than booming
  into sleeping Tyranitar. Explosion did only 47% through resistance, but it
  created a free entry and put Tyranitar in Earthquake range for our own
  Tyranitar.

## Source Check

Current GSC sources support the correction:

- Smogon's GSC Explosion guide emphasizes that Explosion can be used
  defensively to stop sweepers, can simplify winning games by trading down, and
  can create free turns because the Exploder's side gets the next switch.
  It also documents the Gen 2 mechanic that a faster Exploder prevents a
  slower surviving target from moving that turn.
- Smogon's GSC threatlist describes Cloyster as a high-Defense physical check
  with Spikes, Rapid Spin, and Explosion, making it both support and a
  one-time route converter.
- The current GSC sample-team breakdown repeatedly describes Cloyster's
  Surf/Explosion package as a way to threaten most of the metagame and force
  trades once its support job is no longer decisive.
- Smogon's Machamp material frames Machamp as a powerful but slow breaker:
  Cross Chop pressures even boosted Snorlax and Rock Slide covers Zapdos, but
  its low Speed and limited longevity mean it should not be spent when a
  lower-value route removes the threat.
- The GSC speed tiers and mechanics resources reinforce the order issue:
  Cursed Machamp can become slower than Marowak, and GSC self-KO/action order
  must be priced before assuming the slower action happens.

Sources:

- https://www.smogon.com/gs/articles/guide_to_explosion
- https://www.smogon.com/gs/articles/gsc_threats
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- https://www.smogon.com/forums/threads/gsc-ou-machamp.3705043/
- https://www.smogon.com/gs/articles/gsc_speedtiers
- https://www.smogon.com/forums/threads/gsc-mechanics.3542417/

## Policy Compression

Do not add a species-specific wall of notes. Compress into three live rules:

1. Preserve a named converter when controlled sack -> stable revenge removes
   the same threat with less miss/crit exposure.
2. Explosion may convert without KO when the chip plus free-entry owner wins
   the next board.
3. In GSC, faster Explosion/Self-Destruct skips the slower survivor's action;
   do not bank slower wake, Sleep Talk, Rest, phaze, support, or damage after
   it.

## Drill Target

Create one small regression drill with four positions:

- preserve Machamp through sack -> Cloyster revenge;
- spend Cloyster with resisted Explosion to create free Tyranitar entry;
- keep Machamp attacking when exact removal is safer than overguarding;
- mark the self-KO action skip correctly when the slower target survives.

Do not count the drill as progress. Count it only as repair scaffolding before
the next fresh packet.
