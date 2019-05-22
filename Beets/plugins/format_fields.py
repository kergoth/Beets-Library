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

        for field, template in self.config['item_fields'].items():
            def apply(i, field=field, template=template):
                return self.apply_template(field, template.get(str), i, False)
            self.template_fields[field] = apply

        for field, template in self.config['album_fields'].items():
            def apply(i, field=field, template=template):
                return self.apply_template(field, template.get(str), i, True)
            self.album_template_fields[field] = apply

    def apply_template(self, field, template, model, is_album):
        return model.evaluate_template(template)
