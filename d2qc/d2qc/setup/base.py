"""
Django settings for d2qc project.

Generated by 'django-admin startproject' using Django 2.1.dev20180428173945.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAMESPACE_DIR = os.path.join(BASE_DIR, 'd2qc')
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Other libraries
sys.path.insert(0, os.path.join(PROJECT_DIR, 'lib'))

# Backup folder
BACKUP_FOLDER = os.path.join(PROJECT_DIR, 'backup')

# Data folder
DATA_FOLDER = os.path.join(BASE_DIR, 'user_data')

# Database initialization script
INITDB_PATH = '/vagrant/scripts/setup/initdb.sql'

# Path to python environment
PYTHON_ENV = os.path.join(
    os.path.expanduser("~"),
    '.env_vagrant',
    'bin',
    'python'
)

ALLOWED_HOSTS = []

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': "{}/temp/error.log".format(PROJECT_DIR),
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['file'],
    },
}


# Application definition

INSTALLED_APPS = [
    'd2qc.data.apps.DataConfig',
    'd2qc.mockup.apps.MockupdataConfig',
    'd2qc.account.apps.AccountConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django.contrib.gis',
    'mathfilters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'd2qc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(NAMESPACE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'd2qc.context_processors.globals', # Always include user object
            ],
        },
    },
]

WSGI_APPLICATION = 'd2qc.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/static'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,

}

LOGIN_REDIRECT_URL = '/data'
LOGOUT_REDIRECT_URL = '/data'

# Polygon covering the Arctic region. Includes all points north
# of 46.8670°N
ARCTIC_REGION = """
    POLYGON((
    -75 46.8670,-25 46.8670,25 46.8670,
    75 46.8670,125 46.8670,175 46.8670,
    -175 46.8670,-125 46.8670,-75 46.8670
))
"""
