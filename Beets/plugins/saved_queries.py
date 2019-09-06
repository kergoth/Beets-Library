"""Support saved, named queries."""

from __future__ import division, absolute_import, print_function

from beets import config
from beets.library import parse_query_string, Item, Album
from beets.plugins import BeetsPlugin

from beets.dbcore import types
from beets.dbcore import Query


class SavedQuery(Query):
    model_name = 'invalid'

    def __init__(self, name):
        self.name = name
        queries = config[self.model_name + '_queries']
        self.query_string = queries[name].as_str()
        self.query, _ = parse_query_string(self.query_string, self.model)

    def clause(self):
        return self.query.clause()

    def match(self, item):
        return self.query.match(item)


class ItemSavedQuery(SavedQuery):
    model_name = 'item'
    model = Item


class AlbumSavedQuery(SavedQuery):
    model_name = 'album'
    model = Album


class SavedQueriesPlugin(BeetsPlugin):
    """Support saved, named queries.

    Also support creation of Item/Album boolean fields for the query. Do not
    query the fields, as the performance is not great. Use the `query:NAME`
    query syntax for queries, and use the fields for inspection or a format
    string.
    """

    def __init__(self):
        super(SavedQueriesPlugin, self).__init__()

        self.config.add({
            'add_fields': True,
        })

        config.add({
            'item_queries': {},
            'album_queries': {},
        })

        self._log.debug('adding named item query `query`')
        self._log.debug('adding named album query `album_query`')
        self.item_queries = {'query': ItemSavedQuery}
        self.album_queries = {'album_query': AlbumSavedQuery}
        if self.config['add_fields'].get():
            self.item_types = {}
            self.template_fields = {}
            for name in config['item_queries'].keys():
                self._log.debug('adding item field {}', name)
                self.item_types[name] = types.BOOLEAN
                self.template_fields[name] = lambda item, name=name: ItemSavedQuery(name).match(item)

            self.album_types = {}
            self.album_template_fields = {}
            for name in config['album_queries'].keys():
                self._log.debug('adding album field {}', name)
                self.album_types[name] = types.BOOLEAN
                self.album_template_fields[name] = lambda album, name=name: AlbumSavedQuery(name).match(album)
