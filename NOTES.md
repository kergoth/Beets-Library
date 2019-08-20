# Beets usage notes

## Issues of note

Discogs and MusicBrainz differ in their use of the albumtype field. Discogs
has 'Single, Promo' for example, whereas MusicBrainz is lowercase and uses
a semicolon separator. The standard query style `albumtype:single` matches
both, but use of it in inline fields could be more irritating.

I think Discogs title caps differs from MusicBrainz, which leads to
inconsistency.

## Bugs to report

- `albumtotal` can't be queried as an int, it acts like a string. `albumtotal:1`
  will match '12', for example, and `tracktotal` doesn't work with album
  queries. I have to either use regexp queries or a `first_tracktotal` field
  which is `items[0].tracktotal`

### Bugs in Plugins

#### missing

- negative values for missing show up when `albumtotal` is zero, which makes it
  rather irritating to use at times due to how it converts to boolean

# Library TODO

Re-visit the tags on the Twisted Insurrection soundtrack. It seems discogs has
entries for it, but it's split into multiple volumes. Can I split the
soundtrack I downloaded into those volumes, or are later volumes cumulative,
and I have what would be volume 7? At the least, check the titles for sanity.

Sarathan Records Indie Sampler is on Discogs, but removes the record company
from the album name. "Indie Sampler" is not exactly very useful unless it also
sets the albumartist to Sarathan Records. See also ASIN B0045CPEKA

## Album Art

- Wrong / generated art on the Gunship album
