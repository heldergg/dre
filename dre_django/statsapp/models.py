# -*- coding: utf-8 -*-

'''
This model manages Apache logs in the following format:

LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"" my_custom_log
'''

from django.db import models
from django.conf import settings

STATSAPP_DB = getattr(settings, 'STATSAPP_DB', 'stats')

class StatsRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'statsapp':
            return STATSAPP_DB
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'statsapp':
            return STATSAPP_DB
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'statsapp' or \
           obj2._meta.app_label == 'statsapp':
           return True
        return None

    def allow_migrate(self, db, model):
        if db == STATSAPP_DB:
            return model._meta.app_label == 'statsapp'
        elif model._meta.app_label == 'statsapp':
            return False
        return None


class LogLine(models.Model):
    '''
    The following indexes where applied to this table:

    Generic indexes:

    create index timestamp_idx on statsapp_logline (timestamp);
    create index response_status_idx on statsapp_logline (response_status);

    Indexes tailored to a given query:

    create index parcial_idx on statsapp_logline (timestamp)
        where response_status = 200 and request_path ~ '^/dre/[0-9]+/$';

    '''
    timestamp = models.DateTimeField()

    remote_host = models.GenericIPAddressField()
    remote_user = models.CharField(max_length= 32, null=True)

    request_type = models.CharField(max_length=8)
    request_proto= models.CharField(max_length=8)
    request_path = models.CharField(max_length= 8190)
    request_referer = models.CharField(max_length= 5120)
    request_useragent = models.CharField(max_length= 2048)

    response_status = models.IntegerField()
    response_bytes = models.IntegerField()
