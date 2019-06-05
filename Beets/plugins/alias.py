"""Support for beets command aliases, not unlike git.

By default, also checks $PATH for beet-* and makes those available as well.

Example:

    alias:
      from_path: True # Default
      aliases:
        singletons: ls singleton:true
        external-cmd-test: '!echo'
        sh-c-test: '!sh -c "echo foo bar arg1:$1, arg2:$2" sh-c-test'
"""

from __future__ import division, absolute_import, print_function

import glob
import os
import subprocess
import sys

from optparse import OptionParser, BadOptionError, AmbiguousOptionError

from beets import plugins
from beets import ui
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, print_
from beets.util import shlex_split


# VIa https://stackoverflow.com/a/9307174
class PassThroughOptionParser(OptionParser):
    """
    An unknown option pass-through implementation of OptionParser.

    When unknown arguments are encountered, bundle with largs and try again,
    until rargs is depleted.

    sys.exit(status) will still be called if a known argument is passed
    incorrectly (e.g. missing arguments or bad argument types, etc.)
    """

    def _process_args(self, largs, rargs, values):
        while rargs:
            try:
                OptionParser._process_args(self, largs, rargs, values)
            except (BadOptionError, AmbiguousOptionError) as exc:
                largs.append(exc.opt_str)


class AliasCommand(Subcommand):
    def __init__(self, alias, command, log=None, help=None):
        super(AliasCommand, self).__init__(alias, help=help or command, parser=PassThroughOptionParser(add_help_option=False, description=help or command))

        self.alias = alias
        self.command = command
        self.log = log

    def run_command(self, args=None):
        if args is None:
            args = []

        if self.command.startswith('!'):
            command = self.command[1:]
            argv = shlex_split(command) + args
        else:
            argv = ['beet'] + shlex_split(self.command) + args

        if self.log:
            self.log.debug('Running {}', subprocess.list2cmdline(argv))
        try:
            subprocess.check_call(argv)
        except subprocess.CalledProcessError as exc:
            if self.log:
                self.log.debug(u'command `%s` failed with %d' % (subprocess.list2cmdline(argv), exc.returncode))
            raise

    def func(self, lib, opts, args):
        try:
            self.run_command(args)
        except subprocess.CalledProcessError as exc:
            plugins.send('cli_exit', lib=lib)
            lib._close()
            sys.exit(exc.returncode)


class AliasPlugin(BeetsPlugin):
    """Support for beets command aliases, not unlike git."""

    def __init__(self):
        super(AliasPlugin, self).__init__()

        self.config.add({
            'from_path': True,
            'aliases': {},
        })

    def get_command(self, alias, command, help=None):
        """Create a Subcommand instance for the specified alias."""
        return AliasCommand(alias, command, log=self._log, help=help)

    def get_path_commands(self):
        """Create subcommands for beet-* scripts in $PATH."""
        for path in os.getenv('PATH', '').split(':'):
            cmds = glob.glob(os.path.join(path, 'beet-*'))
            for cmd in cmds:
                if os.access(cmd, os.X_OK):
                    command = os.path.basename(cmd)
                    alias = command[5:]
                    self._log.debug('adding {} external alias from PATH', command)
                    yield (alias, self.get_command(alias, '!' + command))

    def cmd_alias(self, lib, opts, args, commands):
        """Print the available alias commands."""
        for alias, command in sorted(commands.items()):
            print_(u'%s: %s' % (alias, command))

    def commands(self):
        """Add the alias commands."""
        if self.config['from_path'].get(bool):
            commands = dict(self.get_path_commands())
        else:
            commands = {}

        for alias in self.config['aliases'].keys():
            command = self.config['aliases'][alias].get()
            if alias in commands:
                raise ui.UserError(u'alias `%s` was specified multiple times' % alias)
            commands[alias] = self.get_command(alias, command)

        if 'alias' in commands:
            raise ui.UserError(u'alias `alias` is reserved for the alias plugin')

        alias = Subcommand('alias',
                           help=u'Print the available alias commands.')
        alias_commands = dict((a, c.command) for a, c in commands.items())
        alias.func = lambda lib, opts, args: self.cmd_alias(lib, opts, args, alias_commands)
        commands['alias'] = alias
        return commands.values()
