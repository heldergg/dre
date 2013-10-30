Testing the system
==================

You need a working [Django 1.5.x](https://www.djangoproject.com/download/) 
installation, and the python [Xapian 1.2.x](http://xapian.org/) bindings.


i) Get the latest version of dre:

    git clone https://github.com/heldergg/dre.git dre
    cd dre
    git submodule init
    git submodule update

Create the 'log' directory inside the project directory.

    mkdir log

ii) Create a 'local_settings.py' in 'dre\_django/dre_django'. We have to have 
defined on this file at least the database configuration and the reCAPTCHA
keys (if you want to be able to create users). You can get the reCAPTCHA keys
[here](http://recaptcha.net/). 

Example:
    
    # Database configuration:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '<some_existing_path>/dre.db',
        }
    }
    # reCAPTCHA
    RECAPTCHA_PUB_KEY = 'XXXX'
    RECAPTCHA_PRIV_KEY = 'XXXX'

iii) Create the database:

    cd dre_django
    ./dev-manage.py syncdb

You should create the superuser, for testing purposes, you can use it as a regular user.

iv) Download a few documents from dre.pt:

    cd ../bin
    ./dre.py --read_docs 

Please note that sometimes the dre.pt will be overloaded or otherwise not 
responding, you'll have to wait a bit to get your documents.

v) Index the documents using the Xapian library:

    cd ../dre_django
    ./dev-manage.py index --verbose --rebuild

vi) Run the dev server:

    ./dev-manage.py runserver

Every time you add new documents you'll have to index them. You can have a 
long running process to do this:

    ./manage.py index --verbose --loop --time-out=600

Usually this is not needed on a development server.

----

Since you have few documents on the database, you have to make a wide enough search to get results, use something like [this](http://127.0.0.1:8000/?q=a).
