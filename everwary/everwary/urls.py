from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^api/', include('api.urls')),
    url(r'^', include('www.urls')),
)
