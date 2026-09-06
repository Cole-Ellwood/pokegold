# Corpus triage, 2026-09-06

This is evaluator-side source triage, not a frozen corpus or a runtime score.
These locations have been inspected during development and must not be presented
as unseen diagnoses by this host agent. The diagnostic runner must receive only
sanitized source exports and runtime inputs, not this document.

The roadmap still requires a 20-failure blind pilot, a separate control set, and
the 100-failure/30-control release corpus. The reproduced development cases
(Grass regrowth, party-mail removal, and the link-mail search below) do not
satisfy those denominators.

## Duplicate history

`de1744a2` and `11b8679b` have the same stable Git patch ID:
`81fdc6bfde57b99266e92eea137515baa2647b2f`. They are two copies of the same
multi-fix patch, not two independent sets of regressions. Individual failures
inside a multi-fix commit still need separate reproductions and causal review.

## Candidates inspected

The following changes occur in `c129c3b8201bb4922a0dd7676fcf524fe4fdaaaf`;
its parent is `2dda61ae8376178c71a0f516232d4ceaf051354c`.

| Candidate | Source evidence | Required runtime witness / remaining gap |
| --- | --- | --- |
| Trainer-script resume context overwritten by shared WRAM | `engine/overworld/scripting.asm`, `Script_startbattle`: adds conditional save/restore of `wSeenTrainerBank` through `wTempTrainerEnd` around battle execution. | Record a real battle/evolution overwrite and the resumed script consuming the wrong context. A synthetic overwrite alone would not establish reachability. |
| Link-mail preamble search reads beyond its buffer | `engine/link/link.asm`, `Gen2ToGen2LinkComms.loop2` and `.loop3`: adds a buffer-length counter and exits at exhaustion. | Run malformed or truncated mail buffers through the unmodified parser; observe all reads and `.skip_mail`. A staged parser snapshot would not establish a live peer exchange. |
| Queued tile copy returns before service acknowledgement | `home/gfx.asm`, `Request1bpp` / `Request2bpp`: replaces a single `DelayFrame` with a wait for the request-size byte to clear. | Delay the actual VBlank service, then observe completion and destination VRAM. The two bit depths are variants of one handshake defect, not automatically two failures. |
| Tile service exceeds its safe scanline interval | `home/video.asm`: adds LY guards; `home/vblank.asm` selects the prechecked 2bpp service. | Capture scanline-sensitive execution and VRAM results. Keep backend-specific results separate; cross-backend claims require the roadmap's VBA-M comparison. |
| Full tilemap copy races pending incremental updates | `home/tilemap.asm`, save-menu and phone copy routines: clears pending update/count bytes. | Observe a pending incremental update, a full copy, and subsequent corruption on the broken revision. Multiple copy entry points do not by themselves constitute independent defects. |
| Disable searches beyond the four move slots | `engine/battle/move_effects/disable.asm`: adds a `NUM_MOVES` bound and failure exit. | Supply an absent previous move and observe bounded failure on the corrected revision versus the broken search. This expands boundary coverage but not the missing non-battle families. |

The release smoke checks added by this commit are predominantly source-text
contracts. `tools/audit/check_vram_request_contract.py` is likewise a source
audit. Neither is a substitute for the requested runtime reproduction or an
autonomous diagnosis result.

Additional development fixture: the bounded link-mail search. It exercises a different
failure mechanism from register clobbering and has a precise buffer-boundary
contract. Both historical exports now build, and the isolated parser witness
reproduces the first out-of-bounds read checkpoint on the parent versus bounded
exit on the correction. Four malformed-input variants replay identically in
fresh emulator instances; they count as one mechanism. See
[link-mail scan evidence](link_mail_search_2026-09-06.md). No live link peer,
fresh-game navigation, public autonomous diagnosis, independent review, or blind
acceptance is established. The other candidates above remain unreproduced here.
