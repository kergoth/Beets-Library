"""Identify tracks which are the only ones we have by that artist.

The intention here is to move one-hit-wonders or random free tracks I've
acquired over the years out of the artist/album structure, as seeing thousands
of "albums" with one track each is not useful.
"""

from beets import library, plugins, ui
from beets.dbcore import types
from beets.dbcore.query import AndQuery, MatchQuery, OrQuery


class SoleTracks(plugins.BeetsPlugin):
    item_types = {
        "sole_track": types.BOOLEAN,
    }

    def __init__(self, name=None):
        super().__init__(name=name)

        self.config.add(
            {
                "artist_fields": "artist artist_credit artists",
                "check_fields": "artist artist_credit artists albumartist albumartist_credit",
                "check_query": "^comp:1",
                "check_single_track": True,
                "sections": "",
            }
        )

    def commands(self):
        list_cmd = ui.Subcommand(
            "list-sole-tracks",
            help="Identify tracks which are the only ones we have by that artist.",
            aliases=(
                "ls-sole-tracks",
                "sole-tracks",
            ),
        )
        list_cmd.parser.add_option(
            "-n",
            "--non-matching",
            help="List non-matching rather than matching tracks.",
            action="store_true",
        )
        list_cmd.parser.add_path_option()
        list_cmd.parser.add_format_option()
        list_cmd.func = self.list_command

        modify_cmd = ui.Subcommand(
            "modify-sole-tracks",
            help='Modify "sole_track" flexible field on tracks based on whether they are the only tracks by that artist.',
        )
        modify_cmd.parser.add_path_option()
        modify_cmd.parser.add_format_option()
        modify_cmd.func = self.modify_command
        return [list_cmd, modify_cmd]

    def list_command(self, lib, opts, args):
        self.handle_common_args(opts, args)

        for sole_track, items in self.list_sole_tracks(lib, self.base_query):
            if opts.non_matching and not sole_track:
                for item in items:
                    ui.print_(format(item))
            elif sole_track:
                ui.print_(format(items))

    def modify_command(self, lib, opts, args):
        self.handle_common_args(opts, args)

        for sole_track, item in self.list_sole_tracks(lib, self.base_query):
            existing_sole_track = item.get("sole_track", False)
            if existing_sole_track != sole_track:
                if not sole_track:
                    del item["sole_track"]
                else:
                    item["sole_track"] = True
                ui.show_model_changes(item, fields=("sole_track",))
                item.store()

    def handle_common_args(self, opts, args):
        self.config.set_args(opts)
        query = ui.decargs(args)
        if query:
            self.config["query"] = query
            self._log.debug(f'Using base query {" ".join(query)}')
            base_query, _ = library.parse_query_parts(query, library.Item)
        else:
            query = self.config["query"].as_str()
            self._log.debug(f"Using base query {query}")
            base_query, _ = library.parse_query_string(query, library.Item)
        self.base_query = base_query

    def list_sole_tracks(self, lib, base_query):
        check_single_track = self.config["check_single_track"].get(True)
        artist_fields = self.config["artist_fields"].as_str_seq()
        check_fields = self.config["check_fields"].as_str_seq()

        base_check_query = self.config["check_query"].as_str()
        self._log.debug(f"Using check query {base_check_query}")
        base_check_query, _ = library.parse_query_string(base_check_query, library.Item)

        seen_items = set()
        for section in self.config["sections"].as_str_seq():
            section_query, _ = library.parse_query_string(section, library.Item)

            self._log.info(f"Checking section: {section}")

            for item in lib.items(AndQuery([base_query, section_query])):
                if check_single_track:
                    if item.album and item._cached_album:
                        if len(item._cached_album.items()) > 1:
                            # Not a single track
                            continue

                if item.id in seen_items:
                    continue
                seen_items.add(item.id)

                artists = [getattr(item, a, None) for a in artist_fields]
                artists = sorted(set(a for a in artists if a))
                matches = []
                for artist in artists:
                    matches.extend(MatchQuery(field, artist) for field in check_fields)

                check_query = AndQuery(
                    [base_check_query, section_query, OrQuery(matches)]
                )
                self._log.debug(f'Checking for artists ({", ".join(artists)})')
                other_items = lib.items(check_query)
                other_items = [i for i in other_items if i.id != item.id]

                if other_items:
                    yield False, item
                    for other in other_items:
                        yield False, other
                else:
                    yield True, item
