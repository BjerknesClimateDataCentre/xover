from d2qc.data.management.newline_command import NewlineCommand
from django.core.cache import cache

class Command(NewlineCommand):
    help = """Clear cache for the application"""
    def handle(self, *args, **options):
        cache.clear()
        if options['verbosity'] > 0:
            self.stdout.write("Cache cleared!")
