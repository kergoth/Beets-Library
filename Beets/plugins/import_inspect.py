"""Inspect candidate changes when importing.

Add a command to inspect candidate changes and has an option to automatically
inspect the changes when the user selects Apply, and will prompt to continue
when timid.
"""

from __future__ import division, absolute_import, print_function

from beets import autotag, config, importer, library, ui
from beets.plugins import BeetsPlugin
from beets.ui.commands import PromptChoice


def new_item(i):
    ni = library.Item()
    ni.update(i)
    return ni


class ImportInspectPlugin(BeetsPlugin):
    def __init__(self):
        super(ImportInspectPlugin, self).__init__()

        self.config.add({
            'on_apply': True,
            'field_whitelist': '',
            'field_blacklist': '',
        })

        self.album_fields = set(library.Album.item_keys)
        self.nonalbum_fields = library.Item._media_tag_fields.difference(self.album_fields)

        self.whitelist = self.config['field_whitelist'].as_str_seq()
        if self.whitelist:
            self.album_fields = self.album_fields.intersection(self.whitelist)
            self.nonalbum_fields = self.nonalbum_fields.intersection(self.whitelist)

        self.blacklist = self.config['field_blacklist'].as_str_seq()
        if self.blacklist:
            self.album_fields = self.album_fields.difference(self.blacklist)
            self.nonalbum_fields = self.nonalbum_fields.difference(self.blacklist)

        self.all_fields = list(sorted(self.album_fields | self.nonalbum_fields))
        self.album_fields = list(sorted(self.album_fields))
        self.nonalbum_fields = list(sorted(self.nonalbum_fields))

        self.register_listener('before_choose_candidate',
                               self.before_choose_candidate_listener)

        if self.config['on_apply'].get():
            self.register_listener('import_task_choice',
                                   self.import_task_choice_listener)

    def before_choose_candidate_listener(self, session, task):
        if task.candidates:
            return [PromptChoice('n', 'iNspect changes',
                                      self.importer_inspect_candidate)]

    def importer_inspect_candidate(self, session, task):
        # Prompt the user for a candidate.
        sel = ui.input_options([], numrange=(1, len(task.candidates)))
        match = task.candidates[sel - 1]

        self.show_changes(session.lib, task, match)
        return None

    def import_task_choice_listener(self, session, task):
        if task.apply:
            if config['import']['quiet'].get():
                return

            changes = self.show_changes(session.lib, task)

            # Only prompt when timid
            if 'timid' in self.config:
                timid = self.config['timid'].get(bool)
            else:
                timid = config['import']['timid'].get()

            if not changes or not timid:
                return

            if not ui.input_yn(u'Continue to apply these changes (Y/n)?'):
                task.set_choice(importer.action.SKIP)

    def show_changes(self, lib, task, match=None):
        if match is None:
            match = task.match

        changes = False
        if task.is_album:
            newmapping = {new_item(item): track_info for item, track_info in match.mapping.items()}
            autotag.apply_metadata(match.info, newmapping)

            # olditems[0].get_album() isn't working, create our own to compare
            olditems = list(match.mapping.keys())
            oldvalues = dict((key, olditems[0][key]) for key in self.album_fields)
            oldalbum = library.Album(lib, **oldvalues)

            newitems = list(newmapping.keys())
            values = dict((key, newitems[0][key]) for key in self.album_fields)
            album = library.Album(lib, **values)

            album_changes = ui.show_model_changes(album, oldalbum, self.album_fields)
            if album_changes:
                changes = True

            new_by_info = {track_info: item for item, track_info in newmapping.items()}
            for item, track_info in match.mapping.items():
                newitem = new_by_info[track_info]
                item_changes = ui.show_model_changes(newitem, item, self.nonalbum_fields)
                if item_changes:
                    changes = True
        else:
            fakeitem = new_item(task.item)
            autotag.apply_item_metadata(fakeitem, match.info)
            changes = ui.show_model_changes(fakeitem, task.item, self.all_fields)

        return changes
