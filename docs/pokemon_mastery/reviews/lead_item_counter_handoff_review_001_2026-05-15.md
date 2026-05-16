# Lead Item Counter-Handoff Review 001 - 2026-05-15

Trigger:
`workspace/quick_tests/side_known_transfer_007_smogtours-gen2ou-885650_p2_2026-05-15.md`

## Verdict

This is a real regression, not replay-oracle noise.

The Rest/Curse timing patch transferred in packet 006, but the next fresh
packet immediately repeated the older opening problem: I treated a lead as a
single visible matchup instead of a transaction. Exeggutor was not only "a
thing Snorlax can Lovely Kiss"; it was a faster status/item lead with likely
handoffs after the job.

## Source-Backed Lesson

The current Smogon lead-analysis thread says GSC lead play often starts from a
cycle of Electrics, Snorlax, and spikers, and that status/item leads such as
Exeggutor can gain early advantage with sleep, paralysis, or Leftovers removal.
The same source notes that Exeggutor's common counters include Electrics and
that it can use status or Thief to support sweepers. Smogon Exeggutor material
backs the broader package: status spreading, key resistances, and Explosion
pressure are all part of its GSC value.

## Compact Repair

Do not add a new live card. The live cards already cover scripts, owner naming,
and package reveals. The missing retrieval step is a sentence inside each:

- Lead item/status can make absorber or handoff the converter before my own
  sleep/status script.
- After a support lead performs its job, assume the old active matchup may be
  over and solve the next owner.
- The branch-punish must hit that owner, not only the lead still on screen.

## Next Test

Regression drill only, then one fresh side-known packet. If the next fresh
packet repeats lead item/counter-handoff twice, stop replay review and consider
whether the prompt should force a separate "transaction ledger" line before
ranked candidates.
