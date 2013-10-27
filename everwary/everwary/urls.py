from django.conf.urls import patterns
from django.conf.urls import include
from django.conf.urls import url


urlpatterns = patterns(
    '',
    url(r'^api/', include('api.urls')),
    url(r'^', include('www.urls')),
)
