# -*- coding: utf-8 -*-
# This file is part of beets.
# Copyright 2016, Pedro Silva.
# Copyright 2017, Quentin Young.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""List existing tracks.
"""
from __future__ import division, absolute_import, print_function

import os
import musicbrainzngs

from musicbrainzngs.musicbrainz import MusicBrainzError
from collections import defaultdict
from beets.autotag import hooks
from beets.library import Item
from beets.plugins import BeetsPlugin
from beets.ui import decargs, print_, Subcommand
from beets import config
from beets.dbcore import types


def _existing_count(album):
    """Return number of existing items in `album`.
    """
    # We can't use len(album.items()) here, as the items list only contains
    # a single track when we're operating in item rather than album context,
    # which would result in existing being 1 whenever you do such a query.
    return len(album.items())
    # return len(os.listdir(album.item_dir()))


class ExistingPlugin(BeetsPlugin):
    """List existing tracks
    """

    album_types = {
        'existing': types.INTEGER,
    }

    def __init__(self):
        super(ExistingPlugin, self).__init__()

        self.album_template_fields['existing'] = _existing_count
