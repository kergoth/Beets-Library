from __future__ import division, absolute_import, print_function

from beets.dbcore import FieldQuery
from beets.plugins import BeetsPlugin


# Copied from beets.dbcore with two additions of 'not'
class NotNoneQuery(FieldQuery):
    """A query that checks whether a field is not null."""

    def col_clause(self):
        return self.field + " IS NOT NULL", ()

    def match(self, item):
        try:
            return item[self.field] is not None
        except KeyError:
            return False

    def __repr__(self):
        return "{0.__class__.__name__}({0.field!r}, {0.fast})".format(self)


class OtherQueriesPlugin(BeetsPlugin):
    def queries(self):
        return {
            '%': NotNoneQuery,
        }
