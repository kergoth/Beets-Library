"""Bits for my personal configuration and layout."""

from __future__ import absolute_import, division, print_function

import os
from pathlib import Path
import re

import beets
from beets.library import DefaultTemplateFunctions
from beets.plugins import BeetsPlugin, find_plugins
from beets.ui import UserError


class KergothPlugin(BeetsPlugin):
    """Bits for my personal configuration and layout."""

    needed_plugins = ["bucket", "replacefunc", "savedqueries", "the"]

    def __init__(self):
        super().__init__()

        self.register_listener("pluginload", self.loaded)

    def loaded(self):
        found_plugins = set()
        for plugin in find_plugins():
            if plugin.name in self.needed_plugins:
                found_plugins.add(plugin.name)

            if plugin.name == "savedqueries":
                self.queryfunc = plugin.item_query

        for plugin_name in self.needed_plugins:
            if plugin_name not in found_plugins:
                raise UserError(
                    f"`{plugin_name}` plugin is required to use the `{self.name}` plugin"
                )

        self.savedqueries = FactoryDict(lambda name: self.queryfunc("query", name))
        self.album_queries = FactoryDict(lambda name: self.queryfunc("album_query", name))
        self.template_fields = {
            "extension": self.extension,
            "navigation_path": self.navigation_path,
        }

        self.funcs = beets.plugins.template_funcs()
        self.the = self.funcs["the"]
        self.replacefunc = self.funcs["replace"]
        self.bucket = self.funcs["bucket"]
        self.asciify = DefaultTemplateFunctions.tmpl_asciify

    # Utility functions
    def query(self, name, formatteditem):
        return self.savedqueries[name].match(formatteditem.item)

    def album_query(self, name, album):
        return self.album_queries[name].match(album)

    def path(self, string):
        return self.replacefunc("alt", string).replace("/", "\0")

    def album_loved(self, item):
        if item.album and item._cached_album:
            return item._cached_album.get("loved", False)
        return False

    def is_loved(self, item):
        return self.album_loved(item) or (
            item.get("loved", False) and self.query("for_single_tracks", item)
        )

    # Path Components

    def artist_title(self, item):
        return f"{self.the(self.filename_artist(item))} - {self.full_title(item)}"

    def disc_and_track_pre(self, item):
        if not item.track or (item.tracktotal and item.tracktotal == 1):
            return ""
        elif item.disctotal > 1:
            return "%02i.%02i - " % (item.disc, item.track)
        else:
            return "%02i - " % item.track

    def comp_filename(self, item):
        if item.album:
            prefix = self.disc_and_track_pre(item)
        else:
            prefix = ""

        if item.comp:
            prefix = f"{prefix}{self.filename_artist(item)} - "

        return f"{prefix}{self.full_title(item)}"

    def tracksuffix(self, item):
        if "advisory" in item:
            if item.advisory == 1:
                return " (Explicit)"
            elif item.advisory == 2:
                return " (Clean)"
        return ""

    def filename_artist(self, item):
        artist = item.artist_credit or item.artist
        return self.asciify(self.replacefunc("artist", artist))

    def full_title(self, item):
        return f"{item.title}{self.tracksuffix(item)}"

    def albumsuffix(self, item):
        if "albumadvisory" in item and item.albumadvisory == 1:
            return " (Explicit)"
        else:
            return ""

    def albumartistname(self, item):
        if item.comp:
            return "Compilations"
        else:
            if self.query("classical", item):
                album = item._cached_album
                if "composer" in album and album.composer:
                    return album.composer

            if "albumartists" in item and item.albumartists:
                return item.albumartists[0]
            else:
                return item.albumartist

    def artistname(self, item):
        if self.query("classical", item):
            if "composer" in item and item.composer:
                return item.composer

        if "artists" in item and item.artists:
            return item.artists[0]
        else:
            return item.artist

    # Directories

    def albumartistdir(self, item):
        return self.the(
            self.asciify(self.replacefunc("artist", self.albumartistname(item)))
        )

    def artistdir(self, item):
        return self.the(self.asciify(self.replacefunc("artist", self.artistname(item))))

    def labeldir(self, item):
        return self.the(self.asciify(item.label))

    def albumonlydir(self, item, media=True):
        if media and "mediatitle" in item and item.mediatitle:
            media = self.replacefunc("media", item.mediatitle)
            if "mediatitledisambig" in item:
                media += f" [{item.mediatitledisambig}]"
            if item.album:
                media += self.albumsuffix(item)
            return media
        else:
            if item.album:
                aunique = item._template_funcs()["aunique"]
                album = self.replacefunc("album", item.album)
                return f"{album}{aunique()}{self.albumsuffix(item)}"
            else:
                return "Single Tracks"

    def franchisedir(self, item):
        franchise = self.replacefunc("franchise", item.franchise)
        return self.the(f"{franchise} Franchise")

    def albumdir(self, item, media=True):
        return self.the(self.albumonlydir(item, media))

    # Filesystem Layouts
    def bucket_by_album(self, item, franchise=False):
        if self.query("for_single_tracks", item):
            return f"Single Tracks/{self.artist_title(item)}"
        else:
            if franchise and "franchise" in item and item.franchise:
                bucket = self.bucket(self.franchisedir(item), "alpha")
                return f"{bucket}/{self.by_album(item, franchise=True)}"
            else:
                bucket = self.bucket(self.albumdir(item), "alpha")
                return f"{bucket}/{self.by_album(item)}"

    def bucket_by_label_flat(self, item):
        bucket = self.bucket(item.label, "alpha")
        return f"{bucket}/{item.label}/{self.artist_title(item)}"

    def by_album(self, item, media=True, franchise=False):
        if self.query("for_single_tracks", item):
            return f"Single Tracks/{self.artist_title(item)}"
        elif "albumdir" in item and item.albumdir:
            return f"{item.item.albumdir}/{self.comp_filename(item)}"
        elif franchise:
            return f"{self.franchise_albumdir(item, media)}/{self.comp_filename(item)}"
        else:
            return f"{self.albumdir(item, media)}/{self.comp_filename(item)}"

    def franchise_albumdir(self, item, media=True):
        if "franchise" in item and item.franchise:
            return f"{self.the(self.franchisedir(item))}/{self.the(self.albumonlydir(item))}"
        else:
            return self.the(self.albumonlydir(item, media))

    def by_artist(self, item, media=True, split_samplers=False, label=False, franchise=False):
        if self.query("for_single_tracks", item) or (
            split_samplers and self.query("is_sampler", item)
        ):
            if label:
                dirname = self.labeldir(item)
            else:
                dirname = self.artistdir(item)
            return f"{dirname}/Single Tracks/{self.full_title(item)}"
        else:
            if label:
                dirname = self.labeldir(item)
            else:
                dirname = self.albumartistdir(item)
            return f"{dirname}/{self.by_album(item, media, franchise=franchise)}"

    def music_section(self, item, media=True):
        album = item._cached_album
        if album:
            if album.genre and self.album_query("separated_by_genre", album):
                genre = re.split(r"[/／ ;]", album.genre)[0]
                return f'{genre}/{self.by_artist(item, media)}'
        else:
            if item.genre and self.query("separated_by_genre", item):
                genre = re.split(r"[/／ ;]", item.genre)[0]
                return f'{genre}/{self.by_artist(item, media)}'

        if self.query("for_single_tracks", item):
            bucketed = self.artistdir(item)
        else:
            bucketed = self.albumartistdir(item)
        return f'{self.bucket(bucketed, "alpha")}/{self.by_artist(item, media)}'

    # Full path
    def extension(self, item):
        return Path(os.fsdecode(item.path)).suffix

    def navigation_path(self, item):
        item = FormattedItem(item)
        if self.query("non_music", item):
            return self.path(
                f"Non-Music/{item.genre}/{self.by_artist(item, media=False)}"
            )
        elif self.query("alt_to_listen", item):
            if self.query("by_label", item):
                return self.path(
                    f"To Listen/{self.by_artist(item, media=False, label=True)}"
                )
            elif self.query("is_sole_track", item) or self.query(
                "for_single_tracks", item
            ):
                return self.path(f"To Listen/Single Tracks/{self.artist_title(item)}")
            else:
                return self.path(f"To Listen/{self.by_artist(item, media=False)}")
        elif self.is_loved(item):
            if self.query("christmas_sole_tracks", item):
                return self.path(f"Loved/Christmas/Single Tracks/{self.artist_title(item)}")
            elif self.query("christmas", item):
                return self.path(f"Loved/Christmas/{self.by_album(item)}")
            elif self.query("classical_sole_tracks", item):
                return self.path(f"Loved/Classical/Single Tracks/{self.artist_title(item)}")
            elif self.query("classical", item):
                return self.path(f"Loved/Classical/{self.by_album(item)}")
            elif self.query("jazz_sole_tracks", item):
                return self.path(
                    f"Loved/Jazz/Single Tracks/{self.artist_title(item)}"
                )
            elif self.query("jazz", item):
                return self.path(f"Loved/Jazz/{self.by_album(item)}")
            elif (
                self.query("is_sole_track", item)
                or self.query("for_single_tracks", item)
                or self.query("is_sampler", item)
            ):
                return self.path(f"Loved/Single Tracks/{self.artist_title(item)}")
            else:
                if self.query("chiptune", item):
                    subdir = "Chiptunes"
                elif self.query("alt_game", item):
                    item.comp = False
                    subdir = "Video Game Soundtracks"
                elif self.query("alt_game_extra", item):
                    item.comp = False
                    subdir = "Video Game Music"
                elif self.query("soundtrack", item):
                    subdir = "Soundtracks"
                else:
                    subdir = "Albums"
                return self.path(f"Loved/{subdir}/{self.by_album(item)}")
        elif self.query("christmas_sole_tracks", item):
            return self.path(f"Christmas/Single Tracks/{self.artist_title(item)}")
        elif self.query("christmas", item):
            return self.path(f"Christmas/{self.by_artist(item, media=False)}")
        elif self.query("chiptune_game", item):
            item.comp = False
            return self.path(
                f"Chiptunes/Video Game Soundtracks/{self.bucket_by_album(item)}"
            )
        elif self.query("chiptune_game_extra", item):
            item.comp = False
            return self.path(f"Chiptunes/Video Game Music/{self.by_album(item)}")
        elif self.query("chiptune", item):
            return self.path(f"Chiptunes/Music/{self.by_artist(item, media=False)}")
        elif self.query("alt_game", item):
            item.comp = False
            return self.path(f"Video Game Soundtracks/{self.bucket_by_album(item, franchise=True)}")
        elif self.query("alt_game_extra", item):
            if self.query("by_label", item):
                return self.path(
                    f"Video Game Music/{self.by_artist(item, media=True, label=True)}"
                )
            elif self.query("is_sole_track", item) or self.query(
                "for_single_tracks", item
            ):
                return self.path(
                    f"Video Game Music/Single Tracks/{self.artist_title(item)}"
                )
            else:
                return self.path(
                    f"Video Game Music/{self.by_artist(item)}"
                )
        elif self.query("soundtrack", item):
            return self.path(f"Soundtracks/{self.by_album(item)}")
        elif self.query("classical_sole_tracks", item):
            return self.path(f"Classical/Single Tracks/{self.artist_title(item)}")
        elif self.query("classical", item):
            return self.path(f"Classical/{self.by_artist(item, media=False)}")
        elif self.query("jazz_sole_tracks", item):
            return self.path(f"Jazz/Single Tracks/{self.artist_title(item)}")
        elif self.query("jazz", item):
            return self.path(f"Jazz/{self.by_artist(item, media=False)}")
        elif self.query("sampler", item):
            return self.path(f"Samplers/{self.by_album(item, media=False)}")
        elif self.query("is_sole_track", item):
            return self.path(
                f"Music/Single Tracks/{item.source}/{self.artist_title(item)}"
            )
        elif self.query("by_label_flat", item):
            return self.path(f"Music/{self.bucket_by_label_flat(item)}")
        elif item.comp and not item.get("single_track", False):
            return self.path(f"Music/Compilations/{self.by_album(item, media=False)}")
        else:
            return self.path(f"Music/{self.music_section(item, media=False)}")


class FactoryDict(dict):
    """Call a factory function to populate on demand, caching it in the dict."""

    def __init__(self, factory, iterable=None, **kwargs):
        if iterable is not None:
            super().__init__(iterable)
        else:
            super().__init__(**kwargs)
        self.factory = factory

    def __missing__(self, name):
        self[name] = value = self.factory(name)
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
