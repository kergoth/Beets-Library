# Beets usage notes

## Bugs to report

- 'albumtotal' can't be queried as an int, it acts like  string. albumtotal:1
  will match '12', for example, and 'tracktotal' doesn't work with album
  queries

### Plugins

#### missing

- negative values for missing show up when albumtotal is zero, which makes it
  rather irritating to use at times due to how it converts to boolean
