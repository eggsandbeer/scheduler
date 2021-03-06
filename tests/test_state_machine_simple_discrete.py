__author__ = 'Bohdan Mushkevych'

import mock
import unittest
from settings import enable_test_mode
enable_test_mode()

from constants import PROCESS_SITE_HOURLY
from synergy.db.dao.unit_of_work_dao import UnitOfWorkDao
from synergy.db.model import job
from synergy.db.manager.ds_manager import BaseManager
from synergy.system.data_logging import get_logger
from synergy.scheduler.timetable import Timetable
from synergy.scheduler.state_machine_simple_dicrete import StateMachineSimpleDiscrete
from tests.state_machine_testing_utils import *
from tests.base_fixtures import create_unit_of_work
from tests.ut_context import PROCESS_UNIT_TEST


class SimpleDiscreteSMUnitTest(unittest.TestCase):
    def setUp(self):
        self.logger = get_logger(PROCESS_UNIT_TEST)

        self.time_table_mocked = mock.create_autospec(Timetable)
        self.uow_dao_mocked = mock.create_autospec(UnitOfWorkDao)
        self.ds_mocked = mock.create_autospec(BaseManager)

        self.sm_real = StateMachineSimpleDiscrete(self.logger, self.time_table_mocked)
        self.sm_real.uow_dao = self.uow_dao_mocked
        self.sm_real.ds = self.ds_mocked
        self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job = mock.Mock()
        self.sm_real._StateMachineSimpleDiscrete__process_finalizable_job = mock.Mock()
        self.sm_real._process_state_in_progress = mock.Mock(
            side_effect=self.sm_real._process_state_in_progress)

    def tearDown(self):
        pass

    def test_future_timeperiod(self):
        """ coverage scope: make sure no actual processing methods are called for the Future timeperiod"""
        job_record = get_job_record(job.STATE_IN_PROGRESS, TEST_FUTURE_TIMEPERIOD, PROCESS_SITE_HOURLY)
        manual_uow = create_unit_of_work(PROCESS_SITE_HOURLY, 0, 1, None)

        self.uow_dao_mocked.get_one = mock.MagicMock(return_value=manual_uow)
        self.time_table_mocked.is_job_record_finalizable = mock.MagicMock(return_value=True)

        self.sm_real.manage_job(job_record)
        self.sm_real._process_state_in_progress.assert_called_once_with(mock.ANY)

        # verify that processing functions were not called
        self.assertTrue(self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job.call_args_list == [])
        self.assertTrue(self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job.call_args_list == [])

    def test_non_finalizable_job(self):
        """ coverage scope: valid timeperiod with non_finalizable job => call non_finalizable method"""
        for timeperiod in [TEST_PAST_TIMEPERIOD, TEST_ACTUAL_TIMEPERIOD]:
            job_record = get_job_record(job.STATE_IN_PROGRESS, timeperiod, PROCESS_SITE_HOURLY)
            manual_uow = create_unit_of_work(PROCESS_SITE_HOURLY, 0, 1, None)

            self.uow_dao_mocked.get_one = mock.MagicMock(return_value=manual_uow)
            self.time_table_mocked.is_job_record_finalizable = mock.MagicMock(return_value=False)

            self.sm_real.manage_job(job_record)
            self.sm_real._process_state_in_progress.assert_called_once_with(mock.ANY)
            self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job.\
                assert_called_once_with(mock.ANY, mock.ANY, mock.ANY, mock.ANY)
            self.assertTrue(self.sm_real._StateMachineSimpleDiscrete__process_finalizable_job.call_args_list == [])

            # reset mock call count
            self.sm_real._process_state_in_progress.reset_mock()
            self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job.reset_mock()

    def test_finalizable_job(self):
        """ coverage scope: past timeperiod + finalizable job => call on_finalizable method"""
        job_record = get_job_record(job.STATE_IN_PROGRESS, TEST_PAST_TIMEPERIOD, PROCESS_SITE_HOURLY)
        manual_uow = create_unit_of_work(PROCESS_SITE_HOURLY, 0, 1, None)

        self.uow_dao_mocked.get_one = mock.MagicMock(return_value=manual_uow)
        self.time_table_mocked.is_job_record_finalizable = mock.MagicMock(return_value=True)

        self.sm_real.manage_job(job_record)
        self.sm_real._process_state_in_progress.assert_called_once_with(mock.ANY)
        self.assertTrue(self.sm_real._StateMachineSimpleDiscrete__process_non_finalizable_job.call_args_list == [])

        self.sm_real._StateMachineSimpleDiscrete__process_finalizable_job.assert_called_once_with(mock.ANY, mock.ANY)


if __name__ == '__main__':
    unittest.main()
