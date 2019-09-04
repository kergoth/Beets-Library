from beets import ui
from beets.plugins import BeetsPlugin, find_plugins


class SpotifyExplicitPlugin(BeetsPlugin):
    def commands(self):
        for plugin in find_plugins():
            if plugin.name == 'spotify':
                self.spotify = plugin
                break
        else:
            raise ui.UserError('spotify plugin is required')

        def explicits(lib, opts, args):
            results = self.spotify._match_library_tracks(lib, ui.decargs(args))
            if results:
                for track in results:
                    if track['explicit']:
                        title = track['name']
                        album = track['album']['name']
                        artist = track['artists'][0]['name']
                        tracknum = track['track_number']
                        url = track['external_urls']['spotify']
                        print('{} - {} - {} - {} - {}'.format(album, tracknum, artist, title, url))

        explicit_cmd = ui.Subcommand(
            'spotify-explicit', help=u''
        )
        explicit_cmd.parser.add_all_common_options()
        explicit_cmd.func = explicits
        return [explicit_cmd]
