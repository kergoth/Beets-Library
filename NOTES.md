# Beets usage notes

In some cases, I'd like to avoid having to use inline python for performance
reasons, but in some cases it's actually faster than one would think,
particularly when `%if{}` is involved, as all `$` expansions have to be done
*before* the call out to the path format function, so slow fields end up
expanded even if the condition branch isn't used.

Sadly, inline python can't access fields of other plugins at this time, so
I can't use this fact to speed up certain fields. The `is_incomplete` field
for example doesn't need to evaluate `$incomplete` if we have a tracktotal, as
`missing` is less expensive in time, but both get expanded within the `%if{}`
block. I'd really like to see the ability to have path format functions which
receive their arguments unexpanded. This would open up a number of interesting
possibilities, not just for performance.

## Issues of note

Discogs and MusicBraircel du Longnz differ in their use of the albumtype field. Discogs
has 'Single, Promo' for example, whereas MusicBrainz is lowercase and uses
a semicolon separator. The standard query style `albumtype:single` matches
both, but use of it in inline fields could be more irritating. Further, the
separator can be / in some cases as well. I need to resolve the inconsistency
in tags with multiple values.

I think Discogs title caps also differs from MusicBrainz, which leads to
inconsistency.

## Bugs to report

### Bugs in Plugins

#### missing

- negative values for missing show up when `albumtotal` is zero, which makes it
  rather irritating to use at times due to how it converts to boolean
