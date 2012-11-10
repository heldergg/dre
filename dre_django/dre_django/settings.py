# Django settings for dre_django project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

##
## BASE PATHS
##

import os.path
project_dir = os.path.abspath ( os.path.join( os.path.dirname( __file__ ), '../..' ))
django_dir = os.path.abspath ( os.path.join( os.path.dirname( __file__ ), '..' ))

##
## Site admins
##

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8r_^#-*ycr1&=w3pfjhl#$$x#f.jkhgf7ghck&_ipg+8mz*u7tz_i4pd^szdtvg5x5'

SITE_ID = 1

##
## Database definition
##

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', 
        'NAME': '',
    }
}

DJAPIAN_DATABASE_PATH = os.path.join(project_dir, 'archive', 'xapian.db')
DJAPIAN_STEMMING_LANG = 'pt'

##
## Time and Language
##

TIME_ZONE = 'Europe/Lisbon'
LANGUAGE_CODE = 'pt-PT'
USE_I18N = False
USE_L10N = False

##
## Static files
##

# media  = user generated content
# static = site's static files

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join( project_dir, 'static' ) 

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    ( 'dre_django', os.path.join( django_dir, 'static' ) ), 
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'dre_django.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'dre_django.wsgi.application'

##
## Templates
##

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


TEMPLATE_DIRS = (
    os.path.join( django_dir, 'templates'), 
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth', 
    'django.core.context_processors.debug', 
    'django.core.context_processors.i18n', 
    'django.core.context_processors.media', 
    'django.core.context_processors.static', 
    'django.core.context_processors.tz', 
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)



##
## Applications
##

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    ##
    ## DRE apps
    ##
    
    'authapp',
    'dreapp',

    ##
    ## 3rd party apps
    ##

    'djapian',
)

##
## Logging
##

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

## LOGGING = {
##     'version': 1,
##     'disable_existing_loggers': False,
##     'filters': {
##         'require_debug_false': {
##             '()': 'django.utils.log.RequireDebugFalse'
##         }
##     },
##     'handlers': {
##         'mail_admins': {
##             'level': 'ERROR',
##             'filters': ['require_debug_false'],
##             'class': 'django.utils.log.AdminEmailHandler'
##         }
##     },
##     'loggers': {
##         'django.request': {
##             'handlers': ['mail_admins'],
##             'level': 'ERROR',
##             'propagate': True,
##         },
##     }
## }

##
## Authentication and sessions
##

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 24 * 3600 * 14   # 14 days
SESSION_COOKIE_SECURE = False    # set to True if using https
SESSION_COOKIE_NAME = 'dre_sessionid'

LOGIN_URL   = '/auth/login/'
LOGOUT_URL  = '/auth/logout/'

LOGIN_REDIRECT_URL = '/'

REMEMBER_LOGIN = True

FAILURE_LIMIT= 3 # number of failed attempts

##
## Registration
##

PASSWORD_MIN_SIZE = 3
PASSWORD_MAX_SIZE = 30

##
## ReCaptcha
##

RECAPTCHA_PUB_KEY = 'GET A VALID KEY FROM http://recaptcha.net'
RECAPTCHA_PRIV_KEY = 'GET A VALID KEY FROM http://recaptcha.net'
RECAPTCHA_THEME = 'white'

##
## DRE specific
##

## Paths

import os.path

project_dir = os.path.abspath ( os.path.join( os.path.dirname( __file__ ), '../..' ))

LOGDIR  = os.path.join(project_dir, 'log')
ARCHIVEDIR = os.path.join(project_dir, 'archive')

## Log file

LOGFILE = os.path.join(LOGDIR, 'dre.log' )

## STOP Periods
# We will stop gathering new documents in the time periods specifeid bellow
import datetime
STOPTIME = ((datetime.time(23,50), datetime.time(23,59, 59)),
            (datetime.time(0,0),   datetime.time(0,40)),
            )

# Result config
RESULTS_PER_PAGE = 10
ORPHANS = 5

##
## LOCAL
##

try:
    from local_settings import *
except ImportError:
    pass

