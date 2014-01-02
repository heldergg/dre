# -*- coding: utf-8 -*-

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

ALLOWED_HOSTS = [
    '.tretas.org',
    ]

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
USE_I18N = True
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
STATIC_ROOT = os.path.join( project_dir, 'collected_static' )

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(django_dir, 'static'),
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
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
    ##
    ## Django apps
    ##

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    ##
    ## DRE apps
    ##

    'bookmarksapp',
    'tagsapp',
    'notesapp',
    'tipsapp',
    'settingsapp',
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

# This dir must be created by hand
log_dir = os.path.join( project_dir, 'log' )

LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                },
            },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
                }
            },
        'handlers': {
            'default': {
                'level':'INFO',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'dre_django.log'),
                'maxBytes': 1024*1024*50, # 50MB
                'backupCount': 5,
                'formatter':'standard',
                },
            'request_handler': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(log_dir, 'django_request.log'),
                'maxBytes': 1024*1024*5, # 5 MB
                'backupCount': 5,
                'formatter':'standard',
                },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
                },
            },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'DEBUG',
                'propagate': True
                },
            'django.request': {
                'handlers': ['request_handler'],
                'level': 'DEBUG',
                'propagate': False
                },
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
                }
            }
        }

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

# User settings config

USER_SETTINGS = [
        { 'name'      : 'profile_public',
          'label'     : 'Quer o seu perfil público?',
          'default'   : True,
          'type'      : 'boolean',
          'help_text' : '<div style="width:20em;">Determina a visibilidade dos marcadores, notas e etiquetas. <strong>ATENÇÃO</strong>, isto apenas se aplica a novos marcadores, notas e etiquetas.</div>',
        },
        { 'name'      : 'newsletter',
          'label'     : 'Quer receber informações deste site via mail?',
          'default'   : False,
          'type'      : 'boolean',
        },
        { 'name'      : 'show_user_notes',
          'label'     : 'Quer visualizar as suas notas?',
          'default'   : True,
          'type'      : 'boolean',
          'help_text' : '<div style="width:20em;">Quando visualiza um documento pode associar-lhe notas se tiver esta opção ligada.</div>',
        },
        { 'name'      : 'show_tips',
          'label'     : 'Quer visualizar as dicas?',
          'default'   : True,
          'type'      : 'boolean',
        },
        ]

# Tips:

TIPS = [
    # Search tips:
    '''
    <p>O sistema de procura tenta optimizar a busca por forma a dar-lhe os
    melhores resultados. No entanto pode refinar a sua busca
    utilizando modificadores de busca. Por exempo para procurar diplomas com um
    determinado número e tipo (por exemplo "Lei 66-B/2012"), pode filtrar usando:
    <div class="code">
    <p><a href="/?q=tipo:lei+número:66-B/2012"><strong>tipo:</strong>lei <strong>número</strong>:66-B/2012</a></p>
    </div>
    <p>Para saber acerca de mais opções de procura, não deixe de ler a nossa
    <a href="/help">ajuda</a>.
    ''',
    '''
    <p>O sistema de buscas admite alguns modificadores que, se utilizados
    correctamente, podem produzir melhores resultados.

    <p>Por exemplo, se quiser
    visualizar uma lista de diplomas publicados num dado dia pode usar o
    modificador <strong>data</strong>. Os diplomas constantes na
    base de dados do dia 17 de Maio de 1937 são devolvidos por:

    <div class="code">
    <p><a href="/?q=data:19370517"><strong>data:</strong>19370517</a></p>
    </div>

    <p>O formato da data é: <em>AAAAMMDD</em>.

    <p>Para saber acerca de mais opções de procura, não deixe de ler a nossa
    <a href="/help">ajuda</a>.
    ''',

    # Bookmark tips:
    '''<p>Os utilizadores registados podem criar colecções de diplomas, para tal
    basta simplesmente clicar no simbolo de marcador
    (<img src="%(static)simg/bookmark_off.png" style="margin:-0.3em;">).
    <p>Estas colecções podem depois ser organizadas de várias maneiras por forma
    a encontrar sempre todos os documentos que deseje.
    ''' % { 'static': STATIC_URL, },
    '''
    <p>Os utilizadores registados podem anotar todos os diplomas. Basta, para
    tal, clicar em <img src="%(static)simg/edit-note.png" style="margin:-0.3em 0 -0.3em 0;">.
    <p>As notas criadas desta forma podem ser públicas, em cujo caso todos os
    visitantes do site as podem visualizar, ou então, podem ser marcadas como
    privadas, neste caso apenas o utilizador tem permissão para as visualizar.
    ''' % { 'static': STATIC_URL, },

    # General tips
    '''
    <p>Pode consultar os <a href="/dre/data/hoje/">documentos produzidos hoje</a>
    escolhendo a opção a partir do menu. Note que pode consultar os documentos
    produzidos em qualquer dia usando <a href="/dre/data/">esta ligação</a>.
    ''' % { 'static': STATIC_URL, },
    ]

##
## LOCAL
##

try:
    from local_settings import *
except ImportError:
    pass

