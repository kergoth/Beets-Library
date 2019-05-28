from __future__ import division, absolute_import, print_function

from beets.plugins import BeetsPlugin

class PyIf(BeetsPlugin):
    def __init__(self):
        super(PyIf, self).__init__()
        self.template_funcs['pyif'] = self.tmpl_pyif

    @staticmethod
    def tmpl_pyif(condition, trueval, falseval=u''):
        if eval(condition):
            return trueval
        else:
            return falseval
