"""
Path format function to apply the specified set of replacements to a path.

This can be used to apply replacements only to the alternative library created
by beets-alternatives, for example, while leaving the original library alone.

Usage:

  foo_replace:
    Foo: Bar

  paths:
    default: '%replace{foo_replace,$album/$track - $artist - $title}'
"""

from __future__ import division, absolute_import, print_function

import confuse
import functools
import re

from beets import config, util
from beets.ui import UserError
from beets.plugins import BeetsPlugin


class ReplacePlugin(BeetsPlugin):
    def __init__(self):
        super(ReplacePlugin, self).__init__()
        self.template_funcs['replace'] = _tmpl_replace


def _tmpl_replace(config_path, path):
    replacements = get_replacements(config_path)
    return util.sanitize_path(path, replacements)


# Copied with tweak from beets itself
def get_replacements(config_path):
    replacements = []
    lookup = functools.reduce(lambda x, y: x[y], config_path.split("."), config)
    if not lookup:
        raise confuse.ConfigError(u'Failed to look up {0}'.format(config_path))

    for pattern, repl in lookup.get(dict).items():
        repl = repl or ''
        try:
            replacements.append((re.compile(pattern), repl))
        except re.error:
            raise UserError(
                u'malformed regular expression in replace: {0}'.format(
                    pattern
                )
            )
    return replacements
