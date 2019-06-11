"""Run inline python code when beets events are fired."""

from __future__ import division, absolute_import, print_function

import ast
import confuse

from beets.plugins import BeetsPlugin


def _syntaxerror_offset(value, lineoffset):
    """Adjust the line number in a SyntaxError exception."""
    if lineoffset:
        msg, (efname, elineno, eoffset, badline) = value.args
        value.args = (msg, (efname, elineno + lineoffset, eoffset, badline))
        value.lineno = elineno + lineoffset


def compile_offset(source, filename='<string>', lineoffset=0):
    """Compile the python source and adjust its line numbers by lineoffset."""
    try:
        compiled = compile(source, filename, 'exec', ast.PyCF_ONLY_AST)
    except SyntaxError as exc:
        _syntaxerror_offset(exc, lineoffset)
        raise

    if lineoffset:
        ast.increment_lineno(compiled, lineoffset)

    return compile(compiled, filename, 'exec', dont_inherit=True)


def compile_func(source, name, argspec='', filename='<string>', lineoffset=0,
                 env=None):
    """Compile the python source, wrapped in a function definition."""
    # Adjust for 'def' line
    lineoffset -= 1

    code = source.rstrip().replace('\t', '    ')
    lines = ('    ' + line for line in code.split('\n'))
    code = '\n'.join(lines)
    defined = 'def {name}({argspec}):\n{body}'.format(name=name,
                                                      argspec=argspec,
                                                      body=code)
    compiled = compile_offset(defined, filename, lineoffset)

    if env is None:
        env = {}
    tmpenv = {}
    exec(compiled, env, tmpenv)
    return eval(name, env, tmpenv)


class InlineHookPlugin(BeetsPlugin):
    """Run inline python code when beets events are fired."""

    argspecs = {
        'after_write': 'item, path',
        'album_imported': 'lib, album',
        'albuminfo_received': 'info',
        'art_set': 'album',
        'before_item_moved': 'item, source',
        'cli_exit': 'lib',
        'database_change': 'lib, model',
        'import': 'lib, paths',
        'import_begin': 'session',
        'import_task_apply': 'session, task',
        'import_task_choice': 'session, task',
        'import_task_created': 'session, task',
        'import_task_files': 'session, task',
        'import_task_start': 'session, task',
        'item_copied': 'item, source',
        'item_hardlinked': 'item, source',
        'item_imported': 'lib, item',
        'item_linked': 'item, source',
        'item_moved': 'item, source',
        'item_removed': 'item',
        'library_opened': 'lib',
        'trackinfo_received': 'info',
        'write': 'item, path, tags',
    }

    def __init__(self):
        super(InlineHookPlugin, self).__init__()

        self.config.add({
            'hooks': []
        })

        inline_hooks = self.config['hooks'].get(list)

        for hook_index in range(len(inline_hooks)):
            hook = self.config['hooks'][hook_index]
            event = hook['event'].as_str()
            if event not in self.argspecs:
                raise confuse.ConfigError('inline_hook.hooks[{0}].event: `{1}` is not a handled event'.format(hook_index, event))
            handler = hook['handler'].as_str()
            # TODO: determine config value line number and use for lineoffset
            function = compile_func(handler, 'inline_hook_' + event, self.argspecs.get(event) or '')
            self.register_listener(event, function)
