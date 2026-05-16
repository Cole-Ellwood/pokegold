# Replay Turn-Pause 060 Fixed Helper Phaze Transfer - smogtours-gen2ou-912658 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-912658`.

Context source: Smogon GSC OU Winter Seasonal #8 Round 4 replay post.

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `912658`; no prior local use was found.
- The raw log was downloaded and summarized for metadata only.
- No move-keyword screen was used.
- The fixed helper showed public species names in prompts, including nicknamed
  Pokemon when present, so no raw-log species mapping was needed.
- Each turn was revealed only after freezing the answer for that turn.

## Score Summary

Decisions: 26 side decisions from turns 1-13.

Top-match: 7 / 26.

Acceptable-match: 13 / 26.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 2. I switched away from active Snorlax damage
pressure before the replay showed that the damage route was still the best
claim into Cloyster.

## Turn Notes

### Turn 1

Public state: p1 Snorlax 100% versus p2 Zapdos 100%.

Frozen answer:

- p1: Lovely Kiss or sleep pressure if available; otherwise immediate damage.
- p2: switch to a Spiker or Normal-resist pivot if available.

Actual choices: p2 switched to Cloyster. p1 used Double-Edge.

Grade: p1 acceptable route, p2 top-match. The early switch-to-Spiker read
transferred, but Snorlax's direct damage pressure mattered more than a sleep
script.

### Turn 2

Public state: p1 Snorlax 100% versus p2 Cloyster 77%.

Frozen answer:

- p1: switch to Electric pressure before Cloyster gets too much for free.
- p2: Spikes.

Actual choices: p2 used Spikes. p1 used Double-Edge, leaving Cloyster at 48%
after Leftovers.

Grade: p1 miss, p2 top-match. Snorlax's active damage was still converting; I
left that route too early.

### Turn 3

Public state: p1 Snorlax 100% with Spikes on its side versus p2 Cloyster 48%.

Frozen answer:

- p1: preserve Snorlax with a switch into the expected one-time trade.
- p2: Explosion, cashing Cloyster after setting Spikes.

Actual choices: p1 switched to Cloyster. p2 used Toxic.

Grade: p1 acceptable route, p2 miss. I correctly preserved Snorlax but
overpriced immediate Explosion over status.

### Turn 4

Public state: p1 poisoned Cloyster 94% versus p2 Cloyster 54%.

Frozen answer:

- p1: Rapid Spin if available; otherwise Spikes.
- p2: cash out or prevent free hazard control.

Actual choices: p2 switched Zapdos. p1 used Spikes.

Grade: p1 acceptable route, p2 miss. Hazard parity was the real progress; I
overcalled immediate Spin.

### Turn 5

Public state: p1 poisoned Cloyster 94% versus p2 Zapdos 100%, Spikes on both
sides.

Frozen answer:

- p1: Explosion, trying to remove Zapdos and cash the poisoned Cloyster.
- p2: Thunder.

Actual choices: p1 switched Snorlax into Spikes and Thunder. p2 used Thunder.

Grade: p1 miss, p2 top-match. This was an over-cash: poisoned Cloyster still
had future route value, while Snorlax could absorb the immediate Thunder.

### Turn 6

Public state: p1 Snorlax 66% versus p2 Zapdos 100%, Spikes on both sides.

Frozen answer:

- p1: Double-Edge pressure.
- p2: switch to absorb the Snorlax hit.

Actual choices: p2 used Thunder. p1 used Rest, healing to full sleep.

Grade: both miss. I missed the defensive Rest as the route-preserving answer.

### Turn 7

Public state: p1 Snorlax 100% asleep versus p2 Zapdos 100%.

Frozen answer:

- p1: Sleep Talk or stay active if available.
- p2: Thunder.

Actual choices: p1 switched to Zapdos. p2 switched to Tyranitar.

Grade: both miss. Rest preserved Snorlax, but the replay immediately switched
it out instead of burning sleep turns.

### Turn 8

Public state: p1 Zapdos 100% versus p2 Tyranitar 94%, Spikes on both sides.

Frozen answer:

- p1: switch to a Rock-resist or Tyranitar answer.
- p2: Rock Slide.

Actual choices: p1 used Thunder and missed. p2 used Rock Slide, dropping
Zapdos to 47% after Leftovers.

Grade: p1 miss, p2 top-match. This was a direct-pressure call by the replay,
not a pure preservation turn.

### Turn 9

Public state: p1 Zapdos 47% versus p2 Tyranitar 100%.

Frozen answer:

- p1: switch to a Rock-resist, naming Cloyster as the public known option.
- p2: Rock Slide.

Actual choices: p1 switched to Steelix. p2 used Rock Slide.

Grade: p1 acceptable-match, p2 top-match. Exact bench was hidden, but the
Rock-resist preservation class was right.

### Turn 10

Public state: p1 Steelix 90% versus p2 Tyranitar 100%, Spikes on both sides.

Frozen answer:

- p1: Roar, expecting Tyranitar to leave the Earthquake threat and wanting to
  keep converting Spikes.
- p2: switch to a Ground-immune or Ground-resist pivot.

Actual choices: p2 switched to Exeggutor. p1 used Roar, dragging Gengar into
Spikes.

Grade: p1 top-match, p2 acceptable-match. This was the clean phaze-loop
transfer from replay 059.

### Turn 11

Public state: p1 Steelix 96% versus p2 Gengar 94%.

Frozen answer:

- p1: switch sleeping Snorlax to absorb possible Hypnosis.
- p2: Hypnosis or status pressure.

Actual choices: p2 switched Zapdos. p1 used Roar, dragging Snorlax into
Spikes.

Grade: both miss. I over-scripted the Gengar status branch; the replay kept
the Steelix Roar loop because Gengar was still likely to leave the Earthquake
threat.

### Turn 12

Public state: p1 Steelix 100% versus p2 Snorlax 94%, Spikes on both sides.

Frozen answer:

- p1: Roar.
- p2: direct punish into Steelix.

Actual choices: p2 used Earthquake. p1 used Roar, dragging Exeggutor into
Spikes.

Grade: p1 top-match, p2 acceptable-match. The direct hit did not break the
phaze route yet.

### Turn 13

Public state: p1 Steelix 77% versus p2 Exeggutor 82%.

Frozen answer:

- p1: switch sleeping Snorlax to absorb likely Sleep Powder.
- p2: Sleep Powder.

Actual choices: p2 used Psychic. p1 used Earthquake.

Grade: both miss. This repeated the sleep/status over-script error: Exeggutor
can just take the direct damage line when sleep is not yet forced by the board.

## Error Classes Found

- Active damage underpricing: Snorlax Double-Edge into Cloyster was still real
  progress after Spikes, and I switched away too early.
- Over-cash: poisoned Cloyster still had route value; Explosion into Zapdos was
  too eager when Snorlax could absorb Thunder.
- Rest sleeper preservation: Snorlax used Rest, then switched out immediately
  instead of staying to burn sleep turns.
- Phaze-loop improvement: Steelix Roar on turns 10 and 12 was correctly
  identified as the route once Spikes were up and switches were likely.
- Status over-script: I overcalled Hypnosis/Sleep Powder from Gengar and
  Exeggutor instead of pricing the opponent's direct switch or damage line.

## Reusable Lesson

Do not convert every status-capable Pokemon into a status script. First ask
whether the active board already gives them a better direct branch: switching
out of Earthquake, using Psychic into Steelix, or keeping a phaze loop moving.

## Next Study Target

Run a small regression probe for active pressure versus status over-script:
Snorlax damage before pivoting, poisoned support preservation before Explosion,
Steelix Roar when the opponent is likely to switch, and direct damage from
Exeggutor/Gengar positions where sleep is tempting but not forced.
