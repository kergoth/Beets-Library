from __future__ import division, absolute_import, print_function

import subprocess

from beets import ui, util
from beets.plugins import BeetsPlugin
from beets.ui.commands import PromptChoice


class ImportPicardPlugin(BeetsPlugin):
    def __init__(self):
        super(ImportPicardPlugin, self).__init__()

        self.register_listener('before_choose_candidate',
                               self.before_choose_candidate_listener)

    def before_choose_candidate_listener(self, session, task):
        if task.candidates:
            return [PromptChoice('p', 'Picard',
                                      self.importer_inspect_candidate)]

    def importer_inspect_candidate(self, session, task):
        paths = [util.syspath(item.path) for item in task.items]
        self.run_command(paths)
        return None

    def run_command(self, args=None):
        if args is None:
            args = []

        argv = ['beet', 'picard'] + args
        try:
            subprocess.check_call(argv)
        except subprocess.CalledProcessError as exc:
            raise ui.UserError(str(exc))
