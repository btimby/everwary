import os
import uuid
import errno
import mimetypes

from datetime import timedelta

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from main.cameras import get_backend


def make_uuid():
    return str(uuid.uuid4())


class EventQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        timeago = kwargs.pop('timeago', None)
        if timeago:
            kwargs['created__gte'] = timezone.now()-timedelta(seconds=timeago)
        return super(EventQuerySet, self).filter(*args, **kwargs)


class EventManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return EventQuerySet(self.model, using=self._db)

    get_query_set = get_queryset


class CameraManager(models.Manager):
    def authenticate(self, username, password):
        try:
            return self.get(auth=username, key=password, disabled=False)
        except Camera.DoesNotExist:
            pass


class UUIDKeyModel(models.Model):
    """Most models will use this as a base class, the UUID key
    is convenient for exposing via the API."""
    class Meta:
        abstract = True

    id = models.CharField(max_length=36, primary_key=True,
                          default=make_uuid, editable=False)


class Zone(models.Model):
    """A zone within which cameras are placed. Think of this as a
    category, or physical location. It's usage is up to the user."""
    class Meta:
        unique_together = ('user', 'name')

    # The user that this zone belongs to
    user = models.ForeignKey(User)
    # The parent zone (can be null)
    parent = models.ForeignKey('Zone', null=True, related_name='children')
    # The zone's friendly name
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return unicode(self)


class Event(models.Model):
    """Represents a 'stack' of camera statuses. This is used
    for alerting when a camera is unreachable, as well as for
    displaying the camera's history."""
    CAMERA_EVENT_UNREACHABLE = 1
    CAMERA_EVENT_MOTION = 2
    CAMERA_EVENT_RECORDING = 3
    CAMERA_EVENT_ALERT = 4

    CAMERA_EVENTS = {
        CAMERA_EVENT_UNREACHABLE: _('Unreachable'),
        CAMERA_EVENT_MOTION: _('Motion detected'),
        CAMERA_EVENT_RECORDING: _('Recording video'),
        CAMERA_EVENT_ALERT: _('Alert'),
    }

    camera = models.ForeignKey('Camera', related_name='events')
    event = models.PositiveSmallIntegerField(choices=CAMERA_EVENTS.items())
    # Some states such as unreachable will use the `count` field to track
    # how many successive failures have occurred. For example, you may
    # want to send an alert on the nth failed check.
    count = models.IntegerField(null=False, default=0)
    # An image associated with this state transition
    image = models.ForeignKey('Image', null=True)
    # A video associated with this state transition
    video = models.ForeignKey('Video', null=True)
    # A free-form field allowing the camera event that triggered the
    # state change to provide additional information.
    details = models.TextField(null=True)
    # The time of the state transition.
    created = models.DateTimeField(auto_now_add=True)

    objects = EventManager()

    def __unicode__(self):
        return u'Event %s: %s/%s' % (self.id, self.get_event_display(), self.created)

    def __repr__(self):
        return unicode(self)


class Camera(models.Model):
    """Represents a single Camera."""
    class Meta:
        unique_together = ('zone', 'name')

    CAMERA_STATE_UNKNOWN = 0
    CAMERA_STATE_UNREACHABLE = 1
    CAMERA_STATE_RECORDING = 3
    CAMERA_STATE_OK = 99

    CAMERA_STATES = {
        CAMERA_STATE_UNKNOWN: _('Unknown'),
        CAMERA_STATE_UNREACHABLE: _('Unreachable'),
        CAMERA_STATE_RECORDING: _('Recording video'),
        CAMERA_STATE_OK: _('Ok'),
    }

    # The zone/location of the camera
    zone = models.ForeignKey(Zone, related_name='cameras')
    # The camera make/model
    make = models.CharField(max_length=128)
    model = models.CharField(max_length=128)
    # The latest state of the camera
    state = models.IntegerField(choices=CAMERA_STATES.items(),
                                default=CAMERA_STATE_UNKNOWN)
    # The camera's friendly name
    name = models.CharField(max_length=64)
    # The IP / host name of the camera, including port
    # - http://192.168.1.88:88/
    # - https://mycam00.dyndns.org/
    url = models.URLField(max_length=256)
    # The auth key the camera uses when sending alarms (SMTP or FTP)
    auth = models.CharField(max_length=36, default=make_uuid)
    # The key the camera uses when sending alarms (SMTP or FTP)
    key = models.CharField(max_length=36, default=make_uuid)
    # The username for accessing the camera
    username = models.CharField(max_length=128)
    # The password for accessing the camera
    password = models.CharField(max_length=128)
    # Record video on motion?
    record = models.BooleanField(default=True)
    # Perform health checks?
    health = models.BooleanField(default=True)
    # Send alerts?
    alerts = models.BooleanField(default=True)
    # A camera can be disabled
    disabled = models.BooleanField(default=False)
    # Timestamp operations
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = CameraManager()

    def __unicode__(self):
        return u'Camera %s: %s' % (self.id, self.model)

    def __repr__(self):
        return unicode(self)

    def get_backend(self):
        """Gets the backend responsible for managing this camera."""
        return get_backend(self)

    def set_state(self, state):
        Camera.objects.filter(id=self.id).update(state=state)


class FileBackedModel(UUIDKeyModel):
    """Some storage related actions."""
    class Meta:
        abstract = True

    camera = models.ForeignKey(Camera)
    mime = models.CharField(max_length=32)

    def get_path(self):
        # TODO: use Django storage system
        ext = mimetypes.guess_extension(self.mime)
        fn = os.path.join(settings.ALARM_IMAGE_DIR, str(self.camera_id))
        if not os.path.isdir(fn):
            os.makedirs(fn)
        return os.path.join(fn, '%s%s' % (self.id, ext))

    def open(self, mode='w'):
        # TODO: use Django storage system
        return open(self.get_path(), mode)

    def write(self, f):
        # TODO: use Django storage system
        with self.open() as o:
            o.write(f)


class Image(FileBackedModel):
    """Represents an image captured by a camera."""
    # The time the image was captured
    created = models.DateTimeField(auto_now_add=True)


class Video(FileBackedModel):
    """Represents a video captured by a camera."""
    duration = models.IntegerField(default=0)
    # The time the recording started
    created = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    """Represents an alarm event."""
    camera = models.ForeignKey(Camera)
    image = models.ForeignKey(Image)
    video = models.ForeignKey(Video)


class Period(models.Model):
    """Represents periodic action such as capture."""
