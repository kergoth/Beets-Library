"""Support the 'ITUNESADVISORY' tag for explicit/clean."""

from __future__ import division, absolute_import, print_function

from beets import mediafile
from beets.plugins import BeetsPlugin


class ITunesAdvisoryPlugin(BeetsPlugin):
    def __init__(self):
        super(ITunesAdvisoryPlugin, self).__init__()

        # This is supposed to be MP4-specific, as itunes will not
        # set it elsewhere, and mp3tag's tag mapping page indicates this, but it's
        # a useful field to be able to set in general. Of course, we could set it just
        # in beets database, not in the tags of non-mp4 files, or we could adopt a new
        # tag for this, but for now I'm using it across the board.
        self.config.add({
            'mp4_only': False,
        })

        if self.config['mp4_only'].get(bool):
            styles = [mediafile.MP4StorageStyle('rtng', as_type=int)]
        else:
            styles = [
                mediafile.MP3DescStorageStyle('ITUNESADVISORY'),
                mediafile.MP4StorageStyle('rtng', as_type=int),
                mediafile.StorageStyle('ITUNESADVISORY'),
                mediafile.ASFStorageStyle('ITUNESADVISORY'),
            ]

        # 1 == explicit, 2 == clean
        itunesadvisory_field = mediafile.MediaField(*styles, out_type=int)
        self.add_media_field('itunesadvisory', itunesadvisory_field)
