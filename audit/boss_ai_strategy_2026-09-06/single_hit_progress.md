# Single-hit endpoint reuse

The public range helper now computes pre-roll damage once for one-hit ranges,
then applies both roll/postroll endpoints separately. The general multihit path
retains per-hit HP transitions. Fixed damage, Super Fang and immunity bypass
random variation as before; False Swipe caps precede raw endpoint storage, and
current target HP separately caps returned HP loss. No replies, weights, policy
choices, or persistent memory were changed. The API document now references
AD_CONTEXT_SIZE instead of its stale literal byte count.

The broad nine-action/254-reply workload measured 464,461,544 cycles versus
623,729,576 before this change (25.5% reduction; about 111 seconds at normal
Game Boy clock). Two measurements, including an expanded profiler, returned
exactly the same cycle upper bound. Both retain less than two frames of return
trap padding. The score vectors and exhaustive comparison pass; runtime is still
unsuitable for production. Source: profile_joint.py; baseline is
joint_profile_before_single_hit.json and latest result is joint_profile.json.

All 298 adapter fixtures now additionally compare optimized range results
against the original two-kernel path on identical normalized contexts. They
compare both endpoints, support, stack and every supported context byte. Existing
checks independently compare with actual combat and check RNG/live-state
preservation. Unsupported output scratch is unspecified; returned zeros and
support are compared, without requiring identical scratch on that path.

Normal Gold/Silver builds, documentation navigation and the 12 applicable audits
passed. Gold and Silver each passed all 773 fixtures with zero errors. The
results and final independent disposition are bound in single_hit_manifest.json
and single_hit_review.md. Debug/trace
binaries were not rebuilt during this increment; their existing audit evidence
is historical.

Next measured bottleneck: the expanded temporary profiler attributes 182,641,388
inclusive cycles (39% of total) to 3,188 chart calls. A same-bank mirror emitted
from authoritative TypeMatchups rows can remove per-byte bank switching while
preserving source order and Foresight markers. This is proposed, not implemented.
Production promotion, complete stage 2 valuation, successor search, learning and
strategic acceptance remain unfinished.
