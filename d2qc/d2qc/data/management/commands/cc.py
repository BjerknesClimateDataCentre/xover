from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    """Clear cache for the application"""
    def handle(self, *args, **options):
        cache.clear()
        if options['verbosity'] > 0:
            self.stdout.write("Cache cleared!")
