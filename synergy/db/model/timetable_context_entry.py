__author__ = 'Bohdan Mushkevych'

from odm.document import BaseDocument
from odm.fields import StringField, ListField

TREE_NAME = 'tree_name'
TREE_CLASSNAME = 'tree_classname'
DEPENDENT_ON = 'dependent_on'
ENCLOSED_PROCESSES = 'enclosed_processes'
MX_PAGE = 'mx_page'
MX_NAME = 'mx_name'


class TimetableContextEntry(BaseDocument):
    """ Non-persistent model. Class presents single process tree (an atomic entry for the Timetable) """

    tree_name = StringField(TREE_NAME)
    tree_classname = StringField(TREE_CLASSNAME)
    dependent_on = ListField(DEPENDENT_ON)
    enclosed_processes = ListField(ENCLOSED_PROCESSES)
    mx_name = StringField(MX_NAME)
    mx_page = StringField(MX_PAGE)

    @property
    def key(self):
        return self.tree_name

    @key.setter
    def key(self, value):
        self.tree_name = value


def _timetable_context_entry(tree_name,
                             tree_classname,
                             enclosed_processes,
                             dependent_on=None,
                             mx_name=None,
                             mx_page=None):
    """ creates timetable context entry """
    assert enclosed_processes is not None and not isinstance(enclosed_processes, str)
    assert dependent_on is not None and not isinstance(dependent_on, str)

    timetable_entry = TimetableContextEntry()
    timetable_entry.tree_name = tree_name
    timetable_entry.tree_classname = tree_classname
    timetable_entry.enclosed_processes = enclosed_processes
    timetable_entry.dependent_on = dependent_on
    timetable_entry.mx_name = mx_name
    timetable_entry.mx_page = mx_page
    return timetable_entry
