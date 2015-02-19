__author__ = 'Bohdan Mushkevych'

from odm.fields import ObjectIdField
from db.model.raw_data import *
from synergy.db.model.base_model import *


class SiteStatistics(BaseModel):
    """
    class presents site statistics, such as number of visits per defined period or list of search keywords
    """

    db_id = ObjectIdField('_id', null=True)
    domain_name = StringField(DOMAIN_NAME)
    timeperiod = StringField(TIMEPERIOD)

    @BaseModel.key.getter
    def key(self):
        return self.domain_name, self.timeperiod

    @key.setter
    def key(self, value):
        self.domain_name = value[0]
        self.timeperiod = value[1]


    @property
    def number_of_pageviews(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if NUMBER_OF_PAGEVIEWS not in family_column:
            family_column[NUMBER_OF_PAGEVIEWS] = 0
        return family_column[NUMBER_OF_PAGEVIEWS]

    @number_of_pageviews.setter
    def number_of_pageviews(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[NUMBER_OF_PAGEVIEWS] = value

    @property
    def total_duration(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if TOTAL_DURATION not in family_column:
            family_column[TOTAL_DURATION] = 0
        return family_column[TOTAL_DURATION]

    @total_duration.setter
    def total_duration(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[TOTAL_DURATION] = value

    @property
    def number_of_visits(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if NUMBER_OF_VISITS not in family_column:
            family_column[NUMBER_OF_VISITS] = 0
        return family_column[NUMBER_OF_VISITS]

    @number_of_visits.setter
    def number_of_visits(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[NUMBER_OF_VISITS] = value

    @property
    def os(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if FAMILY_OS not in family_column:
            family_column[FAMILY_OS] = dict()
        return family_column[FAMILY_OS]

    @os.setter
    def os(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[FAMILY_OS] = value

    @property
    def browsers(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if FAMILY_BROWSERS not in family_column:
            family_column[FAMILY_BROWSERS] = dict()
        return family_column[FAMILY_BROWSERS]

    @browsers.setter
    def browsers(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[FAMILY_BROWSERS] = value

    @property
    def screen_res(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if FAMILY_SCREEN_RESOLUTIONS not in family_column:
            family_column[FAMILY_SCREEN_RESOLUTIONS] = dict()
        return family_column[FAMILY_SCREEN_RESOLUTIONS]

    @screen_res.setter
    def screen_res(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[FAMILY_SCREEN_RESOLUTIONS] = value

    @property
    def languages(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if FAMILY_LANGUAGES not in family_column:
            family_column[FAMILY_LANGUAGES] = dict()
        return family_column[FAMILY_LANGUAGES]

    @languages.setter
    def languages(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[FAMILY_LANGUAGES] = value

    @property
    def countries(self):
        family_column = self._get_column_family(FAMILY_STAT)
        if FAMILY_COUNTRIES not in family_column:
            family_column[FAMILY_COUNTRIES] = dict()
        return family_column[FAMILY_COUNTRIES]

    @countries.setter
    def countries(self, value):
        family_column = self._get_column_family(FAMILY_STAT)
        family_column[FAMILY_COUNTRIES] = value
