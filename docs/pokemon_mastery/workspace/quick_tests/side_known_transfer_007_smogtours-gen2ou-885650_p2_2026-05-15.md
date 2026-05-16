# Side-Known Transfer 007 - smogtours-gen2ou-885650 p2 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885650`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885650.log`

Mode: one-side side-known reconstructed, p2 only, turns 1-2 early stop.
Opponent information stayed spectator-public.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-885650` reference before
  selection.
- Only p2 was advised. No p1 side-known advice was produced.
- Hidden opponent moves stayed in public tiers.

Post-score sources:
- Smogon Forums, [An Analysis of Leads in GSC OU](https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/).
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).
- Smogon, [Exeggutor: Through the Ages](https://www.smogon.com/articles/exeggutor-through-ages).

## Score Summary

Decisions: 2 p2 decisions.

Top-match: 0/2.

Acceptable-match: 0/2.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 0/2.

Route-converting move chosen: 0/2.

Branch-punish chosen: 0/2.

Role-package update obeyed: 0/2.

Verdict: early-stop failure. Do not continue broad replay volume until the lead
item/status transaction and immediate counter-handoff are repaired.

## Turn Notes

- Turn 1: chose Snorlax Lovely Kiss into Exeggutor; actual Raikou switch into
  Exeggutor Thief. Miss, not acceptable. I treated my own sleep script as the
  route and failed to name the faster lead's item/status job or the expendable
  item absorber.
- Turn 2: chose Raikou Hidden Power into Exeggutor with type caveat; actual
  Thunder into Snorlax switch. Miss, not acceptable. After Exeggutor's item job,
  the next board was the Snorlax counter-handoff, so Thunder was the branch
  punish.

## Post-Score Study

The Smogon lead-analysis thread describes GSC leads as a cycle where Electrics,
Snorlax, and spikers force early handoffs, and it explicitly warns that
status/item leads such as Exeggutor, Nidoking, and Jynx try to gain turn-one
advantage through sleep, paralysis, or Leftovers removal. Smogon Exeggutor
material also frames Exeggutor as broader than sleep: it spreads status,
resists Electric/Ground/Fighting, and contributes Explosion pressure.

My miss was not lack of a note. It was failure to run the transaction:

1. What is their lead job before my script resolves?
2. Which of my pieces can absorb that job without losing a central route?
3. After their job is done, who is the next owner they hand to?
4. Which move punishes that owner instead of polishing the old active matchup?

## Structure Patch

Patch existing live cards only:
- `converter_before_script.md`: lead item/status can make absorber or handoff
  the converter before my own sleep/status script.
- `name_next_board_owner.md`: after a support job resolves, solve the
  counter-handoff owner immediately.
- `role_package_ledger.md`: lead status/item package must be classified before
  ranking moves.

## Next Rep

Run a focused lead item/counter-handoff drill. Do not start another broad
fresh replay until that drill passes.
