from django.conf import settings
import os


def postgres_wo_password():
    '''
    To allow postgres access without providing a password, the password can be
    added to a .pgpass - file in the users home folder. This function does that
    if a .pgpass - file don't already exist.
    '''

    db_name = settings.DATABASES['default']['NAME']
    user = settings.DATABASES['default']['USER']
    pw = settings.DATABASES['default']['PASSWORD']
    host = settings.DATABASES['default']['HOST']
    port = settings.DATABASES['default']['PORT']
    pgpass_file = os.path.expanduser('~/.pgpass')
    if not os.path.isfile(pgpass_file):
        with open(pgpass_file, 'a') as pgpass:
            pgpass.write("{}:{}:{}:{}:{}".format(
                    host, port or '*', user, pw, db_name
                )
            )
        os.chmod(pgpass_file, 0o600)
