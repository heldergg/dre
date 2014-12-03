# -*- coding: utf-8 -*-

# Global Imports:
from django.conf.urls import patterns, url

urlpatterns = patterns('dreapp.views',
    # Browsing index:
    url(r'^data/$', 'browse', name='browse'),

    # Today's results:
    url(r'^data/hoje/$', 'today_results', name='today_results'),

    # Browse by day:
    url(r'^data/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 'browse_day', name='browse_day'),

    # Document display
    url(r'^(?P<docid>\d+)/$', 'document_display', name='document_display'),

    # Document display (JSON)
    url(r'^(?P<docid>\d+).json$', 'document_json', name='document_json'),

    # Document display (Original PDF)
    url(r'^(?P<docid>\d+).dre.pdf$', 'document_org_pdf', name='document_org_pdf'),

    # Related documents search result
    url(r'^(?P<docid>\d+)/related/$', 'related', name='related_document'),

    # Display the bookmarked documents
    url(r'^marcador/(?P<userid>\d+)/$','bookmark_display', name='bookmark_display'),
    )

##
# Feeds
##

from dreapp.syndication import LatestEntriesFeed

urlpatterns += patterns('',
    # Latest feeds
    url(r'^rss/$', LatestEntriesFeed(), name='latest_entries_feed'),

    )
