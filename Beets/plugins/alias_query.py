from __future__ import division, absolute_import, print_function

import confuse

from beets import config, ui
from beets.library import parse_query_string, Item, Album
from beets.plugins import BeetsPlugin

from beets.dbcore import Query


class AliasQuery(Query):
    def __init__(self, alias):
        self.alias = alias

    def match(self, item):
        if isinstance(item, Item):
            try:
                query_string = self.item_aliases[self.alias]
            except KeyError:
                raise confuse.ConfigError(u'alias.item_queries.%s not found' % self.alias)
        elif isinstance(item, Album):
            try:
                query_string = self.album_aliases[self.alias]
            except KeyError:
                raise confuse.ConfigError(u'alias.album_queries.%s not found' % self.alias)
        else:
            raise ui.UserError('unable to handle non-Item/Album Models')

        query, parsed_sort = parse_query_string(query_string, item.__class__)
        return query.match(item)


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

        self.item_aliases, self.album_aliases = {}, {}
        for name in self.config['item_queries'].keys():
            query = self.config['item_queries'][name]
            self.item_aliases[name] = query.as_str()
        for name in self.config['album_queries'].keys():
            query = self.config['album_queries'][name]
            self.album_aliases[name] = query.as_str()

        class ConfiguredAliasQuery(AliasQuery):
            item_aliases = self.item_aliases
            album_aliases = self.album_aliases

        self.item_queries = {'alias': ConfiguredAliasQuery}
        self.album_queries = {'alias': ConfiguredAliasQuery}
