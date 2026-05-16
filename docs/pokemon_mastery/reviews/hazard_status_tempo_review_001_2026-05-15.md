# Hazard / Status Tempo Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_033_gen2ou-2585487781_p2_2026-05-15.md`

## Miss Pattern

Packet 033 was not a severe-blunder regression, but top-match fell below gate.
The repeated miss was hazard tempo after sleep or status:

- T13: I wanted Golem Rapid Spin into Skarmory's Toxic. Actual used already
  poisoned Zapdos to absorb the status and keep Golem's spin/phaze job clean.
- T17: after Nidoking slept Snorlax, I treated the sleep turn as a chance to
  switch Golem in for Spin. Actual kept Nidoking in and Earthquaked the Starmie
  spinner branch.
- T19/T30: I under-ranked Cloyster re-entry on passive Skarmory turns to reset
  Spikes. Safe Snorlax pressure was acceptable, but less route-converting.

This is close to existing reset-loop doctrine, but the wording did not force
me to ask whether the "free" reset turn invites the opponent's own resetter or
spends my resetter's status budget.

## Source Check

Current GSC sources support the correction:

- Smogon's Spikes article says the Starmie line is often to bait it into
  spinning, then bring in an immediate pressure owner before Recover.
- The same article emphasizes status as a Spikes-war tool against spinners and
  spikers, while noting Forretress needs sleep or paralysis rather than Toxic.
- The current GSC sample-team breakdown says Golem should usually Rapid Spin
  after switching in on Snorlax or a statused opponent, not by taking needless
  status, and describes Skarmory's Toxic/Rest set as passive but disruptive.
- The sample-team breakdown also frames Cloyster's job as getting and keeping
  Spikes while threatening trades once its support job changes.
- Smogon's Nidoking analysis supports Earthquake plus well-timed Lovely Kiss as
  the route map into Snorlax and other walls, with coverage for Ground-immune
  or resistant targets.

Sources:

- https://www.smogon.com/gs/articles/gsc_spikes
- https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- https://www.smogon.com/forums/threads/nidoking-revamp-qc-3-2-gp-2-2.3481273/

## Policy Compression

Patch `reset_loop_denial.md` with one compact rule:

> Before using a sleep/passive turn to bring in your spinner, ask whether the
> opponent's spinner or status user enters and is punished harder by the active
> move; preserve the spinner's status budget unless Spin converts now.

Do not add a long Starmie/Skarmory species card. The old rules already cover
Starmie, Spikes, status absorbers, and reset loops; the missing step is the
one-cycle comparison before the spinner handoff.

## Drill Target

Create one four-case nonblind drill:

- use a poisoned/status-immune absorber over Golem Spin into Skarmory Toxic;
- keep Nidoking Earthquake after sleep when Starmie is the likely spinner
  branch;
- bring Cloyster back in on Skarmory Rest to reset Spikes;
- Spin with Golem only when it is already in safely and the active threat
  cannot deny the spin first.
