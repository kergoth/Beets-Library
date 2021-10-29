"""Bits for my personal configuration and layout."""

from __future__ import division, absolute_import, print_function

import beets
from beets.library import DefaultTemplateFunctions
from beets.plugins import BeetsPlugin, find_plugins


_query = None

def query(name, item):
    return _query(name).match(item)

class KergothPlugin(BeetsPlugin):
    """Bits for my personal configuration and layout."""

    def __init__(self):
        super().__init__()

        self.register_listener('pluginload', self.pluginload)

    def pluginload(self):
        for plugin in find_plugins():
            if plugin.name == 'savedqueries':
                global _query
                self.query = _query = plugin.item_queries['query']
                break

        self.funcs = beets.plugins.template_funcs()
        self.the = self.funcs['the']
        self.replace = self.funcs['replace']
        self.replace_path = self.funcs['replace_path']
        self.bucket = self.funcs['bucket']
        self.asciify = DefaultTemplateFunctions.tmpl_asciify
        self.template_fields = {
            'artist_title': self.artist_title,
            'comp_filename': self.comp_filename,
            'by_artist': self.by_artist,
            'navigation_path': self.navigation_path,
        }

    # Utility functions

    def path(self, string):
        return self.replace_path('adjust_dap', string).replace('/', '\0')

    def loved(self, context):
        return 'loved' in context and context.loved

    def album_loved(self, context):
        album = context._cached_album
        return 'loved' in album and album.loved

    def is_loved(self, context):
        return (context.album_id and self.album_loved(context) ) or ( self.loved(context) and query('for_single_tracks', context) )

    # Path Components

    def artist_title(self, context):
        # artist_title: '%the{$path_artist} - $full_title'
        return f'{self.the(self.path_artist(context))} - {self.full_title(context)}'

    def disc_and_track_pre(self, context):
        if not context.track or (context.tracktotal and context.tracktotal == 1):
            return ''
        elif context.disctotal > 1:
            return '%02i.%02i - ' % (context.disc, context.track)
        else:
            return '%02i - ' % context.track

    def comp_filename(self, context):
        # comp_filename: '%if{$album,$disc_and_track_pre}%if{$comp,$path_artist - }$full_title'
        if context.album:
            prefix = self.disc_and_track_pre(context)
        else:
            prefix = ''

        if context.comp:
            prefix = f'{prefix}{self.path_artist(context)} - '

        return f'{prefix}{self.full_title(context)}'

    def tracksuffix(self, context):
        if 'advisory' in context:
            if context.advisory == 1:
                return ' (Explicit)'
            elif context.advisory == 2:
                return ' (Clean)'
            else:
                return ''
        else:
            return ''

    def path_artist(self, context):
        # path_artist: '%asciify{%replace{adjust_artist,$artist}}'
        return self.asciify(self.replace('adjust_artist', context.artist))

    def full_title(self, context):
        # full_title: '$title%if{$e_advisory,$explicit_or_clean}'
        return f'{context.title}{self.tracksuffix(context)}'

    def albumsuffix(self, context):
        # albumsuffix: '%if{$e_albumadvisory, (Explicit)}'
        if 'albumadvisory' in context and context.albumadvisory:
            return ' (Explicit)'
        else:
            return ''

    def albumartistname(self, context):
        # albumartistname: '%if{$comp,Compilations,%if{$classical,%if{$album_composer,$album_composer,$albumartist},$albumartist}}'
        if context.comp:
            return 'Compilations'
        else:
            if query('classical', context):
                album = context._cached_album
                if 'composer' in album and album.composer:
                    return album.composer
            return context.albumartist

    def artistname(self, context):
        # artistname: '%if{$classical,%if{$composer,$composer,$artist},$artist}'
        if query('classical', context):
            if 'composer' in context and context.composer:
                return context.composer
        return context.artist

    # Directories

    def albumartistdir(self, context):
        # albumartistdir: '%the{%asciify{%replace{adjust_artist,$albumartistname}}}'
        return self.the(self.asciify(self.replace('adjust_artist', self.albumartistname(context))))

    def artistdir(self, context):
        # artistdir: '%the{%asciify{%replace{adjust_artist,$artistname}}}'
        return self.the(self.asciify(self.replace('adjust_artist', self.artistname(context))))

    def albumonlydir(self, context, media=True):
        # albumonlydir: '%replace{adjust_album,%ifdef{$game,$game%ifdef{gamedisambig, [$gamedisambig]}%if{$album,$albumsuffix},%if{$album,$album%aunique{}$albumsuffix,Single Tracks}}}'
        if media and 'mediatitle' in context and context.mediatitle:
            media = f'{context.mediatitle}'
            if 'mediatitledisambig' in context:
                media += f' [{context.mediatitledisambig}]'
            if context.album:
                media += self.albumsuffix(context)
            return self.replace('adjust_media', media)
        else:
            if context.album:
                aunique = context._template_funcs()['aunique']
                return f'{context.album}{aunique()}{self.albumsuffix(context)}'
            else:
                return 'Single Tracks'

    def franchisedir(self, context):
        # franchisedir: '%the{%replace{adjust_franchise,$franchise} Franchise}'
        franchise = self.replace('adjust_franchise', context.franchise)
        return self.the(f'{franchise} Franchise')

    def albumdir(self, context, media=True):
        # albumdir: '%the{%ifdef{franchise,%path{$franchisedir,$albumonlydir},$albumonlydir}}'
        if 'franchise' in context and context.franchise:
            return self.the(f'{self.franchisedir(context)}/{self.albumonlydir(context)}')
        else:
            return self.the(self.albumonlydir(context, media))

    # Filesystem Layouts

    def bucket_by_album(self, context):
        # bucket_by_album: '%if{$for_single_tracks,%path{Single Tracks,$artist_title},%path{%bucket{$albumdir,alpha},$by_album}}'
        if query('for_single_tracks', context):
            return f'Single Tracks/{self.artist_title(context)}'
        else:
            bucket = self.bucket(self.albumdir(context), 'alpha')
            return f'{bucket}/{self.by_album(context)}'

    def bucket_by_label_flat(self, context):
        # bucket_by_label_flat: '%path{%bucket{$label,alpha},$label,$artist_title}'
        bucket = self.bucket(context.label, 'alpha')
        return f'{bucket}/{context.label}/{self.artist_title(context)}'

    def by_album(self, context, media=True):
        # by_album: '%path{$albumdir,$comp_filename}'
        return f'{self.albumdir(context, media)}/{self.comp_filename(context)}'

    def by_artist(self, context, media=True):
        # '%if{$for_single_tracks,%path{$n_artistdir,Single Tracks,$full_title},%path{$n_albumartistdir,$by_album}}'
        if query('for_single_tracks', context):
            return f'{self.artistdir(context)}/Single Tracks/{self.full_title(context)}'
        else:
            return f'{self.albumartistdir(context)}/{self.by_album(context, media)}'

    def bucket_by_artist(self, context, media=True):
        # bucket_by_artist: '%path{%bucket{%if{$for_single_tracks,$artistdir,$albumartistdir},alpha},$by_artist}'
        if query('for_single_tracks', context):
            bucketed = self.artistdir(context)
        else:
            bucketed = self.albumartistdir(context)
        return f'{self.bucket(bucketed, "alpha")}/{self.by_artist(context, media)}'

    # Full path

    def navigation_path(self, context):
        if query('non_music', context):
            # query:non_music: 'Non-Music/$genre/%pathfield{$by_artist}'
            return self.path(f'Non-Music/{context.genre}/{self.by_artist(context,  media=False)}')
        elif query('alt_to_listen', context):
            # query:alt_to_listen: 'To Listen/%pathfield{$by_album}'
            return self.path(f'To Listen/{self.by_album(context)}')
        elif self.is_loved(context):
            # 'query:is_loved query:sole_tracks': 'Loved/Single Tracks/$artist_title'
            # 'query:is_loved query:for_single_tracks': 'Loved/Single Tracks/$artist_title'
            # 'query:is_loved query:chiptune': 'Loved/Chiptunes/%pathfield{$by_album}'
            # 'query:is_loved query:alt_game': 'Loved/Games/%pathfield{$by_album}'
            # 'query:is_loved query:soundtrack': 'Loved/Soundtracks/%pathfield{$by_album}'
            # query:is_loved: 'Loved/Albums/%pathfield{$by_album}'
            if query('is_sole_track', context) or query('for_single_tracks', context):
                return self.path(f'Loved/Single Tracks/{self.artist_title(context)}')
            else:
                if query('chiptune', context):
                    subdir = 'Chiptunes'
                elif query('alt_game', context):
                    subdir = 'Games'
                elif query('soundtrack', context):
                    subdir = 'Soundtracks'
                else:
                    subdir = 'Albums'
                return self.path(f'Loved/{subdir}/{self.by_album(context)}')
        elif query('christmas_sole_tracks',  context):
            # query:christmas_sole_tracks: 'Christmas/Single Tracks/$artist_title'
            return self.path(f'Christmas/Single Tracks/{self.artist_title(context)}')
        elif query('christmas', context):
            # query:christmas: 'Christmas/%pathfield{$by_artist}'
            return self.path(f'Christmas/{self.by_artist(context,  media=False)}')
        elif query('classical_sole_tracks', context):
            # query:classical_sole_tracks: 'Classical/Single Tracks/$artist_title'
            return self.path(f'Classical/Single Tracks/{self.artist_title(context)}')
        elif query('classical', context):
            # query:classical: 'Classical/%pathfield{$by_artist}'
            return self.path(f'Classical/{self.by_artist(context,  media=False)}')
        elif query('chiptune_game', context):
            # query:chiptune_game: 'Chiptunes/Games/%pathfield{$bucket_by_album}'
            return self.path(f'Chiptunes/Games/{self.bucket_by_album(context)}')
        elif query('chiptune', context):
            # query:chiptune: 'Chiptunes/Music/%pathfield{$by_artist}'
            return self.path(f'Chiptunes/Music/{self.by_artist(context,  media=False)}')
        elif query('alt_game', context):
            # query:alt_game: 'Games/%pathfield{$bucket_by_album}'
            return self.path(f'Games/{self.bucket_by_album(context)}')
        elif query('alt_game_extra', context):
            # query:alt_game_extra: 'Games/Extras/%pathfield{$by_album}'
            return self.path(f'Games/Extras/{self.by_album(context)}')
        elif query('soundtrack', context):
            # query:soundtrack: 'Soundtracks/%pathfield{$by_album}'
            return self.path(f'Soundtracks/{self.by_album(context)}')
        elif query('sampler', context):
            # query:sampler: 'Samplers/%pathfield{$by_album}'
            return self.path(f'Samplers/{self.by_album(context,  media=False)}')
        elif query('is_sole_track', context):
            # query:sole_tracks: 'Music/Single Tracks/$artist_title'
            return self.path(f'Music/Single Tracks/{context.source}/{self.artist_title(context)}')
        elif query('by_label_flat', context):
            # query:by_label_flat: 'Music/%pathfield{$bucket_by_label_flat}'
            return self.path(f'Music/{self.bucket_by_label_flat(context)}')
        else:
            # default: 'Music/%pathfield{$bucket_by_artist}'
            return self.path(f'Music/{self.bucket_by_artist(context,  media=False)}')
