from django.conf.urls import patterns
from django.conf.urls import url


urlpatterns = patterns(
    '',
    url(r'^$', 'www.views.home'),
    url(r'^login/', 'django.contrib.auth.views.login', {'template_name': 'auth/login.html', 'extra_context': {'next': '/'}}),
    url(r'^logout/', 'django.contrib.auth.views.logout', {'next_page': '/'}),
)
