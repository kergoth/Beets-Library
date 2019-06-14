"""Queries from beets and the beets documentation."""

from __future__ import division, absolute_import, print_function

from beets.dbcore import FieldQuery
from beets.dbcore.query import NoneQuery, TrueQuery
from beets.plugins import BeetsPlugin


# Via the beets documentation
class ExactMatchQuery(FieldQuery):
    """Match exact value."""

    @classmethod
    def value_match(cls, pattern, val):
        return pattern == val


# Via beets.dbcore
class AnyQuery(TrueQuery):
    """Match anything/everything."""

    def __init__(self, pattern):
        super(AnyQuery, self).__init__()


# Via beets.dbcore
class NoneFieldQuery(NoneQuery):
    """Match fields which aren't set / are None."""

    def __init__(self, field, _, fast=True):
        super(NoneFieldQuery, self).__init__(field, fast)

    def match(self, item):
        try:
            return item[self.field] is None
        except KeyError:
            return True


class ExistingQueriesPlugin(BeetsPlugin):
    item_queries = {'any': AnyQuery}
    album_queries = {'any': AnyQuery}

    def queries(self):
        return {
            '^': NoneFieldQuery,
            '@': ExactMatchQuery,
        }
