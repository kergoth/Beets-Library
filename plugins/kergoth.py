"""Bits for my personal configuration and layout."""

from __future__ import division, absolute_import, print_function

import beets
from beets.library import DefaultTemplateFunctions
from beets.plugins import BeetsPlugin, find_plugins
from beets.ui import UserError


class KergothPlugin(BeetsPlugin):
    """Bits for my personal configuration and layout."""

    def __init__(self):
        super().__init__()

        self.register_listener('pluginload', self.loaded)

    def loaded(self):
        needed_plugins = ['savedqueries', 'replacefunc', 'the', 'bucket']
        found_plugins = set()
        for plugin in find_plugins():
            if plugin.name in needed_plugins:
                found_plugins.add(plugin.name)

            if plugin.name == 'savedqueries':
                self.queryfunc = _query = plugin.item_queries['query']

        for plugin_name in needed_plugins:
            if plugin_name not in found_plugins:
                raise UserError(f'`{plugin_name}` plugin is required to use the `{self.name}` plugin')

        self.savedqueries = FactoryDict(lambda name: self.queryfunc(name))

        self.funcs = beets.plugins.template_funcs()
        self.the = self.funcs['the']
        self.replace = self.funcs['replace']
        self.bucket = self.funcs['bucket']
        self.asciify = DefaultTemplateFunctions.tmpl_asciify
        self.template_fields = {
            'navigation_path': self.navigation_path,
        }

    # Utility functions

    def query(self, name, formatteditem):
        return self.savedqueries[name].match(formatteditem.item)

    def path(self, string):
        return self.replace('alt', string).replace('/', '\0')

    def loved(self, item):
        return 'loved' in item and item.loved

    def album_loved(self, item):
        album = item._cached_album
        return 'loved' in album and album.loved

    def is_loved(self, item):
        return (item.album_id and self.album_loved(item) ) or ( self.loved(item) and self.query('for_single_tracks', item) )

    # Path Components

    def artist_title(self, item):
        # artist_title: '%the{$path_artist} - $full_title'
        return f'{self.the(self.path_artist(item))} - {self.full_title(item)}'

    def disc_and_track_pre(self, item):
        if not item.track or (item.tracktotal and item.tracktotal == 1):
            return ''
        elif item.disctotal > 1:
            return '%02i.%02i - ' % (item.disc, item.track)
        else:
            return '%02i - ' % item.track

    def comp_filename(self, item):
        # comp_filename: '%if{$album,$disc_and_track_pre}%if{$comp,$path_artist - }$full_title'
        if item.album:
            prefix = self.disc_and_track_pre(item)
        else:
            prefix = ''

        if item.comp:
            prefix = f'{prefix}{self.path_artist(item)} - '

        return f'{prefix}{self.full_title(item)}'

    def tracksuffix(self, item):
        if 'advisory' in item:
            if item.advisory == 1:
                return ' (Explicit)'
            elif item.advisory == 2:
                return ' (Clean)'
            else:
                return ''
        else:
            return ''

    def path_artist(self, item):
        # path_artist: '%asciify{%replace{artist,$artist}}'
        return self.asciify(self.replace('artist', item.artist))

    def full_title(self, item):
        # full_title: '$title%if{$e_advisory,$explicit_or_clean}'
        return f'{item.title}{self.tracksuffix(item)}'

    def albumsuffix(self, item):
        # albumsuffix: '%if{$e_albumadvisory, (Explicit)}'
        if 'albumadvisory' in item and item.albumadvisory:
            return ' (Explicit)'
        else:
            return ''

    def albumartistname(self, item):
        # albumartistname: '%if{$comp,Compilations,%if{$classical,%if{$album_composer,$album_composer,$albumartist},$albumartist}}'
        if item.comp:
            return 'Compilations'
        else:
            if self.query('classical', item):
                album = item._cached_album
                if 'composer' in album and album.composer:
                    return album.composer
            return item.albumartist

    def artistname(self, item):
        # artistname: '%if{$classical,%if{$composer,$composer,$artist},$artist}'
        if self.query('classical', item):
            if 'composer' in item and item.composer:
                return item.composer
        return item.artist

    # Directories

    def albumartistdir(self, item):
        # albumartistdir: '%the{%asciify{%replace{artist,$albumartistname}}}'
        return self.the(self.asciify(self.replace('artist', self.albumartistname(item))))

    def artistdir(self, item):
        # artistdir: '%the{%asciify{%replace{artist,$artistname}}}'
        return self.the(self.asciify(self.replace('artist', self.artistname(item))))

    def albumonlydir(self, item, media=True):
        # albumonlydir: '%replace{album,%ifdef{$game,$game%ifdef{gamedisambig, [$gamedisambig]}%if{$album,$albumsuffix},%if{$album,$album%aunique{}$albumsuffix,Single Tracks}}}'
        if media and 'mediatitle' in item and item.mediatitle:
            media = f'{item.mediatitle}'
            if 'mediatitledisambig' in item:
                media += f' [{item.mediatitledisambig}]'
            if item.album:
                media += self.albumsuffix(item)
            return self.replace('media', media)
        else:
            if item.album:
                aunique = item._template_funcs()['aunique']
                return f'{item.album}{aunique()}{self.albumsuffix(item)}'
            else:
                return 'Single Tracks'

    def franchisedir(self, item):
        # franchisedir: '%the{%replace{franchise,$franchise} Franchise}'
        franchise = self.replace('franchise', item.franchise)
        return self.the(f'{franchise} Franchise')

    def albumdir(self, item, media=True):
        # albumdir: '%the{%ifdef{franchise,%path{$franchisedir,$albumonlydir},$albumonlydir}}'
        if 'franchise' in item and item.franchise:
            return self.the(f'{self.franchisedir(item)}/{self.albumonlydir(item)}')
        else:
            return self.the(self.albumonlydir(item, media))

    # Filesystem Layouts

    def bucket_by_album(self, item):
        # bucket_by_album: '%if{$for_single_tracks,%path{Single Tracks,$artist_title},%path{%bucket{$albumdir,alpha},$by_album}}'
        if self.query('for_single_tracks', item):
            return f'Single Tracks/{self.artist_title(item)}'
        else:
            bucket = self.bucket(self.albumdir(item), 'alpha')
            return f'{bucket}/{self.by_album(item)}'

    def bucket_by_label_flat(self, item):
        # bucket_by_label_flat: '%path{%bucket{$label,alpha},$label,$artist_title}'
        bucket = self.bucket(item.label, 'alpha')
        return f'{bucket}/{item.label}/{self.artist_title(item)}'

    def by_album(self, item, media=True):
        # by_album: '%path{$albumdir,$comp_filename}'
        return f'{self.albumdir(item, media)}/{self.comp_filename(item)}'

    def by_artist(self, item, media=True):
        # '%if{$for_single_tracks,%path{$n_artistdir,Single Tracks,$full_title},%path{$n_albumartistdir,$by_album}}'
        if self.query('for_single_tracks', item):
            return f'{self.artistdir(item)}/Single Tracks/{self.full_title(item)}'
        else:
            return f'{self.albumartistdir(item)}/{self.by_album(item, media)}'

    def bucket_by_artist(self, item, media=True):
        # bucket_by_artist: '%path{%bucket{%if{$for_single_tracks,$artistdir,$albumartistdir},alpha},$by_artist}'
        if self.query('for_single_tracks', item):
            bucketed = self.artistdir(item)
        else:
            bucketed = self.albumartistdir(item)
        return f'{self.bucket(bucketed, "alpha")}/{self.by_artist(item, media)}'

    # Full path

    def navigation_path(self, item):
        item = FormattedItem(item)
        if self.query('non_music', item):
            # query:non_music: 'Non-Music/$genre/%pathfield{$by_artist}'
            return self.path(f'Non-Music/{item.genre}/{self.by_artist(item,  media=False)}')
        elif self.query('alt_to_listen', item):
            # query:alt_to_listen: 'To Listen/%pathfield{$by_album}'
            return self.path(f'To Listen/{self.by_album(item)}')
        elif self.is_loved(item):
            # 'query:is_loved query:sole_tracks': 'Loved/Single Tracks/$artist_title'
            # 'query:is_loved query:for_single_tracks': 'Loved/Single Tracks/$artist_title'
            # 'query:is_loved query:chiptune': 'Loved/Chiptunes/%pathfield{$by_album}'
            # 'query:is_loved query:alt_game': 'Loved/Games/%pathfield{$by_album}'
            # 'query:is_loved query:soundtrack': 'Loved/Soundtracks/%pathfield{$by_album}'
            # query:is_loved: 'Loved/Albums/%pathfield{$by_album}'
            if self.query('is_sole_track', item) or self.query('for_single_tracks', item):
                return self.path(f'Loved/Single Tracks/{self.artist_title(item)}')
            else:
                if self.query('chiptune', item):
                    subdir = 'Chiptunes'
                elif self.query('alt_game', item):
                    subdir = 'Games'
                elif self.query('soundtrack', item):
                    subdir = 'Soundtracks'
                else:
                    subdir = 'Albums'
                return self.path(f'Loved/{subdir}/{self.by_album(item)}')
        elif self.query('christmas_sole_tracks',  item):
            # query:christmas_sole_tracks: 'Christmas/Single Tracks/$artist_title'
            return self.path(f'Christmas/Single Tracks/{self.artist_title(item)}')
        elif self.query('christmas', item):
            # query:christmas: 'Christmas/%pathfield{$by_artist}'
            return self.path(f'Christmas/{self.by_artist(item,  media=False)}')
        elif self.query('classical_sole_tracks', item):
            # query:classical_sole_tracks: 'Classical/Single Tracks/$artist_title'
            return self.path(f'Classical/Single Tracks/{self.artist_title(item)}')
        elif self.query('classical', item):
            # query:classical: 'Classical/%pathfield{$by_artist}'
            return self.path(f'Classical/{self.by_artist(item,  media=False)}')
        elif self.query('chiptune_game', item):
            # query:chiptune_game: 'Chiptunes/Games/%pathfield{$bucket_by_album}'
            return self.path(f'Chiptunes/Games/{self.bucket_by_album(item)}')
        elif self.query('chiptune', item):
            # query:chiptune: 'Chiptunes/Music/%pathfield{$by_artist}'
            return self.path(f'Chiptunes/Music/{self.by_artist(item,  media=False)}')
        elif self.query('alt_game', item):
            # query:alt_game: 'Games/%pathfield{$bucket_by_album}'
            return self.path(f'Games/{self.bucket_by_album(item)}')
        elif self.query('alt_game_extra', item):
            # query:alt_game_extra: 'Games/Extras/%pathfield{$by_album}'
            return self.path(f'Games/Extras/{self.by_album(item)}')
        elif self.query('soundtrack', item):
            # query:soundtrack: 'Soundtracks/%pathfield{$by_album}'
            return self.path(f'Soundtracks/{self.by_album(item)}')
        elif self.query('sampler', item):
            # query:sampler: 'Samplers/%pathfield{$by_album}'
            return self.path(f'Samplers/{self.by_album(item,  media=False)}')
        elif self.query('is_sole_track', item):
            # query:sole_tracks: 'Music/Single Tracks/$artist_title'
            return self.path(f'Music/Single Tracks/{item.source}/{self.artist_title(item)}')
        elif self.query('by_label_flat', item):
            # query:by_label_flat: 'Music/%pathfield{$bucket_by_label_flat}'
            return self.path(f'Music/{self.bucket_by_label_flat(item)}')
        elif item.comp and not item.get('single_track', False):
            return self.path(f'Music/Compilations/{self.by_album(item,  media=False)}')
        else:
            # default: 'Music/%pathfield{$bucket_by_artist}'
            return self.path(f'Music/{self.bucket_by_artist(item,  media=False)}')


class FactoryDict(dict):
    """Call a factory function to populate on demand, caching it in the dict."""
    def __init__(self, factory, iterable=None, **kwargs):
        if iterable is not None:
            super().__init__(iterable)
        else:
            super().__init__(**kwargs)
        self.factory = factory

    def __missing__(self, name):
        self[name] =  value = self.factory(name)
        return value


class FormattedItem:
    """Use string values from the formatted item mapping."""
    def __init__(self, item):
        self.item = item
        self.formatted = item.formatted(for_path=True)

    def __contains__(self, name):
        return name in self.formatted

    def __getattr__(self, attr):
        value = getattr(self.item, attr)
        if isinstance(value, str):
            try:
                value = self.formatted[attr]
            except KeyError:
                raise AttributeError(attr)
        setattr(self, attr, value)
        return value

    def _template_funcs(self):
        return self.item._template_funcs()

    def get(self, field, default=None):
        return getattr(self, field, default)
