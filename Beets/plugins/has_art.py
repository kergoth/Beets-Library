"""Add a field to indicate whether an item/album has art embedded."""

from __future__ import division, absolute_import, print_function

from beets import art
from beets.plugins import BeetsPlugin
from beets.dbcore import types
from beets.dbcore.query import FieldQuery


class ItemArtQuery(FieldQuery):
    def match(self, item):
        return bool(art.get_art(self._log, item))


class AllItemsArtQuery(FieldQuery):
    def match(self, album):
        return all(art.get_art(self._log, item) for item in album.items())


class HasArtPlugin(BeetsPlugin):
    def __init__(self):
        super(HasArtPlugin, self).__init__()
        self.item_types = {'has_embedded_art': types.BOOLEAN}
        self.album_types = {'all_tracks_have_art': types.BOOLEAN}

        class PluginItemArtQuery(ItemArtQuery):
            pass
        PluginItemArtQuery._log = self._log

        class PluginAllItemsArtQuery(AllItemsArtQuery):
            pass
        PluginAllItemsArtQuery._log = self._log

        self.item_queries = {'has_embedded_art': PluginItemArtQuery}
        self.album_queries = {'all_tracks_have_art': PluginAllItemsArtQuery}
