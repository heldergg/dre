Install
=======

You need a working [Django 1.9.x](https://www.djangoproject.com/download/)
installation, and the python [Xapian 1.2.x](http://xapian.org/) bindings.


i) Get the latest version of dre:

    git clone https://github.com/heldergg/dre.git dre
    cd dre

Create the 'log' directory inside the project directory.

    mkdir log

ii) Install the requirements:

    pip install -r requirements.txt

It's also necessary to install the Xapian library and its python key bindings.
Use your distribution packages to do that. For instance for Ubuntu 16.10:

    # sudo apt install python-xapian

iii) Create a 'local_settings.py' in 'dre\_django/dre_django'. We have to have
defined on this file at least the database configuration and the reCAPTCHA
keys (if you want to be able to create users). You can get the reCAPTCHA keys
[here](http://recaptcha.net/).

Example:

    # Database configuration:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '<absolute path to>/dre.db',
        }
    }
    # reCAPTCHA
    RECAPTCHA_PUB_KEY = 'XXXX'
    RECAPTCHA_PRIV_KEY = 'XXXX'

iv) Create the database:

    cd dre_django
    ./dev-manage.py migrate --run-syncdb

You should create the superuser, for testing purposes, you can use it as a regular user:

    ./dev-manage.py createsuperuser

Note we're using **dev**-manage.py. This is similar to manage.py but adds
'dre/lib' to the PYTHONPATH.

v) Download a few documents from dre.pt:

    cd ../bin
    ./dre.py --read_date 2016-11-04

Please note that sometimes the dre.pt will be overloaded or otherwise not
responding, you'll have to wait a bit to get your documents. The above will
retrieve the official journal documents from the stated date. If you want to
have a more complete database we do full database dumps every Sunday at 10:00
GMT. You can get the dump [here](https://www.dropbox.com/sh/l5fwcbnncezluqb/AACiP_oNj6Cv0D74lvXcb-KWa?dl=0). Note, this is a PostgreSQL dump so, to use it,
the easiest way is to use a PostgreSQL database backend.

vi) Index the documents using the Xapian library:

    cd ../dre_django
    ./dev-manage.py index --verbose --rebuild

vii) Run the dev server:

    ./dev-manage.py runserver

Every time you add new documents you'll have to index them. You can have a
long running process to do this:

    ./manage.py index --verbose --loop --time-out=600

Usually this is not needed on a development server.

----

Since you have few documents on the database, you have to make a wide enough search to get results, use something like http://127.0.0.1:8000/?q=a .
