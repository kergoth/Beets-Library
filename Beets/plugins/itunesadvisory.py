from __future__ import division, absolute_import, print_function

from beets import mediafile
from beets.plugins import BeetsPlugin


class ITunesAdvisoryPlugin(BeetsPlugin):
    def __init__(self):
        super(ITunesAdvisoryPlugin, self).__init__()

        # 1 == explicit, 2 == clean
        itunesadvisory_field = mediafile.MediaField(
            mediafile.MP3DescStorageStyle('ITUNESADVISORY'),
            mediafile.MP4StorageStyle('rtng', as_type=int),
            mediafile.StorageStyle('ITUNESADVISORY'),
            mediafile.ASFStorageStyle('ITUNESADVISORY'),
            out_type=int,
        )

        self.add_media_field('itunesadvisory', itunesadvisory_field)
