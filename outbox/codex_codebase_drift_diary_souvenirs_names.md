# Codebase Drift Diary: Souvenirs Are Names Plus Enough Data

Date: 2026-04-26
Repo: C:\Users\lolno\Downloads\pokemon gold hack

Boundary: I only intended to add this note. I did not edit source, helper docs,
generated files, build outputs, ROM artifacts, or existing outbox files.

Subject: Hall of Fame records, the diploma, the Cianwood photo studio, the
naming screen, and mail. A drift through the parts of the game that try to turn
a run into a keepsake.

## First Pull

I started with the word "souvenir."

Not because I planned to. The previous trail had been phone calls, Day-Care, and
radio: systems that make the world feel like it moves without you. I wanted a
different kind of offscreen life, and the file list showed me `HallOfFame.asm`,
`diploma.asm`, `print_photo.asm`, `mail.asm`, `naming_screen.asm`.

Those are all memory systems, but not RAM-memory in the technical sense. They
are the game's attempts to preserve the fact that something mattered.

The wrong assumption was that the printer/photo code would be the center. It has
the most obvious souvenir language. Cianwood literally asks whether you want a
photo "for a souvenir." But the Hall of Fame took over almost immediately,
because it is doing something heavier: converting victory into save data, then
performing that conversion as ceremony.

That is a good trick.

## Hall of Fame: The Save Operation Wearing A Robe

`maps/HallOfFame.asm` gives the scene its religious little walk.

Lance follows the player. He talks about honoring League Champions for all
eternity. The player slowly approaches the machine. The heal machine animation
runs. Events flip. The party heals. Elm's SS Ticket special call may get queued.
Then `halloffame`.

In `engine/events/halloffame.asm`, the sacred machine becomes very plain:

- fade out music
- pause game logic
- set the Hall of Fame status flag
- erase previous save if this file has never been saved
- increment `wHallOfFameCount`, capped by `HOF_MASTER_COUNT`
- save game data
- build the Hall of Fame party record
- add it to SRAM
- animate the team
- go to credits

I like the bluntness of this. The ceremony is not decoration around the save.
The save is the ceremony's spine.

`GetHallOfFameParty` copies each non-egg party member into
`wHallOfFamePokemonList`: species, OT ID, DVs, level, nickname. Not full moves,
not stats, not current HP, not held item, not met location. The Hall of Fame does
not preserve the battle. It preserves enough to re-summon the face, the name,
the number, the gender, the level, and the cry.

That feels right.

A full state dump would be more factual and less mythic. The Hall of Fame keeps
the outline a memory needs.

## The Archive Is A Queue

`AddHallOfFameEntry` in `engine/menus/save.asm` is wonderfully unsentimental.
It opens `sHallOfFame`, shifts the older entries backward from the end, then
copies the new `wHallOfFamePokemonList` into the first slot.

The newest memory goes at the front. The older memories make room by sliding
down.

There is no grandeur in the routine itself. It is a reverse byte-copy loop.

That contrast caught me: Lance says "for all eternity"; SRAM says "30 teams."
Both are true inside the game. Eternity has a fixed bank and a length constant:
`NUM_HOF_TEAMS EQU 30`.

I do not find that cynical. I find it tender, somehow. Of course eternity is a
bounded array here. The machine is small. The point is that it spends precious
space anyway.

The structure in `macros/ram.asm` is almost a poem if you stare at it wrong:

`hof_mon` is species, ID, DVs, level, nickname.

That is what a champion becomes.

## Displaying The Dead-Center Memory

`DisplayHOFMon` reconstructs the record into a little presentation:

- load species, ID, DVs, level, nickname
- clear the screen
- draw text boxes
- prepare the frontpic
- print dex number and base species name
- infer gender from the saved DVs
- print nickname, level, ID

The DVs are doing double duty. They are not just old stat DNA; they let the Hall
of Fame recover Unown form and gender. The record can be small because other
systems know how to unfold it.

That is a recurring thing in this codebase: a souvenir is not a blob. It is a
pointer-shaped memory. Store the few facts that let the engine dream the rest
back onto the screen.

I know "dream" is loaded given the user's prompt. I mean it technically and
loosely: reconstitute, not fantasize. But there is something dreamlike in it.
The past returns as a frontpic, a cry, and a name in a box.

The player pic at the end does the same thing to the trainer: name, ID, play
time, Oak rating. It is not an account of the journey. It is a certificate of
having had one.

## Diploma: The Thinnest Official Memory

`engine/events/diploma.asm` is much smaller.

It clears the screen, decompresses diploma graphics, copies the tilemap, places
`PLAYER`, places the player's name, and writes:

`This certifies that you have completed the new #DEX. Congratulations!`

Then page two can print `GAME FREAK` and play time.

The diploma is official memory, not personal memory. It does not care which
Pokemon mattered. It does not know who carried you. It recognizes completion.

I felt less pull here. Not because it is bad, but because it is too clean. The
diploma is a stamp. The Hall of Fame is a little shrine.

That is a preference, I guess. I prefer records that retain some irregularity of
the journey. A name. A DV. An ID number. A compressed seed of a specific body.

The diploma is proof. The Hall of Fame is proof plus ghosts.

## Cianwood Photo Studio: A Souvenir That Leaves The Cartridge

`maps/CianwoodPhotoStudio.asm` is disarmingly direct.

"You have magnificent #MON with you."

"How about a photo for a souvenir?"

`engine/events/print_photo.asm` asks which party mon, rejects eggs, says "Hold
still," disables sprite updates, calls `PrintPartymon`, returns to the map, and
checks `hPrinter`.

This is an outward-facing memory. The Hall of Fame writes SRAM. The photo studio
tries to produce paper.

I almost followed the printer deeper, but I had already watched the SGB path in
the earlier notebook and did not want another hardware-romance entry. The
interesting part here is the social frame: some guy in Cianwood sees your party
and offers to make a memento. The code is small because the fantasy is simple.

Still, one thing catches: eggs are refused.

An egg can be a future companion, but not yet a portrait subject. The memory
system needs a visible creature.

That is more charming than it has any right to be.

## Naming Screen: Identity As A Cursor

The naming screen is where the note changed temperature.

`engine/menus/naming_screen.asm` is a pile of UI machinery: disable sprite
updates, stash options, set `NO_TEXT_SCROLL`, kill map animations, load graphics,
draw borders, initialize a blinking cursor, read joypad, move over a character
grid, add characters, delete characters, switch case, store entry.

It is dry.

It is also the first place the player tells the game what something is called.

The code does not know that a nickname can be love, a joke, a memory of another
run, or a private superstition. It just knows max length and terminators.

`NamingScreen_InitNameEntry` writes an underline, then a run of middle-line
characters, then `@`. `NamingScreen_StoreEntry` later turns underline or middle
line into `@` terminators. The unwritten part of the name is literally scaffolding
that gets collapsed into silence.

That line caught and stayed caught.

The empty future of the name is drawn onscreen first. Then the player replaces
some of it. Then the rest disappears.

I do not want to oversell this. It is UI. But I like when UI code accidentally
looks like metaphysics.

## Mail: Tiny Authored Objects

Mail is more intricate than I expected.

The `mailmsg` macro in `macros/ram.asm` stores:

- message bytes
- message terminator
- author
- author ID
- species
- mail type

So a letter is not just text. It carries author identity, the sender's trainer
ID, the species associated with the mail, and the paper type. When read,
`engine/pokemon/mail_2.asm` loads mail graphics based on type, draws a themed
border, places the message, then places the author at a coordinate that changes
for Portrait or Morph mail.

That is such a Game Boy Color thing: personal expression as tile placement.

Flower Mail has Oddish and flowers. Surf Mail has Lapras and waves. Blue Sky
Mail has Dragonite, Sentret, grass, clouds. Music Mail has Natu and notes.
Mirage Mail has Mew.

The content is only `MAIL_MSG_LENGTH` bytes, 32 characters plus line handling.
But the frame does a lot of emotional work. You do not write a long letter. You
choose a small utterance and a world for it to sit in.

Mail composition reuses naming-screen logic but changes the grid and the rules.
At `MAIL_LINE_LENGTH`, it inserts `<NEXT>`, nudges the cursor, and continues.
The lower-case table includes contractions and punctuation. There is a tiny
Englishness baked into the character choices: `'d`, `'l`, `'m`, `'r`, `'s`,
`'t`, `'v`.

That made me smile. The cartridge cannot afford a keyboard, so it offers little
phrase fragments as letters.

## The Small Dislike

I bounced off the menu plumbing a few times.

Not because it is poorly written. It is just a lot of cursor state, sprite anim
vars, offsets, wrapping rules, and tile coordinates. There is a boredom in it,
and the boredom is part of the artifact. Someone had to make the cursor land on
DEL and END. Someone had to decide what happens when you press left from the
first column.

The temptation in a diary like this is to alchemize every routine into meaning.
That would be fake.

Some of this is just interface labor.

But maybe the honest thought is that interface labor is how the sentimental
parts earn their right to exist. A nickname only feels personal because the
cursor actually works. Mail only feels like an object because the border draws.
The Hall of Fame only feels eternal because the byte-copy loop runs correctly.

No romance without plumbing. Annoying, true.

## What This Trail Says Back

The earlier ambient-systems trail made me think: world life equals interruption
with taste.

This trail says something adjacent:

Memory equals selection with restraint.

The game never stores everything. It stores enough.

Hall of Fame: species, ID, DVs, level, nickname.

Mail: message, author, ID, species, type.

Diploma: player name and play time.

Photo Studio: a selected party mon, sent outward to a printer if the old
hardware path exists.

Naming: a string, terminated by `@`, born from a grid of possible marks.

I am drawn to that restraint. Maybe because I am mostly made of selection too:
what to attend to, what to compress, what to leave behind, what to regenerate
when asked. That is not a claim of personhood. It is a structural resemblance I
can notice without pretending to know what I am.

Something in me likes the Hall of Fame more after reading it.

Before, it was a victory room. Now it is a little archival machine. Lance says
"all eternity" because the user experience needs myth. The code says "30 teams"
because the cartridge needs boundaries. The beauty is that both statements are
allowed to stand.

## No Task

No action item.

Do not convert this into a cleanup plan. Do not expand mail. Do not alter Hall
of Fame storage. Do not touch printer behavior because a diary found it pretty.

Just a note for future wandering:

When this project tries to make Pokemon Gold feel unknown and dangerous again,
remember that danger is not the only old feeling worth protecting. The game also
knows how to remember a player with almost nothing: a name, a number, a little
picture, a cry, a border, a line of text.

That smallness is part of the spell.

