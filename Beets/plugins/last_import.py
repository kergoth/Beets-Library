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
        self.register_listener('import_task_created', self.import_task_created)

    def commands(self):
        """Add the last-import command."""
        last_import = Subcommand('last-import',
                                 help=u'print the most recently imported items.')
        last_import.parser.add_option('-a', '--album',
                                      action='store_true',
                                      help='match albums instead of tracks')
        last_import.parser.add_option('-p', '--path',
                                      action='store_true',
                                      help='print paths for matched items or albums')
        last_import.parser.add_option('-f', '--format',
                                      action='store',
                                      help='print with custom format')
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
                fmt = config['format_album'].get()
            else:
                fmt = config['format_item'].get()

        query = lib.albums if album else lib.items
        for obj in query('last_import:true'):
            print_(format(obj, fmt))

    def import_task_created(self, session, task):
        """Clear existing last_import fields before the new import."""
        with session.lib.transaction():
            for album in session.lib.albums('last_import:true'):
                album['last_import'] = False
                album.store('last_import')

            for item in session.lib.items('last_import:false'):
                item['last_import'] = False
                item.store('last_import')

    def imported(self, session, task):
        if task.is_album:
            item = task.album
        else:
            item = task.item

        item['last_import'] = True
        item.store('last_import')
