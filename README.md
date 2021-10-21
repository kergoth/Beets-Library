# Beets-Library

My personal beets configuration and scripts

## Terminology

In my library and configuration, a `sole track` is a case where I only have a single track by that artist in my library. I like to separate these to allow tracks where I have other works by that artist to be placed in the same location as the other tracks and albums by that artist, rather than in my `single tracks` folder.
A `single track` is a case where I only have one track from that album.

## Reference

- `beet lastgenre` to set genres on music from last.fm. This requires manual review, and may well require further tweaking of genre-whitelist.txt and genres-tree.yaml. Better yet, I intend to drop it in favor of whatlastgenre, but it'll do for now.
- `beet wlg` to set genre from discogs, etc. This still requires review.
- `beet mbsync` will update from musicbrainz, but often requires manual review to correct bits that were fixed at import time. I should fix `modifyonimport` to also apply on `mbsync`.

## Flexible Fields

I use a number of manually set flexible fields in my library.

The `loved` field is used at both item and track level to bring those items up to the toplevel in my media player path formats for easier navigation to the songs and albums I listen to most often. I may rename this field to `favorite` or `liked` or similar, I have not decided. I may also introduce a separate `liked` field for items which I don't listen to all the time, but nonetheless stand out to me compared to some of the other contents of the library. Further, I may introduce a field to indicate what I have an haven't listened to, in a project aiming to listen to the entire library and either rate things or flag them as liked or not.

### Track Fields

- loved: See above for the description.

### Album Fields

- game: The name of the game this music is about. This may be for a soundtrack, but could also be for albums inspired by that game.
- gamedisambig: This string disambiguates cases where multiple albums reference the same game. In-game, orchestral, inspired by, etc.
- franchise: The media franchise this media belongs to, most commonly the game franchise or series in my gaming music, but this will be expanded upon further in some cases, as there are soundtracks which also apply.
- loved: See above for the description.
- to_listen: Music I'd like to listen to next.
