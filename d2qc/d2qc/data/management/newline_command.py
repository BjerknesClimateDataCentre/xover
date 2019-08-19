from  django.core.management.base import *
from argparse import RawTextHelpFormatter

class NewlineCommand(BaseCommand):
    def create_parser(self, prog_name, subcommand):
        parser = super().create_parser(prog_name, subcommand)
        parser.formatter_class=RawTextHelpFormatter
        return parser
