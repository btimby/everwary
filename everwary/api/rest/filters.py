import django_filters

from main.models import Event

from api.rest.forms import EventFilterForm


class EventFilter(django_filters.FilterSet):
    class Meta:
        model = Event
        fields = ('event', )
        form = EventFilterForm

    event = django_filters.CharFilter()
    timestamp = django_filters.DateRangeFilter(name='created')
