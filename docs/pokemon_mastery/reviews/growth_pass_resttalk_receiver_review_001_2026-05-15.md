# Growth Pass / RestTalk Receiver Review 001 - 2026-05-15

Parent packet:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_026_gen2ou-2588645722_p1_2026-05-15.md`

Trigger: packet 026 had a severe miss on turn 25 and hidden-info errors around
Jynx Thief and RestTalk Snorlax attacking rolls. This review is a repair note,
not progress proof.

## Sources Checked

- Pokemon Showdown replay and raw log:
  `https://replay.pokemonshowdown.com/gen2ou-2588645722`
- Smogon GSC OU Snorlax spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/forums/threads/introduction-to-status-moves-in-gsc.3448819/`
- Smogon GSC OU Espeon spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## What The Sources Changed

Smogon Snorlax material reinforces that Double-Edge plus Earthquake is not a
rare hidden branch; it is the core physical threat package. The status guide's
standard RestTalk Snorlax example also puts Sleep Talk / Rest / Curse /
Double-Edge on the short list of known GSC sleep users. In the replay, once
Sleep Talk and Earthquake were public, a Normal STAB attacking roll had to be
treated as strong-prior, not possible-only.

Smogon Espeon material frames Espeon as powerful but physically fragile, and
the sample-team Baton Pass discussion emphasizes that pass teams are disrupted
by phazing and Spikes but can swing a game from a single pass. That makes the
live question after Growth not "can Psychic do damage?" but "who receives the
boost if the current passer dies to the next public/strong-prior roll?"

The sample-team note on lead Jynx also directly explains the turn-6 miss:
Jynx often Thiefs the incoming Sleep Talk special check. After Lovely Kiss
lands, default Sleep Talk from the Leftovers RestTalker is not automatic.

## Repair Rule

When Growth/Baton Pass is in the live package, keep a receiver ledger:
current boost owner, legal receiver, receiver's survival against revealed and
strong-prior immediate rolls, and the opponent's next reset/phaze owner. Attack
only if it wins before those rolls; otherwise Baton Pass is the converter.

When RestTalk Snorlax is the target, price both reset rolls and attacking
rolls. Sleep Talk calling Rest refreshes the clock; Sleep Talk calling
Earthquake or Normal STAB can remove a frail boosted passer before the damage
route converts.

When Jynx has landed sleep, treat Thief as part of the lead package until it is
revealed absent or the item has already been spent.

## Transfer Check

Required next fresh gate: after a boost, name:

1. current boost owner;
2. receiver that survives revealed and strong-prior Sleep Talk rolls;
3. phazer/spinner branch;
4. attack-now damage threshold.

If I cannot name those four, I should not claim route conversion from another
Psychic/Thunder/Surf click.
