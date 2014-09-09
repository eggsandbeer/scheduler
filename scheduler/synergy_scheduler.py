
__author__ = 'Bohdan Mushkevych'

from db.model import scheduler_entry
from db.dao.scheduler_entry_dao import SchedulerEntryDao
from datetime import datetime
from threading import Lock
from amqp import AMQPError

from mq.flopsy import PublishersPool
from mx.synergy_mx import MX

from constants import *
from system.decorator import with_reconnect, thread_safe
from system.synergy_process import SynergyProcess
from system.repeat_timer import RepeatTimer
from system.process_context import *

from scheduler.continuous_pipeline import ContinuousPipeline
from scheduler.dicrete_pipeline import DiscretePipeline
from scheduler.simplified_dicrete_pipeline import SimplifiedDiscretePipeline
from scheduler.timetable import Timetable


class Scheduler(SynergyProcess):
    """ Scheduler encapsulate logic for handling task pipelines """

    def __init__(self, process_name):
        super(Scheduler, self).__init__(process_name)
        self.lock = Lock()
        self.logger.info('Starting %s' % self.process_name)
        self.publishers = PublishersPool(self.logger)
        self.thread_handlers = dict()
        self.timetable = Timetable(self.logger)
        self.pipelines = self._construct_pipelines()

        self.sc_dao = SchedulerEntryDao(self.logger)
        self.mx = None
        self.logger.info('Started %s' % self.process_name)

    def __del__(self):
        for handler in self.thread_handlers:
            handler.cancel()
        self.thread_handlers.clear()
        super(Scheduler, self).__del__()

    def _log_message(self, level, process_name, timetable_record, msg):
        """ method performs logging into log file and TimeTable node"""
        self.timetable.add_log_entry(process_name, timetable_record, datetime.utcnow(), msg)
        self.logger.log(level, msg)

    def _construct_pipelines(self):
        """ :return: dict in format <state_machine_common_name: instance_of_the_state_machine> """
        pipelines = dict()
        for pipe in [ContinuousPipeline(self.logger, self.timetable),
                     DiscretePipeline(self.logger, self.timetable),
                     SimplifiedDiscretePipeline(self.logger, self.timetable)]:
            pipelines[pipe.name] = pipe
        return pipelines

    # **************** Scheduler Methods ************************
    @with_reconnect
    def start(self, *_):
        """ reading scheduler configurations and starting timers to trigger events """
        scheduler_entries = self.sc_dao.get_all()

        for entry_document in scheduler_entries:
            if entry_document.process_name not in ProcessContext.CONTEXT:
                self.logger.error('Process %r is not known to the system. Skipping it.' % entry_document.process_name)
                continue

            interval = entry_document.interval
            is_active = entry_document.process_state == scheduler_entry.STATE_ON
            process_type = ProcessContext.get_process_type(entry_document.process_name)
            parameters = [entry_document.process_name, entry_document]

            if process_type in [TYPE_BLOCKING_DEPENDENCIES_WORKER, TYPE_BLOCKING_CHILDREN_WORKER, TYPE_MANAGED_WORKER]:
                function = self.fire_managed_worker
            elif process_type == TYPE_FREERUN_WORKER:
                function = self.fire_freerun_worker
            elif process_type == TYPE_GARBAGE_COLLECTOR:
                function = self.fire_garbage_collector
            else:
                self.logger.error('Can not start scheduler for %s since it has no processing function' % process_type)
                continue

            handler = RepeatTimer(interval, function, args=parameters)
            self.thread_handlers[entry_document.process_name] = handler

            if is_active:
                handler.start()
                self.logger.info('Started scheduler for %s:%s, triggering every %d seconds'
                                 % (process_type, entry_document.process_name, interval))
            else:
                self.logger.info('Handler for %s:%s registered in Scheduler. Idle until activated.'
                                 % (process_type, entry_document.process_name))

        # as Scheduler is now initialized and running - we can safely start its MX
        self.mx = MX(self)
        self.mx.start_mx_thread()

    @thread_safe
    def fire_managed_worker(self, *args):
        """requests vertical aggregator (hourly site, daily variant, etc) to start up"""
        try:
            process_name = args[0]
            entry_document = args[1]
            self.logger.info('%s {' % process_name)

            timetable_record = self.timetable.get_next_timetable_record(process_name)
            pipeline = self.pipelines[entry_document.state_machine_name]

            process_type = ProcessContext.get_process_type(entry_document.process_name)
            if process_type == TYPE_BLOCKING_DEPENDENCIES_WORKER:
                pipeline.manage_pipeline_with_blocking_dependencies(process_name, timetable_record)
            elif process_type == TYPE_BLOCKING_CHILDREN_WORKER:
                pipeline.manage_pipeline_with_blocking_children(process_name, timetable_record)
            elif process_type == TYPE_MANAGED_WORKER:
                pipeline.manage_pipeline_for_process(process_name, timetable_record)


        except (AMQPError, IOError) as e:
            self.logger.error('AMQPError: %s' % str(e), exc_info=True)
            self.publishers.reset_all(suppress_logging=True)
        except Exception as e:
            self.logger.error('Exception: %s' % str(e), exc_info=True)
        finally:
            self.logger.info('}')

    @thread_safe
    def fire_freerun_worker(self, *args):
        """fires free-run worker with no dependencies to track"""
        try:
            process_name = args[0]
            entry_document = args[1]
            assert isinstance(entry_document, scheduler_entry.SchedulerEntry)
            self.logger.info('%s {' % process_name)

            publisher = self.publishers.get(process_name)
            publisher.publish(ProcessContext.get_arguments(process_name))
            publisher.release()

            self.logger.info('Publishing trigger for %s' % process_name)
        except (AMQPError, IOError) as e:
            self.logger.error('AMQPError: %s' % str(e), exc_info=True)
            self.publishers.reset_all(suppress_logging=True)
        except Exception as e:
            self.logger.error('fire_freerun_worker: %s' % str(e))
        finally:
            self.logger.info('}')
            self.lock.release()

    @thread_safe
    def fire_garbage_collector(self, *args):
        """fires garbage collector to re-run all invalid records"""
        try:
            process_name = args[0]
            self.logger.info('%s {' % process_name)

            publisher = self.publishers.get(process_name)
            publisher.publish({})
            publisher.release()

            self.logger.info('Publishing trigger for garbage_collector')
            self.timetable.build_trees()
            self.timetable.validate()
            self.logger.info('Validated Timetable for all trees')
        except (AMQPError, IOError) as e:
            self.logger.error('AMQPError: %s' % str(e), exc_info=True)
            self.publishers.reset_all(suppress_logging=True)
        except Exception as e:
            self.logger.error('fire_garbage_collector: %s' % str(e))
        finally:
            self.logger.info('}')
            self.lock.release()


if __name__ == '__main__':
    from constants import PROCESS_SCHEDULER

    source = Scheduler(PROCESS_SCHEDULER)
    source.start()
