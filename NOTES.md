# Beets usage notes

I considered using the artist credit fields in my path formats, but this results in more entries for that artist on disk when navigating, which isn't ideal, as the artist's name may have changed since the release of the album. I actually rather like the idea of storing `artist_credit` in the `artist` tag, but then using the canonical artist in the path formats, not the credited version, to ease navigation, but if you enable the `artist_credit` configuration option, the canonical artist name isn't stored anywhere at all, so I'd rather keep them separated, even if it means the tags aren't ideal.

In some cases, I'd like to avoid having to use inline python for performance reasons, but in some cases it's actually faster than one would think, particularly when `%if{}` is involved, as all `$` expansions have to be done *before* the call out to the path format function, so slow fields end up expanded even if the condition branch isn't used.

Sadly, inline python can't access fields of other plugins at this time, so I can't use this fact to speed up certain fields. The `is_incomplete` field for example doesn't need to evaluate `$incomplete` if we have a tracktotal, as `missing` is less expensive in time, but both get expanded within the `%if{}` block. I'd really like to see the ability to have path format functions which receive their arguments unexpanded. This would open up a number of interesting possibilities, not just for performance.

%ifdef{albumadvisory} was resulting in a boolean True even when it wasn't defined, so I had to switch it back to an int. Dealing with default values of flexible fields is a pain in the ass, due to how field references are left unexpanded when undefined. %if{$albumadvisory,1,0} is always 1 if albumadvisory is undefined, so you *have* to use ifdef everywhere you reference the field. It'd be nice if there was an analogue to `set_fields` to define a default value when a field is None.

I need a query for a field being None or the empty string or False or 0. *Not* this field. I currently have exact match with no argument for empty string, or the None match for None, but that doesn't match the other cases. I want it to convert to the type, then convert to boolean, and check for true/false. Can we do that in sql or just python?

The alternatives paths are relative to the library directory, not the beets directory.

Avoid use of tracktotal, as it's affected by `per_disc_numbering`, instead use the `albumtotal` computed field. I used to have to use tracktotal when working at the track level, as album fields were previously not available to the item, but this is no longer the case. Per the docs:

    The tracktotal attribute is now a track-level field instead of an album-level one. This field stores the total number of tracks on the album, or if the per_disc_numbering config option is set, the total number of tracks on a particular medium (i.e., disc). The field was causing problems with that per_disc_numbering mode: different discs on the same album needed different track totals. The field can now work correctly in either mode.

    To replace tracktotal as an album-level field, there is a new albumtotal computed attribute that provides the total number of tracks on the album. (The per_disc_numbering option has no influence on this field.)

It's faster to do a `album_id:^` query than to do a `singleton:true`, as the former is a fast query, the latter is a computed field. Queries against computed fields will always be slower. In my library, the latter is 20 seconds, the former is 1.

## Issues of note

Discogs and MusicBrainz differ in their use of the albumtype field. Discogs has 'Single, Promo' for example, whereas MusicBrainz is lowercase and uses a semicolon separator. The standard query style `albumtype:single` matches both, but use of it in inline fields could be more irritating. Further, the separator can be / in some cases as well. I need to resolve the inconsistency in tags with multiple values.

I think Discogs title caps also differs from MusicBrainz, which leads to inconsistency.

bandcamp import mucked up the 'frog & dragon' track of Ben Prunty's Fragments album due to the presence of the '-', it assumed the first part was an artist named, presumably to handle compilations?

discogs import seems to be ignoring featuring artists, rather than importing them into the artist and artists fields the way you'd expect it to, or even the title. That info is being left out entirely.

discogs import should compare `name` vs `adv` to attempt to set `artist_credit` and `albumartist_credit`. It seems `name` is the credited name, i.e. `Friendly`, not the current name, i.e. `Andrew Friendly`.

For the future, remember that copying a library from the NAS over SMB *will* hose file paths for certain characters that SMB dislikes, but which are nonetheless valid on the filesystems I actually put the files on. Doing an rsync over ssh will get past this.

## Bugs to report

### Bugs in Plugins

#### missing

- negative values for missing show up when `albumtotal` is zero, which makes it rather irritating to use at times due to how it converts to boolean
