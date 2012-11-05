# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, url

urlpatterns = patterns('dreapp.views',
    # Browsing index:
    url(r'^data/$', 'browse', name='browse'),

    # Browse by day:
    url(r'^data/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'browse_day', name='browse_day'),

    # Document display
    url(r'(?P<docid>\d+)/$', 'document_display', name='document_display'),
    )
