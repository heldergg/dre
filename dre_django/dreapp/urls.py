# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, url

urlpatterns = patterns('dreapp.views',
    # Browsing index:
    url(r'^$', 'browse', name='browse'),

    url(r'(?P<claint>\d+)/$', 'document_display', name='document_display'),
    )
