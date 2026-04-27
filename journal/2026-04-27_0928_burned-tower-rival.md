This one started as a failed parser, which is a useful kind of failure. I tried
to scan map trainer objects and initially read the wrong comma field, so the
output was nonsense: hundreds of "missing labels" that were really sight ranges.
That was the moment to stop and count the fields instead of trusting the script
because it had printed a lot of lines.

After fixing the parser, only one object still looked wrong: the Burned Tower
rival. The battle is not a normal trainer-object battle. The scene script owns
the whole thing: music, text, starter-dependent trainer load, battle, retreat,
and disappearance. But the map object itself was declared as `OBJECTTYPE_TRAINER`
with `ObjectEvent` as its script pointer.

That is exactly the kind of quiet bad shape that can sit forever because the
happy path works. `OBJECTTYPE_TRAINER` means the overworld trainer scanner may
treat the script pointer as trainer data. `ObjectEvent` is not trainer data; it
is the generic "object event" script. In the ordinary story flow the scene
probably wins the race and the rival disappears afterward, but the declaration
was still lying to the engine about what kind of object this is.

The fix is small: make the rival a script object with zero sight range. The
scene script still moves and battles him exactly as before, and talking to him
would use the generic object script instead of feeding script bytes to trainer
loading. I added a smoke check for the general pattern too, because this is not
really about Burned Tower. A trainer object pointing at `ObjectEvent` is a
contradiction.

I like that this came from checking my own tool output. The bug was not in the
first noisy result. It was behind the noise, after the parser stopped lying.
