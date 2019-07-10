# Import some test data to the database

from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):

    def handle(self, *args, **options):
        cache.clear()
