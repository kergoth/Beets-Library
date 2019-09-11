"""Specify fields from set_fields to also be applied to skipped items on reimport."""

from __future__ import division, absolute_import, print_function

from beets import config, dbcore
from beets.dbcore import types
from beets.util import displayable_path
from beets.plugins import BeetsPlugin


class ReimportSkippedFieldsPlugin(BeetsPlugin):
    def __init__(self):
        super(ReimportSkippedFieldsPlugin, self).__init__()

        self.config.add({
            'set_fields': '',
        })
        self.set_fields = self.config['set_fields'].as_str_seq()

        self.register_listener('import_task_choice', self.import_task_choice)

    def import_task_choice(self, session, task):
        reimporting = config['import']['library'].get()
        if reimporting and task.skip:
            self.mark_items(session, task, task.items)

    def mark_items(self, session, task, items):
        fields = self.fields()
        marked = set()
        for item in items:
            if not item.id:
                # Same logic as used by `record_replaced` in `ImportTask` in beets.importer
                old_items = list(session.lib.items(
                    dbcore.query.BytesQuery('path', item.path)
                ))
                item = old_items[0]

            if task.is_album:
                album = item.get_album()
                if album:
                    for field, value in fields:
                        self._log.debug(u'Set field {1}={2} for {0}', displayable_path(album.path), field, value)
                        album[field] = value
                    marked.add(album)
                break
            else:
                for field, value in fields:
                    self._log.debug(u'Set field {1}={2} for {0}', displayable_path(item.path), field, value)
                    item[field] = value
                marked.add(item)

        with session.lib.transaction():
            for item in marked:
                item.store()

    def fields(self):
        for field, view in config['import']['set_fields'].items():
            if field in self.set_fields:
                value = view.get()
                yield field, value
