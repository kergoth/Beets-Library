# Do the same calculation as absubmit, but run it only against non-musicbrainz
# tracks, since absubmit/acousticbrainz only handle musicbrainz tracks, and
# store the lowlevel values rather than submitting them.

import confuse
import json
import os
import tempfile
import subprocess

from beets import ui, util, config
from beets.plugins import BeetsPlugin, find_plugins
from beetsplug import acousticbrainz


class ABCalcPlugin(BeetsPlugin):
    supported_extensions = ['.mp3', '.ogg', '.oga', '.flac', '.mp4', '.m4a', '.m4r',
                            '.m4b', '.m4p', '.aac', '.wma', '.asf', '.mpc', '.wv',
                            '.spx', '.tta', '.3g2', '.aif', '.aiff', '.ape']

    def __init__(self):
        super(ABCalcPlugin, self).__init__()

        self.supported_extensions = [util.bytestring_path(ext) for ext in list(self.supported_extensions)]

        self.config.add({
            'force': False,
            'auto': False,
        })

        try:
            self.extractor = config['absubmit']['extractor'].as_str()
        except confuse.ConfigError:
            self.extractor = None

        if self.extractor:
            self.extractor = util.normpath(self.extractor)
            # Expicit path to extractor
            if not os.path.isfile(self.extractor):
                raise ui.UserError(
                    u'Extractor command does not exist: {0}.'.
                    format(self.extractor)
                )
        else:
            # Implicit path to extractor, search for it in path
            self.extractor = 'streaming_extractor_music'

        self.abscheme = dict(acousticbrainz.ABSCHEME)
        del self.abscheme['highlevel']

        try:
            self.tags = config['acousticbrainz']['tags'].as_str_seq()
        except confuse.ConfigError:
            self.tags = None

        if self.config['auto']:
            self.register_listener('import_task_files',
                                   self.import_task_files)

    def commands(self):
        cmd = ui.Subcommand(
            'abcalc',
            help=u'calculate and store lowlevel AcousticBrainz analysis for non-MusicBrainz tracks'
        )
        cmd.parser.add_option(
            u'-f', u'--force', dest='force_recalc',
            action='store_true', default=False,
            help=u're-calculate data when already present'
        )

        def func(lib, opts, args):
            items = lib.items(ui.decargs(args))
            self._get_info(items, ui.should_write(),
                           opts.force_recalc or self.config['force'])

        cmd.func = func
        return [cmd]

    def import_task_files(self, session, task):
        self._get_info(task.imported_items(), False, True)

    def _get_info(self, items, write, force):
        self.absubmit, self.acousticbrainz = None, None

        for plugin in find_plugins():
            if plugin.name == 'absubmit':
                self.absubmit = plugin
            elif plugin.name == 'acousticbrainz':
                self.acousticbrainz = plugin

        if not self.absubmit or not self.acousticbrainz:
            raise ui.UserError('absubmit and acousticbrainz are required for this plugin')

        def func(item):
            return self.analyze(item, write, force)
        util.par_map(func, self.included_items(items, force))

    def included_items(self, items, force):
        for item in items:
            _, ext = os.path.splitext(item.path)
            if ext not in self.supported_extensions:
                self._log.debug(u'skipping item {} as {} files are unsupported', item, ext)
                continue

            if getattr(item, 'mb_trackid', None):
                self._log.debug(u'skipping item {} as it has mb_trackid. use acousticbrainz or absubmit instead', item)
                continue
            elif not force and (not self.tags or 'bpm' in self.tags):
                if getattr(item, 'bpm', 0):
                    self._log.debug(u'skipping item {} as it has bpm. set force to override', item)
                    continue
            yield item

    def get_extractor_data(self, item):
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.close()

            args = [self.extractor, util.syspath(item.path), tmpfile.name]
            try:
                util.command_output(args)
            except subprocess.CalledProcessError as exc:
                self._log.warning(u'{} "{}" "{}" exited with status {}', self.extractor, util.displayable_path(item.path), tmpfile.name, exc.returncode)
                return

            with open(tmpfile.name, 'rb') as tmp_file:
                return json.load(tmp_file)

    def analyze(self, item, write, force):
        self._log.info(u'getting data for: {0}', item)

        data = self.get_extractor_data(item)
        if not data:
            return

        for attr, val in self.acousticbrainz._map_data_to_scheme(data, self.abscheme):
            if not self.tags or attr in self.tags:
                if not force:
                    if getattr(item, attr, None):
                        self._log.debug(u'attribute {} of {} already set, skipping',
                                        attr,
                                        item)
                        continue

                self._log.debug(u'attribute {} of {} set to {}',
                                attr,
                                item,
                                val)
                setattr(item, attr, val)
            else:
                self._log.debug(u'skipping attribute {} of {}'
                                u' (value {}) due to config',
                                attr,
                                item,
                                val)
        item.store()
        if write:
            item.try_write()
