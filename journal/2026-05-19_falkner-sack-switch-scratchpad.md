# Falkner Sack-Switch Scratchpad

## Status (updated 2026-05-24 worktree cleanup)

- The two design proposals below (doomed-non-wincon -> wincon sack-switch
  veto + early-AI healthy-coverage stay gate) are **DEFERRED** — neither
  was implemented on any branch as of 2026-05-24. Pickaxe across all
  branches finds no `BossAI_VetoSackIntoWincon`-shaped helper or
  equivalent. Player-visible Falkner behavior described in "Observed
  Problem" below is still reachable in current source.
- The "Check-Over Note" register-lifetime bug flagged later in this
  scratchpad (helpers `ld b, a` between confidence cache and threshold
  compare) **was a real bug** and **is now fixed** in commit `9bb1cf50`
  (`boss AI: reload switch confidence from WRAM before stay-vs-switch
  compare`). That commit drops the dead `ld b, a ; confidence` at
  routine entry and reads `wBossAISwitchConfidence` directly into `a`
  immediately before the `cp c`.
- This journal is preserved as the design record for the deferred work
  + the discovery path for the register-lifetime fix that did ship.

## Observed Problem

Falkner switched a nearly dead Spearow out into Noctowl against Rattata. The
switch saved Spearow for the moment, but Noctowl absorbed the damage, then
Spearow was still easy to finish afterward. This is not the kind of mistake
early AI needs to make. Early AI can be simple, but it should not spend its
ace/wincon just to preserve a doomed non-ace.

## Current Source Shape

- `BossAI_SwitchOrTryItem` does the stay-vs-switch arbitration.
- `BossAI_CheckAbleToSwitchSafe` allows low-HP switching when the current boss
  mon is at quarter HP or below, or when the active player has public threat.
- `BossAI_ComputeSwitchConfidence` can reach very high confidence at low HP.
- `BossAI_ShouldSackInsteadOfSwitch` currently only adds a modest threshold
  penalty when the current mon is low, has no KO, and is not the wincon.
- `BossAI_IsSwitchingIntoWinconRisk` only penalizes switching into the wincon
  when the chosen candidate has enough computed risk. Neutral-looking damage
  into Noctowl can slip through as "safe" even though the trade is bad.

## Candidate Fixes

1. Raise the generic sack penalty.
   - Pro: small.
   - Con: too broad; it would also suppress legitimate low-HP pivots into
     non-ace reserves, and late-tier confidence could still punch through.

2. Make `BossAI_IsSwitchingIntoWinconRisk` more sensitive.
   - Pro: uses existing wincon gate.
   - Con: still frames the issue as candidate damage risk. The badness here is
     strategic: a doomed non-wincon is spending the ace's HP to delay a faint.

3. Add a hard stay gate for "doomed non-wincon -> wincon" sack-switches.
   - Pro: matches the bug directly. Allows normal switches to non-wincon
     reserves, still allows preserving the current wincon, and leaves Perish
     escape / KO lines alone.
   - Con: needs one new helper and audit coverage.

## Chosen Shape

Use option 3.

Add a helper beside the existing sack/wincon finalization code:

- no veto if Perish escape is urgent;
- no veto if current enemy is above quarter HP;
- no veto if current enemy has a KO move;
- no veto if no wincon is known;
- no veto if the current enemy is already the wincon;
- veto if the proposed switch target is the wincon.

Then call it after switch confidence is computed and before the softer sack
threshold bump. On carry, jump to `.stay`, which already pops the saved switch
param and falls back to item/stay behavior.

This keeps early Falkner from feeding Noctowl to save Spearow, and it applies
to mid/late bosses too without making their ordinary switch logic dumber.

## Check-Over Note

While checking the insertion point, I noticed the final confidence compare uses
`b` as if helper calls preserve it. The existing sack/wincon helpers already
reuse `b`, so the final compare can read stale helper scratch instead of the
stored confidence. The code should reload `wBossAISwitchConfidence` before the
threshold compare. That makes the new hard veto safe and also fixes the same
register-lifetime issue for the existing softer penalties.

## Tiered Refinement

The first patch made the wincon-protection veto universal. That is right for
early AI, but too blunt for late AI. A late boss should be allowed to spend the
wincon's HP on a public-information pivot when the switch-in is defensively
justified, such as a hypothetical Rock-type Noctowl resisting Rattata's Normal
pressure.

Refined shape:

- early AI keeps the hard veto;
- mid/late AI can pass the veto if the proposed wincon switch-in resists or is
  immune to at least one current player type and is not weak to either current
  player type;
- the existing soft sack and wincon-risk penalties still run afterward, so this
  is permission to evaluate the switch, not a forced switch.

## Healthy Coverage Switch Note

Separate Falkner report: healthy Spearow switched out against Geodude even
though Spearow had Mud-Slap, and Noctowl was about to eat Rock Throw damage.
This is not the doomed-sack case above. The source shape is:

- public-threat detection says Geodude threatens Spearow, so switch evaluation
  can start with high confidence;
- the pre-switch stay gate only recognized active KO pressure;
- Mud-Slap is a public, damaging, super-effective answer, but not a KO from
  full HP, so the stay gate missed it.

Patch shape:

- only for early AI;
- only when the active boss mon is above quarter HP;
- only when it has a usable-damage move whose type chart is super-effective
  into the current player;
- Perish escape and real KO-prevention lines still remain above this gate.
