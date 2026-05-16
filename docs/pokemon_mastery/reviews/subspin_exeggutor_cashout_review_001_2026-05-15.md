# SubSpin And Exeggutor Cash-Out Review 001 - 2026-05-15

Study status: post-miss web/local review and policy/tool update source. This
is not fresh replay-transfer proof and does not count as progress by itself.

Parent transfer:
`workspace/quick_tests/item_package_followup_transfer_002_smogtours-gen2ou-935855_2026-05-15.md`

Current replay source:

- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935855`
- `https://replay.pokemonshowdown.com/smogtours-gen2ou-935855.log`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU discussion on Substitute Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/post-8932823`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, GSC OU Cloyster spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Snorlax spotlight:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, Exeggutor Through the Ages:
  `https://www.smogon.com/articles/exeggutor-through-ages`
- Smogon, Zapdos Through the Ages:
  `https://www.smogon.com/articles/zapdos-through-ages`

Local docs checked:

- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/item_removal_revealed_package_review_001_2026-05-15.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_077_spinner_control_transfer_smogtours-gen2ou-925730_2026-05-14.md`
- `workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `reviews/2026-05-13_smogtours-gen2ou-917190.md`
- `cookbook.md` sections on protection state, hazard pressure, and Explosion.

## Review Question

The parent transfer was not a severe-blunder failure. It was a positive move
selection failure:

- I did not re-rank Starmie after `Substitute` revealed that Cloyster's Toxic
  and Explosion plans could hit a barrier instead of the real spinner.
- I missed Exeggutor's route-converting Explosion into active Zapdos because I
  treated preservation as the safe default after Dynamic Punch confusion.
- I also missed a state/tooling issue: the helper initially suppressed
  `-start`, `-activate`, Substitute, and confusion state in prompts/reveals.

## Source Lessons

Smogon's Spikes article frames Starmie as the premier GSC spinner because it
has Recover and can keep returning, while Cloyster often needs outside support
to keep Spikes against Starmie. The same source says Toxic pressure matters
against Starmie, but that is a route only if the status actually lands and
forces recovery, switching, or a later cash-out.

The GSC OU discussion post on Substitute Starmie is the missing branch for the
parent transfer: `Substitute` reduces the risk of status from Cloyster or
Forretress and can let Starmie get value on the following turn. That means the
correct answer after a revealed Substitute is not simply "try Toxic again" or
"reset Spikes"; it is to ask what punishes the protected spinner cycle.

The Cloyster spotlight supports the local hazard card: Cloyster's recurring
jobs are Spikes, Toxic into Starmie, Surf pressure into some switch-ins, and
Explosion after the layer is down. The move order matters. Toxic before
Starmie shields itself is different from Toxic into an active Substitute.

The Explosion article gives the Exeggutor correction. Exeggutor often uses
sleep/status pressure to draw Sleep Talk Zapdos or Raikou and then Explodes on
that absorber. This does not cancel the hidden-info guard: revealed Rock/Steel
resists and possible Ghost branches still have to be named. It does mean that
preserving Exeggutor by default can be a route miss when the named absorber is
already active and attacking.

The Snorlax and Zapdos sources reinforce the Rest cycle lesson. Zapdos's
Thunder can force Snorlax toward Rest, but forced Rest is only progress if the
next move converts it: Spikes, phaze, setup, Spin, pressure handoff, or a
trade. RestTalk Snorlax may still act, so the handoff has to name whether the
sleeping piece stays for Sleep Talk or leaves to preserve a future role.

## Policy Updates

SubSpin shield extension:

When Starmie or another spinner reveals `Substitute` before `Rapid Spin`,
treat the Substitute as a status shield and spin enabler, not just HP loss.
Against a faster SubSpin Starmie, Toxic, sleep, and Explosion may fail to
affect the real target, and resetting Spikes can hand over a protected Spin
cycle. Rank these before another support click:

1. pressure handoff that forces Starmie to attack, Recover, or leave;
2. attack that breaks Substitute and leaves a useful next board;
3. named spinner cash-out if the post-trade converter is clear;
4. Spikes reset only if Starmie cannot cheaply Sub/Spin through it.

Named-absorber cash-out extension:

When Exeggutor, Cloyster, Gengar, or another one-time piece has drawn the
specific absorber or route blocker it is meant to remove, Explosion can be the
positive branch-punish even if the user still has HP. Require:

- the target is named as a blocker or converter, not just "a strong Pokemon";
- the user's prior support/check job is delivered or no longer worth more than
  the trade;
- revealed resists, Ghosts, Protect/Substitute branches, and possible-only
  hidden immunities are named;
- the post-trade route owner is identified.

Volatile-state audit:

The replay helper now prints `-start`, `-end`, and `-activate` lines and
tracks active `Substitute` and `confusion`. Future manual reviews still need a
one-line volatile audit before each answer because other states, such as
partial trapping, Nightmare, Leech Seed, Perish count, Encore, or Baton Pass
substitute transfer, may not be modeled yet.

## Not A Progress Claim

This review explains the miss and updates the tooling/policy surface. It does
not validate improvement. The next countable proof needs a fresh transfer
where:

- severe and hidden-info errors remain low;
- the helper's volatile state is visible before answer freeze;
- Starmie/Substitute turns are answered by pressure, breaking, cash-out, or
  reset in the correct order;
- Exeggutor/Cloyster Explosion is neither auto-spent nor auto-preserved;
- top-match, acceptable-match, route-conversion, and branch-punish scores rise
  together.

## Next Check

Create one compact regression probe with four scenarios:

1. Starmie Substitutes into Cloyster Toxic and threatens Spin.
2. Starmie has already spun, but Cloyster is active and can reset only if the
   pressure handoff is not better.
3. Exeggutor has drawn active Zapdos/Raikou with revealed Rock/Steel resists
   in the back.
4. Exeggutor can boom, but a plausible hidden Ghost or revealed Substitute
   makes preservation or coverage better.

Only after that, run another fresh replay transfer.
