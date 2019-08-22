from __future__ import division, absolute_import, print_function

from beets import config
from beets.library import parse_query_string, Item, Album
from beets.plugins import BeetsPlugin

from beets.dbcore import Query


class AliasQuery(Query):
    name = None
    config = config['alias_query']

    def __init__(self, alias):
        self.alias = alias
        config = self.config[self.name + '_queries']
        self.query_string = config[alias].as_str()
        self.query, _ = parse_query_string(self.query_string, self.model)

    def clause(self):
        return self.query.clause()

    def match(self, item):
        return self.query.match(item)


class ItemAliasQuery(AliasQuery):
    name = 'item'
    model = Item


class AlbumAliasQuery(AliasQuery):
    name = 'album'
    model = Album


class AliasQueryPlugin(BeetsPlugin):
    """Aliased queries support.

    Allow definition of named / aliased queries.
    """

    def __init__(self):
        super(AliasQueryPlugin, self).__init__()

        self.config.add({
            'item_queries': {},
            'album_queries': {},
        })

        if self.config['item_queries']:
            self.item_queries = {'alias': ItemAliasQuery}

        if self.config['album_queries']:
            self.album_queries = {'album_alias': AlbumAliasQuery}
