"""Define saved format strings by storing them in fields."""

from __future__ import division, absolute_import, print_function

from beets import config
from beets.plugins import BeetsPlugin


class SavedFormatsPlugin(BeetsPlugin):
    """Define saved format strings by storing them in fields.

    Similar to inline, except we specify a format string, not code.
    """

    def __init__(self):
        super(SavedFormatsPlugin, self).__init__()

        config.add({
            'item_formats': {},
            'album_formats': {},
        })
        self.set_template_fields()

    def set_template_fields(self):
        for field, template in config['item_formats'].items():
            self._log.debug('adding item field {}', field)

            def apply(i, field=field, template=template):
                return self.apply_template(field, template.as_str(), i)
            self.template_fields[field] = apply

        for field, template in config['album_formats'].items():
            self._log.debug('adding album field {}', field)

            def apply(i, field=field, template=template):
                return self.apply_template(field, template.as_str(), i)
            self.album_template_fields[field] = apply

    def apply_template(self, field, template, model):
        return model.evaluate_template(template)
