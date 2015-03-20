__author__ = 'Bohdan Mushkevych'

import unittest

from synergy.conf import settings
from tests.base_fixtures import wind_the_time, wind_actual_timeperiod
from constants import TOKEN_SITE, PROCESS_SITE_YEARLY, PROCESS_SITE_MONTHLY, PROCESS_SITE_DAILY, PROCESS_SITE_HOURLY
from synergy.system import time_helper
from synergy.system.time_qualifier import *
from synergy.scheduler.tree import MultiLevelTree


class TestThreeLevelTree(unittest.TestCase):
    def setUp(self):
        self.initial_actual_timeperiod = time_helper.actual_timeperiod
        self.initial_synergy_start_time = settings.settings['synergy_start_timeperiod']
        self.tree = MultiLevelTree(process_names=[PROCESS_SITE_YEARLY, PROCESS_SITE_MONTHLY, PROCESS_SITE_DAILY],
                                   mx_name=TOKEN_SITE, mx_page='some_mx_page')

    def tearDown(self):
        del self.tree
        settings.settings['synergy_start_timeperiod'] = self.initial_synergy_start_time
        time_helper.actual_timeperiod = self.initial_actual_timeperiod

    def test_simple_build_tree(self):
        self.tree.build_tree()

        actual_yearly_timeperiod = time_helper.actual_timeperiod(QUALIFIER_YEARLY)
        actual_monthly_timeperiod = time_helper.actual_timeperiod(QUALIFIER_MONTHLY)
        actual_daily_timeperiod = time_helper.actual_timeperiod(QUALIFIER_DAILY)
        assert len(self.tree.root.children) == 1
        assert actual_yearly_timeperiod in self.tree.root.children
        self.assertEqual(self.tree.get_node(PROCESS_SITE_YEARLY, actual_yearly_timeperiod).process_name,
                         PROCESS_SITE_YEARLY)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_YEARLY, actual_yearly_timeperiod).timeperiod,
                         actual_yearly_timeperiod)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_YEARLY, actual_yearly_timeperiod).time_qualifier,
                         QUALIFIER_YEARLY)

        assert len(self.tree.root.children[actual_yearly_timeperiod].children) == 1
        assert actual_monthly_timeperiod in self.tree.root.children[actual_yearly_timeperiod].children
        self.assertEqual(self.tree.get_node(PROCESS_SITE_MONTHLY, actual_monthly_timeperiod).process_name,
                         PROCESS_SITE_MONTHLY)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_MONTHLY, actual_monthly_timeperiod).timeperiod,
                         actual_monthly_timeperiod)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_MONTHLY, actual_monthly_timeperiod).time_qualifier,
                         QUALIFIER_MONTHLY)

        assert len(self.tree.root.children[actual_yearly_timeperiod].children[actual_monthly_timeperiod].children) == 1
        assert actual_daily_timeperiod in self.tree.root.children[actual_yearly_timeperiod].children[
            actual_monthly_timeperiod].children
        self.assertEqual(self.tree.get_node(PROCESS_SITE_DAILY, actual_daily_timeperiod).process_name,
                         PROCESS_SITE_DAILY)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_DAILY, actual_daily_timeperiod).timeperiod,
                         actual_daily_timeperiod)
        self.assertEqual(self.tree.get_node(PROCESS_SITE_DAILY, actual_daily_timeperiod).time_qualifier,
                         QUALIFIER_DAILY)

    def _perform_assertions(self, start_timeperiod, delta):
        yearly_timeperiod = time_helper.cast_to_time_qualifier(QUALIFIER_YEARLY,
                                                               start_timeperiod)
        monthly_timeperiod = time_helper.cast_to_time_qualifier(QUALIFIER_MONTHLY,
                                                                start_timeperiod)
        daily_timeperiod = time_helper.cast_to_time_qualifier(QUALIFIER_DAILY,
                                                              start_timeperiod)

        number_of_leafs = 0
        for yt, yearly_root in sorted(self.tree.root.children.items(), key=lambda x: x[0]):
            self.assertEqual(yearly_timeperiod, yt)

            for mt, monthly_root in sorted(yearly_root.children.items(), key=lambda x: x[0]):
                self.assertEqual(monthly_timeperiod, mt)

                for dt, daily_root in sorted(monthly_root.children.items(), key=lambda x: x[0]):
                    self.assertEqual(daily_timeperiod, dt)
                    number_of_leafs += 1

                    daily_timeperiod = time_helper.increment_timeperiod(QUALIFIER_DAILY, daily_timeperiod)

                monthly_timeperiod = time_helper.increment_timeperiod(QUALIFIER_MONTHLY, monthly_timeperiod)

            yearly_timeperiod = time_helper.increment_timeperiod(QUALIFIER_YEARLY, yearly_timeperiod)

        self.assertEqual(number_of_leafs, delta + 1, 'Expected number of daily nodes was %d, while actual is %d'
                                                     % (delta + 1, number_of_leafs))

    def test_less_simple_build_tree(self):
        delta = 5 * 24  # 5 days
        new_synergy_start_time = wind_the_time(QUALIFIER_HOURLY, self.initial_synergy_start_time, -delta)

        settings.settings['synergy_start_timeperiod'] = new_synergy_start_time
        self.tree.build_tree()
        self._perform_assertions(new_synergy_start_time, delta / 24)

    def test_catching_up_time_build_tree(self):
        delta = 5 * 24
        new_synergy_start_time = wind_the_time(QUALIFIER_HOURLY, self.initial_synergy_start_time, -delta)
        settings.settings['synergy_start_timeperiod'] = new_synergy_start_time

        self.tree.build_tree()
        self._perform_assertions(new_synergy_start_time, delta / 24)

        new_actual_timeperiod = wind_the_time(QUALIFIER_HOURLY, self.initial_synergy_start_time, delta)

        time_helper.actual_timeperiod = \
            wind_actual_timeperiod(time_helper.synergy_to_datetime(QUALIFIER_HOURLY, new_actual_timeperiod))
        self.tree.build_tree()
        self._perform_assertions(new_synergy_start_time, 2 * delta / 24)

    def test_is_managing_process(self):
        self.assertIn(PROCESS_SITE_YEARLY, self.tree)
        self.assertIn(PROCESS_SITE_MONTHLY, self.tree)
        self.assertIn(PROCESS_SITE_DAILY, self.tree)
        self.assertNotIn(PROCESS_SITE_HOURLY, self.tree)


if __name__ == '__main__':
    unittest.main()
