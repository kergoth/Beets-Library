from __future__ import division, absolute_import, print_function

from beets.plugins import BeetsPlugin


class FormatFieldsPlugin(BeetsPlugin):
    """Define new fields using format strings.

    Similar to inline, except we specify a format string, not code.
    """

    def __init__(self):
        super(FormatFieldsPlugin, self).__init__()

        self.config.add({
            'item_fields': {},
            'album_fields': {},
        })
        self.set_template_fields()

    def set_template_fields(self):
        for field, template in self.config['item_fields'].items():
            self._log.debug('adding item field {}', field)

            def apply(i, field=field, template=template):
                return self.apply_template(field, template.as_str(), i)
            self.template_fields[field] = apply

        for field, template in self.config['album_fields'].items():
            self._log.debug('adding album field {}', field)

            def apply(i, field=field, template=template):
                return self.apply_template(field, template.as_str(), i)
            self.album_template_fields[field] = apply

    def apply_template(self, field, template, model):
        return model.evaluate_template(template)
