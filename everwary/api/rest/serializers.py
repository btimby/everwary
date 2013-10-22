from rest_framework import serializers

from main.models import Zone
from main.models import Camera
from main.models import Event
from main.models import Image
from main.models import Video


def get_model_names():
    return ['%s %s' % ()]


class ZoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Zone
        fields = ('url', 'name', 'parent', 'children', 'cameras')

    url = serializers.HyperlinkedIdentityField(view_name='api.zone-detail')
    parent = serializers.RelatedField()
    children = serializers.RelatedField(many=True)
    cameras = serializers.HyperlinkedRelatedField(many=True,
                                                  view_name='api.camera-detail')


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ('url', 'timestamp', 'stream')

    url = serializers.HyperlinkedIdentityField(view_name='api.image-detail')
    timestamp = serializers.DateTimeField(source='created')
    stream = serializers.HyperlinkedIdentityField(view_name='api.image-stream')


class VideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Video
        fields = ('url', 'timestamp', 'duration', 'stream')

    url = serializers.HyperlinkedIdentityField(view_name='api.video-detail')
    timestamp = serializers.DateTimeField(source='created')
    stream = serializers.HyperlinkedIdentityField(view_name='api.video-stream')


class EventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Event
        fields = ('url', 'camera', 'name', 'timestamp', 'image', 'video')

    url = serializers.HyperlinkedIdentityField(view_name='api.event-detail')
    camera = serializers.HyperlinkedRelatedField(view_name='api.camera-detail')
    name = serializers.CharField(source='get_event_display')
    timestamp = serializers.DateTimeField(source='created')
    # TODO: skip image / video if null
    image = ImageSerializer()
    video = VideoSerializer()


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = ('url', 'href', 'name', 'model', 'username', 'password',
                  'auth', 'key', 'events')
        read_only_fields = ('auth', 'key')

    url = serializers.HyperlinkedIdentityField(view_name='api.camera-detail')
    href = serializers.URLField(source='url')
    model = serializers.CharField(read_only=True, source='model')
    events = serializers.HyperlinkedIdentityField(view_name='api.camera-events')
