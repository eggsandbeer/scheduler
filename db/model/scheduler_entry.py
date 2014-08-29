__author__ = 'Bohdan Mushkevych'

from db.model.base_model import *

PROCESS_NAME = 'process_name'
STATE = 'state'
INTERVAL = 'interval_seconds'
PIPELINE_NAME = 'pipeline_name'

STATE_ON = 'state_on'
STATE_OFF = 'state_off'


class SchedulerEntry(BaseModel):
    """ Class presents single configuration entry for the scheduler. """

    def __init__(self, document=None):
        super(SchedulerEntry, self).__init__(document)

    @property
    def key(self):
        return self.data[PROCESS_NAME]

    @key.setter
    def key(self, value):
        self.data[PROCESS_NAME] = value

    @property
    def process_name(self):
        return self.data[PROCESS_NAME]

    @process_name.setter
    def process_name(self, value):
        self.data[PROCESS_NAME] = value

    @property
    def interval(self):
        return self.data[INTERVAL]

    @interval.setter
    def interval(self, value):
        self.data[INTERVAL] = value

    @property
    def process_state(self):
        return self.data[STATE]

    @process_state.setter
    def process_state(self, value):
        if value not in [STATE_ON, STATE_OFF]:
            raise ValueError('incorrect state for process %r' % value)
        self.data[STATE] = value

    @property
    def state_machine_name(self):
        return self.data[PIPELINE_NAME]

    @state_machine_name.setter
    def state_machine_name(self, value):
        self.data[PIPELINE_NAME] = value