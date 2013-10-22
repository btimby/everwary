from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import generics

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

from main.models import Zone
from main.models import Camera
from main.models import Event
from main.models import Image
from main.models import Video

from api.rest.filters import EventFilter
from api.rest.serializers import ZoneSerializer
from api.rest.serializers import CameraSerializer
from api.rest.serializers import EventSerializer
from api.rest.serializers import ImageSerializer
from api.rest.serializers import VideoSerializer


class StreamView(APIView):
    def get(self, request, *args, **kwargs):
        o = get_object_or_404(self.model, camera__zone__user=request.user, pk=kwargs['pk'])
        f = o.open(mode='rb')
        return StreamingHttpResponse(f, content_type=o.mime)


class ZoneList(mixins.ListModelMixin, mixins.CreateModelMixin,
               generics.GenericAPIView):
    """Lists all of your zones.

    Zones are used to group cameras. Often by physical location and/or type.

    Zones can contain other zones, for nesting."""
    model = Zone
    serializer_class = ZoneSerializer

    def get_queryset(self):
        return Zone.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ZoneDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                 mixins.DestroyModelMixin, generics.GenericAPIView):
    model = Zone
    serializer_class = ZoneSerializer

    def get_queryset(self):
        return Zone.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class CameraList(mixins.ListModelMixin, mixins.CreateModelMixin,
                 generics.GenericAPIView):
    model = Camera
    serializer_class = CameraSerializer

    def get_queryset(self):
        return Camera.objects.filter(zone__user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class CameraDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin, generics.GenericAPIView):
    model = Camera
    serializer_class = CameraSerializer

    def get_queryset(self):
        return Camera.objects.filter(zone__user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class CameraEventList(mixins.ListModelMixin, generics.GenericAPIView):
    model = Event
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(camera__id=self.kwargs['pk']).order_by('-created')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class CameraRecord(APIView):
    def post(self):
        pass


class EventList(mixins.ListModelMixin, generics.GenericAPIView):
    model = Event
    serializer_class = EventSerializer
    filter_class = EventFilter

    def get_queryset(self):
        return Event.objects.filter(camera__zone__user=self.request.user).order_by('-created')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class EventDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    model = Event
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(camera__zone__user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ImageList(mixins.ListModelMixin, generics.GenericAPIView):
    model = Image
    serializer_class = ImageSerializer

    def get_queryset(self):
        return Image.objects.filter(camera__zone__user=self.request.user).order_by('-created')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ImageDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    model = Image
    serializer_class = ImageSerializer

    def get_queryset(self):
        return Image.objects.filter(camera__zone__user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class ImageStream(StreamView):
    model = Image


class VideoList(mixins.ListModelMixin, generics.GenericAPIView):
    model = Video
    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.filter(camera__zone__user=self.request.user).order_by('created')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class VideoDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):
    model = Video
    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.filter(camera__zone__user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class VideoStream(StreamView):
    model = Video
