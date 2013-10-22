from django.conf.urls import patterns, include, url

from api.rest.views import ZoneList
from api.rest.views import ZoneDetail
from api.rest.views import CameraList
from api.rest.views import CameraDetail
from api.rest.views import CameraEventList
from api.rest.views import CameraRecord
from api.rest.views import EventList
from api.rest.views import EventDetail
from api.rest.views import ImageList
from api.rest.views import ImageDetail
from api.rest.views import ImageStream
from api.rest.views import VideoList
from api.rest.views import VideoDetail
from api.rest.views import VideoStream


urlpatterns = patterns('',
    url(r'^zones/$', ZoneList.as_view(), name='api.zone-list'),
    url(r'^zones/(?P<pk>[0-9]+)/$', ZoneDetail.as_view(), name='api.zone-detail'),

    url(r'^cameras/$', CameraList.as_view(), name='api.camera-list'),
    url(r'^cameras/(?P<pk>[0-9]+)/$', CameraDetail.as_view(), name='api.camera-detail'),
    url(r'^cameras/(?P<pk>[0-9]+)/events/$', CameraEventList.as_view(), name='api.camera-events'),
    url(r'^cameras/(?P<pk>[0-9]+)/record/$', CameraRecord.as_view(), name='api.camera-record'),

    url(r'^events/$', EventList.as_view(), name='api.event-list'),
    url(r'^events/(?P<pk>[0-9]+)/$', EventDetail.as_view(), name='api.event-detail'),

    url(r'^images/$', ImageList.as_view(), name='api.image-list'),
    url(r'^images/(?P<pk>[0-9a-f\-]+)/$', ImageDetail.as_view(), name='api.image-detail'),
    url(r'^images/(?P<pk>[0-9a-f\-]+)/stream/$', ImageStream.as_view(), name='api.image-stream'),

    url(r'^videos/$', VideoList.as_view(), name='api.video-list'),
    url(r'^videos/(?P<pk>[0-9a-f\-]+)/$', VideoDetail.as_view(), name='api.video-detail'),
    url(r'^videos/(?P<pk>[0-9a-f\-]+)/stream/$', VideoStream.as_view(), name='api.video-stream'),
)
