from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs EverWary scheduled operations.'

    def handle(self, *args, **kwargs):
        pass
