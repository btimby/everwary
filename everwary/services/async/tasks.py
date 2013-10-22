import time
import logging

from functools import wraps

from django.utils import timezone

from main.models import Camera
from main.models import Event

from services.async import GEARMAN


# TODO: this should be configurable per camera / account.
RECORDING_DURATION = 60
# TODO: this should be configurable per camera / account.
ALERT_INTERVAL = 300

LOGGER = logging.getLogger(__name__)


def task(f):
    @wraps(f)
    def decorator(worker, job):
        args = job.data.get('args', ())
        kwargs = job.data.get('kwargs', {})
        return f(*args, **kwargs)
    setattr(decorator, 'task', True)
    return decorator


@task
def alert(event):
    """Sends an alert when motion is detected."""
    LOGGER.info('Sending alert for %s', event.camera)
    event.camera.events.create(event=Event.CAMERA_EVENT_ALERT, image=event.image)


@task
def motion(event):
    """Handles motion detection for a camera."""
    # Discard stale motion events
    if (timezone.now() - event.created).seconds >= RECORDING_DURATION:
        return
    # if last alert was sent more than ALERT_THRESHOLD ago, send another
    if not event.camera.events.filter(event=Event.CAMERA_EVENT_ALERT,
                                      timeago=ALERT_INTERVAL).count():
        # Send a new alert asynchronously, without waiting.
        GEARMAN.submit_job('alert', data={'args': (event, ), 'kwargs':
                           {}}, background=True, wait_until_complete=False)
    # if already recording, nothing left to do.
    if event.camera.state == Camera.CAMERA_STATE_RECORDING:
        LOGGER.info('Already recording for %s', event.camera)
        return
    LOGGER.info('Recording for %s', event.camera)
    event.camera.set_state(Camera.CAMERA_STATE_RECORDING)
    try:
        be = event.camera.get_backend()
        be.record()
        try:
            while True:
                # Check camera is still enabled
                if event.camera.disabled:
                    break
                # Check that there is recent detected motion
                if not event.camera.events.filter(event=Event.CAMERA_EVENT_MOTION,
                                                  timeago=RECORDING_DURATION).count():
                    break
                time.sleep(10.0)
        finally:
            event.camera.events.create(event=Event.CAMERA_EVENT_RECORDING,
                                       video=be.stop())
    finally:
        event.camera.set_state(Camera.CAMERA_STATE_OK)
    LOGGER.info('Done recording for %s', event.camera)
