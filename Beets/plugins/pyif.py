"""
Python conditional template function.

For example:

    %pyif{int("$something") > 0 && int("$somethingelse") < 0,foo}

It's be nice to avoid the whole sometype("$foo") juggling, but it'd only be
possible to avoid that if there was a way to make a template function receive
the unexpanded value rather than the expanded, or pass the Item/Album to the
template function.
"""

from __future__ import division, absolute_import, print_function

from beets.plugins import BeetsPlugin


class PyIf(BeetsPlugin):
    def __init__(self):
        super(PyIf, self).__init__()
        self.template_funcs['pyif'] = self.tmpl_pyif

    def tmpl_pyif(self, condition, trueval, falseval=u''):
        if eval(condition):
            return trueval
        else:
            return falseval
