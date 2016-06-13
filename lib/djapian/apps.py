# -*- coding: utf-8 -*-

from django.apps import AppConfig

class DjapianConfig(AppConfig):
    name = 'djapian'
    verbose_name = 'Django interface to Xapian'

    def ready(self):
        pass
