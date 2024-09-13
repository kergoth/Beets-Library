# Beets-Library

My personal beets configuration and scripts

## Terminology

In my library and configuration, a `sole track` is a case where I only have a single track by that artist in my library. I like to separate these to allow tracks where I have other works by that artist to be placed in the same location as the other tracks and albums by that artist, rather than in my `single tracks` folder.
A `single track` is a case where I only have one track from that album.

## Flexible Fields

My library utilizes various flexible fields.

The `loved` field is used at both item and track level to bring those items up to the top-level in my media player path formats for easier navigation to the songs and albums I listen to most often. I may rename this field in the future.

- `disliked`: Music I actively dislike but don't yet want to remove from the library.
- `hidden`: Music I don't want to see in my browseable library, but don't want to remove.
- `loved`: This field is used at both album and track level to hoist those items up to the root level in my media player path formats for easier navigation to items I play often.
- `to_listen`: Music I'd like to listen to.
- `avmedia`: Media type. Current expected values: Video Games, TV, Movies, Performances, Musicals, Anime, Documentaries.
- `mediatitle`: The name of the media this music is about. This may be for a soundtrack, but could also be for albums inspired by that game.
- `mediatitledisambig`: This string disambiguates cases where multiple albums reference the same media. In-game, score, orchestral, inspired by, etc.
- `franchise`: The media franchise this music references.

- `single_track`: Boolean field which indicates that a track should be placed with the Single Tracks sections of my browseable library, rather than kept in the album folder. This can be set manually when I want to hoist tracks from incomplete albums or singles out, rather than having album folders with single tracks. This is set automatically for imported albums which only have one track.
- `sole_track`: Boolean field which indicates that a track is a sole track. A sole track is a single track which is placed outside the artist folder, since it's the only track I have by that artist, whereas single tracks which are not sole tracks are placed in a `Single Tracks` folder within the artist folder. This field is normally not set manually, but by the soletracks plugin command `modify-sole-tracks`.

## Genre

I currently lack a cohesive genre system for my library. As such, the assigned genres are currently a bit of a mess. There are a small number of genres I use consistently. For non-music tracks, for example, the genre is used in my browseable layout for my digital audio player, so I use genres there: Background, Book, Comedy, Game, Meditations, Speech. The Comedy genre is also used in the music as well. The Classical, Christmas, and Chiptune genres are also used for browseable sections. Synthwave is a genre I have manually assigned and used in playlist generation. The genre is not used for media type, as that is stored in the avmedia field.

## Music and Exceptions

Generally I keep albums together, and only split up samplers. For example, this means that marking a track within an album as loved, but not marking the album as loved will not result in moving the track in my browseable layout to Loved as this would break up the album. The only current exceptions to this are:

- Smooth by Santana. I don't love the rest of the album, but I do love the track, so I explicitly set single_track=true on this track, which hoists it out of the album into the Single Tracks section.
- Techno Syndrome ('97 Mix*) by The Immortals. This mix is unavailable anywhere else, but the other tracks on this album are in the existing Mortal Kombat soundtracks, so I don't need to play them via this album. I've set single_track=true on this track to hoist it out of the album into the Single Tracks section.

## Reference

### Implicit or Non-Obvious Behavior

#### Path Formats

> As a convenience, however, beets allows $albumartist to fall back to the value for $artist and vice-versa if one tag is present but the other is not.

#### Queries

> For multi-valued tags (such as artists or albumartists), a regular expression search must be used to search for a single value within the multi-valued tag.

#### Sorting

> The artist and albumartist keys are special: they attempt to use their corresponding artist_sort and albumartist_sort fields for sorting transparently (but fall back to the ordinary fields when those are empty).
>
> Note that when sorting by fields that are not present on all items (such as flexible fields, or those defined by plugins) in ascending order, the items that lack that particular field will be listed at the beginning of the list.

### Commands

- `beet tls` will list in a table format.
- `beet lslimit --head=10` will list a limited number of items. Coupled with `added-`, this will show a limited number of the most recent additions to the library. Alternatively, `beet ls added- "limit:<10"` does the same.
- `beet lastgenre` to set genres on music from last.fm. This requires manual review, and may well require further tweaking of genre-whitelist.txt and genres-tree.yaml. Better yet, I intend to drop it in favor of whatlastgenre, but it'll do for now.
- `beet wlg` to set genre from discogs, etc. This still requires review.
- `beet mbsync` will update from musicbrainz, but often requires manual review to correct bits that were fixed at import time. I should fix `modifyonimport` to also apply on `mbsync`.

### Query Prefixes

#### Fields

- `=` is for a case-sensitive exact match
- `~` is for a case-insensitive exact match
- `:` is for a regular expression match
- `#` is for a bare ASCII match
- `*` is for a fuzzy match
- `%` is for a set/non-NULL match
- `^` is for an unset/NULL match
- `@` is for an empty string match

#### Global

- `<` is limit to N entries. I.e. `<10` gives you ten entries

### Other

- [Rehoming an existing database?](https://github.com/beetbox/beets/issues/1598) Shows how to change the library paths hardcoded in the library db after the fact:
  ```sql
  UPDATE items
  SET "path" = CAST(REPLACE(CAST("path" AS TEXT), '/Volumes/SD/Music Library/Library/', '/Volumes/Data/Music Library/Library/') AS BLOB);

  UPDATE albums
  SET "artpath" = CAST(REPLACE(CAST("artpath" AS TEXT), '/Volumes/SD/Music Library/Library/', '/Volumes/Data/Music Library/Library/') AS BLOB);
  ```
