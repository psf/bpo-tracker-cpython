# Django settings for django_gae2django project.

# NOTE: Keep the settings.py in examples directories in sync with this one!

import os, ConfigParser, re

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

_c = ConfigParser.ConfigParser({'password':'', 'port':''})
_c.read(os.path.dirname(__file__)+"/../config.ini")
TRACKER_COOKIE_NAME=re.sub('[^a-zA-Z]', '', _c.get('tracker','name'))

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = _c.get('rdbms', 'name')
DATABASE_USER = _c.get('rdbms', 'user')
DATABASE_PASSWORD = _c.get('rdbms', 'password')
DATABASE_HOST = _c.get('rdbms', 'host')
DATABASE_PORT = _c.get('rdbms', 'port')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/review/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = _c.get('django', 'secret_key')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

AUTHENTICATION_BACKENDS = ('roundup_helper.middleware.UserBackend',)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'roundup_helper.middleware.LookupRoundupUser',
    'gae2django.middleware.FixRequestUserMiddleware',
    'rietveld_helper.middleware.AddUserToRequestMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'roundup_helper.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'gae2django',
    'rietveld_helper',
    'codereview',
)

AUTH_PROFILE_MODULE = 'codereview.Account'
LOGIN_REDIRECT_URL = '/'

# This won't work with gae2django.
RIETVELD_INCOMING_MAIL_ADDRESS = None
