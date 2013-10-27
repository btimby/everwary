import os
import sys
import time
import socket
import logging

from gearman.worker import GearmanWorker as BaseGearmanWorker
from gearman.errors import ServerUnavailable

from django.conf import settings
from django.core.management.base import BaseCommand

from services.async import PickleDataEncoder
from services.async import tasks


LOGGER = logging.getLogger(__name__)
HOSTNAME = socket.gethostname()


class GearmanWorker(BaseGearmanWorker):
    data_encoder = PickleDataEncoder

    def __init__(self, *args, **kwargs):
        super(GearmanWorker, self).__init__(*args, **kwargs)
        self.quit = False

    def on_job_execute(self, job):
        LOGGER.info('Execution of %r starting', job.task)
        return super(GearmanWorker, self).on_job_execute(job)

    def on_job_complete(self, job, result):
        LOGGER.info('Execution of %r complete', job.task)
        return super(GearmanWorker, self).on_job_complete(job, result)

    def on_job_exception(self, job, exc_info):
        LOGGER.error(str(exc_info[0]), exc_info=exc_info)
        return super(GearmanWorker, self).on_job_exception(job, exc_info)

    def stop(self):
        self.quit = True


class Command(BaseCommand):
    help = 'Gearman worker that exposes async tasks.'

    def handle(self, *args, **options):
        # Configure the root logger, so that we can see ALL logging output
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s',
                            handlers=[logging.StreamHandler()])

        worker = GearmanWorker(getattr(settings, 'GEARMAN_SERVERS', ['localhost']))
        worker.set_client_id('%s:%s' % (HOSTNAME, os.getpid()))
        # Walk the tasks module and register any callables as tasks
        for n in dir(tasks):
            t = getattr(tasks, n)
            if callable(t) and getattr(t, 'task', False):
                LOGGER.debug('Registering task %s', t.__name__)
                worker.register_task(t.__name__, t)
        while not worker.quit:
            try:
                worker.work()
                break
            except ServerUnavailable:
                LOGGER.info('Gearmand unreachable will retry...')
                time.sleep(30)
                continue
            except KeyboardInterrupt:
                LOGGER.info('Interrupted, exiting')
                sys.exit(0)
