from django import forms

from main.models import Event


CAMERA_EVENTS_REVERSE = dict((v, k) for (k, v) in Event.CAMERA_EVENTS.items())


class EventFilterForm(forms.Form):
    def clean_event(self):
        value = self.cleaned_data.get('event')
        if not value:
            return
        try:
            return CAMERA_EVENTS_REVERSE[value]
        except KeyError:
            raise forms.ValidationError('Invalid event name "%s"' % value)
