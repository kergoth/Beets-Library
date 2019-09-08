"""Record the most recent import via a flexible field `last_import`."""

from __future__ import division, absolute_import, print_function

from beets import config
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, print_
from beets.dbcore import types


class LastimportPlugin(BeetsPlugin):
    """Record the most recent import via a field."""

    album_types = {
        'last_import': types.BOOLEAN,
    }

    def __init__(self):
        super(LastimportPlugin, self).__init__()

        self.config.add({
            'album': False,
            'format': '',
            'path': False,
        })

        self.import_stages = [self.imported]
        self.register_listener('import_begin', self.clear_last_import)

    def commands(self):
        """Add the last-import command."""
        last_import = Subcommand('last-import',
                                 help=u'print the most recently imported items.')
        last_import.parser.add_all_common_options()
        last_import.func = self.last_import
        return [last_import]

    def last_import(self, lib, opts, args):
        """Print the most recently imported items."""
        self.config.set_args(opts)

        album = self.config['album'].get(bool)
        path = self.config['path'].get(bool)
        fmt = self.config['format'].get(str)

        if path:
            fmt = u'$path'
        elif not fmt:
            if album:
                fmt = u'$added ' + config['format_album'].get()
            else:
                fmt = u'$added ' + config['format_item'].get()

        query = lib.albums if album else lib.items
        for obj in query('last_import:1 added+'):
            print_(format(obj, fmt))

    def clear_last_import(self, session):
        """Clear existing last_import fields before the new import."""
        with session.lib.transaction():
            for album in session.lib.albums('last_import:1'):
                album['last_import'] = 0
                album.store('last_import')

            for item in session.lib.items('last_import:1'):
                item['last_import'] = 0
                item.store('last_import')

    def imported(self, session, task):
        if task.is_album:
            item = task.album
        else:
            item = task.item

        item['last_import'] = 1
        item.store('last_import')
