#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Read Apache logs to the database.

Note: Apache can log directly to the databse, however this will add a certain
overhead to each request/response. Using a batch task such as this one we can
concentrate the load when the server is least loaded.
'''

##
# Imports

import sys
import os.path

sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

import django
django.setup()

from dre_stats import LogReader

##
# Read the logs

log_reader = LogReader()

log_reader.run()
