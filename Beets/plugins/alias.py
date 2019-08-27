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

import confuse
import glob
import optparse
import os
import six
import subprocess
import sys

from beets import plugins
from beets import ui
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, print_
from beets.util import shlex_split

if sys.version_info >= (3, 3):
    from collections import abc
else:
    import collections as abc


class NoOpOptionParser(optparse.OptionParser):
    def parse_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        return [], args


class AliasCommand(Subcommand):
    def __init__(self, alias, command, log=None, help=None):
        super(AliasCommand, self).__init__(alias, help=help or command, parser=NoOpOptionParser(add_help_option=False, description=help or command))

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
            # Note that it's not currently viable to directly execute the
            # Subcommand instance. While we could get the list of subcommands
            # via plugins.commands() and ui.default_commands, we lack access
            # to the library object in this context, which is needed to run
            # the 'func' method.
            #
            # TODO: determine if we can get the global arguments and options
            # from the current cli instance and pass them back into this
            # external beet call, i.e. -v, -l LIBRARY, etc.
            argv = ['beet'] + shlex_split(self.command) + args

        if self.log:
            self.log.debug('Running {}', subprocess.list2cmdline(argv))
        try:
            subprocess.check_call(argv)
        except subprocess.CalledProcessError as exc:
            if self.log:
                self.log.debug(u'command `{0}` failed with {1}', subprocess.list2cmdline(argv), exc.returncode)
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
                    yield (alias, self.get_command(alias, '!' + command, u'Run external command `{0}`'.format(command)))

    def cmd_alias(self, lib, opts, args, commands):
        """Print the available alias commands."""
        for alias, command in sorted(commands.items()):
            print_(u'{0}: {1}'.format(alias, command))

    def commands(self):
        """Add the alias commands."""
        if self.config['from_path'].get(bool):
            commands = dict(self.get_path_commands())
        else:
            commands = {}

        for alias in self.config['aliases'].keys():
            if alias in commands:
                raise confuse.ConfigError(u'alias.aliases.{0} was specified multiple times'.format(alias))

            command = self.config['aliases'][alias].get()
            if isinstance(command, six.text_type):
                commands[alias] = self.get_command(alias, command)
            elif isinstance(command, abc.Mapping):
                command_text = command.get('command')
                if not command_text:
                    raise confuse.ConfigError(u'alias.aliases.{0}.command not found'.format(alias))
                help_text = command.get('help', command_text)
                commands[alias] = self.get_command(alias, command_text, help_text)
            else:
                raise confuse.ConfigError(u'alias.aliases.{0} must be a string or single-element mapping'.format(alias))

        if 'alias' in commands:
            raise ui.UserError(u'alias `alias` is reserved for the alias plugin')

        alias = Subcommand('alias',
                           help=u'Print the available alias commands.')
        alias_commands = dict((a, c.command) for a, c in commands.items())
        alias.func = lambda lib, opts, args: self.cmd_alias(lib, opts, args, alias_commands)
        commands['alias'] = alias
        return commands.values()
